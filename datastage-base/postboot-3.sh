# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

#!/bin/bash
#
# Run from new VM console or SSH session

echo =============================
echo "Install packages"
echo =============================

apt-get install acpid 
apt-get install unattended-upgrades 
apt-get install denyhosts 
apt-get install ufw 
apt-get install samba-doc 
apt-get install krb5-user 
apt-get install ntp 
apt-get install libapache2-webauth 
apt-get install libapache2-mod-auth-kerb 
apt-get install cadaver 
apt-get install nano 
apt-get install slapd  
apt-get install manpages 
apt-get install man-db 
apt-get install locate 
apt-get install kernel-package 
apt-get install lvm2 
apt-get install acl 
apt-get install git-core
apt-get install python-pip

apt-get install wget
cd /mnt/data/tool
wget http://redis.googlecode.com/files/redis-2.4.6.tar.gz
tar xzf redis-2.4.6.tar.gz
cd redis-2.4.6
make
rm /mnt/data/tool/redis*.gz

apt-get install libxml2-dev
apt-get install libxslt1-dev
apt-get install libacl1-dev
apt-get install python-dev
apt-get install python-psycopg2
apt-get install postgresql


apt-get install libapache2-mod-wsgi
/etc/init.d/apache2 restart
sudo a2enmod wsgi
apt-get update

echo =============================
echo "Next step: postboot_4.sh"
echo =============================
