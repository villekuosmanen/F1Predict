import json

def getUserVariables(filename):
    user_vars = {}
    with open(filename) as f:
        for line in f:
            key, value = line.partition("=")[::2]
            user_vars[key.rstrip()] = value.rstrip()
    return user_vars

def readNextRaceDetails(filename):
    with open(filename, 'r') as handle:
        futureRaces = json.load(handle)
        circuit = futureRaces[0]["circuitId"]
        circuitName = futureRaces[0]["name"]
        raceId = futureRaces[0]["raceId"]
        year = futureRaces[0]["year"]
    return circuit, circuitName, raceId, year

def editIndexFile(filename, year, raceId, circuitName):
    with open(filename, 'r+') as handle:
        data = json.load(handle)
        data[str(year)][str(raceId)] = circuitName
        handle.seek(0)        # <--- should reset file position to the beginning.
        json.dump(data, handle, indent=4)
        handle.truncate()

def publishPredictions(filename, outFile):
    with open(filename, 'w') as fp:
        json.dump(outFile, fp)