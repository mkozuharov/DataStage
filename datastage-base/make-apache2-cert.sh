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

#!/bin/sh
umask 077

answers() {
	echo --
	echo Oxfordshire
	echo Oxford
	echo University of Oxford
	echo Zoology Department
	echo %{HOSTFULLNAME}
	echo root@%{HOSTFULLNAME}
}

if [ $# -eq 0 ] ; then
	echo $"Usage: `basename $0` filename [...]"
	exit 0
fi

TARGETKEYDIR=/etc/ssl/private
TARGETCRTDIR=/etc/ssl/certs

#For testing:
#TARGETKEYDIR=.
#TARGETCRTDIR=. 

for target in $@ ; do
	PEM1=`/bin/mktemp /tmp/openssl.XXXXXX`
	PEM2=`/bin/mktemp /tmp/openssl.XXXXXX`
	rm -f $PEM1 $PEM2
	answers | /usr/bin/openssl req -newkey rsa:1024 -keyout $PEM1 -nodes -x509 -days 365 -out $PEM2 2> /dev/null        
	cat $PEM1 > $TARGETKEYDIR/${target}.key
        chown root:ssl-cert $TARGETKEYDIR/${target}.key
        chmod o=rw,g=r,o=   $TARGETKEYDIR/${target}.key
	cat $PEM2 > $TARGETCRTDIR/${target}.pem
        chown root: $TARGETCRTDIR/${target}.pem
        chmod a+r   $TARGETCRTDIR/${target}.pem
	rm -f $PEM1 $PEM2
done
