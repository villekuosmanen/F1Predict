import math

GRID_ADJUSTMENT_COEFFICIENT = 20
GA_ELO_INTERCEPT_COEFFICIENT = 0
K_FACTOR = 4
BASE_RETIREMENT_PROBABILITY = 0.1

DRIVER_WEIGHTING = 0.19
CONSTRUCTOR_WEIGHTING = 0.69
ENGINE_WEIGHTING = 0.09
TRACK_WEIGHTING = 0.03


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

        return (self.drivers[driverId].rating * DRIVER_WEIGHTING) + \
            (self.drivers[driverId].constructor.rating * CONSTRUCTOR_WEIGHTING) + \
            (self.drivers[driverId].constructor.engine.rating *
             ENGINE_WEIGHTING) + gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

    def getGaEloWithTrackAlpha(self, driverId, gridPosition, trackId, alphaAdjustment):
        gridAdjustment = (
            self.tracks[trackId] * alphaAdjustment) * self.getGridAdjustment(gridPosition)

        return (self.drivers[driverId].rating)*DRIVER_WEIGHTING + \
            (self.drivers[driverId].constructor.rating)*CONSTRUCTOR_WEIGHTING + \
            (self.drivers[driverId].constructor.engine.rating)*ENGINE_WEIGHTING + \
            (self.drivers[driverId].trackRatings[trackId]*TRACK_WEIGHTING) + \
            gridAdjustment + GA_ELO_INTERCEPT_COEFFICIENT

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
        self.drivers[driverId].trackRatings[trackId] += (adjustment * K_FACTOR)

    def adjustEloRatingConstructor(self, constructor, adjustment):
        constructor.rating += (adjustment * K_FACTOR)

    def adjustEloRatingEngine(self, engine, adjustment):
        engine.rating += (adjustment * K_FACTOR)

    def adjustCircuitAplha(self, alphaAdjustment, trackId):
        self.tracks[trackId] *= alphaAdjustment

    def addNewTrack(self, circuitId):
        if circuitId not in self.tracks:
            self.tracks[circuitId] = 1
        if circuitId not in self.tracksRetirementFactor:
            self.tracksRetirementFactor[circuitId] = BASE_RETIREMENT_PROBABILITY