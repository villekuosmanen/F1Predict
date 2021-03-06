

class LinearModel:

    def __init__(self, k_rookie_pwr, k_rookie_variance):
        self.theta = [0, 0, 0, 0, 0, 0, 0] # Weights: Driv, cons, eng, track-specifics and intercept
        self.resetVariables()
        self.k_rookie_pwr = k_rookie_pwr
        self.k_rookie_variance = k_rookie_variance

    def resetVariables(self):
        self.drivers = {}  # DriverId, Driver	
        self.constructors = {}  # ConstructorId, Constructor	
        self.engines = {}  # EngineId, Engine	
        self.driver_variances = []	
        self.const_variances = []	
        self.engine_variances = []

    def addNewDriver(self, did, name, cid):
        self.drivers[did] = Driver(name, self.constructors[cid])
        self.drivers[did].pwr = self.k_rookie_pwr
        self.drivers[did].variance = self.k_rookie_variance

    def addNewCircuit(self, driverID, circuitId):
        if circuitId not in self.drivers[driverID].trackpwr:
            self.drivers[driverID].trackpwr[circuitId] = 0
        if circuitId not in self.drivers[driverID].constructor.trackpwr:
            self.drivers[driverID].constructor.trackpwr[circuitId] = 0
        if circuitId not in self.drivers[driverID].constructor.engine.trackpwr:
            self.drivers[driverID].constructor.engine.trackpwr[circuitId] = 0

class Engine:
    """The model for a F1 engine.
        param name:     Name of the engine manufacturer.
        param pwr:      The power ranking of the engine that shows what kind of results is expected from drivers whose cars use it.
        param trackpwr: A dictionary of circuit ids and power rankings, predicting how well the engine does on that track on average."""
    def __init__(self, name):
        self.name = name
        self.trackpwr = {}
        self.pwr = 0
        self.variance = 0.7

class Constructor:
    """The model for a F1 constructor.
        param name:     Name of the constructor.
        param pwr       The power ranking of the constructor that shows what kind of results is expected from its drivers.
        param trackpwr: A dictionary of circuit ids and power rankings, predicting how well the constructor does on that track on average.
        param engine:   The engine model object that this constructor currently uses.
        """
    def __init__(self, name, engine):
        self.name = name
        self.trackpwr = {}
        self.pwr = 0
        self.engine = engine
        self.variance = 0.7

class Driver:
    """The model for a F1 driver.
        param name:         Name of the driver.
        param pwr:          The power ranking of the driver that shows what kind of results is expected from them.
        param trackpwr:     A dictionary of circuit ids and power rankings, predicting how well the driver does on that track on average.
        param constructor:  The constructor model object that this driver currently drives for.
        """
    def __init__(self, name, constructor):
        self.name = name
        self.trackpwr = {}
        self.constructor = constructor
        #Rookie/new driver: special value?
        self.pwr = 0
        self.variance = 0.7
    def changeConstructor(self, constructor):
        self.constructor = constructor
        #change power levels?