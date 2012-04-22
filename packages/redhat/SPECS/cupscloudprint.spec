Name:           cupscloudprint
Version:        20120225
Release:        1
Summary:        Google Cloud Print driver for CUPS, allows printing to printers hosted on Google Cloud Print

License:        GPLv3+
URL:            http://ccp.niftiestsoftware.com
Source0:        http://ccp.niftiestsoftware.com/cupscloudprint-20120225.tar.bz2

BuildRequires:  cups-devel
Requires:       cups,ghostscript,python-cups

%description
Google Cloud Print driver for CUPS, allows printing to printers hosted on Google Cloud Print.

%prep
%setup -q


%build
%configure
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT


%files
%{_libdir}/cloudprint-cups
%{_libdir}/cups/backend/cloudprint
%{_datadir}/cups/model/CloudPrint.ppd
%{_localstatedir}/log/cups/cloudprint_log

%changelog
