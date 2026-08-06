
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


