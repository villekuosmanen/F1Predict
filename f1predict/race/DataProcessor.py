import statistics

from f1predict.race.EloModel import EloModel, EloDriver, EloConstructor, EloEngine

RETIREMENT_PENALTY = -1.8
FINISHING_BONUS = 0.1
BASE_RETIREMENT_PROBABILITY = 0.1
RETIREMENT_PROBABILITY_CHANGE_TRACK = 0.33
RETIREMENT_PROBABILITY_CHANGE_DRIVER = 0.10
ROOKIE_DRIVER_RATING = 1820

class DataProcessor:
    def __init__(self, seasonsData, raceResultsData, driversData, constructorsData, enginesData):
        self.seasonsData = seasonsData
        self.raceResultsData = raceResultsData
        self.driversData = driversData
        self.constructorsData = constructorsData
        self.enginesData = enginesData
        self.model = None

    def processDataset(self):
        self.model = EloModel({}, {}, {}, {})
        self.predictions = []
        for year, season in self.seasonsData.items():  # Read every season:
            self._updateModelsForYear(season)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)

            for raceId, data in racesAsList:
                if raceId in self.raceResultsData and self.raceResultsData[raceId]:
                    results = self.raceResultsData[raceId]
                    self._addNewDriversAndConstructors(results, year)
                    self.model.addNewTrack(data.circuitId)

                    gaElos = {}
                    classified = []
                    retired = []
                    for index, res in enumerate(results):
                        self._addNewTracksToEntities(res["driverId"], data.circuitId)
                        gaElos[res["driverId"]] = self.model.getGaElo(
                            res["driverId"], res["grid"], data.circuitId)
                        if res["position"] is None:
                            retired.append((res["driverId"], res["status"]))
                        else:
                            classified.append(res["driverId"])

                    # Generate predictions:
                    sortedGaElos = [(driverId, gaElo) for (driverId, gaElo) in gaElos.items()]
                    sortedGaElos.sort(key=lambda x: x[1], reverse=True)
                    if sortedGaElos:    # TODO is this if-check necessary?
                        self.predictions.append([x[0] for x in sortedGaElos])

                    # Adjust models based on race results
                    eloAdjustments, alphaAdjustment = self._calculateTrackAlphaAdjustmentAndBestEloAdjustments(
                        classified, results, data.circuitId)
                    self._adjustEloRatings(classified, retired, eloAdjustments, data.circuitId)
                    self._adjustRetirementFactors(retired, classified, data.circuitId)
                    self.model.adjustCircuitAplha(
                        alphaAdjustment, data.circuitId)


    # Returns the generated EloModel from the last processing, or an empty model if the function was not called yet
    def getModel(self):
        return self.model

    # Returns a list of all generated predictions from the last processing
    # Throws an exception if called before processing a dataset
    def getPredictions(self):
        if self.predictions == None:
            raise AssertionError(
                "Predictions not generated yet! Call <processDataset()> before calling me.")
        return self.predictions

    def _updateModelsForYear(self, season):
        '''Resolves team name changes'''
        # Updating list of engines and constructors:
        for new, old in season.teamChanges.items():
            self.model.constructors[new] = self.model.constructors[old]
            self.model.constructors[new].name = self.constructorsData[new]

        for cId, engineId in season.constructorEngines.items():
            # Check that the constructor and engine exist
            if engineId not in self.model.engines:
                self.model.engines[engineId] = EloEngine(
                    self.enginesData[engineId])
            if cId not in self.model.constructors:
                self.model.constructors[cId] = EloConstructor(
                    self.constructorsData[cId], None)
            # Assign it its engine
            self.model.constructors[cId].engine = self.model.engines[engineId]

    def _updateModelsAtEndOfYear(self, season):
        # Delete old, unused constructors
        for new, old in season.teamChanges.items():
            del self.model.constructors[old]

        # Regress all powers towards the mean
        # TODO

    def _addNewTracksToEntities(self, driverId, trackId):
        if trackId not in self.model.drivers[driverId].trackRatings:
            # TODO maybe change defaults
            self.model.drivers[driverId].trackRatings[trackId] = 2200
        if trackId not in self.model.drivers[driverId].constructor.trackRatings:
            # TODO maybe change defaults
            self.model.drivers[driverId].constructor.trackRatings[trackId] = 2200
        if trackId not in self.model.drivers[driverId].constructor.engine.trackRatings:
            # TODO maybe change defaults
            self.model.drivers[driverId].constructor.engine.trackRatings[trackId] = 2200

    def _addNewDriversAndConstructors(self, resultsForRace, year):
        for res in resultsForRace:
            if res["driverId"] not in self.model.drivers:
                self.model.drivers[res["driverId"]] = EloDriver(
                    self.driversData[res["driverId"]], res["constructorId"])
                if year > 2003:
                    self.model.drivers[res["driverId"]
                                       ].rating = ROOKIE_DRIVER_RATING
            if self.model.drivers[res["driverId"]].constructor is not self.model.constructors[res["constructorId"]]:
                self.model.drivers[res["driverId"]
                                   ].constructor = self.model.constructors[res["constructorId"]]

    def _calculateTrackAlphaAdjustmentAndBestEloAdjustments(self, driverIDs, resultsForRace, circuitId):
        eloAdjustments = ()
        eloAdjustmentsSum = None
        bestAdjustment = 0
        adjustments = [0.9, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98,
                       0.99, 1, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1]
        for alphaAdjustment in adjustments:
            results = {}
            gaElos = {}
            for index, res in enumerate(resultsForRace):
                results[res["driverId"]] = res["position"]
                gaElos[res["driverId"]] = self.model.getGaEloWithTrackAlpha(
                    res["driverId"], res["grid"], circuitId, alphaAdjustment)
            curEloAdjustments = self._calculateEloAdjustments(driverIDs, gaElos, results)
            curEloAdjustmentsSum = 0
            curEloAdjustmentsSum += statistics.mean(map(abs, curEloAdjustments[0].values()))
            curEloAdjustmentsSum += statistics.mean(map(abs, curEloAdjustments[1].values()))
            curEloAdjustmentsSum += statistics.mean(map(abs, curEloAdjustments[2].values()))

            if not eloAdjustmentsSum or curEloAdjustmentsSum < eloAdjustmentsSum:
                eloAdjustmentsSum = curEloAdjustmentsSum
                eloAdjustments = curEloAdjustments
                bestAdjustment = alphaAdjustment
        return eloAdjustments, bestAdjustment

    def _calculateEloAdjustments(self, driverIDs, gaElos, results):
        driverAdjustments = {}
        engineAdjustments = {}
        constructorAdjustments = {}
        for i in range(len(driverIDs)):
            for k in range(i+1, len(driverIDs)):
                if driverIDs[i] not in driverAdjustments:
                    driverAdjustments[driverIDs[i]] = 0
                if driverIDs[k] not in driverAdjustments:
                    driverAdjustments[driverIDs[k]] = 0

                if self.model.drivers[driverIDs[i]].constructor not in constructorAdjustments:
                    constructorAdjustments[self.model.drivers[driverIDs[i]].constructor] = 0
                if self.model.drivers[driverIDs[k]].constructor not in constructorAdjustments:
                    constructorAdjustments[self.model.drivers[driverIDs[k]].constructor] = 0

                if self.model.drivers[driverIDs[i]].constructor.engine not in engineAdjustments:
                    engineAdjustments[self.model.drivers[driverIDs[i]
                                                         ].constructor.engine] = 0
                if self.model.drivers[driverIDs[k]].constructor.engine not in engineAdjustments:
                    engineAdjustments[self.model.drivers[driverIDs[k]
                                                         ].constructor.engine] = 0

                headToHeadResult = 1 if results[driverIDs[i]] < results[driverIDs[k]] else 0
                expectedScore = self.model.getExpectedScore(
                    gaElos[driverIDs[i]], gaElos[driverIDs[k]])
                driverAdjustments[driverIDs[i]] += headToHeadResult - expectedScore
                driverAdjustments[driverIDs[k]] += expectedScore - headToHeadResult

                constructorAdjustments[self.model.drivers[driverIDs[i]
                    ].constructor] += headToHeadResult - expectedScore
                constructorAdjustments[self.model.drivers[driverIDs[k]
                    ].constructor] += expectedScore - headToHeadResult

                engineAdjustments[self.model.drivers[driverIDs[i]
                    ].constructor.engine] += headToHeadResult - expectedScore
                engineAdjustments[self.model.drivers[driverIDs[k]
                    ].constructor.engine] += expectedScore - headToHeadResult

        return (driverAdjustments, constructorAdjustments, engineAdjustments)

    def _adjustEloRatings(self, classified, retired, eloAdjustments, circuitId):
        for driverId in classified:
            self.model.adjustEloRating(
                driverId, eloAdjustments[0][driverId] + FINISHING_BONUS, circuitId)
        for (driverId, _) in retired:
            self.model.adjustEloRating(
                driverId, RETIREMENT_PENALTY, circuitId)

        for constructor in eloAdjustments[1]:
            self.model.adjustEloRatingConstructor(
                constructor, eloAdjustments[1][constructor])

        for engine in eloAdjustments[2]:
            self.model.adjustEloRatingEngine(
                engine, eloAdjustments[2][engine])

    def _adjustRetirementFactors(self, retired, classified, circuitID):
        const_retirements = {}
        eng_retirements = {}
        all_retirements = []
        
        # Process drivers who were classified in the race
        for driverID in classified:
            if self.model.drivers[driverID].constructor not in const_retirements:
                const_retirements[self.model.drivers[driverID].constructor] = []
            if self.model.drivers[driverID].constructor.engine not in eng_retirements:
                eng_retirements[self.model.drivers[driverID].constructor.engine] = []

            all_retirements.append(0)
            self.model.drivers[driverID].retirementProbability *= 1-RETIREMENT_PROBABILITY_CHANGE_DRIVER
            const_retirements[self.model.drivers[driverID].constructor].append(0)
            eng_retirements[self.model.drivers[driverID].constructor.engine].append(0)

        # Process drivers who retired from the race    
        for (driverID, retirementReason) in retired:
            if self.model.drivers[driverID].constructor not in const_retirements:
                const_retirements[self.model.drivers[driverID].constructor] = []
            if self.model.drivers[driverID].constructor.engine not in eng_retirements:
                eng_retirements[self.model.drivers[driverID].constructor.engine] = []

            all_retirements.append(1)
            blame = getRetirementBlame(retirementReason)
            self.model.drivers[driverID].retirementProbability = (3 * blame[0] * RETIREMENT_PROBABILITY_CHANGE_DRIVER) + \
                (1-RETIREMENT_PROBABILITY_CHANGE_DRIVER) * self.model.drivers[driverID].retirementProbability
            const_retirements[self.model.drivers[driverID].constructor].append(blame[1])
            eng_retirements[self.model.drivers[driverID].constructor.engine].append(blame[2])

        # Adjust overall retirement factor    
        self.model.overallRetirementProbability = statistics.mean(all_retirements) * \
                RETIREMENT_PROBABILITY_CHANGE_DRIVER + (1-RETIREMENT_PROBABILITY_CHANGE_DRIVER) \
                * self.model.overallRetirementProbability
        
        # Adjust track retirement factors
        if circuitID not in self.model.tracksRetirementFactor:
            self.model.tracksRetirementFactor[circuitID] = BASE_RETIREMENT_PROBABILITY
        oldValue = self.model.tracksRetirementFactor[circuitID]
        self.model.tracksRetirementFactor[circuitID] += (statistics.mean(all_retirements) -
            oldValue) * RETIREMENT_PROBABILITY_CHANGE_TRACK
        
        # Adjust constructor factors
        for constructor, blames in const_retirements.items():
            newValue = statistics.mean(blames)
            constructor.retirementProbability = (3 * newValue * RETIREMENT_PROBABILITY_CHANGE_DRIVER) + \
                (1-RETIREMENT_PROBABILITY_CHANGE_DRIVER) * constructor.retirementProbability

        # Adjust engine factors
        for engine, blames in eng_retirements.items():
            newValue = statistics.mean(blames)
            engine.retirementProbability = (3 * newValue * RETIREMENT_PROBABILITY_CHANGE_DRIVER) + \
                (1-RETIREMENT_PROBABILITY_CHANGE_DRIVER) * engine.retirementProbability

def getRetirementBlame(status):
    if status == "Collision":
        return (1, 0, 0)
    elif status == "Accident":
        return (1, 0, 0)
    elif status == "Engine":
        return (0, 0, 1)
    elif status == "Gearbox":
        return (0, 1, 0)
    elif status == "Hydraulics":
        return (0, 1, 0)
    elif status == "Brakes":
        return (0, 1, 0)
    elif status == "Spun off":
        return (1, 0, 0)
    elif status == "Suspension":
        return (0, 1, 0)
    elif status == "Electrical":
        return (0, 0.5, 0.5)
    elif status == "Power Unit":
        return (0, 0, 1)
    elif status == "Collision damage":
        return (1, 0, 0)
    elif status == "Wheel":
        return (0, 1, 0)
    elif status == "Transmission":
        return (0, 1, 0)
    elif status == "Mechanical":
        return (0, 0.5, 0.5)
    elif status == "Puncture":
        return (0.667, 0.333, 0)
    elif status == "Driveshaft":
        return (0, 1, 0)
    elif status == "Oil leak":
        return (0, 0.5, 0.5)
    elif status == "Tyre":
        return (0, 1, 0)
    elif status == "Fuel pressure":
        return (0, 0.5, 0.5)
    elif status == "Clutch":
        return (0, 1, 0)
    elif status == "Electronics":
        return (0, 0.5, 0.5)
    elif status == "Power loss":
        return (0, 0, 1)
    elif status == "Overheating":
        return (0, 0.5, 0.5)
    elif status == "Throttle":
        return (0, 1, 0)
    elif status == "Wheel nut":
        return (0, 1, 0)
    elif status == "Exhaust":
        return (0, 1, 0)
    elif status == "Steering":
        return (0, 1, 0)
    elif status == "Fuel system":
        return (0, 0.5, 0.5)
    elif status == "Water leak":
        return (0, 1, 0)
    elif status == "Battery":
        return (0, 0, 1)
    elif status == "ERS":
        return (0, 0, 1)
    elif status == "Water pressure":
        return (0, 1, 0)
    elif status == "Rear wing":
        return (0.667, 0.333, 0)
    elif status == "Vibrations":
        return (0.667, 0.333, 0)
    elif status == "Technical":
        return (0, 0.5, 0.5)
    elif status == "Oil pressure":
        return (0, 0.5, 0.5)
    elif status == "Pneumatics":
        return (0, 1, 0)
    elif status == "Turbo":
        return (0, 0, 1)
    elif status == "Front wing":
        return (0.667, 0.333, 0)
    return (0.334, 0.333, 0.333)