import math
import copy
import random

#Participants: key-value mapping of driver id and power score
def predictQualiResults(circuitId, participants):
    editableParticipants = copy.deepcopy(participants)
    finalScores = []
    scores = runQualifying(circuitId, editableParticipants)
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
        del editableParticipants[int(did)]
    finalScores = tempList + finalScores

    #Q2
    scores = runQualifying(circuitId, editableParticipants)
    #Sort scores:
    scoreList = list(scores.items())
    scoreList.sort(key=lambda x: x[1])
    tempList = scoreList[10:]
    for (did, score) in tempList:
        del editableParticipants[int(did)]
    finalScores = tempList + finalScores

    #Q3
    scores = runQualifying(circuitId, editableParticipants)
    #Sort scores:
    scoreList = list(scores.items())
    scoreList.sort(key=lambda x: x[1])
    finalScores = scoreList + finalScores

    return finalScores

def runQualifying(circuitId, participants):
    scores = {}
    for did, driver in participants.items():
        did = int(did)
        score = None

        rand = random.normalvariate(0, driver["driv_var"])
        rand += random.normalvariate(0, driver["const_var"])
        rand += random.normalvariate(0, driver["eng_var"])
        rand *= 0.33
        mistakeOdds = random.random()
        if mistakeOdds < 0.031:    #Experimentally validated!
            rand += 4
        scores[did] = driver["pwr"] + rand
    return scores