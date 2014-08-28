from django.conf.urls import patterns, include

import settings

urlpatterns = patterns('',
    (r'^%s/' % settings.SUB_SITE, include('Experiment.urls_subsite')),
)
