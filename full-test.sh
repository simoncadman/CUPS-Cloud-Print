#! /bin/bash

set -e

cd "`dirname $0`"

export name="$1"
export category="$2"
export testconfig="$4"

if [[ ! -f /etc/cloudprint.conf ]]; then
        if [[ "`whoami`" == "root"  ]]; then
                scp $testconfig /etc/cloudprint.conf
        else
                sudo scp $testconfig /etc/cloudprint.conf
        fi
fi

if [[ "`whoami`" == "root"  ]]; then
       # ensure cups running
       if [[ -f /etc/init.d/cupsd ]]; then
          # running gentoo
          /etc/init.d/cupsd start
       fi
       
       # start via systemctl if exists
       hash systemctl && ( systemctl start cups || cupsd )
       
       # start via 'start' if exists
       hash start && ( start cups || cupsd )
fi

py.test2 || py.test

printers="`./dynamicppd.py list | cut -d'"' -f2`"
langs="en_GB.UTF-8
en_US.UTF-8
it_IT.UTF-8"

for printer in $printers; do
    for lang in $langs; do
        echo "Testing $printer with $lang"
        LANG="$lang" ./dynamicppd.py cat "$printer" > /tmp/test.ppd
        cupstestppd /tmp/test.ppd
    done
done
