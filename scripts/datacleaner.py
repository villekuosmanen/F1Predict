import pymysql
import pymysql.cursors
import pandas as pd
import numpy as np
import pickle

from f1predict.common import dataclean
from f1predict.common import file_operations

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
try:
    with connection.cursor() as cursor:
        dataclean.getDriversData(cursor, driversData)
        dataclean.getConstructorData(cursor, constructorsData)
        dataclean.getEngineData(enginesData)
finally:
    connection.close()

with open('data/driversData.pickle', 'wb') as out:
    pickle.dump(driversData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/constructorsData.pickle', 'wb') as out:
    pickle.dump(constructorsData, out, protocol=pickle.HIGHEST_PROTOCOL)
    
with open('data/enginesData.pickle', 'wb') as out:
    pickle.dump(enginesData, out, protocol=pickle.HIGHEST_PROTOCOL)