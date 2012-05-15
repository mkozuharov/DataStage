import os
import StringIO
import urlparse

try: # 0.9.8+
    from pywebdav.lib import WebDAVServer, errors
    from pywebdav.server import fshandler
except ImportError: # 0.9.4.1 and earlier
    from DAV import WebDAVServer, errors
    from DAVServer import fshandler

from django.core.servers.basehttp import is_hop_by_hop
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic import View

class RequestHeaders(dict):
    def __init__(self, meta):
        meta = dict((self.norm_key(k[5:]), meta[k]) for k in meta if k.startswith('HTTP_'))
        super(RequestHeaders, self).__init__(meta)
    def norm_key(self, key):
        return key.lower().replace('-', '_')
    def __getitem__(self, key):
        return super(RequestHeaders, self).__getitem__(self.norm_key(key))
    def get(self, key, default=None):
        return super(RequestHeaders, self).get(self.norm_key(key), default)
    def __setitem__(self, key, value):
        return super(RequestHeaders, self).__setitem__(self.norm_key(key), value)
    def __contains__(self, key):
        return super(RequestHeaders, self).__contains__(self.norm_key(key))
    has_key = __contains__

class DAVConfig(object):
        def __init__(self):
            self.DAV = self
        def getboolean(self, name):
            return getattr(self, name)
        chunked_http_response = False
        lockemulation = False
        http_request_use_iterator = False

class FilesystemHandler(fshandler.FilesystemHandler):
    def uri2local(self, uri):
        url = urlparse.urlparse(uri)
        local = os.path.relpath(urlparse.urlparse(uri)[2],
                                urlparse.urlparse(self.baseuri)[2])
        local = os.path.normpath(os.path.join(self.directory, local))

        return local

    def local2uri(self, local):
        return urlparse.urljoin(self.baseuri,
                                os.path.relpath(local, self.directory)).encode('utf-8')

    baseurl = None

class DAVHandler(WebDAVServer.DAVRequestHandler):
    def __init__(self, request, filesystem_handler):
        self._request, self._response = request, HttpResponse()
        self.headers = RequestHeaders(request.META)
        self.request_version = 'HTTP/1.1'
        self._config = DAVConfig()
        self.command = request.method
        self.path = request.path
        self.rfile = StringIO.StringIO(request.raw_post_data)
        self.headers['Content-Length'] = str(len(request.raw_post_data))
        self.IFACE_CLASS = filesystem_handler
        #self.IFACE_CLASS._get_dav_getetag = lambda uri: "F"
        self.wfile = self._response
        self.requestline = '{0} {1} {2}'.format(request.method, request.path_info, request.META['SERVER_PROTOCOL'])
        self.client_address = (request.META['REMOTE_ADDR'], None)

    def send_response(self, code, message=None):
        self._response.status_code = code
    def send_header(self, header, value):
        if not is_hop_by_hop(header):
            self._response[header] = value
    def end_headers(self):
        pass
    def get_response(self):
        return self._response
    


class DAVView(View):
    """
    Wraps the PyWebDAV module in a Django view.
    """

    http_method_names = ['propfind', 'proppatch', 'mkcol', 'copy', 'head',
                         'move', 'lock', 'unlock', 'put', 'options', 'delete']

    data_directory = None

    def dispatch(self, request, path):
        self.filesystem_handler = FilesystemHandler(self.data_directory,
                                                    request.build_absolute_uri(reverse('browse:index', kwargs={'path':''})))
        self.dav_handler = DAVHandler(request,
                                      self.filesystem_handler)
        return super(DAVView, self).dispatch(request, path)

    def options(self, request, path):
        self.dav_handler.do_OPTIONS()
        return self.dav_handler.get_response()

    def propfind(self, request, path):
        self.dav_handler.do_PROPFIND()
        return self.dav_handler.get_response()

    def move(self, request, path):
        self.dav_handler.do_MOVE()
        return self.dav_handler.get_response()

    def put(self, request, path):
        self.dav_handler.do_PUT()
        return self.dav_handler.get_response()

    def mkcol(self, request, path):
        self.dav_handler.do_MKCOL()
        return self.dav_handler.get_response()

    def copy(self, request, path):
        self.dav_handler.do_COPY()
        return self.dav_handler.get_response()

    def proppatch(self, request, path):
        self.dav_handler.do_PROPPATCH()
        return self.dav_handler.get_response()

    def delete(self, request, path):
        self.dav_handler.do_DELETE()
        return self.dav_handler.get_response()

    def head(self, request, path):
        self.dav_handler.do_HEAD()
        return self.dav_handler.get_response()


