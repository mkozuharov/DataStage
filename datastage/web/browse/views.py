# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

import datetime
import errno
import httplib
import mimetypes
import os
from os.path import abspath, dirname
import pwd
import tempfile
import urllib
import xattr
import zipfile
import httplib
import shutil
from wsgiref.handlers import format_date_time
from django.utils.datastructures import MergeDict
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect
from django.views.generic import View
from django.utils.decorators import method_decorator
from django_conneg.http import HttpResponseSeeOther
from django_conneg.decorators import renderer
from django_conneg.views import ContentNegotiatedView, HTMLView, JSONView, TextView, ErrorCatchingView
import posix1e

from datastage.web.auth.decorators import login_required
from datastage.web.dataset.models import DatasetSubmission
from datastage.config import settings
from datastage.util.path import statinfo_to_dict

def can_read(path):
    try:
        if os.path.isdir(path):
            os.stat(os.path.join(path, '.'))
        else:
            with open(path, 'r'):
                pass
        return True
    except OSError, e:
        if e.errno == errno.EACCES:
            return False
        raise
def can_write(path):
    try:
        if os.path.isdir(path):
            return False
        else:
            with open(path, 'r+'):
                return True
    except OSError, e:
        if e.errno == errno.EACCES:
            return False
        raise

class DirectoryView(HTMLView, JSONView):
    _json_indent = 2

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
            subpath.update({
                'type': 'dir' if os.path.isdir(subpath_on_disk) else 'file',
                'stat': statinfo_to_dict(subpath_stat),
                'last_modified': datetime.datetime.fromtimestamp(subpath_stat.st_mtime),
                'url': request.build_absolute_uri(reverse('browse:index',
                                                          kwargs={'path': subpath['path']})),
                'link': can_read(subpath_on_disk),
            })
            print subpath_on_disk, subpath['link']
            try:
                pw_user = pwd.getpwuid(subpath_stat.st_uid)
                subpath.update({'owner_name': pw_user.pw_gecos,
                                'owner_username': pw_user.pw_name})
            except KeyError:
                subpath['owner'] = None
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


    def get(self, request, path_on_disk, path, message=None):
        if path:
            parent_url = request.build_absolute_uri(reverse('browse:index',
                                                    kwargs={'path': ''.join(p + '/' for p in path.split('/')[:-2])}))
        else:
            parent_url = None

        subpaths, sort_name, sort_reverse = self.get_subpath_data(request, path_on_disk, path)

        stat = os.stat(path_on_disk)
        context = {
            'path': path,
            'message': message,
            'parent_url': parent_url,
            'subpaths': subpaths,
            'stat': statinfo_to_dict(stat),
            'additional_headers': {
                'Last-Modified': format_date_time(stat.st_mtime),
            },
            'sort_name': sort_name,
            'sort_reverse': sort_reverse,
            'column_names': (('name', 'Name'), ('modified', 'Last modified'), ('size', 'Size'), ('owner_name', 'Owner')),
            'dataset_submissions': DatasetSubmission.objects.filter(path_on_disk=path_on_disk),
        }

        return self.render(request, context, 'browse/directory')

    def post(self, request, path_on_disk, path):
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
                    del subpath_xattr[key]
                elif value:
                    subpath_xattr[key] = value
        return HttpResponseSeeOther('')


class FileView(View):
    def get(self, request, path_on_disk, path):
        mimetype, encoding = mimetypes.guess_type(path_on_disk)
        stat = os.stat(path_on_disk)

        response = HttpResponse(open(path_on_disk, 'rb'), mimetype=mimetype)
        response['Last-Modified'] = format_date_time(stat.st_mtime)
        response['Content-Length'] = stat.st_size
        if not mimetype:
            del response['Content-Type']
        return response

class ForbiddenView(HTMLView, JSONView, TextView):
    _json_indent = 2

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

    def get(self, request, path_on_disk, path):
        if not os.path.isdir(path_on_disk):
            raise Http404
        return self.render_to_format(request,{'path_on_disk': path_on_disk}, 'application/zip','zip')
        
   # def post(self, request, path_on_disk, source_file, path):
   #     if not os.path.isdir(path_on_disk):
   #         raise Http404
   #     return self.render_to_format(request, {'path_on_disk': path_on_disk, 'source_file': source_file },'text/html','html')        

        
        
    @renderer(format='zip', mimetypes=('application/zip',), name='ZIP archive')
    def render_zip(self, request, context, template_name):

        temp_file = tempfile.TemporaryFile()
        basename = os.path.basename(context['path_on_disk'])

        try:
            zip_file = zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED)
        except:
            zip_file = zipfile.ZipFile(temp_file, 'w')

        for root, dirs, files in os.walk(context['path_on_disk']):
            dirs[:] = [d for d in dirs if can_read(os.path.join(root, d))]
            files[:] = [f for f in files if can_read(os.path.join(root, f))]
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
        
        
        
class UploadView(ContentNegotiatedView):
        
    def post(self, request, path_on_disk, source_file, path):
        if not os.path.isdir(path_on_disk):
            raise Http404
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        basename = os.path.basename(path_on_disk)
        src_file=source_file
        msg = None

        try:
	        if src_file.multiple_chunks() == True:
	           for chunk in src_file.chunks():
	        	 temp_file.write(chunk)
	        	 temp_file.close()
	        else:
	             temp_file.write(src_file.read())
	             fileName, fileExtension = os.path.splitext(src_file.name)
	             
	        if fileExtension == ".zip":
	             msg =  "The package: ' " + src_file.name + " ' has been successfully unpacked!"	   
	             zip_ref = zipfile.ZipFile(temp_file, 'r')
	             zip_ref.extractall(path_on_disk)
	             zip_ref.close() 
	        else:
	             msg =  "The file: ' " + src_file.name + " ' has been successfully uploaded!"
	             temp_file.write(src_file.read())
	             temp_file.close()
	             temp_dir = tempfile.gettempdir()
	             temp_path = os.path.join(temp_dir, temp_file.name)
	             shutil.copy2(temp_path,path_on_disk+"/"+src_file.name)

        except Exception, e:
            msg = "Upload was unsuccessful !"
        msgcontext={'path_on_disk':path_on_disk,'message': msg }
        url = '%s?%s' % ( '/data/'+path, urllib.urlencode({'message': msg}))
        
        msgcontext={'path_on_disk':path_on_disk,'message': msg }
        url = '%s?%s' % ( '/data/'+path, urllib.urlencode({'message': msg}))
                            
        return HttpResponseSeeOther(url)

          
	        
class IndexView(ContentNegotiatedView):
    data_directory = None
    source_file = None
    error_template_names = MergeDict({httplib.FORBIDDEN: 'browse/403'}, ErrorCatchingView.error_template_names)
    directory_view = staticmethod(DirectoryView.as_view())
    file_view = staticmethod(FileView.as_view())
    forbidden_view = staticmethod(ForbiddenView.as_view())

    action_views = {'zip': ZipView.as_view(),'upload': UploadView.as_view()}

    @method_decorator(login_required)
    def dispatch(self, request, path):
        path_parts = path.rstrip('/').split('/')
        message = request.GET.get('message') 
        if path and any(part in ('.', '..', '') for part in path_parts):
            raise Http404

        self.path_on_disk = path_on_disk = os.path.normpath(os.path.join(self.data_directory, *path_parts))
        
        try:
            if not can_read(path_on_disk):
                return self.forbidden_view(request, path)
        except IOError, e:
            if e.errno == errno.ENOENT and request.method not in ('PUT',):
                raise Http404
            raise

        try:
            # action views are additional bits of behaviour for a location
            action_view = self.action_views.get(request.REQUEST.get('action'))
            src_file = None
            if request.method == 'POST':
                #src_file = "/Users/bhavana/Desktop/services.sh"
            	src_file = request.FILES['file']
            if action_view:
                if src_file:
                	return action_view(request, path_on_disk, src_file, path)
                else:
                	return action_view(request, path_on_disk,path)
            elif request.method.lower() in ('get', 'head'):
                view = self.directory_view if os.path.isdir(path_on_disk) else self.file_view
                if view == self.directory_view and path and not path.endswith('/'):
                    return HttpResponsePermanentRedirect(reverse('browse:index', kwargs={'path':path + '/', 'message':message}))
                response = view(request, path_on_disk, path, message)
            else:
                response = super(IndexView, self).dispatch(request, path)
            response['Allow'] = ','.join(m.upper() for m in self.http_method_names)
            response['DAV'] = "1,2"
            response['MS-Author-Via'] = 'DAV'
            return response
        except PermissionDenied:
            return self.forbidden_view(request, path)
        except:
            raise

