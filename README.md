# F1Predict

A project for predicting F1 qualifying results using statistical analysis, machine learning and a Monte Carlo simulation. For visualising the predictions, see [F1PredictWeb](https://github.com/villekuosmanen/F1PredictWeb).

The project uses the [Ergast F1 API](https://ergast.com/mrd/) for statistical data.

## Running the project

In order to run the prediction generator you first need to set up a MySQL database where a local copy of the F1 data will be stored. You will also need Python 3 and Pip. These instructions should work in Linux and MacOS computers (unfortunately there may be problems with installing certain Python packages in Windows).

The instructions are as follows:
- Fork and clone F1Predict on GitHub
- Install MySQL on your computer (this may already be installed)
- Set up a local database for your MySQL program. It doesn't need to have any tables. This will be used for storing the F1 data used by the program.
- Set up a username-password account for your F1 database
- (Optional) Clone F1PredictWeb in the same parent folder as you cloned F1Predict.
- Create a file `user-variables.txt` inside F1Predict (see example below). Change the values of each field to match the values in your local database.
- Create a new Python virtual environment and activate it. `python3 -m venv <environment name>`, and `. venv/bin/activate`
- Run `pip install -r requirements.txt`.
    - This command also attempts to install the local F1Predict package from source control. I'm not sure if it will work correctly. If not, run the commands `python3 setup.py sdist bdist_wheel` and `pip install -e .` inside the `F1Predict` folder
- Run `sh dbUpdater.sh`. This adds most recent data to your local database and runs the program, generating predictions to the output folder specified in user-variables.txt

### Example `user_variables.txt` file:
db_username=username  
db_password=password  
db_database=f1db  
predictions_output_folder=../F1PredictWeb/src/public/data/

The keys (left side of equation) must remain constant, but the values (right-hand side) can be changed to values you prefer. Bu using the example output folder, the predictions are automatically saved to F1ProjectWeb's data folder (if the repositories share the same root folder).

## Package structure

The `f1predict` folder contains the models, and utility and common code for running them. It is structured in classes and runnable functions. This package is designed to be as self-contained as possible, and as such it needs to be locally installed in order to use the scripts and notebooks below.

The `scripts` folder contains scripts, each corresponding to a particular workflow. The shell script `dbUpdater.sh` runs them to generate qualifying an (pre-quali) race predictions, as well as generating all models for most recent data. The script `runRaceModel.py` generates post-quali predictions for a particular grid.

The `notebooks` folder contains Jupyter Notebooks, which are mainly used for evaluating the models, and investigating the data.

## How to contribute

If you're interested in contributing to the project, feel free to open an issue about the feature or improvement you would like to add. If an issue for it already exists, comment under it to express your interest. If you don't have a specific issue in mind but would like to contribute, you can open a new issue saying you'd like to contribute

## Credits

### Qualifying model
- Ville Kuosmanen

### Race model
- Ville Kuosmanen
- Raiyan Chowdhury
- Philip Searcy

### Special thanks
- [Ergast F1 API](https://ergast.com/mrd/)
