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

# This script will run the first time the virtual machine boots
# It is run as root.

echo "*****FIRST BOOT*****"

mv /etc/sudoers /etc/sudoers-orig
chmod 440 /root/sudoers
cp /root/sudoers /etc/sudoers
#chmod 440 /etc/sudoers
smbpasswd -s -a datastage <<END
%{PASSWORD}
%{PASSWORD}
END

a2enmod ssl
a2ensite default-ssl

#a2enmod webauth
#a2enmod auth_kerb
#ln -s /var/lib/webauth /etc/apache2/webauth
#cp /root/webauth.keytab /etc/apache2/webauth/keytab
#chgrp www-data /etc/apache2/webauth/keytab
#chmod u=rw,g=r,o= /etc/apache2/webauth/keytab
#cp /root/krb5.keytab /etc/krb5.keytab
#chmod u=rw,go= /etc/krb5.keytab
#cp /root/webdav.keytab /etc/apache2/webdav.keytab
#chown root:www-data /etc/apache2/webdav.keytab
#chmod 640 /etc/apache2/webdav.keytab

mkdir /home/data
chown www-data: /home/data
chmod g+ws /home/data
cp /root/DATASTAGE.README /home/data

chmod +x /root/make-apache2-cert.sh
/root/make-apache2-cert.sh %{HOSTFULLNAME}
cp /root/apache-default-ssl /etc/apache2/sites-available/default-ssl

a2enmod dav
a2enmod dav_fs
mkdir /usr/share/apache2/var
touch /usr/share/apache2/var/DAVlock
chown -R www-data:www-data /usr/share/apache2/var
mv /etc/apache2/sites-available/default /etc/apache2/sites-available/default_orig
cp /root/apache-default /etc/apache2/sites-available/default

a2enmod proxy
a2enmod proxy_http

/etc/init.d/apache2 restart

