from lyrics.lyrics import get_lyrics, map_lyrics, adjust_lyrics
from video.utils import create_aep, render_aep, upload_video
from models import Song, Channel
from paths import songs_dir, backgrounds_dir

# fix duration in adobe after script (to_lyrics.jsx)
# change file_name to filename
# adapt with background not with bg_ext


songs = songs_dir.glob('*.mp3')
channel = Channel('ncs_arabi')
for song in songs:
    song = Song(song)
    # get_lyrics(song)
    # map_lyrics(song)
    # adjust_lyrics(song)
    create_aep(song, backgrounds_dir / 'love me.jpg', '#7d0800')
    render_aep(song)
    upload_video(song, channel=channel, title=song.title)

