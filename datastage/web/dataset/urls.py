from django.conf.urls.defaults import patterns, include, url

from datastage.web.dataset import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), {}, 'index'),
)
