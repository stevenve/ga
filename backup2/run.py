#! /usr/bin/env python

import subprocess
import sys
import random

dbNumber = int(sys.argv[1])

for j in range(20):
    for i in range(5):
        tmp = random.randint(1,100000)
        subprocess.call(['time','python','ga.py','-1',str(tmp),'20','20','0.9','0.1','0.9',str(dbNumber)])