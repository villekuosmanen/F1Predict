# F1Predict

A project for predicting F1 qualifying results using statistical analysis, machine learning and a Monte Carlo simulation. For visualising the predictions, see [F1PredictWeb](https://github.com/villekuosmanen/F1PredictWeb). Created by Ville Kuosmanen.

The project uses the [Ergast F1 API](https://ergast.com/mrd/) for statistical data.

## Running the project

In order to run the prediction generator you first need to set up a MySQL database where a local copy of the F1 data will be stored. In addition, install the Pip packages required for the program by running the command `pip install -r requirements.txt`.

To pull data from Ergast API, a convenience script `dbUpdater.sh` exists, which will download a database dump and run it on the local database. To log in to your database, you need to specify the username, password and database name in question. These are specified in your local file `user_variables.txt`. Do not commit this file to Git.

The generated predictions are saved to a new file inside a target folder. The target folder is specified in `user_variables.txt`.

### Example `user_variables.txt` file:
db_username=username
db_password=password
db_database=f1db
predictions_output_folder=../F1PredictWeb/src/public/data/

The keys (left side of equation) must remain constant, but the values (right-hand side) can be changed to values you prefer. Bu using the example output folder, the predictions are automatically saved to F1ProjectWeb's data folder (if the repositories share the same root folder).

## How to contribute

If you're interested in contributing to the project, feel free to open an issue about the feature or improvement you would like to add. If an issue for it already exists, comment under it to express your interest.
