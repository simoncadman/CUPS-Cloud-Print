# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $
EAPI="3"

inherit git-2 python eutils
DESCRIPTION="Google Cloud Print"
HOMEPAGE="https://ccp.niftiestsoftware.com"
EGIT_REPO_URI="git://github.com/simoncadman/CUPS-Cloud-Print.git"
EGIT_COMMIT="7cd40ac8a9b5174c2235eaa2cfc0bd1a167816d7"
LICENSE="GPL-3"
PYTHON_DEPEND="2"
SLOT="0"
KEYWORDS="~alpha ~amd64 ~arm ~ia64 ~ppc ~ppc64 ~s390 ~sh ~sparc ~x86 ~x64 ~amd64-fbsd ~x86-fbsd"
IUSE=""
RDEPEND="!net-print/cups-cloudprint
>=dev-lang/python-2.6
net-print/cups
app-text/ghostscript-gpl
dev-python/pycups
dev-python/httplib2
media-gfx/imagemagick[postscript,jpeg,png]"
S=${WORKDIR}/${P}

src_install() {
       einstall DESTDIR="${D}" install
       cd "${D}"
       $(PYTHON) -m compileall -q -f .
}

pkg_postinst() {
       /usr/share/cloudprint-cups/upgrade.py
}