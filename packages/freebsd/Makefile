# $FreeBSD$

PORTNAME=	cupscloudprint
PORTVERSION=	20140307
CATEGORIES=	print

MAINTAINER=	src@niftiestsoftware.com
COMMENT=	Google Cloud Print driver for CUPS

RUN_DEPENDS=	cups:${PORTSDIR}/print/cups\
		ps2pdf:${PORTSDIR}/print/ghostscript9-nox11\
		ImageMagick:${PORTSDIR}/graphics/ImageMagick\
		${PYTHON_SITELIBDIR}/cups.so:${PORTSDIR}/print/py-cups\
		${PYTHON_SITELIBDIR}/httplib2:${PORTSDIR}/www/py-httplib2

USE_GITHUB=     yes
USE_PYTHON=	2.6-2.7
GH_ACCOUNT=     simoncadman
GH_PROJECT=     CUPS-Cloud-Print
GH_TAGNAME=     ${PORTVERSION}
GH_COMMIT=	6f8c397

GNU_CONFIGURE=	yes
USE_PKGCONFIG=  build
USE_GMAKE=	yes

post-install:
		/usr/local/share/cloudprint-cups/upgrade.py	

.include <bsd.port.mk>
