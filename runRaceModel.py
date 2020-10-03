import json
import copy

from python.common import file_operations
from python.race_model.EloRaceModel import EloRaceModelGenerator, EloRaceModel, EloDriver
from python.race_model.raceMonteCarlo import simulateRace
from python.race_model import common as race_common

ROOKIE_DRIVER_RATING = 1800
USER_VARS = file_operations.getUserVariables("user_variables.txt")


def generateModel():
    seasonsData, raceResultsData, driversData, constructorsData, enginesData = race_common.loadData()
    generator = EloRaceModelGenerator(
        seasonsData, raceResultsData, driversData, constructorsData, enginesData)
    generator.generateModel()
    raceModel = generator.getModel()
    print("Model done")
    return raceModel


def overwriteRaceModelWithNewDrivers(raceModel):
    newDrivers = json.load(open('data/newDrivers.json'))["drivers"]
    newDrivers = {int(did): cid for did, cid in newDrivers.items()}
    for did, cid in newDrivers.items():
        if did < 0:  # Cases when driver doesn't exist in data
            raceModel.drivers[did] = EloDriver(
                "__PLACEHOLDER__", raceModel.constructors[int(cid)])
            raceModel.drivers[did].rating = ROOKIE_DRIVER_RATING
        if not cid == "":
            # Data in newDrivers.json overwrites database
            raceModel.drivers[did].constructor = raceModel.constructors[int(
                cid)]


def calculateGaElos(raceModel, grid, circuit):
    gaElos = []
    for gridPosition, did in enumerate(grid):
        gaElo = raceModel.getGaElo(did, gridPosition, circuit)
        gaElos.append((did, gaElo))
    return gaElos


def generatePercentualPredictions(raceModel, grid, circuit):
    racePredictions = {did: {} for did in grid}
    for i in range(10000):
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
    return racePredictions


raceModel = generateModel()
overwriteRaceModelWithNewDrivers(raceModel)

grid = json.load(open('data/grid.json'))
circuit, circuitName, raceId, year = file_operations.readNextRaceDetails(
    'data/futureRaces.json')

outFile = {}  # The object where we write output
outFile["name"] = circuitName
outFile["year"] = year
outFile["drivers"] = race_common.getDriverDetailsForOutFile(raceModel, grid)

raceModel.addNewTrack(circuit)
gaElos = calculateGaElos(raceModel, grid, circuit)
gaElos.sort(key=lambda x: x[1], reverse=True)
outFile["order"] = [a for (a, b) in gaElos]

outFile["predictions"] = generatePercentualPredictions(
    raceModel, grid, circuit)

# Publish predictions
indexFileName = '{}races/index.json'.format(USER_VARS['predictions_output_folder'])
file_operations.editIndexFile(indexFileName, year, raceId, circuitName)

predictionsFileName = '{}races/{}_afterQuali.json'.format(USER_VARS['predictions_output_folder'], str(raceId))
file_operations.publishPredictions(predictionsFileName, outFile)
