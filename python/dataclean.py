from . import Season
from . import RaceData

import pymysql
import pymysql.cursors
import pandas as pd

def compareQualiTimes(q1, q2, q3):
    '''Returns the best time of the three'''
    if q3 is None or not q3:
        if q2 is None or not q2:
            if q1 is None or not q1:
                #Didn't take part
                return None
            else:
                return 60.0 + float(q1.split(":")[1])
        else:
            #See which is greater
            return 60.0 + fasterTime(float((q1.split(":"))[1]), float((q2.split(":"))[1]))
    else:
        #See which is greater
        return 60.0 + fasterTime(float((q1.split(":"))[1]), fasterTime(float((q2.split(":"))[1]), float((q3.split(":"))[1])))

def fasterTime(previous, current):
    '''Returns the faster time, or either of them if they are equal'''
    if previous is None:
        return current
    elif current is None:
        return previous
    
    if previous < current:
        return previous
    else:
        return current
    
def slowerTime(previous, current):
    '''Returns the slower time, or either of them if they are equal'''
    if previous is None:
        return current
    elif current is None:
        return previous
    
    if previous < current:
        return current
    else:
        return previous

def addSeason(cursor, seasonsData, qualiResultsData, year):
    '''Adds a Season Data object to the given map of seasons'''
    s = Season()
    
    sql = "SELECT `raceId`, `round`, `circuitId`, `name` FROM `races` WHERE `year`=%s"
    cursor.execute(sql, year)
    result = cursor.fetchall()
    
    for x in result:
        raceData = RaceData(x.get('circuitId'), x.get('round'))
        s.addRace(x.get('raceId'), raceData)
        addQualiResults(cursor, qualiResultsData, x.get('raceId'))
        
    seasonsData[year] = s

def addQualiResults(cursor, qualiResultsData, raceId):
    '''Adds quali results from a race. Each result has a separate object for each driver's performance'''
    qs = []
    
    sql = "SELECT `driverId`, `constructorId`, `q1`, `q2`, `q3`, `position` FROM `qualifying` WHERE `raceId`=%s"
    cursor.execute(sql, raceId)
    result = cursor.fetchall()
    if result:
        #The tuple is non-empty. Here we remove the trivial cases (races where there is no data).
        result.sort(key=lambda result: result['position'])    
        lastBestTime = None
        for x in result:
            #Use q1, q2 and q3 to identify best time
            q1 = x.get('q1')
            q2 = x.get('q2')
            q3 = x.get('q3')
            bestTime = compareQualiTimes(q1, q2, q3)
            if (bestTime is not None):
                #If is 'None', don't add to results at all!
                lastBestTime = slowerTime(lastBestTime, bestTime)
                qs.append( (x.get('driverId'), x.get('constructorId'), lastBestTime) ) #A tuple
        qualiResultsData[raceId] = qs

def getDriversData(cursor, driversData):
    '''Gathers the wanted data from all drivers'''
    sql = "SELECT `driverId`, `forename`, `surname` FROM `drivers`"
    cursor.execute(sql)
    result = cursor.fetchall()
    for x in result:
        driversData[x.get('driverId')] = x.get('forename') + " " + x.get('surname')

def getConstructorData(cursor, constructorsData):
    '''Gathers the wanted data from all constructors'''
    sql = "SELECT `constructorId`, `name` FROM `constructors`"
    cursor.execute(sql)
    result = cursor.fetchall()
    for x in result:
        constructorsData[x.get('constructorId')] = x.get('name')

def getEngineData(enginesData):
    '''Gathers the wanted data from all engines'''
    df = pd.read_csv('Engines.csv', names=['engineId', 'name'])
    for row in df.itertuples():
        #The index value is 0: meaning 1=id, 2=name
        enginesData[row[1]] = row[2]
    #print(enginesData)

def addEngineToConstructor(seasonsData):
    '''Constructs a table that shows what engine each constructor used in a given year'''
    df = pd.read_csv('ConstructorEngines.csv')
    for row in df.itertuples():
        if row[1] != 2018:
            #The index value is 0: meaning 1=year, 2=teamId, 3=engineId
            seasonsData[row[1]].addConstructorEngine(row[2], row[3])

def getTeamChangeData(seasonsData):
    '''Constructs a table that shows when a team changed its name and ID, therefore tying the two together'''
    df = pd.read_csv('TeamChanges.csv')
    for row in df.itertuples():
        if row[1] != 2018:
            #The index value is 0: meaning 1=year, 2=newId, 3=oldId
            seasonsData[row[1]].addTeamChange(row[2], row[3])