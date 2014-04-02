#! /usr/bin/env python

import pickle

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
    if fitnessDB[chrom] > max:
        max = fitnessDB[chrom]
        maxChrom = chrom 
print 'F = ' + str(max) + ", chrom = " + str(maxChrom)