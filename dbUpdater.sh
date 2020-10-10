#Del old db file:
rm f1db.sql
rm f1db.sql.gz

#Get most recent version of database from the internet and extract it
wget http://ergast.com/downloads/f1db.sql.gz
gunzip f1db.sql.gz

#Run the SQL dump on the database
db_username=$(grep -Po '(?<=^db_username=)\w*$' 'user_variables.txt')
db_password=$(grep -Po '(?<=^db_password=)\w*$' 'user_variables.txt')
db_database=$(grep -Po '(?<=^db_database=)\w*$' 'user_variables.txt')
mysql -u $db_username -p$db_password -D $db_database < f1db.sql

#Clean data
python3 dataclean-script.py
python3 raceModelDataCleaner.py

# Generate predictions
python3 qualiModelTrainer.py
python3 generate-predictions.py