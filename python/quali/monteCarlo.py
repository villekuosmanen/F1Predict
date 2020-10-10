import copy
import random
import numpy as np

#driverIDs: key-value mapping of driver id and power score
def predictQualiResults(circuitId, driverIDs, model):
    editableDriverIDs = copy.deepcopy(driverIDs)
    finalScores = []
    scores = runQualifying(circuitId, editableDriverIDs, model)
    #Sort scores:
    scoreList = list(scores.items())
    scoreList.sort(key=lambda x: x[1])
    tempList = []
    if len(scoreList) == 20:
        tempList = scoreList[15:]
    elif len(scoreList) == 22:
        tempList = scoreList[16:]
    elif len(scoreList) == 24:
        tempList = scoreList[17:]
    else:
        return scoreList
    for (did, score) in tempList:
        del editableDriverIDs[int(did)]
    finalScores = tempList + finalScores

    #Q2
    scores = runQualifying(circuitId, editableDriverIDs, model)
    #Sort scores:
    scoreList = list(scores.items())
    scoreList.sort(key=lambda x: x[1])
    tempList = scoreList[10:]
    for (did, score) in tempList:
        del editableDriverIDs[int(did)]
    finalScores = tempList + finalScores

    #Q3
    scores = runQualifying(circuitId, editableDriverIDs, model)
    #Sort scores:
    scoreList = list(scores.items())
    scoreList.sort(key=lambda x: x[1])
    finalScores = scoreList + finalScores

    return [x[0] for x in finalScores]

def runQualifying(circuitId, driverIDs, model):
    scores = {}
    constructorRands = {}
    engineRands = {}
    for did in driverIDs.keys():
        did = int(did)

        if model.drivers[did].constructor in constructorRands:
            constRand = constructorRands[model.drivers[did].constructor]
        else:
            constRand = random.normalvariate(0, model.drivers[did].constructor.variance)
            constructorRands[model.drivers[did].constructor] = constRand
        if model.drivers[did].constructor.engine in engineRands:
            engineRand = engineRands[model.drivers[did].constructor.engine]
        else:
            engineRand = random.normalvariate(0, model.drivers[did].constructor.engine.variance)
            engineRands[model.drivers[did].constructor.engine] = engineRand

        entry = [
            model.drivers[did].pwr + random.normalvariate(0, model.drivers[did].variance) / 3,
            model.drivers[did].constructor.pwr + constRand / 3, 
            model.drivers[did].constructor.engine.pwr + engineRand / 3,
            model.drivers[did].trackpwr[circuitId],
            model.drivers[did].constructor.trackpwr[circuitId],
            model.drivers[did].constructor.engine.trackpwr[circuitId],
            1
        ]
        score = np.dot(entry, model.theta)
        mistakeOdds = random.random()
        if mistakeOdds < 0.031:    #Experimentally validated!
            score += 4
        scores[did] = score
    return scores