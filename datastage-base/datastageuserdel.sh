#!/bin/bash

source /root/datastageconfig.d/datastageconfig.sh

if [[ "$1" == "" ]]; then
  echo "Usage: $0 username [purge]"
  exit 1
else 

  if [[ "$2" == "purge" ]]; then

    rm -rf "/home/data/private/$1"
    rm -rf "/home/data/shared/$1"
    rm -rf "/home/data/collab/$1"
    rm -rf "/mnt/data/home/$1"
    rm -rf "/home/$1"
    rm -rf "/home/$1-saved"
    rm -rf "/home/$1-deleted"
    
    rm -f /etc/apache2/conf.d/user.$1
    rm -f /root/datastageconfig.d/datastageresearchgroupmembers/$1.sh
    rm -f /etc/apache2/conf.d/orphan.$1
    rm -f /root/datastageconfig.d/datastageresearchgrouporphans/$1.sh
    
  else

    chown -R datastage-orphan:RGOrphan /home/data/private/$1
    chown -R datastage-orphan:RGOrphan /home/data/shared/$1
    chown -R datastage-orphan:RGOrphan /home/data/collab/$1
    chown -R datastage-orphan:RGOrphan /mnt/data/home/$1
    # (-L tests for symlink ...)
    if [[ -L "/home/$1" ]]; then
      rm "/home/$1"
    elif [[ -e "/home/$1" ]]; then
      mv "/home/$1" "/home/$1-deleted"
    fi
    if [[ -e "/home/$1-saved" ]]; then
      mv /home/$1-saved /home/$1
    fi
  
    mv /etc/apache2/conf.d/user.$1 /etc/apache2/conf.d/orphan.$1
    mkdir -p /root/datastageconfig.d/datastageresearchgrouporphans
    mv /root/datastageconfig.d/datastageresearchgroupmembers/$1.sh /root/datastageconfig.d/datastageresearchgrouporphans/
  fi
  
  smbpasswd -x $1
  userdel -r $1
 
fi

# End.
