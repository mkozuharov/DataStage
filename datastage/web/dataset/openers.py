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
import types
import urllib
import urllib2
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

from lxml import etree
import oauth2

from datastage.config import settings
from .models import RepositoryUser

class OAuthHandler(urllib2.BaseHandler):
    def __init__(self, repository, repository_user):
        if not repository.oauth_consumer_key:
            return
        
        self._consumer = oauth2.Consumer(repository.oauth_consumer_key,
                                         repository.oauth_consumer_secret)

        
        
    #def http_error_401(self, request, fp, code, msg, headers):
    #    pass
    
    def http_error_401(self, req, fp, code, msg, headers):
        www_a
    
    def https_request(self, request):
        return request
    
    def https_response(self, request, response):
        return response

class SimpleCredentialsRequired(Exception):
    pass

class LoginFormHandler(urllib2.BaseHandler):
    def __init__(self, repository, repository_user, cookiejar):
        self._base_url = urlparse.urlparse(repository.homepage)._replace(path='/').geturl()
        self._username = repository_user.username
        self._password = repository_user.password
        self._cookiejar = cookiejar
        self._tried = False
        
    def https_response(self, request, response):
        if response.url.startswith(self._base_url) and 'login?' in response.url:
            return self.perform_authentication(request, response)
        return response
    
    def perform_authentication(self, request, response):
        if self._tried:
            raise urllib2.HTTPError(401,
                                    response,
                                    "Authentication failed",
                                    response.headers,
                                    response.fp)
        if not (self._username and self._password):
            raise SimpleCredentialsRequired
        html = etree.parse(response, parser=etree.HTMLParser())
        login_form = html.xpath(".//form[.//input[@type='password']]")[0]
        form_data = dict((e.name, e.value) for e in login_form.xpath('input'))
        
        password_field = login_form.xpath(".//input[@type='password']")[0]
        username_field = password_field.xpath("preceding::input")[-1]
        
        form_data[username_field.attrib['name']] = self._username
        form_data[password_field.attrib['name']] = self._password
        
        target = urlparse.urljoin(response.url, login_form.attrib['action'])
        
        self._tried = True
        try:
            return self.parent.open(target, urllib.urlencode(form_data))
        finally:
            self._tried = False
        return response

class PreemptiveBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    def https_request(self, request):
        credentials = self.passwd.find_user_password(None, request.get_full_url())
        if all(credentials):
            request.add_header(self.auth_header, 'Basic %s' % base64.b64encode(':'.join(credentials)))
        return request
    http_request = https_request

class AuthenticateRedirectHandler(urllib2.HTTPRedirectHandler):
    """
    Ensures that redirects with WWW-Authenticate headers are treated as 401s,
    so that authentication is forced. Useful when a site is redirecting to a
    login page for human users.
    """
    
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if 'WWW-Authenticate' in headers:
            response = urllib.addinfourl(fp, msg, req.get_full_url())
            response.code = 401
            response.msg = headers
            return self.parent.error(
                'http', req, response, 401, msg, headers)
        else:
            return urllib2.HTTPRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)

def get_opener(repository, user):
    repository_user, _ = RepositoryUser.objects.get_or_create(repository=repository,
                                                              user=user)

    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    if repository_user.username and repository_user.password:
        password_manager.add_password(None,
                                      urlparse.urlparse(repository.homepage)._replace(path='/').geturl(),
                                      repository_user.username,
                                      repository_user.password)
    
    if repository.authentication == 'oauth':
        oauth_handler = OAuthHandler(repository, repository_user)
        opener = urllib2.build_opener(oauth_handler)
    elif repository.authentication == 'basic':
        if not (repository_user.username and repository_user.password):
            raise SimpleCredentialsRequired
        basic_auth_handler = PreemptiveBasicAuthHandler(password_manager)
        opener = urllib2.build_opener(basic_auth_handler)
    else:
        oauth_handler = OAuthHandler(repository, repository_user)
        basic_auth_handler = urllib2.HTTPBasicAuthHandler(password_manager)
        opener = urllib2.build_opener(oauth_handler,
                                      basic_auth_handler,
                                      AuthenticateRedirectHandler())

       
    def wrap_open(old_open):
        def open(self, url, data=None, *args, **kwargs):
            headers, method = kwargs.pop('headers', {}), kwargs.pop('method', None)
            if not isinstance(url, urllib2.Request):
                url = urllib2.Request(url, data)
            for key, value in headers.iteritems():
                url.add_header(key, value)
            if method:
                url.get_method = lambda : method
            try:
                return old_open(url)
            except urllib2.HTTPError, e:
                if e.code == 401:
                    raise SimpleCredentialsRequired
                raise
        return types.MethodType(open, type(opener))
    opener.open = wrap_open(opener.open)
    
    def json_request(self, *args, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['Accept'] = 'application/json'
        response = self.open(*args, **kwargs)
        content_type = response.headers['Content-type'].split(';',1)[0]
        if content_type != 'application/json':
            raise ValueError("Unexpected content type")
        return json.load(response)
    opener.json = types.MethodType(json_request, opener)

    opener.addheaders = (('User-Agent', settings.USER_AGENT),)
    
    return opener
