import random

from python import *

import pickle

class F1RaceRandomModel:
    '''Predicts qualifying results randomly'''

    def __init__(self, raceSeasonsData, raceResultsData):
        self.seasonsData = seasonsData
        self.raceResultsData = raceResultsData

    def constructPredictions(self):
        predictions = []

        for year, season in self.seasonsData.items():  # Read every season:
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData:
                    results = self.raceResultsData[raceId]
                    driver_ids = [x['driverId'] for x in results]
                    random.shuffle(driver_ids)
                    predictions.append(driver_ids)
        return predictions


with open('data/raceSeasonsData.pickle', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/raceResultsData.pickle', 'rb') as handle:
    raceResultsData = pickle.load(handle)

randomModel = F1RaceRandomModel(seasonsData, raceResultsData)
randomPredictions = randomModel.constructPredictions()

print(randomPredictions)
