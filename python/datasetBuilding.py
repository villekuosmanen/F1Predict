import json
import random
import pandas as pd
import numpy as np
import math
import copy

from .f1Data import Season
from .f1Data import RaceData
from .f1Models import Engine
from .f1Models import Constructor
from .f1Models import Driver

# Constructs two tables:
#  A table of entries (driverPower, constPower, engPower, track powers...)
#  An array with the scaled times of the entries, on the same order as the entries

k_engine_change = 0.35
k_const_change = 0.33
k_driver_change = 0.189
k_track_impact = 0.20
k_eng_impact = 0.38
k_const_impact = 1.0

k_variance = 0.06  # At the moment, best is 0 (= no randomness)!
k_mistake_variance = 0.0015
k_rookie_pwr = 0.75
k_rookie_variance = 5
k_race_regress_exp = 0.87
k_variance_multiplier_end = 1.5

k_eng_regress = 0.9
k_const_regress = 1
k_driver_regress = 0.74


class F1DataCleaner:
    '''Generates a dataset from statistical data'''

    def __init__(self, seasonsData, qualiResultsData, driversData, constructorsData, enginesData):
        self.seasonsData = seasonsData
        self.qualiResultsData = qualiResultsData
        self.driversData = driversData
        self.constructorsData = constructorsData
        self.enginesData = enginesData

    def constructDataset(self, entries, results):
        # Initializing data structures
        self.drivers = {}  # DriverId, Driver
        self.constructors = {}  # ConstructorId, Constructor
        self.engines = {}  # EngineId, Engine

        # Deviation variables
        globaldev = [None] * 20
        trackdev = {}
        for year, season in self.seasonsData.items():  # Read every season:
            updateModelsForYear(season, self.constructors, self.engines,
                                self.enginesData, self.constructorsData)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.qualiResultsData:
                    qresults = self.qualiResultsData[raceId]
                    addNewDriversAndConstructors(
                        qresults, self.drivers, self.constructors, self.driversData, year)

                    # Scores and qresults need to be in the same, sequential order by score
                    qresults.sort(key=lambda x: x[2])
                    scores = calculateScoresFromResults(
                        qresults, self.drivers, self.constructors, data, globaldev, trackdev)

                    # Add to entries and results
                    if year > 2005:  # Don't use the oldest data in the dataset
                        for index, (driverId, constId, time) in enumerate(qresults):
                            self._addNewCircuitsToEntities(
                                driverId, data.circuitId)

                            entry = self._buildEntry(driverId, data.circuitId)
                            result = scores[index]
                            entries.append(entry)
                            results.append(result)
                    updateModels(qresults, scores, self.constructors,
                                 data.circuitId, self.drivers)
            updateModelsAtEndOfYear(
                season, self.engines, self.constructors, self.drivers)

    def _addNewCircuitsToEntities(self, driverId, circuitId):
        if circuitId not in self.drivers[driverId].trackpwr:
            # TODO maybe change defaults
            self.drivers[driverId].trackpwr[circuitId] = 0
        if circuitId not in self.drivers[driverId].constructor.trackpwr:
            # TODO maybe change defaults
            self.drivers[driverId].constructor.trackpwr[circuitId] = 0
        if circuitId not in self.drivers[driverId].constructor.engine.trackpwr:
            # TODO maybe change defaults
            self.drivers[driverId].constructor.engine.trackpwr[circuitId] = 0

    def _buildEntry(self, driverId, circuitId):
        entry = [
            self.drivers[driverId].pwr,
            self.drivers[driverId].constructor.pwr,
            self.drivers[driverId].constructor.engine.pwr,
            self.drivers[driverId].trackpwr[circuitId],
            self.drivers[driverId].constructor.trackpwr[circuitId],
            self.drivers[driverId].constructor.engine.trackpwr[circuitId]
        ]
        return entry

# Utility functions---------------


def updateModelsAtEndOfYear(season, engines, constructors, drivers):
    # Delete old, unused constructors
    for new, old in season.teamChanges.items():
        del constructors[old]

    # Regress all powers towards the mean
    for (engid, eng) in engines.items():
        eng.pwr *= k_eng_regress
    for (constid, const) in constructors.items():
        const.pwr *= k_const_regress
    for (drivId, driver) in drivers.items():
        driver.pwr *= k_driver_regress
        driver.variance *= k_variance_multiplier_end


def updateModelsForYear(season, constructors, engines, enginesData, constructorsData):
    '''Resolves team name changes'''
    # Updating list of engines and constructors:
    for new, old in season.teamChanges.items():
        constructors[new] = constructors[old]
        constructors[new].name = constructorsData[new]

    for cId, engineId in season.constructorEngines.items():
        # Check that the constructor and engine exist
        if engineId not in engines:
            engines[engineId] = Engine(enginesData[engineId])
        if cId not in constructors:
            constructors[cId] = Constructor(constructorsData[cId], None)
        # Assign it its engine
        constructors[cId].engine = engines[engineId]


def addNewDriversAndConstructors(qresults, drivers, constructors, driversData, year):
    for res in qresults:
        if res[0] not in drivers:
            drivers[res[0]] = Driver(driversData[res[0]], res[1])
            if year > 2003:
                drivers[res[0]].pwr = k_rookie_pwr
                drivers[res[0]].variance = k_rookie_variance
        if drivers[res[0]].constructor is not constructors[res[1]]:
            drivers[res[0]].constructor = constructors[res[1]]


def updateDevValues(dev, circuitId, globaldev, trackdev):
    '''Updates the deviation values by popping the oldest value and inserting the newest to the front'''
    globaldev.pop()  # Removes last item
    globaldev.insert(0, dev)

    if circuitId not in trackdev:
        trackdev[circuitId] = [None] * 6
    trackdev[circuitId].pop()
    trackdev[circuitId].insert(0, dev)


def calculateScoresFromResults(qresults, drivers, constructors, raceData, globaldev, trackdev):
    '''Return a list of standardised quali score values for the quali results.'''
    # Make sure all drivers have been added to the list and their info is correct
    best = qresults[0][2]

    # Only the times. Maintains the same order as the original tuples, so the same index can be used
    times = [((x[2])*100/best) for x in qresults]
    median = np.median(times)
    dev = np.mean(np.abs(times - median))

    # Standardised list
    stdList = [(x - median)/dev for x in times]
    # print(stdList)

    updateDevValues(dev, raceData.circuitId, globaldev, trackdev)
    return [x/(np.median(list(filter(None.__ne__, globaldev))) + np.median(list(filter(None.__ne__, trackdev[raceData.circuitId])))/2)
            for x in stdList]


def updateModels(qresults, scores, constructors, circuitId, drivers):
    # enumerate through results to get list of scores by constructor & engine
    engineScores = {}  # engineId, [list of scores]
    constScores = {}  # constId, [list of scores]
    fillEngineAndConstructorScores(
        qresults, scores, constructors, engineScores, constScores)

    # TODO ALGO
    updateEngineScores(engineScores, circuitId)
    updateConstructorScores(constScores, circuitId)
    updateDriverScores(qresults, drivers, circuitId, scores)


def fillEngineAndConstructorScores(qresults, scores, constructors, engineScores, constScores):
    for i, qres in enumerate(qresults):
        if constructors[qres[1]].engine not in engineScores:
            # Add engine to scores
            engineScores[constructors[qres[1]].engine] = []
        engineScores[constructors[qres[1]].engine].append(scores[i])
        if constructors[qres[1]] not in constScores:
            # Add constructor to scores
            constScores[constructors[qres[1]]] = []
        constScores[constructors[qres[1]]].append(scores[i])


def updateEngineScores(engineScores, circuitId):
    '''Update scores for Engine model objects.'''
    for engine, es in engineScores.items():
        actual = np.mean(es)
        if circuitId not in engine.trackpwr:
            engineExpt = engine.pwr
            engine.trackpwr[circuitId] = 0
        else:
            engineExpt = (engine.pwr + k_track_impact *
                          engine.trackpwr[circuitId]) / (1 + k_track_impact)
        engine.trackpwr[circuitId] += k_engine_change * \
            (actual - engineExpt)*2  # Set track power normally
        engine.pwr += k_engine_change*(actual - engineExpt)


def updateConstructorScores(constScores, circuitId):
    '''Update scores for Constructor model objects.'''
    for const, cs in constScores.items():
        engineExpt = (const.engine.pwr + k_track_impact *
                      const.engine.trackpwr[circuitId]) / (1 + k_track_impact)
        actual = np.mean(cs)
        if circuitId not in const.trackpwr:
            constExpt = (const.pwr + k_eng_impact*engineExpt) / (1)
            # Set track power to be result minus engine effect
            const.trackpwr[circuitId] = 0
        else:
            constExpt = (const.pwr + k_track_impact*const.trackpwr[circuitId] + k_eng_impact*engineExpt
                         ) / (1 + k_track_impact)
        const.trackpwr[circuitId] += k_const_change * \
            (actual - constExpt)*2  # Set track power normally
        const.pwr += k_const_change*(actual - constExpt)


def updateDriverScores(qresults, drivers, circuitId, scores):
    '''Update scores for Driver model objects.'''
    for i, qres in enumerate(qresults):
        constExpt = (
            (drivers[qres[0]].constructor.pwr
             + k_track_impact *
             drivers[qres[0]].constructor.trackpwr[circuitId]
             + k_eng_impact * (
                drivers[qres[0]].constructor.engine.pwr
                + k_track_impact * drivers[qres[0]].constructor.engine.trackpwr[circuitId]))
            / (1 + k_track_impact)
        )
        actual = scores[i]
        if circuitId not in drivers[qres[0]].trackpwr:
            expected = (drivers[qres[0]].pwr + k_const_impact*constExpt) / (1)
            # Set track power to be result minus constructor effect
            drivers[qres[0]].trackpwr[circuitId] = 0
        else:
            expected = (drivers[qres[0]].pwr + k_track_impact*drivers[qres[0]].trackpwr[circuitId]
                        + k_const_impact*constExpt) / (1 + k_track_impact)

        drivers[qres[0]].trackpwr[circuitId] += k_driver_change * \
            (actual - expected)*2
        drivers[qres[0]].pwr += k_driver_change * \
            (actual - expected) * (drivers[qres[0]].variance)**0.45
        drivers[qres[0]].variance **= k_race_regress_exp
