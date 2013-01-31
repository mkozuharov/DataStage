import contextlib
import errno
import os

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django_conneg.views import ErrorCatchingView

from datastage.config import settings

import logging
logger = logging.getLogger(__name__)

class BaseBrowseView(ErrorCatchingView):
    @property
    def path_on_disk(self):
        try:
            return self._path_on_disk
        except AttributeError:
            data_directory, path = settings.DATA_DIRECTORY, self.path

            path_parts = path.rstrip('/').split('/')
            if path and any(part in ('.', '..', '') for part in path_parts):
                raise Http404
            self._path_on_disk = os.path.normpath(os.path.join(data_directory, *path_parts))
            return self._path_on_disk

    def dispatch(self, request, path, *args, **kwargs):
        self.path = path
        self.path_on_disk
        return super(BaseBrowseView, self).dispatch(request, path, *args, **kwargs)

    def can_read(self, path=None):
        path = path or self.path_on_disk
        try:
            if os.path.isdir(path):
                os.stat(os.path.join(path, '.'))
                return True
            else:
                with open(path, 'r'):
                    return True
        except IOError, e:
            if e.errno == errno.EACCES:
                return False
        except OSError, e:
            if e.errno == errno.EACCES:
                return False
            raise

    def can_write(self, path=None):
        path = path or self.path_on_disk
        logger.debug("Path : " + str(path))
        try:
            if os.path.isdir(path):
                logger.debug(" is a directory and is not writable")
                return False        
            else:
                with open(path, 'r+'):
                    #os.close(path)
                    logger.debug(" is writable")
                    return True
        except IOError, e:
            if e.errno == errno.EACCES:
                logger.debug(" is not writable")
                return False
            raise
        except OSError, e:
            if e.errno == errno.EACCES:
                logger.debug(" is not writable")
                return False
            raise
        
            
    def can_submit(self, path=None):
        path = path or self.path_on_disk
        try:
            if os.path.isdir(path):
                file = os.path.join(self.path_on_disk,"testsubmit")
                open(file , 'w+')
                os.remove(file)
                return True
        except IOError, e:
            if e.errno == errno.EACCES:
                return False
        except OSError, e:
            if e.errno == errno.EACCES:
                return False
            raise

    @staticmethod
    @contextlib.contextmanager
    def access_error_handler():
        try:
            yield
        except (OSError, IOError), e:
            if e.errno == errno.ENOENT:
                raise Http404
            elif e.errno == errno.EACCES:
                raise PermissionDenied
            else:
                raise