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

class F1DataCleaner:
    '''Generates a dataset from statistical data'''

    def __init__(self, seasonsData, qualiResultsData, driversData, constructorsData, enginesData):
        self.seasonsData = seasonsData
        self.qualiResultsData = qualiResultsData
        self.driversData = driversData
        self.constructorsData = constructorsData
        self.enginesData = enginesData
        self._initialiseConstants()

    def _initialiseConstants(self):
        self.k_engine_change = 0.35
        self.k_const_change = 0.33
        self.k_driver_change = 0.189
        self.k_track_impact = 0.20
        self.k_eng_impact = 0.38
        self.k_const_impact = 1.0

        self.k_rookie_pwr = 0.75
        self.k_rookie_variance = 5
        self.k_race_regress_exp = 0.87  #TODO needs to change!
        self.k_variance_multiplier_end = 1.5

        self.k_eng_regress = 0.9
        self.k_const_regress = 0.9
        self.k_driver_regress = 0.74

    def constructDataset(self, entries, results):
        # Initializing data structures
        self.drivers = {}  # DriverId, Driver
        self.constructors = {}  # ConstructorId, Constructor
        self.engines = {}  # EngineId, Engine

        # Deviation variables
        globaldev = [None] * 20
        trackdev = {}
        for year, season in self.seasonsData.items():  # Read every season:
            self._updateModelsForYear(season)
            racesAsList = list(season.races.items())
            racesAsList.sort(key=lambda x: x[1].round)
            for raceId, data in racesAsList:
                # A single race
                if raceId in self.qualiResultsData:
                    qresults = self.qualiResultsData[raceId]
                    self._addNewDriversAndConstructors(qresults, year)

                    # Scores and qresults need to be in the same, sequential order by score
                    qresults.sort(key=lambda x: x[2])
                    scores = calculateScoresFromResults(qresults, data.circuitId, globaldev, trackdev)

                    # Add to entries and results
                    if year > 2005:  # Don't use the oldest data in the dataset
                        for index, (driverId, constId, time) in enumerate(qresults):
                            self._addNewCircuitsToEntities(
                                driverId, data.circuitId)

                            entry = self._buildEntry(driverId, data.circuitId)
                            result = scores[index]
                            entries.append(entry)
                            results.append(result)
                    self._updateModels(qresults, scores, data.circuitId)
            self._updateModelsAtEndOfYear(season)

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

    def _updateModelsAtEndOfYear(self, season):
        # Delete old, unused constructors
        for new, old in season.teamChanges.items():
            del self.constructors[old]

        # Regress all powers towards the mean
        for (engid, eng) in self.engines.items():
            eng.pwr *= self.k_eng_regress
        for (constid, const) in self.constructors.items():
            const.pwr *= self.k_const_regress
        for (drivId, driver) in self.drivers.items():
            driver.pwr *= self.k_driver_regress
            driver.variance *= self.k_variance_multiplier_end

    def _updateModelsForYear(self, season):
        '''Resolves team name changes'''
        # Updating list of engines and constructors:
        for new, old in season.teamChanges.items():
            self.constructors[new] = self.constructors[old]
            self.constructors[new].name = self.constructorsData[new]

        for cId, engineId in season.constructorEngines.items():
            # Check that the constructor and engine exist
            if engineId not in self.engines:
                self.engines[engineId] = Engine(self.enginesData[engineId])
            if cId not in self.constructors:
                self.constructors[cId] = Constructor(self.constructorsData[cId], None)
            # Assign it its engine
            self.constructors[cId].engine = self.engines[engineId]

    def _addNewDriversAndConstructors(self, qresults, year):
        for res in qresults:
            if res[0] not in self.drivers:
                self.drivers[res[0]] = Driver(self.driversData[res[0]], res[1])
                if year > 2003:
                    self.drivers[res[0]].pwr = self.k_rookie_pwr
                    self.drivers[res[0]].variance = self.k_rookie_variance
            if self.drivers[res[0]].constructor is not self.constructors[res[1]]:
                self.drivers[res[0]].constructor = self.constructors[res[1]]

    def _updateModels(self, qresults, scores, circuitId):
        # enumerate through results to get list of scores by constructor & engine
        engineScores = {}  # engineId, [list of scores]
        constScores = {}  # constId, [list of scores]
        self._fillEngineAndConstructorScores(qresults, engineScores, constScores, scores)

        # TODO ALGO
        self._updateEngineScores(circuitId, engineScores)
        self._updateConstructorScores(circuitId, constScores)
        self._updateDriverScores(qresults, circuitId, scores)

    def _fillEngineAndConstructorScores(self, qresults, engineScores, constScores, scores):
        for i, qres in enumerate(qresults):
            if self.constructors[qres[1]].engine not in engineScores:
                # Add engine to scores
                engineScores[self.constructors[qres[1]].engine] = []
            engineScores[self.constructors[qres[1]].engine].append(scores[i])
            if self.constructors[qres[1]] not in constScores:
                # Add constructor to scores
                constScores[self.constructors[qres[1]]] = []
            constScores[self.constructors[qres[1]]].append(scores[i])

    def _updateEngineScores(self, circuitId, engineScores):
        '''Update scores for Engine model objects.'''
        for engine, es in engineScores.items():
            actual = np.mean(es)
            if circuitId not in engine.trackpwr:
                engineExpt = engine.pwr
                engine.trackpwr[circuitId] = 0
            else:
                engineExpt = (engine.pwr + self.k_track_impact *
                            engine.trackpwr[circuitId]) / (1 + self.k_track_impact)
            engine.trackpwr[circuitId] += self.k_engine_change * \
                (actual - engineExpt)*2  # Set track power normally
            engine.pwr += self.k_engine_change*(actual - engineExpt)


    def _updateConstructorScores(self, circuitId, constScores):
        '''Update scores for Constructor model objects.'''
        for const, cs in constScores.items():
            engineExpt = (const.engine.pwr + self.k_track_impact *
                        const.engine.trackpwr[circuitId]) / (1 + self.k_track_impact)
            actual = np.mean(cs)
            if circuitId not in const.trackpwr:
                constExpt = (const.pwr + self.k_eng_impact*engineExpt) / (1)
                # Set track power to be result minus engine effect
                const.trackpwr[circuitId] = 0
            else:
                constExpt = (const.pwr + self.k_track_impact*const.trackpwr[circuitId] + self.k_eng_impact*engineExpt
                            ) / (1 + self.k_track_impact)
            const.trackpwr[circuitId] += self.k_const_change * \
                (actual - constExpt)*2  # Set track power normally
            const.pwr += self.k_const_change*(actual - constExpt)


    def _updateDriverScores(self, qresults, circuitId, scores):
        '''Update scores for Driver model objects.'''
        for i, qres in enumerate(qresults):
            constExpt = (
                (self.drivers[qres[0]].constructor.pwr
                + self.k_track_impact *
                self.drivers[qres[0]].constructor.trackpwr[circuitId]
                + self.k_eng_impact * (
                    self.drivers[qres[0]].constructor.engine.pwr
                    + self.k_track_impact * self.drivers[qres[0]].constructor.engine.trackpwr[circuitId]))
                / (1 + self.k_track_impact)
            )
            actual = scores[i]
            if circuitId not in self.drivers[qres[0]].trackpwr:
                expected = (self.drivers[qres[0]].pwr + self.k_const_impact*constExpt) / (1)
                # Set track power to be result minus constructor effect
                self.drivers[qres[0]].trackpwr[circuitId] = 0
            else:
                expected = (self.drivers[qres[0]].pwr + self.k_track_impact*self.drivers[qres[0]].trackpwr[circuitId]
                            + self.k_const_impact*constExpt) / (1 + self.k_track_impact)

            self.drivers[qres[0]].trackpwr[circuitId] += self.k_driver_change * \
                (actual - expected)*2
            self.drivers[qres[0]].pwr += self.k_driver_change * \
                (actual - expected) * (self.drivers[qres[0]].variance)**0.45
            self.drivers[qres[0]].variance **= self.k_race_regress_exp




def calculateScoresFromResults(qresults, circuitId, globaldev, trackdev):
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

    updateDevValues(dev, circuitId, globaldev, trackdev)
    return [x/(np.median(list(filter(None.__ne__, globaldev))) + np.median(list(filter(None.__ne__, trackdev[circuitId])))/2)
            for x in stdList]

def updateDevValues(dev, circuitId, globaldev, trackdev):
    '''Updates the deviation values by popping the oldest value and inserting the newest to the front'''
    globaldev.pop()  # Removes last item
    globaldev.insert(0, dev)

    if circuitId not in trackdev:
        trackdev[circuitId] = [None] * 6
    trackdev[circuitId].pop()
    trackdev[circuitId].insert(0, dev)
