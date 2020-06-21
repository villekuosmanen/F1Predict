import random

from python import *

import pickle

class F1RaceRandomModel:
    '''Predicts race results randomly'''

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

# print(randomPredictions)


class F1RaceResultsGetter:
    '''Returns results of races without times'''

    def __init__(self, seasonsData, raceResultsData):
        self.seasonsData = seasonsData
        self.raceResultsData = raceResultsData

    def constructRaceResults(self):
        racesResults = []

        for year, season in self.seasonsData.items():  # Read every season:
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData:
                    results = self.raceResultsData[raceId]
                    res = [x['driverId'] for x in results]
                    racesResults.append(res)
        return racesResults



# class F1RacePreviousModel:
#     '''Predicts qualifying results based on the results of previous qualifying'''

#     def __init__(self, seasonsData, qualiResultsData):
#         self.seasonsData = seasonsData
#         self.qualiResultsData = qualiResultsData

#     def constructPredictions(self):
#         predictions = []
#         previousQualiResults = []

#         for year, season in self.seasonsData.items():  # Read every season:
#             racesAsList = list(season.races.items())
#             racesAsList.sort(key=lambda x: x[1].round)
#             for raceId, data in racesAsList:
#                 # A single race
#                 if raceId in self.qualiResultsData:
#                     qresults = self.qualiResultsData[raceId]
#                     driver_ids = [x[0] for x in qresults]

#                     prediction = []
#                     for driver_id in previousQualiResults:
#                         if driver_id in driver_ids:
#                             prediction.append(driver_id)

#                     unseen_drivers = []
#                     for driver_id in driver_ids:
#                         if driver_id not in prediction:
#                             unseen_drivers.append(driver_id)
#                     random.shuffle(unseen_drivers)
#                     prediction.extend(unseen_drivers)

#                     predictions.append(prediction)
#                     qresults.sort(key=lambda x: x[2])
#                     previousQualiResults = [x[0] for x in qresults]
#         return predictions