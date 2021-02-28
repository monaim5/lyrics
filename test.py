import json
from datetime import datetime
from pathlib import Path
from youtube_dl import YoutubeDL

from models import get_session, UploadedVideo
from paths import Dir
from youtube_utils import get_mapped_uploaded_to_original_videos

original_videos_source_folder = Dir.scrapped_youtube_videos_data.value / 'NoCopyrightSounds_uploads'
target_videos_folder = Dir.scrapped_youtube_videos_data.value / 'NCSArabi_uploads'

target_uploaded_videos = []
original_uploaded_videos = []
with get_session() as session:
    for file in target_videos_folder.glob('*.json'):
        with open(file, 'r', encoding='utf-8') as f:
            target_uploaded_videos.extend(json.load(f)['items'])

    videos = get_mapped_uploaded_to_original_videos(original_videos_source_folder.glob('*.json'),
                                                    target_videos_folder.glob('*.json'))
    videos = list(videos)
    videos_not_in_ncs = list(filter(lambda x: x['snippet']['resourceId']['videoId'] not in list(map(
        lambda y: y['target_video_id'], videos)),
                                    target_uploaded_videos))

    for video in videos_not_in_ncs:
        uploaded_video = UploadedVideo(None, None)
        uploaded_video.youtube_id = video['snippet']['resourceId']['videoId']
        uploaded_video.channel_id = video['snippet']['videoOwnerChannelId']
        uploaded_video.title = video['snippet']['title']
        uploaded_video.published_date = datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
        uploaded_video.add(session)
    session.commit()
    exit()
    for video in videos_not_in_ncs:
        if uploaded_video := session.query(UploadedVideo).filter_by(youtube_id=video['target_video_id']).scalar():
            print(f'{uploaded_video.youtube_id} exists in db')
        else:
            uploaded_video = UploadedVideo(None, None)

        uploaded_video.original_youtube_id = video['original_video_id']
        uploaded_video.youtube_id = video['target_video_id']
        uploaded_video.original_channel_id = video['original_video_channel_id']
        uploaded_video.channel_id = video['target_video_channel_id']
        print(uploaded_video.channel_id)

        uploaded_video.published_date = datetime.strptime(video['target_published_date'], '%Y-%m-%dT%H:%M:%SZ')
        uploaded_video.title = video['target_video_title']
        uploaded_video.add(session)
    session.commit()

exit()

videos = get_mapped_uploaded_to_original_videos(original_videos_source_folder.glob('*.json'),
                                                target_videos_folder.glob('*.json'))

videos = list(videos)

print(len(videos))

original_duplicates = list(filter(lambda v: v['target_video_id'] in duplicates, videos))
print(duplicates)
for video in original_duplicates:
    print(video)

exit()
target_video_ids = list(map(lambda v: v['target_video_id'], videos))
duplicated_videos_ids = set(filter(lambda video_id: target_video_ids.count(video_id) > 1, target_video_ids))
vds = [video for video in videos if video['target_video_id'] in duplicated_videos_ids]
print(vds)
exit()

# dup = {(video, videos.count(video)) for video in set(videos) if videos.count(video) > 1}
exit()


def download_song(url, out_dir):
    download_options = {
        'format': 'bestaudio/best',
        'outtmpl': f'{out_dir}/%(title)s.%(ext)s',
        'nocheckcertificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    with YoutubeDL(download_options) as youtube:
        youtube.download([url])

    return True


home = Path.home() / 'desktop/omar_songs.txt'
omar_songs = home / 'desktop/omar songs'
songs_file = omar_songs / 'omar_songs.txt'

with open(songs_file) as f:
    songs = f.read().splitlines()

for url in songs:
    download_song(url, omar_songs)
