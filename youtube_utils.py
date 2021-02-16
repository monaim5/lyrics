import pickle
import re
from functools import reduce

from apiclient.discovery import build

from models2 import Background


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
    top = {(k, v) for k, v in top.items()}
    top_commentators = sorted(top, key=lambda v: v[1]['comment_count'], reverse=True)[:top_count]
    for commentator in top_commentators:
        url = re.search('[^=]*', commentator[1]['imageUrl'])
        background = Background(url)
        background.path = Dir.

