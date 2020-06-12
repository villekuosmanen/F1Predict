import json
import random
import pandas as pd
import numpy as np
import math
import copy
import datetime
from statistics import mean
from surprise import SVD
from surprise import Dataset
from surprise import Reader

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
        self.theta = [0, 0, 0, 0, 0, 0, 0, 0, 0] # Weights: Driv, cons, eng, track-specifics and intercept

        # Various hyperparameters
        self.k_driver_change = 0.2
        self.k_const_change = 0.14
        self.k_engine_change = 0.05
        self.k_track_change_multiplier = 4
        self.k_rookie_pwr = 0.70

        self.k_rookie_variance = 1
        self.k_driver_variance_change = 0.15
        self.k_const_variance_change = 0.15
        self.k_engine_variance_change = 0.06
        self.k_variance_multiplier_end = 1
        self.k_eng_regress = 0.9
        self.k_const_regress = 0.9
        self.k_driver_regress = 0.74

    # Used in evaluation
    def constructPredictions(self):
        self._prepareDataStructures()
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
                    pwr_changes = {}

                    # Scores and qresults need to be in the same, sequential order by score
                    qresults.sort(key=lambda x: x[2])
                    scores = calculateScoresFromResults(
                        qresults, data.circuitId, globaldev, trackdev)

                    self._trainTrackPredictor()

                    prediction = []
                    for index, (driverId, constId, time) in enumerate(qresults):
                            self._addNewCircuitsToEntities(
                                driverId, constId, data.circuitId)
                            entry = self._buildEntry(driverId, constId, data.circuitId)

                            # Predict result for this entrant
                            y_hat = np.dot(entry, self.theta) + random.uniform(0, 0.00001)
                            prediction.append((driverId, y_hat))
                            # Calculate error
                            err = scores[index] - y_hat
                            pwr_changes[driverId] = err

                    prediction.sort(key=lambda x: x[1])
                    predictions.append([x[0] for x in prediction])
                    # Set old model values to be new values
                    self._updateModels(pwr_changes, data.circuitId)
                    
            self._updateModelsAtEndOfYear(season)
        return predictions

    def constructDataset(self):
        self._prepareDataStructures()
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
                    pwr_changes = {}

                    # Scores and qresults need to be in the same, sequential order by score
                    qresults.sort(key=lambda x: x[2])
                    scores = calculateScoresFromResults(
                        qresults, data.circuitId, globaldev, trackdev)

                    self._trainTrackPredictor()

                    for index, (driverId, constId, time) in enumerate(qresults):
                            self._addNewCircuitsToEntities(
                                driverId, constId, data.circuitId)
                            entry = self._buildEntry(driverId, constId, data.circuitId)
                            entries.append(entry)
                            results.append(scores[index])

                            # Predict result for this entrant
                            y_hat = np.dot(entry, self.theta)
                            # Calculate error
                            err = scores[index] - y_hat
                            # Append error to total errors
                            errors.append(err)
                            pwr_changes[driverId] = err

                    # Set old model values to be new values
                    self._updateModels(pwr_changes, data.circuitId)
                    
            self._updateModelsAtEndOfYear(season)
        return np.array(entries), np.array(errors), np.array(results)

    def _addNewCircuitsToEntities(self, driverId, constId, circuitId):
        if circuitId not in self.drivers[driverId].trackpwr:
            # TODO maybe change defaults
            self.drivers[driverId].trackpwr[circuitId] = 0
        if circuitId not in self.constructors[constId].trackpwr:
            # TODO maybe change defaults
            self.constructors[constId].trackpwr[circuitId] = 0
        if circuitId not in self.engines[self.constructors[constId].engine].trackpwr:
            # TODO maybe change defaults
            self.engines[self.constructors[constId].engine].trackpwr[circuitId] = 0

    def _prepareDataStructures(self):
        self.drivers = {}  # DriverId, Driver
        self.constructors = {}  # ConstructorId, Constructor
        self.engines = {}  # EngineId, Engine
        self.driver_variances = []
        self.const_variances = []
        self.engine_variances = []
        self.algo = SVD(n_factors=8, n_epochs=10)

    def _trainTrackPredictor(self):
        # Train track predictor:
        track_results_df = self._generateTrackResultsDf()
        reader = Reader(rating_scale=(track_results_df['score'].min(), track_results_df['score'].max()))
        track_dataset = Dataset.load_from_df(track_results_df, reader).build_full_trainset()
        self.algo.fit(track_dataset)

    def _buildEntry(self, driverId, constId, circuitId):
        # Get track-specific predictions:
        driver_track_pwr = self.algo.predict(1000000 + driverId, circuitId).est
        const_track_pwr = self.algo.predict(2000000 + constId, circuitId).est
        engine_track_pwr = self.algo.predict(3000000 + self.constructors[constId].engine, circuitId).est

        entry = [
            self.drivers[driverId].pwr,
            self.constructors[constId].pwr,
            self.engines[self.constructors[constId].engine].pwr,
            self.drivers[driverId].trackpwr[circuitId],
            const_track_pwr if not math.isnan(const_track_pwr) else 0,
            engine_track_pwr if not math.isnan(engine_track_pwr) else 0,
            const_track_pwr**2 if not math.isnan(const_track_pwr) else 0,
            engine_track_pwr**2 if not math.isnan(engine_track_pwr) else 0,
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

        for cId, engineId in season.constructorEngines.items():
            # Check that the constructor and engine exist
            if engineId not in self.engines:
                self.engines[engineId] = Engine(self.enginesData[engineId])
            if cId not in self.constructors:
                self.constructors[cId] = Constructor(self.constructorsData[cId], None)
            # Assign it its engine
            self.constructors[cId].engine = engineId

    def _addNewDriversAndConstructors(self, qresults, year):
        for res in qresults:
            if res[0] not in self.drivers:
                self.drivers[res[0]] = Driver(self.driversData[res[0]], res[1])
                if year > 2003:
                    self.drivers[res[0]].pwr = self.k_rookie_pwr
                    self.drivers[res[0]].variance = self.k_rookie_variance
            if self.drivers[res[0]].constructor is not res[1]:
                self.drivers[res[0]].constructor = res[1]

    def _generateTrackResultsDf(self):
        data = []
        for constructorId, constructor in self.constructors.items():
            for circuitId, power in constructor.trackpwr.items():
                data.append([constructorId + 2000000, circuitId, power])

        for engineId, engine in self.engines.items():
            for circuitId, power in engine.trackpwr.items():
                data.append([engineId + 3000000, circuitId, power])
        return pd.DataFrame(data, columns = ['entityId', 'circuitId', "score"]) 

    def addNewDriver(self, did, name, cid):
        self.drivers[did] = Driver(name, cid)
        self.drivers[did].pwr = self.k_rookie_pwr
        self.drivers[did].variance = self.k_rookie_variance

    def _updateModels(self, pwr_changes, circuitId):
        for did, err in pwr_changes.items():
            self.drivers[did].pwr += err * self.k_driver_change
            self.constructors[self.drivers[did].constructor].pwr += err * self.k_const_change
            self.engines[self.constructors[self.drivers[did].constructor].engine].pwr += err * self.k_engine_change

            self.drivers[did].trackpwr[circuitId] += err * self.k_driver_change * self.k_track_change_multiplier
            self.constructors[self.drivers[did].constructor].trackpwr[circuitId] += (
                err * self.k_const_change * self.k_track_change_multiplier)
            self.engines[self.constructors[self.drivers[did].constructor].engine].trackpwr[circuitId] += (
                err * self.k_engine_change * self.k_track_change_multiplier)

            driv_var = abs(err) - self.drivers[did].variance
            self.drivers[did].variance += self.k_driver_variance_change * driv_var
            self.driver_variances.append(abs(driv_var))

            const_var = abs(err) - self.constructors[self.drivers[did].constructor].variance
            self.constructors[self.drivers[did].constructor].variance += self.k_const_variance_change * const_var
            self.const_variances.append(abs(const_var))

            eng_var = abs(err) - self.engines[self.constructors[self.drivers[did].constructor].engine].variance
            self.engines[self.constructors[self.drivers[did].constructor].engine].variance += self.k_engine_variance_change * eng_var
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
