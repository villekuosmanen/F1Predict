import math

GRID_ADJUSTMENT_COEFFICIENT = 22
GA_ELO_INTERCEPT_COEFFICIENT = 0
K_FACTOR = 4
K_FACTOR_TRACK = 8
BASE_RETIREMENT_PROBABILITY = 0.1

FIRST_TRACK_RATING = 1820

DRIVER_WEIGHTING = 0.12
CONSTRUCTOR_WEIGHTING = 0.52
ENGINE_WEIGHTING = 0.36
TRACK_WEIGH_SHARE = 0.00    # NOTE: Does not improve performance, so it's turned off for now


class EloDriver:
    def __init__(self, name, constructor):
        self.name = name
        self.constructor = constructor
        self.rating = 2200  # Default rating
        self.trackRatings = {}
        self.retirementProbability = BASE_RETIREMENT_PROBABILITY

    def changeConstructor(self, constructor):
        self.constructor = constructor


class EloConstructor:
    def __init__(self, name, engine):
        self.name = name
        self.engine = engine
        self.rating = 2200  # Default rating
        self.trackRatings = {}
        self.retirementProbability = BASE_RETIREMENT_PROBABILITY


class EloEngine:
    def __init__(self, name):
        self.name = name
        self.rating = 2200  # Default rating
        self.trackRatings = {}
        self.retirementProbability = BASE_RETIREMENT_PROBABILITY


class EloModel:
    def __init__(self, drivers, constructors, engines, tracks):
        self.drivers = drivers
        self.constructors = constructors
        self.engines = engines
        self.tracks = tracks
        self.tracksRetirementFactor = {}
        self.overallRetirementProbability = BASE_RETIREMENT_PROBABILITY

    def getGaElo(self, driverId, gridPosition, trackId):
        gridAdjustment = self.tracks[trackId] * \
            self.getGridAdjustment(gridPosition)

        return (self.getDriverRating(driverId, trackId) * DRIVER_WEIGHTING) + \
            (self.getConstructorRating(driverId, trackId) * CONSTRUCTOR_WEIGHTING) + \
            (self.getEngineRating(driverId, trackId) * ENGINE_WEIGHTING) + \
            gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getGaEloWithTrackAlpha(self, driverId, gridPosition, trackId, alphaAdjustment):
        gridAdjustment = (
            self.tracks[trackId] * alphaAdjustment) * self.getGridAdjustment(gridPosition)

        return (self.getDriverRating(driverId, trackId) * DRIVER_WEIGHTING) + \
            (self.getConstructorRating(driverId, trackId) * CONSTRUCTOR_WEIGHTING) + \
            (self.getEngineRating(driverId, trackId) * ENGINE_WEIGHTING) + \
            gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getDriverRating(self, driverId, trackId):
        return self.drivers[driverId].rating * (1-TRACK_WEIGH_SHARE) + \
            self.drivers[driverId].trackRatings[trackId] * TRACK_WEIGH_SHARE

    def getConstructorRating(self, driverId, trackId):
        return self.drivers[driverId].constructor.rating * (1-TRACK_WEIGH_SHARE) + \
            self.drivers[driverId].constructor.trackRatings[trackId] * TRACK_WEIGH_SHARE

    def getEngineRating(self, driverId, trackId):
        return self.drivers[driverId].constructor.engine.rating * (1-TRACK_WEIGH_SHARE) + \
            self.drivers[driverId].constructor.engine.trackRatings[trackId] * TRACK_WEIGH_SHARE

    def getRetirementProbability(self, trackId, driverID):
        return (self.overallRetirementProbability + 
            self.tracksRetirementFactor[trackId] + 
            self.drivers[driverID].retirementProbability + 
            self.drivers[driverID].constructor.retirementProbability + 
            self.drivers[driverID].constructor.engine.retirementProbability) / 5

    def getGridAdjustment(self, gridPosition):
        return (9.5 - gridPosition) * GRID_ADJUSTMENT_COEFFICIENT

    def getExpectedScore(self, a, b):
        '''Returns a's expected score against b. A float value between 0 and 1'''
        # This is the mathematical formula for calculating expected score in Elo ranking
        # See Wikipedia article for more details
        return 1 / (1 + 10 ** ((b - a) / 400))

    def adjustEloRating(self, driverId, adjustment, trackId):
        self.drivers[driverId].rating += (adjustment * K_FACTOR)
        self.drivers[driverId].trackRatings[trackId] += (adjustment * K_FACTOR_TRACK)

    def adjustEloRatingConstructor(self, constructor, adjustment, trackId):
        constructor.rating += (adjustment * K_FACTOR)
        constructor.trackRatings[trackId] += (adjustment * K_FACTOR_TRACK)

    def adjustEloRatingEngine(self, engine, adjustment, trackId):
        engine.rating += (adjustment * K_FACTOR)
        engine.trackRatings[trackId] += (adjustment * K_FACTOR_TRACK)

    def adjustCircuitAplha(self, alphaAdjustment, trackId):
        self.tracks[trackId] *= alphaAdjustment

    def addNewCircuit(self, circuitId):
        if circuitId not in self.tracks:
            self.tracks[circuitId] = 1
        if circuitId not in self.tracksRetirementFactor:
            self.tracksRetirementFactor[circuitId] = BASE_RETIREMENT_PROBABILITY

    def addNewCircuitToParticipant(self, driverId, trackId):
        if trackId not in self.drivers[driverId].trackRatings:
            # TODO maybe change defaults
            self.drivers[driverId].trackRatings[trackId] = FIRST_TRACK_RATING
        if trackId not in self.drivers[driverId].constructor.trackRatings:
            # TODO maybe change defaults
            self.drivers[driverId].constructor.trackRatings[trackId] = FIRST_TRACK_RATING
        if trackId not in self.drivers[driverId].constructor.engine.trackRatings:
            # TODO maybe change defaults
            self.drivers[driverId].constructor.engine.trackRatings[trackId] = FIRST_TRACK_RATING