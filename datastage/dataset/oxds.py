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

from __future__ import with_statement

import logging
import os
import tempfile
import urllib
import urllib2
import zipfile

import rdflib
import xattr

from datastage.namespaces import OXDS, DCTERMS, RDF, FOAF, bind_namespaces
from datastage.dataset.base import Dataset
import datastage.util.serializers
from datastage.util.multipart import MultiPartFormData

logger = logging.getLogger(__name__)

class OXDSDataset(Dataset):
    def __init__(self, path, **kwargs):
        super(OXDSDataset, self).__init__(path)
        self._manifest_filename = os.path.join(path, 'manifest.rdf')
        self._manifest = bind_namespaces(rdflib.ConjunctiveGraph())
        
        try:
            with open(self._manifest_filename, 'rb') as f:
                self._manifest.parse(f, base=self._manifest_filename)
        except IOError, e:
            pass

        for name in ('title', 'description', 'identifier'):
            setattr(self, name,
                    kwargs.get(name)
                    or unicode(self._manifest.value(rdflib.URIRef(path), DCTERMS[name]) or u''))
        
        
    def package(self):
        pass
    
    def _update_field(self, s, p, o):
        print list(self._manifest.subject_objects(p))
        print "s", (s, p, o, len(self._manifest))
        for o2 in self._manifest.objects(s, p):
            print "REMOVING", s, p, o2
            self._manifest.remove((s, p, o2))
        if o is not None:
            if not isinstance(o, rdflib.Literal):
                o = rdflib.Literal(o)
            self._manifest.add((s, p, o))
    
    def _remove_cbd(self, s):
        for p, o in self._manifest.predicate_objects(s):
            self._manifest.remove((s, p, o))
            if isinstance(o, rdflib.URIRef):
                self._remove_cbd(o)
    
    def update_manifest(self):        
        package = rdflib.URIRef(self._path)
        
        self._manifest += ((package, RDF.type, OXDS.Grouping),)
        
        seen_uris = set()
        for base, dirs, files in os.walk(self._path):
            for filename in files + dirs:
                if not base and filename == 'manifest.rdf':
                    continue
                # URIs use '/' as separators, and we don't want to trust that the OS
                # uses the same separator.
                uri = rdflib.URIRef('/'.join(os.path.split(os.path.join(base, filename))))
                filename = os.path.join(self._path, base, filename)
                seen_uris.add(uri)
                
                if os.path.isdir(filename):
                    self._manifest.add((uri, RDF.type, FOAF.Document))
                
                
                xattr_data = dict(xattr.xattr(filename))
                self._update_field(uri, DCTERMS['title'], xattr_data.get('user.dublincore.title'))
                self._update_field(uri, DCTERMS.description, xattr_data.get('user.dublincore.description'))
        for uri in self._manifest.subjects(RDF.type, FOAF.Document):
            if uri not in seen_uris:
                self._remove_cbd(uri)      
        
        print "Updating"
        self._update_field(package, DCTERMS['title'], self.title)
        self._update_field(package, DCTERMS.description, self.description)
        self._update_field(package, DCTERMS.identifier, self.identifier)

    def save(self, update_manifest=True, enforce_metadata=True):
        if enforce_metadata and not (self.title and self.description):
            raise Dataset.IncompleteMetadataException
        if update_manifest:
            self.update_manifest()
        with open(self._manifest_filename, 'w') as f:
            self._manifest.serialize(f, 'better-pretty-xml', base=self._manifest_filename)
    
    def preflight_submission(self, opener, repository):
        # Make sure we're authenticated
        # opener.open(repository.homepage + 'states')        
        # dataset_list = opener.json(repository.homepage)       
        # if self.identifier in dataset_list:
        # raise self.DatasetIdentifierAlreadyExists
        # else:
        
            try:
                # Attempt to create new dataset
                response = opener.open(repository.homepage + 'datasets/' + self.identifier,
                                       urllib.urlencode({'title': self.title}))
            except urllib2.HTTPError, e:
                if e.code == 400 and e.msg == 'Bad request. Dataset name not valid':
                    raise self.DatasetIdentifierRejected
                elif e.code == 409 :
                     raise self.DatasetIdentifierAlreadyExists             
                elif 200 <= e.code < 300:
                    response = e
                else: 
                    raise

            return response.headers.get('Location', response.url)
    
    def complete_submission(self, opener, repository, update_status):
        update_status('started')
        
        logger.debug("Updating manifest in readiness for submitting dataset")
        self.save()
        
        fd, filename = tempfile.mkstemp('.zip')
        try:
            # We only wanted the file created; we're not going to write to it
            # directly.
            os.close(fd)
            
            # Try a compressed ZIP first, otherwise try without. The zipfile
            # documentation talks of zlib compression being potentially unavailable.
            
            logger.info("Beginning to write zip archive to %r", filename)
            try:
                zip = zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_DEFLATED)
            except RuntimeError:
                zip = zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_STORED)
            
            for base, dirs, files in os.walk(self._path):
                relbase = os.path.relpath(base, self._path)
                for fn in files:
                    print base, relbase, fn
                    if os.path.normpath(os.path.join(relbase, fn)) == 'manifest.rdf':
                        continue
                    zip.write(os.path.join(self._path, base, fn),
                              os.path.join(self.identifier, relbase, fn))
                    logger.debug("Added %r to zip archive at %r",
                                 os.path.join(self._path, base, fn),
                                 os.path.join(self.identifier, relbase, fn))
            
            zip.write(os.path.join(self._manifest_filename), 'manifest.rdf')
            logger.debug("Added manifest.rdf to zip archive")
            
            zip.close()
            
            update_status('transfer')
            logger.debug("Starting transfer to repository")
            
            stat_info = os.stat(filename)
            with open(filename, 'rb') as data:
                data = MultiPartFormData(files=[{'name': 'file',
                                                 'filename': self.identifier + '.zip',
                                                 'stream': data,
                                                 'mimetype': 'application/zip',
                                                 'size': stat_info.st_size}])
                opener.open(repository.homepage + 'datasets/' + self.identifier,
                            data=data,
                            method='POST',
                            headers={'Content-type': data.content_type,
                                     'Content-length': data.content_length})
            
            data = MultiPartFormData(fields=[('filename', self.identifier + '.zip'),
                                             ('id', self.identifier)])
            
            opener.open(repository.homepage + 'items/' + self.identifier,
                        data=data,
                        method='POST',
                        headers={'Content-type': data.content_type,
                                 'Content-length': data.content_length})
            
        finally:
            os.unlink(filename)
        
        
        update_status('submitted')
            

