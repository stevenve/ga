#! /usr/bin/env python

import pickle
import operator
import numpy as np
import sys
from copy import deepcopy

dbNumber = int(sys.argv[1])

fitnessDB = {}
try:
    f = open('db'+str(dbNumber),'rb')
    fitnessDB = pickle.load(f)
    f.close()
except (EOFError, IOError):
    print 'No db found or it is empty'
    
fitnessDB2 = deepcopy(fitnessDB)
    
for j in fitnessDB:
    fitnessDB[j] = np.mean(fitnessDB[j])
    
sortedz = sorted(fitnessDB.iteritems(), key=operator.itemgetter(1))

for i in range(len(sortedz)):
    chrom = eval(sortedz[i][0])
    fitness = sortedz[i][1]
    print 'F = ' + str(round(np.mean(fitness),1)) + ", chrom = " + str(chrom[1:]) + ", Fs = " + str(fitnessDB2[str(chrom)])