import json
import pickle
import re
from functools import reduce
from pathlib import Path

from apiclient.discovery import build
from typing import List

from bs4 import BeautifulSoup
from googleapiclient.discovery import Resource
from urllib3 import HTTPResponse

from background.utils import download_background
from models import Background
from paths import Dir


class YoutubeApiManager:
    __apis_by_token = {}
    __apis_by_api_key = {}

    __api_service_name = "youtube"
    __api_version = "v3"

    @classmethod
    def api_by_api_key(cls, api_key):
        if api_key in cls.__apis_by_api_key:
            return cls.__apis_by_api_key[api_key]
        else:
            cls.__apis_by_api_key[api_key] = build(cls.__api_service_name, cls.__api_version, developerKey=api_key)
            return cls.__apis_by_api_key[api_key]

    @classmethod
    def api_by_token(cls, token_path):
        if token_path in cls.__apis_by_token:
            return cls.__apis_by_token[token_path]
        else:
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            cls.__apis_by_token[token_path] = build(cls.__api_service_name, cls.__api_version, credentials=creds)
            return cls.__apis_by_token[token_path]


def list_comments(channel_id, api_key, max_result):
    youtube = YoutubeApiManager.api_by_api_key(api_key)
    api_request = youtube.commentThreads().list(
        part="snippet",  # ,replies
        allThreadsRelatedToChannelId=channel_id,
        maxResults=max_result
    )
    return api_request.execute()


def get_top_commentators(channel, top_count):
    comments = list_comments(channel.id, channel.api_key, 100)

    def map_reduce(acc, c):
        comment_info = c['snippet']['topLevelComment']['snippet']
        author_channel_id = comment_info['authorChannelId']['value']
        if author_channel_id in acc:
            acc[author_channel_id]['comment_count'] += 1
        else:
            acc[author_channel_id] = {'comment_count': 1,
                                      'name': comment_info['authorDisplayName'],
                                      'imageUrl': comment_info['authorProfileImageUrl']}
        return acc

    top = reduce(map_reduce, comments['items'], {})
    top = [{'channel_id': k, 'info': v} for k, v in top.items()]
    # top = {(k, v) for k, v in top.items()}
    top_commentators = sorted(top, key=lambda v: v['info']['comment_count'], reverse=True)[:top_count]
    for index, commentator in enumerate(top_commentators):
        commentator['info']['rank'] = index + 1
        url = re.search('[^=]*', commentator['info']['imageUrl']).group()
        background = Background(url)
        background.path = (Dir.channels_images.value / commentator['channel_id'])
        background = download_background(background)
        commentator['info']['image_path'] = background.path
    return [{'name': commentator['info']['name'],
             'rank': commentator['info']['rank'],
             'thumbnailPath': commentator['info']['image_path'].__str__()} for commentator in top_commentators]


def pick_musics_from_youtube(uploaded_videos):
    pass


def get_uploads_playlist_id(channel_id, api_key):
    api = YoutubeApiManager.api_by_api_key(api_key)
    request = api.channels().list(
        part='contentDetails',
        id=channel_id
    )
    response = request.execute()
    return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


def get_playlist_videos(playlist_id, api_key):
    # Obtain the Uploads Playlist ID of the channel:
    # https://www.googleapis.com/youtube/v3/channels?id={channel Id}&key={API key}&part=contentDetails
    api = YoutubeApiManager.api_by_api_key(api_key)

    videos = []
    has_more = True
    page_token = None

    while has_more:
        request = api.playlistItems().list(
            part='snippet',
            maxResults=100,
            playlistId=playlist_id,
            pageToken=page_token
        )
        response = request.execute()
        videos.append(response)
        has_more = 'nextPageToken' in response
        page_token = response['nextPageToken'] if has_more else None

    return videos


def get_channel_uploads(channel_id, api_key):
    uploads_playlist_id = get_uploads_playlist_id(channel_id, api_key)
    return get_playlist_videos(uploads_playlist_id, api_key)


def scrape_tags_by_id(video_id):
    from urllib3 import PoolManager
    url = f'http://www.youtube.com/watch?v={video_id}'
    http = PoolManager()
    print(f'GET tags for url: {url} ...')
    resp: HTTPResponse = http.request('GET', url)

    soup = BeautifulSoup(resp.data, 'html.parser')
    return list(map(lambda x: x.strip(), soup.find('meta', {'name': 'keywords'}).get('content').split(',')))


def search_videos_by_keyword(keyword, api_key):
    api = YoutubeApiManager.api_by_api_key(api_key)
    request = api.search().list(
        part='snippet',
        q=keyword,
        maxResults=25,
    )
    videos = request.execute()
    for v in videos['items']:
        try:
            v['snippet']['tags'] = scrape_tags_by_id(v['id']['videoId'])
        except Exception as e:
            print(e.__str__())
    return videos


def register_searched_videos(videos: dict, name, folder):
    directory: Path = Dir.scrapped_youtube_videos_data.value / folder if folder else Dir.scrapped_youtube_videos_data.value
    if not directory.exists():
        directory.mkdir()
    with open(directory / f'{name}_videos.json', 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2, sort_keys=True)


def register_videos(videos: List, folder):
    directory: Path = Dir.scrapped_youtube_videos_data.value / folder if folder else Dir.scrapped_youtube_videos_data.value
    if not directory.exists():
        directory.mkdir()
    for index, page in enumerate(videos):
        with open(directory / f'{videos[0]["items"][0]["snippet"]["channelId"]}_page_{index + 1}.json',
                  'w', encoding='utf-8') as f:
            json.dump(page, f, ensure_ascii=False, indent=2, sort_keys=True)


def get_mapped_uploaded_to_original_videos(original_videos_source: List[Path], target_videos: List[Path]):
    original_videos = []
    uploaded_videos = []

    for path in original_videos_source:
        with open(path, encoding='utf-8') as f:
            original_videos.extend(json.load(f)['items'])

    for path in target_videos:
        with open(path, encoding='utf-8') as f:
            uploaded_videos.extend(json.load(f)['items'])

    def map_to_id_title_channel_id(v):
        return (v['snippet']['resourceId']['videoId'],
                v['snippet']['title'],
                v['snippet']['videoOwnerChannelId'],
                v['snippet']['publishedAt'])

    uploaded_videos = map(map_to_id_title_channel_id, uploaded_videos)
    original_videos = list(map(map_to_id_title_channel_id, original_videos))
    while True:
        try:
            uploaded_video = next(uploaded_videos)
            for video in original_videos:
                # video (video_id, video_title, channel_id, publish_at)
                if not re.search('remix', video[1], re.IGNORECASE) and re.match(
                        re.match('[^\(.*\)|\[.*\]|\u0627-\u064a]+', uploaded_video[1]).group(),
                        video[1]):
                    yield {
                        'original_video_id': video[0],
                        'original_video_title': video[1],
                        'original_video_channel_id': video[2],
                        'original_published_date': video[3],
                        'target_video_id': uploaded_video[0],
                        'target_video_title': uploaded_video[1],
                        'target_video_channel_id': uploaded_video[2],
                        'target_published_date': uploaded_video[3]
                    }
        except StopIteration:
            print("end of iterator in get_mapped_uploaded_to_original_videos")
            break


def register_uploaded_videos(videos):
    pass


def get_video_from_youtube():
    pass
