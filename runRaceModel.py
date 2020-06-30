import pickle

from python.race_model.EloRaceModel import EloRaceModelGenerator, EloRaceModel


#Read user variables:
user_vars = {}
with open("user_variables.txt") as f:
    for line in f:
        key, value = line.partition("=")[::2]
        user_vars[key.rstrip()] = value.rstrip()

with open('data/raceSeasonsData.pickle', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/raceResultsData.pickle', 'rb') as handle:
    raceResultsData = pickle.load(handle)
    
with open('data/driversData.pickle', 'rb') as handle:
    driversData = pickle.load(handle)
    
with open('data/constructorsData.pickle', 'rb') as handle:
    constructorsData = pickle.load(handle)
    
with open('data/enginesData.pickle', 'rb') as handle:
    enginesData = pickle.load(handle)

generator = EloRaceModelGenerator(seasonsData, raceResultsData, driversData, constructorsData, enginesData)
predictions = generator.generatePredictions()
raceModel = generator.getModel()

# for driver in raceModel.drivers.values():
#     print(driver)
#     print("{}: {}".format(driver.name, driver.rating))
print("Predictions:")
for pred in predictions[-5:]:
    for driverId in pred:
        print(raceModel.drivers[driverId].name)
    print("\n")
