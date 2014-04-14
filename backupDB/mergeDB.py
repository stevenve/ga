#! /usr/bin/env python

import pickle
from copy import deepcopy

fitnessDB0 = {}
fitnessDB1 = {}
fitnessDB2 = {}
fitnessDB3 = {}
iFitness = 0
iOdometry = 1
iRobotDistr = 2
iExploreTime = 3
iSignalTime = 4
iSignalCloseRange = 5
iSignalHasPriority = 6

def dumpDB():
    f = open('db0','wb')
    pickle.dump(fitnessDB0, f)
    f.close()
    
def loadDB(nb, var):
    global fitnessDB0
    global fitnessDB1
    global fitnessDB2
    global fitnessDB3
    try:
        f = open('db'+str(nb),'rb')
        var = pickle.load(f)
        f.close()
    except (EOFError, IOError):
        print 'No db found or it is empty'
    return var
        
fitnessDB0 = loadDB(0,fitnessDB0)
print fitnessDB0
fitnessDB1 = loadDB(1,fitnessDB1)
fitnessDB2 = loadDB(2,fitnessDB2)
fitnessDB3 = loadDB(3,fitnessDB3)

def merge(db1, db2):
    for chrom in db1:
        if chrom in db2:
            db1[chrom] = db1[chrom]+db2[chrom]
    for chrom in db2:
        if chrom not in db1:
            db1[chrom] = db2[chrom]

merge(fitnessDB0, fitnessDB1)
merge(fitnessDB0, fitnessDB2)
merge(fitnessDB0, fitnessDB3)
dumpDB()
