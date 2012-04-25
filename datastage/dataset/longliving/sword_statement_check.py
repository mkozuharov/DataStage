from _future_ import absolute_imports
import logging
import time
import thread
import urllib2
import sys
import datetime

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
    
    # this is how long the thread will sleep between requests (in seconds)
    throttle = 5
    
    # this is how long the thread will sleep between retrys (in seconds)
    retry_delay = 3
    
    # This is how long the thread will sleep between entire batches of updates.
    # This is particularly useful if the total number of submissions is quite
    # small - it will stop the while True loop just spinning aimlessly most of
    # the time. (in seconds)
    batch_throttle = 120
    
    # this is how many times the thread will re-try contacting the server if
    # it suffers a major exception (i.e. not a sword exception, but something
    # network related)
    retry_count = 10
    
    # this is the gap between attempts to check a specific item.  If the item
    # has been checked more recently than this amount of time ago, it will not
    # be checked again on the current run.  Specified in seconds (here it is
    # set to once per day).
    check_gap = 86400
    
    def run(self):
        # just keep going until the thread is killed
        while True:
            self._check_all_datasets()
            time.sleep(SwordStatementCheckThread.batch_throttle)
    
    def _check_all_datasets(self):
        dss = DatasetSubmission.objects.all()
        for dataset_submission in dss:
            if not self._checkable(dataset_submission):
                continue
            self._check_dataset(dataset_submission)

    def _checkable(self, dataset_submission):
        last_checked = dataset_submission.last_checked
        if last_checked is None:
            return True
        now = datetime.datetime.now()
        minimum = datetime.timedelta(0, SwordStatementCheckThread.check_gap)
        gap = now - last_checked
        return gap > minimum

    def _check_dataset(self, dataset_submission):
        retry_counter = 0
        exception = None
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
                        logger.info("URI: " + state_uri + " is an error state ... setting 'error' state on submission record")
                        break
                dataset_submission.last_checked = datetime.datetime.now()
                dataset_submission.save()
                time.sleep(SwordStatementCheckThread.throttle)
        
            except urllib2.URLError as e:
                # if we get an exception, try again up to the limit
                logger.info("Got error connecting to the server ... retrying " + str(retry_counter + 1) + " of " + str(SwordStatementCheckThread.retry_count))
                retry_counter += 1
                exception = e
                time.sleep(SwordStatementCheckThread.retry_delay)
                continue
                
            else:
                # if we don't get an exception, we're done
                return
        
        # if we don't return from the else statement above, it means the retries
        # all failed, and we have a problem.  Raise the last thrown exception.
        raise exception
        
