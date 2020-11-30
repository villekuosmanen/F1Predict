import pickle
import json

from f1predict.common import common
from f1predict.race.EloModel import EloDriver
from f1predict.race.DataProcessor import DataProcessor

ROOKIE_DRIVER_RATING = 1820

def loadData():
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
    return seasonsData, raceResultsData, driversData, constructorsData, enginesData


def getDriverDetailsForOutFile(raceModel, driverIDs):
    driversToWrite = {}
    for did in driverIDs:
        driversToWrite[int(did)] = {}
        driversToWrite[int(did)]["name"] = raceModel.drivers[int(did)].name
        driversToWrite[int(did)]["constructor"] = raceModel.drivers[int(
            did)].constructor.name
        driversToWrite[int(did)]["color"] = common.getColor(
            raceModel.drivers[int(did)].constructor.name)
    return driversToWrite

def generateModel():
    seasonsData, raceResultsData, driversData, constructorsData, enginesData = loadData()
    processor = DataProcessor(
        seasonsData, raceResultsData, driversData, constructorsData, enginesData)
    processor.processDataset()
    return processor.getModel()

def overwriteRaceModelWithNewDrivers(raceModel, filename):
    newDrivers = json.load(open(filename))["drivers"]
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