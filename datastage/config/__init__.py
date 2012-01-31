import ConfigParser
import os

from django.core.exceptions import ImproperlyConfigured

from datastage import __version__

class Settings(object):
    def __init__(self):
        self.config_location, self._config = self.get_config()

    def relative_to_config(self, *args):
        # Return None if any of the arguments are None.
        if all(args):
            return os.path.abspath(os.path.join(os.path.dirname(self.config_location), *args))

    @staticmethod
    def get_config():
        # Find config file
        def _config_locations():
            if 'DATASTAGE_CONFIG' in os.environ:
                yield os.environ['DATASTAGE_CONFIG']
            yield os.path.expanduser('~/.datastage.conf')
            yield '/etc/datastage.conf'
            yield os.path.join(os.path.dirname(__file__), 'datastage.conf')

        for config_location in _config_locations():
            if os.path.exists(config_location):
                break
        else:
            raise ImproperlyConfigured("Couldn't find config file")

        config = ConfigParser.ConfigParser()
        config.read(config_location)

        config = dict((':'.join([sec, key]), config.get(sec, key)) for sec in config.sections() for key in config.options(sec))

        return config_location, config
    
    def __getitem__(self, key):
        return self._config[key]
    def get(self, key):
        return self._config.get(key)
    
    config_item = lambda key: property(lambda self: self[key])
    SITE_NAME = config_item('main:site_name')
    GROUP_NAME = config_item('group:name')
    GROUP_URL = config_item('group:url')
    del config_item

    @property
    def DATA_DIRECTORY(self):
        return self.relative_to_config(self._config['data:path'])

    USER_AGENT = property(lambda self:'Mozilla (compatible; DataStage/%s; %s' % (__version__, self.GROUP_URL))

settings = Settings()
