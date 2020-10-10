import operator
import pickle
import numpy as np
import json
import copy

from python.quali.QualiDataProcessor import QualiDataProcessor
from python.quali.monteCarlo import predictQualiResults
from python.race_model.EloRaceModel import EloRaceModelGenerator, EloRaceModel, EloDriver
from python.race_model.raceMonteCarlo import simulateRace

def gradient(x, err):
    grad = -(1.0/len(x)) * err @ x
    return grad

def squaredError(err):
    return err**2

def getColor(constructor):
    return {
        "Mercedes": "#00D2BE",
        "Ferrari": "#C00000",
        "Red Bull": "#0600EF",
        "Racing Point": "#F596C8",
        "Williams": "#0082FA",
        "Renault": "#FFF500",
        "AlphaTauri": "#C8C8C8",
        "Haas F1 Team": "#787878",
        "McLaren": "#FF8700",
        "Alfa Romeo": "#960000"
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

#Read user variables:
user_vars = {}
with open("user_variables.txt") as f:
    for line in f:
        key, value = line.partition("=")[::2]
        user_vars[key.rstrip()] = value.rstrip()

with open('data/seasonsData.pickle', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/qualiResultsData.pickle', 'rb') as handle:
    qualiResultsData = pickle.load(handle)

with open('data/raceResultsData.pickle', 'rb') as handle:
    raceResultsData = pickle.load(handle)
    
with open('data/driversData.pickle', 'rb') as handle:
    driversData = pickle.load(handle)
    
with open('data/constructorsData.pickle', 'rb') as handle:
    constructorsData = pickle.load(handle)
    
with open('data/enginesData.pickle', 'rb') as handle:
    enginesData = pickle.load(handle)

processor = QualiDataProcessor(seasonsData, qualiResultsData, driversData, constructorsData, enginesData)

# Run gradient descent
alpha = 0.18
stop = 0.016
processor.processDataset()
model = processor.getModel()
entries, errors, results = processor.getDataset()
grad = gradient(entries, errors)

i = 0
while np.linalg.norm(grad) > stop and i < 40:
    # Move in the direction of the gradient
    # N.B. this is point-wise multiplication, not a dot product
    model.theta = model.theta - grad*alpha
    mae = np.array([abs(x) for x in errors]).mean()
    print(mae)

    processor.processDataset()
    entries, errors, results = processor.getDataset()
    grad = gradient(entries, errors)
    i += 1

print("Gradient descent finished. MAE="+str(mae))
model = processor.getModel()
print(model.theta)

with open('out/driver_variances.pickle', 'wb+') as out:
    pickle.dump(model.driver_variances, out, protocol=pickle.HIGHEST_PROTOCOL)
with open('out/const_variances.pickle', 'wb+') as out:
    pickle.dump(model.const_variances, out, protocol=pickle.HIGHEST_PROTOCOL)
with open('out/engine_variances.pickle', 'wb+') as out:
    pickle.dump(model.engine_variances, out, protocol=pickle.HIGHEST_PROTOCOL)

# Save model (if needed): TODO FIX
# with open('out/trained_cleaner.pickle', 'wb+') as out:
#     pickle.dump(cleaner, out, protocol=pickle.HIGHEST_PROTOCOL)

print("Generating race model...")
generator = EloRaceModelGenerator(seasonsData, raceResultsData, driversData, constructorsData, enginesData)
generator.generateModel()
raceModel = generator.getModel()

outFile = {} # The object where we write output
raceOutFile = {}

# Overwrite models based on newDrivers.json
newDrivers = json.load(open('data/newDrivers.json'))["drivers"]
newDrivers = {int(did): cid for did, cid in newDrivers.items()}
for did, cid in newDrivers.items():
    if int(did) < 0:  # Cases when driver doesn't exist in data
        driversToWrite[int(did)]["name"] = "__PLACEHOLDER__"
        model.addNewDriver(int(did), "__PLACEHOLDER__", cid)
        raceModel.drivers[int(did)] = EloDriver("__PLACEHOLDER__", raceModel.constructors[int(cid)])
        raceModel.drivers[int(did)].rating = ROOKIE_DRIVER_RATING
    if not cid == "":
        model.drivers[int(did)].constructor = model.constructors[int(cid)]   # Data in newDrivers.json overwrites database
        raceModel.drivers[int(did)].constructor = raceModel.constructors[int(cid)]

# Write driver details to outFile
driversToWrite = {}
for did in newDrivers.keys():
    driversToWrite[int(did)] = {}
    driversToWrite[int(did)]["name"] = model.drivers[int(did)].name
    driversToWrite[int(did)]["constructor"] = model.drivers[int(did)].constructor.name
    driversToWrite[int(did)]["color"] = getColor(model.drivers[int(did)].constructor.name)
outFile["drivers"] = driversToWrite
raceOutFile["drivers"] = driversToWrite

# Write race details to outFile
raceId = -1
with open('data/futureRaces.json', 'r') as handle:
    futureRaces = json.load(handle)
    circuit = futureRaces[0]["circuitId"]
    circuitName = futureRaces[0]["name"]
    raceId = futureRaces[0]["raceId"]
    
# Edit index file
with open(user_vars['predictions_output_folder'] + 'index.json', 'r+') as handle:
    data = json.load(handle)
    data[str(futureRaces[0]["year"])][str(raceId)] = circuitName
    handle.seek(0)        # <--- should reset file position to the beginning.
    json.dump(data, handle, indent=4)
    handle.truncate()

# Edit index file
with open('{}races/index.json'.format(user_vars['predictions_output_folder']), 'r+') as handle:
    data = json.load(handle)
    data[str(futureRaces[0]["year"])][str(raceId)] = circuitName
    handle.seek(0)        # <--- should reset file position to the beginning.
    json.dump(data, handle, indent=4)
    handle.truncate()

outFile["name"] = circuitName
outFile["year"] = futureRaces[0]["year"]
raceOutFile["name"] = circuitName
raceOutFile["year"] = futureRaces[0]["year"]

predictedEntrants = []

for did, cid in newDrivers.items():
    if circuit not in model.drivers[did].trackpwr:
        model.drivers[did].trackpwr[circuit] = 0
    if circuit not in model.drivers[did].constructor.trackpwr:
        model.drivers[did].constructor.trackpwr[circuit] = 0
    if circuit not in model.drivers[did].constructor.engine.trackpwr:
        model.drivers[did].constructor.engine.trackpwr[circuit] = 0
    
    entry = [
        model.drivers[did].pwr,
        model.drivers[did].constructor.pwr, 
        model.drivers[did].constructor.engine.pwr,
        model.drivers[did].trackpwr[circuit],
        model.drivers[did].constructor.trackpwr[circuit],
        model.drivers[did].constructor.engine.trackpwr[circuit],
        1
    ]
    predictedEntrants.append(entry)

linearRegResults = [np.dot(x, model.theta) for x in predictedEntrants]

driverResults = {} # {did: {position: amount}}
orderedResults = [] # [(did, prediction) ...]
for index, (did, cid) in enumerate(newDrivers.items()):
    driverResults[int(did)] = {}
    orderedResults.append((did, linearRegResults[index]))
    
orderedResults.sort(key = operator.itemgetter(1))
outFile["order"] = [a for (a, b) in orderedResults]

gaElos = []
racePredictions = {}
raceModel.addNewTrack(circuit)
for gridPosition, did in enumerate(outFile["order"]):
    gaElo = raceModel.getGaElo(did, gridPosition, circuit)
    gaElos.append((did, gaElo))
    racePredictions[did] = {}
gaElos.sort(key=lambda x: x[1], reverse=True)
raceOutFile["order"] = [a for (a, b) in gaElos]
    
for i in range(10000):
    scoreList = predictQualiResults(circuit, newDrivers, model)
    for i, drivRes in enumerate(scoreList):
        if i not in driverResults[drivRes[0]]:
            driverResults[drivRes[0]][i] = 0
        driverResults[drivRes[0]][i] += 1
    # Generate predictions for races
    grid = [drivRes[0] for drivRes in scoreList]
    modelCopy = copy.deepcopy(raceModel)
    results, retiredDrivers = simulateRace(modelCopy, grid, circuit)
    for pos, did in enumerate(results):
        if pos not in racePredictions[did]:
            racePredictions[did][pos] = 0
        racePredictions[did][pos] += 1
    for did in retiredDrivers:
        if "ret" not in racePredictions[did]:
            racePredictions[did]["ret"] = 0
        racePredictions[did]["ret"] += 1
    
        
outFile["predictions"] = driverResults
with open(user_vars['predictions_output_folder'] + str(raceId) + '.json', 'w') as fp:
    json.dump(outFile, fp)

raceOutFile["predictions"] = racePredictions
with open('{}races/{}.json'.format(user_vars['predictions_output_folder'], str(raceId)), 'w') as fp:
    json.dump(raceOutFile, fp)