import re
import shutil
from urllib import request, parse
from urllib.request import urlopen

import requests

from paths import Dir


def download_background(background):
    if background.path is None:
        assert len(background.url) > 40
        background.path = (Dir.backgrounds_dir.value / background.url[-50:-4]).with_suffix('.jpg')
    if background.file_exists:
        return background

    def get_bg_from_wallpaperflare():
        res = requests.get(background.url, stream=True)
        with open(background.path, 'wb') as out_file:
            shutil.copyfileobj(res.raw, out_file)
        return background

    def get_bg_by_urlretrieve():

        response = urlopen(background.url)
        image_type = response.info().get_content_type()
        image_type = re.search('image/(.*)', image_type).group(1)
        ext = '.' + ('jpg' if image_type == 'jpeg' else image_type)
        background.path = background.path.with_suffix(ext)

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
        if '500px' in background.url:
            return get_bg_from_500px()
        elif 'pexels' in background.url:
            return get_bg_from_pexels()
        elif 'wallpaperflare' in background.url:
            return get_bg_from_wallpaperflare()
        else:
            return get_bg_by_urlretrieve()

    background.downloaded = True
    return main()