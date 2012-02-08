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

if [[ "$1" == "" || "$2" == "" || "$3" == "" ]]; then
  echo "Usage: $0 username fullname role [room number] [work phone] [password]"
  exit 1
fi

if [[ -e "/home/$1" || -e "/mnt/data/home/$1" ]]; then
  echo "User $1 already exists (or home directory exists)"
  exit 1
fi

if [[ -e "/root/datastageconfig.d/datastageresearchgroupmembers/$1.sh" ]]; then
  echo "User $1 configuration record already exists"
  exit 1
fi

if [[ -e "/root/datastageconfig.d/datastageresearchgrouporphans/$1.sh" ]]; then
  echo "Deleted user $1 configuration record already exists"
  exit 1
fi

source /root/datastageconfig.d/datastageconfig.sh
source /root/datastageusermanagement.sh

generateuserrecord "$1" "$2" "$3" "$4" "$5"
generatesystemuser /root/datastageconfig.d/datastageresearchgroupmembers/$1.sh $6
generatesystemuserhomedir $1

# End.
