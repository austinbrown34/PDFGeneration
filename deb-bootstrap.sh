cd /vagrant/
sudo apt-get -y update
sudo apt-get -y install python-pip python-dev build-essential
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv
sudo apt-get -y install git-all
virtualenv env
. env/bin/activate
pip install -r requirements.txt
sudo apt-get -y install build-essential chrpath libssl-dev libxft-dev
sudo cp bin/phantomjs /usr/local/share/
sudo ln -sf /usr/local/share/phantomjs /usr/local/bin
sudo apt-get -y install pdftk
sudo apt-get install -y libxml2-dev libxslt-dev python-dev
