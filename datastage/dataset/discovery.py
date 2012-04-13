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

import urllib2
import urlparse
import sword2

from lxml import etree

from datastage.config import settings
from datastage.namespaces import namespaces

# from sword2.sword2_logging import logging
import logging
d_l = logging.getLogger(__name__)

class DiscoveryError(Exception):
    pass

def urlopen(*args, **kwargs):
    headers = kwargs.pop('headers', {})
    method = kwargs.pop('method', None)
    request = urllib2.Request(*args, **kwargs)
    if method:
        request.get_method = lambda : method
    for key, value in headers.iteritems():
        request.add_header(key, value)
    request.add_header('User-Agent', settings.USER_AGENT)
    return urllib2.urlopen(request)

def analyse_endpoint(repository):
    # get a properly formatted URL
    url = urlparse.urlparse(repository.homepage)._replace(path='/').geturl()
    
    d_l.info("attempting discovery on repository: " + url)
    
    # start with sword auto-discovery (use Urllib2 to be in-line with the
    # rest of datastage
    try:
        ad = sword2.AutoDiscovery(url, http_impl=sword2.UrlLib2Layer())
        d_l.debug("AutoDiscovery request completed without error")
    except urllib2.HTTPError, e:
        raise DiscoveryError("Couldn't connect; received code %d" % e.code)
    except urllib2.URLError, e:
        raise DiscoveryError("Couldn't contact remote host: %s" % e)
    
    # if the auto-discovery gives us a service document, we are good to go
    d_l.debug("AutoDiscovery found following sword2 service document: " + str(ad.service_document))
    if ad.service_document is not None:
        repository.sword2_sd_url = ad.service_document
        repository.type = 'sword2'
        d_l.info("Found sword2 repository with service document: " + ad.service_document)
        return
    
    # FIXME: this should be deprecated
    # if not, we need to check if this is an old-style DataBank repository
    d_l.debug("Did not find sword2 service document, checking old-style DataBank criteria")
    content_type = ad.response['Content-type'].split(';')[0]
    d_l.debug("Content-Type of response was: " + content_type)
    if content_type == 'application/xhtml+xml':
        html = etree.parse(ad.data)
    elif content_type == 'text/html':
        html = etree.parse(ad.data, parser=etree.HTMLParser())
    else:
        raise DiscoveryError("Remote homepage returned unexpected content-type: %r" % content_type)
    
    databank_search = html.xpath(".//form[@action='/search/raw']")
    if databank_search:
        d_l.info("Found old-style databank repository")
        repository.type = 'databank'
        return
    
    # if we get to here there was a discovery problem 
    raise DiscoveryError("Couldn't discover type of remote repository")

# FIXME: this is now deprecated
def discover(repository):
    url = urlparse.urlparse(repository.homepage)._replace(path='/').geturl()
    try:
        response = urlopen(url)
    except urllib2.HTTPError, e:
        raise DiscoveryError("Couldn't connect; received code %d" % e.code)
    except urllib2.URLError, e:
        raise DiscoveryError("Couldn't contact remote host: %s" % e)
    
    content_type = response.headers.get('Content-type').split(';')[0]
    if content_type == 'application/xhtml+xml':
        html = etree.parse(response)
    elif content_type == 'text/html':
        html = etree.parse(response, parser=etree.HTMLParser())
    else:
        raise DiscoveryError("Remote homepage returned unexpected content-type: %r" % content_type)
    
    sword_link = html.xpath("/html:html/html:head/html:link[@rel='sword']", namespaces=namespaces) \
              or html.xpath("/html/head/link[@rel='sword']")
    
    if sword_link:
        href = sword_link[0].attrib.get('href')
        if href:
            repository.sword_sd_url = urlparse.urljoin(response.url, href)
            repository.type = 'sword2'
            return
    
    databank_search = html.xpath(".//form[@action='/search/raw']")
    if databank_search:
        repository.type = 'databank'
        return
        
    
    #try:
    #    print urlparse.urljoin(repository.homepage, 'silos')
    #    response = urlopen(urlparse.urljoin(repository.homepage, 'silos'),
    #                       headers={'Accept': 'application/json'})
    #except (urllib2.URLError, urllib2.HTTPError), e:
    #    raise DiscoveryError("Couldn't discover type of remote repository")
    # 
    #content_type = response.headers.get('Content-type')
    #if content_type == 'application/json':
    #    repository.type = 'databank'
    #    return
    
    raise DiscoveryError("Couldn't discover type of remote repository")
    
