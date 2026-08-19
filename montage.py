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
from moviepy.video.fx import FadeIn, FadeOut
import math

import annote

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


def image_focus(image, point, radius, transition=None, blur_radius=15):
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




def load_media(filename):
	"""
	Charge une image ou une vidéo et retourne un VideoClip.
	"""

	extension = filename.suffix.lower()

	if extension in IMAGE_EXTENSIONS:
		
		img =  Image.open(filename)
		try :
			cercle = annote.read_circle(img)
		except :
			cercle = { "cx" : self.image.width/2,
					   "cy" : self.image.height/2,					   
					   "r" : self.image.width/2,
					   "desc" : ""
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
	#files = files[:4]

	def rr(fn) :
		img =  Image.open(fn)
		try :
			cercle = annote.read_circle(img)
		except :
			cercle = { "cx" : img.width/2,
					   "cy" : img.height/2,					   
					   "r" : img.width/2,
					   "desc" : ""
					  }
		return cercle
	
	files_2 = [ (x, rr(x)) for x in files]
	files_2 = sorted(files_2, key = lambda x : x[1]["desc"])
	files = [ x[0] for x in files_2]

	

	# ============================================================
	# CHARGEMENT DES CLIPS
	# ============================================================

	clips = []

	for filename in files:

		print(f"Chargement : {filename.name}")

		clip = load_media(filename)

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
	for i, (clip, clip2) in enumerate(zip(clips, clipd)):
	#for i, clip in enumerate(clips) :
		duration = clip.duration
		EKON(clip.duration, clip2.duration)
		if i == 0:
			# Premier clip
			clip = clip.with_start(0)

		else:
			"""
			---------
			         \     
                      \
			           \
			            \
			             \
			              \
			               \
			                \
			                 \____________________________________
			                 --------------------
			                /
			               /
			              /
			             /
			            /
			           /
			          /
 			         /
			________/

			"""
			# Le clip commence avant la fin du précédent
			# afin de créer le fondu.
			current_time -= FADE_DURATION

			clip = clip.with_start(current_time)

			# Fondu d'entrée
			#clip = clip.crossfadein(FADE_DURATION)


			clip = clip.with_effects([
				FadeIn(FADE_DURATION)
			])

			# Overlap clips by setting the start time of clip2
			#clip2_shifted = clip2.with_start(clip.end - FADE_DURATION).crossfadein(FADE_DURATION)
			#final_clips.append(clip2_shifted)
		final_clips.append(clip)

		current_time += duration


	# ============================================================
	# COMPOSITION FINALE
	# ============================================================

	final_duration = current_time

	final_video = CompositeVideoClip(
		final_clips,
		size=(VIDEO_WIDTH, VIDEO_HEIGHT)
	).with_duration(final_duration)


	# ============================================================
	# ENCODAGE
	# ============================================================

	print()
	print("Création de la vidéo...")
	print(f"Durée : {final_duration:.1f} secondes")

	
	music = "f_00_zao.mp4.mp4"
	music = "/mnt/NUC/data/zao.mp3"
	
	audio = AudioFileClip(music)
	final_video  = final_video.with_audio(audio)	
	
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
