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

if [[ "$1" != "test" && ! -e /mnt/data/data/DATASTAGE.README ]]; then
  echo "Allocate and mount data volume first (or use '$0 test')"
  echo "See http://imageweb.zoo.ox.ac.uk/wiki/index.php/DATASTAGE_LVM_allocation"
  exit
fi

if [[ "$1" == "test" ]]; then
  mkdir /mnt/data
  mkdir /mnt/data/home
  mkdir /mnt/data/data
  ln -s /mnt/data/data /home/data
fi

echo ===========================================
echo "Create and populate configuration directory"
echo ===========================================

mkdir -p /mnt/data/config
if [[ ! -e /root/datastageconfig.d ]]; then
    ln -s /mnt/data/config /root/datastageconfig.d
fi

for f in datastageconfig.sh; do  # (Used to be >1 file here; maybe again)
    ff=/mnt/data/config/$f
    if [[ -e "$ff" ]]; then
        echo "Copying new version of $f as $ff-new"
        cp -f /root/$f $ff-new
    else
        cp -f /root/$f $ff
    fi
done

echo ========================
echo "Installing DATASTAGE tools"
echo ========================

./datastagetoolsetup.sh

echo ===========================================
echo "Installing and configuring shared data area"
echo ===========================================

./datastagedatasetup.sh
/etc/init.d/apache2 restart

echo ===========================================
echo "Create user account for orphaned data files"
echo ===========================================


#smbldap-useradd -a -P -m -s /bin/false -g RGOrphan datastage-orphan

#smbldap-userinfo -f "Orphaned data" datastage-orphan

echo =================================
echo "Next step: configure system users"
echo =================================

mkdir -p /root/datastageconfig.d/datastageresearchgroupmembers
mkdir -p /root/datastageconfig.d/datastageresearchgrouporphans

# End.
