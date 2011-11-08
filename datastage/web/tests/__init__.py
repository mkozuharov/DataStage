import os
import sys
import unittest

class DatastageWebTestCase(unittest.TestCase):
    _settings_module = 'datastage.web.tests.settings'
    
    def setUp(self):
        if os.environ.get('DJANGO_SETTINGS_MODULE') != self._settings_module:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'datastage.web.tests.settings'
        super(DatastageWebTestCase, self).setUp()
