class ResultsGetter:
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