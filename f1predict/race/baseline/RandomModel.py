import random


class RandomModel:
    '''Predicts race results randomly'''

    def __init__(self, seasonsData, raceResultsData):
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