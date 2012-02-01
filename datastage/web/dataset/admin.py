from django.contrib.admin import site

from .models import Repository, DatasetSubmission

site.register(Repository)
site.register(DatasetSubmission)