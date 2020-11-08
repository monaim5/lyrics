from pathlib import Path

root = Path('../').resolve()
songs_dir = root / 'songs'
videos_dir = root / 'videos'
backgrounds_dir = root / 'backgrounds'
lyrics_dir = root / 'lyrics'
aep_temp_dir = root / 'assets/aep/temp'
test_dir = root / 'test'


chrome_binary = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
chrome_driver = 'chromedriver.exe'
afterfx_com = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/afterfx.com'
aerender = 'c:/Program Files/Adobe/Adobe After Effects CS6/Support Files/aerender.exe'

json_bridge = root / 'assets/bridge.json'
json_uploaded_to_lyrics = root / 'assets/uploaded_to_lyrics.json'

lyrics_script_path = root / 'assets/aep/scripts/to_lyrics.jsx'

# must be in database
lyrics_yt_credentials = root / 'assets/credentials/lyrics_yt_credentials.json'
lyrics_client_secrets = root / 'assets/credentials/lyrics_client_secrets.json'
