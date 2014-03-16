#! /bin/bash

set -e

cd "`dirname $0`/../"

if [[ $1 == "" ]]; then
    echo "This script is designed to be ran when creating packages, it shouldn't normally be ran by end users"
    exit 1
fi

export name="$1"
export category="$2"
export testconfig="$5"

if [[ ! -f /etc/cloudprint.conf ]]; then
        if [[ "`whoami`" == "root"  ]]; then
                scp -v $testconfig /etc/cloudprint.conf
        else
                sudo scp -v $testconfig /etc/cloudprint.conf
        fi
fi

if [[ "`whoami`" == "root"  ]]; then
       sed -i 's/LogLevel warn/LogLevel debug/g' /etc/cups/cupsd.conf 
       
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

echo "Permissions of config and logs:"
ls -al /etc/cloudprint.conf
ls -al /var/log/cups/

export PYTHONDONTWRITEBYTECODE=1

set +e
py.test2 -rxs --cov-report xml  --cov . || py.test -rxs --cov-report xml  --cov .
testresult=$?
ls -al /var/log/cups
cat /var/log/cups/cloudprint_log
cat /var/log/cups/error_log
ls -al /etc/cloudprint.conf
cat /etc/cloudprint.conf
set -e

if [[ $testresult != 0 ]]; then
    echo "Exited due to unit test errors"
    exit 1
fi

codecoverage=`fgrep "<coverage" coverage.xml | grep -Po 'line-rate="(.*?)"' | cut -d'"' -f2`
codecoveragepercent="`echo $codecoverage*100 | bc | cut -d'.' -f1`"
if [[ $codecoveragepercent -lt 85 ]]; then
    echo "Code coverage is only $codecoveragepercent , aborting"
    cat coverage.xml
    exit 1
else
    echo "Code coverage is $codecoveragepercent , continuing"
fi

unlink .coverage
unlink coverage.xml

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

./upgrade.py

ccpversion="`./setupcloudprint.py version`"

if [[ "`whoami`" == "root"  ]]; then
    ./setupcloudprint.py unattended
else
    sudo ./setupcloudprint.py unattended    
fi

# try pdf
pdfjobname="PDF CCP Test $ccpversion at `date`"
printfilepath="/usr/share/cloudprint-cups/testing/testfiles/Test Page.pdf"
if [[ -e "/usr/local/share/cloudprint-cups/testing/testfiles/Test Page.pdf" ]]; then
    printfilepath="/usr/local/share/cloudprint-cups/testing/testfiles/Test Page.pdf"
fi
lp "$printfilepath" -d 'GCP-Save_to_Google_Docs' -t "$pdfjobname"
echo "Submitted job $pdfjobname"

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
    echo "PDF Job failed to submit in 30 seconds"
    lpstat -W all
    exit 1
fi

# try postscript file
psjobname="Postscript CCP Test $ccpversion at `date`"
printfilepath="/usr/share/cloudprint-cups/testing/testfiles/Test Page.ps"
if [[ -e "/usr/local/share/cloudprint-cups/testing/testfiles/Test Page.ps" ]]; then
    printfilepath="/usr/local/share/cloudprint-cups/testing/testfiles/Test Page.ps"
fi

lp "$printfilepath" -d 'GCP-Save_to_Google_Docs' -t "$psjobname"
echo "Submitted job $psjobname"

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

# try postscript from adobe reader
psreaderjobname="Reader Postscript CCP Test $ccpversion at `date`"
printfilepath="/usr/share/cloudprint-cups/testing/testfiles/Test Page reader.ps"
if [[ -e "/usr/local/share/cloudprint-cups/testing/testfiles/Test Page reader.ps" ]]; then
    printfilepath="/usr/local/share/cloudprint-cups/testing/testfiles/Test Page reader.ps"
fi

lp "$printfilepath" -d 'GCP-Save_to_Google_Docs' -t "$psreaderjobname"
echo "Submitted job $psreaderjobname"

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
    echo "Postscript Job failed to submit in 30 seconds"
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

if [[ `./testing/listdrivefiles.py "$pdfjobname"` -lt 100000 ]]; then
    echo "Uploaded pdf file does not match expected size:"
    ./testing/listdrivefiles.py "$pdfjobname"
    exit 1
else
    echo "Uploaded pdf file matches expected size"
fi

if [[ `./testing/listdrivefiles.py "$psjobname"` -lt 100000 ]]; then
    echo "Uploaded ps file does not match expected size:"
    ./testing/listdrivefiles.py "$psjobname"
    exit 1
else
    echo "Uploaded ps file matches expected size"
fi

if [[ `./testing/listdrivefiles.py "$psreaderjobname"` -lt 100000 ]]; then
    echo "Uploaded ps reader file does not match expected size:"
    ./testing/listdrivefiles.py "$psreaderjobname"
    exit 1
else
    echo "Uploaded ps reader file matches expected size"
fi

tail /var/log/cups/cloudprint_log
