#!/bin/bash
# This script creates some directories, makes the initial clone of the source from github and creates the repository distributions file

# the build requires the following packages - debhelper , python-all and python-setuptools
# repository creation needs the reprepro package

# execute the following commands to update the apt repository and install the required packages:
sudo apt-get update
sudo apt-get install git debhelper python-all python-setuptools reprepro


DIR=${PWD}
mkdir -p ./build #contains the github clone with the source code
mkdir -p ./repo/conf #contains the apt-get repository

echo "Origin: Mihail Kozhuharov
Label: DataStage repository
Suite: unstable
Codename: quantal
Architectures: i386 amd64 source
Components: main non-free contrib
Description: DataStage development repository for enabling multiple projects.

Origin: Mihail Kozhuharov
Label: DataStage repository
Suite: unstable
Codename: raring
Architectures: i386 amd64 source
Components: main non-free contrib
Description: DataStage development repository for enabling multiple projects.

" > ./repo/conf/distributions

cd ./build
git clone https://github.com/mkozuharov/DataStage.git
cd ../

./reload_and_publish.sh

echo "#####################"
echo "add the following line at the end of /etc/apt/sources.list"
echo "for ubuntu 12:"
echo "deb file:${DIR}/repo quantal main"
echo "for ubuntu 13:"
echo "deb file:${DIR}/repo raring main"
echo
echo "after that run 'apt-get update' and 'apt-get install dataflow-datastage'"
echo "#####################"
echo
echo "to retrieve the latest code version and redeploy it you can run the 'reload_and_publish.sh' script in this directory"
echo "#####################"
