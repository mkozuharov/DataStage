from django.conf.urls.defaults import patterns, include, url

from datastage.config import settings
from datastage.web.browse import views

urlpatterns = patterns('',
    url(r'^(?P<path>.*)$', views.IndexView.as_view(data_directory=settings.DATA_DIRECTORY), {}, name='index'),
)
