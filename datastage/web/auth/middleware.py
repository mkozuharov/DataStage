import base64
import ctypes
import os
import pwd

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import authenticate, login

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
                raise
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

    def process_request(self, request):
        # Can't do anything if we're not uid zero.
        if os.geteuid() != 0:
            return

        if request.user.is_authenticated():
            username = request.user.username
        else:
            username = settings['main:datastage_user']

        user = pwd.getpwnam(username)

        self._libc.setfsuid(user.pw_uid)
        self._libc.setfsgid(user.pw_gid)

