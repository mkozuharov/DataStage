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
