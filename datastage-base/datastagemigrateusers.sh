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

if [[ "$1" == "" ]]; then
    echo "Usage:"
    echo "  $0 username"
    echo "      Generate system configuration for named user" 
    echo ""
    echo "  $0 all password"
    echo "      Generate system configuration for all recorded DATASTAGE users" 
    echo "      Each user gets a password of the form 'username-password',"
    echo "      which they should change on first login." 
    echo ""
    echo "  $0 fileaccess"
    echo "      Scan all files for configured DATASTAGE users and set file " 
    echo "      ownership and permissions."
    echo ""
    exit
fi

if [[ "$1" == "all" ]]; then
    if [[ "$2" == "" ]]; then
        echo "Provide password suffix when regenerating all user accounts"
        exit
    fi
elif [[ "$1" == "fileaccess" ]]; then
    echo "Updating data volume file ownership and access"
else
    if [[ ! -e /root/datastageconfig.d/datastageresearchgroupmembers/$1.sh ]]; then
        echo "No such user recorded: $1"
        exit
    fi
fi
 
source /root/datastageconfig.d/datastageconfig.sh

source /root/datastageusermanagement.sh

# Process all user files in /root/datastageconfig.d/a/root/datastageresearchgroupmembers

if [[ "$1" == "all" ]]; then
    for u in `ls /root/datastageconfig.d/datastageresearchgroupmembers/*.sh`; do
        #@@TODO: save password hash with user record; use this to reinstate?
        #        (problem: may make user susceptible to dictionary attack, etc.)
        source $u
        echo "Migrate user $username..."
        password=$username-$2
        generatesystemuser $u $password
        generatesystemuserhomedir $username
        echo "Migrate user $username done."
    done

    for u in `ls /root/datastageconfig.d/datastageresearchgrouporphans/*.sh`; do
        source $u
        echo "Orphan user $username..."
        setdataownerandaccess $username datastage-orphan RGOrphan
        echo "Orphan user $username done."
    done
    
elif [[ "$1" == "fileaccess" ]]; then
    for u in `ls /root/datastageconfig.d/datastageresearchgroupmembers/*.sh`; do       
        source $u
        if [[ "$userrole" == "RGMember" || "$userrole" == "RGLeader" ]]; then
            echo "Set file access for user $username as $userrole ..."
            setdataownerandaccess $username $username $userrole
        fi
    done

    for u in `ls /root/datastageconfig.d/datastageresearchgrouporphans/*.sh`; do
        source $u
        echo "Set file access for orphan $username..."
        setdataownerandaccess $username datastage-orphan RGOrphan
    done

elif [[ -e "/root/datastageconfig.d/datastageresearchgroupmembers/$1.sh" ]]; then
    echo "Migrate designated user $1"
    generatesystemuser /root/datastageconfig.d/datastageresearchgroupmembers/$1.sh    
    generatesystemuserhomedir $1
    echo "Migrate user $1 done."

else
    echo "No such user ($1)"
fi

# End.
