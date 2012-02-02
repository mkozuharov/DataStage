from base import Dataset
from sword2 import Connection, HttpLayer, HttpResponse, UrlLib2Layer, Entry
import urllib2

class Sword2(object):
    def preflight_submission(self, dataset, opener, repository):
        # verify that we can get a service document, and that there
        # is at least one silo and that we can authenticate
        
        if repository.sword2_sd_url is None:
            #FIXME: what kind of error to raise here?
            raise Exception("No sword2 service-document URL for repository configuration")
            
        # get the service document (for which we must be authenticated)
        conn = Connection(repository.sword2_sd_url, error_response_raises_exceptions=False, http_impl=UrlLib2Layer(opener))
        conn.get_service_document()
        
        # we require there to be at least one workspace
        if conn.sd is None:
            # FIXME: what kind of error to raise here?
            raise Exception("did not successfully retrieve a service document")
        
        if conn.sd.workspaces is None:
            # FIXME: what kind of error to raise here?
            raise Exception("no workspaces defined in service document")
        
        if len(conn.sd.workspaces) == 0:
            # FIXME: what kind of error to raise here?
            raise Exception("no workspaces defined in service document")
        
        workspace = conn.sd.workspaces[0][1]
        
        # we require there to be at least one collection
        if len(workspace) == 0:
            # FIXME: what kind of error to raise here?
            raise Exception("no collections defined in workspace")
            
        # FIXME: we don't currently have a mechanism to make decisions about
        # which collection to put stuff in, so we just put stuff in the first
        # one for the time being
        col = workspace[0]
        
        # assemble the entry ready for deposit, using the basic metadata
        # FIXME: is there anything further we need to do about the metadata here?
        e = Entry(id=dataset.identifier, title=dataset.title, dcterms_abstract=dataset.description)
        
        # create the item using the metadata-only approach
        receipt = conn.create(col_iri=col.href, metadata_entry=e, suggested_identifier=dataset.identifier)
        
        return receipt.location
        
    """
    Reference ...
    # Make sure we're authenticated
    opener.open(repository.homepage + 'states')
    
    dataset_list = opener.json(repository.homepage)
    
    if self.identifier in dataset_list:
        raise self.DatasetIdentifierAlreadyExists
    else:
        try:
            # Attempt to create new dataset
            response = opener.open(repository.homepage + 'datasets/' + self.identifier,
                                   urllib.urlencode({'title': self.title}))
        except urllib2.HTTPError, e:
            if e.code == 400 and e.msg == 'Bad request. Dataset name not valid':
                raise self.DatasetIdentifierRejected
            elif 200 <= e.code < 300:
                response = e
            else: 
                raise

        return response.headers.get('Location', response.url)
    """
    def complete_submission(self, dataset, opener, repository, update_status):
        pass
    
    """
    Reference ...
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
    """
