# Delete old SQL files:
rm f1db.sql
rm f1db.sql.gz

# Get most recent database dump from the internet and extract it
wget http://ergast.com/downloads/f1db.sql.gz
gunzip f1db.sql.gz

# Run the database dump SQL file to the database
# Note that this resets everything in the database
db_username=$(grep -Po '(?<=^db_username=)\w*$' 'user_variables.txt')
db_password=$(grep -Po '(?<=^db_password=)\w*$' 'user_variables.txt')
db_database=$(grep -Po '(?<=^db_database=)\w*$' 'user_variables.txt')
mysql -u $db_username -p$db_password -D $db_database < f1db.sql

# Run data cleaning scripts
python3 scripts/datacleaner.py
python3 scripts/datacleaner_quali.py
python3 scripts/datacleaner_race.py

# Run scripts that generate predictions
python3 scripts/qualiModelTrainer.py
python3 scripts/generate-predictions.py