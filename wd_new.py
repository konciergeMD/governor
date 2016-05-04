#!/usr/bin/env python

import subprocess, os

governor_start_cmd = [ '/bin/systemctl', 'start', 'governor' ]

try:
    pid_file = "/pg_cluster/pgsql/9.4/data/postmaster.pid"
    f = open(pid_file, "r")
    pid_num = int(f.readline().rstrip())
    f.close()
    print pid_num
    os.kill(pid_num, 0)
except Exception, e:
    subprocess.call(governor_start_cmd)
