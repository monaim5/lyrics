import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib import request, parse

import requests
from models import Song
from models2 import MapLyrics, Background, AEP, Video, UploadedVideo
from paths import Dir, File, Binary
from youtube_upload.main import main as yt_main

from utils import Bcolors


def effects(shadow, stroke, glass):
    return {'shadow': shadow,
            'stroke': stroke,
            'glass': glass}


def download_background(background):
    assert len(background.url) > 40
    background.path = (Dir.backgrounds_dir.value / background.url[-50:-4]).with_suffix('.jpg')
    if background.file_exists:
        return background

    def get_bg_from_wallpaperflare():
        res = requests.get(background.url, stream=True)
        with open(background.path, 'wb') as out_file:
            shutil.copyfileobj(res.raw, out_file)
        return background

    def get_bg_from_reddit():
        request.urlretrieve(background.url, background.path)
        return background

    def get_bg_from_pexels():
        id_ = re.search(r'(.*)-(?P<id>[0-9]+)/', background.url)
        url_ = 'https://www.pexels.com/photo/%s/download' % id_.group('id')
        opener = request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        request.install_opener(opener)
        request.urlretrieve(url_, background.path)
        return background

    def get_bg_from_500px():
        payload = {'url': background.url}
        payload = parse.urlencode(payload).encode()
        res = request.urlopen("https://www.500pxdownload.com/pix.php", data=payload)

        encoding = res.info().get_param('charset', 'utf8')
        html = res.read().decode(encoding)

        result = re.search(r'src=\'(?P<lien>data:image/(?P<ext>.*);base(.|\n)*)\'( )*/>', html)

        img = request.urlopen(result.group('lien'))
        with open(background.path, 'wb') as f:
            f.write(img.file.read())

        return background

    def main():
        if 'i.redd.it' in background.url:
            return get_bg_from_reddit()
        elif '500px' in background.url:
            return get_bg_from_500px()
        elif 'pexels' in background.url:
            return get_bg_from_pexels()
        elif 'wallpaperflare' in background.url:
            return get_bg_from_wallpaperflare()
        else:
            return False

    background.downloaded = True
    return main()


def create_aep(song: Song, map_lyrics: MapLyrics, background: Background, color):
    aep = AEP(song, map_lyrics, background, color)
    if aep.file_exists:
        return aep

    content = {
        'aep_path': aep.path.__str__(),
        'song_path': song.path.__str__(),
        'background_path': background.path.__str__(),
        'lyrics_map_path': map_lyrics.path.__str__(),
        'template_path': aep.template_path.__str__(),
        'color': color,
        'offset_time': 0.12,  # 0.2
        'max_fade_duration': 0.7,
        'effects': {'arabic_text': effects(shadow={'color': [0, 0, 0], 'animation': False},
                                           stroke={'color': [0, 0, 0], 'width': 3},
                                           glass={'color': [255, 5, 18]}),

                    'english_text': effects(shadow={'color': [0, 0, 0], 'animation': False},
                                            stroke={'color': [0, 0, 0], 'width': 3},
                                            glass={'color': [255, 5, 18]}),

                    'logo': effects(shadow=False,
                                    stroke=False,
                                    glass={'color': [255, 5, 18]})}
    }

    with open(File.json_bridge.value, 'w+') as f:
        json.dump(content, f, sort_keys=True, indent=2)
    # script = r'C:\Users\mon\Documents\lyrics\assets\AEP\scripts\to_lyrics.jsx'
    subprocess.call([Binary.afterfx_com.value, '-r', File.lyrics_script_path.value.resolve().__str__()])
    return aep


def render_aep(aep: AEP):
    video = Video(aep)
    if video.file_exists:
        return video

    print(aep.path)
    print(video.path)
    subprocess.call([
        Binary.aerender.value,
        # '-project', f'"{aep_path}"',
        '-project', f'"{aep.path}"',
        '-OMtemplate', 'H.264',
        '-comp', 'Comp',
        # '-output', r'"C:\Users\mon\Documents\lyrics\assets\AEP\temp\UnknownBrain.mp4"'
        '-output', f'"{video.path}"'
    ])


def upload_video(video: Video, channel, **kwargs):
    # edited the youtube_upload.main.run_main and youtube_upload.main.main
    # by adding (video_ids: list) for return it at the end, by the main function

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

    uploaded_video = UploadedVideo(video, channel)
    arguments = []

    for arg in kwargs:
        arguments.append(f'--{arg.replace("_", "-")}={kwargs.get(arg)}')
    arguments.extend((f'--client-secrets={channel.client_secrets}',
                      f'--credentials-file={channel.yt_credentials}',
                      f'--category={channel.category}'))
    arguments.append(video.path.__str__())

    uploaded_video.published_date = kwargs['publish_at'] if kwargs['publish_at'] is not None else datetime.now()

    upload_try = 1
    while upload_try <= 3:
        try:
            print(f'{Bcolors.WARNING.value}{Bcolors.BOLD.value}the {upload_try} try{Bcolors.ENDC.value}')
            uploaded_video.yt_video_id = yt_main(arguments)[0]
            add_to_uploaded_to_lyrics(uploaded_video)
            return uploaded_video

        except ConnectionResetError as e:
            upload_try += 1
            print(f'try {upload_try} {e.__class__} : {e}')

    raise ConnectionResetError


def add_to_uploaded_to_lyrics(uploaded_video: UploadedVideo):
    original_song = uploaded_video.video.aep.map_lyrics.lyrics.song.id
    with open(File.json_uploaded_to_lyrics.value) as f:
        videos = json.load(f)
    videos.append({
        'original': original_song.id,
        'lyrics': uploaded_video.yt_video_id,
        'title': original_song.title
    })
    with open(File.json_uploaded_to_lyrics.value, 'w') as f:
        json.dump(videos, f, sort_keys=True, indent=2)


def generate_title(song):
    if re.search('\[.*\]', song.title):
        t = re.sub('\[.*\]', '[Arabic Lyrics] اغنية حماسية مترجمة', song.title)
    else:
        t = song.title + ' [Arabic Lyrics] اغنية حماسية مترجمة'
    return t


def generate_tags(song):
    original_tags = song.tags
    original_tags = original_tags.split(',') if song.tags is not None else []
    additional_tags = ['"ncs arabi"', '"أغاني انجليزية مترجمة"', '"كلمات مترجمة"', '"كلمات انجليزية"',
                       '"أغاني انجليزية ومعناها بالعربي"', '"تعلم انجليزية"', '"تعلم الانجليزية بالأغاني"',
                       '"NCS lyrics"', '"اغاني انجليزية سهلة الحفظ للاطفال"', '"اغاني انجليزية حماسية"', '"مترجم"',
                       '"ncs"', '"اغنية حماسية اجنبية 2020"', '"اغاني انجليزية مشهورة 2020"',
                       '"اغاني انجليزية مشهورة"', '"اغاني انجليزية لتعلم اللغة"']
    tags = ','.join(additional_tags)

    for tag in original_tags:
        if len(tags.replace('"', '')) + len(tag) < 400:
            tags += ',' + tag.strip()

    return tags


def generate_desc(song):
    try:
        credit = '\nCredit:\n%s' % song.credit.replace(r'\n', '\n')
    except Exception:
        credit = ''

    desc = 'أغنية حماسية مترجمة ضع السماعات و إستمتع بالحماس و أنت فاهم الكلمات باللغة العربية و في نفس الوقت تعلم بعض الكلمات الإنجليزية\n' \
           '\nإن اعجبك الفيديو لا تنسي الاعجاب والاشتراك بالقناة وتفعيل زر الجرس ليصلك كل ما هو جديد\n\n' \
           'حسابنا على الإنستجرام:' + 'https://www.instagram.com/ncsarab' + '\n' \
                                                                            'حسابنا على الفايسبوك:' + 'https://www.facebook.com/ncs.arabi' + '\n\n' + \
           generate_title(song) + credit + '\n\nنورتو قناة حبايبي شكرا لكم جميعا يا رفاق على دعمكم' \
                                           '\n#أغاني_مترجمة #أغاني_حماسية #أغاني_غربية'

    return desc
