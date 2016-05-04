#!/usr/bin/env python

import subprocess, os

os.environ['PATH'] += os.pathsep + '/usr/sbin'
governor_start_cmd = [ '/bin/systemctl', 'start', 'governor' ]

def pip_checker():
    pid_file = "/pg_cluster/pgsql/9.4/data/postmaster.pid"
    try:
        f = open (pid_file, "r")
        pid_num = int(f.readline().rstrip())
        f.close()
        return pid_num
    except Exception, e:
        raise e

try:
    pid_num = pip_checker()
    print pid_num
    try:
        os.kill(pid_num, 0)
    except Exception as e:
        subprocess.call(governor_start_cmd)
except Exception, e:
    raise e
