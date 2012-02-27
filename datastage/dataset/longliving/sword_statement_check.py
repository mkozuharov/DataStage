import logging
import time
import thread
import urllib2
import sys

from django_longliving.base import LonglivingThread

from datastage.dataset import SUBMISSION_QUEUE
from datastage.web.dataset.models import DatasetSubmission
from datastage.web.dataset import openers

from sword2 import Connection, UrlLib2Layer

logger = logging.getLogger(__name__)

# list of all the error states that we can see in the statement that we want
# to be able to react to
ERROR_STATES = [
    "http://databank.ox.ac.uk/errors/UnzippingIssue"
]

# NOTE: this thread is resistant to being stopped.  A KeyboardInterrupt will
# NOT suffice, it will need to be killed with a "kill <pid>" on the command
# line

class SwordStatementCheckThread(LonglivingThread):
    
    # FIXME: not quite sure how the __init__ function on LonglivingThread, 
    # so setting this as a class variable for the time being
    
    # this is how long the thread will sleep between requests
    throttle = 5
    
    # this is how many times the thread will re-try contacting the server if
    # it suffers a major exception (i.e. not a sword exception, but something
    # network related)
    retry_count = 10
    
    def run(self):
        # just keep going until the thread is killed
        while True:
            self._check_all_datasets()
    
    def _check_all_datasets(self):
        dss = DatasetSubmission.objects.all()
        for dataset_submission in dss:
            self._check_dataset(dataset_submission)

    def _check_dataset(self, dataset_submission):
        retry_counter = 0
        while retry_counter < SwordStatementCheckThread.retry_count:
            try:
                logger.info("Checking state of dataset at " + dataset_submission.remote_url)
                
                opener = openers.get_opener(dataset_submission.repository,
                                        dataset_submission.submitting_user)
                conn = Connection(error_response_raises_exceptions=False, http_impl=UrlLib2Layer(opener))
                receipt = conn.get_deposit_receipt(dataset_submission.remote_url)
                statement = conn.get_ore_sword_statement(receipt.ore_statement_iri)
                for state_uri, state_desc in statement.states:
                    logger.info("Dataset has state URI: " + state_uri)
                    if state_uri in ERROR_STATES:
                        dataset_submission.status = 'error'
                        dataset_submission.save()
                        logger.info("URI: " + state_uri + " is an error state ... setting 'error' state on submission record")
                time.sleep(SwordStatementCheckThread.throttle)
        
            except urllib2.URLError as e:
                # if we get an exception, try again up to the limit
                retry_counter += 1
                continue
                
            else:
                # if we don't get an exception, we're done
                return
            
            
    """
    def run(self):
        client = self.get_redis_client()
        
        for key, pk in self.watch_queue(client, SUBMISSION_QUEUE, True):
            try:
                self.process_item(client, pk)
            except Exception:
                logger.exception("Failed to process submission")
                try:
                    dataset_submission = DatasetSubmission.objects.get(pk=pk)
                    dataset_submission.status = 'error'
                    dataset_submission.save()
                except Exception:
                    logger.exception("Failed to mark submission as failed")
    """             
    
    """
    def process_item(self, client, pk):
        dataset_submission = DatasetSubmission.objects.get(pk=pk)
        
        logger.info("Received submission request for %r to %r",
                    dataset_submission.identifier,
                    dataset_submission.repository.homepage)
        
        dataset = dataset_submission.dataset
        opener = openers.get_opener(dataset_submission.repository,
                                    dataset_submission.submitting_user)
        
        def update_status(status):
            logger.debug("Status updated to %r", status)
            dataset_submission.status = status
            dataset_submission.save()

        dataset.complete_submission(opener, dataset_submission, update_status)

        logger.info("Submission completed")
    """
    
