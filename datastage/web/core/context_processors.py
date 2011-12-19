from datastage.config import settings as config_settings

def settings(request):
    return {
        'settings': config_settings,
        'hostname': request.META.get('HTTP_HOST'),
        'is_secure': request.is_secure(),
    }
