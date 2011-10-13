from django.contrib.formtools.wizard import FormWizard
from django_conneg.views import HTMLView, JSONView

class IndexView(HTMLView):
    def get(self, request):
        return self.render(request, {}, 'dataset/index')

class SubmitView(HTMLView):
    def get(self, request):
        return self.render(request, {}, 'dataset/submit')

#class SubmitWizard(HTMLView, JSONView, CookieWizardView):
#    pass
