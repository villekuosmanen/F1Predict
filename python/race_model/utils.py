import pickle
import json

from python.common import common
from python.race_model.EloRaceModel import EloRaceModelGenerator, EloRaceModel, EloDriver


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
    generator = EloRaceModelGenerator(
        seasonsData, raceResultsData, driversData, constructorsData, enginesData)
    generator.generateModel()
    raceModel = generator.getModel()
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
