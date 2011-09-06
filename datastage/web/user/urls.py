from django.conf.urls.defaults import patterns, include, url

from datastage.web.user import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), {}, 'index'),
)
