"""
WSGI config for Experiment project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import sys
import os
import site

# site.addsitedir('d:/Python/purdue/Lib/site-packages')
site.addsitedir('/usr/lib64/python2.6/site-packages')
site.addsitedir('/usr/lib/python2.6/site-packages')
site.addsitedir('/opt/python/env/designforinstinctsgames/lib/python2.6/site-packages')

# path = 'c:/Apache24/Apps/Experiment'
path = '/var/www/data/root/designforinstinctsgames/apache'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Experiment.settings")

from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()

def application(environ, start_response):
    environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    environ['SCRIPT_NAME'] = '' # my little addition to make it work
    return _application(environ, start_response)

