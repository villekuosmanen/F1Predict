class QualiLinearModel:

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