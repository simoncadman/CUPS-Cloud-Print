all: cloudprint.ppd
	
cloudprint.ppd:
	ppdc cloudprint.drv  -d .
	
clean:
	rm cloudprint.ppd
	
install:
	cp backend.py /usr/libexec/cups/backend/cloudprint
	mkdir -p /usr/lib/cloudprint-cups/
	cp submitjob.py /usr/lib/cloudprint-cups/
	cp config.py /usr/lib/cloudprint-cups/
	cp cloudprint.ppd /usr/share/cups/model/CloudPrint.ppd
	chown root:root /usr/libexec/cups/backend/cloudprint
	chmod 700 /usr/libexec/cups/backend/cloudprint
