import mock
import unittest

from django.http import HttpRequest

from datastage.web.tests import DatastageWebTestCase

class ViewsTestCase(DatastageWebTestCase):
    
    def testIsBrowser(self):
        from .views import LoginRequiredView
        
        user_agents = {True:  ['Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16',
                               'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
                               'Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.2.17) Gecko/20110428 Fedora/3.6.17-1.fc14 Firefox/3.6.17'],
                       False: ['Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                               'msnbot/1.1 (+http://search.msn.com/msnbot.htm)',
                               'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',
                               'Microsoft-WebDAV-MiniRedir/5.1.2600',
                               'Microsoft Data Access Internet Publishing Provider DAV',
                               'gvfs/1.6.6']}

        view = LoginRequiredView()
        
        for is_browser, uas in user_agents.items():
            for ua in uas:
                
                request = mock.Mock(HttpRequest)
                request.META = mock.Mock(dict)
                request.META.get.return_value = ua
                
                self.assertEqual(view.is_browser(request), is_browser)
                
                self.assertEqual(request.META.get.call_count, 1)
                self.assertEqual(request.META.get.call_args[0][0], 'HTTP_USER_AGENT')
        
