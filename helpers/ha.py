import sys, time, re, urllib2, json, psycopg2
import syslog
from base64 import b64decode

import helpers.errors

import inspect

def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno

class Ha:
    def __init__(self, state_handler, etcd, rt53, sns, sqs, hostname):
        self.state_handler = state_handler
        self.etcd = etcd
        self.rt53 = rt53
        self.sns = sns
        self.sqs = sqs

    def acquire_lock(self):
        return self.etcd.attempt_to_acquire_leader(self.state_handler.name)

    def update_lock(self):
        return self.etcd.update_leader(self.state_handler.name)

    def is_unlocked(self):
        return self.etcd.leader_unlocked()

    def has_lock(self):
        return self.etcd.am_i_leader(self.state_handler.name)

    def fetch_current_leader(self):
            return self.etcd.current_leader()

    def run_cycle(self):
        try:
            if self.state_handler.is_healthy():
                if self.is_unlocked():
                    if self.state_handler.is_healthiest_node(self.etcd.members()):
                        if self.acquire_lock():
                            if not self.state_handler.is_leader():
                                self.state_handler.promote()
                                # update DNS
                                self.rt53.update()
                                # publish message to SNS
                                sns_msg = "leader lock changed to %s" % (hostname)
                                self.sns.publish(sns_msg) 
                                # publish a SQS
                                self.sqs.send(hostname)                     
                                return "promoted self to leader by acquiring session lock"

                            return "acquired session lock as a leader"
                        else:
                            if self.state_handler.is_leader():
                                self.state_handler.demote(self.fetch_current_leader())
                                return "demoted self due after trying and failing to obtain lock"
                            else:
                                self.state_handler.follow_the_leader(self.fetch_current_leader())
                                return "following new leader after trying and failing to obtain lock"
                    else:
                        if self.state_handler.is_leader():
                            self.state_handler.demote(self.fetch_current_leader())
                            return "demoting self because i am not the healthiest node"
                        else:
                            self.state_handler.follow_the_leader(self.fetch_current_leader())
                            return "following a different leader because i am not the healthiest node"

                else:
                    if self.has_lock():
                        self.update_lock()

                        if not self.state_handler.is_leader():
                            self.state_handler.promote()
                            return "promoted self to leader because i had the session lock"
                        else:
                            return "no action.  i am the leader with the lock"
                    else:
                        syslog.syslog("does not have lock")
                        if self.state_handler.is_leader():
                            self.state_handler.demote(self.fetch_current_leader())
                            return "demoting self because i do not have the lock and i was a leader"
                        else:
                            self.state_handler.follow_the_leader(self.fetch_current_leader())
                            return "no action.  i am a secondary and i am following a leader"
            else:
                if not self.state_handler.is_running():
                    self.state_handler.start()
                    return "postgresql was stopped.  starting again."
                return "no action.  not healthy enough to do anything."
        except helpers.errors.CurrentLeaderError:
            syslog.syslog(syslog.LOG_ERR, "failed to fetch current leader from etcd")
        except psycopg2.OperationalError:
            syslog.syslog(syslog.LOG_ERR, "Error communicating with Postgresql.  Will try again.")
        except helpers.errors.HealthiestMemberError:
            syslog.syslog(syslog.LOG_ERR, "failed to determine healthiest member fromt etcd")

    def run(self):
        while True:
            self.run_cycle()
            time.sleep(10)
