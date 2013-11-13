#! /bin/bash

set -e

export name="$1"
export category="$2"
export testconfig="$4"

if [[ ! -f /etc/cloudprint.conf ]]; then
        sudo wget $testconfig -O /etc/cloudprint.conf
fi

py.test