#! /bin/bash

set -e

cd "`dirname $0`"

export name="$1"
export category="$2"
export testconfig="$5"

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

if [[ "`whoami`" == "root"  ]]; then
    python2 -m compileall .
else
    sudo python2 -m compileall .
fi

export PYTHONDONTWRITEBYTECODE=1

py.test2 || py.test

export PYTHONDONTWRITEBYTECODE=0

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

ccpversion="`./setupcloudprint.py version`"
osversion="`cat /proc/version`"
jobname="CCP Test $ccpversion on $osversion at `date`"
pdfpath="/usr/share/cloudprint-cups/testfiles/Test Page.pdf"
if [[ -e "/usr/local/share/cloudprint-cups/testfiles/Test Page.pdf" ]]; then
    pdfpath="/usr/local/share/cloudprint-cups/testfiles/Test Page.pdf"
fi
if [[ "`whoami`" == "root"  ]]; then
    ./setupcloudprint.py unattended
else
    sudo ./setupcloudprint.py unattended    
fi
lp "$pdfpath" -d 'GCP-Save_to_Google_Docs' -t "$jobname"
echo "Submitted job $jobname"

success=0
for i in {1..30}
do
   echo "Waiting for job to complete: $i of 30 tries"
   jobcount="`lpstat -W not-completed | wc -l`"
   if [[ $jobcount == 0 ]]; then
        success=1
        break
   fi
   sleep 1
done

if [[ $success == 0 ]]; then
    echo "Job failed to submit in 30 seconds"
    lpstat -W all
    exit 1
fi

if [[ $testconfig != "" ]]; then
    # download drive config file so we can check if file exists on drive correctly
    if [[ "`whoami`" == "root"  ]]; then
            scp $testconfig.drive /etc/cloudprint.conf
    else
            sudo scp $testconfig.drive /etc/cloudprint.conf
    fi
fi

if [[ `./listdrivefiles.py "$jobname"` -lt 100000 ]]; then
    echo "Uploaded file does not match expected size"
    exit 1
else
    echo "Uploaded file matches expected size"
fi

tail /var/log/cups/cloudprint_log