import json
import re
import shutil
import subprocess
from urllib import request, parse

import requests
from models import Song
from models2 import MapLyrics, Background, AEP
from paths import Dir, File, Binary
from youtube_upload.main import main as yt_main


def effects(shadow, stroke, glass):
    return {'shadow': shadow,
            'stroke': stroke,
            'glass': glass}


def download_background(background):
    background.path = (Dir.backgrounds_dir.value / background.url[-50:-4]).with_suffix('.jpg')

    def get_bg_from_wallpaperflare():
        res = requests.get(background.url, stream=True)
        with open(background.path, 'wb') as out_file:
            shutil.copyfileobj(res.raw, out_file)
        print(background)
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

    return main()


def create_aep(song: Song, map_lyrics: MapLyrics, background: Background, color):
    aep = AEP(song, map_lyrics, background, color)
    if aep.file_exists:
        return aep

    payload = []
    content = {
        'title': map_lyrics.title,
        'song_path': song.path.resolve().__str__(),
        'background_path': background.path.resolve().__str__(),
        'lyrics_map_path': map_lyrics.path.resolve().__str__(),
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
    payload.append(content)

    with open(File.json_bridge.value, 'w+') as f:
        json.dump(payload, f, sort_keys=True, indent=2)
    # script = r'C:\Users\mon\Documents\lyrics\assets\AEP\scripts\to_lyrics.jsx'
    print(File.lyrics_script_path.value.resolve().__str__())
    subprocess.call([Binary.afterfx_com.value, '-r', File.lyrics_script_path.value.resolve().__str__()])
    return aep


def render_aep(song: Song):
    if song.has_video:
        return True

    print(song.video_path)
    subprocess.call(
        [Binary.aerender.value,
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

    with open(File.json_uploaded_to_lyrics.value) as f:
        videos = json.load(f)
    videos.append({
        'original': '',
        'lyrics': video_ids[0],
        'title': song.title
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
