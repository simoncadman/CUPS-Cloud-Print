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

py.test
