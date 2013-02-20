
import re
import sys
import ConfigParser

import htcondor

def get_schedds(cp):
    coll = htcondor.Collector(cp.get("condor", "pool"))
    names = cp.get("condor", "exclude_schedds")
    names = re.split(",?\s*", names)
    schedds = coll.locateAll(htcondor.DaemonTypes.Schedd)
    return [i for i in schedds if (('Name' in i) and (i['Name'] not in names))]

def status_for_jobs(cp):
    coll = htcondor.Collector(cp.get("condor", "pool"))
    starters = coll.query(htcondor.AdTypes.Startd, 'True',
        ["GlobalJobId", "EnteredCurrentActivity", "MyCurrentTime", "Name"])
    job_corr = {}
    for starter in starters:
        if 'Name' not in starter: continue
        if 'GlobalJobId' not in starter: continue
        if 'EnteredCurrentActivity' not in starter: continue
        if 'MyCurrentTime' not in starter: continue
        job_corr[starter["GlobalJobId"]] = {'ActiveTime': (starter['MyCurrentTime'] - starter['EnteredCurrentActivity']),
            'Name': starter['Name']}
    return job_corr

def fix_dn(dn):
    parts = dn.split("/")
    while parts[-1] == "CN=limited proxy" or parts[-1] == "CN=proxy":
        parts.pop()
    return "/".join(parts)

def summarize_jobs(cp):
    jobs = []
    group_default_stats = {'jobs': 0, 'running': 0, 'pending': 0, 'held': 0, 'cpu_eff': 0, 'low_eff': 0, 'cpu': 0, 'wall': 0}
    jobs_tables = dict(group_default_stats)
    group_tables = {}
    schedd_tables = {}
    user_tables = {}

    job_corr = status_for_jobs(cp)

    for schedd_ad in get_schedds(cp):
        schedd = htcondor.Schedd(schedd_ad)
        for job in schedd.query('True', ["AccountingGroup", "JobStatus",
                "X509UserProxySubject", "Owner", "WallDuration", "x509UserProxyFirstFQAN",
                "GlobalJobId", "RemoteSysCpu", "RemoteUserCpu"]):
            if 'Owner' not in job: continue
            if 'JobStatus' not in job: continue
            if 'GlobalJobId' not in job: continue

            eff = -1
            cpu = -1
            wall = -1
            if ('RemoteSysCpu' in job) and ('RemoteUserCpu' in job) and \
                    (job['GlobalJobId'] in job_corr):
                cpu = job['RemoteSysCpu'] + job['RemoteUserCpu']
                wall = job_corr[job['GlobalJobId']]['ActiveTime']
                if wall:
                    eff = cpu / float(wall)
                else:
                    eff = 0

            status = job['JobStatus']

            agroup_name = '<none>'
            if 'AccountingGroup' in job:
                agroup_name = job['AccountingGroup']
                agroup_name = agroup_name.split(".")
                agroup_name = ".".join(agroup_name[:-1])
            agroup = group_tables.setdefault(agroup_name, dict(group_default_stats))

            schedd_name = job['GlobalJobId'].split("#")[0]
            schedd = schedd_tables.setdefault(schedd_name, dict(group_default_stats))

            user_name = job['Owner']

            dn = '<unknown>'
            if 'X509UserProxySubject' in job: dn = job['X509UserProxySubject']
            fqan = '<unknown>'
            if 'x509UserProxyFirstFQAN' in job: fqan = job['x509UserProxyFirstFQAN']
            dn = fix_dn(dn)

            user_group = str([user_name , agroup_name, dn, fqan])
            user = user_tables.setdefault(user_group, dict(group_default_stats))
            user['Owner'] = user_name
            user['AccountingGroup'] = agroup_name
            user['X509UserProxySubject'] = dn
            user['x509UserProxyFirstFQAN'] = fqan

            jobs_tables['jobs'] += 1
            agroup['jobs'] += 1
            schedd['jobs'] += 1
            user['jobs'] += 1
            if status == 1:
                jobs_tables['pending'] += 1
                agroup['pending'] += 1
                schedd['pending'] += 1
                user['pending'] += 1
            elif status == 2:
                jobs_tables['running'] += 1
                agroup['running'] += 1
                schedd['running'] += 1
                user['running'] += 1
            elif status == 5:
                jobs_tables['held'] += 1
                agroup['held'] += 1
                schedd['held'] += 1
                user['held'] += 1
            if eff >= 0 and eff < .1:
                jobs_tables['low_eff'] += 1
                agroup['low_eff'] += 1
                schedd['low_eff'] += 1
                user['low_eff'] += 1
            if cpu >= 0 and wall >= 0:
                jobs_tables['cpu'] += cpu
                jobs_tables['wall'] += cpu
                agroup['cpu'] += cpu
                agroup['wall'] += wall
                schedd['cpu'] += cpu
                schedd['wall'] += wall
                user['cpu'] += cpu
                user['wall'] += wall

    for table in [{'foo': jobs_tables}, group_tables, schedd_tables, user_tables]:
        for value in table.values():
            if ('wall' in value) and ('cpu' in value) and value['wall']:
                value['cpu_eff'] = value['cpu'] / float(value['wall'])

    return jobs_tables, group_tables, schedd_tables, user_tables

if __name__ == '__main__':
    cp = ConfigParser.ConfigParser()
    cp.read(sys.argv[1])
    print summarize_jobs(cp)

