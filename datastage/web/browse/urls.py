from django.conf.urls.defaults import patterns, include, url

from datastage.web.browse import views

urlpatterns = patterns('',
    url(r'^(?P<path>.*)$', views.IndexView.as_view(), {}, 'index'),
)
