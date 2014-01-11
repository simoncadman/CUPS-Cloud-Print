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

%post
%{_usr}/share/cloudprint-cups/upgrade.py

%files
%{_usr}/%{_lib}/cups/backend/cloudprint
%{_usr}/%{_lib}/cups/driver/cupscloudprint
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/auth.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/cloudprintrequestor.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/printer.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/test_auth.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/test_backend.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/test_cloudprintrequestor.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/test_mockrequestor.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/test_printer.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/test_syntax.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/__init__.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/anyjson.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/client.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/clientsecrets.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/crypt.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/locked_file.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/multistore_file.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/backend.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/deleteaccount.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/dynamicppd.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/listcloudprinters.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/full-test.sh
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/reportissues.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/setupcloudprint.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/submitjob.py
%attr(755, root, lp) %{_usr}/share/cloudprint-cups/upgrade.py
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/*.pyc
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/oauth2client/*.pyo
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/*.pyc
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/*.pyo
%attr(644, root, lp) %{_usr}/share/cloudprint-cups/testfiles/*

%doc %{_usr}/share/cloudprint-cups/COPYING
%doc %{_usr}/share/cloudprint-cups/README.md
%docdir %{_usr}/share/cloudprint-cups/testfiles

%changelog
* Tue Jan 07 2014  <src@niftiestsoftware.com> 20140107-1
- Package fixes for rpmlint