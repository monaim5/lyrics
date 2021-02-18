import json
from pathlib import Path
from youtube_dl import YoutubeDL

from paths import Dir
from youtube_utils import register_playlist_videos, register_channel_uploads


register_channel_uploads(channel_id='UCLbsLjqzPKBLa7kzlEmfCXA',
                         api_key='AIzaSyB-PW9xhNxCC5EGZm0du75i3P27fB5ij50',
                         folder='NCSArabi_uploads')


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