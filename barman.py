#!/usr/bin/env python

import sys, yaml, time, subprocess, os, shutil, json

from helpers.sqs import Sqs
from helpers.sns import Sns

f = open(sys.argv[1], "r")
config = yaml.load(f.read())
f.close()

sns = Sns(config["sns"])
sqs = Sqs(config["sqs"])

m = sqs.read()

print m

m_obj = json.load(m.get_body())
print m_obj