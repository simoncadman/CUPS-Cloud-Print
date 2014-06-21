#! /bin/bash

set -e
returnval=0

if [[ -d '/usr/share/cloudprint-cups/' ]]; then
    echo "/usr/share/cloudprint-cups/ dir still exists: "
    ls -alR /usr/share/cloudprint-cups/
    returnval=1
fi

cupsdir="/usr/lib/cups"

if [[ -d '/usr/libexec/cups' ]]; then
    cupsdir="/usr/libexec/cups"
fi


if [[ -e "$cupsdir/backend/gcp" ]]; then
    echo "$cupsdir/backend/gcp file still exists: "
    ls -alR $cupsdir/backend/gcp
    returnval=1
fi

if [[ -e "$cupsdir/driver/cupscloudprint" ]]; then
    echo "$cupsdir/driver/cupscloudprint file still exists: "
    ls -alR $cupsdir/driver/cupscloudprint
    returnval=1
fi

if [[ -e "/etc/cron.daily/cupscloudprint" ]]; then
    echo "/etc/cron.daily/cupscloudprint file still exists: "
    ls -alR /etc/cron.daily/cupscloudprint
    returnval=1
fi

exit $returnval