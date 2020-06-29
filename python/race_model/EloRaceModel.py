GRID_ADJUSTMENT_COEFFICIENT = 40
GA_ELO_INTERCEPT_COEFFICIENT = 0
K_FACTOR = 8
RETIREMENT_PENALTY = -0.8
FINISHING_BONUS = 0.1
ROOKIE_DRIVER_RATING = 1800

from python.f1Models import Engine, Constructor

class EloDriver:
    def __init__(self, name, constructor):
        self.name = name
        self.trackRatings = {}
        self.constructor = constructor
        self.rating = 2200  # Default rating
    def changeConstrucutor(self, constructor):
        self.constructor = constructor

class EloRaceModel:
    def __init__(self, drivers, constructors, engines, tracks):
        self.drivers = drivers
        # TODO make it cover not only drivers
        self.constructors = constructors
        self.engines = engines

        self.tracks = tracks

    def getGaElo(self, driverId, gridPosition, trackId):
        gridAdjustment = self.tracks[trackId] * self.getGridAdjustment(gridPosition)
        return self.drivers[driverId].rating + gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getGridAdjustment(self, gridPosition):
        return (10.5 - gridPosition) * GRID_ADJUSTMENT_COEFFICIENT

    def getExpectedScore(self, a, b):
        '''Returns a's expected score against b. A float value between 0 and 1'''
        return 1 / (1 + 10 ** ((b - a) / 400))

    def adjustEloRating(self, driverId, adjustment):
        self.drivers[driverId].rating += (adjustment * K_FACTOR) # TODO check if this is correct

class EloRaceModelGenerator:
    def __init__(self, seasonsData, raceResultsData, driversData, constructorsData, enginesData):
        self.seasonsData = seasonsData
        self.raceResultsData = raceResultsData
        self.driversData = driversData
        self.constructorsData = constructorsData
        self.enginesData = enginesData
        self.model = None

    def getModel(self):
        if not self.model:
            raise ValueError("Model not generated yet")
        return self.model

    def generateModel(self):
        self.model = EloRaceModel({}, {}, {}, {})
        for year, season in self.seasonsData.items():  # Read every season:
            self._updateModelsForYear(season)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)

            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData:
                    resultsForRace = self.raceResultsData[raceId]
                    self._addNewDriversAndConstructors(resultsForRace, year)
                    self._addNewTrack(data.circuitId)

                    results = {}
                    gaElos = {}
                    for index, res in enumerate(resultsForRace):
                        results[res["driverId"]] = res["position"]
                        gaElos[res["driverId"]] = self.model.getGaElo(res["driverId"], res["grid"], data.circuitId)

                    # For each matchup, calculate expected score and real score. Put results to special data structure
                    driverIds = [x["driverId"] for x in resultsForRace]
                    eloAdjustments = self._calculateEloAdjustments(driverIds, gaElos, results)
                    for driverId in driverIds:
                        if results[driverId] is None:
                            self.model.adjustEloRating(driverId, RETIREMENT_PENALTY)
                        self.model.adjustEloRating(driverId, eloAdjustments[driverId] + FINISHING_BONUS)
                    # TODO Adjust circuit ALPHA
        
    def generatePredictions(self):
        self.model = EloRaceModel({}, {}, {}, {})
        predictions = []
        for year, season in self.seasonsData.items():  # Read every season:
            self._updateModelsForYear(season)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)

            for raceId, data in racesAsList:
                # A single race
                if raceId in self.raceResultsData:
                    resultsForRace = self.raceResultsData[raceId]
                    self._addNewDriversAndConstructors(resultsForRace, year)
                    self._addNewTrack(data.circuitId)

                    results = {}
                    gaElos = {}
                    for index, res in enumerate(resultsForRace):
                        results[res["driverId"]] = res["position"]
                        gaElos[res["driverId"]] = self.model.getGaElo(res["driverId"], res["grid"], data.circuitId)

                    # Generate predictions:
                    sortedGaElos = [(driverId, gaElo) for (driverId, gaElo) in gaElos.items()]
                    sortedGaElos.sort(key=lambda x: x[1], reverse=True)
                    if sortedGaElos:
                        predictions.append([x[0] for x in sortedGaElos])

                    # For each matchup, calculate expected score and real score. Put results to special data structure
                    driverIds = [x["driverId"] for x in resultsForRace]
                    eloAdjustments = self._calculateEloAdjustments(driverIds, gaElos, results)
                    for driverId in driverIds:
                        if results[driverId] is None:
                            self.model.adjustEloRating(driverId, RETIREMENT_PENALTY)
                        self.model.adjustEloRating(driverId, eloAdjustments[driverId] + FINISHING_BONUS)
                    # TODO Adjust circuit ALPHA
        return predictions

    def _updateModelsForYear(self, season):
        '''Resolves team name changes'''
        # Updating list of engines and constructors:
        for new, old in season.teamChanges.items():
            self.model.constructors[new] = self.model.constructors[old]
            self.model.constructors[new].name = self.constructorsData[new]

        for cId, engineId in season.constructorEngines.items():
            # Check that the constructor and engine exist
            if engineId not in self.model.engines:
                self.model.engines[engineId] = Engine(self.enginesData[engineId])
            if cId not in self.model.constructors:
                self.model.constructors[cId] = Constructor(self.constructorsData[cId], None)
            # Assign it its engine
            self.model.constructors[cId].engine = self.model.engines[engineId]

    def _updateModelsAtEndOfYear(self, season):
        # Delete old, unused constructors
        for new, old in season.teamChanges.items():
            del self.model.constructors[old]

        # Regress all powers towards the mean
        # TODO

    def _addNewDriversAndConstructors(self, resultsForRace, year):
        for res in resultsForRace:
            if res["driverId"] not in self.model.drivers:
                self.model.drivers[res["driverId"]] = EloDriver(self.driversData[res["driverId"]], res["constructorId"])
                if year > 2003:
                    self.model.drivers[res["driverId"]].rating = ROOKIE_DRIVER_RATING
            if self.model.drivers[res["driverId"]].constructor is not self.model.constructors[res["constructorId"]]:
                self.model.drivers[res["driverId"]].constructor = self.model.constructors[res["constructorId"]]

    def _addNewTrack(self, circuitId):
        if circuitId not in self.model.tracks:
            self.model.tracks[circuitId] = 1

    def _calculateEloAdjustments(self, driverIds, gaElos, results):
        eloAdjustments = {}
        for i in range(len(driverIds)):
            for k in range(i+1, len(driverIds)):
                if driverIds[i] not in eloAdjustments:
                    eloAdjustments[driverIds[i]] = 0
                if driverIds[k] not in eloAdjustments:
                    eloAdjustments[driverIds[k]] = 0
                if results[driverIds[i]] is not None and results[driverIds[k]] is not None:
                    headToHeadResult = 1 if results[driverIds[i]] < results[driverIds[k]] else 0
                    expectedScore = self.model.getExpectedScore(gaElos[driverIds[i]], gaElos[driverIds[k]])
                    eloAdjustments[driverIds[i]] += headToHeadResult - expectedScore
                    eloAdjustments[driverIds[k]] += expectedScore - headToHeadResult
        return eloAdjustments
    