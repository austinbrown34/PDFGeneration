# ensure yum is up to date

yum update

# let's get python 2.7 installed with pip and source it

yum install -y python27
easy_install pip
pip install --upgrade pip
echo "alias python='python27'" >> ~/.bashrc
source ~/.bashrc

# install some python development helpers

yum install -y gcc-c++
yum install -y libxml2-python libxml2-devel
yum install -y python-devel

# now we must install uwsgi, Flask, and nginx to be a real server

easy_install uwsgi
easy_install Flask
yum install -y nginx

# the following installs will help us work with images

yum install -y libjpeg-devel
pip install pillow
pip install piexif

# finally we get to the pdf specific libraries

pip install pdfminer
pip install fdfgen
pip install reportlab
pip install pypdf2

# we must install some helper dependencies that assist with fonts

yum install -y fontconfig freetype freetype-devel fontconfig-devel libstdc++
yum install -y fontconfig freetype freetype-devel fontconfig-devel libstdc++

# in order to have flexibility over data visualizations, we need phantomjs

wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
mkdir -p /opt/phantomjs
bzip2 -d phantomjs-2.1.1-linux-x86_64.tar.bz2
tar -xvf phantomjs-2.1.1-linux-x86_64.tar --directory /opt/phantomjs/ --strip-components 1
ln -s /opt/phantomjs/bin/phantomjs /usr/bin/phantomjs

# let's get git

yum install -y git

# to take care of some xml parsing needs we'll need these as well

yum install -y libxslt-devel
pip install lxml

# to help us make command line tools
pip install click

# to work with S3 we need to grab boto

pip install boto3

# PDFtk - a free java application - helps us accomplish a couple important tasks
# unfortunately, PDFtk doesn't compile natively on Amazon Linux - so we will
# grab a precompiled version of it

git clone https://github.com/lob/lambda-pdftk-example.git
mkdir -p /opt/pdftk
cp lambda-pdftk-example/bin/pdftk /opt/pdftk/
cp lambda-pdftk-example/bin/libgcj.so.10 /opt/pdftk/
ln -s /opt/pdftk/pdftk /usr/bin/pdftk
ln -s /opt/pdftk/libgcj.so.10 /usr/lib/libgcj.so.10
cp /opt/pdftk/libgcj.so.10 /usr/lib64/
export LD_LIBRARY_PATH=/opt/pdftk/libgcj.so.10

# Finally, let's replace the nginx config file with our own and fire her up

cp -f nginx.conf /etc/nginx/nginx.conf
service nginx start
chkconfig nginx on
uwsgi --yaml app.yaml

# Though, the docs specify using (kill -INT `cat /tmp/uwsgi.pid`)
# to stop all uwsgi processes, if this doesn't work, this should:
# (sudo kill `pidof uwsgi`) - just be sure to restart when you need it again
# Also, to check your logs do this - sudo cat /var/log/uwsgi.log

