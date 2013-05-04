Name:           cupscloudprint
Version:        20130504
Release:        1
Summary:        Google Cloud Print driver for CUPS, allows printing to printers hosted on Google Cloud Print

License:        GPLv3+
URL:            http://ccp.niftiestsoftware.com
Source0:        http://ccp.niftiestsoftware.com/cupscloudprint-20130504.tar.bz2

BuildRequires:  cups-devel,cups,make,python-httplib2
Requires:       cups,ghostscript,system-config-printer-libs,python-httplib2

%description
Google Cloud Print driver for CUPS, allows printing to printers hosted on Google Cloud Print.

%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT NOPERMS=1

%post
chown root:lp /var/log/cups/cloudprint_log
chown -R root:lp /usr/lib/cloudprint-cups/
chmod 660 /var/log/cups/cloudprint_log
/usr/lib/cloudprint-cups/upgrade.py

%files
/usr/lib/cloudprint-cups
/usr/lib/cups/backend/cloudprint
/usr/lib/cups/driver/cupscloudprint
%{_localstatedir}/log/cups/cloudprint_log

%changelog
