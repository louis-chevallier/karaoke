import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os, sys
import json
import glob
import math
import numpy as np

from moviepy import (
	ImageClip,
	AudioFileClip,
	VideoFileClip,
	CompositeVideoClip,
	concatenate_videoclips
)
import moviepy

from moviepy.audio.fx import AudioLoop
from moviepy.video.fx import CrossFadeIn, CrossFadeOut, FadeIn, FadeOut
from utillc import *
EKOX(moviepy.__version__)
photo_dir = "/mnt/NUC/perso/solene-photos"			# Répertoire contenant images et vidéos

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")

# Tag EXIF UserComment
EXIF_USER_COMMENT = 37510


# ------------------------------------------------------------
# Application
# ------------------------------------------------------------
def read_circle(image):

	try:
		exif = image.getexif()

		if EXIF_USER_COMMENT not in exif:
			return None

		data = exif[EXIF_USER_COMMENT]

		if isinstance(data, bytes):

			# UserComment peut commencer par ASCII\0\0\0
			if data.startswith(b"ASCII\x00\x00\x00"):
				data = data[8:]

			data = data.decode("utf-8")

		return json.loads(data)

	except Exception:
		return None


class ImageViewer:

	def __init__(self, root, directory):
		self.root = root
		self.root.title("Visualiseur d'images")

		self.directory = directory

		# Liste des images
		self.files = sorted(
			f for f in glob.glob(os.path.join(directory, "*"))
			if os.path.isfile(f)
			and f.lower().endswith(IMAGE_EXTENSIONS)
		)

		#### test
		IMAGE_DURATION = 5
		FADE_DURATION = 1
		"""
		c = lambda img : ImageClip(np.array(Image.open(img))).with_duration(IMAGE_DURATION)
		clipa, clipb = list(map(c, self.files[0:2]))

		clip1 = clipa.subclipped(0, 5)
		clip2 = clipb

		# adding cross fade of 2 seconds in the clip2
		#clip2 = clip2.crossfadein(2.0)
		clip2 = clip2.with_effects([
				CrossFadeIn(FADE_DURATION)
		])
		
		# creating a composite video
		final = CompositeVideoClip([clip1, clip2])
		EKOX(final.duration)
		# showing final clip
		#final.ipython_display(width = 480)
		final.write_videofile(
				"out.mp4",
				fps=24,
				codec="libx264",
				audio_codec="aac",
				preset="medium",
				threads=4
		)

		sys.exit(0)
		"""



		
		
		self.root.title("Visualiseur d'images (%d images)" % len(self.files))
		if not self.files:
			raise RuntimeError("Aucune image trouvée dans le dossier.")

		self.index = 0

		# Image originale
		self.image = None

		# Image affichée
		self.display_image = None

		# Dimensions affichées
		self.display_width = 0
		self.display_height = 0

		# Facteur d'échelle
		self.scale = 1.0

		# Cercle : coordonnées dans l'image originale
		self.circle = None

		# Objet graphique du cercle
		self.circle_id = None

		# Position du centre lors du dessin
		self.center_x = None
		self.center_y = None
		self.description = "xxx"
		self.age = "9"
		# ----------------------------------------------------
		# Interface
		# ----------------------------------------------------

		self.canvas = tk.Canvas(
			root,
			background="black",
			highlightthickness=0
		)

		self.canvas.pack(
			fill=tk.BOTH,
			expand=True
		)

		# Informations
		self.info = tk.Label(root, text="")
		self.info.pack(fill=tk.X)

		# Souris
		self.canvas.bind("<ButtonPress-1>", self.mouse_press)
		self.canvas.bind("<B1-Motion>", self.mouse_drag)
		self.canvas.bind("<ButtonRelease-1>", self.mouse_release)

		# Espace = image suivante
		self.root.bind("<space>", self.next_image)
		self.root.bind("/", self.rotate_image)
		self.root.bind("<slash>", self.rotate_image)		
		self.root.bind("q", self.exit)		
		self.root.bind("m", self.desc)		
		self.root.bind("s", self.desc)		
		self.root.bind("d", self.desc)		

		#self.root.bind("<KeyRelease>", self.age)
		self.root.bind("<KeyRelease>", lambda e : self.agef(e))
		# Flèches
		self.root.bind("<Right>", self.next_image)
		self.root.bind("<Left>", self.previous_image)

		# Redimensionnement
		self.root.bind("<Configure>", self.window_resize)

		self.load_image()

	def exit(self, _):
		sys.exit(0)
	# --------------------------------------------------------
	# Lecture EXIF
	# --------------------------------------------------------


	# --------------------------------------------------------
	# Écriture EXIF
	# --------------------------------------------------------

	def save_circle(self):

		if self.circle is None:
			return

		try:

			# Recharge l'image originale afin de conserver
			# correctement ses métadonnées
			image = Image.open(self.files[self.index])

			exif = image.getexif()
			self.circle["desc"] = self.description
			self.circle["age"] = self.age
			data = json.dumps(
				self.circle,
				separators=(",", ":")
			)
			EKOX(data)
			# Format EXIF UserComment :
			# 8 octets indiquant l'encodage + données
			exif[EXIF_USER_COMMENT] = (
				b"ASCII\x00\x00\x00" + data.encode("utf-8")
			)

			# Pour JPEG, il faut passer les données EXIF
			# lors de la sauvegarde.
			if image.format == "JPEG":

				image.save(
					self.files[self.index],
					exif=exif.tobytes(),
					quality=95
				)

			else:
				# Pillow peut également écrire l'EXIF sur
				# les formats qui le permettent.
				image.save(
					self.files[self.index],
					exif=exif.tobytes()
				)

			image.close()

		except Exception as e:
			print("Erreur lors de l'enregistrement EXIF :", e)

	def rotate_image(self, event=None):

		filename = self.files[self.index]

		try:
			image = Image.open(filename)

			# Conserver les métadonnées EXIF
			exif = image.getexif()

			# Rotation 90° horaire
			image = image.transpose(Image.Transpose.ROTATE_270)
			# (utiliser ROTATE_90 pour une rotation anti-horaire)

			# Adapter le cercle si présent
			if self.circle is not None:

				w = self.image.width
				h = self.image.height

				cx = self.circle["cx"]
				cy = self.circle["cy"]

				# Rotation 90° horaire
				new_cx = h - 1 - cy
				new_cy = cx

				self.circle["cx"] = new_cx
				self.circle["cy"] = new_cy

				# Réécrire le cercle dans l'EXIF
				exif[EXIF_USER_COMMENT] = (
					b"ASCII\x00\x00\x00" +
					json.dumps(self.circle).encode("utf-8")
				)

			image.save(
				filename,
				exif=exif.tobytes(),
				quality=95
			)

			image.close()

			# Recharger l'image
			self.load_image()

		except Exception as e:
			print(e)

	# --------------------------------------------------------
	# Chargement d'une image
	# --------------------------------------------------------

	def load_image(self):

		filename = self.files[self.index]

		self.image = Image.open(filename)

		# Lire le cercle enregistré dans l'EXIF
		self.circle = read_circle(self.image)

		self.display_image_now()

		self.info.config(
			text=f"{self.index + 1}/{len(self.files)}	"
				 f"{os.path.basename(filename)}	  "
				 f"{self.image.width} × {self.image.height}"
		)
		self.root.title("%d %s %s (%d images)" % (self.index, filename, str(self.circle), len(self.files)))


	# --------------------------------------------------------
	# Affichage de l'image
	# --------------------------------------------------------

	def display_image_now(self):

		if self.image is None:
			return

		canvas_width = max(self.canvas.winfo_width(), 100)
		canvas_height = max(self.canvas.winfo_height(), 100)

		iw = self.image.width
		ih = self.image.height

		# Calcul du facteur d'échelle
		self.scale = min(
			canvas_width / iw,
			canvas_height / ih
		)

		self.display_width = int(iw * self.scale)
		self.display_height = int(ih * self.scale)

		resized = self.image.resize(
			(self.display_width, self.display_height),
			Image.Resampling.LANCZOS
		)

		self.display_image = ImageTk.PhotoImage(resized)

		self.canvas.delete("all")

		x = (canvas_width - self.display_width) // 2
		y = (canvas_height - self.display_height) // 2

		self.image_x = x
		self.image_y = y

		self.canvas.create_image(
			x,
			y,
			anchor=tk.NW,
			image=self.display_image
		)

		self.draw_circle()


	# --------------------------------------------------------
	# Dessin du cercle
	# --------------------------------------------------------

	def draw_circle(self):

		if self.circle is None:
			return

		cx = self.circle["cx"]
		cy = self.circle["cy"]
		r = self.circle["r"]

		# Conversion coordonnées image -> écran
		x = self.image_x + cx * self.scale
		y = self.image_y + cy * self.scale

		rr = r * self.scale

		self.circle_id = self.canvas.create_oval(
			x - rr,
			y - rr,
			x + rr,
			y + rr,
			outline="red",
			width=3
		)


	# --------------------------------------------------------
	# Souris
	# --------------------------------------------------------

	def screen_to_image(self, x, y):

		ix = (x - self.image_x) / self.scale
		iy = (y - self.image_y) / self.scale

		return ix, iy


	def mouse_press(self, event):

		# Vérifie que le clic est dans l'image
		if not (
			self.image_x <= event.x <=
			self.image_x + self.display_width
			and
			self.image_y <= event.y <=
			self.image_y + self.display_height
		):
			return

		self.center_x, self.center_y = self.screen_to_image(
			event.x,
			event.y
		)

		# Nouveau cercle
		self.circle = {
			"cx": round(self.center_x),
			"cy": round(self.center_y),
			"r": 0
		}


	def mouse_drag(self, event):

		if self.center_x is None:
			return

		x, y = self.screen_to_image(
			event.x,
			event.y
		)

		radius = math.sqrt(
			(x - self.center_x) ** 2 +
			(y - self.center_y) ** 2
		)

		self.circle = {
			"cx": round(self.center_x),
			"cy": round(self.center_y),
			"r": round(radius)
		}

		# Redessine
		if self.circle_id is not None:
			self.canvas.delete(self.circle_id)

		self.draw_circle()


	def mouse_release(self, event):

		if self.center_x is None:
			return

		self.save_circle()

		self.center_x = None
		self.center_y = None


	# --------------------------------------------------------
	# Navigation
	# --------------------------------------------------------

	def desc(self, event=None):
		EKON(event)
		EKOX(dir(event))
		EKOX(event.keysym)
		self.description = event.keysym
		self.save_circle()
		self.load_image()

	def agef(self, event=None):
		EKON(event)
		if event.keysym in [ "0", "1", "2"] :
				EKOX(dir(event))
				EKOX(event.keysym)
				self.age = event.keysym
				self.save_circle()
				self.load_image()
				EKOX(self.circle)
		
	def next_image(self, event=None):

		if self.index < len(self.files) - 1:

			self.index += 1
			self.load_image()


	def previous_image(self, event=None):

		if self.index > 0:

			self.index -= 1
			self.load_image()


	# --------------------------------------------------------
	# Redimensionnement de la fenêtre
	# --------------------------------------------------------

	def window_resize(self, event=None):

		if self.image is not None:
			self.display_image_now()


# ------------------------------------------------------------
# Programme principal
# ------------------------------------------------------------

if __name__ == "__main__":

	root = tk.Tk()

	root.geometry("1000x700")

	# Choix du dossier
	#directory = filedialog.askdirectory(		title="Choisir le dossier contenant les images"	   )
	directory = photo_dir

	if directory:

		app = ImageViewer(root, directory)

		root.mainloop()
		
