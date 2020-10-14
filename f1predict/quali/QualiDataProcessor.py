import random
import pandas as pd
import numpy as np
from statistics import mean

from f1predict.quali.QualiLinearModel import QualiLinearModel
from f1predict.common.Season import Season
from f1predict.common.RaceData import RaceData
from f1predict.quali.f1Models import Engine
from f1predict.quali.f1Models import Constructor
from f1predict.quali.f1Models import Driver


class QualiDataProcessor:

    def __init__(self, seasonsData, qualiResultsData, driversData, constructorsData, enginesData):
        self.seasonsData = seasonsData
        self.qualiResultsData = qualiResultsData
        self.driversData = driversData
        self.constructorsData = constructorsData
        self.enginesData = enginesData

        self._initialiseConstants()

        self.model = QualiLinearModel(
            self.k_rookie_pwr, self.k_rookie_variance)
        self.predictions = None
        self.entries = None
        self.errors = None
        self.results = None

    def _initialiseConstants(self):
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

    # Processes the qualifying data the class was initialised with
    # After completion, the class contains the processed model, list of predictions, and list of entries, errors and results
    def processDataset(self):
        self.model.resetVariables()
        self.predictions = []
        self.entries = []
        self.errors = []
        self.results = []

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
                        self.model.addNewCircuit(driverId, data.circuitId)
                        entry = self._buildEntry(driverId, data.circuitId)
                        self.entries.append(entry)
                        self.results.append(scores[index])

                        y_hat = np.dot(entry, self.model.theta)
                        prediction.append((driverId, y_hat))

                        # Calculate error
                        err = scores[index] - y_hat
                        # Append error to total errors
                        self.errors.append(err)

                        pwr_changes_driver[driverId] = err
                        if constId not in pwr_changes_constructor:
                            pwr_changes_constructor[constId] = []
                        pwr_changes_constructor[constId].append(err)
                        if self.model.constructors[constId].engine not in pwr_changes_engine:
                            pwr_changes_engine[self.model.constructors[constId].engine] = [
                            ]
                        pwr_changes_engine[self.model.constructors[constId].engine].append(
                            err)

                    random.shuffle(prediction)
                    prediction.sort(key=lambda x: x[1])
                    self.predictions.append([x[0] for x in prediction])
                    # Set old model values to be new values
                    self._updateModels(
                        pwr_changes_driver, pwr_changes_constructor, pwr_changes_engine, data.circuitId)
            self._updateModelsAtEndOfYear(season)

    # Returns the generated LinearQualiModel from the last processing, or an empty model if the function was not called yet
    def getModel(self):
        return self.model

    # Returns a list of all generated predictions from the last processing
    # Throws an exception if called before processing a dataset
    def getPredictions(self):
        if self.predictions == None:
            raise AssertionError(
                "Predictions not generated yet! Call <processDataset()> before calling me.")
        return self.predictions

    # Returns the entries, errors and results from the last processing
    # Throws an exception if called before processing a dataset
    def getDataset(self):
        if self.entries == None:
            raise AssertionError(
                "Dataset not generated yet! Call <processDataset()> before calling me.")
        return np.array(self.entries), np.array(self.errors), np.array(self.results)

    def _buildEntry(self, driverId, circuitId):
        entry = [
            self.model.drivers[driverId].pwr,
            self.model.drivers[driverId].constructor.pwr,
            self.model.drivers[driverId].constructor.engine.pwr,
            self.model.drivers[driverId].trackpwr[circuitId],
            self.model.drivers[driverId].constructor.trackpwr[circuitId],
            self.model.drivers[driverId].constructor.engine.trackpwr[circuitId],
            1   # Intercept
        ]
        return entry

    def _updateModelsAtEndOfYear(self, season):
        # Delete old, unused constructors
        for new, old in season.teamChanges.items():
            del self.model.constructors[old]

        # Regress all powers towards the mean
        for (engid, eng) in self.model.engines.items():
            eng.pwr *= self.k_eng_regress
            eng.variance *= self.k_variance_multiplier_end
        for (constid, const) in self.model.constructors.items():
            const.pwr *= self.k_const_regress
            const.variance *= self.k_variance_multiplier_end
        for (drivId, driver) in self.model.drivers.items():
            driver.pwr *= self.k_driver_regress
            driver.variance *= self.k_variance_multiplier_end

    def _updateModelsForYear(self, season):
        '''Resolves team name changes'''
        # Updating list of engines and constructors:
        for new, old in season.teamChanges.items():
            self.model.constructors[new] = self.model.constructors[old]
            self.model.constructors[new].name = self.constructorsData[new]
            self.model.constructors[new].variance *= self.k_const_name_change_variace_multiplier

        for cId, engineId in season.constructorEngines.items():
            # Check that the constructor and engine exist
            if engineId not in self.model.engines:
                self.model.engines[engineId] = Engine(
                    self.enginesData[engineId])
            if cId not in self.model.constructors:
                self.model.constructors[cId] = Constructor(
                    self.constructorsData[cId], None)
            # Assign it its engine
            self.model.constructors[cId].engine = self.model.engines[engineId]

    def _addNewDriversAndConstructors(self, qresults, year):
        for res in qresults:
            if res[0] not in self.model.drivers:
                self.model.drivers[res[0]] = Driver(
                    self.driversData[res[0]], res[1])
                if year > 2003:
                    self.model.drivers[res[0]].pwr = self.k_rookie_pwr
                    self.model.drivers[res[0]
                                       ].variance = self.k_rookie_variance
            if self.model.drivers[res[0]].constructor is not self.model.constructors[res[1]]:
                self.model.drivers[res[0]
                                   ].constructor = self.model.constructors[res[1]]
                self.model.drivers[res[0]
                                   ].variance *= self.k_driver_const_change_variance_multiplier

    def _updateModels(self, pwr_changes_driver, pwr_changes_constructor, pwr_changes_engine, circuitId):
        for did, err in pwr_changes_driver.items():
            self.model.drivers[did].pwr += err * \
                self.k_driver_change * self.model.drivers[did].variance
            self.model.drivers[did].trackpwr[circuitId] += err * \
                self.k_driver_change * self.k_track_change_multiplier

            driv_var = abs(err) - self.model.drivers[did].variance
            self.model.drivers[did].variance += self.k_driver_variance_change * driv_var
            self.model.driver_variances.append(abs(driv_var))

        for cid, err_list in pwr_changes_constructor.items():
            self.model.constructors[cid].pwr += mean(err_list) * \
                self.k_const_change * self.model.constructors[cid].variance
            self.model.constructors[cid].trackpwr[circuitId] += mean(
                err_list) * self.k_const_change * self.k_track_change_multiplier

            const_var = abs(mean(err_list)) - \
                self.model.constructors[cid].variance
            self.model.constructors[cid].variance += self.k_const_variance_change * const_var
            self.model.const_variances.append(abs(const_var))

        for engine, err_list in pwr_changes_engine.items():
            engine.pwr += mean(err_list) * \
                self.k_engine_change * engine.variance
            engine.trackpwr[circuitId] += mean(err_list) * \
                self.k_engine_change * self.k_track_change_multiplier

            eng_var = abs(mean(err_list)) - engine.variance
            engine.variance += self.k_engine_variance_change * eng_var
            self.model.engine_variances.append(abs(eng_var))


def calculateScoresFromResults(qresults, circuitId, globaldev, trackdev):
    '''Return a list of standardised quali score values for the quali results.'''
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
