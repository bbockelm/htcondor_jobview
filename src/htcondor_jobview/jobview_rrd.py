
import os
import sys
import tempfile
import ConfigParser

import rrdtool

import htcondor_jobview.jobs
import htcondor_jobview.cluster_summary
import htcondor_jobview.schedd_stats

def get_rrd_name(cp, plot, subplot=None):
    if subplot:
        return os.path.join(cp.get("jobview", "db_directory"), "%s.%s.rrd" % (plot, subplot))
    else:
        return os.path.join(cp.get("jobview", "db_directory"), "%s.rrd" % plot)

def create_rrd(cp, plot, subplot = None):
    path = get_rrd_name(cp, plot, subplot)
    if plot == "jobs":
        rrdtool.create(path,
            "--step", "180",
            "DS:running:GAUGE:360:U:U",
            "DS:pending:GAUGE:360:U:U",
            "RRA:AVERAGE:0.5:1:1000",
            "RRA:MIN:0.5:20:8760",
            "RRA:MAX:0.5:20:8760",
            "RRA:AVERAGE:0.5:20:8760",
            )
    elif plot == "schedd":
        rrdtool.create(path,
            "--step", "180",
            "DS:JobsPreExecTime:DERIVE:360:0:U",
            "DS:JobsPostExecTime:DERIVE:360:0:U",
            "DS:WaitingToUpload:GAUGE:360:0:U",
            "DS:UploadNum:GAUGE:360:0:U",
            "DS:WaitingToDownload:GAUGE:360:0:U",
            "DS:NumDownloading:GAUGE:360:0:U",
            "DS:JobsStarted:DERIVE:360:0:U",
            "DS:JobsSubmitted:DERIVE:360:0:U",
            "DS:JobsCompleted:DERIVE:360:0:U",
            "DS:ShadowsStarted:DERIVE:360:0:U",
            "DS:JobsExited:DERIVE:360:0:U",
            "DS:JobsHeld:DERIVE:360:0:U",
            "DS:JobsRequeue:DERIVE:360:0:U",
            "DS:JobsTimeToStart:DERIVE:360:0:U",
            "DS:TotalIdleJobs:GAUGE:360:0:U",
            "DS:JobsBadputTime:DERIVE:360:0:U",
            "DS:JobsExecuteTime:DERIVE:360:0:U",
            "DS:TotalRunningJobs:GAUGE:360:0:U",
            "DS:AvgJobQueueTime:GAUGE:360:0:U",
            "DS:AvgJobRunTime:GAUGE:360:0:U",
            "RRA:AVERAGE:0.5:1:1000",
            "RRA:MIN:0.5:20:8760",
            "RRA:MAX:0.5:20:8760",
            "RRA:AVERAGE:0.5:20:8760",
            )
    else:
        rrdtool.create(path,
            "--step", "180",
            "DS:total:GAUGE:360:U:U",
            "DS:free:GAUGE:360:U:U",
            "RRA:AVERAGE:0.5:1:1000",
            "RRA:MIN:0.5:20:8760",
            "RRA:MAX:0.5:20:8760",
            "RRA:AVERAGE:0.5:20:8760",
            )

def make_stats_list(stats):
    stats_list = []
    stats_list.append(stats['JobsAccumPostExecuteTime'])
    stats_list.append(stats['JobsAccumPreExecuteTime'])
    stats_list.append(stats['TransferQueueNumWaitingToUpload'])
    stats_list.append(stats['TransferQueueNumUploading'])
    stats_list.append(stats['TransferQueueNumWaitingToDownload'])
    stats_list.append(stats['TransferQueueNumDownloading'])
    stats_list.append(stats['JobsStarted'])
    stats_list.append(stats['JobsSubmitted'])
    stats_list.append(stats['JobsCompleted'])
    stats_list.append(stats['ShadowsStarted'])
    stats_list.append(stats['JobsExited'])
    stats_list.append(stats['JobsShouldHold'])
    stats_list.append(stats['JobsExitException'] + stats['JobsExecFailed'] + \
        stats['JobsShouldRequeue'] + stats['JobsKilled'] + stats['JobsNotStarted'])
    stats_list.append(stats['JobsAccumTimeToStart'])
    stats_list.append(stats['TotalIdleJobs'])
    stats_list.append(stats['JobsAccumBadputTime'])
    stats_list.append(stats['JobsAccumExecuteTime'])
    stats_list.append(stats['TotalRunningJobs'])
    stats_list.append(stats['JobsAccumTimeToStart'] / (stats['TotalIdleJobs']+1))
    stats_list.append(stats['JobsAccumExecuteTime'] / (stats['TotalRunningJobs']+1))
    return stats_list

def update_rrd(cp):

    totals = []
    for stats in htcondor_jobview.schedd_stats.get_schedd_stats(cp):

        path = get_rrd_name(cp, "schedd", stats['Name'])
        if not os.path.exists(path):
            create_rrd(cp, "schedd", stats['Name'])

        stats_list = make_stats_list(stats)
        rrdtool.update(path, ("N:" + ":".join(["%d"]*len(stats_list))) % tuple(stats_list))
        if not totals:
            totals = stats_list
        else:
            for i in range(len(stats_list)): totals[i] += stats_list[i]

    if totals:
        path = get_rrd_name(cp, "schedd")
        if not os.path.exists(path):
            create_rrd(cp, "schedd")
        rrdtool.update(path, ("N:" + ":".join(["%d"]*len(totals))) % tuple(totals))

    jobs_tables, group_tables, schedd_tables, user_tables = \
        htcondor_jobview.jobs.summarize_jobs(cp)

    path = get_rrd_name(cp, "jobs")
    if not os.path.exists(path):
        create_rrd(cp, "jobs")

    rrdtool.update(path, "N:%d:%d" % (jobs_tables['running'], jobs_tables['pending']))

    total, free = htcondor_jobview.cluster_summary.get_cpu_slots(cp)
    path = get_rrd_name(cp, "cluster")

    path = get_rrd_name(cp, "cluster")
    if not os.path.exists(path):
        create_rrd(cp, "cluster")

    rrdtool.update(path, "N:%d:%d" % (total, free))

def graph_rrd(cp, plot, interval, subplot = None):
    if interval == "hourly":
        rrd_interval = "h"
    elif interval == "daily":
        rrd_interval = "d"
    elif interval == "weekly":
        rrd_interval = "w"
    elif interval == "monthly":
        rrd_interval = "m"
    elif interval == "yearly":
        rrd_interval = "y"
    else:
        raise ValueError("Unknown interval: %s" % interval)

    fd, pngpath = tempfile.mkstemp(".png")
    if plot == "schedd_shadows":
        path = get_rrd_name(cp, "schedd", subplot)
        if not os.path.exists(path):
            create_rrd(cp, "schedd", subplot)

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Jobs / s",
            "--lower-limit", "0",
            "--title", "%s Shadow Statistics" % cp.get("jobview", "site_name"),
            "DEF:shadows=%s:ShadowsStarted:AVERAGE" % path,
            "DEF:jobs_exited=%s:JobsExited:AVERAGE" % path,
            "DEF:jobs_requeued=%s:JobsRequeue:AVERAGE" % path,
            "DEF:jobs_hold=%s:JobsHeld:AVERAGE" % path,
            "LINE1:shadows#0000FF:Shadow Start",
            "LINE2:jobs_exited#00FF00:Job Exit",
            "LINE3:jobs_requeued#FF0000:Job Requeue",
            "LINE3:jobs_hold#FF00FF:Job Hold",
            "COMMENT:\\n",
            "COMMENT:                   max   avg   cur\\n",
            "COMMENT:Shadow Start Rate",
            "GPRINT:shadows:MAX:%-2.1lf",
            "GPRINT:shadows:AVERAGE:%-2.1lf",
            "GPRINT:shadows:LAST:%-2.1lf\\n",
            "COMMENT:Job Exit Rate    ",
            "GPRINT:jobs_exited:MAX:%-2.1lf",
            "GPRINT:jobs_exited:AVERAGE:%-2.1lf",
            "GPRINT:jobs_exited:LAST:%-2.1lf\\n",
            "COMMENT:Job Requeue Rate ",
            "GPRINT:jobs_requeued:MAX:%-2.1lf",
            "GPRINT:jobs_requeued:AVERAGE:%-2.1lf",
            "GPRINT:jobs_requeued:LAST:%-2.1lf\\n",
            "COMMENT:Job Hold Rate    ",
            "GPRINT:jobs_hold:MAX:%-2.1lf",
            "GPRINT:jobs_hold:AVERAGE:%-2.1lf",
            "GPRINT:jobs_hold:LAST:%-2.1lf\\n",
            )

    elif plot == "schedd_io":
        path = get_rrd_name(cp, "schedd", subplot)
        if not os.path.exists(path):
            create_rrd(cp, "schedd", subplot)

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Avg Transfers",
            "--lower-limit", "0",
            "--title", "%s Scheduler IO" % cp.get("jobview", "site_name"),
            "DEF:uploads=%s:JobsPreExecTime:AVERAGE" % path,
            "DEF:downloads=%s:JobsPostExecTime:AVERAGE" % path,
            "DEF:waiting_uploads=%s:WaitingToUpload:AVERAGE" % path,
            "DEF:waiting_downloads=%s:WaitingToDownload:AVERAGE" % path,
            "LINE1:uploads#0000FF:Uploads",
            "LINE2:downloads#00FF00:Downloads",
            "LINE3:waiting_uploads#FF0000:Queued Uploads",
            "LINE4:waiting_downloads#FF00FF:Queued Downloads",
            "COMMENT:\\n",
            "COMMENT:                    max  avg  cur\\n",
            "COMMENT:Uploads          ",
            "GPRINT:uploads:MAX:%-2.1lf",
            "GPRINT:uploads:AVERAGE:%-2.1lf",
            "GPRINT:uploads:LAST:%-2.1lf\\n",
            "COMMENT:Downloads        ",
            "GPRINT:downloads:MAX:%-2.1lf",
            "GPRINT:downloads:AVERAGE:%-2.1lf",
            "GPRINT:downloads:LAST:%-2.1lf\\n",
            "COMMENT:Queued Uploads   ",
            "GPRINT:waiting_uploads:MAX:%-2.1lf",
            "GPRINT:waiting_uploads:AVERAGE:%-2.1lf",
            "GPRINT:waiting_uploads:LAST:%-2.1lf\\n",
            "COMMENT:Queued Downloads ",
            "GPRINT:waiting_downloads:AVERAGE:%-2.1lf",
            "GPRINT:waiting_downloads:LAST:%-2.1lf\\n",
            )

    elif plot == "schedd_rates":
        path = get_rrd_name(cp, "schedd", subplot)
        if not os.path.exists(path):
            create_rrd(cp, "schedd", subplot)

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Jobs / s",
            "--lower-limit", "0",
            "--title", "%s Job Rates" % cp.get("jobview", "site_name"),
            "DEF:started=%s:JobsStarted:AVERAGE" % path,
            "DEF:submitted=%s:JobsSubmitted:AVERAGE" % path,
            "DEF:completed=%s:JobsCompleted:AVERAGE" % path,
            "LINE1:started#0000FF:Started",
            "LINE2:submitted#00FF00:Submitted",
            "LINE3:completed#FF0000:Completed",
            "COMMENT:\\n",
            "COMMENT:             max  avg  cur\\n",
            "COMMENT:Started   ",
            "GPRINT:started:MAX:%-2.1lf",
            "GPRINT:started:AVERAGE:%-2.1lf",
            "GPRINT:started:LAST:%-2.1lf\\n",
            "COMMENT:Submitted ",
            "GPRINT:submitted:MAX:%-2.1lf",
            "GPRINT:submitted:AVERAGE:%-2.1lf",
            "GPRINT:submitted:LAST:%-2.1lf\\n",
            "COMMENT:Completed ",
            "GPRINT:completed:MAX:%-2.1lf",
            "GPRINT:completed:AVERAGE:%-2.1lf",
            "GPRINT:completed:LAST:%-2.1lf\\n",
            )

    elif plot == "schedd":
        path = get_rrd_name(cp, "schedd", subplot)
        if not os.path.exists(path):
            create_rrd(cp, "schedd", subplot)

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Jobs / s",
            "--lower-limit", "0",
            "--title", "%s Job Rates" % cp.get("jobview", "site_name"),
            "DEF:running=%s:JobsExecuteTime:AVERAGE" % path,
            "DEF:pending=%s:JobsTimeToStart:AVERAGE" % path,
            "DEF:badput=%s:JobsBadputTime:AVERAGE" % path,
            "LINE1:running#0000FF:Running",
            "LINE2:pending#00FF00:Pending",
            "LINE3:badput#FF0000:Badput",
            "COMMENT:\\n",
            "COMMENT:             max  avg  cur\\n",
            "COMMENT:Running   ",
            "GPRINT:running:MAX:%-2.1lf",
            "GPRINT:running:AVERAGE:%-2.1lf",
            "GPRINT:running:LAST:%-2.1lf\\n",
            "COMMENT:Pending   ",
            "GPRINT:pending:MAX:%-2.1lf",
            "GPRINT:pending:AVERAGE:%-2.1lf",
            "GPRINT:pending:LAST:%-2.1lf\\n",
            "COMMENT:Badput    ",
            "GPRINT:badput:MAX:%-2.1lf",
            "GPRINT:badput:AVERAGE:%-2.1lf",
            "GPRINT:badput:LAST:%-2.1lf\\n",
            )


    elif plot == "jobs":
        path = get_rrd_name(cp, plot)
        if not os.path.exists(path):
            create_rrd(cp, "jobs")

        schedd_path = get_rrd_name(cp, "schedd")
        if not os.path.exists(schedd_path):
            create_rrd(cp, "schedd")

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Jobs",
            "--lower-limit", "0",
            "--title", "%s Job Counts" % cp.get("jobview", "site_name"),
            "DEF:running=%s:running:AVERAGE" % path,
            "DEF:pending=%s:pending:AVERAGE" % path,
            "DEF:badput=%s:JobsBadputTime:AVERAGE" % schedd_path,
            "LINE1:running#0000FF:Running",
            "LINE2:pending#00FF00:Pending",
            "LINE3:pending#FF0000:Pending",
            "COMMENT:%s" % cp.get("jobview", "site_name"),
            "COMMENT:\\n",
            "COMMENT:            max     avg     cur\\n",
            "COMMENT:Running ",
            "GPRINT:running:MAX:%-6.0lf",
            "GPRINT:running:AVERAGE:%-6.0lf",
            "GPRINT:running:LAST:%-6.0lf",
            "COMMENT:\\n",
            "COMMENT:Pending ",
            "GPRINT:pending:MAX:%-6.0lf",
            "GPRINT:pending:AVERAGE:%-6.0lf",
            "GPRINT:pending:LAST:%-6.0lf\\n",
            "COMMENT:Badput  ",
            "GPRINT:badput:MAX:%-6.0lf",
            "GPRINT:badput:AVERAGE:%-6.0lf",
            "GPRINT:badput:LAST:%-6.0lf\\n",
            )

    elif plot == "cluster":
        path = get_rrd_name(cp, plot)
        if not os.path.exists(path):
            create_rrd(cp, "cluster")

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Cores",
            "--lower-limit", "0",
            "--title", "%s Pool" % cp.get("jobview", "site_name"),
            "DEF:total=%s:total:AVERAGE" % path,
            "DEF:free=%s:free:AVERAGE" % path,
            "LINE1:total#0000FF:Total",
            "LINE2:free#00FF00:Free",
            "COMMENT:%s" % cp.get("jobview", "site_name"),
            "COMMENT:\\n",
            "COMMENT:         max     avg      cur\\n",
            "COMMENT:Total ",
            "GPRINT:total:MAX:%-6.0lf",
            "GPRINT:total:AVERAGE:%-6.0lf",
            "GPRINT:total:LAST:%-6.0lf",
            "COMMENT:\\n",
            "COMMENT:Free   ",
            "GPRINT:free:MAX:%-6.0lf",
            "GPRINT:free:AVERAGE:%-6.0lf",
            "GPRINT:free:LAST:%-6.0lf\\n",
            )

    return os.fdopen(fd).read()

if __name__ == '__main__':
    cp = ConfigParser.ConfigParser()
    cp.read(sys.argv[1])
    update_rrd(cp)
    print graph_rrd(cp, "schedd_io", "hourly")

