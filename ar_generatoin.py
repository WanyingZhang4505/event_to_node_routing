import os
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

FIG_DIR = "fig"
os.makedirs(FIG_DIR, exist_ok=True)

# # 1. Basic AR(1) model [Learning Purpose]
# T = 100 # time steps
# phi = [0.2, 0.7, 0.95] # AR cofficient
# x = np.zeros(T) # initialize time series with zeros
# x[0] = np.random.rand() # Initialize first value

# # Generate time series
# for phi, lc in zip([0.2, 0.7, 0.95], ["orange", "grey", "lightgreen"]):
#     x = np.zeros(T)
#     x[0] = np.random.rand()
#     for t in range (1, T):
#         x[t] = phi * x[t-1]+np.random.normal()
#     plt.plot(x, color=lc, linewidth=1,
#         # alpha=0.7, color="black",
#         # marker='*', markersize=4, markevery=10,
#         # markerfacecolor="yellow", markeredgecolor="black", markeredgewidth=1,
#         label=f"phi = {phi}")
#     plt.axhline(x.mean(), color=lc, linestyle="--", linewidth=1, alpha=0.6)

# plt.legend()
# plt.grid(True, which="both", linestyle="--", alpha=0.3)
# plt.savefig("ar_plot.png", 
#     dpi=300, 
#     bbox_inches="tight",
#     facecolor="white",
#     edgecolor="black")
# print("saved to ar_plot.png")



# 2. AR(1) model with trend & seasonality (clean version)
T = 100
t = np.arange(T)    # an array

# Trend
slope = 0.1         # 整体上升趋势
trend = slope * t     # apply to all numbers in the array

# Seasonality
period = 12     # seasonality occurs every 12 periods
amplitude = 3   # 波峰振幅

seasonality = amplitude * np.sin(2 * np.pi * t / period)

for phi, lc in zip([0.2, 0.7, 0.95], ['orange', 'k', 'lightgreen']):
    ar = np.zeros(T)
    ar[0] = np.random.rand()
    for t in range(1,T):
        ar[t] = phi * ar[t-1] + np.random.normal()
    y = trend + seasonality + ar
    plt.plot(y, color=lc, linewidth=1, label=f'phi = {phi}')
    plt.axhline(y.mean(), color=lc, linewidth=1, linestyle="--", alpha=0.6)

plt.legend()
plt.grid(True, which='both', linestyle="--", alpha=0.3)
plt.savefig(
    os.path.join(FIG_DIR, 'ar_plot.png'), 
    dpi=300, bbox_inches='tight', facecolor='white', edgecolor='k')
print(f"saved to {os.path.join(FIG_DIR, 'ar_plot.png')}")