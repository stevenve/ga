#! /usr/bin/env python

# usage: ga.py envSeed gaSeed nbChromosomes nbGenerations selectionRate mutationProb crossProb dbNumber

# Implementation details:
#    - if envSeed == -1, then random envSeed
#    - Selection process should always select an even number of parents
#    - Relative fitness scaling uses scaling factor: 2*max - min. This assures that as fitness spread becomes smaller, scaling becomes more important. (paper)

# Notes:
#    - Mutation for the robot numbers should just generate a new robot distribution. Mutating the first or second number, 
#    would always automatically result in also mutating the third number when the total number of robots is fixed, which is unfair.
#    Adding 1 randomly as a mutation would be a too little mutation. Mutating larger numbers results in a completely new gene anyway.
#    Using an inversion mutation would also not make sense, because depending on the initial population, not all the search space can be searched.
#    Mutation should keep 1 robot number the same and then mutate the other two in some way.

# Use multiple fitnesses, use deviation to determine how many fitness before stopping to calculate fitness

import random
import sys
import math
from copy import deepcopy
from lxml import etree
from io import StringIO, BytesIO
import pickle
import subprocess
import os
import csv
import atexit
import numpy as np
import time
import multiprocessing as mp


fitnessDB = {}
envSeed = int(sys.argv[1])
gaSeed = int(sys.argv[2])
nbChromosomes = int(sys.argv[3])
nbGenerations = int(sys.argv[4])
selectionRate = float(sys.argv[5]) # If 1, no elitism
mutationProb =  float(sys.argv[6]) # 0.05
crossProb = float(sys.argv[7]) # 0.95
dbNumber = int(sys.argv[8]) # 0

if envSeed == -1:
    envRandom = random.Random(random.randint(1,100000))
else:
    envRandom = random.Random(envSeed)
    
if gaSeed == -1:
    gaSeed = random.randint(1,100000)

# Actual parameters
nbFitnessValues = 4
# Experiment
random_seed = envRandom.randint(1, 100000) # 11
#parameters
useOdometry = 'false'
#exploreTime = 300
#signalTime = 2000
dropTime = 1
pickupTime = 1
#signalCloseRange = 50
signalDistance = 500000
obstacleAvoidanceDistance = 50
avoidanceFactor = 3
# Entity
totalNbRobots = 12
# Foraging
radius = 0.1
nestSize = 2
nbFoodPatches = 1
nbFoodItems = 50
renewalRate = 1
foodPatchSize = 2
patchType = 'patched'
output = '/home/stevenve/ARGOS3/argos3-projects/problem/results/ga'+str(dbNumber)+'.csv'
outputParallel = '/home/stevenve/tmp2/ga'

nbParameters = 7

iStart = 3
iEnd = 6
# Names for chromosome indices, making the code more readable
iFitness = 0
#iSeed = 11
iOdometry = 1
iRobotDistr = 2
iExploreTime = 3
iSignalTime = 4
iSignalCloseRange = 5
iSignalHasPriority = 6

iSignalDistance = 7
iObstacleAvoidanceDistance = 8
iAvoidanceFactor = 9


iTotalNbRobots = 10
iDropTime = 11
iPickupTime = 12
iRadius = 13
iNestSize = 14
iNbFoodPatches = 15
iNbFoodItems = 16
iRenewalRate = 17
iFoodPatchSize = 18
iPatchType = 19



#################################### FITNESS ####################################
def dumpDB():
    f = open('db'+str(dbNumber),'wb')
    pickle.dump(fitnessDB, f)
    f.close()
atexit.register(dumpDB)

def loadDB():
    global fitnessDB
    try:
        f = open('db'+str(dbNumber),'rb')
        fitnessDB = pickle.load(f)
        f.close()
    except (EOFError, IOError):
        print 'No db found or it is empty'

def calculateFakeFitness(chroms): 
    for i in range(len(chroms)):
        if(chroms[i][iFitness] == -1):
            chroms[i][iFitness] = chroms[i][iRobotDistr][0]/6.0 + chroms[i][iRobotDistr][1]/6.0
            if(chroms[i][iRobotDistr][0] == 6 and chroms[i][iRobotDistr][1] == 6):
                chroms[i][iFitness] = 5.0
                
def setupXML(chrom):
    xml = '/home/stevenve/ARGOS3/argos3-projects/problem/xml/ga.argos'
    tree = etree.parse(xml)
    root = tree.getroot()
    experiment = root.find('framework').find('experiment')
    parameters = root.find('controllers').find('footbot_combined_novis_controller').find('params').find('parameters')
    #entity = root.find('arena').find('distribute').find('entity')
    foraging = root.find('loop_functions').find('foraging')
    
    experiment.set('random_seed',str(envRandom.randint(1, 100000)))
    
    parameters.set('useOdometry',str(chrom[iOdometry]))
    parameters.set('exploreTime',str(chrom[iExploreTime]*100))
    parameters.set('signalTime',str(chrom[iSignalTime]*1000))
    parameters.set('signalHasPriority',str(chrom[iSignalHasPriority]))
    parameters.set('signalCloseRange',str(chrom[iSignalCloseRange]*10))
    parameters.set('dropTime',str(dropTime))
    parameters.set('pickupTime',str(pickupTime))
    parameters.set('signalDistance',str(signalDistance))
    parameters.set('obstacleAvoidanceDistance',str(obstacleAvoidanceDistance))
    parameters.set('avoidanceFactor',str(avoidanceFactor))
    
    #entity.set('quantity',str(totalNbRobots))
    foraging.set('nbRobots',str(totalNbRobots))
    
    foraging.set('radius',str(radius))
    foraging.set('nestSize',str(nestSize))
    foraging.set('nbFoodPatches',str(nbFoodPatches))
    foraging.set('nbFoodItems',str(nbFoodItems))
    foraging.set('renewalRate',str(renewalRate))
    foraging.set('foodPatchSize',str(foodPatchSize))
    foraging.set('type',patchType)
    foraging.set('nbSolitary',str(chrom[iRobotDistr][0]))
    foraging.set('nbRecruiter',str(chrom[iRobotDistr][1]))
    foraging.set('nbRecruitee',str(chrom[iRobotDistr][2]))
    foraging.set('output',output)
    etree.tostring(root, pretty_print=True)
    f = open(xml, 'w')
    f.write(etree.tostring(root, pretty_print=True))
    f.close()
    
    print 'Executing experiment with nbSolitary=' + str(chrom[iRobotDistr][0]) + ', nbRecruiter='+str(chrom[iRobotDistr][1])+', nbRecruitee='+str(chrom[iRobotDistr][2])
    
def lookupFitness(chrom):
    tmp = deepcopy(chrom)
    tmp[iFitness] = -1
    tmp = str(tmp)
    if tmp in fitnessDB:
        return fitnessDB[tmp]
    else:
        return -1
    
def executeExperiment():
    start = time.time()
    os.chdir('/home/stevenve/ARGOS3')
    bla = subprocess.Popen(['time','argos3','-c','argos3-projects/problem/xml/ga.argos'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]
    os.chdir('/home/stevenve/eclipseworkspace/GA-thesis')
    print "Experiment finished after " + str(round(time.time()-start,2)) + " seconds."
    
def getFitnessFromFile():
    with open(output, 'rb') as f:
        content = f.readlines()
        ll = content[len(content)-1]
        tmp = ll.rstrip().split(',')
        return int(tmp[1]) + int(tmp[2]) + int(tmp[3])

def setupXMLParallel(chrom, i, j):
    xml = '/home/stevenve/gaworkspace/ga/ga.argos'
    xml2 = '/home/stevenve/tmp2/ga' + str(i) + '_' + str(j) + '.argos'
    tree = etree.parse(xml)
    root = tree.getroot()
    experiment = root.find('framework').find('experiment')
    parameters = root.find('controllers').find('footbot_combined_novis_controller').find('params').find('parameters')
    #entity = root.find('arena').find('distribute').find('entity')
    foraging = root.find('loop_functions').find('foraging')
    
    experiment.set('random_seed',str(envRandom.randint(1, 100000)))
    experiment.set('length', str(5000))
    
    parameters.set('useOdometry',str(chrom[iOdometry]))
    parameters.set('exploreTime',str(chrom[iExploreTime]*100))
    parameters.set('signalTime',str(chrom[iSignalTime]*1000))
    parameters.set('signalHasPriority',str(chrom[iSignalHasPriority]))
    parameters.set('signalCloseRange',str(chrom[iSignalCloseRange]*10))
    parameters.set('dropTime',str(dropTime))
    parameters.set('pickupTime',str(pickupTime))
    parameters.set('signalDistance',str(signalDistance))
    parameters.set('obstacleAvoidanceDistance',str(obstacleAvoidanceDistance))
    parameters.set('avoidanceFactor',str(avoidanceFactor))
    
    #entity.set('quantity',str(totalNbRobots))
    foraging.set('nbRobots',str(totalNbRobots))
    
    foraging.set('radius',str(radius))
    foraging.set('nestSize',str(nestSize))
    foraging.set('nbFoodPatches',str(nbFoodPatches))
    foraging.set('nbFoodItems',str(nbFoodItems))
    foraging.set('renewalRate',str(renewalRate))
    foraging.set('foodPatchSize',str(foodPatchSize))
    foraging.set('type',patchType)
    foraging.set('nbSolitary',str(chrom[iRobotDistr][0]))
    foraging.set('nbRecruiter',str(chrom[iRobotDistr][1]))
    foraging.set('nbRecruitee',str(chrom[iRobotDistr][2]))
    foraging.set('output',output)
    etree.tostring(root, pretty_print=True)
    f = open(xml2, 'w')
    f.write(etree.tostring(root, pretty_print=True))
    f.close()
    
    print 'Executing experiment with nbSolitary=' + str(chrom[iRobotDistr][0]) + ', nbRecruiter='+str(chrom[iRobotDistr][1])+', nbRecruitee='+str(chrom[iRobotDistr][2])

def getFitnessFromFileParallel(i, j):
    with open(outputParallel + str(i) + '_' + str(j) + '.argos', 'rb') as f:
        content = f.readlines()
        ll = content[len(content)-1]
        tmp = ll.rstrip().split(',')
        return int(tmp[1]) + int(tmp[2]) + int(tmp[3])
    
def executeExperimentParallel(i, j):
    start = time.time()
    os.chdir('/home/stevenve/argos/argos3/argos3-projects')
    bla = subprocess.Popen(['time','argos3','-c',outputParallel + str(i) + '_' + str(j) + '.argos'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]
    os.chdir('/home/stevenve/gaworkspace/ga')
    print "Experiment finished after " + str(round(time.time()-start,2)) + " seconds."
    
def doExperiment(args):
    setupXMLParallel(args[2], args[0], args[1])
    executeExperimentParallel(args[0], args[1])
    return getFitnessFromFileParallel(args[0], args[1])
    
def calculateRealFitnessParallel(chroms): # DON'T RECALCULATE IF DONE BEFORE
    global fitnessDB
    global pool
    done = False

    while(not done):
        done = True
        pool = mp.Pool(processes=20)
        args = []
        results = []
        for i in range(len(chroms)):
            if(chroms[i][iRobotDistr][0] == 12):
                chr = chroms[i][0:iRobotDistr+1]
            else:
                chr = chroms[i]
            fit = lookupFitness(chr)
            if(fit == -1 or len(fit)<nbFitnessValues):
                for j in range(nbFitnessValues - len(fit)):
                    done = False
                    print 'Adding experiment to experiment pool..'
                    args.append([i,j,chr])
            else:
                chroms[i][iFitness] = np.mean(fit)
                print 'Chrom = ' + str(chroms[i][1:]) + ', fitness = ' + str(chroms[i][iFitness])
        print 'Executing experiments...'
        results = pool.map(doExperiment, args)
        pool.close()
        pool.join()
        for x in range(len(results)):
            tmp = deepcopy(args[x][2])
            tmp[iFitness] = -1
            fitnessDB[str(tmp)] = fitnessDB[str(tmp)] + [results[x]]
            dumpDB()
   

                
def calculateRealFitness(chroms): # DON'T RECALCULATE IF DONE BEFORE
    global fitnessDB
    for i in range(len(chroms)):
        if(chroms[i][iRobotDistr][0] == 12):
            chr = chroms[i][0:iRobotDistr+1]
        else:
            chr = chroms[i]
        # See if fitness has been calculated sufficiently before
        fit = lookupFitness(chr)
        while(fit == -1 or len(fit)<nbFitnessValues):
            if fit == -1:
                print "Looking up fitness in DB, nothing found..."
                setupXML(chroms[i])
                executeExperiment()
                fitness = getFitnessFromFile()
                chroms[i][iFitness] = fitness
                # Store fitness for later reference
                tmp = deepcopy(chr)
                tmp[iFitness] = -1
                fitnessDB[str(tmp)] = [chroms[i][iFitness]]
                dumpDB()
            elif len(fit) < nbFitnessValues: # add the fitness to fitness list
                print "Looking up fitness in DB, found:" + str(fit) + " with mean " + str(np.mean(fit))
                setupXML(chroms[i])
                executeExperiment()
                fitness = getFitnessFromFile()
                chroms[i][iFitness] = fitness
                # add the fitness to fitness list
                tmp = deepcopy(chr)
                tmp[iFitness] = -1
                fitnessDB[str(tmp)] = fitnessDB[str(tmp)] + [chroms[i][iFitness]]
                dumpDB()
                chroms[i][iFitness] = np.mean(fitnessDB[str(tmp)])
            else:
                #print 'DB: chrom = ' + str(chroms[i][1]) + ', fitness = ' + str(fit)
                chroms[i][iFitness] = np.mean(fit)
            fit = lookupFitness(chr)
        chroms[i][iFitness] = np.mean(fit)
        print 'Chrom = ' + str(chroms[i][1:]) + ', fitness = ' + str(chroms[i][iFitness])
        
#         if(chroms[i][iFitness] == -1):
#             # See if fitness has been calculated sufficiently before
#             fit = lookupFitness(chr)
#             if fit == -1:
#                 print "Looking up fitness in DB, nothing found..."
#                 setupXML(chroms[i])
#                 executeExperiment()
#                 fitness = getFitnessFromFile()
#                 chroms[i][iFitness] = fitness
#                 # Store fitness for later reference
#                 tmp = deepcopy(chr)
#                 tmp[iFitness] = -1
#                 fitnessDB[str(tmp)] = [chroms[i][iFitness]]
#                 dumpDB()
#             elif len(fit) < nbFitnessValues: # add the fitness to fitness list
#                 print "Looking up fitness in DB, found:" + str(fit) + " with mean " + str(np.mean(fit))
#                 setupXML(chroms[i])
#                 executeExperiment()
#                 fitness = getFitnessFromFile()
#                 chroms[i][iFitness] = fitness
#                 # add the fitness to fitness list
#                 tmp = deepcopy(chr)
#                 tmp[iFitness] = -1
#                 fitnessDB[str(tmp)] = fitnessDB[str(tmp)] + [chroms[i][iFitness]]
#                 dumpDB()
#                 chroms[i][iFitness] = np.mean(fitnessDB[str(tmp)])
#             else:
#                 #print 'DB: chrom = ' + str(chroms[i][1]) + ', fitness = ' + str(fit)
#                 chroms[i][iFitness] = np.mean(fit)
        
#        print 'Chrom = ' + str(chroms[i][1:]) + ', fitness = ' + str(chroms[i][iFitness])
            
                
def calculateFitness(chroms): 
    #calculateFakeFitness(chroms)
    #calculateRealFitness(chroms)
    calculateRealFitnessParallel(chroms)
    
def cumsum(lis):
    nlist = [None] * len(lis)
    total = 0
    for i in range(len(lis)):
        total += lis[i]
        nlist[i] = total
    return nlist

#################################### SELECTION ####################################

def selectProportionateWithRF(chroms): # paper
    # Scale fitnesses
    fitnesses = [None] * len(chroms)
    maxi = max(chroms,key=lambda x: x[iFitness])[iFitness]
    mini = min(chroms,key=lambda x: x[iFitness])[iFitness]
    for i in range(len(chroms)):
        f = float(chroms[i][iFitness])
        c = float(2*maxi - mini)
        fitnesses[i] = f/math.sqrt(1-(f**2/c**2))
    # Selection procedure (Roulette Wheel)
    cumfit = cumsum(fitnesses)
    cumfit_normalized = [x/cumfit[len(cumfit)-1] for x in cumfit]
    nbChromosomesToSelect = int(nbChromosomes*selectionRate)
    if(nbChromosomesToSelect % 2 != 0):
        if(nbChromosomesToSelect == nbChromosomes or nbChromosomesToSelect+1 == nbChromosomes):
            nbChromosomesToSelect -= 1
        else:
            nbChromosomesToSelect += 1
    selChroms = [None]*nbChromosomesToSelect
    for i in range(len(selChroms)):
        rand = random.random();
        j = 0
        while(rand > cumfit_normalized[j] ):
            j += 1
        selChroms[i] = deepcopy(chroms[j])
    return selChroms

#################################### RECOMBINATION ####################################

# Either split between genes or in genes:
#    - Between: just do regular crossover
#    - In: Do regular crossover by splitting after the gene + take average of the gene in both chromosomes

# Recombination splits somewhere in the genome. In order to define whether we need to split between genes or in genes, 
# we need a chance distribution. This distribution is determined by the length we define for the different genes. Ideally
# every gene would have its own length which would determine the chance that recombination happens inside that gene. 
# We therefore define an int to have length 3 and a bool to have length 3. A space between genes also has length 1.
def recombine(chroms): 
    for i in range(0, len(chroms), 2):
        if(random.random() < crossProb):
            print "Recombining: " 
            print str(chroms[i])
            print str(chroms[i+1])
            if random.randint(1,23) <= 4: 
                recombineBetweenGenes(chroms[i], chroms[i+1], random.randint(iStart+1, iEnd))
            else:
                # Recombine in gene
                r = random.randint(1,21)  
                if r <= 9:
                    recombineRobotDistr(chroms[i], chroms[i+1])
                elif r == 12:
                    recombineSignalHasPriority(chroms[i], chroms[i+1])
                elif r <= 15:
                    recombineExploreTime(chroms[i], chroms[i+1])
                elif r <= 18:
                    recombineSignalTime(chroms[i], chroms[i+1])
                elif r <= 21:
                    recombineSignalCloseRange(chroms[i], chroms[i+1])
            # Reset fitness
            chroms[i][iFitness] = -1
            chroms[i+1][iFitness] = -1
            print "Recombined to: " 
            print str(chroms[i])
            print str(chroms[i+1])
                          
#         # Recombine robot numbers
#         if(random.random() < crossProb):
#             recombineRobotDistr(chroms[i],chroms[i+1])
#             # Reset fitness
#             chroms[i][iFitness] = -1
#             chroms[i+1][iFitness] = -1
#         # Recombine ...
#         
def recombineBetweenGenes(chrom1, chrom2, index): # Splitting happens exactly before the given index: i.e. giving the last possible index, splits at the last gene.
    chrom1 = chrom1[0:index] + chrom2[index:len(chrom2)]
    chrom2 = chrom2[0:index] + chrom1[index:len(chrom1)]
    
def recombineRobotDistr(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iRobotDistr)
    chrom1[iRobotDistr] = [(x + y)/2 for x, y in zip(chrom1[iRobotDistr], chrom2[iRobotDistr])]
    chrom2[iRobotDistr] = [(x + y)/2 for x, y in zip(chrom2[iRobotDistr], chrom1[iRobotDistr])]
    while(sum(chrom1[iRobotDistr]) < totalNbRobots):
        chrom1[iRobotDistr][random.randint(0, 2)] += 1
    while(sum(chrom2[iRobotDistr]) < totalNbRobots):
        chrom2[iRobotDistr][random.randint(0, 2)] += 1

def recombineOdometry(chrom1, chrom2):
    # Recombination of odometry regresses into a simple recombination between genes. Two chromosomes with the same value for odometry would result 
    # in two children with the same value. If they'd had different values, they'd result in two children with two different values.
    # It is still included in the recombination-in-a-gene case, because it is statistically more correct.
    recombineBetweenGenes(chrom1, chrom2, iOdometry)
    
def recombineSignalHasPriority(chrom1, chrom2):
    # Recombination of SignalHasPriority regresses into a simple recombination between genes. Two chromosomes with the same value for odometry would result 
    # in two children with the same value. If they'd had different values, they'd result in two children with two different values.
    # It is still included in the recombination-in-a-gene case, because it is statistically more correct.
    recombineBetweenGenes(chrom1, chrom2, iSignalHasPriority)
        
def recombineExploreTime(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iExploreTime)
    tmp = (chrom1[iExploreTime] + chrom2[iExploreTime])/2
    chrom1[iExploreTime] = tmp
    chrom2[iExploreTime] = tmp
    
def recombineSignalTime(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iSignalTime)
    tmp = (chrom1[iSignalTime] + chrom2[iSignalTime])/2
    chrom1[iSignalTime] = tmp
    chrom2[iSignalTime] = tmp
    
def recombineSignalCloseRange(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iSignalCloseRange)
    tmp = (chrom1[iSignalCloseRange] + chrom2[iSignalCloseRange])/2
    chrom1[iSignalCloseRange] = tmp
    chrom2[iSignalCloseRange] = tmp
        

#################################### MUTATION ####################################

# Mutation probablities are defined in the same way as for recombination, but here we give the entire robotDistr gene only a length of 3
def mutate(chroms): #TODO
    for i in range(len(chroms)):
        if(random.random() < mutationProb):
            print "Mutating: " + str(chroms[i])
            # Recombine in gene
            r = random.randint(1,15)  
            if r <= 3:
                mutateRobotDistr(chroms[i])
            elif r <= 6:
                mutateSignalHasPriority(chroms[i])
            elif r <= 9:
                mutateExploreTime(chroms[i])
            elif r <= 12:
                mutateSignalTime(chroms[i])
            elif r <= 15:
                mutateSignalCloseRange(chroms[i])
            # Reset fitness
            chroms[i][iFitness] = -1
            print "Mutated in: " + str(chroms[i])

#         # Mutate robot numbers
#         if(random.random() < mutationProb):
#             mutateRobotDistr(chroms[i]) # TODO: Only point or combination with inversion?
#             # Reset fitness
#             chroms[i][iFitness] = -1
#         # Mutate ...

def mutateRobotDistr(chrom):
    static = random.randint(0,2)
    if static == 0:
        d = 1 
        d2 = 2
    elif static == 1:
        d = 0
        d2 = 2
    elif static == 2:
        d = 0
        d2 = 1
        
    chrom[iRobotDistr][d] = random.randint(0,totalNbRobots - chrom[iRobotDistr][static])
    chrom[iRobotDistr][d2] = totalNbRobots - chrom[iRobotDistr][d] - chrom[iRobotDistr][static]
    
    # Try again if bad mutation
    if(isUseless(chrom)):
        print "Bad mutation: " + str(chrom) + ", retrying..."
        mutateRobotDistr(chrom)
    
#def robotNbInversionMutation(chrom): # Do not only use this mutation or not all of search space can be searched!
    # TODO: inverse 2 robot numbers
    
def mutateOdometry(chrom):
    if chrom[iOdometry] == 'false':
        chrom[iOdometry] = 'true'
    elif chrom[iOdometry] == 'true':
        chrom[iOdometry] = 'false'
        
def mutateSignalHasPriority(chrom):
    if chrom[iSignalHasPriority] == 'false':
        chrom[iSignalHasPriority] = 'true'
    elif chrom[iSignalHasPriority] == 'true':
        chrom[iSignalHasPriority] = 'false'
        
def mutateExploreTime(chrom): 
    chrom[iExploreTime] = random.randint(1, 20) # for now max = signalTimeMax #changed on remote
    
def mutateSignalTime(chrom):
    chrom[iSignalTime] = random.randint(1, 20) #changed on remote

def mutateSignalCloseRange(chrom): # Usefulness depends on patch size, maybe set limit relative to patch size here?
    chrom[iSignalCloseRange] = random.randint(1, 20) #changed on remote
    

#################################### REINSERTION ####################################

def insertOffspring(chroms, newChroms): #TODO: better replacement strategy. Now worst are substituted
    for i in range(len(newChroms)):
        chroms[i] = newChroms[i]
    return chroms


#################################### GENERATION ####################################

def generateRobotDist():
    r = random.randint(0, totalNbRobots)
    r2 = random.randint(0, totalNbRobots-r)
    return [r, r2, totalNbRobots-r-r2]

def generateBool():
    if random.randint(0,1) == 1:
        return 'true'
    else:
        return 'false' 

def generateChromosome():
    c = [None]*nbParameters
    c[iFitness] = -1    # -1 means no fitness calculated yet
    #c[iSeed] = random_seed
    c[iRobotDistr] = generateRobotDist()
    c[iOdometry] = useOdometry
    c[iExploreTime] = random.randint(1,20) # per 100 # 300 #changed on remote
    c[iSignalTime] = random.randint(1,50) # per 1000 # 2000 #changed on remote
    c[iSignalCloseRange] = random.randint(6, 15) # per 10 # 50 # should be bigger than obstacle avoidance distance #changed on remote
    c[iSignalHasPriority] = generateBool()
    return c 

#################################### DIVERSITY ####################################




def replaceBadChromosomes(chroms):
    increaseDiversity(chroms)
    removeUselessChromosomes(chroms)
    
def isUseless(chrom):
    if ((chrom[iRobotDistr][1] == 0 and chrom[iRobotDistr][2] != 0) or (chrom[iRobotDistr][1] != 0 and chrom[iRobotDistr][2] == 0)):
        return True
    else:
        return False

# An optimization is to remove all chromosomes that have robot distributions [a,0,c] or [a,b,0]. The first one is the same as [a+c,0,0], 
# while the other one can never be an optimal solution.
def removeUselessChromosomes(chroms):
    i = 0
    while(i != len(chroms)):
        if (isUseless(chroms[i])):
            tmp = chroms[i]
            chroms.remove(tmp)
            tmp2 = generateChromosome()
            chroms.append(tmp2)
            print "[USELESS] Replacing " + str(tmp) + " with " + str(tmp2)
            i -= 1
        i += 1
    
# In small populations (or ones with low selection rate), some individuals might reproduce with themselves, essentially making 2 clones. 
# This leaves 4 individuals in the population that are exactly the same. We therefore remove any individuals 
# that appear more than twice in the population and replace them with newly generated ones. This way, diversity is ensured.
def increaseDiversity(chroms):
    i = 0
    while i != len(chroms):
        counter = 0
        tmp = chroms[i]
        for j in range(len(chroms)):
            if str(chroms[j][1:]) == str(chroms[i][1:]):
                counter = counter + 1
        while counter > 2:
            chroms.remove(tmp)
            tmp2 = generateChromosome()
            chroms.append(tmp2)
            print "[DIVERSITY] Replacing " + str(tmp) + " with " + str(tmp2)
            counter -= 1
            i = 0 # restart search because indices of chroms have changed
        i += 1

#################################### ALGORITHM ####################################

def getAverageFitness(chroms):
    sum = [0]
    for i in range(len(chroms)):
        sum += [chroms[i][iFitness]]
    return np.mean(sum)

def run_ga():
    global fitnessDB
    # Initiliatize GA seed
    random.seed(gaSeed)
    # read in fitness database
    loadDB()
    # initialize population
    chroms = nbChromosomes * [None]
    
    for i in range(nbChromosomes):  # TODO, define which ones are valid and make generation of invalid ones impossible
        chroms[i] = generateChromosome() # first number is fitness, -1 means no fitness calculated yet

    print chroms

    # generation loop
    for gen in range(nbGenerations):
        print '************ GENERATION ' + str(gen) + ' ************'
        # Replace bad chromosomes
        replaceBadChromosomes(chroms)
        # assign fitness to entire population and sort
        calculateFitness(chroms)
        chroms.sort(key=lambda c: c[iFitness], reverse=False)
        print '<<<<<<<<<< Average fitness: ' + str(getAverageFitness(chroms)) + ' >>>>>>>>>>'
        # stop criteria
        #TODO
        # select breeders: fitness proportionate with scaling
        selChroms = selectProportionateWithRF(chroms)
        # recombine
        recombine(selChroms)
        # mutate
        mutate(selChroms)
        # insert offspring
        chroms = insertOffspring(chroms, selChroms)
        
    # Return best
    print '********** Final population **********'
    calculateFitness(chroms)
    chroms.sort(key=lambda c: c[iFitness], reverse=False)
    print chroms
    dumpDB()
    return max(chroms,key=lambda x: x[iFitness])


print run_ga()




    
    