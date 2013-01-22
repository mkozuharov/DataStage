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

import logging

from django_longliving.base import LonglivingThread

from datastage.dataset import SUBMISSION_QUEUE
from datastage.web.dataset.models import DatasetSubmission
from datastage.web.dataset import openers

logger = logging.getLogger(__name__)

class SubmissionThread(LonglivingThread):
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
                    
    
    def process_item(self, client, pk):
        dataset_submission = DatasetSubmission.objects.get(pk=pk)
        
        logger.debug("Received submission request for %r to %r",
                    dataset_submission.identifier,
                    dataset_submission.remote_url)
                    #dataset_submission.repository.homepage)
        
        dataset = dataset_submission.dataset
        
        opener = openers.get_opener(dataset_submission.repository,
                                    dataset_submission.submitting_user)
        
        def update_status(status):
            logger.debug("Status updated to %r", status)
            dataset_submission.status = status
            dataset_submission.save()

        dataset.complete_submission(opener, dataset_submission, update_status)
        logger.info("Submission completed")
