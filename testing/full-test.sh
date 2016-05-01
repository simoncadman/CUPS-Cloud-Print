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

if [[ "`uname`" != "Darwin"  && ! -f /etc/cron.daily/cupscloudprint ]]; then
        echo "Crontab entry in /etc/cron.daily/cupscloudprint is missing:"
        ls -al /etc/cron.daily/
        exit 1
fi

if [[ "`uname`" == "Darwin"  && ! -f /Library/LaunchDaemons/cupscloudprint.plist ]]; then
        echo "Launchd entry in /Library/LaunchDaemons/cupscloudprint.plist is missing:"
        ls -al /Library/LaunchDaemons/
        exit 1
fi

echo "Listing /etc/:"
ls -al /etc/

if [[ ! -f /etc/cloudprint.conf ]]; then
        if [[ "`whoami`" == "root"  ]]; then
		echo "Fetching $testconfig to /etc/cloudprint.conf"
                scp -v $testconfig /etc/cloudprint.conf
        else
		echo "Fetching $testconfig to /etc/cloudprint.conf with sudo"
                sudo scp -v $testconfig /etc/cloudprint.conf
        fi
fi

if [[ "`whoami`" == "root"  ]]; then
       if [[ "`uname`" == "Darwin" ]]; then
           sed -i '.backup' 's/LogLevel warn/LogLevel debug/g' /etc/cups/cupsd.conf 
       else
           sed -i 's/LogLevel warn/LogLevel debug/g' /etc/cups/cupsd.conf 
       fi
       
       # ensure cups running
       if [[ -f /etc/init.d/cupsd ]]; then
          # running gentoo
          /etc/init.d/cupsd start
       fi
       
       # start via systemctl if exists
       hash systemctl && ( systemctl start cups || cupsd )
       
       # start via 'start' if exists
       hash start && ( ( start cups ; restart dbus ) || cupsd )
       
       hash launchctl && ( launchctl stop org.cups.cupsd; launchctl start org.cups.cupsd )
fi

if [[ "`whoami`" == "root"  ]]; then
    if command -v python2 > /dev/null; then
      python2 -m compileall .
    else
      python -m compileall .
    fi

else
    sudo python2 -m compileall .
fi

echo "Permissions of config and logs before upgrade:"
ls -al /etc/cloudprint.conf
ls -al /var/log/cups/

./upgrade.py

echo "Permissions of config and logs after upgrade:"
ls -al /etc/cloudprint.conf
ls -al /var/log/cups/

if [[ "`uname`" != "Darwin" ]]; then
	/etc/cron.daily/cupscloudprint
fi

export PYTHONDONTWRITEBYTECODE=1

pwd
cat .coveragerc

set +e

skipcoverage=0

export PATH="$PATH:/usr/local/bin"

if [[ "`cat /etc/*release* | fgrep -c 'CentOS release 6.'`" -gt "0"  ]]; then
        py.test2 -rfEsxw . | py.test -rfEsxw .
	skipcoverage=1
else
	py.test2 -rfEsxw --cov-report xml  --cov . || py.test -rfEsxw --cov-report xml --cov .
fi
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

if [[ $skipcoverage == 0 ]]; then

	codecoverage=`fgrep "<coverage" coverage.xml | grep -Eo 'line-rate="(.*?)"' | cut -d'"' -f2`
	codecoveragepercent="`echo $codecoverage*100 | bc | cut -d'.' -f1`"
	if [[ $codecoveragepercent -lt 85 ]]; then
	    echo "Code coverage is only $codecoveragepercent , aborting"
	    cat coverage.xml
	    exit 1
	else
	    echo "Code coverage is $codecoveragepercent , continuing"
	fi
	unlink coverage.xml
	unlink .coverage
fi


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

echo "Printing: $printfilepath"
ls -al "$printfilepath"
file "$printfilepath"
lp "$printfilepath" -d 'GCP-Save_to_Google_Drive' -t "$pdfjobname"
echo "Submitted job $pdfjobname"

success=0
for i in {1..60}
do
   echo "Waiting for job to complete: $i of 60 tries"
   jobcount="`lpstat -W not-completed | wc -l`"
   if [[ $jobcount -eq 0 ]]; then
        success=1
        break
   fi
   sleep 1
done

if [[ $success == 0 ]]; then
    echo "PDF Job failed to submit in 60 seconds"
    lpstat -W all
    cat /var/log/cups/cloudprint_log
    cat /var/log/cups/error_log
    exit 1
fi

# try postscript file
psjobname="Postscript CCP Test $ccpversion at `date`"
printfilepath="/usr/share/cloudprint-cups/testing/testfiles/Test Page.ps"
if [[ -e "/usr/local/share/cloudprint-cups/testing/testfiles/Test Page.ps" ]]; then
    printfilepath="/usr/local/share/cloudprint-cups/testing/testfiles/Test Page.ps"
fi

echo "Printing: $printfilepath"
ls -al "$printfilepath"
file "$printfilepath"
lp "$printfilepath" -d 'GCP-Save_to_Google_Drive' -t "$psjobname"
echo "Submitted job $psjobname"

success=0
for i in {1..60}
do
   echo "Waiting for job to complete: $i of 60 tries"
   jobcount="`lpstat -W not-completed | wc -l`"
   if [[ $jobcount -eq 0 ]]; then
        success=1
        break
   fi
   sleep 1
done

if [[ $success == 0 ]]; then
    echo "Postscript Job failed to submit in 60 seconds"
    lpstat -W all
    cat /var/log/cups/cloudprint_log
    cat /var/log/cups/error_log
    exit 1
fi

# try postscript from adobe reader
psreaderjobname="Reader Postscript CCP Test $ccpversion at `date`"
printfilepath="/usr/share/cloudprint-cups/testing/testfiles/Test Page reader.ps"
if [[ -e "/usr/local/share/cloudprint-cups/testing/testfiles/Test Page reader.ps" ]]; then
    printfilepath="/usr/local/share/cloudprint-cups/testing/testfiles/Test Page reader.ps"
fi

echo "Printing: $printfilepath"
ls -al "$printfilepath"
file "$printfilepath"
lp "$printfilepath" -d 'GCP-Save_to_Google_Drive' -t "$psreaderjobname"
echo "Submitted job $psreaderjobname"

success=0
for i in {1..60}
do
   echo "Waiting for job to complete: $i of 60 tries"
   jobcount="`lpstat -W not-completed | wc -l`"
   if [[ $jobcount -eq 0 ]]; then
        success=1
        break
   fi
   sleep 1
done

if [[ $success == 0 ]]; then
    echo "Reader Postscript Job failed to submit in 60 seconds"
    lpstat -W all
    cat /var/log/cups/cloudprint_log
    cat /var/log/cups/error_log
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

# wait until files exist
success=0
for i in {1..60}
do
   echo "Waiting for files to exist: $i of 60 tries"
   if [[ `./testing/listdrivefiles.py "$psreaderjobname"` != "" && `./testing/listdrivefiles.py "$psjobname"` != "" && `./testing/listdrivefiles.py "$pdfjobname"` != "" ]]; then
        break
   fi
   sleep 1
done

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
