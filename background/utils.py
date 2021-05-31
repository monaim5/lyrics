import re
import shutil
from pathlib import Path
from urllib import request, parse
from urllib.request import urlopen

import requests

from paths import Dir


def get_bg_from_wallpaperflare(url, path: Path) -> Path:
    res = requests.get(url, stream=True)
    with open(path, 'wb') as out_file:
        shutil.copyfileobj(res.raw, out_file)
    return path


def get_bg_by_urlretrieve(url, path: Path) -> Path:

    response = urlopen(url)
    image_type = response.info().get_content_type()
    image_type = re.search('image/(.*)', image_type).group(1)
    ext = '.' + ('jpg' if image_type == 'jpeg' else image_type)
    path = path.with_suffix(ext)
    request.urlretrieve(url, path)

    return path


def get_bg_from_pexels(url, path):

    query = url.split('/')[-2 if url.endswith('/') else -1]
    id_ = re.search(r'.*-(?P<id>[0-9]+)$', query).group('id')
    path = (Dir.backgrounds_dir.value / query).with_suffix('.jpg')

    url_ = f'https://www.pexels.com/photo/{id_}/download'
    opener = request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    request.install_opener(opener)

    request.urlretrieve(url_, path)
    return path


def get_bg_from_500px(url, path):
    payload = {'url': url}
    payload = parse.urlencode(payload).encode()
    res = request.urlopen("https://www.500pxdownload.com/pix.php", data=payload)

    encoding = res.info().get_param('charset', 'utf8')
    html = res.read().decode(encoding)

    result = re.search(r'src=\'(?P<lien>data:image/(?P<ext>.*);base(.|\n)*)\'( )*/>', html)

    img = request.urlopen(result.group('lien'))
    with open(path, 'wb') as f:
        f.write(img.file.read())

    return path


def get_bg_from_local(url, path):
    shutil.copy(url, path)
    return path


def download_background(background):
    """parameter must include {url: str, file_exists: bool, path: Path} """

    try:
        if re.match(r'[cCdDeE]:[/\\]', background.url):
            background_path = Dir.backgrounds_dir.value / Path(background.url).name
            background.path = get_bg_from_local(background.url, background_path)

        else:
            background_path = (Dir.backgrounds_dir.value / background.url[-50:-4]).with_suffix('.jpg')

            if '500px' in background.url:
                background.path = get_bg_from_500px(background.url, background_path)

            elif 'pexels' in background.url:
                background.path = get_bg_from_pexels(background.url, background_path)

            elif 'wallpaperflare' in background.url:
                background.path = get_bg_from_wallpaperflare(background.url, background_path)
            else:
                background.path = get_bg_by_urlretrieve(background.url, background_path)

    except Exception:
        raise Exception

    else:
        background.downloaded = True
        return background
