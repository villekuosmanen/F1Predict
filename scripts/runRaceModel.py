import json
import copy

from f1predict.common import file_operations
from f1predict.race.raceMonteCarlo import simulateRace
from f1predict.race import utils as race_utils

USER_VARS = file_operations.getUserVariables("user_variables.txt")


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


raceModel = race_utils.generateModel()
race_utils.overwriteRaceModelWithNewDrivers(raceModel)
print("Model done")

grid = json.load(open('data/grid.json'))
circuit, circuitName, raceId, year = file_operations.readNextRaceDetails(
    'data/futureRaces.json')

outFile = {}  # The object where we write output
outFile["name"] = circuitName
outFile["year"] = year
outFile["drivers"] = race_utils.getDriverDetailsForOutFile(raceModel, grid)

raceModel.addNewTrack(circuit)
gaElos = race_utils.calculateGaElos(raceModel, grid, circuit)
gaElos.sort(key=lambda x: x[1], reverse=True)
outFile["order"] = [a for (a, b) in gaElos]

outFile["predictions"] = generatePercentualPredictions(
    raceModel, grid, circuit)

# Publish predictions
indexFileName = '{}races/index.json'.format(
    USER_VARS['predictions_output_folder'])
file_operations.editIndexFile(indexFileName, year, raceId, circuitName)

predictionsFileName = '{}races/{}_afterQuali.json'.format(
    USER_VARS['predictions_output_folder'], str(raceId))
file_operations.publishPredictions(predictionsFileName, outFile)
