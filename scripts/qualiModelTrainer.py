import pickle
import numpy as np

from f1predict.quali.QualiDataProcessor import QualiDataProcessor

def gradient(x, err):
    grad = -(1.0/len(x)) * err @ x
    return grad

def squaredError(err):
    return err**2


with open('data/seasonsData.pickle', 'rb') as handle:
    seasonsData = pickle.load(handle)
    
with open('data/qualiResultsData.pickle', 'rb') as handle:
    qualiResultsData = pickle.load(handle)
    
with open('data/driversData.pickle', 'rb') as handle:
    driversData = pickle.load(handle)
    
with open('data/constructorsData.pickle', 'rb') as handle:
    constructorsData = pickle.load(handle)
    
with open('data/enginesData.pickle', 'rb') as handle:
    enginesData = pickle.load(handle)

processor = QualiDataProcessor(seasonsData, qualiResultsData, driversData, constructorsData, enginesData)

# Run gradient descent
alpha = 0.18
stop = 0.016
processor.processDataset()
model = processor.getModel()
entries, errors, results = processor.getDataset()
grad = gradient(entries, errors)

i = 0
while np.linalg.norm(grad) > stop and i < 40:
    # Move in the direction of the gradient
    # N.B. this is point-wise multiplication, not a dot product
    model.theta = model.theta - grad*alpha
    mae = np.array([abs(x) for x in errors]).mean()
    print(mae)

    processor.processDataset()
    entries, errors, results = processor.getDataset()
    grad = gradient(entries, errors)
    i += 1

print("Gradient descent finished. MAE="+str(mae))
model = processor.getModel()
print(model.theta)

with open('out/driver_variances.pickle', 'wb+') as out:
    pickle.dump(model.driver_variances, out, protocol=pickle.HIGHEST_PROTOCOL)
with open('out/const_variances.pickle', 'wb+') as out:
    pickle.dump(model.const_variances, out, protocol=pickle.HIGHEST_PROTOCOL)
with open('out/engine_variances.pickle', 'wb+') as out:
    pickle.dump(model.engine_variances, out, protocol=pickle.HIGHEST_PROTOCOL)

# Save model
with open('out/trained_quali_processor.pickle', 'wb+') as out:
    pickle.dump(processor, out, protocol=pickle.HIGHEST_PROTOCOL)

with open('out/trained_quali_model.pickle', 'wb+') as out:
    pickle.dump(model, out, protocol=pickle.HIGHEST_PROTOCOL)