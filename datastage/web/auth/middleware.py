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

import base64
import ctypes
import os
import pwd

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import authenticate, login
import django.contrib.auth.views as auth_views

from datastage.config import settings

from .views import LoginRequiredView

class BasicAuthMiddleware(object):
    _login_required_view = staticmethod(LoginRequiredView.as_view())
    
    def process_request(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            request.user = AnonymousUser()
            try:
                username, password = self.get_credentials(request.META['HTTP_AUTHORIZATION'])
            except (ValueError, TypeError):
                return self._login_required_view(request)
            
            user = authenticate(username=username, password=password)
            if not user:
                return self._login_required_view(request)
            
            # We don't want to use auth.login as we don't want the logged-in-ness
            # to extend beyond this one request.
            request.user = user
            
    
    def get_credentials(self, authorization):
        if not authorization.startswith('Basic '):
            raise ValueError
        return base64.b64decode(authorization[6:]).split(':', 1)
            
class DropPrivilegesMiddleware(object):
    """This middleware drops down to the user performing the request."""

    _libc = ctypes.cdll.LoadLibrary('libc.so.6')

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Can't do anything if we're not uid zero.
        if os.geteuid() != 0:
            return

        if view_func is auth_views.login:
            # We need to be able to reach /etc/shadow
            username = 'root'
        elif request.user.is_authenticated():
            username = request.user.username
        else:
            username = settings['main:datastage_user']

        user = pwd.getpwnam(username)

        self._libc.setfsuid(user.pw_uid)
        self._libc.setfsgid(user.pw_gid)

