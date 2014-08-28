#!/usr/bin/env python
import os
import sys
import site

site.addsitedir('/usr/lib64/python2.6/site-packages')
site.addsitedir('/usr/lib/python2.6/site-packages')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Experiment.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
