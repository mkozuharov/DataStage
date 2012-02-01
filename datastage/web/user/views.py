from django_conneg.views import HTMLView

#from django.contrib.auth.forms.PasswordChangeForm

class IndexView(HTMLView):
    def get(self, request):
        return self.render(request, {}, 'user/index')

class PasswordView(HTMLView):
    def get(self, request):
        pass
