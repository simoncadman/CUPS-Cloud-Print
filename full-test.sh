#! /bin/bash

set -e

cd "`dirname $0`"

export name="$1"
export category="$2"
export testconfig="$4"

if [[ ! -f /etc/cloudprint.conf ]]; then
        if [[ "`whoami`" == "root"  ]]; then
                wget $testconfig -O /etc/cloudprint.conf    
        else
                sudo wget $testconfig -O /etc/cloudprint.conf
        fi
fi

if [[ "`whoami`" == "root"  ]]; then
       # ensure cups running
       if [[ -f /etc/init.d/cupsd ]]; then
          # running gentoo
          /etc/init.d/cupsd start
       fi
       
       hash systemctl
       if [[ $? == 0 ]]; then
          # running systemd
          systemctl start cups

          if [[ $? != 0  ]] ; then
               # run manually if systemctl fails
               cupsd -C /etc/cups/cupsd.conf
          fi
       fi
fi

py.test
