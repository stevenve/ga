#! /usr/bin/env python

import pickle
import operator

fitnessDB = {}
try:
    f = open('db','rb')
    fitnessDB = pickle.load(f)
    f.close()
except (EOFError, IOError):
    print 'No db found or it is empty'
    
sorted = sorted(fitnessDB.iteritems(), key=operator.itemgetter(1))

for i in range(len(sorted)):
    chrom = eval(sorted[i][0])
    fitness = sorted[i][1]
    print 'F = ' + str(fitness) + ", chrom = " + str(chrom)