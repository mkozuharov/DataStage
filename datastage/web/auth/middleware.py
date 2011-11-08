import base64

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import authenticate, login

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
            
                