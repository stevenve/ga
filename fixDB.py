#! /usr/bin/env python

import pickle

fitnessDB = {}
iFitness = 0
iOdometry = 1
iRobotDistr = 2
iExploreTime = 3
iSignalTime = 4
iSignalCloseRange = 5
iSignalHasPriority = 6

def dumpDB():
    f = open('db','wb')
    pickle.dump(fitnessDB, f)
    f.close()
    
def loadDB():
    global fitnessDB
    try:
        f = open('db','rb')
        fitnessDB = pickle.load(f)
        f.close()
    except (EOFError, IOError):
        print 'No db found or it is empty'
        

loadDB()
print fitnessDB
tmpChrom = None
tmp = []
delList = []
for chrom in fitnessDB:
    if eval(chrom)[iRobotDistr][0] == 12:
        tmpChrom = eval(chrom)[:iRobotDistr+1]
        tmp.append(fitnessDB[chrom][0])
        delList.append(chrom)
for i in range(len(delList)):
    del fitnessDB[delList[i]]
fitnessDB[str(tmpChrom)] =  tmp
print fitnessDB
dumpDB()
