import random
import os
from pathlib import Path
from utillc import *
from PIL import Image, ImageFilter
from PIL import ImageDraw, ImageFont
import numpy as np
from moviepy import (
	ImageClip,
	AudioFileClip,
	VideoFileClip,
	CompositeVideoClip,
	CompositeAudioClip,
	concatenate_videoclips, TextClip
)

import moviepy
from moviepy.video.fx import CrossFadeIn, CrossFadeOut, FadeIn, FadeOut
EKOX(moviepy.__version__)
from moviepy.audio.fx import AudioLoop, MultiplyVolume
import math
import annote
EKOX(moviepy.__file__)

# ============================================================
# PARAMÈTRES
# ============================================================

INPUT_DIR = annote.photo_dir 

OUTPUT_FILE = "diaporama.mp4"

IMAGE_DURATION = 5.0		 # Durée d'affichage de chaque image (secondes)
FADE_DURATION = 1.0			 # Durée du fondu enchaîné
FPS = 30					 # Images par seconde de la vidéo finale

# Résolution de la vidéo finale
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080


# ============================================================
# EXTENSIONS RECONNUES
# ============================================================

IMAGE_EXTENSIONS = {
	".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", "heic", ".JPG"
}

VIDEO_EXTENSIONS = {
	".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"
}


# ============================================================
# FONCTIONS
# ============================================================

from PIL import Image, ImageFilter
import numpy as np


def image_focus(image, point, radius,
                transition=None,
                blur_radius=20):
    """
    Crée une image centrée sur 'point', avec :
      - une largeur de 4 * radius pixels
      - le disque de rayon 'radius' parfaitement net
      - un flou progressif autour du disque
      - conservation du rapport largeur/hauteur de l'image

    Parameters
    ----------
    image : PIL.Image
        Image source.

    point : (x, y)
        Coordonnées du centre du disque dans l'image originale.

    radius : float
        Rayon du disque net, en pixels dans l'image originale.

    transition : float
        Largeur de la zone de transition net -> flou,
        en pixels de l'image originale.
        Par défaut : radius / 2.

    blur_radius : float
        Intensité du flou Gaussian.

    Returns
    -------
    PIL.Image
        Nouvelle image.
    """

    if transition is None:
        transition = radius / 2

    x, y = point

    # ---------------------------------------------------------
    # Conversion en RGB/RGBA pour faciliter les traitements
    # ---------------------------------------------------------

    original_mode = image.mode

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    width, height = image.size

    # ---------------------------------------------------------
    # Dimensions de l'image finale
    #
    # Largeur = 4 * rayon
    # Hauteur conservant le rapport d'aspect original
    # ---------------------------------------------------------

    output_width = round(4 * radius)
    output_height = round(output_width * height / width)

    # ---------------------------------------------------------
    # Zone à extraire autour du point
    #
    # On extrait une zone dont la largeur correspond à 4R
    # et dont la hauteur respecte le rapport d'aspect final.
    # ---------------------------------------------------------

    crop_width = 4 * radius
    crop_height = crop_width * height / width

    left = x - crop_width / 2
    top = y - crop_height / 2
    right = x + crop_width / 2
    bottom = y + crop_height / 2

    # ---------------------------------------------------------
    # Création d'une image temporaire.
    # Cela permet également de gérer le cas où le point est
    # proche du bord de l'image.
    # ---------------------------------------------------------

    temp = Image.new(
        image.mode,
        (
            round(crop_width),
            round(crop_height)
        ),
        (0, 0, 0, 0) if image.mode == "RGBA" else (0, 0, 0)
    )

    # Zone source
    src_left = max(0, round(left))
    src_top = max(0, round(top))
    src_right = min(width, round(right))
    src_bottom = min(height, round(bottom))

    if src_right > src_left and src_bottom > src_top:

        part = image.crop(
            (src_left, src_top, src_right, src_bottom)
        )

        # Position de la partie extraite dans temp
        dst_x = round(src_left - left)
        dst_y = round(src_top - top)

        temp.paste(
            part,
            (dst_x, dst_y)
        )

    # ---------------------------------------------------------
    # Mise à l'échelle finale
    # ---------------------------------------------------------

    sharp = temp.resize(
        (output_width, output_height),
        Image.Resampling.LANCZOS
    )

    # ---------------------------------------------------------
    # Création de la version floue
    # ---------------------------------------------------------

    blurred = sharp.filter(
        ImageFilter.GaussianBlur(blur_radius)
    )

    # ---------------------------------------------------------
    # Création du masque progressif
    #
    # Le point est maintenant exactement au centre.
    #
    # Le rayon du disque est transformé dans les dimensions
    # de l'image finale.
    # ---------------------------------------------------------

    mask_width = output_width
    mask_height = output_height

    yy, xx = np.ogrid[
        0:mask_height,
        0:mask_width
    ]

    center_x = output_width / 2
    center_y = output_height / 2

    distance = np.sqrt(
        (xx - center_x) ** 2 +
        (yy - center_y) ** 2
    )

    # Facteur d'échelle entre l'image originale et l'image finale
    scale = output_width / crop_width

    final_radius = radius * scale
    final_transition = transition * scale

    # ---------------------------------------------------------
    # Masque :
    #
    # distance <= radius       -> 100% net
    # distance >= radius+T     -> 100% flou
    # entre les deux           -> transition progressive
    # ---------------------------------------------------------

    mask = np.zeros(
        (mask_height, mask_width),
        dtype=np.float32
    )

    r0 = final_radius
    r1 = final_radius + final_transition

    mask[distance <= r0] = 1.0

    transition_zone = (
        (distance > r0) &
        (distance < r1)
    )

    t = (distance[transition_zone] - r0) / final_transition

    # Smoothstep pour une transition très douce
    t = t * t * (3 - 2 * t)

    mask[transition_zone] = 1.0 - t

    # Conversion en masque PIL
    mask = Image.fromarray(
        np.uint8(mask * 255),
        mode="L"
    )

    # ---------------------------------------------------------
    # Mélange image nette / image floue
    # ---------------------------------------------------------

    result = Image.composite(
        sharp,
        blurred,
        mask
    )

    return result

def image_focus2(image, point, radius, transition=None, blur_radius=15):
    """
    Place 'point' au centre de l'image et applique un flou progressif
    autour d'un disque de rayon 'radius'.

    Parameters
    ----------
    image : PIL.Image
        Image source.

    point : (x, y)
        Coordonnées du centre du disque dans l'image originale.

    radius : float
        Rayon de la zone parfaitement nette.

    transition : float, optional
        Largeur de la transition entre net et flou.
        Par défaut : radius * 0.5.

    blur_radius : float
        Rayon du flou Gaussian appliqué à l'extérieur du disque.

    Returns
    -------
    PIL.Image
        Nouvelle image.
    """

    if transition is None:
        transition = radius * 0.5

    x, y = point

    width, height = image.size

    # ---------------------------------------------------------
    # 1. Déplacer l'image pour que le point soit au centre
    # ---------------------------------------------------------

    cx = width / 2
    cy = height / 2

    dx = cx - x
    dy = cy - y

    shifted = Image.new(
        image.mode,
        image.size
    )

    shifted.paste(
        image,
        (round(dx), round(dy))
    )

    # ---------------------------------------------------------
    # 2. Image floue
    # ---------------------------------------------------------

    blurred = shifted.filter(
        ImageFilter.GaussianBlur(blur_radius)
    )

    # ---------------------------------------------------------
    # 3. Création du masque circulaire progressif
    # ---------------------------------------------------------

    mask = Image.new(
        "L",
        (width, height),
        0
    )

    pixels = mask.load()

    center_x = width / 2
    center_y = height / 2

    r0 = radius
    r1 = radius + transition

    for py in range(height):

        dy = py - center_y

        for px in range(width):

            dx = px - center_x

            distance = math.sqrt(
                dx * dx + dy * dy
            )

            if distance <= r0:
                # Zone parfaitement nette
                value = 255

            elif distance >= r1:
                # Zone parfaitement floue
                value = 0

            else:
                # Transition progressive
                t = (distance - r0) / transition

                # Smoothstep :
                # transition plus naturelle qu'une interpolation linéaire
                t = t * t * (3 - 2 * t)

                value = round(255 * (1 - t))

            pixels[px, py] = value

    # ---------------------------------------------------------
    # 4. Mélange net / flou
    # ---------------------------------------------------------

    result = Image.composite(
        shifted,
        blurred,
        mask
    )

    return result


def image_centre_point_disque(image, point, rayon):
	"""
	Centre l'image sur 'point' et conserve nette la zone
	correspondant à un disque de rayon 'rayon'.
	L'extérieur du disque est flouté.

	Paramètres
	----------
	image : PIL.Image
		Image source.
	point : (x, y)
		Coordonnées du centre du disque dans l'image source.
	rayon : int ou float
		Rayon du disque en pixels.

	Retour
	------
	PIL.Image
		Nouvelle image de même taille que l'image source.
	"""

	x, y = point
	largeur, hauteur = image.size

	# ---------------------------------------------------------
	# 1. Déplacer l'image pour que le point soit au centre
	# ---------------------------------------------------------

	cx = largeur / 2
	cy = hauteur / 2

	dx = cx - x
	dy = cy - y

	# Translation de l'image
	translatee = Image.new(
		image.mode,
		image.size
	)

	translatee.paste(
		image,
		(round(dx), round(dy))
	)

	# ---------------------------------------------------------
	# 2. Créer une version floue
	# ---------------------------------------------------------

	floue = translatee.filter(
		ImageFilter.GaussianBlur(radius=15)
	)

	# ---------------------------------------------------------
	# 3. Créer le masque du disque
	# ---------------------------------------------------------

	masque = Image.new(
		"L",
		image.size,
		0
	)

	# Cercle blanc = zone nette
	masque_draw = Image.new("L", image.size, 0)
	draw = ImageDraw.Draw(masque)
	draw.ellipse(
		(
			cx - rayon,
			cy - rayon,
			cx + rayon,
			cy + rayon
		),
		fill=255
	)

	# ---------------------------------------------------------
	# 4. Combiner l'image nette et l'image floue
	# ---------------------------------------------------------

	resultat = Image.composite(
		translatee,
		floue,
		masque
	)

	return resultat

def resize_and_crop(clip, width, height):
	"""
	Redimensionne le clip pour remplir complètement
	la surface width x height, puis coupe ce qui dépasse.
	"""

	target_ratio = width / height
	clip_ratio = clip.w / clip.h

	if clip_ratio > target_ratio:
		# Clip trop large
		clip = clip.resized(height=height)
		x1 = (clip.w - width) / 2
		clip = clip.cropped(
			x1=x1,
			x2=x1 + width,
			y1=0,
			y2=height
		)
	else:
		# Clip trop haut
		clip = clip.resized(width=width)
		y1 = (clip.h - height) / 2
		clip = clip.cropped(
			x1=0,
			x2=width,
			y1=y1,
			y2=y1 + height
		)

	return clip




def load_media(filename, ifile=0):
	"""
	Charge une image ou une vidéo et retourne un VideoClip.
	"""
	clip = TextClip(text=str(ifile),
					font = "/usr/share/fonts/type1/texlive-fonts-recommended/pcrbo8a.pfb",
					font_size=300, color="red" if ifile % 2 == 0 else "blue",
					size = (VIDEO_WIDTH, VIDEO_HEIGHT)).with_position((100, 100)).with_duration(IMAGE_DURATION)

	#return clip

	extension = filename.suffix.lower()

	if extension in IMAGE_EXTENSIONS:
		
		img =  Image.open(filename)
		try :
			cercle = annote.read_circle(img)
		except :
			cercle = { "cx" : self.image.width/2,
					   "cy" : self.image.height/2,					   
					   "r" : self.image.width/2,
					   "desc" : "",
					   "age" : "9"
					  }
		cx, cy, rayon = cercle["cx"], cercle["cy"], cercle["r"]
		#img = image_centre_point_disque(img, (cx, cy), rayon)
		img = image_focus(img, (cx, cy), rayon)
		
		
		#clip = ImageClip(str(filename))
		#clip = ImageClip(img)
		clip = ImageClip(np.array(img))		
		clip = clip.with_duration(IMAGE_DURATION)

	elif extension in VIDEO_EXTENSIONS:
		clip = VideoFileClip(str(filename))

	else:
		return None

	# Mise au format de la vidéo finale
	clip = resize_and_crop(
		clip,
		VIDEO_WIDTH,
		VIDEO_HEIGHT
	)

	return clip



def intercaler(a, b):
    n = min(len(a), len(b))

    resultat = [x for paire in zip(a[:n], b[:n]) for x in paire]

    restants = a[n:] + b[n:]

    for x in restants:
        resultat.insert(random.randrange(len(resultat) + 1), x)

    return resultat
# ============================================================
# RECHERCHE DES FICHIERS
# ============================================================

def main() :

	input_path = Path(INPUT_DIR)

	files = sorted(
		[
			f for f in input_path.iterdir()
			if f.is_file()
			and f.suffix.lower() in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
		],
		key=lambda f: f.name.lower()
	)
	random.shuffle(files)

	if not files:
		raise RuntimeError(
			f"Aucune image ou vidéo trouvée dans {INPUT_DIR}"
		)

	EKOX(len(files))

	print("Fichiers trouvés :")

	for f in files:
		print("	 ", f.name)
	#files = files[:6]
	#files = files[:18]

	def rr(fn) :
		img =  Image.open(fn)
		try :
			cercle = annote.read_circle(img)
		except :
			cercle = { "cx" : img.width/2,
					   "cy" : img.height/2,					   
					   "r" : img.width/2,
					   "desc" : "",
					   "age" : "9"
					  }
		return cercle


	

	
	files_2 = [ (x, rr(x)) for x in files]
	EKON(files_2)
	cf = lambda nn : [ x for x in files_2 if x[1]["desc"] == nn]
	EKON(len(cf("s")))
	EKON(len(cf("m")))
	EKON(len(cf("d")))

	files_2 = sorted(files_2, key = lambda x : x[1]["age"])
	solene, matthieu, deux = list(map(cf, "smd"))	
	
	files_2 = sorted(files_2, key = lambda x : x[1]["desc"])

	files_2 = intercaler(solene, matthieu) + deux

	
	files = [ x[0] for x in files_2]

	

	# ============================================================
	# CHARGEMENT DES CLIPS
	# ============================================================

	clips = []

	for ifile, filename in enumerate(files) :

		print(f"Chargement : {filename.name}")

		clip = load_media(filename, ifile)

		if clip is not None:
			clips.append(clip)


	# ============================================================
	# CRÉATION DU FONDU ENCHAÎNÉ
	# ============================================================

	if not clips:
		raise RuntimeError("Aucun clip valide.")


	final_clips = []

	current_time = 0
	clipd = clips[1:] + clips[0:1]
	def opacite(t):
		return min(1, max(0, t / FADE_DURATION))
	epsi = 0.01
	for i, (clip, clip2) in enumerate(zip(clips, clipd)):
	#for i, clip in enumerate(clips) :
		duration = clip.duration
		EKON(clip.duration, clip2.duration)
		if i == 0:
			# Premier clip
			EKOX(clip.duration)			
			clipa = clip.subclipped(0, IMAGE_DURATION - FADE_DURATION)
			EKOX(clipa.duration)
			clipx = clip.subclipped(IMAGE_DURATION - FADE_DURATION, IMAGE_DURATION)
			clipx = clipx.with_effects([
				CrossFadeOut(FADE_DURATION - epsi)
			])
			EKOX(clipx.duration)
			clipy = clip2.subclipped(0, FADE_DURATION)
			EKOX(clipy.duration)

			clipy = clipy.with_effects([
				CrossFadeIn(FADE_DURATION - epsi)
			])
			clipb = CompositeVideoClip([clipy, clipx])
			EKOX(clipb.duration)
		else:
			current_time -= FADE_DURATION
			clipa = clip.subclipped(FADE_DURATION, IMAGE_DURATION - FADE_DURATION)
			EKOX(clipa.duration)
			clipx = clip.subclipped(IMAGE_DURATION - FADE_DURATION, IMAGE_DURATION)
			clipx = clipx.with_effects([
				CrossFadeOut(FADE_DURATION - epsi)
			])

			clipy = clip2.subclipped(0, FADE_DURATION)
			clipy = clipy.with_effects([
				CrossFadeIn(FADE_DURATION - epsi)
			])

			clipb = CompositeVideoClip([clipx, clipy])
			EKOX(clipb.duration)
		final_clips.append(clipa)
		final_clips.append(clipb)

		current_time += duration


	# ============================================================
	# COMPOSITION FINALE
	# ============================================================

	final_duration = current_time
	"""
	final_video = CompositeVideoClip(
		final_clips,
		size=(VIDEO_WIDTH, VIDEO_HEIGHT)
	)
	"""
	final_video = concatenate_videoclips(final_clips) #, method="compose")

	
	#.with_duration(final_duration)
	EKOX(final_video.duration)

	# ============================================================
	# ENCODAGE
	# ============================================================

	print()
	print("Création de la vidéo...")
	print(f"Durée : {final_duration:.1f} secondes")

	
	zao = "/mnt/NUC/data/zao.mp3"
	pinard  = "/mnt/NUC/data/fabienne_thierry_zao.mp3"
	no_vocals  = "/mnt/NUC/data/zao_no_vocals.mp3"

	zao = AudioFileClip(zao)
	pinard = AudioFileClip(pinard)
	pinard = pinard.subclipped(0, 20)

	audio = CompositeAudioClip(pinard + zao, no_vocals)
	
	EKOX(audio.duration)
	EKOX(final_video.duration)
	audio = audio.with_effects([
		AudioLoop(duration=final_video.duration)
	])
	final_video  = final_video.with_audio(audio).with_duration(final_duration)
	
	final_video.write_videofile(
		OUTPUT_FILE,
		fps=FPS,
		codec="libx264",
		audio_codec="aac",
		preset="medium",
		threads=4
	)


	# Libération des ressources
	for clip in clips:
		clip.close()

	final_video.close()
	#video.close()	
	audio.close()
	print()
	print(f"Vidéo créée : {OUTPUT_FILE}")

if __name__ == "__main__":
	main()
