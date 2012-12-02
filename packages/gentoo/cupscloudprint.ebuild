# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit git-2 eutils

DESCRIPTION="Google Cloud Print"
HOMEPAGE="https://ccp.niftiestsoftware.com"
EGIT_REPO_URI="git://github.com/simoncadman/CUPS-Cloud-Print.git"
EGIT_COMMIT="59e7f6631b170464fcd1308e9586af7878f78414"
LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~ia64 ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~x64"
IUSE=""
RDEPEND="!net-print/cups-cloudprint
>=dev-lang/python-2.6
net-print/cups
app-text/ghostscript-gpl
dev-python/pycups
dev-python/httplib2"
S=${WORKDIR}/${P}

src_install() {
	einstall DESTDIR="${D}" install
}

pkg_postinst() {
	/usr/lib/cloudprint-cups/upgrade.py
}
