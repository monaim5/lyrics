import re
from pathlib import Path

from youtube_dl import YoutubeDL


import urllib.request

url = 'https://yt3.ggpht.com/ytc/AAUvwnjAlfI_yEokR2mvK0mOZATU_vKQgq8UUNrW0fBT=s48-c-k-c0xffffffff-no-rj-mo'

pattern = re.compile('[^=]*')
nurl = pattern.search(url)
print(nurl.group(0))
exit()
urllib.request.urlretrieve(url, "00000001.jpg")

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