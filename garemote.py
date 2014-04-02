#! /usr/bin/env python

# usage: ga.py nbChromosomes nbGenerations selectionRate mutationProb crossProb

# Implementation details:
#    - Selection process should always select an even number of parents
#    - Relative fitness scaling uses scaling factor: 2*max - min. This assures that as fitness spread becomes smaller, scaling becomes more important.

# Notes:
#    - Mutation for the robot numbers should just generate a new robot distribution. Mutating the first or second number, 
#    would always automatically result in also mutating the third number when the total number of robots is fixed, which is unfair.
#    Adding 1 randomly as a mutation would be a too little mutation. Mutating larger numbers results in a completely new gene anyway.
#    Using an inversion mutation would also not make sense, because depending on the initial population, not all the search space can be searched.
#    Mutation should keep 1 robot number the same and then mutate the other two in some way.

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


fitnessDB = {}
nbChromosomes = int(sys.argv[1])
nbGenerations = int(sys.argv[2])
selectionRate = float(sys.argv[3]) # If 1, no elitism
mutationProb =  float(sys.argv[4]) # 0.05
crossProb = float(sys.argv[5]) # 0.95

# Actual parameters
# Experiment
random_seed = 11
#parameters
#useOdometry = 'false'
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
nbFoodPatches = 2
nbFoodItems = 50
renewalRate = 1
foodPatchSize = 3
patchType = 'patched'
output = 'ga.csv'

nbParameters = 7

iStart = 2
iEnd = 6
# Names for chromosome indices, making the code more readable
iFitness = 0
iSeed = 1
iRobotDistr = 2
iOdometry = 3
iExploreTime = 4
iSignalTime = 5
iSignalCloseRange = 6

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
    f = open('db','wb')
    pickle.dump(fitnessDB, f)
    f.close()
atexit.register(dumpDB)

def calculateFakeFitness(chroms): 
    for i in range(len(chroms)):
        if(chroms[i][iFitness] == -1):
            chroms[i][iFitness] = chroms[i][iRobotDistr][0]/6.0 + chroms[i][iRobotDistr][1]/6.0
            if(chroms[i][iRobotDistr][0] == 6 and chroms[i][iRobotDistr][1] == 6):
                chroms[i][iFitness] = 5.0
                
def setupXML(chrom):
    xml = 'ga.argos'
    tree = etree.parse(xml)
    root = tree.getroot()
    experiment = root.find('framework').find('experiment')
    parameters = root.find('controllers').find('footbot_combined_novis_controller').find('params').find('parameters')
    entity = root.find('arena').find('distribute').find('entity')
    foraging = root.find('loop_functions').find('foraging')
    
    experiment.set('random_seed',str(random_seed))
    
    parameters.set('useOdometry',str(chrom[iOdometry]))
    parameters.set('exploreTime',str(chrom[iExploreTime]))
    parameters.set('signalTime',str(chrom[iSignalTime]))
    parameters.set('dropTime',str(dropTime))
    parameters.set('pickupTime',str(pickupTime))
    parameters.set('signalCloseRange',str(chrom[iSignalCloseRange]))
    parameters.set('signalDistance',str(signalDistance))
    parameters.set('obstacleAvoidanceDistance',str(obstacleAvoidanceDistance))
    parameters.set('avoidanceFactor',str(avoidanceFactor))
    
    entity.set('quantity',str(totalNbRobots))
    
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
    
    print 'Setting up XML file with nbSolitary=' + str(chrom[iRobotDistr][0]) + ', nbRecruiter='+str(chrom[iRobotDistr][1])+', nbRecruitee='+str(chrom[iRobotDistr][2])
    
def lookupFitness(chrom):
    tmp = deepcopy(chrom)
    tmp[iFitness] = -1
    tmp = str(tmp)
    if tmp in fitnessDB:
        return fitnessDB[tmp]
    else:
        return -1
    
def executeExperiment():
    os.chdir('/home/stevenve/ARGOS3')
    subprocess.call(['time','argos3','-c','argos3-projects/problem/xml/ga.argos'])
    os.chdir('~/gaworkspace/ga')
    
def getFitnessFromFile():
    with open('ga.csv', 'rb') as f:
        content = f.readlines()
        ll = content[len(content)-1]
        tmp = ll.rstrip().split(',')
        return int(tmp[1]) + int(tmp[2]) + int(tmp[3])
                
def calculateRealFitness(chroms): # DON'T RECALCULATE IF DONE BEFORE
    global fitnessDB
    for i in range(len(chroms)):
        if(chroms[i][iFitness] == -1):
            # See if fitness has been calculated before
            fit = lookupFitness(chroms[i])
            if fit == -1:
                setupXML(chroms[i])
                executeExperiment()
                fitness = getFitnessFromFile()
                chroms[i][iFitness] = fitness
                # Store fitness for later reference
                tmp = deepcopy(chroms[i])
                tmp[iFitness] = -1
                fitnessDB[str(tmp)] = chroms[i][iFitness]
                dumpDB()
            else:
                #print 'DB: chrom = ' + str(chroms[i][1]) + ', fitness = ' + str(fit)
                chroms[i][iFitness] = fit
        print 'Chrom = ' + str(chroms[i][iRobotDistr]) + ', fitness = ' + str(chroms[i][iFitness])
            
                
def calculateFitness(chroms): 
    #calculateFakeFitness(chroms)
    calculateRealFitness(chroms)
    
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

def recombine(chroms): #TODO
    for i in range(0, len(chroms), 2):
#         if(random.random() < crossProb):
#             if random.random() < 0.5: 
#                 recombineBetweenGenes(chroms[i], chroms[i+1], random.randint(iStart+1, iEnd))
#             else:
#                 # Recombine in gene
#                 r = random.randint(1,5)  
#                 if r == 1:
#                     recombineRobotDistr(chroms[i], chroms[i+1])
#                 elif r == 2:
#                     recombineOdometry(chroms[i], chroms[i+1])
#                 elif r == 3:
#                     recombineExploreTime(chroms[i], chroms[i+1])
#                 elif r == 4:
#                     recombineSignalTime(chroms[i], chroms[i+1])
#                 elif r == 5:
#                     recombineSignalCloseRange(chroms[i], chroms[i+1])
#             # Reset fitness
#             chroms[i][iFitness] = -1
#             chroms[i+1][iFitness] = -1
                          
        # Recombine robot numbers
        if(random.random() < crossProb):
            recombineRobotDistr(chroms[i],chroms[i+1])
            # Reset fitness
            chroms[i][iFitness] = -1
            chroms[i+1][iFitness] = -1
        # Recombine ...
        
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
        
def recombineExploreTime(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iExploreTime)
    chrom1[iExploreTime] = (chrom1[iExploreTime] + chrom2[iExploreTime])/2
    chrom2[iExploreTime] = (chrom1[iExploreTime] + chrom2[iExploreTime])/2
    
def recombineSignalTime(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iSignalTime)
    chrom1[iSignalTime] = (chrom1[iSignalTime] + chrom2[iSignalTime])/2
    chrom2[iSignalTime] = (chrom1[iSignalTime] + chrom2[iSignalTime])/2
    
def recombineSignalCloseRange(chrom1, chrom2):
    recombineBetweenGenes(chrom1, chrom2, iSignalCloseRange)
    chrom1[iSignalCloseRange] = (chrom1[iSignalCloseRange] + chrom2[iSignalCloseRange])/2
    chrom2[iSignalCloseRange] = (chrom1[iSignalCloseRange] + chrom2[iSignalCloseRange])/2
        

#################################### MUTATION ####################################
        
def mutate(chroms): #TODO
    for i in range(len(chroms)):
#         if(random.random() < mutationProb):
#             # Recombine in gene
#             r = random.randint(1,5)  
#             if r == 1:
#                 mutateRobotDistr(chroms[i])
#             elif r == 2:
#                 mutateOdometry(chroms[i])
#             elif r == 3:
#                 mutateExploreTime(chroms[i])
#             elif r == 4:
#                 mutateSignalTime(chroms[i])
#             elif r == 5:
#                 mutateSignalCloseRange(chroms[i])
#         # Reset fitness
#         chroms[i][iFitness] = -1
#         chroms[i+1][iFitness] = -1

        # Mutate robot numbers
        if(random.random() < mutationProb):
            mutateRobotDistr(chroms[i]) # TODO: Only point or combination with inversion?
            # Reset fitness
            chroms[i][iFitness] = -1
        # Mutate ...

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
    
#def robotNbInversionMutation(chrom): # Do not only use this mutation or not all of search space can be searched!
    # TODO: inverse 2 robot numbers
    
def mutateOdometry(chrom):
    if chrom[iOdometry] == 'false':
        chrom[iOdometry] = 'true'
    elif chrom[iOdometry] == 'true':
        chrom[iOdometry] = 'false'
        
def mutateExploreTime(chrom): 
    chrom[iExploreTime] = random.randint(100, 10000) # for now max = signalTimeMax
    
def mutateSignalTime(chrom):
    chrom[iSignalTime] = random.randint(100, 10000)

def mutateSignalCloseRange(chrom): # Usefulness depends on patch size, maybe set limit relative to patch size here?
    chrom[iSignalCloseRange] = random.randint(20, 500)
    

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

def generateChromosome():
    c = [None]*nbParameters
    c[iFitness] = -1    # -1 means no fitness calculated yet
    c[iSeed] = random_seed
    c[iRobotDistr] = generateRobotDist()
    c[iOdometry] = 'false'
    c[iExploreTime] = 300
    c[iSignalTime] = 2000
    c[iSignalCloseRange] = 50
    return c 


#################################### ALGORITHM ####################################

def run_ga():
    global fitnessDB
    # read in fitness database
    try:
        f = open('db','rb')
        fitnessDB = pickle.load(f)
        f.close()
    except (EOFError, IOError):
        print 'No db found or it is empty'
    # initialize population
    chroms = nbChromosomes * [None]
    
    random.seed('seed')
    for i in range(nbChromosomes):  # TODO, define which ones are valid and make generation of invalid ones impossible
        chroms[i] = generateChromosome() # first number is fitness, -1 means no fitness calculated yet

    print chroms

    # generation loop
    for gen in range(nbGenerations):
        print '************ GENERATION ' + str(gen) + ' ************'
        # assign fitness to entire population and sort
        calculateFitness(chroms)
        chroms.sort(key=lambda c: c[iFitness], reverse=False)
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




    
    