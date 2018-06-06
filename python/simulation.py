import json
import random
import pandas as pd
import numpy as np

from .f1Data import Season
from .f1Data import RaceData
from .f1Models import Engine
from .f1Models import Constructor
from .f1Models import Driver

k_engine_change = 0.35
k_const_change = 0.34
k_driver_change = 0.40

k_track_impact = 0.10        #ZERO!
k_eng_impact = 0.40
k_const_impact = 1.15

k_variance = 0.08    #At the moment, best is 0 (= no randomness)!
k_rookie_pwr = 0.96
k_rookie_variance = 5
k_race_regress_exp = 0.87
k_variance_multiplier_end = 1.5

k_eng_regress = 0.9
k_const_regress = 1
k_driver_regress = 0.74

#runNo is never used. It is required for paraller processing to work properly
def runSimulation(runNo, seasonsData, qualiResultsData, driversData, constructorsData, enginesData):
    #Deviation variables
    globaldev = [None] * 20
    trackdev = {}

    #Drivers, engines and constructors:
    drivers = {} #DriverId, Driver
    constructors = {} #ConstructorId, Constructor
    engines = {} #EngineId, Engine
    grades = []
    for year, season in seasonsData.items():    #Read every season:
        #print(year)
        updateModelsForYear(season, constructors, engines, enginesData, constructorsData)
        racesAsList = list(season.races.items())
        racesAsList.sort(key=lambda x: x[1].round)
        for raceId, data in racesAsList:
            #A single race
            if raceId < 992:
                circuit = data.circuitId
                qresults = qualiResultsData[raceId]
                addDriversToModel(qresults, drivers, constructors, driversData, year)
                nextDrivers = {did: cid for (did, cid, time) in qresults}
                predictedScores = predictQualiResults(circuit, nextDrivers, drivers, constructors, engines)
            
                qresults.sort(key=lambda x: x[2])   #Scores and qresults need to be in same order!
                if year >= 2013:
                    grade = gradePrediction([i[0] for i in predictedScores], [k[0] for k in qresults], len(qresults))
                    grades.append(grade)
                    #print("Year " + str(year) + ", circuit " + str(circuit) + ": " + str(grade))
                scores = calculateScoresFromResults(qresults, drivers, constructors, data, globaldev, trackdev)
                updateModels(qresults, scores, constructors, data, drivers)
        #Regress all powers towards the mean
        for (engid, eng) in engines.items():
            eng.pwr *= k_eng_regress
        for (constid, const) in constructors.items():
            const.pwr *= k_const_regress
        for (drivId, driver) in drivers.items():
            driver.pwr *= k_driver_regress
            driver.variance *= k_variance_multiplier_end
    return np.median(grades)

#Exactly the same, except it returns the drivers, constructors and engines
def runSimReturnDrivConstEng(seasonsData, qualiResultsData, driversData, constructorsData, enginesData):
    #Deviation variables
    globaldev = [None] * 20
    trackdev = {}

    #Drivers, engines and constructors:
    drivers = {} #DriverId, Driver
    constructors = {} #ConstructorId, Constructor
    engines = {} #EngineId, Engine
    grades = []
    for year, season in seasonsData.items():    #Read every season:
        #print(year)
        updateModelsForYear(season, constructors, engines, enginesData, constructorsData)
        racesAsList = list(season.races.items())
        racesAsList.sort(key=lambda x: x[1].round)
        for raceId, data in racesAsList:
            #A single race
            if raceId < 992:
                circuit = data.circuitId
                qresults = qualiResultsData[raceId]
                addDriversToModel(qresults, drivers, constructors, driversData, year)
                nextDrivers = {did: cid for (did, cid, time) in qresults}
                predictedScores = predictQualiResults(circuit, nextDrivers, drivers, constructors, engines)
            
                qresults.sort(key=lambda x: x[2])   #Scores and qresults need to be in same order!
                if year >= 2013:
                    grade = gradePrediction([i[0] for i in predictedScores], [k[0] for k in qresults], len(qresults))
                    grades.append(grade)
                    #print("Year " + str(year) + ", circuit " + str(circuit) + ": " + str(grade))
                scores = calculateScoresFromResults(qresults, drivers, constructors, data, globaldev, trackdev)
                updateModels(qresults, scores, constructors, data, drivers)
        #Regress all powers towards the mean
        for (engid, eng) in engines.items():
            eng.pwr *= k_eng_regress
        for (constid, const) in constructors.items():
            const.pwr *= k_const_regress
        for (drivId, driver) in drivers.items():
            driver.pwr *= k_driver_regress
            driver.variance *= k_variance_multiplier_end
    return (drivers, constructors, engines)

#Functions for calculating deviation of qualifying times:
def addTrackToTrackDev(trackdev, circuitId):
    '''Adds the given circuit to the list of track deviations'''
    trackdev[circuitId] = [None] * 6

def updateDevValues(dev, circuitId, globaldev, trackdev):
    '''Updates the deviation values by popping the oldest value and inserting the newest to the front'''
    globaldev.pop() #Removes last item
    globaldev.insert(0, dev)
    
    if circuitId not in trackdev:
        addTrackToTrackDev(trackdev, circuitId)
    trackdev[circuitId].pop()
    trackdev[circuitId].insert(0, dev)

#Functions for updating model objects for a year:
def updateModelsForYear(season, constructors, engines, enginesData, constructorsData):
    '''Do these housekeeping things at the beginning of the year'''
    #Updating list of engines and constructors:
    for new, old in season.teamChanges.items():
        constructors[new] = constructors[old]
        constructors[new].name = constructorsData[new]
    #print(season.constructorEngines)
    for cId, engineId in season.constructorEngines.items():
        #Check that the constructor and engine exist
        if engineId not in engines:
            engines[engineId] = Engine(enginesData[engineId])
        if cId not in constructors:
            constructors[cId] = Constructor(constructorsData[cId], None)
        #Assign it its engine
        constructors[cId].engine = engines[engineId]
        
def addDriversToModel(qresults, drivers, constructors, driversData, year):
     for res in qresults:
        if res[0] not in drivers:
            drivers[res[0]] = Driver(driversData[res[0]], res[1])
            if year > 2003:
                drivers[res[0]].pwr = k_rookie_pwr
                drivers[res[0]].variance = k_rookie_variance
        if drivers[res[0]].constructor is not constructors[res[1]]:
            drivers[res[0]].constructor = constructors[res[1]]
        
def calculateScoresFromResults(qresults, drivers, constructors, raceData, globaldev, trackdev):
    '''Return a list of standardised quali score values for the quali results.'''
    #Make sure all drivers have been added to the list and their info is correct
    best = qresults[0][2]

    #Only the times. Maintains the same order as the original tuples, so the same index can be used
    times = [((x[2])*100/best) for x in qresults]
    median = np.median(times)
    dev = np.mean(np.abs(times - median))
    #print(dev)
        
    #Standardised list
    stdList = [(x - median)/dev for x in times]
    #print(stdList)

    updateDevValues(dev, raceData.circuitId, globaldev, trackdev)
    return [x/(np.median(list(filter(None.__ne__, globaldev))) + np.median(list(filter(None.__ne__, trackdev[raceData.circuitId])))/2) 
                  for x in stdList]

def updateModels(qresults, scores, constructors, data, drivers):
    #enumerate through results to get list of scores by constructor & engine
            engineScores = {} #engineId, [list of scores]
            constScores = {} #constId, [list of scores]
            for i, qres in enumerate(qresults):
                if constructors[qres[1]].engine not in engineScores:
                    #Add engine to scores
                    engineScores[constructors[qres[1]].engine] = []
                engineScores[constructors[qres[1]].engine].append(scores[i])
                if constructors[qres[1]] not in constScores:
                    #Add constructor to scores
                    constScores[constructors[qres[1]]] = []
                constScores[constructors[qres[1]]].append(scores[i])
            
            #Update scores for Engine model objects.
            for engine, es in engineScores.items():
                actual = np.mean(es)
                if data.circuitId not in engine.trackpwr:
                    engineExpt = engine.pwr
                    engine.trackpwr[data.circuitId] = 0
                else:
                    engineExpt = (engine.pwr + k_track_impact*engine.trackpwr[data.circuitId]) / (1 + k_track_impact)
                engine.trackpwr[data.circuitId] += k_engine_change*(actual - engineExpt)*2 #Set track power normally
                engine.pwr += k_engine_change*(actual - engineExpt)
            
            #Update scores for Constructor model objects.        
            for const, cs in constScores.items():
                engineExpt = (const.engine.pwr + k_track_impact*const.engine.trackpwr[data.circuitId]) / (1 + k_track_impact)
                actual = np.mean(cs)
                if data.circuitId not in const.trackpwr:
                    constExpt = (const.pwr + k_eng_impact*engineExpt) / (1+k_eng_impact)
                    #Set track power to be result minus engine effect
                    const.trackpwr[data.circuitId] = 0
                else:
                    constExpt = (const.pwr + k_track_impact*const.trackpwr[data.circuitId] + k_eng_impact*engineExpt
                                ) / (1 + k_track_impact + k_eng_impact) 
                const.trackpwr[data.circuitId] += k_const_change * (actual - constExpt)*2 #Set track power normally
                const.pwr += k_const_change*(actual - constExpt)
            
            #Update scores for Driver model objects.
            for i, qres in enumerate(qresults):
                constExpt = (drivers[qres[0]].constructor.pwr + k_track_impact*drivers[qres[0]].constructor.trackpwr[data.circuitId]
                                + k_eng_impact*(drivers[qres[0]].constructor.engine.pwr + 
                                k_track_impact*const.engine.trackpwr[data.circuitId])) / (1 + k_track_impact + k_eng_impact)
                actual = scores[i]
                if data.circuitId not in drivers[qres[0]].trackpwr:
                    expected = (drivers[qres[0]].pwr + k_const_impact*constExpt) / (1+k_const_impact)
                    #Set track power to be result minus constructor effect
                    drivers[qres[0]].trackpwr[data.circuitId] = 0
                else:
                    expected = (drivers[qres[0]].pwr + k_track_impact*drivers[qres[0]].trackpwr[data.circuitId] 
                                + k_const_impact*constExpt) / (1 + k_track_impact + k_const_impact)
                drivers[qres[0]].trackpwr[data.circuitId] += k_driver_change*(actual - expected)*2
                #print(drivers[qres[0]].pwr)
                drivers[qres[0]].pwr += k_driver_change*(actual - expected)
                drivers[qres[0]].variance **= k_race_regress_exp

#Predicts the results for a quali in a given circuit for the given participants using the given data.

#The participants have to be added to drivers etc. beforehand
#Returns a sorted list of tuples of (driverId, score)
def predictQualiResults(circuitId, participants, drivers, constructors, engines):
    scores = {}
    for driver, const in participants.items():
        did = int(driver)
        score = None
        #cid only used if driver is new...
        if did not in drivers:
            cid = int(const)
            #Rookie, not added to drivers yet!
            drivers[did] = Driver("_NO_NAME_", constructors[cid])
        rand = (random.weibullvariate(1.95, 1.55) - 1) * k_variance * drivers[did].variance
        #rand = (random.betavariate(5, 7.5) - 0.4) * k_variance
        mistakeOdds = random.random()
        if mistakeOdds < 0.012*drivers[did].variance:
            rand += 4
        if circuitId not in drivers[did].trackpwr:
            if circuitId not in drivers[did].constructor.trackpwr:
                if circuitId not in drivers[did].constructor.engine.trackpwr:
                    score = (drivers[did].pwr + k_const_impact*((drivers[did].constructor.pwr) + k_eng_impact*(
                            drivers[did].constructor.engine.pwr))) / (1 + k_const_impact) + rand
                else:
                    score = (drivers[did].pwr + k_const_impact*(drivers[did].constructor.pwr + k_eng_impact*(
                            drivers[did].constructor.engine.pwr + k_track_impact*drivers[did].constructor.engine.trackpwr
                            [circuitId]))) / (1 + k_const_impact) + rand
            else:
                score = (drivers[did].pwr + k_const_impact*(drivers[did].constructor.pwr + k_track_impact*
                        drivers[did].constructor.trackpwr[circuitId] + k_eng_impact*drivers[did].constructor.engine.pwr)
                        ) / (1 + k_const_impact) + rand
        elif (circuitId not in drivers[did].constructor.trackpwr):
            if circuitId not in drivers[did].constructor.engine.trackpwr:
                score = (drivers[did].pwr + k_track_impact*drivers[did].trackpwr[circuitId] + k_const_impact*(
                        (drivers[did].constructor.pwr) + k_eng_impact*(drivers[did].constructor.engine.pwr)
                        )) / (1 + k_track_impact + k_const_impact) + rand
            else:
                score = (drivers[did].pwr + k_track_impact*drivers[did].trackpwr[circuitId] + k_const_impact*(
                        (drivers[did].constructor.pwr) + k_eng_impact*(
                        drivers[did].constructor.engine.pwr + k_track_impact*drivers[did].constructor.engine.trackpwr[circuitId]))
                        ) / (1 + k_track_impact + k_const_impact) + rand
        else:
            if circuitId not in drivers[did].constructor.engine.trackpwr:
                score = (drivers[did].pwr + k_track_impact*drivers[did].trackpwr[circuitId] + k_const_impact*((drivers[did].constructor.pwr 
                        + k_track_impact*drivers[did].constructor.trackpwr[circuitId]) + k_eng_impact*(
                        drivers[did].constructor.engine.pwr))) / (1 + k_track_impact + k_const_impact) + rand
            else:
                score = (drivers[did].pwr + 
                        k_track_impact*drivers[did].trackpwr[circuitId] +  
                        k_const_impact*((drivers[did].constructor.pwr + k_track_impact*drivers[did].constructor.trackpwr[circuitId]) + 
                            k_eng_impact*(drivers[did].constructor.engine.pwr + k_track_impact*drivers[did].constructor.engine.trackpwr[circuitId]))
                        ) / (1 + k_track_impact + k_const_impact) + rand
        #print("Score: " + str(score) + ", Rand: " + str(rand))
        scores[did] = score
    #Sort scores:
    scoreList = list(scores.items())
    scoreList.sort(key=lambda x: x[1])
    return scoreList

#Predicted, Actual: [driver]
def gradePrediction(predicted, actual, length):
    gradeVals = [1.00, 0.75, 0.54, 0.36, 0.22, 0.10, 0]
    total = 0
    for i, driver in enumerate(actual):
        if driver in predicted:
            predictedPos = predicted.index(driver)
            diff = abs(i - predictedPos)
            if diff > 6:
                diff = 6
            if i == 0:
                total += 10 * gradeVals[diff]
            elif i == 1:
                total += 8 * gradeVals[diff]
            elif i < 5:
                total += 6 * gradeVals[diff]
            elif i < 10:
                total += 4 * gradeVals[diff]
            else:
                total += 2 * gradeVals[diff]
    if length < 10:
        raise AttributeError("Too few drivers")
    grade = total / (10 + 8 + 18 + 20 + (length - 10)*2)
    return grade