import random


class QualiOrderModel:
    '''Predicts race results to be equal to qualifying results'''

    def __init__(self, seasonsData, raceResultsData, qualiResultsData):
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
                if raceId in self.raceResultsData:
                    results = self.raceResultsData[raceId]
                    if results:
                        this_pred = []
                        no_quali = []
                        results.sort(key=lambda x: x['grid'])
                        for x in results:
                            if x['grid']:
                                this_pred.append(x['driverId'])
                            else:
                                no_quali.append(x['driverId'])
                        random.shuffle(no_quali)
                        this_pred += no_quali
                        predictions.append(this_pred)
        return predictions