import json
import sqlite3
from paths import root, json_uploaded_to_lyrics


class Database:
    def __init__(self, db):
        self.__connection = None
        self.host = root / f'databases/{db}.db'

    def get_connection(self):
        if self.__connection is not None:
            print("already connected to database")
            return self.__connection
        else:
            # try:
            self.__connection = sqlite3.connect(self.host)
            print("Connecting to database")
            return self.__connection
            # except pymysql.err.InternalError:
            #     config_database()
            #     return get_connection()

    def config_database(self):
        cursor = self.get_connection()
        cursor.execute('CREATE TABLE IF NOT EXISTS songs ('
                       'id VARCHAR(20) PRIMARY KEY,'
                       'title VARCHAR(255) UNIQUE,'
                       'as_lyrics_video TINYINT(1) DEFAULT 0,'
                       'uploaded_to_lyrics TINYINT(1) DEFAULT 0,'
                       'file_name VARCHAR(255),'
                       'duration INTEGER(3),'
                       'tags TEXT,'
                       'credit TEXT)')

        cursor.execute('CREATE TABLE IF NOT EXISTS videos ('
                       'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                       'song_id VARCHAR(20),'
                       'FOREIGN KEY(song_id) REFERENCES songs(id))')

        cursor.execute('CREATE TABLE IF NOT EXISTS uploaded_to_lyrics ('
                       'song_id VARCHAR(20) PRIMARY KEY,'
                       'video_id INTEGER,'
                       'uploaded_id VARCHAR(20),'
                       'title VARCHAR(255),'
                       'channel_name VARCHAR(255),'
                       'channel_id VARCHAR(255),'
                       'publish_date DATE DEFAULT NULL,'
                       'FOREIGN KEY(video_id) REFERENCES videos(id))')

        cursor.execute('CREATE TABLE IF NOT EXISTS upload_queue ('
                       'video_id INTEGER PRIMARY KEY,'
                       'FOREIGN KEY(video_id) REFERENCES videos(id))')

        # cursor.execute('CREATE TABLE IF NOT EXISTS colors('
        #                'name VARCHAR(20) PRIMARY KEY,'
        #                'code VARCHAR(7) NOT NULL )')
        #
        # cursor.execute('CREATE TABLE IF NOT EXISTS users('
        #                'name VARCHAR(255) PRIMARY KEY,'
        #                'race VARCHAR(255) NOT NULL,'
        #                'email VARCHAR(255),'
        #                'password VARCHAR(255),'
        #                'channel_id VARCHAR(255),'
        #                'nb_accounts INT,'
        #                'client_secrets_path VARCHAR(255),'
        #                'token_path VARCHAR(255)),'
        #                'purpose VARCHAR(40)')
        self.get_connection().commit()
        print("create database")
#
#
#
# def close_connection():
#     global CONNECTION
#     if CONNECTION is not None:
#         CONNECTION.close()


def configure_data():
    db = Database('ncs_arabi')
    db.config_database()
    conn = db.get_connection()
    cursor = conn.cursor()
    with open(json_uploaded_to_lyrics) as f:
        uploaded_to_lyrics = json.load(f)

    for v in uploaded_to_lyrics:
        cursor.execute("""
                INSERT INTO uploaded_to_lyrics
                VALUES (:song_id, :uploaded_id, :title, :channel_name, :channel_id, :publish_date, :video_id)
            """, {'song_id': v['original'], 'uploaded_id': v['lyrics'], 'title': v['title'],
                  'channel_name': 'ncs_arabi', 'channel_id': 'UCLbsLjqzPKBLa7kzlEmfCXA',
                  'publish_date': None, 'video_id': None})
    conn.commit()

# db = Database('ncs_arabi')
# conn = db.get_connection()
# cur = conn.cursor()
# videos = cur.execute('SELECT max(publish_date) as date FROM `uploaded_to_lyrics`').fetchone()
# print(videos)

