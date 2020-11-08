import datetime
from pathlib import Path

from paths import lyrics_dir, aep_temp_dir, videos_dir, lyrics_client_secrets, lyrics_yt_credentials
from config import Database

db = Database('ncs_arabi')


class Song(object):
    def __init__(self, song_path: Path, lyrics_path: Path = None):
        # self.id = input('This song\'s id is : ')
        self.path = song_path
        self.title = self.path.stem
        self._lyrics_path = lyrics_path
        self.lyrics_dir = lyrics_dir / self.title
        # self.save()

    @property
    def lyrics_path(self):
        if not self.lyrics_dir.exists():
            self.lyrics_dir.mkdir()
        return lyrics_dir / self.title / 'lyrics.json' if self._lyrics_path is None else self._lyrics_path

    @property
    def lyrics_map_path(self):
        return lyrics_dir / self.title / 'lyrics_map.json'

    @property
    def video_path(self):
        return videos_dir / (self.title + '.mp4')

    @property
    def aep_path(self):
        return aep_temp_dir / (self.title + ' [lyrics].aep')

    @property
    def has_video(self):
        return bool(self.video_path.stat().st_size) if self.video_path.exists() else False

    @property
    def has_aep(self):
        return self.aep_path.exists()

    def save(self):
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO ')


class Channel:
    def __init__(self, name):
        self.name = name
        self.yt_credentials = lyrics_yt_credentials
        self.client_secrets = lyrics_client_secrets
        self.category = 'Music'
        self.publish_time = datetime.time(15, 0, 0)
        self.publish_days = {1, 3, 5}

    @property
    def latest_published_date(self) -> datetime:
        cur = db.get_connection().cursor()
        return cur.execute('SELECT max(publish_date) as date FROM `uploaded_to_lyrics`'
                           'where channel_name = ?', (self.name,)).fetchone()[0]

    def next_publish_date(self):
        def get_days_ahead_from_to(date: datetime, weekday: int):
            days_ahead = weekday - date.weekday()
            return days_ahead if days_ahead >= 0 else 6 + days_ahead

        def get_publish_date_according_to(date: datetime):
            days_ahead = min([get_days_ahead_from_to(date, days) for days in self.publish_days])
            return date + datetime.timedelta(days=days_ahead)

        today = datetime.datetime.now()
        today = today.date() if today.time() < self.publish_time else today.date() + datetime.timedelta(days=1)

        if self.latest_published_date is None or self.latest_published_date < get_publish_date_according_to(today):
            publish_at = datetime.datetime.combine(get_publish_date_according_to(today), self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)
        else:
            publish_at = datetime.datetime.combine(get_publish_date_according_to(self.latest_published_date),
                                                   self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)

        return publish_at
