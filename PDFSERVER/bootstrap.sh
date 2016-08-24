# ensure yum is up to date

sudo yum update

# let's get python 2.7 installed with pip and source it

sudo yum install -y python27
sudo easy_install pip
sudo pip install --upgrade pip
echo "alias python='python27'" >> ~/.bashrc
source ~/.bashrc

# install some python development helpers

sudo yum install -y gcc-c++
sudo yum install -y libxml2-python libxml2-devel
sudo yum install -y python-devel

# now we must install uwsgi, Flask, and nginx to be a real server

sudo easy_install uwsgi
sudo easy_install Flask
sudo yum install -y nginx

# the following installs will help us work with images

sudo yum install -y libjpeg-devel
sudo pip install pillow
sudo pip install piexif

# finally we get to the pdf specific libraries

sudo pip install pdfminer
sudo pip install fdfgen
sudo pip install reportlab
sudo pip install pypdf2

# we must install some helper dependencies that assist with fonts

sudo yum install -y fontconfig freetype freetype-devel fontconfig-devel libstdc++
sudo yum install -y fontconfig freetype freetype-devel fontconfig-devel libstdc++

# in order to have flexibility over data visualizations, we need phantomjs

wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
sudo mkdir -p /opt/phantomjs
bzip2 -d phantomjs-2.1.1-linux-x86_64.tar.bz2
sudo tar -xvf phantomjs-2.1.1-linux-x86_64.tar --directory /opt/phantomjs/ --strip-components 1
sudo ln -s /opt/phantomjs/bin/phantomjs /usr/bin/phantomjs

# let's get git

sudo yum install -y git

# to take care of some xml parsing needs we'll need these as well

sudo yum install -y libxslt-devel
sudo pip install lxml

# to work with S3 we need to grab boto

sudo pip install boto3

# PDFtk - a free java application - helps us accomplish a couple important tasks
# unfortunately, PDFtk doesn't compile natively on Amazon Linux - so we will
# grab a precompiled version of it

git clone https://github.com/lob/lambda-pdftk-example.git
sudo mkdir -p /opt/pdftk
sudo cp lambda-pdftk-example/bin/pdftk /opt/pdftk/
sudo cp lambda-pdftk-example/bin/libgcj.so.10 /opt/pdftk/
sudo ln -s /opt/pdftk/pdftk /usr/bin/pdftk
sudo ln -s /opt/pdftk/libgcj.so.10 /usr/lib/libgcj.so.10
sudo cp /opt/pdftk/libgcj.so.10 /usr/lib64/
export LD_LIBRARY_PATH=/opt/pdftk/libgcj.so.10

# Finally, let's replace the nginx config file with our own and fire her up

sudo cp -f nginx.conf /etc/nginx/nginx.conf
sudo service nginx start
sudo chkconfig nginx on
sudo uwsgi --yaml app.yaml

# Though, the docs specify using (kill -INT `cat /tmp/uwsgi.pid`)
# to stop all uwsgi processes, if this doesn't work, this should:
# (sudo kill `pidof uwsgi`) - just be sure to restart when you need it again
# Also, to check your logs do this - sudo cat /var/log/uwsgi.log
