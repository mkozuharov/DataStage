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

from django_conneg.views import HTMLView, ErrorCatchingView
from django.utils.datastructures import MergeDict
import httplib

class SimpleView(HTMLView):
    template_name = None
    #error_template_names = MergeDict({httplib.NOT_FOUND: 'core/404'}, ErrorCatchingView.error_template_names)
    #error_template_names = MergeDict({httplib.INTERNAL_SERVER_ERROR: 'core/500'}, ErrorCatchingView.error_template_names)
 
    def get(self, request):
        return self.render(request, {}, self.template_name)
    
class Simple404View(HTMLView):
    template_name = 'core/404'
    #error_template_names = MergeDict({httplib.NOT_FOUND: 'core/404'}, ErrorCatchingView.error_template_names)
    #error_template_names = MergeDict({httplib.INTERNAL_SERVER_ERROR: 'core/404'}, ErrorCatchingView.error_template_names)
 
    def get(self, request):
        return self.render(request, {}, self.template_name)
  
class Simple500View(HTMLView):
    template_name = 'core/500'
    #error_template_names = MergeDict({httplib.NOT_FOUND: 'core/404'}, ErrorCatchingView.error_template_names)
    #error_template_names = MergeDict({httplib.INTERNAL_SERVER_ERROR: 'core/500'}, ErrorCatchingView.error_template_names)
 
    def get(self, request):
        return self.render(request, {}, self.template_name)
  