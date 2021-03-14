import re

from background.utils import download_background
from models import Background

bg_path = r'C:\Users\mon\Downloads\jaina_proudmoore_portrait_by_narga_lifestream_debl4d1.jpg'
background = Background(bg_path)

print(download_background(background))