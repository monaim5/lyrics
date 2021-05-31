from urllib3 import HTTPResponse
from youtube_utils import search_videos_by_keyword, register_searched_videos, scrape_tags_by_id
import json
import re
import string
from pathlib import Path
import pandas as pd
from pandas import DataFrame
from scipy.sparse.csr import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from nltk.corpus import stopwords
from spacy.lang.en.stop_words import STOP_WORDS as en_stop

from nltk import download as download_nltk


# q = 'gaming music'
# videos = search_videos_by_keyword(q, 'AIzaSyBh_M02cc69Gqkel1IoJdourfTjS6rrCBQ')
# register_searched_videos(videos, q, 'search')
#
# exit()


try:
    STOP_WORDS_ = stopwords.words('english')
except LookupError as e:
    download_nltk('stopwords')
    STOP_WORDS_ = stopwords.words('english')


HTTP_PATTERN = re.compile(r'http\S+')
WWW_PATTERN = re.compile(r'www.\S+')
STOP_WORDS_PATTERN = re.compile(r'\b' + r'\b|\b'.join(map(re.escape, en_stop)) + r'\b')


def preprocessor(s):
    s = s.lower()
    s = HTTP_PATTERN.sub('', s)
    s = WWW_PATTERN.sub('', s)
    s = STOP_WORDS_PATTERN.sub('', s)
    s = s.translate(str.maketrans('', '', string.punctuation))
    return s


def remove_punctuation(s):
    return s.translate(str.maketrans('', '', string.punctuation))


dataset_folder = Path('../databases/scrapped_youtube_videos_data/NoCopyrightSounds_uploads_29_05_2021/')
search_dataset_folder = Path('../databases/scrapped_youtube_videos_data/search/')
columns = ['id', 'title', 'description', 'tags']

# for file in search_dataset_folder.glob('*.json'):
#     try:
#         with file.open(encoding='utf-8') as f:
#             videos = json.load(f)
#
#         for v in videos['items']:
#             v['snippet']['tags'] = scrape_tags_by_id(v['id']['videoId'])
#
#     finally:
#         with file.open(mode='w', encoding='utf-8') as f:
#             json.dump(videos, f, indent=2, ensure_ascii=False)


df = pd.DataFrame(columns=columns)

for ds in search_dataset_folder.glob('*.json'):
    with ds.open(encoding='utf-8') as f:
        df = pd.concat([df, pd.DataFrame(map(lambda x: [x['id']['videoId'], x['snippet']['title'],
                                                        x['snippet']['description'],
                                                        ' '.join(x['snippet']['tags'])],
                                             json.load(f)['items']), columns=columns)], ignore_index=True)

        # df = pd.concat([df, pd.DataFrame(map(lambda x: [x['snippet']['resourceId']['videoId'], x['snippet']['title'],
        #                                                 x['snippet']['description'], None],
        #                                      json.load(f)['items']), columns=columns)], ignore_index=True)

df = df.set_index('id')
# df['bow'] = df.apply(lambda x: f'{preprocessor(x["title"])} {preprocessor(x["description"])}', axis=1)
df['bow'] = df.apply(lambda x: f'{remove_punctuation(x["title"])} '
                               f'{remove_punctuation(x["description"])} '
                               f'{remove_punctuation(x["tags"])}', axis=1)
print(df)
counter = CountVectorizer(token_pattern=r'\S+')
tfidf_transformer = TfidfTransformer()

counter: CountVectorizer = counter.fit(df['bow'])

title_transformation = counter.transform(df['title'])
description_transformation = counter.transform(df['description'])
tags_transformation = counter.transform(df['tags'])

print(counter.get_feature_names())
print(title_transformation)
print()
print(description_transformation)
print()
print(tags_transformation)
# vectorizer = TfidfVectorizer()
# tfidf_vec = vectorizer.fit_transform(df['bow'])

exit()
def get_knowledge(video_id):
    index: DataFrame = df.index.get_loc(video_id)
    matrix = tfidf_vec[index]
    return map(lambda x: (vectorizer.get_feature_names()[x[0]], x[1]),
               sorted(enumerate(matrix.toarray()[0]), key=lambda x: x[1], reverse=True)[:10])


print(tfidf_vec)