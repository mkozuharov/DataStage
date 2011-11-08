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
        