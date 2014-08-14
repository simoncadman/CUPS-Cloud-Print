Name:           cupscloudprint
Version:        %{_version}
Release:        1
Summary:        Print via Google Cloud print using CUPS

License:        GPLv3+
URL:            http://ccp.niftiestsoftware.com
Source0:        http://ccp.niftiestsoftware.com/cupscloudprint-%{_version}.tar.bz2

BuildArch:      noarch
BuildRequires:  python2-devel,cups-devel,cups,make
Requires:       cups,system-config-printer-libs,python-httplib2,ghostscript,ImageMagick

%description
Google Cloud Print driver for UNIX-like operating systems.
It allows any application which prints via CUPS to print to Google Cloud 
Print directly.

%prep
%setup -q


%build
%configure
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT NOPERMS=1
%{__install} -Dp -m0744 cron.daily/cupscloudprint %{buildroot}%{_sysconfdir}/cron.daily/cupscloudprint
cd "$RPM_BUILD_ROOT"
python2 -m compileall -q -f .

%post
%{_usr}/share/cloudprint-cups/upgrade.py

# load selinux module if running selinux
hash semodule > /dev/null 2>&1
if [[ "$?" == 0 ]]; then
    semodule -i %{_usr}/share/cloudprint-cups/selinux/cupscloudprint.pp
    if [[ -f "%{_sysconfdir}/cloudprint.conf" ]]; then
        restorecon -RF "%{_sysconfdir}/cloudprint.conf"
    fi
    
    if [[ -d "%{_usr}/share/cloudprint-cups/" ]]; then
        restorecon -RF "%{_usr}/share/cloudprint-cups/"
    fi
    
    if [[ -d "%{_localstatedir}/log" ]]; then
        restorecon -RF "%{_localstatedir}/log"
    fi
fi

%postun
# remove selinux module if running selinux
if [[ $1 == 0 ]]; then
    hash semodule > /dev/null 2>&1
    if [[ "$?" == 0 ]]; then
        semodule -r cupscloudprint
        if [[ -f "%{_sysconfdir}/cloudprint.conf" ]]; then
            restorecon -RF "%{_sysconfdir}/cloudprint.conf"
        fi
        
        if [[ -d "%{_usr}/share/cloudprint-cups/" ]]; then
            restorecon -RF "%{_usr}/share/cloudprint-cups/"
        fi
        
        if [[ -d "%{_localstatedir}/log" ]]; then
            restorecon -RF "%{_localstatedir}/log"
        fi
    fi
fi

%files
%dir %{_usr}/share/cloudprint-cups/
%dir %{_usr}/share/cloudprint-cups/oauth2client
%dir %{_usr}/share/cloudprint-cups/testing
%dir %{_usr}/share/cloudprint-cups/selinux
%docdir %{_usr}/share/cloudprint-cups/testing/testfiles
%{_usr}/%{_lib}/cups/backend/gcp
%{_usr}/%{_lib}/cups/driver/cupscloudprint
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/.coveragerc
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/auth.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/cloudprintrequestor.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/printer.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/printermanager.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/__init__.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/anyjson.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/client.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/clientsecrets.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/crypt.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/locked_file.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/multistore_file.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/ccputils.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/backend.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/deleteaccount.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/dynamicppd.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/listcloudprinters.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/reportissues.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/refreshtokens.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/setupcloudprint.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/upgrade.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/*.pyc
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/*.pyo
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/*.pyc
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/*.pyo
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/testing/*
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/testing/*.sh
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/testing/testfiles
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/testing/testfiles/*
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/testing/listdrivefiles.py
%attr(744, root, root) %{_sysconfdir}/cron.daily/cupscloudprint
%attr(644, root, root) %{_usr}/share/cloudprint-cups/selinux/*
%doc %{_usr}/share/cloudprint-cups/COPYING
%doc %{_usr}/share/cloudprint-cups/README.md

%changelog
* Thu Aug 14 2014 Simon Cadman <src@niftiestsoftware.com> (20140814-1)
- Fix: Issue #71 on Github, always send use_cdd=false param with every request

* Wed Jul 02 2014 Simon Cadman <src@niftiestsoftware.com> (20140702-1)
- New: Split printer class into seperate Printer and PrinterManager classes
- New: OS X package support
- New: Added SELinux support to RPM packages
- New: Added refresh token cron script
- Fix: Use python interpreter when python2 interpreter not available.
- Fix: Setup script shows printer names in multiple columns, instead of one column.
- Fix: Now PEP8 compliant
- Fix: Detect _lp as valid cups group in configure script
- Change: Moved testing data and scripts into 'testing' subdirectory
- Change: Changed protocol to gcp:// instead of cloudprint://

* Sat Mar 08 2014 Simon Cadman <src@niftiestsoftware.com> (20140308-1)
- Fix: Use shorter URI format to workaround issue on older distros having a short max length on printer URIs

* Fri Mar 07 2014 Simon Cadman <src@niftiestsoftware.com> (20140307-1)
- New: Show better error message if printer ppd not found
- Fix: Use python logging facility instead of writing to log files directly, fixes No handlers could be found for logger error
- Fix: Upgrade script now faster with multiple printers, now only gets list of PPDs once and filters for each printer
- Fix: Show better error if renewing OAUTH2 token fails
- Fix: Explicitely define dirs in rpm files list, ensures will be removed correctly on uninstall
- Fix: Deb package now deletes old pyc files on uninstall/upgrade
- Fix: Config file permissions now fixed to allow updating of access token when printing
- Fix: Compile python code on rpm install to ensure old files are removed on uninstall
- Fix: Compile python code on arch install to ensure old files are removed on uninstall
- Fix: Compile python code on Gentoo install to ensure old files are removed on uninstall
- Change: Merged submitjob.py script into backend script
- Change: Error out immediately if lpadmin command not in path on upgrade

* Mon Feb 10 2014 Simon Cadman <src@niftiestsoftware.com> (20140210-1)
- New: Show better error message if printer ppd not found
- Fix: Use python logging facility instead of writing to log files directly, fixes No handlers could be found for logger error
- Fix: Upgrade script now faster with multiple printers, now only gets list of PPDs once and filters for each printer
- Fix: Show better error if renewing OAUTH2 token fails
- Fix: Explicitely define dirs in rpm files list, ensures will be removed correctly on uninstall
- Fix: Deb package now deletes old pyc files on uninstall/upgrade
- Fix: Config file permissions now fixed to allow updating of access token when printing
- Fix: Compile python code on rpm install to ensure old files are removed on uninstall
- Fix: Compile python code on arch install to ensure old files are removed on uninstall
- Fix: Compile python code on Gentoo install to ensure old files are removed on uninstall
- Change: Merged submitjob.py script into backend script
- Change: Error out immediately if lpadmin command not in path on upgrade

* Sun Jan 12 2014 Simon Cadman <src@niftiestsoftware.com> (20140112-1)
- New: Added test script for post-packaging testing
- New: Can now delete associated printers when deleting an account
- New: When invalid OAuth2 shown, show the error message
- Change: Moved files from /usr/lib/ to /usr/share

* Sun Oct 13 2013 Simon Cadman <src@niftiestsoftware.com> (20131013-1)
- Change: Use imagemagick for rotating PDFs instead of pdfjam due to issues with CentOS and Fedora

* Wed Oct 09 2013 Simon Cadman <src@niftiestsoftware.com> (20131009-1)
- New: Use display name if available for generating values for ppd
- New: Added version param to scripts
- New: Added test cases and list of capabilities for testing internal name function
- Fix: Prevent duplicate options and capabilities being generated
- Fix: Post name of capability instead of internal hash, should fix issues with capabilities failing to work correctly
- Fix: Fixed displaying of errors from Google side ( eg when print proxy is down )
- Fix: Allow overriding print params per print job
- Change: Removed gcp_ prefix for capabilities ( unless conflicts with reserved words )

* Sat Sep 14 2013 Simon Cadman <src@niftiestsoftware.com> (20130914-1)
- New: Use display name if available for generating values for ppd
- New: Added version param to scripts
- New: Added test cases and list of capabilities for testing internal name function
- Fix: Prevent duplicate options and capabilities being generated
- Fix: Post name of capability instead of internal hash, should fix issues with capabilities failing to work correctly
- Fix: Fixed displaying of errors from Google side ( eg when print proxy is down )
- Fix: Allow overriding print params per print job
- Change: Removed gcp_ prefix for capabilities ( unless conflicts with reserved words )

* Thu Jul 18 2013 Simon Cadman <src@niftiestsoftware.com> (20130718-1)
- New: PDF now supplied to CCP via CUPS, increases printing speed.
- New: Default to A4 paper size in countries that use A4 paper.
- Fix: Use utf8 output for ppd, use internal option and capability hashes for names to prevent errors - should fix a lot of errors related to non-ASCII chars in capabilities.
- Fix: Removed redundant ppdc dependencies.
- Fix: Removed old PPD files, as no longer used.
- Fix: Optimise PDF generated for printing.
- Fix: Only ask once per account for prefix.
- Fix: CUPS Backend etc now use source install by default.
- Fix: Custom printer name should now work.
- Fix: Fixed final warnings in PPD.
- Fix: Add translations into cups ppdc.

* Sat Jun 08 2013 Simon Cadman <src@niftiestsoftware.com> (20130608-1)
- Fix: Parameters with long names should no longer error.

* Tue Jun 04 2013 Simon Cadman <src@niftiestsoftware.com> (20130604-1)
- Fix: Fixed syntax error on adding individual printers.

* Mon Jun 03 2013 Simon Cadman <src@niftiestsoftware.com> (20130603-1)
- New: Added reportissues.py script to assist in debugging issues.
- Change: On answering no for adding all printers, ask to add individual printers.
- Change: Ask whether or not to use prefix rather than assuming user knows to enter prefix directly.
- Fix: Use option name instead of displayname if displayname is missing.

* Sun May 26 2013 Simon Cadman <src@niftiestsoftware.com> (20130526-1)
- Fix: Strip out colon chars from capability and options in ppd. 

* Sun May 19 2013 Simon Cadman <src@niftiestsoftware.com> (20130519-1)
- Fix: No longer error on capabilities with missing display name.

* Fri May 10 2013 Simon Cadman <src@niftiestsoftware.com> (20130510-1)
- Fix: Deb package installs cloudprint files with correct permissions.
- Fix: Only update config file permissions when config options changed, not when tokens refreshed.

* Sat May 04 2013 Simon Cadman <src@niftiestsoftware.com> (20130504-1)
- New: Capabilities for printer supplied by Google Cloud Print ( eg Colour, Print tray, etc ) now appear as options in dialogs.
- New: Script to delete user accounts ( deleteaccount.py )
- Change: PPD file now generated dynamically
- Fix: RPM package can now be built as a non-root user.

* Sun Feb 03 2013 Simon Cadman <src@niftiestsoftware.com> (20130203-1)
- Major Fix: Ensure printing is always sent over HTTPS, fixes an issue where Google has began returning errors on HTTP API requests
- New: Extra debug data now logged if JSON decoding fails
- New: Added gentoo/freebsd support
- Change: Detect CUPS user group automatically rather than assume group name is always lp

* Tue Jan 01 2013 Simon Cadman <src@niftiestsoftware.com> (20130101-1)
- New: Python 2.6 now properly supported

* Sat Dec 08 2012 Simon Cadman <src@niftiestsoftware.com> (20121208-1)
- New: Added FedEx office support

* Sun Dec 02 2012 Simon Cadman <src@niftiestsoftware.com> (20121202-1)
- Change: Backwards compatiblity changes for older versions of python
- Fix: Show all printers, including ones marked as dormant
- Fix: Issue #16 - Arch package, cupsddk dependency is discontinued.
- Fix: Depend on system-config-printer-libs instead of python-cups in RPM

* Sat Sep 08 2012 Simon Cadman <src@niftiestsoftware.com> (20120908-1)
- Fix: Issue #13 - Invalid CUPS printer name generated

* Thu Aug 23 2012 Simon Cadman <src@niftiestsoftware.com> (20120823-1)
- Fix: Fixed error when trying to print to printers with an account name containing an '@' symbol ( commit 8b8cc6edf419656e192ce82dd0e8cf662d80a54a )

* Sat Aug 18 2012 Simon Cadman <src@niftiestsoftware.com> (20120818-1)
- New: Depreciated Google ClientLogin replaced with OAuth2 implementation – Google Account password no longer stored locally – when upgrading you will need to remove and re-add your Google Account and printers
- New: Multiple Google user account support, you can now add printers from multiple Google Cloud Print accounts
- Fix: No longer blindly overwrite printers when adding a new printer with same name as an existing printer

* Sun Aug 12 2012 Simon Cadman <src@niftiestsoftware.com> (20120812-1)
- Fixed: Error when installing printer with non ASCII characters
- Fixed: More Python 3 fixes
- Added colour option to printer, should now allow colour printig on most printers
- Added more logging to aid debugging
  
* Sun May 13 2012 Simon Cadman <src@niftiestsoftware.com> (20120513-1)
- Fixed: cloudprint.conf details exposed to users
- Fixed: backend script fails if cannot write to logfile
- Fixed: Logrotate recreates /var/log/cups/cloudprint_log file with wrong permissions

* Mon Apr 23 2012 Simon Cadman <src@niftiestsoftware.com> (20120423-1)
- Added prefix support to setup script

* Sun Apr 22 2012 Simon Cadman <src@niftiestsoftware.com> (20120422-1)
- Added prefix support to setup script

* Sat Feb 25 2012 Simon Cadman <src@niftiestsoftware.com> (20120225-5)
- Added 12.04 support

* Sat Feb 25 2012 Simon Cadman <src@niftiestsoftware.com> (20120225-4)
- Yet more build dependancies

* Sat Feb 25 2012 Simon Cadman <src@niftiestsoftware.com> (20120225-3)
- More build dependancies

* Sat Feb 25 2012 Simon Cadman <src@niftiestsoftware.com> (20120225-2)
- Fixed build dependancies

* Sat Feb 25 2012 Simon Cadman <src@niftiestsoftware.com> (20120225-1)
- Debian package release
