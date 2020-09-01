GRID_ADJUSTMENT_COEFFICIENT = 40
GA_ELO_INTERCEPT_COEFFICIENT = 0
K_FACTOR = 8
RETIREMENT_PENALTY = -0.8
FINISHING_BONUS = 0.1
ROOKIE_DRIVER_RATING = 1800


DRIVER_WEIGHTING = 0.19
CONSTRUCTOR_WEIGHTING = 0.69
ENGINE_WEIGHTING = 0.09
TRACK_WEIGHTING = 0.03

from python.f1Models import Engine, Constructor

class EloDriver:
    def __init__(self, name, constructor):
        self.name = name
        self.trackRatings = {}
        self.constructor = constructor
        self.rating = 2200  # Default rating
    def changeConstructor(self, constructor): # Spelling mistake
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

        return (self.drivers[driverId].rating)*DRIVER_WEIGHTING + (self.drivers[driverId].constructor.rating)*CONSTRUCTOR_WEIGHTING + (self.drivers[driverId].constructor.engine.rating)*ENGINE_WEIGHTING + (self.drivers[driverId].trackRatings[trackId]*TRACK_WEIGHTING) + gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getGridAdjustment(self, gridPosition):
        return (10.5 - gridPosition) * GRID_ADJUSTMENT_COEFFICIENT

    def getExpectedScore(self, a, b):
        '''Returns a's expected score against b. A float value between 0 and 1'''
        return 1 / (1 + 10 ** ((b - a) / 400))

    def adjustEloRating(self, driverId, adjustment, trackId):
        self.drivers[driverId].rating += (adjustment * K_FACTOR)  # TODO check if this is correct
        self.drivers[driverId].trackRatings[trackId] += (adjustment * K_FACTOR)

    def adjustEloRatingConstructor(self, constructor, adjustment):
        constructor.rating += (adjustment * K_FACTOR) # TODO check if this is correct

    def adjustEloRatingEngine(self, engine, adjustment):
        engine.rating += (adjustment * K_FACTOR)  # TODO check if this is correct

    def _addNewTracksToEntities(self, driverId, trackId):
        if trackId not in self.drivers[driverId].trackRatings[trackId]:
            # TODO maybe change defaults
            self.drivers[driverId].trackRatings[trackId] = 2200
        if trackId not in self.drivers[driverId].constructor.trackRatings:
            # TODO maybe change defaults
            self.drivers[driverId].constructor.trackRatings[trackId] = 2200
        if trackId not in self.drivers[driverId].constructor.engine.trackRatings:
            # TODO maybe change defaults
            self.drivers[driverId].constructor.engine.trackRatings[trackId] = 2200
        
    
        
class EloConstructor:
    def __init__(self, name, engine):
        self.name = name
        self.engine = engine
        self.trackRatings = {}

class EloEngine:
    def __init__(self, name):
        self.name = name
        self.trackRatings = {}
        

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
                    # self._addNewTrack(data.circuitId)
                    self._addNewTracksToEntities(data.trackId)

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
                        self.model.adjustEloRating(driverId, eloAdjustments[0][driverId] + FINISHING_BONUS)

                    for constructor in eloAdjustments[1]:
                        self.model.adjustEloRatingConstructor(constructor, eloAdjustments[1][constructor] + FINISHING_BONUS)
                    
                    for engine in eloAdjustments[2]:
                        self.model.adjustEloRatingConstructor(engine, eloAdjustments[2][engine] + FINISHING_BONUS)
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
                self.model.engines[engineId] = EloEngine(self.enginesData[engineId])
            if cId not in self.model.constructors:
                self.model.constructors[cId] = EloConstructor(self.constructorsData[cId], None)
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
        driverAdjustments = {}
        engineAdjustments = {}
        constructorAdjustments = {}
        for i in range(len(driverIds)):
            for k in range(i+1, len(driverIds)):
                if driverIds[i] not in driverAdjustments:
                    driverAdjustments[driverIds[i]] = 0
                if driverIds[k] not in driverAdjustments:
                    driverAdjustments[driverIds[k]] = 0

                if self.model.drivers[driverIds[i]].constructor not in constructorAdjustments:
                    constructorAdjustments[self.model.drivers[driverIds[i]].constructor] = 0
                if self.model.drivers[driverIds[k]].constructor not in constructorAdjustments:
                    constructorAdjustments[self.model.drivers[driverIds[k]].constructor] = 0

                if self.model.drivers[driverIds[i]].constructor.engine not in engineAdjustments:
                    engineAdjustments[self.model.drivers[driverIds[i]].constructor.engine] = 0
                if self.model.drivers[driverIds[k]].constructor.engine not in engineAdjustments:
                    engineAdjustments[self.model.drivers[driverIds[k]].constructor.engine] = 0

                if results[driverIds[i]] is not None and results[driverIds[k]] is not None:
                    headToHeadResult = 1 if results[driverIds[i]] < results[driverIds[k]] else 0
                    expectedScore = self.model.getExpectedScore(gaElos[driverIds[i]], gaElos[driverIds[k]])
                    driverAdjustments[driverIds[i]] += headToHeadResult - expectedScore
                    driverAdjustments[driverIds[k]] += expectedScore - headToHeadResult

                    constructorAdjustments[self.model.drivers[driverIds[i]].constructor] += headToHeadResult - expectedScore
                    constructorAdjustments[self.model.drivers[driverIds[k]].constructor] += expectedScore - headToHeadResult

                    engineAdjustments[self.model.drivers[driverIds[i]].constructor.engine] += headToHeadResult - expectedScore
                    engineAdjustments[self.model.drivers[driverIds[k]].constructor.engine] += expectedScore - headToHeadResult

        return (driverAdjustments, constructorAdjustments, engineAdjustments)