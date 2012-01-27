# This will monkey-patch django.contrib.auth.models.User
__import__("datastage.web.user.models")

from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import django.contrib.auth.views as auth_views

urlpatterns = patterns('',
    url(r'^data/', include('datastage.web.browse.urls', 'browse')),
    url(r'^docs/', include('datastage.web.documentation.urls', 'documentation')),
    url(r'^dataset/', include('datastage.web.dataset.urls', 'dataset')),
    url(r'^', include('datastage.web.core.urls', 'core')),
    url(r'^login/$', auth_views.login, {}, 'login'),
    url(r'^logout/$', auth_views.logout, {}, 'logout'),
    url(r'^admin/', include(admin.site.urls)),
)  

urlpatterns += staticfiles_urlpatterns()

