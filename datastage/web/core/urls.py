from django.conf.urls.defaults import patterns, include, url

from datastage.web.core import views

urlpatterns = patterns('',
    url(r'^$', views.SimpleView.as_view(template_name='core/index'), {}, 'index'),
    url(r'^about/$', views.SimpleView.as_view(template_name='info/about'), {}, 'about'),
    url(r'^contact/$', views.SimpleView.as_view(template_name='info/contact'), {}, 'contact'),
)
