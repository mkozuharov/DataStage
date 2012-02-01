.. py:module:: datastage.admin

``datastage.admin``
===================

This has yet to be written, but should contain the following features:

* Generation of external config files

  * Apache config for datastage.web.
  * Updating certificate files and private keys for datastage.web

* Setting the research group name and other metadata

Upon installation, this should be accessible on a local-listening port. It
should either:

* contact fingerd to check that the connecting user is root
* use PAM to check for a root password
