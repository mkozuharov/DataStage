from datastage import __version__

class Settings(object):
    DATA_DIRECTORY = '/home/data/'
    SITE_NAME = 'DataStage'
    GROUP_NAME = 'Example Research Group'
    GROUP_URL = 'http://research.example.ac.uk/'
    
    USER_AGENT = 'Mozilla (compatible; DataStage/%s; %s' % (__version__, GROUP_URL)
    

settings = Settings()
