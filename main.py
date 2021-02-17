import traceback
from datetime import datetime
from multiprocessing import Process, Condition, Queue

from background.utils import download_background
from lyrics.lyrics import get_lyrics, map_lyrics, adjust_lyrics
from models import get_session, Song, Background, Lyrics, AEP, MapLyrics, RenderQueue, Channel, UploadQueue, Video
from paths import File
from utils import download_song, Color
from video.utils import *
from song.utils import download_song
import logging

from video.utils import comment_to_origin, generate_comment_from_lyrics
from youtube_utils import get_top_commentators

logging.basicConfig(filename=File.log_file.value, level=logging.INFO)


def register_songs_process(session, song_urls):
    """adding songs to database. songs located in songs directory
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    """
    added_songs = 0
    for song_id in song_urls:
        song = Song(song_id)
        if song.exists_in_db(session):
            continue
        song.add(session, commit=True)
        added_songs += 1
    print(f'{added_songs} song has been added to database')


def download_songs_process(session):
    songs = session.query(Song).filter_by(downloaded=False).all()
    for song in songs:
        download_song(song).add(session, commit=True)


def register_backgrounds_process(session, background_urls):
    backgrounds_added = 0

    for url in background_urls:
        background = Background(url)
        if background.exists_in_db(session, url=background.url):
            continue
        background.add(session, commit=True)
        backgrounds_added += 1
    print(f'{backgrounds_added} background has been added to database')


def download_backgrounds_process(session):
    backgrounds = session.query(Background).filter_by(downloaded=False).all()
    for bg in backgrounds:
        download_background(bg).add(session, commit=True)


def get_lyrics_process(session):
    print('get lyrics process')
    sub_query = session.query(Lyrics.song_id)
    songs = session.query(Song).filter(~Song.id.in_(sub_query)).all()
    for song in songs:
        lyrics = get_lyrics(song)
        lyrics.add(session, commit=True)


def register_map_lyrics_process(session):
    lyrics_list = session.query(Lyrics).filter(Lyrics.archived == 0) \
        .filter(Lyrics.id.notin_(session.query(MapLyrics.id))).all()
    for lyrics in lyrics_list:
        MapLyrics(lyrics).add(session, commit=True)


def map_lyrics_process(session):
    lyrics_list = session.query(Lyrics).filter(Lyrics.archived == 0).all()

    for lyrics in lyrics_list:
        map_lyrics_ = map_lyrics(lyrics)
        # adjust_lyrics(map_lyrics_)


def register_aeps_process(session):
    lyrics_havnt_aep = session.query(Lyrics).filter(Lyrics.id.notin_(session.query(AEP.lyrics_id))).all()
    backgrounds = session.query(Background).filter(Background.archived == 0) \
        .filter(Background.id.notin_(session.query(AEP.background_id))).all()
    for lyrics, background in zip(lyrics_havnt_aep, backgrounds):
        color = Color.YELLOW.value
        aep = AEP(lyrics, background, color)
        aep.add(session, commit=True)


def create_aeps_process(session, channel):
    """
    creating adobe after effects projects (aep)
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    :param channel: the channel which we want to upload the video and get top commentators
    """
    print('creating aeps process')
    aeps1 = session.query(AEP).filter(AEP.archived == 0).all()
    aeps2 = session.query(AEP).filter(AEP.archived == 1).filter(AEP.id.notin_(session.query(Video.aep_id))).all()

    for aep in aeps2 + aeps1:
        # TODO: maybe it s better to add channel to aep model
        top_commentators = get_top_commentators(channel, 3)
        aep = create_aep(aep, top_commentators)
        RenderQueue(aep).add(session, commit=True, id=aep.id)


def render_aeps_process(session, queue: Queue, condition: Condition):
    """
    rendering adobe after effects projects (aep) and adding rendered videos to upload queue
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    :param queue: The upload queue that used by the func upload_video_process it contains videos.
    :type queue: multiprocessing.Queue
    :param condition: by this param we can resumed upload process (separate process)
                      which may be waiting for videos to add to upload queue
    :type condition: multiprocessing.Condition
    1 - get render queue from database
    2 - render aep and export it into videos folder as an .mp4 file
    3 - add rendered video to database
    4 - add it to upload_queue table in database
    5 - delete his corresponding item in render queue
    6 - add it to the local upload_queue
    7 - notify the upload queue process that we added a video into his queue
    """
    render_queue_items = session.query(RenderQueue).all()
    channel = session.query(Channel).filter(Channel.name == 'ncs arabi').one()
    print(f'{len(render_queue_items)} item in render queue')
    for item in render_queue_items:
        video = render_aep(item.aep)
        video.add(session, flush=True)
        aep = video.aep
        lyrics = aep.lyrics

        aep.archive(session, flush=True)
        lyrics.archive(session, flush=True)
        aep.background.archive(session, flush=True)
        lyrics.song.archive(session, flush=True)

        upload_queue_item = UploadQueue(video, channel)
        upload_queue_item.add(session, flush=True)
        print(f'render complete for video {video.path}')
        item.delete(session, commit=True)
        queue.put(upload_queue_item)
        with condition:
            condition.notify_all()


def upload_video_process(upload_queue: Queue, condition: Condition):
    """Upload videos in queue one by one
    :param upload_queue: The queue which we will use for uploading videos
    :type upload_queue: multiprocessing.Queue
    :param condition: this param Condition we will use it for make the upload process
                      wait if there is no more videos in queue
                      or resume it after we added videos to queue, where it was waiting
    :type condition: multiprocessing.Condition
    """
    video_index = 1
    with get_session() as session:
        while True:
            if upload_queue.empty():
                with condition:
                    print('waiting for videos to upload')
                    condition.wait()

            upload_queue_item = upload_queue.get()
            if upload_queue_item in (True, False):
                print('upload videos done')
                if upload_queue_item:
                    print('shuting down PC ...')
                    import os
                    os.system('shutdown -s')
                return
            upload_queue_item = session.merge(upload_queue_item)
            video, channel = upload_queue_item.video, upload_queue_item.channel
            try:
                print(f'uploading the {video_index} video : {video.path}')
                song = video.aep.lyrics.song
                uploaded_video = upload_video(video, channel,
                                              title=generate_title(song.title),
                                              description=generate_desc(song.title, song.credit),
                                              tags=generate_tags(song.title, song.tags),
                                              publish_at=channel.next_publish_date(session))
                try:
                    comment_to_origin(channel.token_path,
                                      generate_comment_from_lyrics(song.lyrics.path),
                                      song.id)
                except Exception as e:
                    print(e.__class__)
                    print(e)

                uploaded_video.add(session=session, commit=True)
                video.archive(session, flush=True)
                upload_queue_item.delete(session, commit=True)
                video_index += 1
            except ConnectionResetError as e:
                print(e.__class__)
                print(e)


def main():
    queue = Queue()
    condition = Condition()
    songs_urls = []
    backgrounds_urls = []

    # TODO add url validation for both songss and background urls
    while (url := input('enter music url : ')) != '':
        songs_urls.append(url)
    while (bg := input('enter background url : ')) != '':
        backgrounds_urls.append(bg)

    with get_session() as session:
        uploading_process = Process(target=upload_video_process, args=(queue, condition))
        upload_queue = session.query(UploadQueue).all()
        channel = session.query(Channel).filter(Channel.name == 'ncs arabi').one()
        for item in upload_queue:
            queue.put(item)
        if input('parallel videos upload? (y, n) (default n) : ') == 'y':
            uploading_process.start()
        shutdown = input('shutdown pc at the end of process? (y, n) (default n)') in ('y', 'yes')

        try:
            register_backgrounds_process(session, backgrounds_urls)
            download_backgrounds_process(session)
            register_songs_process(session, songs_urls)
            download_songs_process(session)

            get_lyrics_process(session)
            register_map_lyrics_process(session)
            map_lyrics_process(session)

            register_aeps_process(session)
            create_aeps_process(session, channel)
            render_aeps_process(session=session, queue=queue, condition=condition)

        finally:
            queue.put(shutdown)
            with condition:
                condition.notify_all()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        logging.exception(f'\n--------- An exception was raised :: {datetime.now.__str__()} ----------')
