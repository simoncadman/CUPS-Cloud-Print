# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $
EAPI="3"

inherit git-2 python eutils
DESCRIPTION="Google Cloud Print"
HOMEPAGE="https://ccp.niftiestsoftware.com"
EGIT_REPO_URI="git://github.com/simoncadman/CUPS-Cloud-Print.git"
EGIT_COMMIT="5a110d7f73a507750aa2cb12f7ac7341781a13a1"
LICENSE="GPL-3"
PYTHON_DEPEND="2"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~ia64 ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~x64 ~amd64-fbsd ~x86-fbsd"
IUSE="selinux"
RDEPEND="!net-print/cups-cloudprint
>=dev-lang/python-2.6
net-print/cups
app-text/ghostscript-gpl
dev-python/pycups
dev-python/httplib2
media-gfx/imagemagick[postscript,jpeg,png]
selinux? ( sec-policy/cupscloudprint )"
S=${WORKDIR}/${P}

src_install() {
       einstall DESTDIR="${D}" install
       cd "${D}"
       python2 -m compileall -q -f .
       
       insinto /etc/cron.daily
       newins "${S}"/cron.daily/cupscloudprint cupscloudprint
       fperms 0755 /etc/cron.daily/cupscloudprint
}

pkg_postinst() {
       /usr/share/cloudprint-cups/upgrade.py
}