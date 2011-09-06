from django_conneg.views import HTMLView

class SimpleView(HTMLView):
    template_name = None

    def get(self, request):
        return self.render(request, {}, self.template_name)