import json
import random
import pandas as pd
import numpy as np
import math
import copy
from statistics import mean

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
        # Weights
        self.theta = [0, 0, 0, 0, 0, 0, 0] # Weights: Driv, cons, eng, track-specifics and intercept

        # Various hyperparameters
        self.k_driver_change = 0.33
        self.k_const_change = 0.33
        self.k_engine_change = 0.20
        self.k_track_change_multiplier = 1
        self.k_rookie_pwr = 0.70

        self.k_rookie_variance = 1
        self.k_driver_variance_change = 0.20
        self.k_const_variance_change = 0.15
        self.k_engine_variance_change = 0.055
        self.k_variance_multiplier_end = 1.5
        self.k_driver_const_change_variance_multiplier = 1.2
        self.k_const_name_change_variace_multiplier = 1.5

        self.k_eng_regress = 0.9
        self.k_const_regress = 0.9
        self.k_driver_regress = 0.74

    # Used in evaluation
    def constructPredictions(self):
        # Initializing data structures
        self.drivers = {}  # DriverId, Driver
        self.constructors = {}  # ConstructorId, Constructor
        self.engines = {}  # EngineId, Engine
        self.driver_variances = []
        self.const_variances = []
        self.engine_variances = []

        predictions = []

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
                    pwr_changes_driver = {}
                    pwr_changes_constructor = {}
                    pwr_changes_engine = {}

                    # Scores and qresults need to be in the same, sequential order by score
                    qresults.sort(key=lambda x: x[2])
                    scores = calculateScoresFromResults(
                        qresults, data.circuitId, globaldev, trackdev)

                    prediction = []
                    for index, (driverId, constId, time) in enumerate(qresults):
                            self._addNewCircuitsToEntities(
                                driverId, data.circuitId)
                            entry = self._buildEntry(driverId, data.circuitId)

                            # Predict result for this entrant
                            y_hat = np.dot(entry, self.theta) + random.uniform(0, 0.00001)
                            prediction.append((driverId, y_hat))
                            # Calculate error
                            err = scores[index] - y_hat
                            pwr_changes_driver[driverId] = err
                            if constId not in pwr_changes_constructor:
                                pwr_changes_constructor[constId] = []
                            pwr_changes_constructor[constId].append(err)
                            if self.constructors[constId].engine not in pwr_changes_engine:
                                pwr_changes_engine[self.constructors[constId].engine] = []
                            pwr_changes_engine[self.constructors[constId].engine].append(err)

                    prediction.sort(key=lambda x: x[1])
                    predictions.append([x[0] for x in prediction])
                    # Set old model values to be new values
                    self._updateModels(pwr_changes_driver, pwr_changes_constructor, pwr_changes_engine, data.circuitId)
                    
            self._updateModelsAtEndOfYear(season)
        return predictions

    def constructDataset(self):
        # Initializing data structures
        self.drivers = {}  # DriverId, Driver
        self.constructors = {}  # ConstructorId, Constructor
        self.engines = {}  # EngineId, Engine
        self.driver_variances = []
        self.const_variances = []
        self.engine_variances = []
        entries = []
        errors = []
        results = []

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
                    pwr_changes_driver = {}
                    pwr_changes_constructor = {}
                    pwr_changes_engine = {}

                    # Scores and qresults need to be in the same, sequential order by score
                    qresults.sort(key=lambda x: x[2])
                    scores = calculateScoresFromResults(
                        qresults, data.circuitId, globaldev, trackdev)

                    for index, (driverId, constId, time) in enumerate(qresults):
                            self._addNewCircuitsToEntities(
                                driverId, data.circuitId)
                            entry = self._buildEntry(driverId, data.circuitId)
                            entries.append(entry)
                            results.append(scores[index])

                            # Predict result for this entrant
                            y_hat = np.dot(entry, self.theta)
                            # Calculate error
                            err = scores[index] - y_hat
                            # Append error to total errors
                            errors.append(err)

                            pwr_changes_driver[driverId] = err
                            if constId not in pwr_changes_constructor:
                                pwr_changes_constructor[constId] = []
                            pwr_changes_constructor[constId].append(err)
                            if self.constructors[constId].engine not in pwr_changes_engine:
                                pwr_changes_engine[self.constructors[constId].engine] = []
                            pwr_changes_engine[self.constructors[constId].engine].append(err)

                    # Set old model values to be new values
                    self._updateModels(pwr_changes_driver, pwr_changes_constructor, pwr_changes_engine, data.circuitId)
                    
            self._updateModelsAtEndOfYear(season)
        return np.array(entries), np.array(errors), np.array(results)

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
            self.drivers[driverId].constructor.engine.trackpwr[circuitId],
            1   # Intercept
        ]
        return entry

    def _updateModelsAtEndOfYear(self, season):
        # Delete old, unused constructors
        for new, old in season.teamChanges.items():
            del self.constructors[old]

        # Regress all powers towards the mean
        for (engid, eng) in self.engines.items():
            eng.pwr *= self.k_eng_regress
            eng.variance *= self.k_variance_multiplier_end
        for (constid, const) in self.constructors.items():
            const.pwr *= self.k_const_regress
            const.variance *= self.k_variance_multiplier_end
        for (drivId, driver) in self.drivers.items():
            driver.pwr *= self.k_driver_regress
            driver.variance *= self.k_variance_multiplier_end

    def _updateModelsForYear(self, season):
        '''Resolves team name changes'''
        # Updating list of engines and constructors:
        for new, old in season.teamChanges.items():
            self.constructors[new] = self.constructors[old]
            self.constructors[new].name = self.constructorsData[new]
            self.constructors[new].variance *= self.k_const_name_change_variace_multiplier

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
                self.drivers[res[0]].variance *= self.k_driver_const_change_variance_multiplier

    def addNewDriver(self, did, name, cid):
        self.drivers[did] = Driver(name, self.constructors[cid])
        self.drivers[did].pwr = self.k_rookie_pwr
        self.drivers[did].variance = self.k_rookie_variance

    def _updateModels(self, pwr_changes_driver, pwr_changes_constructor, pwr_changes_engine, circuitId):
        for did, err in pwr_changes_driver.items():
            self.drivers[did].pwr += err * self.k_driver_change * self.drivers[did].variance
            self.drivers[did].trackpwr[circuitId] += err * self.k_driver_change * self.k_track_change_multiplier

            driv_var = abs(err) - self.drivers[did].variance
            self.drivers[did].variance += self.k_driver_variance_change * driv_var
            self.driver_variances.append(abs(driv_var))

        for cid, err_list in pwr_changes_constructor.items():
            self.constructors[cid].pwr += mean(err_list) * self.k_const_change * self.constructors[cid].variance
            self.constructors[cid].trackpwr[circuitId] += mean(err_list) * self.k_const_change * self.k_track_change_multiplier

            const_var = abs(mean(err_list)) - self.constructors[cid].variance
            self.constructors[cid].variance += self.k_const_variance_change * const_var
            self.const_variances.append(abs(const_var))

        for engine, err_list in pwr_changes_engine.items():
            engine.pwr += mean(err_list) * self.k_engine_change * engine.variance
            engine.trackpwr[circuitId] += mean(err_list) * self.k_engine_change * self.k_track_change_multiplier

            eng_var = abs(mean(err_list)) - engine.variance
            engine.variance += self.k_engine_variance_change * eng_var
            self.engine_variances.append(abs(eng_var))

def calculateScoresFromResults(qresults, circuitId, globaldev, trackdev):
    '''Return a list of standardised quali score values for the quali results.'''
    best=qresults[0][2]

    # Only the times. Maintains the same order as the original tuples, so the same index can be used
    times=[((x[2])*100/best) for x in qresults]
    median=np.median(times)
    dev=np.mean(np.abs(times - median))

    # Standardised list
    stdList=[(x - median)/dev for x in times]
    # print(stdList)

    updateDevValues(dev, circuitId, globaldev, trackdev)
    return [x/(np.median(list(filter(None.__ne__, globaldev))) + np.median(list(filter(None.__ne__, trackdev[circuitId])))/2)
            for x in stdList]


def updateDevValues(dev, circuitId, globaldev, trackdev):
    '''Updates the deviation values by popping the oldest value and inserting the newest to the front'''
    globaldev.pop()  # Removes last item
    globaldev.insert(0, dev)

    if circuitId not in trackdev:
        trackdev[circuitId]=[None] * 6
    trackdev[circuitId].pop()
    trackdev[circuitId].insert(0, dev)
