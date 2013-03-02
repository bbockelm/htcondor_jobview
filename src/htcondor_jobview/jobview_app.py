
import os
import time
import ConfigParser
import re
import json

from genshi.template import TemplateLoader

from jobs import summarize_jobs
from cluster_summary import get_cpu_slots
import jobview_rrd

initialized = False
loader = TemplateLoader('templates', auto_reload=True)
cp = None

def check_initialized(environ):
    global initialized
    global loader
    global cp
    if not initialized:
        if 'jobview.templates' in environ:
            loader = TemplateLoader(environ['jobview.templates'], auto_reload=True)
        else:
            loader = TemplateLoader('/usr/share/htcondor-jobview/templates', auto_reload=True)
        tmp_cp = ConfigParser.ConfigParser()
        if 'jobview.config' in environ:
            tmp_cp.read(environ['jobview.config'])
        else:
            tmp_cp.read('/etc/jobview.conf')
        cp = tmp_cp
        initialized = True


def jobs(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'application/json'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    
    jobs, groups, schedd, user = summarize_jobs(cp)
    global_dict = {'jobs': jobs, 'groups': groups, 'schedd': schedd, 'user': user}

    return [ json.dumps(global_dict) ]
    
jobs_graph_re = re.compile(r'^/+jobs_graph/?([a-zA-Z]+)?/?$')
def jobs_graph(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png'),
               ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    path = environ.get('PATH_INFO', '')
    m = jobs_graph_re.match(path)
    interval = "daily"
    if m.groups()[0]: interval=m.groups()[0]

    return [ jobview_rrd.graph_rrd(cp, "jobs", interval) ]


def cluster(environ, start_response):
    global cp
    status = '200 OK'
    headers = [('Content-type', 'application/json'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    
    total_slots, free_slots = get_cpu_slots(cp)
    cpu_slots = {'total': total_slots, 'free': free_slots}
    
    return [ json.dumps(cpu_slots) ]
    

cluster_graph_re = re.compile(r'^/+cluster_graph/?([a-zA-Z]+)?/?$')
def cluster_graph(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png'),
               ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    path = environ.get('PATH_INFO', '')
    m = cluster_graph_re.match(path)
    interval = "daily"
    if m.groups()[0]: interval=m.groups()[0]

    return [ jobview_rrd.graph_rrd(cp, "cluster", interval) ]


schedd_rates_graph_re = re.compile(r'^/+schedd_rates_graph/?([a-zA-Z]+)?/?([a-zA-Z.\-_@ 0-9]+)?/?$')
def schedd_rates_graph(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png'),
               ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    path = environ.get('PATH_INFO', '')
    m = schedd_rates_graph_re.match(path)
    interval = "daily"
    if m.groups()[0]: interval=m.groups()[0]

    if m.groups()[1]:
        return [ jobview_rrd.graph_rrd(cp, "schedd_rates", interval, m.groups()[1]) ]
    else:
        return [ jobview_rrd.graph_rrd(cp, "schedd_rates", interval) ]


schedd_jobs_graph_re = re.compile(r'^/+schedd_jobs_graph/?([a-zA-Z]+)?/?([a-zA-Z.\-_@ 0-9]+)?/?$')
def schedd_jobs_graph(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png'),
               ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    path = environ.get('PATH_INFO', '')
    m = schedd_jobs_graph_re.match(path)
    interval = "daily"
    if m.groups()[0]: interval=m.groups()[0]

    if m.groups()[1]:
        return [ jobview_rrd.graph_rrd(cp, "schedd", interval, m.groups()[1]) ]
    else:
        return [ jobview_rrd.graph_rrd(cp, "schedd", interval) ]


shadow_graph_re = re.compile(r'^/+shadow_graph/?([a-zA-Z]+)?/?([a-zA-Z.\-_@ 0-9]+)?/?$')
def shadow_graph(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png'),
               ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    path = environ.get('PATH_INFO', '')
    m = shadow_graph_re.match(path)
    interval = "daily"
    if m.groups()[0]: interval=m.groups()[0]

    if m.groups()[1]:
        return [ jobview_rrd.graph_rrd(cp, "schedd_shadows", interval, m.groups()[1]) ]
    else:
        return [ jobview_rrd.graph_rrd(cp, "schedd_shadows", interval) ]


schedd_io_graph_re = re.compile(r'^/+schedd_io_graph/?([a-zA-Z]+)?/?([a-zA-Z.\-_@ 0-9]+)?/?$')
def schedd_io_graph(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png'),
               ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)

    path = environ.get('PATH_INFO', '')
    m = schedd_io_graph_re.match(path)
    interval = "daily"
    if m.groups()[0]: interval=m.groups()[0]

    if m.groups()[1]:
        return [ jobview_rrd.graph_rrd(cp, "schedd_io", interval, m.groups()[1]) ]
    else:
        return [ jobview_rrd.graph_rrd(cp, "schedd_io", interval) ]


def index(environ, start_response):
    status = '200 OK' # HTTP Status
    headers = [('Content-type', 'text/html'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    
    tmpl = loader.load('index.html')
    
    site_name = cp.get("jobview", "site_name")

    return [tmpl.generate(site_name=site_name).render('html', doctype='html')]
    

def not_found(environ, start_response):
    status = '404 Not Found'
    headers = [('Content-type', 'text/html'),
              ('Cache-Control', 'max-age=60, public')]
    start_response(status, headers)
    return [ "Resource not found"]
    


# Add url's here for new pages
urls = [
    (re.compile(r'^$'), index),
    (re.compile(r'^jobs/?$'), jobs),
    (re.compile(r'^cluster/?$'), cluster),
    (re.compile(r'^jobs_graph/?'), jobs_graph),
    (re.compile(r'^cluster_graph/?'), cluster_graph),
    (re.compile(r'^schedd_jobs_graph/?'), schedd_jobs_graph),
    (re.compile(r'^schedd_rates_graph/?'), schedd_rates_graph),
    (re.compile(r'^schedd_io_graph/?'), schedd_io_graph),
    (re.compile(r'^shadow_graph/?'), shadow_graph),
]

def application(environ, start_response):
    check_initialized(environ)

    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = regex.match(path)
        if match:
            environ['jobview.url_args'] = match.groups()
            return callback(environ, start_response)
    return not_found(environ, start_response)

    #site_name = cp.get("jobview", "site_name")

    #total_slots, free_slots = get_cpu_slots(cp)
    #cpu_slots = {'total': total_slots, 'free': free_slots}

    #jobs, groups, schedd, user = summarize_jobs(cp)

    #tmpl = loader.load('index.html')

    #return [tmpl.generate(site_name=site_name, schedds=schedd, groups=groups, cpu_slots=cpu_slots, jobs=jobs).render('html', doctype='html')]

