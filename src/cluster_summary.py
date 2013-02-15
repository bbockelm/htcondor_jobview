
import sys
import ConfigParser

import htcondor
import classad

def get_cpu_slots(cp):
    coll = htcondor.Collector(cp.get("condor", "pool"))
    total_cpus, free = 0, 0
    for ad in coll.query(htcondor.AdTypes.Startd, 'True', ['Cpus','TotalCpus']):
        try:
            total_cpus += ad['Cpus']
        except AttributeError:
            pass
        try:
            free += ad['Cpus']
        except AttributeError:
            pass
    return total_cpus, free

if __name__ == '__main__':
    cp = ConfigParser.ConfigParser()
    cp.read(sys.argv[1])
    print get_cpu_slots(cp)

