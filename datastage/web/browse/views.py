import datetime
import errno
import httplib
import mimetypes
import os
import pwd
import tempfile
import urllib
import xattr
import zipfile
from wsgiref.handlers import format_date_time

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.views.generic import View
from django.utils.decorators import method_decorator
from django_conneg.http import HttpResponseSeeOther
from django_conneg.decorators import renderer
from django_conneg.views import ContentNegotiatedView, HTMLView, JSONView, TextView
import posix1e

from datastage.web.auth.decorators import login_required
from datastage.config import settings
from datastage.util.path import get_permissions, statinfo_to_dict, permission_map, has_permission

from .dav import DAVView

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
                                                    kwargs={'path': ''.join(p + '/' for p in path.split('/')[:-2])}))
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

    def get(self, request, path_on_disk, path, permissions):
        if posix1e.ACL_EXECUTE not in permissions:
            raise PermissionDenied
        if not os.path.isdir(path_on_disk):
            raise Http404
        return self.render(request, {'path_on_disk': path_on_disk}, 'browse/zip')

    @renderer(format='zip', mimetypes=('application/zip',), name='ZIP archive')
    def render_zip(self, request, context, template_name):

        temp_file = tempfile.TemporaryFile()
        basename = os.path.basename(context['path_on_disk'])

        try:
            zip_file = zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED)
        except:
            zip_file = zipfile.ZipFile(temp_file, 'w')

        for root, dirs, files in os.walk(context['path_on_disk']):
            dirs[:] = [d for d in dirs if has_permission(os.path.join(root, d), request.user.username, posix1e.ACL_EXECUTE)]
            files[:] = [f for f in files if has_permission(os.path.join(root, f), request.user.username, posix1e.ACL_READ)]
            for fn in files:
                fn = os.path.join(root, fn)
                zip_file.write(fn,
                               os.path.join(basename,
                                            os.path.relpath(fn, context['path_on_disk'])))

        # This is a bit of a hack as ZipFile won't write anything if we
        # haven't added any files
        zip_file._didModify = True

        # We've finished adding files. Flush everything, work out how much has
        # been written and return to the start so we can serve the file back
        # to the user.
        zip_file.close()
        temp_file.flush()
        content_length = temp_file.tell()
        temp_file.seek(0)

        response = HttpResponse(temp_file, mimetype='application/zip')
        response['Content-Length'] = content_length
        response['Content-Disposition'] = 'attachment;filename=%s.zip' % urllib.quote(basename)
        return response

class IndexView(DAVView, ContentNegotiatedView):

    directory_view = staticmethod(DirectoryView.as_view())
    file_view = staticmethod(FileView.as_view())
    forbidden_view = staticmethod(ForbiddenView.as_view())

    action_views = {'zip': ZipView.as_view()}

    http_method_names = ContentNegotiatedView.http_method_names + DAVView.http_method_names

    @method_decorator(login_required)
    def dispatch(self, request, path):
        path_parts = path.rstrip('/').split('/')
        if path and any(part in ('.', '..', '') for part in path_parts):
            raise Http404

        print "UA", request.META['HTTP_USER_AGENT']

        self.path_on_disk = path_on_disk = os.path.normpath(os.path.join(settings.DATA_DIRECTORY, *path_parts))

        try:
            permissions = get_permissions(path_on_disk, request.user.username, check_prefixes=True)
        except IOError, e:
            if e.errno == errno.ENOENT and request.method not in ('PUT',):
                raise Http404
            elif e.errno == errno.EACCES:
                return self.forbidden_view(request, path)
            raise

        try:
            # action views are additional bits of behaviour for a location
            action_view = self.action_views.get(request.REQUEST.get('action'))
            if action_view:
                return action_view(request, path_on_disk, path, permissions)
            elif request.method.lower() in ('get', 'head', 'post'):
                view = self.directory_view if os.path.isdir(path_on_disk) else self.file_view
                if view == self.directory_view and path and not path.endswith('/'):
                    return HttpResponsePermanentRedirect(reverse('browse:index', kwargs={'path':path + '/'}))
                response = view(request, path_on_disk, path, permissions)
            else:
                response = super(IndexView, self).dispatch(request, path, permissions)
            response['Allow'] = ','.join(m.upper() for m in self.http_method_names)
            response['DAV'] = "1,2"
            response['MS-Author-Via'] = 'DAV'
            return response
        except PermissionDenied:
            traceback.print_exc()
            return self.forbidden_view(request, path)
        except:
            traceback.print_exc()
            raise

