
import os
import time
import ConfigParser

from genshi.template import TemplateLoader

from jobs import summarize_jobs
from cluster_summary import get_cpu_slots

initialized = False
loader = TemplateLoader('templates', auto_reload=True)
cp = None

def check_initialized(environ):
    global initialized
    global loader
    global cp
    if not initialized:
        loader = TemplateLoader('templates', auto_reload=True)
        tmp_cp = ConfigParser.ConfigParser()
        if 'jobview.config' in environ:
            tmp_cp.read(environ['jobview.config'])
        else:
            tmp_cp.read('/etc/jobview.conf')
        cp = tmp_cp
        initialized = True

def application(environ, start_response):
    check_initialized(environ)

    status = '200 OK' # HTTP Status
    headers = [('Content-type', 'text/html'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    site_name = cp.get("jobview", "site_name")

    total_slots, free_slots = get_cpu_slots(cp)
    cpu_slots = {'total': total_slots, 'free': free_slots}

    jobs, groups, schedd, user = summarize_jobs(cp)

    tmpl = loader.load('index.html')

    return [tmpl.generate(site_name=site_name, schedds=schedd, groups=groups, cpu_slots=cpu_slots, jobs=jobs).render('html', doctype='html')]

