
import sys
import htcondor
import classad

def get_cpu_slots(pool=None):
    if pool:
        coll = htcondor.Collector(pool)
    else:
        coll = htcondor.Collector()
    total_cpus, free = 0, 0
    for ad in coll.query(htcondor.AdTypes.Startd, 'True', ['Cpus','TotalCpus']):
        try:
            total_cpus += ad['TotalCpus']
        except AttributeError:
            pass
        try:
            free += ad['Cpus']
        except AttributeError:
            pass
    return total_cpus, free

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print get_cpu_slots(sys.argv[1])
    else:
        print get_cpu_slots()

