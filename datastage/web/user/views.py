from django_conneg.views import HTMLView

class IndexView(HTMLView):
    def get(self, request):
        return self.render(request, {}, 'user/index')