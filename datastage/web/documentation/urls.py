from django.conf.urls.defaults import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^(?:(?P<slug>[a-z\d\-]+)/)?$', views.DocumentationView.as_view(), name='page'),
)
