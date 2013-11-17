#! /bin/bash

set -e

cd "`dirname $0`"

export name="$1"
export category="$2"
export testconfig="$4"

if [[ ! -f /etc/cloudprint.conf ]]; then
        if [[ "`whoami`" == "root"  ]]; then
                wget $testconfig -O /etc/cloudprint.conf    

                # ensure cups running
                if [[ -f /etc/init.d/cupsd ]]; then
                        # running gentoo
                        /etc/init.d/cupsd start
                fi
        else
                sudo wget $testconfig -O /etc/cloudprint.conf
                
                # ensure cups running
                if [[ -f /etc/init.d/cupsd ]]; then
                        # running gentoo
                        sudo /etc/init.d/cupsd start
                fi
        fi
fi

py.test
