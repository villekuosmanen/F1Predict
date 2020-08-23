import pickle
import json
import copy

from python.race_model.EloRaceModel import EloRaceModelGenerator, EloRaceModel, EloDriver
from python.race_model.raceMonteCarlo import simulateRace

ROOKIE_DRIVER_RATING = 1800

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

#Read user variables:
user_vars = {}
with open("user_variables.txt") as f:
    for line in f:
        key, value = line.partition("=")[::2]
        user_vars[key.rstrip()] = value.rstrip()

with open('data/raceSeasonsData.pickle', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/raceResultsData.pickle', 'rb') as handle:
    raceResultsData = pickle.load(handle)
    
with open('data/driversData.pickle', 'rb') as handle:
    driversData = pickle.load(handle)
    
with open('data/constructorsData.pickle', 'rb') as handle:
    constructorsData = pickle.load(handle)
    
with open('data/enginesData.pickle', 'rb') as handle:
    enginesData = pickle.load(handle)

generator = EloRaceModelGenerator(seasonsData, raceResultsData, driversData, constructorsData, enginesData)
predictions = generator.generateModel()
predictions = generator.generatePredictions()
raceModel = generator.getModel()

print("Model done")

# for driver in raceModel.drivers.values():
#     print(driver)
#     print("{}: {}".format(driver.name, driver.rating))

# for constructor in raceModel.constructors.values():
#     print("Constructor {}: {}".format(constructor.name, constructor.rating))

# print()

# for engine in raceModel.engines.values():
#     print("Engine {}: {}".format(engine.name, engine.rating))

# for trackId, alpha in raceModel.tracks.items():
#     print("{}: {}".format(trackId, alpha))
# print("Predictions:")
# for pred in predictions[-5:]:
#     for driverId in pred:
#         print(raceModel.drivers[driverId].name)
#     print("\n")



grid = json.load(open('data/gridTest.json'))

outFile = {} # The object where we write output

newDrivers = json.load(open('data/newDrivers.json'))["drivers"]
newDrivers = {int(did): cid for did, cid in newDrivers.items()}
for did, cid in newDrivers.items():
    if int(did) == -1:  # Cases when driver doesn't exist in data
        raceModel.drivers[int(did)] = EloDriver("__PLACEHOLDER__", raceModel.constructors[int(cid)])
        raceModel.drivers[int(did)].rating = ROOKIE_DRIVER_RATING
    if not cid == "":
        raceModel.drivers[int(did)].constructor = raceModel.constructors[int(cid)]   # Data in newDrivers.json overwrites database

driversToWrite = {}
for did in grid:
    driversToWrite[int(did)] = {}
    driversToWrite[int(did)]["name"] = raceModel.drivers[int(did)].name
    driversToWrite[int(did)]["constructor"] = raceModel.drivers[int(did)].constructor.name
    driversToWrite[int(did)]["color"] = getColor(raceModel.drivers[int(did)].constructor.name)
outFile["drivers"] = driversToWrite

raceId = -1
with open('data/futureRaces.json', 'r') as handle:
    futureRaces = json.load(handle)
    circuit = futureRaces[0]["circuitId"]
    circuitName = futureRaces[0]["name"]
    raceId = futureRaces[0]["raceId"]

# Edit index file
with open('{}races/index.json'.format(user_vars['predictions_output_folder']), 'r+') as handle:
    data = json.load(handle)
    data[str(futureRaces[0]["year"])][str(raceId)] = circuitName
    handle.seek(0)        # <--- should reset file position to the beginning.
    json.dump(data, handle, indent=4)
    handle.truncate()

outFile["name"] = circuitName
outFile["year"] = futureRaces[0]["year"]

gaElos = []
racePredictions = {}
for gridPosition, did in enumerate(grid):
    gaElo = raceModel.getGaElo(did, gridPosition, circuit)
    gaElos.append((did, gaElo))
    racePredictions[did] = {}

gaElos.sort(key=lambda x: x[1], reverse=True)
outFile["order"] = [a for (a, b) in gaElos]

for i in range(10000):
    modelCopy = copy.deepcopy(raceModel)
    results = simulateRace(modelCopy, grid, circuit)
    for pos, did in enumerate(results):
        if pos not in racePredictions[did]:
            racePredictions[did][pos] = 0
        racePredictions[did][pos] += 1
outFile["predictions"] = racePredictions

with open('{}races/{}.json'.format(user_vars['predictions_output_folder'], str(raceId)), 'w') as fp:
    json.dump(outFile, fp)