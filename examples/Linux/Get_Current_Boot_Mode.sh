#!/bin/bash

#    RESTful Interface Tool Sample Script for HPE iLO Products    #
#  Copyright 2014, 2019 Hewlett Packard Enterprise Development LP #

# Description: This is a sample bash script to get the current    #
#              boot mode.                                         #

# NOTE:  You will need to replace the USER_LOGIN and PASSWORD     #
#        and other values inside the quotation marks with values  #
#        that are appropriate for your environment.               #

#        Firmware support information for this script:            #
#            iLO 5 - All versions                                 #
#            iLO 4 - version 1.40 or later.                       #
runLocal(){
  ilorest get BootMode --selector=Bios. -u USER_LOGIN -p PASSWORD
  ilorest logout
}

runRemote(){
  ilorest get BootMode --selector=Bios. --url=$1 --user $2 --password $3
  ilorest logout
}

error(){
  echo "Usage:"
  echo        "remote: Get_Current_Boot_Mode.sh ^<iLO url^> ^<iLO username^>  ^<iLO password^>"
  echo        "local:  Get_Current_Boot_Mode.sh"
}

if [ "$#" -eq "3" ]
then 
  runRemote "$1" "$2" "$3"
elif [ "$#" -eq "0" ]
then
  runLocal
else
  error
fi