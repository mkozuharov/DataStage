import datetime
import errno
import httplib
import itertools
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
from wsgiref.handlers import format_date_time

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.views.generic import View
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
        
    def get(self, request, path_on_disk, path, permissions):

        stat = os.stat(path_on_disk)
        subpaths = [{'name': name} for name in os.listdir(path_on_disk) if not name.startswith('.')]
        for subpath in subpaths:
            subpath_on_disk = os.path.join(path_on_disk, subpath['name'])
            subpath_stat = os.lstat(subpath_on_disk)
            subpath['path'] = '%s/%s' % (path, subpath['name']) if path else subpath['name']
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
        subpaths.sort(key=lambda sp: (sp['type'] != 'dir', sp['name'].lower()))
        
        if path:
            parent_url = request.build_absolute_uri(reverse('browse:index',
                                                    kwargs={'path': '/'.join(path.split('/')[:-1])}))
        else:
            parent_url = None
        
        context = {
            'path': path,
            'parent_url': parent_url,
            'subpaths': subpaths,
            'stat': statinfo_to_dict(stat),
            'additional_headers': {
                'Last-Modified': format_date_time(stat.st_mtime),
            }
        }

        return self.render(request, context, 'browse/directory')

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
    def get(self, request, path):
        context = {
            'path': path,
            'message': 'Access to this path is forbidden.',
            'status_code': httplib.FORBIDDEN,
        }
        return self.render(request, context, 'browse/forbidden')
    post = put = delete = options = get

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

class IndexView(ContentNegotiatedView):

    directory_view = staticmethod(DirectoryView.as_view())
    file_view = staticmethod(FileView.as_view())
    forbidden_view = staticmethod(ForbiddenView.as_view())
    
    zip_view = staticmethod(ZipView.as_view())

    def dispatch(self, request, path):
        path_parts = path.split('/')
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
        
        action = request.REQUEST.get('action')
        if action == 'zip' and view == self.directory_view:
            view = self.zip_view

        try:
            return view(request, path_on_disk, path, permissions)
        except PermissionDenied:
            return self.forbidden_view(request, path)
        
