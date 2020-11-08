import json
import os
import re
import time
from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import tkinter as tk

from lyrics.gui import MappingConsole, AdjustmentConsole
from models import Song
from paths import chrome_driver, chrome_binary, lyrics_dir


def get_lyrics(song: Song):
    if song.lyrics_path.exists():
        return True

    headers = {
        "Host": "www.musixmatch.com",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Upgrade-Insecure-Requests": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }
    title = re.sub('\(.*\)', '', song.title)
    title = re.sub('\[.*\]', '', title)
    q = re.sub('\[.*\]|\.', '', title).strip().replace(' ', '%20')
    url = f'https://www.musixmatch.com/search/{q}'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = chrome_binary.__str__()
    driver = webdriver.Chrome(executable_path=chrome_driver.__str__(), chrome_options=chrome_options)
    driver.get(url)
    driver.find_element_by_xpath(
        '//*[@id="search-all-results"]/div[1]/div[1]/div[2]/div/ul/li/div/div[2]/div/h2/a') \
        .click()

    url = driver.current_url + '/translation/arab'
    driver.quit()
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    row = soup.select('.mxm-translatable-line-readonly .row')
    lyrics = []
    i = 1
    for line in row:
        if line.select('div')[0] is not None and len(line.select('div')[0].text) > 1:
            text_en = line.select('div')[0].text
        else:
            text_en = '/'
        if line.select_one('.text-right') is not None and len(line.select_one('.text-right').text) > 1:
            text_ar = line.select_one('.text-right').text
        else:
            text_ar = '/'
        if text_en != '/' or text_ar != '/':
            lyrics.append({'text_en': text_en, 'text_ar': text_ar})
            i += 1


        with open(song.lyrics_path, 'w+', encoding='utf-8') as f:
            json.dump(lyrics, f, ensure_ascii=False, sort_keys=True, indent=2)

    return True


def map_lyrics(song: Song):
    if song.lyrics_map_path.exists():
        return True
    root = tk.Tk()
    root.title('lyrics <press space when after you heard the first word')
    console = MappingConsole(root, song)
    root.bind('<space>', console.on_space_press)
    root.bind('<KeyRelease-space>', console.on_space_release)
    root.bind('<BackSpace>', console.on_backspace_press)
    root.bind('<KeyRelease-BackSpace>', console.on_backspace_release)
    console.pack()
    root.focus_force()
    console.start_time = time.perf_counter()
    root.mainloop()


def adjust_lyrics(song: Song):
    root = tk.Tk()
    root.title('adjust lyrics')
    adjustment_console = AdjustmentConsole(root, song)
    adjustment_console.pack()
    root.focus_force()
    root.mainloop()
