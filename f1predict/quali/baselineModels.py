import random

from f1predict.common.Season import Season
from f1predict.common.RaceData import RaceData
from f1predict.quali.f1Models import Engine
from f1predict.quali.f1Models import Constructor
from f1predict.quali.f1Models import Driver

class F1ResultsGetter:
    '''Returns results of qualifyings without times'''

    def __init__(self, seasonsData, qualiResultsData):
        self.seasonsData = seasonsData
        self.qualiResultsData = qualiResultsData

    def constructQualiResults(self):
        results = []

        for year, season in self.seasonsData.items():  # Read every season:
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.qualiResultsData:
                    qresults = self.qualiResultsData[raceId]
                    res = [x[0] for x in qresults]
                    results.append(res)
        return results

class F1RandomModel:
    '''Predicts qualifying results randomly'''

    def __init__(self, seasonsData, qualiResultsData):
        self.seasonsData = seasonsData
        self.qualiResultsData = qualiResultsData

    def constructPredictions(self):
        predictions = []

        for year, season in self.seasonsData.items():  # Read every season:
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.qualiResultsData:
                    qresults = self.qualiResultsData[raceId]
                    driver_ids = [x[0] for x in qresults]
                    random.shuffle(driver_ids)
                    predictions.append(driver_ids)
        return predictions

class F1PreviousModel:
    '''Predicts qualifying results based on the results of previous qualifying'''

    def __init__(self, seasonsData, qualiResultsData):
        self.seasonsData = seasonsData
        self.qualiResultsData = qualiResultsData

    def constructPredictions(self):
        predictions = []
        previousQualiResults = []

        for year, season in self.seasonsData.items():  # Read every season:
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.qualiResultsData:
                    qresults = self.qualiResultsData[raceId]
                    driver_ids = [x[0] for x in qresults]

                    prediction = []
                    for driver_id in previousQualiResults:
                        if driver_id in driver_ids:
                            prediction.append(driver_id)

                    unseen_drivers = []
                    for driver_id in driver_ids:
                        if driver_id not in prediction:
                            unseen_drivers.append(driver_id)
                    random.shuffle(unseen_drivers)
                    prediction.extend(unseen_drivers)

                    predictions.append(prediction)
                    qresults.sort(key=lambda x: x[2])
                    previousQualiResults = [x[0] for x in qresults]
        return predictions



