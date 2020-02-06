from python import *

import operator
import pickle
import os
import numpy as np
import json
from ipyparallel import Client
from itertools import repeat

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split


def gradient(x, err):
    grad = -(1.0/len(x)) * err @ x
    return grad

def squaredError(err):
    return err**2

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

cleaner = F1DataCleaner(seasonsData, qualiResultsData, driversData, constructorsData, enginesData)

# Run gradient descent
alpha = 0.18
stop = 0.02
entries, errors, results = cleaner.constructDataset()
grad = gradient(entries, errors)
while np.linalg.norm(grad) > stop:
    # Move in the direction of the gradient
    # N.B. this is point-wise multiplication, not a dot product
    cleaner.theta = cleaner.theta - grad*alpha
    mae = errors.mean()
    print(mae)
    entries, errors, results = cleaner.constructDataset()
    grad = gradient(entries, errors)

print("Gradient descent finished. MAE="+str(mae))
print(cleaner.theta)

newDrivers = json.load(open('data/newDrivers.json'))["drivers"]
newDrivers = {int(did): cid for did, cid in newDrivers.items()}

outFile = {} # The object where we write output

driversToWrite = {}
for did, cid in newDrivers.items():
    driversToWrite[int(did)] = {}
    if int(did) == -1:  # Cases when driver doesn't exist in data
        driversToWrite[int(did)]["name"] = "Nicholas Latifi"
        cleaner.addNewDriver(int(did), "Nicholas Latifi", cid)
    else:
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
        cleaner.drivers[did].constructor.engine.trackpwr[circuit],
        1
    ]
    predictedEntrants.append(entry)

linearRegResults = [np.dot(x, cleaner.theta) for x in predictedEntrants]

driverResults = {} # {did: {position: amount}}
orderedResults = [] # [(did, prediction) ...]
for index, (did, cid) in enumerate(newDrivers.items()):
    newDrivers[did] = linearRegResults[index]
    driverResults[int(did)] = {}
    orderedResults.append((did, linearRegResults[index]))
print(newDrivers)
    
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