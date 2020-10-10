import pymysql
import pymysql.cursors
import pandas as pd
import numpy as np
import pickle

from python.common import file_operations
from python import *

#Create data classes
#Year, Season
seasonsData = {}
#RaceId, List of tuples of (driverId, constructorId, time)
qualiResultsData = {}
#DriverId, name
driversData = {}
#ConstructorId, name
constructorsData = {}
#EngineId, name
enginesData = {}

USER_VARS = file_operations.getUserVariables("user_variables.txt")

#Set up a database connection:
connection = pymysql.connect(host='localhost',
                             user=USER_VARS['db_username'],
                             password=USER_VARS['db_password'],
                             db=USER_VARS['db_database'],
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

qualiChanges = pd.read_csv('data/qualiChanges.csv')
print(qualiChanges)
try:
    with connection.cursor() as cursor:
        total_mistakes = 0
        getDriversData(cursor, driversData)
        getConstructorData(cursor, constructorsData)
        for x in range(2003, 2021):
            no_mistakes = addSeason(cursor, seasonsData, qualiResultsData, qualiChanges, x)
            total_mistakes += no_mistakes
        getEngineData(enginesData)
        addEngineToConstructor(seasonsData)
        getTeamChangeData(seasonsData)
        print(total_mistakes)
finally:
    connection.close()

with open('data/seasonsData.pickle', 'wb') as out:
    pickle.dump(seasonsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/qualiResultsData.pickle', 'wb') as out:
    pickle.dump(qualiResultsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/driversData.pickle', 'wb') as out:
    pickle.dump(driversData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/constructorsData.pickle', 'wb') as out:
    pickle.dump(constructorsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/enginesData.pickle', 'wb') as out:
    pickle.dump(enginesData, out, protocol=pickle.HIGHEST_PROTOCOL)