#! /usr/bin/env python

import pickle
import numpy as np

fitnessDB = {}
try:
    f = open('db','rb')
    fitnessDB = pickle.load(f)
    f.close()
except (EOFError, IOError):
    print 'No db found or it is empty'
    
max = 0 
maxChrom = None
for chrom in fitnessDB.keys():
    if np.mean(fitnessDB[chrom]) > max:
        max = np.mean(fitnessDB[chrom])
        maxChrom = chrom 
print 'F = ' + str(max) + ", chrom = " + str(maxChrom[1:])