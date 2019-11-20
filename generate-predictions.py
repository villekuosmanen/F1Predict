from python import *

import operator
import pickle
import os
import numpy as np
import json
from ipyparallel import Client
from itertools import repeat

from sklearn.ensemble import RandomForestRegressor

def getColor(constructor):
    return {
        "Mercedes": "#00d2be",
        "Ferrari": "#dc0000",
        "Red Bull": "#1e41ff",
        "Racing Point": "#f596c8",
        "Williams": "#ffffff",
        "Renault": "#fff500",
        "Toro Rosso": "#469bff",
        "Haas F1 Team": "#f0d787",
        "McLaren": "#ff8700",
        "Alfa Romeo": "#9b0000"
    }.get(constructor, "#000000")

#Create data classes
#Year, Season
seasonsData = None
#RaceId, List of tuples of (driverId, constructorId, time)
qualiResultsData = None
#DriverId, name
driversData = None
#ConstructorId, name
constructorsData = None
#EngineId, name
enginesData = None

with open('data/seasonsData.txt', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/qualiResultsData.txt', 'rb') as handle:
    qualiResultsData = pickle.load(handle)
    
with open('data/driversData.txt', 'rb') as handle:
    driversData = pickle.load(handle)
    
with open('data/constructorsData.txt', 'rb') as handle:
    constructorsData = pickle.load(handle)
    
with open('data/enginesData.txt', 'rb') as handle:
    enginesData = pickle.load(handle)

entries = []
results = []
cleaner = F1DataCleaner(seasonsData, qualiResultsData, driversData, constructorsData, enginesData)

#Constants we can change
cleaner.k_engine_change = 0.0145
cleaner.k_const_change = 0.240
cleaner.k_driver_change = 0.19
cleaner.k_const_impact = 0.80
cleaner.k_eng_impact = (1 - cleaner.k_const_impact)
cleaner.k_driver_impact = 0.02
        
cleaner.k_rookie_pwr = 0.40
#cleaner.k_rookie_variance = 5
cleaner.k_race_regress_exp = 0.87  #TODO needs to change!
#cleaner.k_variance_multiplier_end = 1.5

cleaner.k_eng_regress = 1.04
cleaner.k_const_regress = 0.60
cleaner.k_driver_regress = 0.67

cleaner.constructDataset(entries, results)
#print(entries[-10:])
#print(results[-10:])
X = np.array(entries)
y = results

forest = RandomForestRegressor(random_state=0, n_estimators=100)
forest.fit(X, y)

newDrivers = json.load(open('data/newDrivers.json'))["drivers"]
newDrivers = {int(did): cid for did, cid in newDrivers.items()}

outFile = {} # The object where we write output

driversToWrite = {}
for did, cid in newDrivers.items():
    driversToWrite[int(did)] = {}
    driversToWrite[int(did)]["name"] = cleaner.drivers[int(did)].name
    if not cid == "":
        cleaner.drivers[int(did)].constructor = cleaner.constructors[int(cid)]   # Data in newDrivers.json overwrites database
    driversToWrite[int(did)]["constructor"] = cleaner.drivers[int(did)].constructor.name
    driversToWrite[int(did)]["color"] = getColor(cleaner.drivers[int(did)].constructor.name)
outFile["drivers"] = driversToWrite

raceId = -1
with open('data/futureRaces.json', 'r') as handle:
    futureRaces = json.load(handle)
    circuit = futureRaces[0]["circuitId"]
    circuitName = futureRaces[0]["name"]
    raceId = futureRaces[0]["raceId"]
    #print(seasonsData)
    
# Edit index file
with open('../F1PredictWeb/src/public/data/index.json', 'r+') as handle:
    data = json.load(handle)
    data[str(futureRaces[0]["year"])][str(raceId)] = circuitName
    handle.seek(0)        # <--- should reset file position to the beginning.
    json.dump(data, handle, indent=4)
    handle.truncate()

outFile["name"] = circuitName
outFile["year"] = futureRaces[0]["year"]

predictedEntrants = []

for did, cid in newDrivers.items():
    if circuit not in cleaner.drivers[did].trackpwr:
        cleaner.drivers[did].trackpwr[circuit] = 0 #TODO maybe change defaults
    if circuit not in cleaner.drivers[did].constructor.trackpwr:
        cleaner.drivers[did].constructor.trackpwr[circuit] = 0 #TODO maybe change defaults
    if circuit not in cleaner.drivers[did].constructor.engine.trackpwr:
        cleaner.drivers[did].constructor.engine.trackpwr[circuit] = 0 #TODO maybe change defaults
    
    entry = [
        cleaner.drivers[did].pwr,
        cleaner.drivers[did].constructor.pwr, 
        cleaner.drivers[did].constructor.engine.pwr,
        cleaner.drivers[did].trackpwr[circuit],
        cleaner.drivers[did].constructor.trackpwr[circuit],
        cleaner.drivers[did].constructor.engine.trackpwr[circuit]
    ]
    predictedEntrants.append(entry)

forestResults = forest.predict(np.array(predictedEntrants))

driverResults = {} # {did: {position: amount}}
orderedResults = [] # [(did, prediction) ...]
for index, (did, cid) in enumerate(newDrivers.items()):
    newDrivers[did] = forestResults[index]
    driverResults[int(did)] = {}
    orderedResults.append((did, forestResults[index]))
    
orderedResults.sort(key = operator.itemgetter(1))
outFile["order"] = [a for (a, b) in orderedResults]
    
for i in range(1000):
    scoreList = predictQualiResults(circuit, newDrivers)
    for i, drivRes in enumerate(scoreList):
        if i not in driverResults[drivRes[0]]:
            driverResults[drivRes[0]][i] = 0
        driverResults[drivRes[0]][i] += 1
        
outFile["predictions"] = driverResults
with open('../F1PredictWeb/src/public/data/' + str(raceId) + '.json', 'w') as fp:
    json.dump(outFile, fp)