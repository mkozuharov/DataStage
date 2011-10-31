

class Dataset(object):
    class IncompleteMetadataException(Exception): pass
    class DatasetIdentifierRejected(Exception):
        def __unicode__(self):
            return "The remote repository rejected the proposed identifier for your dataset."
    class DatasetIdentifierAlreadyExists(DatasetIdentifierRejected):
        def __unicode__(self):
            return "A dataset already exists in the remote repositoy with the proposed identifier."

    def __init__(self, path):
        self._path = path
    
    def package(self):
        raise NotImplementedError