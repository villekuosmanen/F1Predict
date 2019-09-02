# F1Predict

A project for predicting F1 qualifying results using statistical analysis, machine learning and a Monte Carlo simulation. For visualising the predictions, see [F1PredictWeb](https://github.com/villekuosmanen/F1PredictWeb). Created by Ville Kuosmanen.

The project uses the [Ergast F1 API](https://ergast.com/mrd/) for statistical data.

## Running the project

In order to run the prediction generator you first need to set up the SQL database where a local copy of the F1 data will be stored. To pull data from Ergast API, a convenience script `dbUpdater.sh` exists, which will download a database dump and run it on the local database. Replace your database name, username and password in the script with your own versions. You will also have to replace them inside `dataclean-script.py`. You will have to install pip packages used by these Python scripts -- we recommend using a virtual envirionment (A requirements.txt -file will be provided for convenience in the future).

To generate the predictions files, a Jupyter Notebook `ModelEvaluation.ipynb` is provided. Simply run all cells, and the file will be automatically saved in the data-folder of the F1PredictWeb-project, should one exist (you can replace the filepath if you want).

## Documentation

See the project Wiki for further details.

## How to contribute

If you're interested in contributing to the project, feel free to open an issue about the feature or improvement you would like to add. If an issue for it already exists, comment under it to express your interest.
