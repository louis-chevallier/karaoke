
# make deploy : copie tout dans le rep de deploiement
# les serveurs snt lancés via cron : voir crontab -e


DEPLOY_DIR = /deploy
export DATE:=$(shell date +%Y-%m-%d_%Hh%Mm%Ss)
export HOST=$(shell hostname)
SHELL=bash
export GITINFO=$(shell git log --pretty=format:"%h - %an, %ar : %s" -1)
#WOD="$(shell fortune -s)"
WOD?='$(shell fortune -s | sed -e 's/["]//g' | sed -e "s/[']//g")'
xxx :
	echo $(WOD)

start :
	python server.py
deploy :
	-git commit -a -m $(WOD)
	-git push
	-cd $(DEPLOY_DIR); rm -fr karaoke; git clone  https://github.com/louis-chevallier/karaoke.git; cd karaoke



# separate voice/music
#  pip install -U demucs

# demucs -n htdemucs --two-stems=vocals /mnt/NUC/Audio/karaoke/mon-amie-la-rose.mp3

SONG ?=song_does_not_exist.mp3
SONG ?="/mnt/NUC/data/zao.mp3"

demux :
# 	High-quality model (slower, better results)
	demucs --two-stems=vocals -n htdemucs_ft $(SONG)
# 	Faster model
#	demucs -n htdemucs audio.mp3
# 	Best quality (slowest)
#	demucs -n mdx_extra_q $(SONG)



YT="https://www.youtube.com/watch?v=pHKQ7HJvS0s&list=RDpHKQ7HJvS0s&start_radio=1"
YT="https://www.youtube.com/watch?v=pHKQ7HJvS0s"
YT='https://www.youtube.com/watch?v=8eKYKOjg0fY&list=RD8eKYKOjg0fY'

zao :
#	yt-dlp 'https://www.youtube.com/watch?v=0eOHEU3sXik&list=RD0eOHEU3sXik&start_radio=1'
#	yt-dlp -x --audio-format mp3 --no-playlist 'https://www.youtube.com/watch?v=0eOHEU3sXik'
#	yt-dlp -x -t mp3 --no-playlist 'https://www.youtube.com/watch?v=pqo59FkF_5g'
	yt-dlp -x -t  mp3 --no-playlist  $(YT)

#&list=RDpqo59FkF_5g&start_radio=1
#&list=RD0eOHEU3sXik'

#&start_radio=1'


