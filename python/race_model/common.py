import pickle

from python.common import common


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
