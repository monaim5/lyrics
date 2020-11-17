from lyrics.lyrics import get_lyrics, map_lyrics, adjust_lyrics
from video.utils import create_aep, render_aep, upload_video, generate_desc, generate_tags, generate_title
from models import Song, Channel
from paths import songs_dir, backgrounds_dir
from utils import bcolors

# fix duration in adobe after script (to_lyrics.jsx)
# change file_name to filename
# adapt with background not with bg_ext
songs = songs_dir.glob('*.mp3')
channel = Channel('ncs_arabi')


def up_vid():
    upload_try = 1
    try:

        print(f'{bcolors.WARNING}{bcolors.BOLD}the {upload_try} try{bcolors.ENDC}')
        upload_video(song,
                     channel=channel,
                     title=generate_title(song),
                     description=generate_desc(song),

                     tags=generate_tags(song),
                     category='Music')
    except ConnectionResetError as e:
        upload_try += 1
        print('An existing connection was forcibly closed by the remote host')
        up_vid()
for song_path in songs:
    song = Song(song_path)
    # get_lyrics(song)
    # map_lyrics(song)
    # adjust_lyrics(song)
    # create_aep(song, backgrounds_dir / 'happy.jpg', '#519dc9')
    render_aep(song)
    up_vid()



