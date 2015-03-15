# make sure in correct directory
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..

INSTALL_DIR="/home/cloo/repl/apps/contentmine/src/cmapi/"
APP_NAME="cmapi"

NEW_NORMA="norma_0.1_SNAPSHOT_20150312a.deb"
NEW_AMI="ami2_0.1_SNAPSHOT_20150315b.deb"
NEW_QS="0.3.6"

# prep sym links for gateway nginx
ln -sf $INSTALL_DIRdeploy/$APP_NAME-gate /home/cloo/repl/gateway/nginx/sites-available/$APP_NAME-gate
ln -sf /home/cloo/repl/gateway/nginx/sites-available/$APP_NAME-gate /home/cloo/repl/gateway/nginx/sites-enabled/$APP_NAME-gate

# prep sym links for app servers supervisor and nginx
ln -sf $DIR/$APP_NAME.conf /home/cloo/repl/apps/supervisor/conf.d/$APP_NAME.conf
ln -sf $DIR/nginx/$APP_NAME-apps /home/cloo/repl/apps/nginx/sites-available/$APP_NAME-apps
ln -sf /home/cloo/repl/apps/nginx/sites-available/$APP_NAME-apps /home/cloo/repl/apps/nginx/sites-enabled/$APP_NAME-apps
# end of simple default stuff

# reload the nginx if syntax is OK, and gateway should now be prepped to serve the apps
sudo nginx -t && sudo nginx -s reload

# NOW DO WHATEVER INSTALLS AND DOWNLOADS CAN BE DONE INSIDE THE repl/apps FOLDER OF THIS APP
# if needing to install into the virtualenv, assume we are in one that was manually created on first install
. ../../bin/activate
pip install -e .

cd ../
# get ami and norma versions
wget https://bitbucket.org/petermr/norma/downloads/$NEW_NORMA
wget https://bitbucket.org/petermr/ami-plugin/downloads/$NEW_AMI

# and get journal-scrapers too - in a suitable dir
git clone http://github.com/contentmine/journal-scrapers

# AND THEN replicate the repl folders across the infrastructure servers
/home/cloo/repl/replicate.sh

# NOW ISSUE ANY NECESSARY COMMANDS TO SETUP OR INSTALL DIRECTLY ON THE APPS SERVERS

# issue commands to the apps servers to get things running on them
/home/cloo/repl/command.sh apps sudo apt-get update -q -y
/home/cloo/repl/command.sh apps sudo apt-get -q -y install libxml2-dev libxslt-dev python-dev lib32z1-dev

# install new ami and norma and quickscrape if required
/home/cloo/repl/command.sh apps sudo dpkg -i /home/cloo/repl/apps/contentmine/src/$NEW_NORMA
/home/cloo/repl/command.sh apps sudo dpkg -i /home/cloo/repl/apps/contentmine/src/$NEW_AMI
/home/cloo/repl/command.sh apps sudo npm install --global quickscrape@$NEW_QS

# AND NOW RESTART SUPERVISOR FOR THE APP ON THE APPS MACHINES, THEN NGINX ON THE APPS MACHINES

# restart the supervisor script looking after this, on the apps machines
/home/cloo/repl/command.sh apps sudo supervisorctl reread $APP_NAME
/home/cloo/repl/command.sh apps sudo supervisorctl update $APP_NAME
/home/cloo/repl/command.sh apps sudo supervisorctl restart $APP_NAME
# reload the nginx on the apps
/home/cloo/repl/command.sh apps sudo nginx -t && sudo nginx -s reload

# APP SHOULD NOW BE UP AND RUNNING ON THE APPS MACHINES AND BEING SERVED BY THE GATEWAY

# tidy unnecessary files and replicate tidied repl folder
rm $NEW_AMI
rm $NEW_NORMA
/home/cloo/repl/replicate.sh
