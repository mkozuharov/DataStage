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
# Commands to create a data volume on the disk partition at /dev/sdb1,
# copy files from the /home/data directory, and symlink /home/data to the
# new data location
#
# This is the default case for a new system build when using a single 
# separate disk volume for DATASTAGE data

pvcreate /dev/sdb1
vgcreate vg-datastage-data /dev/sdb1
lvcreate --name lv-datastage-data --extents 100%FREE vg-datastage-data
mkfs.ext3 /dev/vg-datastage-data/lv-datastage-data
mkdir /mnt/lv-datastage-data
mount /dev/vg-datastage-data/lv-datastage-data /mnt/lv-datastage-data
if [[ -L /mnt/data ]]; then
    # /mnt/data is symlink
    rm /mnt/data
elif [[ -e /mnt/data ]]; then
    # /mnt/data is directory
    mv /mnt/data /mnt/data-saved
fi
ln -s /mnt/lv-datastage-data-ext/ /mnt/data
cd /home
cp -axv data/ /mnt/data/
mv data data-saved
ln -s /mnt/data/data/ data
mkdir /mnt/data/home 

# End.
