import json
import operator
import numpy as np

def overwriteQualiModelWithNewDrivers(qualiModel, filename):
    newDrivers = json.load(open(filename))["drivers"]
    newDrivers = {int(did): cid for did, cid in newDrivers.items()}
    for did, cid in newDrivers.items():
        if did < 0 or did not in qualiModel.drivers:  # Cases when driver doesn't exist in data
            qualiModel.addNewDriver(did, "__PLACEHOLDER__", cid)
        if not cid == "":
            # Data in newDrivers.json overwrites database
            qualiModel.drivers[did].constructor = qualiModel.constructors[int(cid)]

def calculateOrder(qualiModel, driverIDs, circuit):
    entries = []
    for did in driverIDs:
        entry = [
            qualiModel.drivers[did].pwr,
            qualiModel.drivers[did].constructor.pwr, 
            qualiModel.drivers[did].constructor.engine.pwr,
            qualiModel.drivers[did].trackpwr[circuit],
            qualiModel.drivers[did].constructor.trackpwr[circuit],
            qualiModel.drivers[did].constructor.engine.trackpwr[circuit],
            1
        ]
        entries.append(entry)

    linearRegResults = [np.dot(x, qualiModel.theta) for x in entries]

    orderedResults = [] # [(did, prediction) ...]
    for index, did in enumerate(driverIDs):
        orderedResults.append((did, linearRegResults[index]))
        
    orderedResults.sort(key = operator.itemgetter(1))
    return [a for (a, b) in orderedResults]