import random
import os
from pathlib import Path
from utillc import *
from PIL import Image, ImageFilter
from PIL import ImageDraw
import numpy as np
from moviepy import (
	ImageClip,
	AudioFileClip,
	VideoFileClip,
	CompositeVideoClip,
	concatenate_videoclips
)
import moviepy
EKOX(moviepy.__version__)
from moviepy.audio.fx import AudioLoop
from moviepy.video.fx import FadeIn, FadeOut
import math

import annote

f1 = "

img1 =  Image.open(filename)
