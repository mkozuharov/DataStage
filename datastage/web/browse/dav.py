import os
import StringIO
import urlparse

import DAV.WebDAVServer
import DAVServer.fshandler
from django.core.exceptions import PermissionDenied
from django.core.servers.basehttp import is_hop_by_hop
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic import View
import posix1e

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

class FilesystemHandler(DAVServer.fshandler.FilesystemHandler):
    def uri2local(self, uri):
        url = urlparse.urlparse(uri)
        local = os.path.relpath(urlparse.urlparse(uri)[2],
                                urlparse.urlparse(self.baseuri)[2])
        local = os.path.normpath(os.path.join(self.directory, local))
        
        #root = os.path.normpath(self.directory).split(os.path.sep)
        #if local.split(os.path.sep)[:len(root)] != root:
        #    print self.directory, local
        #    raise PermissionDenied

        return local
    
    def local2uri(self, local):
        print local, urlparse.urljoin(self.baseuri,
                                os.path.relpath(local, self.directory))
        return urlparse.urljoin(self.baseuri,
                                os.path.relpath(local, self.directory)).encode('utf-8')

    def get_childs(self, uri):
        result = DAVServer.fshandler.FilesystemHandler.get_childs(self, uri)
        print "E", os.listdir(self.uri2local(uri))
        print uri, result
        return result

class DAVHandler(DAV.WebDAVServer.DAVRequestHandler):
    def __init__(self, request, data_directory):
        self._request, self._response = request, HttpResponse()
        self.headers = RequestHeaders(request.META)
        self.request_version = 'HTTP/1.1'
        self._config = DAVConfig()
        self.command = request.method
        self.path = request.path
        self.rfile = StringIO.StringIO(request.raw_post_data)
        self.headers['Content-Length'] = str(len(request.raw_post_data))
        self.IFACE_CLASS = FilesystemHandler(data_directory,
                                             request.build_absolute_uri(reverse('browse:index', kwargs={'path':''})))
        self.IFACE_CLASS._get_dav_getetag = lambda uri: "F"
        self.wfile = self._response
        self._BufferedHTTPRequestHandler__buffer = ""
        self.wfile.write = lambda :1
    def send_response(self, code, message):
        print "CODE", code
        self._response.status_code = code
    def send_header(self, header, value):
        if not is_hop_by_hop(header):
            self._response[header] = value
    def end_headers(self):
        pass
    def get_response(self):
        self._response.content = self._BufferedHTTPRequestHandler__buffer
        return self._response


class DAVView(View):
    http_method_names = ['propfind', 'proppatch', 'mkcol', 'copy',
                         'move', 'lock', 'unlock']
    
    data_directory = None
    
    def dispatch(self, request, path, permissions):
         
        self.dav_hander = DAVHandler(request, self.data_directory)
        return super(DAVView, self).dispatch(request, path, permissions)
    
    def propfind(self, request, path, permissions):
        if os.path.isdir(self.path_on_disk) and posix1e.ACL_EXECUTE not in permissions:
            raise PermissionDenied
        elif not os.path.isdir(self.path_on_disk) and posix1e.ACL_READ not in permissions:
            raise PermissionDenied
        
        self.dav_hander.do_PROPFIND()
        return self.dav_hander.get_response()