#!/bin/bash
#
# Run from new VM console or SSH session

echo =============================
echo "Update packages"
echo =============================

apt-get install acpid 
apt-get install unattended-upgrades 
apt-get install denyhosts 
apt-get install ufw 
apt-get install apache2 
apt-get install samba 
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


apt-get update

echo =============================
echo "Next step: postboot_4.sh"
echo =============================
