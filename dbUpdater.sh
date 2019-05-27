#Del old db file:
rm f1db.sql
rm f1db.sql.gz

#Get most recent version of database from the internet
wget http://ergast.com/downloads/f1db.sql.gz

#Move it to right place
#Not needed (?)

#Extract it
gunzip f1db.sql.gz

#Run it to the database
mysql -u f1user -pf1pw -D f1db < f1db.sql

#Run the python script on it
python3 dataclean-script.py


