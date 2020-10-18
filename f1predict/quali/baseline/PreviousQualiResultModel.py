import random


class PreviousQualiResultModel:
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