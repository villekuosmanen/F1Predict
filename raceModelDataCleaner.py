#This non-descript folder contains all the standalone python modules
from python import *

import pymysql
import pymysql.cursors
import pandas as pd
import numpy as np
import pickle

# Get season and race data
raceSeasonsData = {}

raceResultsData = {}

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

try:
    with connection.cursor() as cursor:
        for year in range(2003, 2021):
            addRaceSeasonData(cursor, raceSeasonsData, raceResultsData, year)         
finally:
    connection.close()


# Save to pickle file
with open('data/raceSeasonsData.pickle', 'wb') as out:
    pickle.dump(raceSeasonsData, out, protocol=pickle.HIGHEST_PROTOCOL)

with open('data/raceResultsData.pickle', 'wb') as out:
    pickle.dump(raceResultsData, out, protocol=pickle.HIGHEST_PROTOCOL)