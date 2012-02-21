from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from datastage.dataset import OXDSDataset

REPOSITORY_TYPE_CHOICES = (
    ('sword2', 'Sword-2'),
    ('databank', 'DataBank'),
    ('unknown', 'Unknown'),
)

AUTHENTICATION_TYPE_CHOICES = (
    ('basic', 'HTTP Basic Authentication'),
    ('oauth', 'OAuth'),
)

DATASET_STATUS_CHOICES = (
    ('new', 'Submission being finalized'),
    ('queued', 'Queued for submission'),
    ('started', 'Submission started'),
    ('transfer', 'Upload in progress'),
    ('submitted', 'Submitted successfully'),
    ('error', 'Submission failed'),
)

class Repository(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=8, choices=REPOSITORY_TYPE_CHOICES, null=True, blank=True)
    homepage = models.URLField()
    
    authentication = models.CharField(max_length=12, choices=AUTHENTICATION_TYPE_CHOICES, blank=True)
    
    sword2_sd_url = models.URLField(blank=True, null=True)
    
    oauth_consumer_key = models.TextField(blank=True)
    oauth_consumer_secret = models.TextField(blank=True)
    
    def discover(self):
        from datastage.dataset import discovery
        # discovery.discover(self)
        discovery.analyse_endpoint(self)
    
    def save(self, *args, **kwargs):
        if self.type is None:
            self.discover()
        super(Repository, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return self.name

class RepositoryUser(models.Model):
    repository = models.ForeignKey(Repository)
    user = models.ForeignKey(User)
    
    oauth_key = models.TextField(blank=True)
    oauth_secret = models.TextField(blank=True)
    
    username = models.TextField(blank=True)
    password = models.TextField(blank=True)


class DatasetSubmission(models.Model):
    title = models.TextField()
    description = models.TextField()
    identifier = models.TextField()
    path_on_disk = models.TextField()
    submitting_user = models.ForeignKey(User)
    repository = models.ForeignKey(Repository)
    status = models.CharField(max_length=10, choices=DATASET_STATUS_CHOICES, default='new')
    queued_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    remote_url = models.URLField(blank=True, null=True)
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('dataset:submission-detail', args=[self.id])
    
    # FIXME: I'm not really sure of the consequences of this, but I have implemented
    # the SWORD2 connector independently of the datasets, as a function of the
    # repository rather than the dataset - which makes more sense - so here both
    # dataset types are the same implementation
    _dataset_types = {'sword2': OXDSDataset,
                      'databank': OXDSDataset}
    
    @property
    def dataset(self):
        dataset_cls = self._dataset_types[self.repository.type]
        return dataset_cls(self.path_on_disk,
                           title=self.title,
                           description=self.description,
                           identifier=self.identifier)
