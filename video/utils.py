import json
import re
import subprocess
from datetime import datetime
from models import AEP, Video, UploadedVideo
from paths import File, Binary
from youtube_upload.main import main as yt_main

from utils import Bcolors

__all__ = [
    'create_aep',
    'render_aep',
    'upload_video',
    'generate_desc',
    'generate_tags',
    'generate_title',
    'comment_to_origin',
    'generate_comment_from_lyrics'
]

from youtube_utils import YoutubeApiManager


def effects(**kwargs):
    return kwargs


def white_theme_text(**kwargs):
    kwargs['font_color'] = [1, 1, 1]
    kwargs['stroke'] = {'color': [0, 0, 0], 'width': 5}
    if 'shadow' not in kwargs:
        kwargs['shadow'] = {'color': [0, 0, 0], 'static': {'direction': 300}, 'animation': False}
    if 'glass' not in kwargs:
        kwargs['glass'] = {'color': [255, 5, 18]}
    return effects(**kwargs)


def black_theme_text(**kwargs):
    kwargs['font_color'] = [0, 0, 0]
    kwargs['stroke'] = {'color': [1, 1, 1], 'width': 5}
    kwargs['shadow'] = False
    if 'glass' not in kwargs:
        kwargs['glass'] = False
    return effects(**kwargs)


def black_theme_logo(**kwargs):
    return effects(shadow=False, stroke=False, glass={'color': [255, 5, 18]}, invert=True, **kwargs)


def white_theme_logo(**kwargs):
    return effects(shadow={'color': [0, 0, 0], 'static': False, 'animation': True},
                   stroke=False, glass={'color': [255, 5, 18]}, invert=False, **kwargs)


def black_them_spectrum(**kwargs):
    return effects(color='#000000', **kwargs)


def white_them_spectrum(**kwargs):
    return effects(**kwargs)


HISTORY_FONTS = [
    ('bader_al-yadawi', 'spacing :5', 'OptimusPrinceps', 68),
    ('VIPRawyRegular', 'spacing :3', 'Amita-Regular', 68),
    ('VIPRawy-Bold', 'spacing: 3')
]


def black_them():
    return {
        'arabic_text': black_theme_text(font='VIPRawy-Bold', spacing=3, font_size=72),
        'latin_text': black_theme_text(font='VIPRawy-Bold', font_size=68),
        'logo': black_theme_logo(),
        'spectrum': black_them_spectrum()
    }


def white_them(spectrum_color, **kwargs):
    return {
        'arabic_text': white_theme_text(font='VIPRawy-Bold', spacing=3, font_size=72,
                                        shadow={'color': [0, 0, 0], 'static': {'direction': 300}, 'animation': False}),
        'latin_text': white_theme_text(font='VIPRawy-Bold', font_size=68,
                                       shadow={'color': [0, 0, 0], 'static': {'direction': 240}, 'animation': False}),
        'logo': white_theme_logo(),
        'spectrum': white_them_spectrum(color=spectrum_color)
    }


def create_aep(aep: AEP, commentators=None):
    # if aep.file_exists:
    #     return aep

    content = {
        'aep_path': aep.path.__str__(),
        'song_path': aep.lyrics.song.path.__str__(),
        'background_path': aep.background.path.__str__(),
        'lyrics_map_path': aep.lyrics.map_lyrics.path.__str__(),
        'template_path': aep.template_path.__str__(),
        'offset_time': 0.35,  # 0.2
        'max_fade_duration': 0.7,
        'effects': white_them(aep.color),
        # 'effects': white_them(),
        'commentators': commentators
    }

    with open(File.json_bridge.value, 'w+', encoding='utf-8') as f:
        json.dump(content, f, sort_keys=True, indent=2, ensure_ascii=False)
    # script = r'C:\Users\mon\Documents\lyrics\assets\AEP\scripts\to_lyrics.jsx'
    subprocess.call([Binary.afterfx_com.value, '-r', aep.script_path])
    return aep


def render_aep(aep: AEP):
    video = Video(aep)
    if video.file_exists:
        return video

    subprocess.call([
        Binary.aerender.value,
        '-project', f'"{aep.path}"',
        '-OMtemplate', 'H.264',
        '-comp', 'Comp',
        '-output', f'"{video.path}"'
    ])
    return video


def upload_video(video: Video, channel, **kwargs):
    # edited the youtube_upload.main.run_main and youtube_upload.main.main
    # by adding (video_ids: list) for return it at the end, by the main function

    arguments = []
    tags = kwargs.pop('tags')
    arguments.append('--tags="' + ','.join(tags) + '"')
    for arg in kwargs:
        if arg == 'publish_at':
            arguments.append('--publish-at=' + kwargs.get(arg).strftime('%Y-%m-%dT%H:%M:%SZ'))
            continue
        arguments.append(f'--{arg.replace("_", "-")}={kwargs.get(arg)}')
    arguments.extend((f'--client-secrets={channel.client_secrets}',
                      f'--credentials-file={channel.yt_credentials}',
                      f'--category={channel.category}'))
    arguments.append(video.path.__str__())

    uploaded_video = UploadedVideo(video, channel)
    uploaded_video.title = kwargs['title']
    uploaded_video.description = kwargs['description']
    uploaded_video.tags = tags
    uploaded_video.published_date = kwargs['publish_at'] if 'publish_at' in kwargs and kwargs['publish_at'] is not None else datetime.now()
    uploaded_video.original_youtube_id = video.aep.lyrics.song.id
    uploaded_video.original_channel_id = video.aep.lyrics.song.channel_id

    upload_try = 1
    while upload_try <= 3:
        try:
            print(arguments)
            print(f'{Bcolors.WARNING.value}{Bcolors.BOLD.value}the {upload_try} try{Bcolors.ENDC.value}')
            uploaded_video.youtube_id = yt_main(arguments)[0]
            uploaded_video.add_to_uploaded_to_lyrics()
            return uploaded_video

        except ConnectionResetError as e:
            upload_try += 1
            print(f'try {upload_try} {e.__class__} : {e}')

    raise ConnectionResetError


def generate_title(title: str):
    if re.search(r'\[.*]', title):
        t = re.sub(r'\[.*]', '[Arabic Lyrics] translated arabic مترجمة بالانجليزي', title)
    else:
        t = title + ' [Arabic Lyrics] translated arabic مترجمة بالانجليزي'
    return t


def generate_tags(title, tags) -> list:
    original_tags = tags if tags is not None else []
    # original_tags = original_tags.split(',') if tags is not None else []
    additional_tags = ['مترجمة بالانجليزي', 'translated arabic', 'مترجمة google', 'تعلم انجليزية',
                       'مترجمة بالعربي', 'Arapça öğren', 'youmusic', 'al maany', 'translate english arabe',
                       'arabickey', 'word arabic', 'darija', 'free copyright music', 'no copyright music']

    new_tags = additional_tags + original_tags
    tags_length = 0
    tag_index = 0
    while tag_index < len(new_tags) and tags_length + len(new_tags[tag_index]) < 400:
        tags_length += len(new_tags[tag_index])
        tag_index += 1

    return new_tags[:tag_index]


def generate_desc(title, credit):
    try:
        credit = '\nCredit:\n%s' % credit.replace(r'\n', '\n')
    except Exception:
        credit = ''

    desc = 'أغنية مترجمة بالانجليزي ضع السماعات و إستمتع بالحماس و أنت فاهم الكلمات باللغة العربية و في نفس الوقت تعلم بعض الكلمات الإنجليزية\n' \
           '\nMusic translated into arabic from english\n\n' \
           '\nإن اعجبك الفيديو لا تنسي الاعجاب والاشتراك بالقناة وتفعيل زر الجرس ليصلك كل ما هو جديد\n\n' \
           'حسابنا على الإنستجرام:' + 'https://www.instagram.com/ncsarab' + '\n' \
                                                                            'حسابنا على الفايسبوك:' + 'https://www.facebook.com/ncs.arabi' + '\n\n' + \
           title + credit + '\n\nنورتو قناة حبايبي شكرا لكم جميعا يا رفاق على دعمكم' \
                            '\n#أغاني_مترجمة #مترجمة_بالانجليزي #أغاني_غربية'

    return desc


def generate_comment_from_lyrics(lyrics_path):
    with open(lyrics_path, encoding='utf-8') as f:
        lyrics = json.load(f)

    ar_lyrics = ''
    en_lyrics = ''
    for line in lyrics:
        ar_lyrics += f'{line["text_ar"]}\n'
        en_lyrics += f'{line["text_en"]}\n'
    comment = "Lyrics: It's available in my channel tho\nالكلمات باللغة العربية أيضا، تعال و شاهدها على قناتي"
    comment += f'\n{en_lyrics}\n\n{ar_lyrics}'
    return comment


def comment_to_origin(token_path, comment, video_id):
    youtube = YoutubeApiManager.api_by_token(token_path)
    request_body = {"snippet": {"videoId": video_id,
                                "topLevelComment": {
                                    "snippet": {
                                        "textOriginal": comment
                                    }}}}

    api_request = youtube.commentThreads().insert(part='snippet', body=request_body)
    api_response = api_request.execute()
    print(api_response)
