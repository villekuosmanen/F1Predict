import random

from python import *

import pickle

class F1RaceFromQualiModel:
    '''Predicts race results to be equal to qualifying results'''

    def __init__(self, raceSeasonsData, raceResultsData, qualiResultsData):
        self.seasonsData = seasonsData
        self.raceResultsData = raceResultsData
        self.qualiResultsData = qualiResultsData

    def constructPredictions(self):
        predictions = []

        for year, season in self.seasonsData.items():  # Read every season:
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData and raceId in self.qualiResultsData:
                    qualiResults = self.qualiResultsData[raceId]
                    driver_ids = [x['driverId'] for x in qualiResults]
                    predictions.append(driver_ids)
        return predictions


with open('data/raceSeasonsData.pickle', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/raceResultsData.pickle', 'rb') as handle:
    raceResultsData = pickle.load(handle)
    
with open('data/qualiResultsData.pickle', 'rb') as handle:
    qualiResultsData = pickle.load(handle)

fromQualiModel = F1RaceFromQualiModel(seasonsData, raceResultsData, qualiResultsData)
fromQualiPredictions = fromQualiModel.constructPredictions()

print(fromQualiPredictions)
