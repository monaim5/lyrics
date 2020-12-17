import re


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


from pathlib import Path

from youtube_dl import YoutubeDL

from models2 import Song
from paths import Dir


def get_yt_id(url):
    match = re.search(r"youtube\.com/.*v=([^&]*)", url)
    if match:
        return match.group(1)
    else:
        raise Exception('no id in url')


def download_song(song) -> Song:
    download_options = {
        'format': 'bestaudio/best',
        'outtmpl': f'{Dir.songs_dir.value}/%(title)s.%(ext)s',
        'nocheckcertificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }

    with YoutubeDL(download_options) as youtube:
        youtube.download([song.url])
        info = youtube.extract_info(song.url)
        song.title = info.get('title')
        song.path = Path(youtube.filename.replace('webm', 'mp3'))
        song.description = info.get('description')
        # song.credit=get_credit(info.get('description')),
        song.channel_name = info.get('channel')
        song.channel_id = info.get('channel_id')
    return song
