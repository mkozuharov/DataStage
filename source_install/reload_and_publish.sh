#!/bin/bash 
# this script retrieves the latest code version from github, builds the debian package and puts it in the repository

DIR=`pwd`
VER=`grep site_version ${DIR}/build/DataStage/debian-conf/datastage.conf | awk '{ print $3 }'`

cd ./build/DataStage
git pull origin
git checkout multiple-projects
dpkg-buildpackage -rfakeroot
fakeroot debian/rules clean

cd ../../repo
reprepro remove quantal dataflow-datastage
reprepro remove raring dataflow-datastage
reprepro -Vb . include quantal ${DIR}/build/dataflow-datastage_${VER}_amd64.changes
reprepro -Vb . include raring ${DIR}/build/dataflow-datastage_${VER}_amd64.changes
