from base import Dataset
from sword2 import Connection, HttpLayer, HttpResponse, UrlLib2Layer, Entry
import urllib2
import logging
import time
logger = logging.getLogger(__name__)

class SwordSlugRejected(Exception):
    pass

class SwordDepositError(Exception):
    def __init__(self, receipt):
        self.receipt = receipt
        
class SwordServiceError(Exception):
    def __init__(self, msg):
        self.msg = msg

class Sword2(object):
    def preflight_submission(self, dataset, opener, repository):
        logger.info("Carrying out pre-flight submission")
        
        # verify that we can get a service document, and that there
        # is at least one silo and that we can authenticate
        
        if repository.sword2_sd_url is None:
            raise SwordServiceError("No sword2 service-document URL for repository configuration")
            
        # get the service document (for which we must be authenticated)
        conn = Connection(repository.sword2_sd_url, error_response_raises_exceptions=False, http_impl=UrlLib2Layer(opener))
        conn.get_service_document()
        
        # we require there to be at least one workspace
        if conn.sd is None:
            raise SwordServiceError("did not successfully retrieve a service document")
        
        if conn.sd.workspaces is None:
            raise SwordServiceError("no workspaces defined in service document")
        
        if len(conn.sd.workspaces) == 0:
            raise SwordServiceError("no workspaces defined in service document")
        
        workspace = conn.sd.workspaces[0][1]
        
        # we require there to be at least one collection
        if len(workspace) == 0:
            raise SwordServiceError("no collections defined in workspace")
            
        # FIXME: we don't currently have a mechanism to make decisions about
        # which collection to put stuff in, so we just put stuff in the first
        # one for the time being
        col = workspace[0]
        
        # assemble the entry ready for deposit, using the basic metadata
        # FIXME: is there anything further we need to do about the metadata here?
        e = Entry(id=dataset.identifier, title=dataset.title, dcterms_abstract=dataset.description)
        
        # create the item using the metadata-only approach (suppress errors along the way,
        # we'll check for them below)
        receipt = conn.create(col_iri=col.href, metadata_entry=e, suggested_identifier=dataset.identifier)
        
        # check for errors
        if receipt.code >= 400:
            # this is an error
            logger.debug("Received error message from server: " + receipt.to_xml())
            if receipt.error_href == "http://databank.ox.ac.uk/errors/DatasetConflict":
                raise SwordSlugRejected()
            raise SwordDepositError(receipt)
        
        logger.info("Deposit carried out to: " + receipt.location)
        
        return receipt.location
        
    def complete_submission(self, dataset, opener, dataset_submission, filename, retry_limit=3, retry_delay=2):
        logger.info("Carrying out complete submission")
        
        # create a connection
        repository = dataset_submission.repository
        conn = Connection(repository.sword2_sd_url, error_response_raises_exceptions=False, http_impl=UrlLib2Layer(opener))
        
        # get hold of a copy of the deposit reciept
        edit_uri = dataset_submission.remote_url
        
        receipt = None
        
        try:
            receipt = conn.get_deposit_receipt(edit_uri)
        except urllib2.URLError as e:
            # The sword2 client does not catch network errors like this one,
            # which indicates that the url couldn't be reached at all
            
            # don't do anything about it here - we'll try again in a moment
            # and then error out appropriately later
            pass
            
        # at this stage we need to ensure that we actually got back a deposit
        # receipt
        i = 0
        while (receipt is None or receipt.code >= 400) and i < retry_limit:
            err = None
            if receipt is None:
                err = "<unable to reach server>"
            else:
                err = str(receipt.code)
            logger.info("Attempt to retrieve Entry Document failed with error " + str(err) + " ... trying again in " + str(retry_delay) + " seconds")
            i += 1
            time.sleep(retry_delay)
            try:
                receipt = conn.get_deposit_receipt(edit_uri)
            except urllib2.URLError as e:
                # The sword2 client does not catch network errors like this one,
                # which indicates that the url couldn't be reached at all
                
                # just try again up to the retry_limit
                continue
            
        # if we get to here, and the receipt code is still an error, we give
        # up and re-set the item status
        if receipt is None or receipt.code >= 400:
            return self._set_error(dataset_submission, "error", "Attempt to retrieve Entry Document failed " + str(retry_limit + 1) + " times ... giving up")
        
        logger.info("Entry Document retrieved ... continuing to full package deposit")
        
        # if we get to here we can go ahead with the deposit for real
        try:
            with open(filename, "rb") as data:
                new_receipt = conn.update(dr = receipt,
                                payload=data,
                                mimetype="application/zip",
                                filename=dataset.identifier + ".zip", 
                                packaging='http://dataflow.ox.ac.uk/package/DataBankBagIt')
            
            if new_receipt.code >= 400:
                return self._set_error(dataset_submission, "error", "Attempt to deposit content failed")
            
        except urllib2.URLError as e:
            # The sword2 client does not catch network errors like this one,
            # which indicates that the url couldn't be reached at all
            return self._set_error(dataset_submission, "error", "Attempt to deposit content failed")
    
    def _set_error(self, dataset_submission, error, log_message):
        logger.info(log_message)
        dataset_submission.status = error # FIXME: this is not very descriptive, but we are limited to 10 characters and from the allowed list of values
        dataset_submission.save()
        return
