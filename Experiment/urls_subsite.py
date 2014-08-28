from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from django.contrib.staticfiles import views

from django.shortcuts import Http404
def no_view(request):
    raise Http404

urlpatterns = patterns('',
    url(r'^stock/', include('stock.urls', namespace='stock')),
    url(r'^ultimatum/', include('ultimatum.urls', namespace='ultimatum')),

    url(r'^$', RedirectView.as_view(url='stock/', permanent=False), name='index'),
    #url(r'static/$', no_view, name='static_root'),
	url(r'^static/(?P<path>.*)$', views.serve),
)
