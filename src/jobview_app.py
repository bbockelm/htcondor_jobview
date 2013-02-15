
import os
import time
import ConfigParser
import re
import json

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




def jobs(environ, start_response):
    global cp
    status = '200 OK'
    headers = [('Content-type', 'application/json'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    
    jobs, groups, schedd, user = summarize_jobs(cp)
    global_dict = {'jobs': jobs, 'groups': groups, 'schedd': schedd, 'user': user}

    return [ json.dumps(global_dict) ]
    
    

def cluster(environ, start_response):
    global cp
    status = '200 OK'
    headers = [('Content-type', 'application/json'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    
    total_slots, free_slots = get_cpu_slots(cp)
    cpu_slots = {'total': total_slots, 'free': free_slots}
    
    return [ json.dumps(cpu_slots) ]
    

def index(environ, start_response):
    status = '200 OK' # HTTP Status
    headers = [('Content-type', 'text/html'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    
    tmpl = loader.load('index.html')
    
    site_name = cp.get("jobview", "site_name")

    return [tmpl.generate(site_name=site_name).render('html', doctype='html')]
    

def not_found(environ, start_response):
    pass


urls = [
    (r'^$', index),
    (r'jobs/?$', jobs),
    (r'cluster/?$', cluster)
]

def application(environ, start_response):
    check_initialized(environ)


    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
            environ['jobview.url_args'] = match.groups()
            return callback(environ, start_response)
    return not_found(environ, start_response)

    #site_name = cp.get("jobview", "site_name")

    #total_slots, free_slots = get_cpu_slots(cp)
    #cpu_slots = {'total': total_slots, 'free': free_slots}

    #jobs, groups, schedd, user = summarize_jobs(cp)

    #tmpl = loader.load('index.html')

    #return [tmpl.generate(site_name=site_name, schedds=schedd, groups=groups, cpu_slots=cpu_slots, jobs=jobs).render('html', doctype='html')]

