#!/usr/bin/python

import os
import sys

if os.path.exists("src"):
    sys.path.append("src")

from wsgiref.simple_server import make_server

from htcondor_jobview.jobview_app import application

httpd = make_server('', 8000, application)

httpd.base_environ['jobview.config'] = 'tests/unl.conf'

print "Serving on port 8000..."

# Serve until process is killed
httpd.serve_forever()

