class Season:
    def __init__(self):
        self.races = {}
        #constructorId, engineId
        self.constructorEngines = {}
        #New, old
        self.teamChanges = {}
    def addRace(self, raceId, raceData):
        self.races[raceId] = raceData
    def addConstructorEngine(self, constructorId, engineId):
        self.constructorEngines[constructorId] = engineId
    def addTeamChange(self, new, old):
        self.teamChanges[new] = old

class RaceData:
    def __init__(self, circuitId, round):
        self.circuitId = circuitId
        self.round = round