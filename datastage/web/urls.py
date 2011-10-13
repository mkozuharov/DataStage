from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^data/', include('datastage.web.browse.urls', 'browse')),
    url(r'^dataset/', include('datastage.web.dataset.urls', 'dataset')),
    url(r'^', include('datastage.web.core.urls', 'core')),
)

urlpatterns += staticfiles_urlpatterns()
