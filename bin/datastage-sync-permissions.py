
import os

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'datastage.web.settings'

if __name__ == '__main__':
    from datastage.admin.sync_permissions import sync_permissions
    sync_permissions()
