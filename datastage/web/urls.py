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

# This will monkey-patch django.contrib.auth.models.User
__import__("datastage.web.user.models")
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
admin.site.unregister(User)
admin.site.unregister(Group)

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

