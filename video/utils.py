import json
import subprocess
from models import Song
from paths import json_bridge, afterfx_com, lyrics_script_path, aerender
from youtube_upload.main import main as yt_main


def create_aep(song: Song, background_path, color):
    if song.has_aep:
        return True

    payload = []
    content = {
        'title': song.title,
        'song_path': song.path.resolve().__str__(),
        'background_path': background_path.resolve().__str__(),
        'lyrics_map_path': song.lyrics_map_path.resolve().__str__(),
        'color': color
    }
    payload.append(content)

    with open(json_bridge, 'w+') as f:
        json.dump(payload, f, sort_keys=True, indent=2)
    # script = r'C:\Users\mon\Documents\lyrics\assets\AEP\scripts\to_lyrics.jsx'
    print(lyrics_script_path.resolve().__str__())
    subprocess.call([afterfx_com, '-r', lyrics_script_path.resolve().__str__()])
    return True


def render_aep(song: Song):
    if song.has_video:
        return True

    print(song.video_path)
    subprocess.call(
        [aerender,
         '-project', song.aep_path.resolve().__str__(),
         '-OMtemplate', 'H.264',
         '-comp', 'Comp',
         '-output', song.video_path.resolve().__str__(),
         ])


def upload_video(song, channel, **kwargs):
    # arguments = [
    #     '--title=%s' % title,
    #     '--description=%s' % description,
    #     '--category=Music',
    #     '--tags=%s' % tags,
    #     '--publish-at=%s' % publish_at,
    #     '--client-secrets=%s' % self.client_secrets,
    #     '--credentials-file=%s' % self.yt_credentials,
    #     video_path
    # ]
    arguments = []
    for arg in kwargs:
        arguments.append(f'--{arg.replace("_", "-")}={kwargs.get(arg)}')
    arguments.extend((f'--client-secrets={channel.client_secrets}',
                      f'--credentials-file={channel.yt_credentials}',
                      f'--publish-at={channel.next_publish_date()}'))
    arguments.append(song.video_path.__str__())

    video_ids = yt_main(arguments)
    print(video_ids)
    song.add_to_uploaded()


