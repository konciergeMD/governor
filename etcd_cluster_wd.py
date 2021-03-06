#!/usr/bin/env python

# makes sure etcd cluster is healthy

import subprocess, os, time, syslog

stop_cmd = [ '/bin/systemctl', 'stop', 'etcd' ]
start_cmd = [ '/bin/systemctl', 'start', 'etcd' ]


def restart(msg):
	syslog.syslog(msg)
	subprocess.call(stop_cmd)
	time.sleep(1)
	subprocess.call(start_cmd)

def check_record_ttl(ttl):
	# url: curl http://127.0.0.1:4001/v2/keys/service/batman/leader
	pass

try:
	cmd = [ '/bin/etcdctl', 'cluster-health' ]
	p = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	out, err = p.communicate()

	if len(out) == 0:
		err_msg = "etcd not running restarting..."
		restart(err_msg)
	else:
		lines = out.split(os.linesep)
		for l in lines:
			find = l.find('cluster')
			if find == 0:
				args = l.split(' ')
				if not args[2] == 'healthy':
					err_msg = "etcd cluster is not healthy restarting..."
					syslog.syslog(err_msg)
					restart(err_msg)

except Exception, e:
	err_msg = "Exception: %s occured running the test, ignoring..." % (str(e))
	syslog.syslog(err_msg)
	# err_msg = "genral exception, restarting..."
	# restart(err_msg)
