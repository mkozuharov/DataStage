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

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from datastage.dataset import OXDSDataset, Sword2Dataset

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
        discovery.discover(self)
    
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
    addrepository = models.TextField()
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
    
    _dataset_types = {'sword2': Sword2Dataset,
                      'databank': OXDSDataset}
    
    @property
    def dataset(self):
        dataset_cls = self._dataset_types[self.repository.type]
        return dataset_cls(self.path_on_disk,
                           title=self.title,
                           description=self.description,
                           identifier=self.identifier)
