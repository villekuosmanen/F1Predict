# DEPRECATED, DO NOT USE
# This file will be updated in the future

from python import *

import pickle
import numpy as np

cleaner = None
best_regress = None
best_driver = None
best_const = None
best_engine = None
for i in range(1):
    print("i=" + str(i))
    variance_regress = 1.5
    for m in range(12):
        with open('out/trained_cleaner.pickle', 'rb') as handle:
            cleaner = pickle.load(handle)
        cleaner.k_variance_multiplier_end = variance_regress
        cleaner.k_rookie_variance = 1
        cleaner.k_driver_variance_change = 0.18 + 0.02*m
        cleaner.k_const_variance_change = 0.12 + 0.02*m
        cleaner.k_engine_variance_change = 0.06 + 0.01*m

        cleaner.constructDataset()
        overall_variance = (mean(cleaner.driver_variances) + mean(cleaner.const_variances) + mean(cleaner.engine_variances))
        if best_regress is None or best_regress[1] > overall_variance:
            best_regress = (cleaner.k_variance_multiplier_end, overall_variance)
        if best_driver is None or best_driver[1] > mean(cleaner.driver_variances):
            best_driver = (cleaner.k_driver_variance_change, mean(cleaner.driver_variances))
        if best_const is None or best_const[1] > mean(cleaner.const_variances):
            best_const = (cleaner.k_const_variance_change, mean(cleaner.const_variances))
        if best_engine is None or best_engine[1] > mean(cleaner.engine_variances):
            best_engine = (cleaner.k_engine_variance_change, mean(cleaner.engine_variances))

print("Regress variance param= " + str(best_regress[0]))
print("Driver variance param= " + str(best_driver[0]))
print("Constructor variance param= " + str(best_const[0]))
print("Engine variance param= " + str(best_engine[0]))