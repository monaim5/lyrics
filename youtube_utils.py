import pickle
import re
from functools import reduce

from apiclient.discovery import build

from background.utils import download_background
from models2 import Background
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

