from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Experiment.views.home', name='home'),
    # url(r'^Experiment/', include('Experiment.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^stock/', include('stock.urls', namespace='stock')),
    url(r'^ultimatum/', include('ultimatum.urls', namespace='ultimatum')),

    url(r'^$', RedirectView.as_view(url='stock/', permanent=False), name='index')
)
