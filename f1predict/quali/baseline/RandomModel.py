import random


class RandomModel:
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