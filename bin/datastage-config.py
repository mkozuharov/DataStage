
import os

if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'datastage.web.settings'

if __name__ == '__main__':
    from datastage.admin.interactive import main
    main()
