#! /usr/bin/env python

import subprocess
import sys
import random

dbNumber = int(sys.argv[1])

random.seed(dbNumber)
for j in range(20):
    tmp = random.randint(1,100000)
    for i in range(5):
        subprocess.call(['time','python','gaRemote.py','-1',str(tmp),'20','100','0.9','0.2','0.9',str(dbNumber)])
