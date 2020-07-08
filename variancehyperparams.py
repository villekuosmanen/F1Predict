from python import *

import pickle
import numpy as np

cleaner = None
for i in range(5):
    print("i=" + str(i))
    variance_regress = 0.90 + 0.05*i
    for m in range(5):
        print("m=" + str(m))
        with open('out/trained_cleaner.pickle', 'rb') as handle:
            cleaner = pickle.load(handle)
        cleaner.k_variance_multiplier_end = variance_regress
        cleaner.k_rookie_variance = 1
        cleaner.k_driver_variance_change = 0.1 + 0.05*m
        cleaner.k_const_variance_change = 0.05 + 0.05*m
        cleaner.k_engine_variance_change = 0.02 + 0.02*m

        cleaner.constructDataset()
        print("Driver variance MAE= " + str(mean(cleaner.driver_variances)))
        print("Constructor variance MAE= " + str(mean(cleaner.const_variances)))
        print("Engine variance MAE= " + str(mean(cleaner.engine_variances)))