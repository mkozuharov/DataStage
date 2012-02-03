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

from rdflib import URIRef
from rdflib.plugin import register
try: # These moved during the transition from rdflib 2.4 to rdflib 3.0.
    from rdflib.plugins.serializers.rdfxml import PrettyXMLSerializer  # 3.0
    from rdflib.serializer import Serializer
except ImportError:
    from rdflib.syntax.serializers.PrettyXMLSerializer import PrettyXMLSerializer  # 2.4
    from rdflib.syntax.serializers import Serializer

class BetterPrettyXMLSerializer(PrettyXMLSerializer):
    def relativize(self, uri):
        base = URIRef(self.base)
        basedir = URIRef(self.base if base.endswith('/') else base.rsplit('/', 1)[0])
        if base is not None:
            if uri == base:
                uri = URIRef('')
            elif uri == basedir:
                uri = URIRef('.')
            elif uri.startswith(basedir + '/'):
                uri = URIRef(uri.replace(basedir + '/', "", 1))
        return uri
    
register('better-pretty-xml', Serializer, __name__, 'BetterPrettyXMLSerializer')
    
