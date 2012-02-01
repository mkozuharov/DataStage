import urllib2
import urlparse

from lxml import etree

from datastage.config import settings
from datastage.namespaces import namespaces

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
    