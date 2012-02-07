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

# rm /etc/libvirt/qemu/datastage.xml
# sudo /etc/init.d/libvirt-bin restart
HOSTNAME=%{HOSTNAME}
DOMAINNAME=%{DATASTAGEDOMAINNAME}
IPADDR=%{IPADDR}
PASSWD=%{PASSWORD}
if true; then
vmbuilder vmserver ubuntu \
  --suite karmic \
  --flavour virtual \
  --arch amd64 \
  --overwrite \
  --ip $IPADDR \
  --mask 255.255.252.0 \
  --gw 129.67.27.254 \
  --dns 129.67.1.1 \
  --bridge br0 \
  --part datastage.partitions \
  --user datastage \
  --pass $PASSWD \
  --domain $DOMAINNAME \
  --hostname $HOSTNAME \
  --addpkg acpid \
  --addpkg unattended-upgrades \
  --addpkg denyhosts \
  --addpkg ufw \
  --addpkg apache2 \
  --addpkg samba \
  --addpkg samba-doc \
  --addpkg krb5-user \
  --addpkg ntp \
  --addpkg libapache2-webauth \
  --addpkg libapache2-mod-auth-kerb \
  --addpkg cadaver \
  --addpkg nano \
  --addpkg slapd \
  --addpkg samba \
  --addpkg manpages \
  --addpkg man-db \
  --addpkg locate \
  --addpkg kernel-package \
  --addpkg linux-headers-2.6.31-20-server \
  --addpkg lvm2 \
  --addpkg acl \
  --copy config-files \
  --firstboot firstboot.sh \


# When using this, remove old XML files in /etc/libvirt/qemu and restart libvirt-bin service
# before running this script
#  --libvirt qemu:///system \

#  --addpkg libpam-krb5 \
#  --firstlogin login.sh \  # BUG: generated firstlogin script issues sudo command, requires password entry
#
fi
# mkdir -p VMBuilder/plugins/libvirt/templates
# cp /etc/vmbuilder/libvirt/* VMBuilder/plugins/libvirt/templates/
time=`date +%Y%m%dT%H%M`
mkdir $time
if [ -e ubuntu-vmserver/disk0.vmdk ]
then
    cp ubuntu-vmserver/disk0.vmdk $time
else
    echo Problem creating disk image
fi
if [ -e ubuntu-vmserver/$HOSTNAME.vmx ]
then
    cp ubuntu-vmserver/$HOSTNAME.vmx $time
else
    echo Problem creating VMX file
fi
