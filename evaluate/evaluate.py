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
import multiprocessing


nbRuns = int(sys.argv[1])
nbThreads = int(sys.argv[2])

envRandom = random.Random(random.randint(1,100000))

# Experiment
random_seed = envRandom.randint(1, 100000)
#parameters
useOdometry = 'false'
signalHasPriority = 'true'
exploreTime = 3
signalTime = 15
dropTime = 1
pickupTime = 1
signalCloseRange = 2
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
output = '/home/stevenve/results/ga'



                
def setupXML(nb):
    xml = '/home/stevenve/gaworkspace/ga/ga.argos'
    xml2 = '/home/stevenve/gaworkspace/ga/ga' + str(nb) + '.argos'
    tree = etree.parse(xml)
    root = tree.getroot()
    experiment = root.find('framework').find('experiment')
    parameters = root.find('controllers').find('footbot_combined_novis_controller').find('params').find('parameters')
    #entity = root.find('arena').find('distribute').find('entity')
    foraging = root.find('loop_functions').find('foraging')
    
    experiment.set('random_seed',str(envRandom.randint(1, 100000)))
    experiment.set('length', str(50000))
    
    parameters.set('useOdometry',str(useOdometry))
    parameters.set('exploreTime',str(exploreTime*100))
    parameters.set('signalTime',str(signalTime*1000))
    parameters.set('signalHasPriority',str(signalHasPriority))
    parameters.set('signalCloseRange',str(signalCloseRange*10))
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
    foraging.set('nbSolitary',str(0))
    foraging.set('nbRecruiter',str(4))
    foraging.set('nbRecruitee',str(8))
    foraging.set('output',output + str(nb) + '.csv')
    etree.tostring(root, pretty_print=True)
    f = open(xml, 'w')
    f.write(etree.tostring(root, pretty_print=True))
    f.close()
    
    print 'Executing experiment with nbSolitary=' + str(0) + ', nbRecruiter='+str(4)+', nbRecruitee='+str(8)
    
def executeExperiment(nb):
    start = time.time()
    os.chdir('/home/stevenve/argos/argos3/argos3-projects')
    bla = subprocess.Popen(['time','argos3','-c','/home/stevenve/gaworkspace/ga/ga'+str(nb)+'.argos'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE).communicate()[0]
    os.chdir('/home/stevenve/gaworkspace/ga')
    print "Experiment finished after " + str(round(time.time()-start,2)) + " seconds."
    
def doExperiment(nb):
    random_seed = envRandom.randint(1, 100000)
    setupXML(nb)
    executeExperiment(nb)
    
pool = multiprocessing.Pool(processes=nbThreads)
pool.map(doExperiment, range(nbRuns))




    
    