
import re
import sys
import ConfigParser

import htcondor

def get_schedd_stats(cp):
    coll = htcondor.Collector(cp.get("condor", "pool"))
    names = cp.get("condor", "exclude_schedds")
    names = re.split(",?\s*", names)
    schedds = coll.locateAll(htcondor.DaemonTypes.Schedd)
    return schedds

