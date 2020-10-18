import pickle
import json

from f1predict.common import common
from f1predict.race.EloModel import EloDriver
from f1predict.race.DataProcessor import DataProcessor


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
    raceModel = processor.getModel()
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

def getRetirementBlame(status):
    if status == "Collision":
        return (1, 0, 0)
    elif status == "Accident":
        return (1, 0, 0)
    elif status == "Engine":
        return (0, 0, 1)
    elif status == "Gearbox":
        return (0, 1, 0)
    elif status == "Hydraulics":
        return (0, 1, 0)
    elif status == "Brakes":
        return (0, 1, 0)
    elif status == "Spun off":
        return (1, 0, 0)
    elif status == "Suspension":
        return (0, 1, 0)
    elif status == "Electrical":
        return (0, 0.5, 0.5)
    elif status == "Power Unit":
        return (0, 0, 1)
    elif status == "Collision damage":
        return (1, 0, 0)
    elif status == "Wheel":
        return (0, 1, 0)
    elif status == "Transmission":
        return (0, 1, 0)
    elif status == "Mechanical":
        return (0, 0.5, 0.5)
    elif status == "Puncture":
        return (0.667, 0.333, 0)
    elif status == "Driveshaft":
        return (0, 1, 0)
    elif status == "Oil leak":
        return (0, 0.5, 0.5)
    elif status == "Tyre":
        return (0, 1, 0)
    elif status == "Fuel pressure":
        return (0, 0.5, 0.5)
    elif status == "Clutch":
        return (0, 1, 0)
    elif status == "Electronics":
        return (0, 0.5, 0.5)
    elif status == "Power loss":
        return (0, 0, 1)
    elif status == "Overheating":
        return (0, 0.5, 0.5)
    elif status == "Throttle":
        return (0, 1, 0)
    elif status == "Wheel nut":
        return (0, 1, 0)
    elif status == "Exhaust":
        return (0, 1, 0)
    elif status == "Steering":
        return (0, 1, 0)
    elif status == "Fuel system":
        return (0, 0.5, 0.5)
    elif status == "Water leak":
        return (0, 1, 0)
    elif status == "Battery":
        return (0, 0, 1)
    elif status == "ERS":
        return (0, 0, 1)
    elif status == "Water pressure":
        return (0, 1, 0)
    elif status == "Rear wing":
        return (0.667, 0.333, 0)
    elif status == "Vibrations":
        return (0.667, 0.333, 0)
    elif status == "Technical":
        return (0, 0.5, 0.5)
    elif status == "Oil pressure":
        return (0, 0.5, 0.5)
    elif status == "Pneumatics":
        return (0, 1, 0)
    elif status == "Turbo":
        return (0, 0, 1)
    elif status == "Front wing":
        return (0.667, 0.333, 0)
    return (0.334, 0.333, 0.333)