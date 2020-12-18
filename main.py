from multiprocessing import Process, Condition, Queue
from lyrics.lyrics import get_lyrics, map_lyrics, adjust_lyrics
# from song import *
from models2 import get_session, Song, Background, Lyrics, AEP, MapLyrics, RenderQueue, Channel, UploadQueue
from paths import Dir
from utils import download_song
from video.utils import download_background, create_aep, render_aep, upload_video, generate_desc, generate_tags, \
    generate_title


# from models import Song, Channel
# from models2 import Song, Channel
# from paths import songs_dir, backgrounds_dir
# from utils import bcolors, download_song

# fix duration in adobe after script (to_lyrics.jsx)
# change file_name to filename
# adapt with background not with bg_ext
# songs = songs_dir.glob('*.mp3')
# channel = Channel('ncs_arabi')
# with get_session() as session:
#     url = 'https://www.youtube.com/watch?v=ztvIhqVtrrw'
#     song =
#     song = download_song(session, url)
#     lyrics = get_lyrics(session, song)
#     map_lyrics = map_lyrics(session, lyrics, song)
#     print(map_lyrics.id)
#     adjust_lyrics(song, map_lyrics)
#     exit()
# aep = create_aep(song, background, map_lyrics, '#519dc9')
# video = render_aep(aep)
# uploaded_video = upload_video(video)
#
# print(song)
# exit()
#
# def up_vid():
#     upload_try = 1
#     try:
#         print(f'{bcolors.WARNING}{bcolors.BOLD}the {upload_try} try{bcolors.ENDC}')
#         upload_video(song,
#                      channel=channel,
#                      title=generate_title(song),
#                      description=generate_desc(song),
#                      tags=generate_tags(song),
#                      category='Music')
#     except ConnectionResetError as e:
#         upload_try += 1
#         print('An existing connection was forcibly closed by the remote host')
#         up_vid()
#
#
# for song_path in songs:
#     url = 'https://r4.wallpaperflare.com/wallpaper/979/531/766/the-witcher-3-wild-hunt-wallpaper-fb06bc9dc321ef89f5647b09ed2c3c00.jpg'
#
#
#     exit()
#     # song = Song(song_path, )
#     image_path = download_background(url, song.title) if not song.has_background else song.background
#     # get_lyrics(song)
#
#     # map_lyrics(song)
#     # adjust_lyrics(song)
#
#     # create_aep(song, image_path, '#519dc9')
#     render_aep(song)
#     try:
#         up_vid()
#     finally:
#         import os
#         os.system('shutdown -s')


def register_songs_process(session, song_urls):
    """adding songs to database. songs located in songs directory
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    """
    added_songs = 0
    for song_id in song_urls:
        song = Song(song_id)
        if song.exists_in_db():
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
        if background.exists_in_db(url=background.url):
            continue
        background.add(session, commit=True)
        backgrounds_added += 1
    print(f'{backgrounds_added} background has been added to database')


def download_backgrounds_process(session):
    backgrounds = session.query(Background).filter_by(downloaded=False).all()
    for bg in backgrounds:
        download_background(bg).add(session, commit=True)


def map_lyrics_process(session):
    sub_query = session.query(MapLyrics.lyrics_id)
    lyrics_list = session.query(Lyrics).filter(~Lyrics.id.in_(sub_query)).all()

    for lyrics in lyrics_list:
        song = lyrics.song
        map_lyrics(lyrics, song).add(session, commit=True)


def get_lyrics_process(session):
    sub_query = session.query(Lyrics.song_id)
    songs = session.query(Song).filter(~Song.id.in_(sub_query)).all()

    for song in songs:
        get_lyrics(song).add(session, commit=True)


def create_aeps_process(session):
    """
    creating adobe after effects projects (aep) from 8d songs :
    which they have an aep but not rendered as video and not in render queue
        -> [query used : songs_not_in_rq_and_vid]
    which basically have not an aep
        -> [query used : songs_havnt_aep]
    :param session: The current database connection
    :type session: sqlalchemy.orm.session.Session
    """
    # aep_in_rq = session.query(RenderQueue.aep_id)
    # return list of song_ids which the 8d song have aep but not approved
    # aep_rendered = session.query(Video.aep_id)
    # aep_not_in_rq_and_vid = session.query(AEP.song_8d_id).filter(AEP.id.notin_(aep_in_rq)) \
    #                                                      .filter(AEP.id.notin_(aep_rendered))
    # songs_not_in_rq_and_vid = session.query(Song8d).filter(Song8d.id.in_(aep_not_in_rq_and_vid)).all()

    # for song_8d in songs_not_in_rq_and_vid:
    #     create_aep(song_8d, background, color)
    #     RenderQueue(song_8d.aep).add(session, flush=False, commit=True)
    print('creating aeps process')
    aeps = session.query(AEP.map_lyrics_id)
    map_lyrics_havnt_aep = session.query(MapLyrics).filter(MapLyrics.id.notin_(aeps)).all()

    bg_used = session.query(AEP.background_id)
    backgrounds = session.query(Background).filter(Background.id.notin_(bg_used)).all()

    for map_lyrics, background in zip(map_lyrics_havnt_aep, backgrounds):
        color = '#123456'
        song = map_lyrics.lyrics.song
        aep = create_aep(song, map_lyrics, background, color)
        aep.add(session, flush=True)
        RenderQueue(aep).add(session, commit=True)


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
        item.delete(session, flush=True)
        item.aep.background.archive(session)
        item.aep.song_8d.archive(session)
        item.aep.song_8d.song.archive(session)
        item.aep.archive(session)
        upload_queue_item = UploadQueue(video, channel)
        upload_queue_item.add(session, commit=True)
        print(f'render complete for video {video.title}')
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
                    import os
                    os.system('shutdown -s')
                return
            upload_queue_item = session.merge(upload_queue_item)
            video, channel = upload_queue_item.video, upload_queue_item.channel
            try:
                print(f'uploading the {video_index} video : {video.title}')
                uploaded_video = upload_video(video, channel,
                                              title=generate_title(video.title),
                                              description=generate_desc(video.title),
                                              tags=generate_tags(video.title),
                                              publish_at=channel.next_publish_date(session))
                uploaded_video.add(session=session, commit=True)
                session.delete(upload_queue_item)
                session.commit()
                video_index += 1
            except ConnectionResetError as e:
                print(e.__class__)
                print(e)


def main():
    queue = Queue()
    condition = Condition()
    songs_urls = ['https://www.youtube.com/watch?v=Y2Lu0o3S2sU']
    backgrounds_urls = ['https://r4.wallpaperflare.com/wallpaper/610/259/809/women-samurai-katana-artwork-wallpaper-a4aa02025d5e77e2b14042e58602e560.jpg']
    with get_session() as session:
        uploading_process = Process(target=upload_video_process, args=(queue, condition))
        upload_queue = session.query(UploadQueue).all()

        for item in upload_queue:
            queue.put(item)
        if input('parallel videos upload? (y, n) (default n) : ') == 'y':
            uploading_process.start()
        shutdown = input('shutdown pc at the end of process? (y, n) (default n)') in ('y', 'yes')

        try:
            register_backgrounds_process(session, backgrounds_urls)
            register_songs_process(session, songs_urls)
            download_backgrounds_process(session)
            download_songs_process(session)
            get_lyrics_process(session)
            map_lyrics_process(session)
            create_aeps_process(session)
            render_aeps_process(session=session, queue=queue, condition=condition)

        finally:
            queue.put(shutdown)
            with condition:
                condition.notify_all()


if __name__ == '__main__':
    main()
