import random

# TODO investigate if deviation should be different for drivers, constructors and engines
RANDOM_STANDARD_DEVIATION = 220

def simulateRace(raceModel, grid, circuit):
    # At the beginning, adjust the ranking of each participating driver, constructor or engine randomly up or down
    adjustedConstructors = set()
    adjustedEngines = set()
    for did in grid:
        raceModel.drivers[did].rating += random.normalvariate(0, RANDOM_STANDARD_DEVIATION)

        if raceModel.drivers[did].constructor not in adjustedConstructors:
            raceModel.drivers[did].constructor.rating += random.normalvariate(0, RANDOM_STANDARD_DEVIATION)
            adjustedConstructors.add(raceModel.drivers[did].constructor)

            if raceModel.drivers[did].constructor.engine not in adjustedEngines:
                raceModel.drivers[did].constructor.engine.rating += random.normalvariate(0, RANDOM_STANDARD_DEVIATION)
                adjustedEngines.add(raceModel.drivers[did].constructor.engine)

    # Adjust track alpha up or down randomly
    raceModel.tracks[circuit] *= random.normalvariate(1, 0.15) # TODO investigate what value works best

    gaElos = []
    retiredDrivers = []
    for gridPosition, did in enumerate(grid):
        gaElo = raceModel.getGaElo(did, gridPosition, circuit)

        # Simulate "major event", allows participant to have a major gain or loss
        randCeck = random.random()
        if randCeck < 0.20:
            gaElo += random.uniform(-2*RANDOM_STANDARD_DEVIATION, RANDOM_STANDARD_DEVIATION)

        # Simulate retirement
        randCeck = random.random()
        if randCeck < raceModel.getRetirementProbability(circuit):
            retiredDrivers.append(did)
        else: 
            gaElos.append((did, gaElo))
    gaElos.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in gaElos], retiredDrivers