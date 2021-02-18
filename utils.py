import re
from enum import Enum


class Color(Enum):
    YELLOW = '#eddd00'


class Bcolors(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_yt_id(url):
    match = re.search(r"youtube\.com/.*v=([^&]*)", url)
    if match:
        return match.group(1)
    else:
        raise Exception('no id in url')