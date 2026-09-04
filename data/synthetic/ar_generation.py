from cProfile import label
import os
import numpy as np
import matplotlib.pyplot as plt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG_DIR = os.path.join(PROJECT_ROOT, "fig")
os.makedirs(FIG_DIR, exist_ok=True)

# Step 0: Set-up
T = 100
t = np.arange(T)
rng = np.random.default_rng(42)

# 1. Generate AR + Seasonality + Trend
def make_leaf(phi, amp, slope, lc):
    trend = slope * t
    seasonality = amp * np.sin(2 * np.pi * t / 12)
    ar = np.zeros(T)
    for i in range(1,T):
        ar[i] = phi * ar[i-1] + rng.normal()
    y = ar + seasonality + trend
    plt.plot(y, color=lc, linewidth=1.0, alpha=0.7, linestyle="-", label=f"phi = {phi}")

    return {"y": y, "ar": ar, "trend": trend, "seasonality": seasonality}

# 2. Make leaf
A = make_leaf(phi=0.2, amp=3, slope=0.1, lc="k")
B = make_leaf(phi=0.7, amp=1, slope=-0.05, lc="orange")
C = make_leaf(phi=0.95, amp=5, slope=0.15, lc="lightgreen")

# 3. Build Hierarchy 
hierarchy = {
    "y": A["y"] + B["y"] + C["y"],
    "trend": A["trend"] + B["trend"] + C["trend"],
    "seasonality": A["seasonality"] + B["seasonality"] + C["seasonality"],
    "ar": A["ar"] + B["ar"] + C["ar"]
}

# 3.1 Sanity Check: Coherence for hierarchy
err = np.abs(hierarchy["y"] - (A["y"] + B["y"] + C["y"])).max()
print("Coherent Error (should be 0): ", err)

# 4. Inject Shock/Signal (generated ground-truth impact to node in location-wise and time window-wise)
# a. Set-up: Shock period and value
shock_s, shock_e, shock_v = 40, 50, 10.
shock = np.zeros(T)
shock[shock_s:shock_e] = shock_v

# b. inject shock into time series to A only 
# ===== so that can explain reconsiliation impact to B/C becasue dataset for B/C no change ======
A["shock"] = shock
B["shock"], C["shock"] = np.zeros(T), np.zeros(T)

A["y"] = A["y"] + A["shock"]

# c. update hierarchy
hierarchy = {
    "y": A["y"] + B["y"] + C["y"],
    "shock": A["shock"] + B["shock"] + C["shock"]
}

# (optional) d. Sanlity Check: all shock is from A in hierarchy
print("检查shock是否只存在A:")
print(" A shock total: ", A["shock"].sum())
print(" B shock total: ", B["shock"].sum())
print(" C shock total: ", C["shock"].sum())
print(" Hierarchy shock total: ", hierarchy["shock"].sum())
print("结论: ", "是的" if A["shock"].sum()==hierarchy["shock"].sum() else "Shock不只存在于A, 请检查！")


plt.legend()
plt.grid(True, which='both', linestyle="--", alpha=0.3)

plt.savefig(
    os.path.join(FIG_DIR, 'ar_plot.png'), 
    dpi=300, bbox_inches='tight', facecolor='white', edgecolor='k')
print(f"saved to {os.path.join(FIG_DIR, 'ar_plot.png')}")