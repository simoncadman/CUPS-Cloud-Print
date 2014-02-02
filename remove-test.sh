#! /bin/bash

set -e

if [[ -d '/usr/share/cloudprint-cups/' ]]; then
    echo "/usr/share/cloudprint-cups/ dir already exists: "
    ls -alR /usr/share/cloudprint-cups/
    exit 1
fi