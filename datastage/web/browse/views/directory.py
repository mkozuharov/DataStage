import datetime
import errno
import httplib
import os
import pwd
import shutil
import tempfile
import urllib
from wsgiref.handlers import format_date_time
import zipfile

from django.http import Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django_conneg.decorators import renderer
from django_conneg.http import HttpResponseSeeOther
from django_conneg.views import HTMLView, JSONView
import posix1e
import xattr

from datastage.util.path import statinfo_to_dict
from datastage.web.dataset.models import DatasetSubmission

from .base import BaseBrowseView

class DirectoryView(HTMLView, JSONView, BaseBrowseView):
    _json_indent = 2

    sorts = {
        'size': lambda sp: (sp['stat']['st_size'] if sp['type'] == 'file' else 0),
        'name': lambda sp: (sp['type'] != 'dir', sp['name'].lower()),
        'modified': lambda sp: sp['last_modified'],
    }

    def get_subpath_data(self, request, path):
        try:
            sort_name = request.GET.get('sort') or 'name'
            sort_function = self.sorts[request.GET.get('sort', 'name')]
            sort_reverse = {'true': True, 'false': False}[request.GET.get('reverse', 'false')]
        except KeyError:
            raise Http404

        with self.access_error_handler():
            subpaths = [{'name': name} for name in os.listdir(self.path_on_disk) if not name.startswith('.')]

        for subpath in subpaths:
            subpath_on_disk = os.path.join(self.path_on_disk, subpath['name'])
            try:
                subpath_stat = os.stat(subpath_on_disk)
            except OSError, e:
                if e.errno == errno.ENOENT:
                    subpath['type'] = 'missing'
                    continue
                raise
            subpath['path'] = '%s%s' % (self.path, subpath['name']) if self.path else subpath['name']
            subpath.update({
                'type': 'dir' if os.path.isdir(subpath_on_disk) else 'file',
                'stat': statinfo_to_dict(subpath_stat),
                'last_modified': datetime.datetime.fromtimestamp(subpath_stat.st_mtime),
                'url': request.build_absolute_uri(reverse('browse:index',
                                                          kwargs={'path': subpath['path']})),
                'link': self.can_read(subpath_on_disk),
                'can_read': self.can_read(subpath_on_disk),
                'can_write': self.can_write(subpath_on_disk),
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


    def get(self, request, path):
        if self.path:
            parent_url = request.build_absolute_uri(reverse('browse:index',
                                                    kwargs={'path': ''.join(p + '/' for p in path.split('/')[:-2])}))
        else:
            parent_url = None

        subpaths, sort_name, sort_reverse = self.get_subpath_data(request, path)

        stat = os.stat(self.path_on_disk)
        context = {
            'path': self.path,
            'message': request.GET.get('message'),
            'parent_url': parent_url,
            'subpaths': subpaths,
            'stat': statinfo_to_dict(stat),
            'additional_headers': {
                'Last-Modified': format_date_time(stat.st_mtime),
            },
            'sort_name': sort_name,
            'sort_reverse': sort_reverse,
            'column_names': (('name', 'Name'), ('modified', 'Last modified'), ('size', 'Size'), ('owner_name', 'Owner')),
            'dataset_submissions': DatasetSubmission.objects.filter(path_on_disk=self.path_on_disk),
        }

        return self.render(request, context, 'browse/directory')

    def post(self, request, path):
        subpaths, sort_name, sort_reverse = self.get_subpath_data(request, path)

        for subpath in subpaths:
            subpath_on_disk = os.path.join(self.path_on_disk, subpath['name'])
            if not subpath.get('can_write'):
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
        if request.is_ajax():
            return HttpResponse('', status=httplib.NO_CONTENT)
        else:
            return HttpResponseSeeOther('')

    @renderer(format='zip', mimetypes=('application/zip',), name='ZIP archive')
    def render_zip(self, request, context, template_name):
        temp_file = tempfile.TemporaryFile()
        basename = os.path.basename(self.path_on_disk)

        try:
            zip_file = zipfile.ZipFile(temp_file, 'w', compression=zipfile.ZIP_DEFLATED)
        except:
            zip_file = zipfile.ZipFile(temp_file, 'w')

        for root, dirs, files in os.walk(self.path_on_disk):
            dirs[:] = [d for d in dirs if self.can_read(os.path.join(root, d))]
            files[:] = [f for f in files if self.can_read(os.path.join(root, f))]
            for fn in files:
                fn = os.path.join(root, fn)
                zip_file.write(fn,
                               os.path.join(basename,
                                            os.path.relpath(fn, self.path_on_disk)))

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

class UploadView(HTMLView, BaseBrowseView):
    def post(self, request, path):
        src_file = None
        if 'file' in request.FILES:
            src_file = request.FILES['file']

        if not self.can_write(path):
            raise PermissionDenied

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        basename = os.path.basename(self.path_on_disk)

        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, temp_file.name)
        parent_acl = posix1e.ACL(file=self.path_on_disk.encode('utf-8'))
        msg = None
        abs_path = request.build_absolute_uri(reverse('browse:index',kwargs={'path': path}))
        if src_file:
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

                    # Get the parent acl and apply it to the zip file before the zip is unpacked
                    parent_acl.applyto(temp_path)

                    zip_ref = zipfile.ZipFile(temp_file, 'r')
                    zip_ref.extractall(self.path_on_disk)
                    zip_ref.close()
                else:
                    msg =  "The file: ' " + src_file.name + " ' has been successfully uploaded!"
                    temp_file.write(src_file.read())
                    temp_file.close()

                    temp_path = os.path.join(temp_dir, temp_file.name)
                    shutil.copy2(temp_path, os.path.join(self.path_on_disk, src_file.name))

                    # Get the parent acl and apply it to the child entry
                    child_entry = self.path_on_disk+'/'+src_file.name
                    parent_acl.applyto(child_entry)

            except (IOError, OSError) as e:
                if e.errno == errno.ENOENT:
                    raise Http404
                elif e.errno == errno.EACCES:
                    msg = "Files can only be uploaded in your own area!"
                else:
                    msg = "Upload was unsuccessful !"
            except Exception, e:
                msg = "Upload was unsuccessful !"
            msgcontext={'message': msg }
            uri = abs_path + "?" +  urllib.urlencode({'message': msg})
            return HttpResponseSeeOther(uri)

        return HttpResponseSeeOther(abs_path)
