import random

RANDOM_STANDARD_DEVIATION = 250

def simulateRace(raceModel, grid, circuit):
    # At the beginning, adjust the ranking of each participating driver, constructor or engine randomly upwards
    adjustedConstructors = set()
    adjustedEngines = set()
    for did in grid:
        raceModel.drivers[did].rating += random.normalvariate(0, RANDOM_STANDARD_DEVIATION)

        if raceModel.drivers[did].constructor not in adjustedConstructors:
            raceModel.drivers[did].constructor.rating += random.normalvariate(0, RANDOM_STANDARD_DEVIATION) # TODO
            adjustedConstructors.add(raceModel.drivers[did].constructor)

            if raceModel.drivers[did].constructor.engine not in adjustedEngines:
                raceModel.drivers[did].constructor.engine.rating += random.normalvariate(0, RANDOM_STANDARD_DEVIATION) # TODO
                adjustedEngines.add(raceModel.drivers[did].constructor.engine)

    # Adjust track alpha up or down randomly
    raceModel.tracks[circuit] *= random.normalvariate(1, 0.15) # TODO

    # Get GAElo for everyone, sort and return the list
    gaElos = []
    for gridPosition, did in enumerate(grid):
        gaElo = raceModel.getGaElo(did, gridPosition, circuit)

        randCeck = random.random()
        if randCeck > 0.75:
            gaElo += random.uniform(-2*RANDOM_STANDARD_DEVIATION, RANDOM_STANDARD_DEVIATION)
        gaElos.append((did, gaElo))
    gaElos.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in gaElos]