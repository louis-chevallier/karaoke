

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

start1 : server_nuc

start : run_test

launch :
	make launch_server &
	make launch_chaudiere &
#	make start_linky &

# monitor linky now in server
start_linky :
	(export PORT=8093 && cd /deploy/server_https &&  export MINEKOLEVEL=0 && make linky >> /tmp/traceLinky.trc 2>&1)

linky :
	source ${HOME}/scripts/.bashrc; spy; pyenv; python monitor_linky.py --write

launch_chaudiere :
	(export PORT=8093 && cd /deploy/EPortier/robot_chaudiere/frontend/ &&  export MINEKOLEVEL=0 && make run >> /tmp/traceSensor.trc 2>&1)

launch_server :
	echo mdp $(MDP)
	echo myip $(MYIP)
	(cd /deploy/server_https ; export MINEKOLEVEL=0 && export PORT=8092 && export GARAGE_URL=http://194.183.210.10:8080/main$(MDP) && make run >> /tmp/traceServer.trc 2>&1)
#	(cd /deploy/server_https ; export MINEKOLEVEL=0 && export PORT=8092 && export GARAGE_URL=http://192.168.1.95:80/main$(MDP) && make run)

bbox :
	python bbox.py

server_nuc : pem 
#	ip -f inet addr show eth1 | awk '/inet / {print https://$2:8080}'
	date
	python -c 'import server; server.go()'

server_ws :  
#	ip -f inet addr show eth1 | awk '/inet / {print https://$2:8080}'
	date
	python server_websocket.py

run :
	date
	source ${HOME}/scripts/.bashrc; spy; pyenv; make server_nuc

deploy :
	-git commit -a -m $(WOD)
	-git push
	-cd $(DEPLOY_DIR); rm -fr server_https; git clone  https://github.com/louis-chevallier/server_https.git; cd server_https; make dopem

run_test :
	date
	source ${HOME}/scripts/.bashrc; spy; pyenv; export MDP=xxx ; make server_nuc

run2 :
	echo 111
	date
	source ${HOME}/scripts/.bashrc; spy; echo 222; pyenv; export MDP=xxx ; echo 333; make server_ws

dopem :
	-rm *.pem
	make pem

pem : privkey.pem  privkey.pem

%.pem :
# https://docs.cherrypy.dev/en/latest/deploy.html
	openssl genrsa -out privkey.pem 2048
	openssl req -new -x509 -days 365 -key privkey.pem -out cert.pem -subj "/C=FR/ST=LaMeziere/L=LaMeziere/O=Global Security/OU=IT Department/CN=example.com"

ccc :
	echo aaa
