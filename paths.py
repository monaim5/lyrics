from enum import Enum
from pathlib import Path


class Dir(Enum):
    root = Path(__file__).resolve().parent.parent
    songs_dir = root / 'songs'
    videos_dir = root / 'videos'
    backgrounds_dir = root / 'backgrounds'
    lyrics_dir = root / 'lyrics'
    aep_temp_dir = root / 'assets/aep/temp'
    test_dir = root / 'test'


class Binary(Enum):
    sqlite_db = Dir.root.value / 'databases/ncs_arabi.db'
    chrome_binary = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    chrome_driver = 'chromedriver.exe'
    afterfx_com = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/afterfx.com'
    aerender = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/aerender.exe'


class File(Enum):
    json_bridge = Dir.root.value / 'assets/bridge.json'
    json_uploaded_to_lyrics = Dir.root.value / 'assets/uploaded_to_lyrics.json'

    lyrics_script_path = Dir.root.value / 'assets/aep/scripts/to_lyrics.jsx'

    # must be in database
    lyrics_yt_credentials = Dir.root.value / 'assets/credentials/lyrics_yt_credentials.json'
    lyrics_client_secrets = Dir.root.value / 'assets/credentials/lyrics_client_secrets.json'


class Other(Enum):
    lyrics_template = Dir.root.value / 'assets/AEP/templates/to_lyrics.aep'
