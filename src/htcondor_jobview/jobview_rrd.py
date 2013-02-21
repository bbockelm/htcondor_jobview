
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
            "DS:JobsRequeue:DERIVE:360:0:U",
            "DS:JobsTimeToStart:DERIVE:360:0:U",
            "DS:TotalIdleJobs:DERIVE:360:0:U",
            "DS:JobsBadputTime:DERIVE:360:0:U",
            "DS:JobsExecuteTime:DERIVE:360:0:U",
            "DS:TotalRunningJobs:DERIVE:360:0:U",
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

def update_rrd(cp):

    for stats in htcondor_jobview.schedd_stats.get_schedd_stats(cp):

        path = get_rrd_name(cp, "schedd", stats['Name'])
        if not os.path.exists(path):
            create_rrd(cp, "schedd", stats['Name'])

        rrdtool.update(path, "N:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d:%d" % (\
            stats['JobsAccumPostExecuteTime'],
            stats['JobsAccumPreExecuteTime'],
            stats['TransferQueueNumWaitingToUpload'],
            stats['TransferQueueNumUploading'],
            stats['TransferQueueNumWaitingToDownload'],
            stats['TransferQueueNumDownloading'],
            stats['JobsStarted'],
            stats['JobsSubmitted'],
            stats['JobsCompleted'],
            stats['ShadowsStarted'],
            stats['JobsExited'] + stats['JobsExitedAndClaimClosing'],
            stats['JobsExitException'] + stats['JobsShouldHold'] + stats['JobsExecFailed'] + \
                stats['JobsShouldRequeue'] + stats['JobsKilled'] + stats['JobsNotStarted'],
            stats['JobsAccumTimeToStart'],
            stats['TotalIdleJobs'],
            stats['JobsAccumBadputTime'],
            stats['JobsAccumExecuteTime'],
            stats['TotalRunningJobs'],
            stats['JobsAccumTimeToStart'] / (stats['TotalIdleJobs']+1),
            stats['JobsAccumExecuteTime'] / (stats['TotalRunningJobs']+1),
            ))

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
            "DEF:shadows=%s:ShadowsStarted:AVERAGE" % path,
            "DEF:jobs_exited=%s:JobsExited:AVERAGE" % path,
            "DEF:jobs_requeued=%s:JobsRequeue:AVERAGE" % path,
            "LINE1:shadows#0000FF:Shadow Start Rate",
            "LINE2:jobs_exited#00FF00:Job Exit Rate",
            "LINE3:jobs_requeued#FF0000:Job Requeue Rate",
            "COMMENT:\\n",
            "COMMENT:                   avg   cur\\n",
            "COMMENT:Shadow Start Rate",
            "GPRINT:shadows:AVERAGE:%-2.1lf",
            "GPRINT:shadows:LAST:%-2.1lf\\n",
            "COMMENT:Job Exit Rate    ",
            "GPRINT:jobs_exited:AVERAGE:%-2.1lf",
            "GPRINT:jobs_exited:LAST:%-2.1lf\\n",
            "COMMENT:Job Requeue Rate ",
            "GPRINT:jobs_requeued:AVERAGE:%-2.1lf",
            "GPRINT:jobs_requeued:LAST:%-2.1lf\\n",
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
            "DEF:uploads=%s:JobsPreExecTime:AVERAGE" % path,
            "DEF:downloads=%s:JobsPostExecTime:AVERAGE" % path,
            "DEF:waiting_uploads=%s:WaitingToUpload:AVERAGE" % path,
            "DEF:waiting_downloads=%s:WaitingToDownload:AVERAGE" % path,
            "LINE1:uploads#0000FF:Uploads",
            "LINE2:downloads#00FF00:Downloads",
            "LINE3:waiting_uploads#FF0000:Queued Uploads",
            "LINE4:waiting_downloads#FF00FF:Queued Downloads",
            "COMMENT:\\n",
            "COMMENT:                    avg    cur\\n",
            "COMMENT:Uploads          ",
            "GPRINT:uploads:AVERAGE:%-2.1lf",
            "GPRINT:uploads:LAST:%-2.1lf\\n",
            "COMMENT:Downloads        ",
            "GPRINT:downloads:AVERAGE:%-2.1lf",
            "GPRINT:downloads:LAST:%-2.1lf\\n",
            "COMMENT:Queued Uploads   ",
            "GPRINT:waiting_uploads:AVERAGE:%-2.1lf",
            "GPRINT:waiting_uploads:LAST:%-2.1lf\\n",
            "COMMENT:Queued Downloads ",
            "GPRINT:waiting_downloads:AVERAGE:%-2.1lf",
            "GPRINT:waiting_downloads:LAST:%-2.1lf\\n",
            )


    elif plot == "jobs":
        path = get_rrd_name(cp, plot)
        if not os.path.exists(path):
            create_rrd(cp, "jobs")

        rrdtool.graph(pngpath,
            "--imgformat", "PNG",
            "--width", "400",
            "--start", "-1%s" % rrd_interval,
            "--vertical-label", "Jobs",
            "--lower-limit", "0",
            "DEF:running=%s:running:AVERAGE" % path,
            "DEF:pending=%s:pending:AVERAGE" % path,
            "LINE1:running#0000FF:Running",
            "LINE2:pending#00FF00:Pending",
            "COMMENT:%s" % cp.get("jobview", "site_name"),
            "COMMENT:\\n",
            "COMMENT:           max     avg      cur\\n",
            "COMMENT:Running ",
            "GPRINT:running:MAX:%-6.0lf",
            "GPRINT:running:AVERAGE:%-6.0lf",
            "GPRINT:running:LAST:%-6.0lf",
            "COMMENT:\\n",
            "COMMENT:Pending ",
            "GPRINT:pending:MAX:%-6.0lf",
            "GPRINT:pending:AVERAGE:%-6.0lf",
            "GPRINT:pending:LAST:%-6.0lf\\n",
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
    print graph_rrd(cp, "schedd_io", "hourly", "red.unl.edu")

