# Copyright 1999-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
EAPI="5"

IUSE=""
MODS="cupscloudprint"
BASEPOL="2.20140311-r3"
HOMEPAGE="https://ccp.niftiestsoftware.com"
EGIT_REPO_URI="git://github.com/simoncadman/CUPS-Cloud-Print.git"
EGIT_COMMIT="5a110d7f73a507750aa2cb12f7ac7341781a13a1"

inherit selinux-policy-2

DESCRIPTION="SELinux policy for CUPS Cloud Print"

KEYWORDS=""