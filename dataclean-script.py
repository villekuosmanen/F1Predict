#import statements

#This non-descript folder contains all the standalone python modules
from python import *

import pymysql
import pymysql.cursors
import pandas as pd
import numpy as np
import pickle

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

#Read user variables:
user_vars = {}
with open("user_variables.txt") as f:
    for line in f:
        key, value = line.partition("=")[::2]
        user_vars[key.rstrip()] = value.rstrip()

#Set up a database connection:
connection = pymysql.connect(host='localhost',
                             user=user_vars['db_username'],
                             password=user_vars['db_password'],
                             db=user_vars['db_database'],
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

with open('data/seasonsData.txt', 'wb') as out:
    pickle.dump(seasonsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/qualiResultsData.txt', 'wb') as out:
    pickle.dump(qualiResultsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/driversData.txt', 'wb') as out:
    pickle.dump(driversData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/constructorsData.txt', 'wb') as out:
    pickle.dump(constructorsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/enginesData.txt', 'wb') as out:
    pickle.dump(enginesData, out, protocol=pickle.HIGHEST_PROTOCOL)