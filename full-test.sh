#! /bin/bash

set -e

cd "`dirname $0`"

export name="$1"
export category="$2"
export testconfig="$4"

if [[ ! -f /etc/cloudprint.conf ]]; then
        if [[ "`whoami`" == "root"  ]]; then
                curl $testconfig -o /etc/cloudprint.conf
        else
                sudo curl $testconfig -o /etc/cloudprint.conf
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
LANG="en_GB.UTF-8" ./dynamicppd.py cat "`./dynamicppd.py list | head -n1 | cut -d'"' -f2`" > /tmp/test.ppd ; cupstestppd /tmp/test.ppd
LANG="en_US.UTF-8" ./dynamicppd.py cat "`./dynamicppd.py list | head -n1 | cut -d'"' -f2`" > /tmp/test.ppd ; cupstestppd /tmp/test.ppd
LANG="it_IT.UTF-8" ./dynamicppd.py cat "`./dynamicppd.py list | head -n1 | cut -d'"' -f2`" > /tmp/test.ppd ; cupstestppd /tmp/test.ppd