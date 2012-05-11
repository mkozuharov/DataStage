import errno
import mimetypes
import os
import urllib
import urlparse
from wsgiref.handlers import format_date_time

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django_conneg.http import HttpResponseSeeOther
from django_conneg.views import HTMLView

from .base import BaseBrowseView

class FileView(BaseBrowseView):
    def get(self, request, path):
        with self.access_error_handler():
            stat = os.stat(self.path_on_disk)
            mimetype, encoding = mimetypes.guess_type(self.path_on_disk)
            response = HttpResponse(open(self.path_on_disk, 'rb'), mimetype=mimetype)

        response['Last-Modified'] = format_date_time(stat.st_mtime)
        response['Content-Length'] = stat.st_size
        if not mimetype:
            del response['Content-Type']
        return response

    def delete(self, request, path):
        filename = path.rsplit('/', 1)[-1]

        try:
            os.remove(self.path_on_disk)
            msg =  "The file: '%s' has been successfully deleted!" % filename
        except (IOError, OSError) as e:
            if e.errno == errno.ENOENT:
                raise Http404
            elif e.errno == errno.EACCES:
                msg = "You do not have permission to delete this file."
            else:
                msg = "Delete was unsuccessful !"
        except Exception, e:
            msg = "Delete was unsuccessful !"

        url = urlparse.urlunsplit(('', # scheme
                                   '', # netloc
                                   reverse('browse:index', kwargs={'path': path.rsplit('/', 1)[0]}),
                                   urllib.urlencode({'message': msg}),
                                   '')) # fragment

        return HttpResponseSeeOther(url)

class FileDeleteView(HTMLView, FileView):
    def get(self, request, path):
        context = {'path': self.path,
                   'filename': path.rsplit('/', 1)[-1],
                   'parent_url': reverse('browse:index', kwargs={'path': path.rsplit('/', 1)[0]})}
        return self.render(request, context, 'browse/confirm')

    def post(self, request, path):
        return self.delete(request, path)
