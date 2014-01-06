import errno
import httplib
import os
import urllib

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponsePermanentRedirect
from django.utils.datastructures import MergeDict
from django.utils.decorators import method_decorator
from django_conneg.views import ErrorCatchingView, HTMLView

from datastage.config import settings
from datastage.web.auth.decorators import login_required

from .base import BaseBrowseView
from .directory import DirectoryView, UploadView
from .file import FileView, FileDeleteView
from .dav import DAVView

class BadRequestView(HTMLView):
    _force_fallback_format = 'html'

    def request(self, request, path):
        context = {'path': path,
                   'status_code': 400}
        return self.render(request, context, 'browse/bad_request')

class IndexView(BaseBrowseView):
    data_directory = None
    error_template_names = MergeDict({httplib.FORBIDDEN: 'browse/403'},
                                     ErrorCatchingView.error_template_names)

    bad_request_view = staticmethod(BadRequestView.as_view())

    directory_views = {'upload': UploadView.as_view(),
                       None: DirectoryView.as_view()}
    file_views = {'delete': FileDeleteView.as_view(),
                  None: FileView.as_view()}

    dav_view = staticmethod(DAVView.as_view(data_directory=settings.DATA_DIRECTORY))

    @method_decorator(login_required)
    def dispatch(self, request, path):

        self.path = path
        self.path = urllib.unquote(path)
        # Make sure that directories have a trailing slash.
        if os.path.isdir(self.path_on_disk) and path and not path.endswith('/'):
            abs_path =  request.build_absolute_uri(reverse('browse:index', kwargs={'path': path + '/'}))
            message = request.GET.get('message')
            uri = abs_path + "?" +  urllib.urlencode({'message': message}) if message else abs_path
            return HttpResponsePermanentRedirect(uri)
       
        views = self.directory_views if os.path.isdir(self.path_on_disk) else self.file_views

        if request.method.lower() in DAVView.http_method_names:
            view = self.dav_view
        else:
            try:
                view = views[request.REQUEST.get('action')]
            except KeyError:
                return self.bad_request_view(request, path)

        response = view(request, path)

        response['Allow'] = ','.join(m.upper() for m in self.http_method_names)
        response['DAV'] = "1,2"
        response['MS-Author-Via'] = 'DAV'

        return response
