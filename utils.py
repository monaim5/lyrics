import re
from enum import Enum


class Color(Enum):
    WHITE = '#ffffff'
    
    LIGHT_RED = '#500606'
    LIGHT_GREEN = '#074205'
    LIGHT_BLUE = '#060F8E'

    LIGHT_YELLOW = '#A89E10'

    RED = '#FF0000'
    GREEN = '#00FF00'
    BLUE = '#03043F'

    YELLOW = '#eddd00'
    CYAN = '#07E1EF'
    ORANGE = '#360F02'
    PURPLE = '#42053E'



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