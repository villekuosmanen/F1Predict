import pymysql
import pymysql.cursors
import pandas as pd
import numpy as np
import pickle

from f1predict.common import dataclean
from f1predict.common import file_operations
from f1predict.race import dataclean as race_dataclean

# Get season and race data
raceSeasonsData = {}

raceResultsData = {}

#Read user variables:
USER_VARS = file_operations.getUserVariables("user_variables.txt")

#Set up a database connection:
connection = pymysql.connect(host='localhost',
                             user=USER_VARS['db_username'],
                             password=USER_VARS['db_password'],
                             db=USER_VARS['db_database'],
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

try:
    with connection.cursor() as cursor:
        for year in range(2003, 2021):
            race_dataclean.addRaceSeasonData(cursor, raceSeasonsData, raceResultsData, year)
        dataclean.addEngineToConstructor(raceSeasonsData)
        dataclean.getTeamChangeData(raceSeasonsData)        
finally:
    connection.close()


# Save to pickle file
with open('data/raceSeasonsData.pickle', 'wb') as out:
    pickle.dump(raceSeasonsData, out, protocol=pickle.HIGHEST_PROTOCOL)

with open('data/raceResultsData.pickle', 'wb') as out:
    pickle.dump(raceResultsData, out, protocol=pickle.HIGHEST_PROTOCOL)