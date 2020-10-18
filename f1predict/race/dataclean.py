import pymysql
import pymysql.cursors

from f1predict.common.Season import Season
from f1predict.common.RaceData import RaceData

def addRaceSeasonData(cursor, seasonsData, raceResultsData, year):
    """Adds a Season Data object to the given map of seasons"""
    s = Season()

    sql = "SELECT `raceId`, `round`, `circuitId`, `name` FROM `races` WHERE `year`=%s"
    cursor.execute(sql, year)
    result = cursor.fetchall()
    
    for x in result:
        circuitId = x.get('circuitId')
        roundNo = x.get('round')

        raceData = RaceData(circuitId, roundNo)
        s.addRace(x.get('raceId'), raceData)
        addRaceResults(cursor, raceResultsData, x.get('raceId'))
    seasonsData[year] = s

def addRaceResults(cursor, raceResultsData, raceId):
    """Adds race results data"""
    sql = "SELECT `driverId`, `constructorId`, `position`, `grid`, `status`.status as status \
        FROM `results`, `status` WHERE `raceId`=%s AND `status`.statusId = `results`.statusId"
    cursor.execute(sql, raceId)
    result = cursor.fetchall()

    if result:
        result.sort(key=lambda result: (result['position'] is None, result['position']))
    raceResultsData[raceId] = result