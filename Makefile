all:

debian-package:
	pwd
	dpkg-buildpackage
	mkdir debian-package
	mv ../dataflow-datastage_* debian-package

clean-debian-package:
	rm -rf debian-package

clean: clean-debian-package
