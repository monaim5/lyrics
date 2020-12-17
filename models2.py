import datetime
import re
import shutil
from ast import literal_eval, parse
from pathlib import Path
from enum import Enum as NativeEnum
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, Date, Time, func, Enum
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound

from paths import Dir, File, Binary, Other

# from config import Config, Color
# from mutagen.mp3 import MP3

Base = declarative_base()
engine = create_engine(f'sqlite:///{Binary.sqlite_db.value}')

__all__ = [
    'get_session',
    'Song',
    'Lyrics',
    'MapLyrics',
    'AEP',
    'RenderQueue',
    'Video',
    'UploadQueue',
    'UploadedVideo',
    'Channel',
    'Background'
]


class WeekDays(NativeEnum):
    mon = 0
    tue = 1
    wed = 2
    thu = 3
    fri = 4
    sat = 5
    sun = 6


class get_session:
    def __enter__(self) -> Session:
        self.session = sessionmaker(bind=engine, expire_on_commit=True)()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()


#
# def get_mp3_duration(path):
#     audio = MP3(path)
#     return audio.info.length


class MyBase:

    def add(self, session, *, flush=False, commit=False, expire=False):
        # try:
        session.add(self)
        if flush:
            session.flush()
        if commit:
            session.commit()
        if expire:
            session.expire(self)
        # except IntegrityError as e:
        #     duplicated_field = re.search('^.*\.(.*)', str(e.orig))[1]
        #     session.refresh()
        #     # print(duplicated_field)

    def add_or_update(self, session, *, flush=False, commit=False, expire=False):
        session._save_or_update_impl(self)

    def delete(self, session, *, flush=False, commit=False):
        session.delete(self)
        if flush:
            session.flush()
        if commit:
            session.commit()

    @classmethod
    def select(cls, session, id_):
        return session.query(cls).filter_by(id=id_).one()

    def archive(self, session):
        new_path = self.path.parent / 'archive' / self.path.name
        try:
            shutil.move(self.path, new_path)
            self.path = new_path
            session.commit()
        except FileNotFoundError:
            print('file not found maybe it was archived already')
            return

    def exists_in_db(self, **kwargs):
        if kwargs:
            fields = kwargs
        else:
            fields = {'id': self.id}
        with get_session() as session:
            return session.query(self.__class__).filter_by(**fields).scalar()

    @property
    def file_exists(self):
        return bool(self.path.stat().st_size) if self.path is not None and self.path.exists() else False

    def __str__(self):
        return '\n'.join([f'{a} : {getattr(self, a)}' for a in dir(self)
                          if not a.startswith('_') and
                          not callable(getattr(self, a)) and
                          a != 'metadata'])


class Background(Base, MyBase):
    __tablename__ = 'backgrounds'
    id = Column('id', Integer, primary_key=True)
    url = Column('url', String, unique=True)
    filename = Column('filename', String)
    __path = Column('path', String)

    aep = relationship("AEP")

    def __init__(self, url):
        self.url = url
        self.filename = None
        self.path = None

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path if self.__path is not None else None

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__() if value is not None else None
        self.filename = self.path.stem if self.path is not None else None
    # @property
    # def path(self) -> Path:
    #     return Dir.root.value / self.__path
    #
    # @path.setter
    # def path(self, value: Path):
    #     self.__path = value.relative_to(Dir.root.value).__str__()
    #
    # def exists(self):
    #     with get_session() as session:
    #         return session.query(Background).filter(Background.title == self.title).scalar()

def get_yt_id(url):
    match = re.search(r"youtube\.com/.*v=([^&]*)", url)
    if match:
        return match.group(1)
    else:
        raise Exception('no id in url')


class Song(Base, MyBase):
    __tablename__ = 'songs'
    id = Column('id', String, primary_key=True)
    url = Column('url', String)
    title = Column('title', String)
    filename = Column('filename', String)
    tags = Column('tags', String)
    credit = Column('credit', String)
    __path = Column('path', String)
    # duration = Column('duration', Numeric)

    lyrics = relationship("Lyrics", uselist=False)

    def __init__(self, url):
        self.url = url
        self.id = get_yt_id(url)
        self.title = None
        self.path = None
        self.description = None
        self.credit = None

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path if self.__path is not None else None

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__() if value is not None else None
        self.filename = self.path.stem if self.path is not None else None


class Lyrics(Base, MyBase):
    __tablename__ = 'lyrics'
    id = Column('id', Integer, primary_key=True)
    song_id = Column(String, ForeignKey('songs.id'))
    title = Column('title', String)
    __path = Column('path', String)

    song = relationship("Song", uselist=False)
    map_lyrics = relationship("MapLyrics", uselist=False)

    def __init__(self, song: Song):
        self.title = f'{song.title} [lyrics]'
        self.song_id = song.id
        self.path = Dir.lyrics_dir.value / self.title / 'lyrics.json'

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    # @property
    # def path(self):
    #     return Dir.root.value / self.__path
    #
    # @path.setter
    # def path(self, value: Path):
    #     self.__path = value.relative_to(Dir.root.value).__str__()

    # @property
    # def flp_path(self) -> Path:
    #     return Dir.root.value / self.__flp_path
    #
    # @flp_path.setter
    # def flp_path(self, value: Path):
    #     self.__flp_path = value.relative_to(Dir.root.value).__str__()

    def exists(self):
        return bool(self.path.stat().st_size) if self.path.exists() else False


class MapLyrics(Base, MyBase):
    __tablename__ = 'map_lyrics'
    id = Column('id', Integer, primary_key=True)
    lyrics_id = Column(Integer, ForeignKey('lyrics.id'))
    title = Column('title', String)
    __path = Column('path', String)

    lyrics = relationship('Lyrics', uselist=False)
    aep = relationship('AEP', uselist=False)

    def __init__(self, lyrics: Lyrics):
        self.title = f'{lyrics.title} [Maplyrics]'
        self.lyrics_id = lyrics.id
        self.path = lyrics.path.parent / 'map_lyrics.json'

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()


class AEP(Base, MyBase):
    __tablename__ = 'aeps'
    id = Column('id', Integer, primary_key=True)
    song_id = Column(String, ForeignKey('songs.id'))
    background_id = Column(Integer, ForeignKey('backgrounds.id'))
    map_lyrics_id = Column(Integer, ForeignKey('map_lyrics.id'))
    # color = Column('color', Enum(Color))
    __path = Column('path', String)
    __template_path = Column('template_path', String)

    song = relationship("Song", uselist=False)
    background = relationship("Background", uselist=False)
    map_lyrics = relationship("MapLyrics", uselist=False)
    video = relationship("Video", uselist=False)
    render_queue_item = relationship("RenderQueue", uselist=False)

    def __init__(self, song: Song, map_lyrics: MapLyrics, background: Background, color):
        self.song_id = song.id
        self.map_lyrics_id = map_lyrics.id
        self.background_id = background.id
        self.color = color
        self.path = Dir.aep_temp_dir.value / (song.filename + '.aep')
        self.template_path = Other.lyrics_template.value

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    # @property
    # def path(self) -> Path:
    #     return Dir.root.value / self.__path
    #
    # @path.setter
    # def path(self, value: Path):
    #     self.__path = value.relative_to(Dir.root.value).__str__()

    @property
    def template_path(self) -> Path:
        return Dir.root.value / self.__template_path

    @template_path.setter
    def template_path(self, value: Path):
        self.__template_path = value.relative_to(Dir.root.value).__str__()


class RenderQueue(Base, MyBase):
    __tablename__ = 'render_queue'
    id = Column('id', Integer, primary_key=True)
    aep_id = Column(Integer, ForeignKey('aeps.id'))
    # priority = Column('priority', Integer)
    # added_date = Column('added_date', Date)
    aep = relationship("AEP", uselist=False)

    def __init__(self, aep: AEP):
        self.aep_id = aep.id


class Video(Base, MyBase):
    __tablename__ = 'videos'
    id = Column('id', Integer, primary_key=True)
    title = Column('title', String)
    aep_id = Column(Integer, ForeignKey('aeps.id'))
    __path = Column('path', String)

    aep = relationship("AEP", uselist=False)
    upload_queue_item = relationship("UploadQueue", uselist=False)
    uploaded_video = relationship("UploadedVideo", uselist=False)

    def __init__(self, aep):
        self.aep_id = aep.id
        self.path = Dir.videos.value / (aep.song.filename + '.mp4')
        self.title = aep.song.title

    @property
    def path(self) -> Path:
        return Dir.root.value / self.__path

    @path.setter
    def path(self, value: Path):
        self.__path = value.relative_to(Dir.root.value).__str__()

    # @property
    # def path(self):
    #     return Dir.root.value / self.__path
    #
    # @path.setter
    # def path(self, value: Path):
    #     self.__path = value.relative_to(Dir.root.value).__str__()
    #
    def exists(self):
        return bool(self.path.stat().st_size) if self.path.exists() else False


class Channel(Base, MyBase):
    __tablename__ = 'channels'
    id = Column('id', Integer, primary_key=True)
    yt_channel_id = Column('yt_channel_id', String)
    name = Column('name', String)
    __yt_credentials = Column('yt_credentials', String)
    __client_secrets = Column('client_secrets', String)
    category = Column('category', String)
    publish_time = Column('publish_time', Time)
    __publish_days = Column('publish_days', String)

    uploaded_videos = relationship("UploadedVideo")
    upload_queue_items = relationship("UploadQueue")

    def __init__(self, name, channel_id, yt_credentials, client_secrets):
        self.name = name
        self.yt_channel_id = channel_id
        self.yt_credentials = yt_credentials
        self.client_secrets = client_secrets
        self.category = 'Music'
        self.publish_time = datetime.time(15, 0, 0)
        self.publish_days = [WeekDays.tue.name, WeekDays.thu.name, WeekDays.sat.name]

    @property
    def yt_credentials(self) -> Path:
        return Dir.root.value / self.__yt_credentials

    @yt_credentials.setter
    def yt_credentials(self, value: Path):
        self.__yt_credentials = value.relative_to(Dir.root.value).__str__()

    @property
    def client_secrets(self) -> Path:
        return Dir.root.value / self.__client_secrets

    @client_secrets.setter
    def client_secrets(self, value: Path):
        self.__client_secrets = value.relative_to(Dir.root.value).__str__()

    @property
    def publish_days(self) -> List[WeekDays]:
        return list(map(lambda x: WeekDays.__getitem__(x), literal_eval(self.__publish_days)))

    @publish_days.setter
    def publish_days(self, value: List[WeekDays]):
        self.__publish_days = str(value)

    def latest_published_date(self, session) -> datetime:
        return session.query(func.max(UploadedVideo.published_date)) \
            .filter(UploadedVideo.channel_id == self.id).one()[0]

    def next_publish_date(self, session) -> datetime:
        def get_days_ahead_from_to(date: datetime, weekday: int):
            days_ahead = weekday - date.weekday()
            return days_ahead if days_ahead >= 0 else 6 + days_ahead

        def get_publish_date_according_to(date: datetime):
            publish_days = (day.value for day in self.publish_days)
            days_ahead = min([get_days_ahead_from_to(date, days) for days in publish_days])
            return date + datetime.timedelta(days=days_ahead)

        today = datetime.datetime.now()
        today = today.date() if today.time() < self.publish_time else today.date() + datetime.timedelta(days=1)
        latest_published_date = self.latest_published_date(session)

        if latest_published_date is None or latest_published_date < get_publish_date_according_to(today):
            publish_at = datetime.datetime.combine(get_publish_date_according_to(today), self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)
        else:
            publish_at = datetime.datetime.combine(get_publish_date_according_to(latest_published_date),
                                                   self.publish_time) \
                .replace(tzinfo=datetime.timezone.utc)

        return publish_at


class UploadQueue(Base, MyBase):
    __tablename__ = 'upload_queue'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    channel_id = Column(Integer, ForeignKey('channels.id'))

    video = relationship("Video", uselist=False)
    channel = relationship("Channel", uselist=False)

    def __init__(self, video: Video, channel: Channel):
        self.channel_id = channel.id
        self.video_id = video.id


class UploadedVideo(Base, MyBase):
    __tablename__ = 'uploaded_videos'
    id = Column('id', Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    title = Column('title', String)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    yt_video_id = Column('youtube_id', String)
    published_date = Column('published_date', Date)

    video = relationship("Video", uselist=False)
    channel = relationship("Channel", uselist=False)

    def __init__(self, video, channel):
        self.video_id = video.id
        self.channel_id = channel.id


def migrate():
    Base.metadata.create_all(bind=engine)


def main():
    migrate()
    channel = Channel(
        'ncs arabi',
        'UCLbsLjqzPKBLa7kzlEmfCXA',
        File.lyrics_yt_credentials.value,
        File.lyrics_client_secrets.value
    )
    with get_session() as session:
        session.add(channel)
        session.commit()


if __name__ == '__main__':
    main()