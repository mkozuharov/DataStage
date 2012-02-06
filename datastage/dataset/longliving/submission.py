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
