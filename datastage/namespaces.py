from rdflib import Namespace

DCTERMS = Namespace('http://purl.org/dc/terms/')
FOAF = Namespace('http://xmlns.com/foaf/0.1/')
OXDS = Namespace('http://vocab.ox.ac.uk/dataset/schema#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
HTML = Namespace('http://www.w3.org/1999/xhtml')
XHTML = Namespace('http://www.w3.org/1999/xhtml#')

namespaces = {}

for name, value in locals().items():
    if isinstance(value, Namespace):
        namespaces[name.lower()] = value

def bind_namespaces(graph):
    for prefix, uri in namespaces.iteritems():
        graph.bind(prefix, uri)
    return graph