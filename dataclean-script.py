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

#Set up a database connection:

#I know, I know, this is fucking horrible data security buy who cares tbh
connection = pymysql.connect(host='localhost',
                             user='f1user',
                             password='f1pw',
                             db='f1db',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

qualiChanges = pd.read_csv('data/qualiChanges.csv')
print(qualiChanges)
try:
    with connection.cursor() as cursor:
        getDriversData(cursor, driversData)
        getConstructorData(cursor, constructorsData)
        for x in range(2003, 2020):
            addSeason(cursor, seasonsData, qualiResultsData, qualiChanges, x)
        getEngineData(enginesData)
        addEngineToConstructor(seasonsData)
        getTeamChangeData(seasonsData)
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