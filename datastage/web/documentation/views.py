from django.http import Http404
from django_conneg.views import HTMLView

class DocumentationView(HTMLView):
    def get(self, request, slug):
        if slug in ('index', 'base'):
            raise Http404
        elif slug is None:
            slug = 'index'
        response = self.render(request, {}, 'documentation/' + slug)

        # Couldn't find an appropriate template; the page doesn't exist.
        if response.status_code != 200:
            raise Http404
        return response
