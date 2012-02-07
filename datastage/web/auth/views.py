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

import urllib

from django.http import HttpResponseRedirect
from django.conf import settings
from django_conneg.views import HTMLView, TextView

class LoginRequiredView(HTMLView, TextView):
    protected_view = None
    
    _format_force_fallback = 'txt'
    
    _browser_search = 'IE Firefox Chrome Opera Safari'.split()
    
    def is_browser(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return any(s in user_agent for s in self._browser_search)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return self.protected_view(request, *args, **kwargs)

        if self.is_browser(request):
            return HttpResponseRedirect('%s?%s' % (settings.LOGIN_URL,
                                                   urllib.urlencode({'next': request.build_absolute_uri()})))
        else:
            realm = request.META.get('HTTP_HOST', 'authenticated_area')
            context = {'login_url': request.build_absolute_uri(settings.LOGIN_URL),
                       'next': request.build_absolute_uri(),
                       'status_code': 401,
                       'additional_headers': {'WWW-Authenticate': 'Basic Realm="%s"' % realm}}
            return self.render(request, context, 'auth/unauthorized')
        