from datastage.config import settings as config_settings

def settings(request):
    return {
        'settings': config_settings,
    }