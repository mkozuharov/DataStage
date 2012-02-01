from django.conf.urls.defaults import patterns, include, url

from datastage.web.dataset import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), {}, 'index'),
    url(r'^remote-login/$', views.SimpleCredentialsView.as_view(), {}, 'simple-credentials'),
    url(r'^submit/$', views.SubmitView.as_view(), {}, 'submit'),
    url(r'^submission/(?P<id>\d+)/$', views.DatasetSubmissionView.as_view(), {}, 'submission-detail'),
)
