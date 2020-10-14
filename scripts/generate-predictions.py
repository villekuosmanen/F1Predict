import pickle
import json
import copy

from f1predict.common import common
from f1predict.common import file_operations
from f1predict.quali import utils as quali_utils
from f1predict.quali.monteCarlo import predictQualiResults
from f1predict.race_model import utils as race_utils
from f1predict.race_model.raceMonteCarlo import simulateRace

USER_VARS = file_operations.getUserVariables("user_variables.txt")

def generatePercentualPredictions(qualiModel, raceModel, driverIds, circuit):
    racePredictions = {did: {} for did in driverIds}
    qualiPredictions = {did: {} for did in driverIds}
    for i in range(10000):
        grid = predictQualiResults(circuit, {did: None for did in driverIds}, qualiModel)
        for pos, did in enumerate(grid):
            if pos not in qualiPredictions[did]:
                qualiPredictions[did][pos] = 0
            qualiPredictions[did][pos] += 1

        # Generate predictions for races
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
    return qualiPredictions, racePredictions


with open('out/trained_quali_model.pickle', 'rb') as handle:
    qualiModel = pickle.load(handle)
quali_utils.overwriteQualiModelWithNewDrivers(qualiModel, 'data/newDrivers.json')

raceModel = race_utils.generateModel()
race_utils.overwriteRaceModelWithNewDrivers(raceModel)

newDrivers = json.load(open('data/newDrivers.json'))["drivers"]
driverIDs = [int(did) for did, cid in newDrivers.items()]
circuit, circuitName, raceId, year = file_operations.readNextRaceDetails(
    'data/futureRaces.json')

outFile = {}  # The object where we write quali output
outFile["name"] = circuitName
outFile["year"] = year
outFile["drivers"] = race_utils.getDriverDetailsForOutFile(qualiModel, driverIDs)
raceOutFile = copy.deepcopy(outFile)  # The object where we write race output

for did in driverIDs:
    qualiModel.addNewCircuit(did, circuit)
predictedOrder = quali_utils.calculateOrder(qualiModel, driverIDs, circuit)
outFile["order"] = predictedOrder

raceModel.addNewTrack(circuit)
gaElos = race_utils.calculateGaElos(raceModel, predictedOrder, circuit)
gaElos.sort(key=lambda x: x[1], reverse=True)
raceOutFile["order"] = [a for (a, b) in gaElos]

qualiPredictions, racePredictions = generatePercentualPredictions(qualiModel, raceModel, driverIDs, circuit)

outFile["predictions"] = qualiPredictions
raceOutFile["predictions"] = racePredictions

# Publish predictions: edit index file
qualiIndexFileName = '{}/index.json'.format(
    USER_VARS['predictions_output_folder'])
file_operations.editIndexFile(qualiIndexFileName, year, raceId, circuitName)

raceIndexFileName = '{}races/index.json'.format(
    USER_VARS['predictions_output_folder'])
file_operations.editIndexFile(raceIndexFileName, year, raceId, circuitName)

# Publish predictions: write out file
qualiPredictionsFileName = '{}/{}.json'.format(
    USER_VARS['predictions_output_folder'], str(raceId))
file_operations.publishPredictions(qualiPredictionsFileName, outFile)

racePredictionsFileName = '{}races/{}.json'.format(
    USER_VARS['predictions_output_folder'], str(raceId))
file_operations.publishPredictions(racePredictionsFileName, raceOutFile)