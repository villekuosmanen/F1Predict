import pymysql
import pymysql.cursors
import pandas as pd

def getDriversData(cursor, driversData):
    """Gathers the wanted data from all drivers"""
    sql = "SELECT `driverId`, `forename`, `surname` FROM `drivers`"
    cursor.execute(sql)
    result = cursor.fetchall()
    for x in result:
        driversData[x.get('driverId')] = x.get('forename') + " " + x.get('surname')

def getConstructorData(cursor, constructorsData):
    """Gathers the wanted data from all constructors"""
    sql = "SELECT `constructorId`, `name` FROM `constructors`"
    cursor.execute(sql)
    result = cursor.fetchall()
    for x in result:
        constructorsData[x.get('constructorId')] = x.get('name')

def getEngineData(enginesData):
    """Gathers the wanted data from all engines"""
    df = pd.read_csv('data/Engines.csv', names=['engineId', 'name'])
    for row in df.itertuples():
        #The index value is 0: meaning 1=id, 2=name
        enginesData[row[1]] = row[2]

def addEngineToConstructor(seasonsData):
    """Constructs a table that shows what engine each constructor used in a given year"""
    df = pd.read_csv('data/ConstructorEngines.csv')
    for row in df.itertuples():
        #The index value is 0: meaning 1=year, 2=teamId, 3=engineId
        seasonsData[row[1]].addConstructorEngine(row[2], row[3])

def getTeamChangeData(seasonsData):
    """Constructs a table that shows when a team changed its name and ID, therefore tying the two together"""
    df = pd.read_csv('data/TeamChanges.csv')
    for row in df.itertuples():
        #The index value is 0: meaning 1=year, 2=newId, 3=oldId
        seasonsData[row[1]].addTeamChange(row[2], row[3])


