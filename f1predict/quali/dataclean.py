import pymysql
import pymysql.cursors
import json

from f1predict.common.Season import Season
from f1predict.common.RaceData import RaceData

def compareQualiTimes(q1, q2, q3):
    """Returns the best time of the three"""
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
    """Returns the faster time, or either of them if they are equal"""
    if previous is None:
        return current
    elif current is None:
        return previous
    
    if previous < current:
        return previous
    else:
        return current
    
def slowerTime(previous, current):
    """Returns the slower time, or either of them if they are equal"""
    if previous is None:
        return current
    elif current is None:
        return previous
    
    if previous < current:
        return current
    else:
        return previous

def addSeason(cursor, seasonsData, qualiResultsData, qualiChanges, year):
    """Adds a Season Data object to the given map of seasons"""
    s = Season()
    q3no = 0
    q2no = 0
    futureRaces = None  # Used when a race has no data yet
    
    sql = "SELECT `raceId`, `round`, `circuitId`, `name` FROM `races` WHERE `year`=%s"
    cursor.execute(sql, year)
    result = cursor.fetchall()
    no_mistakes = 0
    
    for x in result:
        circuitId = x.get('circuitId')
        roundNo = x.get('round')

        #Inefficient to loop through every time, but doesn't matter here
        for index, row in qualiChanges.iterrows():
            if int(row["Year"]) == year and int(row["Race"]) == roundNo:
                print("quali change")
                q3no = row["Q3"]
                q2no = row["Q2"]
                break

        raceData = RaceData(circuitId, roundNo)
        s.addRace(x.get('raceId'), raceData)
        res, mistakes = addQualiResults(cursor, qualiResultsData, q3no, q2no, x.get('raceId'))
        no_mistakes += mistakes
        if not res:
            # Fail: there were no quali results! Therefore add race to future races object
            if futureRaces is None:
                futureRaces = []
            futureRaces.append({
                "raceId": x.get('raceId'),
                "name": x.get('name'),
                "circuitId": x.get('circuitId'),
                "year": year
            })
    if futureRaces is not None:
        with open('data/futureRaces.json', 'w') as fp:
            json.dump(futureRaces, fp)
    seasonsData[year] = s
    return no_mistakes

def addQualiResults(cursor, qualiResultsData, q3no, q2no, raceId):
    """Adds quali results from a race. Each result has a separate object for each driver's performance
    
        Returns true if quali results were found, and false otherwise"""
    qs = []
    mistakes = 0
    
    sql = "SELECT `driverId`, `constructorId`, `q1`, `q2`, `q3`, `position` FROM `qualifying` WHERE `raceId`=%s"
    cursor.execute(sql, raceId)
    result = cursor.fetchall()
    if result:
        result.sort(key=lambda result: result['position']) 
        fastestTimeOfAll = None
        for index, x in enumerate(result):
            #Use q1, q2 and q3 to identify best time
            q1 = x.get('q1')
            q2 = x.get('q2')
            q3 = x.get('q3')
            bestTime = compareQualiTimes(q1, q2, q3)
            if (index < q3no and (q3 is None or not q3)) or (index < q2no and (q2 is None or not q2)) or not q1:
                #Driver didn't participate to a qualifying they got in. Can take several actions but now just ignore them
                print("Race " + str(raceId) + ", place " + str(index + 1) + " failed to set a time")
                mistakes += 1
                continue

            if (fastestTimeOfAll == None):
                fastestTimeOfAll = bestTime
            if bestTime is not None:
                #If is 'None', don't add to results at all!
                #lastBestTime = slowerTime(lastBestTime, bestTime)
                if bestTime < 1.07*fastestTimeOfAll:    #Using a 107% rule
                    qs.append( (x.get('driverId'), x.get('constructorId'), bestTime) ) #A tuple
                else:
                    mistakes += 1
            else:
                mistakes += 1
        qualiResultsData[raceId] = qs
        return True, mistakes
    return False, mistakes