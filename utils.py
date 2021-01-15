import re
from enum import Enum
from pathlib import Path
from youtube_dl import YoutubeDL
from models2 import Song
from paths import Dir


class Color(Enum):
    YELLOW = '#eddd00'


class Bcolors(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_yt_id(url):
    match = re.search(r"youtube\.com/.*v=([^&]*)", url)
    if match:
        return match.group(1)
    else:
        raise Exception('no id in url')


def get_credit(desc):
    result = re.search('Track:(.|\n)*- -', desc)
    return str(result.group(0)) if result else ''


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
        info = youtube.extract_info(song.url)
        song.title = info.get('title')
        song.audio_bitrate = info.get('abr')
        song.path = Path(youtube.filename.replace('webm', 'mp3'))
        song.description = info.get('description')
        song.tags = info.get('tags')
        song.credit = get_credit(info.get('description'))
        song.channel_name = info.get('channel')
        song.channel_id = info.get('channel_id')

        if not song.file_exists:
            youtube.download([song.url])
        song.downloaded = True

    return song
