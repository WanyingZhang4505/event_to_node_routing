import numpy as np

# 1. Basic AR(1) model
T = 100 # time steps
phi = 0.7 # AR cofficient
x = np.zeros(T) # initialize time series with zeros
x[0] = np.random.rand() # Initialize first value
epsilon = np.random.normal(0,1)

# Generate time series
for t in range (1, T):
    x[t] = phi * x[t-1] + epsilon[t]