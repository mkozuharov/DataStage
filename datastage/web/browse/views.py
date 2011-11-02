import datetime
import errno
import httplib
import itertools
import mimetypes
import os
import pwd
import shutil
import StringIO
import subprocess
import sys
import tempfile
import urllib
import xattr
from wsgiref.handlers import format_date_time

import DAV.WebDAVServer
import DAVServer.fshandler
from django.core.exceptions import PermissionDenied
from django.core.servers.basehttp import is_hop_by_hop
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django_conneg.http import HttpResponseSeeOther
from django_conneg.decorators import renderer
from django_conneg.views import ContentNegotiatedView, HTMLView, JSONView, TextView
import posix1e

from datastage.config import settings
from datastage.util.path import get_permissions, statinfo_to_dict, permission_map, has_permission

class DirectoryView(HTMLView, JSONView):
    def dispatch(self, request, path_on_disk, path, permissions):
        if posix1e.ACL_EXECUTE not in permissions:
            raise PermissionDenied
        return super(DirectoryView, self).dispatch(request, path_on_disk, path, permissions)
    
    sorts = {
        'size': lambda sp: (sp['stat']['st_size'] if sp['type'] == 'file' else 0),
        'name': lambda sp: (sp['type'] != 'dir', sp['name'].lower()),
        'modified': lambda sp: sp['last_modified'],
    }
    
    def get_subpath_data(self, request, path_on_disk, path):
        try:
            sort_name = request.GET.get('sort') or 'name'
            sort_function = self.sorts[request.GET.get('sort', 'name')]
            sort_reverse = {'true': True, 'false': False}[request.GET.get('reverse', 'false')]
        except KeyError:
            raise Http404

        subpaths = [{'name': name} for name in os.listdir(path_on_disk) if not name.startswith('.')]
        for subpath in subpaths:
            subpath_on_disk = os.path.join(path_on_disk, subpath['name'])
            subpath_stat = os.lstat(subpath_on_disk)
            subpath['path'] = '%s%s' % (path, subpath['name']) if path else subpath['name']
            permissions = map(permission_map.get, get_permissions(subpath_on_disk, request.user.username))
            subpath.update({
                'type': 'dir' if os.path.isdir(subpath_on_disk) else 'file',
                'stat': statinfo_to_dict(subpath_stat),
                'last_modified': datetime.datetime.fromtimestamp(subpath_stat.st_mtime),
                'url': request.build_absolute_uri(reverse('browse:index',
                                                          kwargs={'path': subpath['path']})),
                'permissions': permissions,
                'link': ('execute' if os.path.isdir(subpath_on_disk) else 'read') in permissions,
            })
            try:
                pw_user = pwd.getpwuid(subpath_stat.st_uid)
                subpath.update({'owner_name': pw_user.pw_gecos,
                                'owner_username': pw_user.pw_name})
            except KeyError:
                subpath['owner'] = None
            for permission in permissions:
                subpath['can_%s' % permission] = True
            if subpath['type'] == 'dir':
                subpath['url'] += '/'
            if subpath['link']:
                subpath['xattr'] = dict(xattr.xattr(subpath_on_disk))
                # Only expose user-space extended attributes
                for k in list(subpath['xattr']):
                    if not k.startswith('user.'):
                        del subpath['xattr'][k]
                subpath['title'] = subpath['xattr'].get('user.dublincore.title')
                subpath['description'] = subpath['xattr'].get('user.dublincore.description')

        subpaths.sort(key=sort_function, reverse=sort_reverse)
        
        return subpaths, sort_name, sort_reverse
        
        
    def get(self, request, path_on_disk, path, permissions):
        if path:
            parent_url = request.build_absolute_uri(reverse('browse:index',
                                                    kwargs={'path': ''.join(p+'/' for p in path.split('/')[:-2])}))
        else:
            parent_url = None
            
        subpaths, sort_name, sort_reverse = self.get_subpath_data(request, path_on_disk, path)
        
        stat = os.stat(path_on_disk)
        context = {
            'path': path,
            'parent_url': parent_url,
            'subpaths': subpaths,
            'stat': statinfo_to_dict(stat),
            'additional_headers': {
                'Last-Modified': format_date_time(stat.st_mtime),
            },
            'sort_name': sort_name,
            'sort_reverse': sort_reverse,
            'column_names': (('name', 'Name'), ('modified', 'Last modified'), ('size', 'Size'), ('owner_name', 'Owner')),
        }

        return self.render(request, context, 'browse/directory')
    
    def post(self, request, path_on_disk, path, permissions):
        subpaths, sort_name, sort_reverse = self.get_subpath_data(request, path_on_disk, path)

        for subpath in subpaths:
            subpath_on_disk = os.path.join(path_on_disk, subpath['name'])
            if 'write' not in subpath['permissions']:
                continue
            part = urllib.quote(subpath['name'])
            subpath_xattr = xattr.xattr(subpath_on_disk)
            for field in ('title', 'description'):
                key = 'user.dublincore.' + field
                value = request.POST.get('meta-%s-%s' % (field, part))
                if value == "" and field in subpath_xattr:
                    del subpath_xattr[field]
                elif value:
                    subpath_xattr[field] = value
        return HttpResponseSeeOther('')
                

class FileView(View):
    def get(self, request, path_on_disk, path, permissions):
        mimetype, encoding = mimetypes.guess_type(path_on_disk)
        stat = os.stat(path_on_disk)

        response = HttpResponse(open(path_on_disk, 'rb'), mimetype=mimetype)
        response['Last-Modified'] = format_date_time(stat.st_mtime)
        response['Content-Length'] = stat.st_size
        if not mimetype:
            del response['Content-Type']
        return response

class ForbiddenView(HTMLView, JSONView, TextView):
    def dispatch(self, request, path):
        context = {
            'path': path,
            'message': 'Access to this path is forbidden.',
            'status_code': httplib.FORBIDDEN,
        }
        return self.render(request, context, 'browse/forbidden')

class ZipView(ContentNegotiatedView):
    _default_format = 'zip'
    _force_fallback_format = 'zip'
    
    _sink_filename = {'linux2': '/dev/null',
                      'win32': 'NUL:',
                      'cygwin': 'NUL:',
                      'darwin': 'dev/null'}[sys.platform] 
    
    def get(self, request, path_on_disk, path, permissions):
        if posix1e.ACL_EXECUTE not in permissions:
            raise PermissionDenied
        return self.render(request, {'path_on_disk': path_on_disk}, 'browse/zip')
    
    @renderer(format='zip', mimetypes=('application/zip',), name='ZIP archive')
    def render_zip(self, request, context, template_name):
        tempdir = tempfile.mkdtemp()
        sink_file = open(self._sink_filename, 'w')

        parent_dir = os.path.dirname(context['path_on_disk'])
        try:
            filename = os.path.join(tempdir, 'temp.zip')
            zip_process = subprocess.Popen(['zip', filename, '-@'],
                                           cwd=parent_dir,
                                           stdin=subprocess.PIPE,
                                           stdout=sink_file)
            for root, dirs, files in os.walk(context['path_on_disk']):
                dirs[:] = [d for d in dirs if has_permission(os.path.join(root, d), request.user.username, posix1e.ACL_EXECUTE)]
                files[:] = [f for f in files if has_permission(os.path.join(root, f), request.user.username, posix1e.ACL_READ)]
                paths = itertools.chain([root], files)
                for path in paths:
                    zip_process.stdin.write(os.path.relpath(os.path.join(root, path), parent_dir) + '\n')
            zip_process.stdin.close()
            zip_process.wait()
            
            response = HttpResponse(open(filename, 'rb'), mimetype='application/zip')
            response['Content-Length'] = os.stat(filename).st_size
            response['Content-Disposition'] = 'attachment;filename=%s.zip' % os.path.basename(context['path_on_disk'])
            return response
        finally:
            shutil.rmtree(tempdir)
            sink_file.close()

class DAVView(View):
    http_method_names = ['propfind', 'proppatch', 'mkcol', 'copy',
                         'move', 'lock', 'unlock']
    
    class RequestHeaders(dict):
        def __init__(self, meta):
            meta = dict((self.norm_key(k[5:]), meta[k]) for k in meta if k.startswith('HTTP_'))
            super(DAVView.RequestHeaders, self).__init__(meta)
        def norm_key(self, key):
            return key.lower().replace('-', '_')
        def __getitem__(self, key):
            return super(DAVView.RequestHeaders, self).__getitem__(self.norm_key(key))
        def get(self, key, default=None):
            return super(DAVView.RequestHeaders, self).get(self.norm_key(key), default)
        def __setitem__(self, key, value):
            return super(DAVView.RequestHeaders, self).__setitem__(self.norm_key(key), value)
        def __contains__(self, key):
            return super(DAVView.RequestHeaders, self).__contains__(self.norm_key(key))
        has_key = __contains__

    class DAVConfig(object):
        def __init__(self):
            self.DAV = self
        def getboolean(self, name):
            return getattr(self, name)
        chunked_http_response = False
    
    class DAVHandler(DAV.WebDAVServer.DAVRequestHandler):
        def __init__(self, request):
            self._request, self._response = request, HttpResponse()
            self.headers = DAVView.RequestHeaders(request.META)
            self.request_version = 'HTTP/1.1'
            self._config = DAVView.DAVConfig()
            self.command = request.method
            self.path = request.path
            self.rfile = StringIO.StringIO(request.raw_post_data)
            self.headers['Content-Length'] = str(len(request.raw_post_data))
            self.IFACE_CLASS = DAVServer.fshandler.FilesystemHandler(settings.DATA_DIRECTORY,
                                                                     request.build_absolute_uri(reverse('browse:index', kwargs={'path':''})))
            self.IFACE_CLASS._get_dav_getetag = lambda uri: "F"
            self.wfile = self._response
            self._BufferedHTTPRequestHandler__buffer = ""
            self.wfile.write = lambda :1
        def send_response(self, code, message):
            self._response.status_code = code
        def send_header(self, header, value):
            if not is_hop_by_hop(header):
                self._response[header] = value
        def end_headers(self):
            pass
        def get_response(self):
            self._response.content = self._BufferedHTTPRequestHandler__buffer
            return self._response
    
    def dispatch(self, request, path, permissions):
        if posix1e.ACL_EXECUTE not in permissions:
            raise PermissionDenied
        self.dav_hander = DAVView.DAVHandler(request)
        return super(DAVView, self).dispatch(request)
    
    def propfind(self, request):
        self.dav_hander.do_PROPFIND()
        return self.dav_hander.get_response()


class IndexView(DAVView, ContentNegotiatedView):

    directory_view = staticmethod(DirectoryView.as_view())
    file_view = staticmethod(FileView.as_view())
    forbidden_view = staticmethod(ForbiddenView.as_view())
    
    zip_view = staticmethod(ZipView.as_view())
    
    http_method_names = ContentNegotiatedView.http_method_names + DAVView.http_method_names

    @method_decorator(login_required)
    def dispatch(self, request, path):
        path_parts = path.rstrip('/').split('/')
        if path and any(part in ('.', '..', '') for part in path_parts):
            raise Http404
        
        path_on_disk = os.path.normpath(os.path.join(settings.DATA_DIRECTORY, *path_parts))
        
        try:
            permissions = get_permissions(path_on_disk, request.user.username, check_prefixes=True)
        except IOError, e:
            if e.errno == errno.ENOENT:
                raise Http404
            elif e.errno == errno.EACCES:
                return self.forbidden_view(request, path)
            raise

        view = self.directory_view if os.path.isdir(path_on_disk) else self.file_view
        if view == self.directory_view and path and not path.endswith('/'):
            return HttpResponsePermanentRedirect(reverse('browse:index', kwargs={'path':path+'/'}))
        
        try:
            action = request.REQUEST.get('action')
            if action == 'zip' and os.path.isdir(path_on_disk):
                return self.zip_view(request, path_on_disk, path, permissions)
            elif request.method.lower() in ('get', 'post'):
                view = self.directory_view if os.path.isdir(path_on_disk) else self.file_view
                response = view(request, path_on_disk, path, permissions)
            else:
                response = super(IndexView, self).dispatch(request, path, permissions)
            response['Allow'] = ','.join(m.upper() for m in self.http_method_names)
            response['DAV'] = "1,2"
            response['MS-Author-Via'] = 'DAV'
            return response
        except PermissionDenied:
            return self.forbidden_view(request, path)
        except:
            import traceback
            traceback.print_exc()
            raise
        
