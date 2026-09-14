import array
from cProfile import label
import os
from tkinter.constants import S
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG_DIR = os.path.join(PROJECT_ROOT, "fig")
os.makedirs(FIG_DIR, exist_ok=True)

# Step 0: Set-up
T = 100
t = np.arange(T)
seasonality_period = 12
rng = np.random.default_rng(42)

# 1. Generate AR + Seasonality + Trend
def make_leaf(phi, amp, slope, lc, name):
    trend = slope * t
    seasonality = amp * np.sin(2 * np.pi * t / seasonality_period)
    ar = np.zeros(T)
    for i in range(1,T):
        ar[i] = phi * ar[i-1] + rng.normal()
    y = ar + seasonality + trend
    plt.plot(y, color=lc, linewidth=1.0, alpha=0.7, linestyle="-", label=f"{name} (phi = {phi})")

    return {"y": y, "ar": ar, "trend": trend, "seasonality": seasonality}

# 2. Make leaf
A = make_leaf(phi=0.2, amp=3, slope=0.1, lc="k", name="A")
B = make_leaf(phi=0.7, amp=1, slope=-0.05, lc="purple", name="B")
C = make_leaf(phi=0.95, amp=5, slope=0.15, lc="orange", name="C")


A_shock = {k: v.copy() for k, v in A.items()}   # 独立副本,改它不会动到 A

# 3. Build Hierarchy 
hierarchy = {

    "y": A["y"] + B["y"] + C["y"],
    "trend": A["trend"] + B["trend"] + C["trend"],
    "seasonality": A["seasonality"] + B["seasonality"] + C["seasonality"],
    "ar": A["ar"] + B["ar"] + C["ar"]
}
# plt.plot(hierarchy["y"], color="red", linewidth=1.0, alpha=0.7, linestyle="--", label="Total")

# 3.1 Sanity Check: Coherence for hierarchy
err = np.abs(hierarchy["y"] - (A["y"] + B["y"] + C["y"])).max()
print("Coherent Error (should be 0): ", err)

# 4. Inject Shock/Signal (generated ground-truth impact to node in location-wise and time window-wise)
# a. Set-up: Shock period and value
shock_s, shock_e, shock_v = 88, 96, 50*rng.random()   # 窗口落在预测区 [80,100) 内
shock = np.zeros(T)
shock[shock_s:shock_e] = shock_v

# b. inject shock into time series to A only 
# ===== so that can explain reconsiliation impact to B/C becasue dataset for B/C no change ======
A_shock["shock"] = shock
A["shock"], B["shock"], C["shock"] = np.zeros(T), np.zeros(T), np.zeros(T)

A_shock["y"] = A_shock["y"] + A_shock["shock"]
# plot the shocked copy of A (treated): same baseline as A, plus shock, different color
plt.plot(A_shock["y"], color="lightblue", linewidth=1.5, alpha=0.7, linestyle="--", label=f"A + shock({shock_v})")

# c. update hierarchy
hierarchy = {"shock": A["shock"] + B["shock"] + C["shock"]}

hierarchy_shock = hierarchy
hierarchy_shock ={
    "y": A_shock["y"] + B["y"] + C["y"],
    "shock": A_shock["shock"] + B["shock"] + C["shock"]
}

# (optional) d. Sanlity Check: all shock is from A in hierarchy
print("检查shock是否只存在A:")
print(" A shock total: ", A["shock"].sum())
print(" B shock total: ", B["shock"].sum())
print(" C shock total: ", C["shock"].sum())
print(" Hierarchy shock total: ", hierarchy["shock"].sum())
print(" A_shock shock total: ", A_shock["shock"].sum())
print(" Hierarchy shock total: ", hierarchy_shock["shock"].sum())
print("结论: ", "是的" if A_shock["shock"].sum()==hierarchy_shock["shock"].sum() else "Shock不只存在于A, 请检查！")

# 5. Forecastting Model - Seasonal Naive
def season_navie(hist:np.ndarray, m:int, h:int):
    """The simplest forecating model without parameters. Used for validation of problem reasonablity.
        m: seasonality period / number of time steps for 1 season
        h: prediction period / number of time steps for predistion
    """
    # cut idx of perdiction horizon from orginal ts
    hist_no_pred = np.asarray(hist[:len(hist)-h])
    # season naive model
    pred = np.zeros(h)
    for each_pred in range(h):
        idx = len(hist_no_pred) - m + (each_pred % m)
        pred[each_pred] = hist_no_pred[idx]
    # append pred, return new entire ts
    new_ts = np.append(hist_no_pred,pred)

    return new_ts

# 5.1 make forecast for baseline and treatment/shock
A_forcast = season_navie(A["y"], seasonality_period, 20)
plt.plot(A_forcast, color="r", linewidth=1.0, alpha=0.3, label="A_forecast")

A_shock_forcast = season_navie(A_shock["y"], seasonality_period, 20)
plt.plot(A_shock_forcast, color="green", linewidth=1.0, alpha=0.3, label="A_shock_forecast")


# Sanity Check
print(A["y"][68], A_forcast[80])
print(A_shock["y"][68], A_shock_forcast[80])


# 6. Routing Ablation
H = 20                       # 预测 horizon 长度(最后 H 步)
m = seasonality_period

# 每条 item 的真值(treated):A 真实打了 promo(在 horizon 窗口内),B/C 没有
true = {"A": A_shock["y"], "B": B["y"], "C": C["y"]}

# horizon 索引 + promo 窗口(落在 horizon 内)
h_idx = np.arange(T - H, T)                         # [80..99]
in_window = (h_idx >= shock_s) & (h_idx < shock_e)  # horizon 上标记 promo 生效的时刻
effect = shock_v

# 每条 item 的 seasonal-naive 底座预测(只取 horizon 部分;历史干净,不含 promo)
def naive_h(hist):
    return season_navie(np.asarray(hist), m, H)[-H:]

base = {k: naive_h(v) for k, v in true.items()}

def with_promo(f):                                  # 在窗口内加 effect
    f = f.copy(); f[in_window] += effect; return f

methods = {
    # 6.1 correct: promo 加在 A(判断对了),B/C 正常 naive
    "correct": {"A": with_promo(base["A"]), "B": base["B"], "C": base["C"]},
    # 6.2 wrong: promo 加在 B(判断错了),A/C 正常 naive
    "wrong":   {"A": base["A"], "B": with_promo(base["B"]), "C": base["C"]},
    # 6.3 no-routing: 三条都正常 naive,不加 effect
    "none":    {"A": base["A"], "B": base["B"], "C": base["C"]},
}

# 7. 用 MASE 比较三个方法
def mase(actual, forecast, train, m):
    train = np.asarray(train)
    scale = np.mean(np.abs(train[m:] - train[:-m]))   # 训练集内 seasonal-naive 的 MAE(尺度)
    return np.mean(np.abs(np.asarray(actual) - np.asarray(forecast))) / scale

print("\n===== Step 7: MASE(整体 / 只看窗口)=====")
for name, fc in methods.items():
    overall, window = [], []
    for k in ("A", "B", "C"):
        actual = true[k][T-H:]      # 真值(horizon 部分)
        train  = true[k][:T-H]      # 训练集(用于尺度归一)
        overall.append(mase(actual, fc[k], train, m))
        window.append(mase(actual[in_window], fc[k][in_window], train, m))
    print(f"{name:8s} overall={np.mean(overall):.3f}  window={np.mean(window):.3f}")

# Step LAST: plot & save figures
plt.legend()
plt.grid(True, which='both', linestyle="--", alpha=0.3)

plt.savefig(
    os.path.join(FIG_DIR, 'ar_plot.png'), 
    dpi=300, bbox_inches='tight', facecolor='white', edgecolor='k')
print(f"saved to {os.path.join(FIG_DIR, 'ar_plot.png')}")