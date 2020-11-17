import json
import re
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
