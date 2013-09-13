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
from django.contrib.auth.models import User, Group
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
    
    class Meta:
        verbose_name = "Repository"
        verbose_name_plural = 'Repositories'
    
class DefaultRepository(models.Model):
    repository = models.ForeignKey(Repository)

    class Meta:
        verbose_name = "Choose Default Repository"
        verbose_name_plural = 'Choose Default Repository'

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
    silo = models.TextField()
    identifier = models.TextField()
    license =  models.TextField(blank=True, null=True)
    path_on_disk = models.TextField()
    submitting_user = models.ForeignKey(User)
    repository = models.ForeignKey(Repository)
    status = models.CharField(max_length=10, choices=DATASET_STATUS_CHOICES, default='new')
    queued_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)
    remote_url = models.URLField(blank=True, null=True)
    alternate_url = models.URLField(blank=True, null=True)
    
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
                           identifier=self.identifier,
                           license = self.license)


# Not sure if this class belongs here, but it will do for now
class Project(models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    long_name = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # Every project has exactly one group for each of leaders, members and collaborators
    leader_group = models.OneToOneField(Group, related_name='leaders_of_project')
    member_group = models.OneToOneField(Group, related_name='members_of_project')
    collaborator_group = models.OneToOneField(Group, related_name='collaborators_of_project')
    #TODO: implement project archiving
    is_archived = models.BooleanField(default=False)

    def _get_leaders(self):
        return self.leader_group.user_set.all()
    leaders = property(_get_leaders)

    def _get_members(self):
        return self.member_group.user_set.all()
    members = property(_get_members)

    def _get_collaborators(self):
        return self.collaborator_group.user_set.all()
    collaborators = property(_get_collaborators)

    def __unicode__(self):
        return ' - '.join([self.short_name, self.long_name, self.description])

    class Meta:
        ordering = ['short_name']