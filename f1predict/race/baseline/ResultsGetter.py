class ResultsGetter:
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
                    if results:
                        results.sort(key=lambda x: (x['position'] is None, x['position']))
                        res = [x['driverId'] for x in results]
                        racesResults.append(res)
        return racesResults