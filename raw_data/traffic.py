"""
prepare_traffic.py
==================
Hierarchical Traffic benchmark (SF Bay Area freeway lane occupancy; 207 series = 1 + 2 + 4 + 200)
loaded with Nixtla's datasetsforecast, checked, and turned into temporal-GNN inputs with
hier_st_prep (bottom tensor, mask, S, HiGP `selects`, train-only graph, splits).

    pip install datasetsforecast
    python prepare_traffic.py --data-dir ./data --out ./prepared/traffic

On first use HierarchicalData.load downloads Nixtla's benchmark zip into --data-dir.
"""
import argparse

import numpy as np
from datasetsforecast.hierarchical import HierarchicalData, HierarchicalInfo

import hier_st_prep as hp


def pems_lane_index(n_lanes: int = 963, n_bottom: int = 200, seed: int = 13) -> np.ndarray:
    """Bottom{i+1} -> column index among the 963 PEMS-SF lanes, IF the benchmark was produced by
    import_traffic.py of the HierE2E / PROFHiT repos (np.random.seed(13), sampling without
    replacement). Combined with PEMS-SF's stations_list this would give real sensor ids.
    NOT verified against the raw UCI files."""
    return np.random.RandomState(seed).choice(n_lanes, size=n_bottom, replace=False)


def main(data_dir: str, out_dir: str, window: int, horizon: int, test_len: int,
         val_frac: float, k: int) -> hp.HierSTData:
    # 1) Nixtla's loader: Y_df (unique_id, ds, y), S_df (207 x 200), tags {level: ids}
    Y_df, S_df, tags = HierarchicalData.load(data_dir, "Traffic", cache=False)
    info = HierarchicalInfo["Traffic"]
    print(f"[nixtla] Y_df {Y_df.shape} | S_df {S_df.shape} | levels "
          f"{[(name, len(ids)) for name, ids in tags.items()]}")
    print(f"[nixtla] metadata: freq={info.freq} horizon={info.horizon} "
          f"papers_horizon={info.papers_horizon} seasonality={info.seasonality} "
          f"test_size={info.test_size}")
    total = Y_df[Y_df["unique_id"] == "Total"].sort_values("ds")["y"].to_numpy()
    print(f"[fingerprint] sum(y)={Y_df['y'].sum():.4f} Total[0]={total[0]:.4f} "
          f"Total[-1]={total[-1]:.4f}")

    # 2) Nixtla format -> bottom panel + given hierarchy (tree + coherence checks inside)
    panel, hier = hp.panel_from_nixtla(Y_df, S_df, tags)

    # 3) GNN inputs. No missing values in this benchmark; calendar features are OFF because the
    #    dates are synthetic (see README notes in the reply / docstring below).
    cfg = hp.PrepConfig(hierarchy_cols=None, freq=panel.time_index.freqstr, missing="zero",
                        supervise_from=None, val_frac=val_frac, test_len=test_len,
                        calendar_features=False)
    data = hp.prepare(panel, cfg, graph="knn", k=k, hierarchy=hier)

    # 4) the prepared data must agree with Nixtla exactly
    assert data.node_ids == [str(i) for i in S_df.index], "node order differs from S_df"
    assert np.array_equal(data.S.toarray(), S_df.to_numpy()), "S differs from S_df"
    wide = Y_df.pivot(index="ds", columns="unique_id", values="y")[S_df.index].to_numpy()
    assert np.allclose(data.y_all(), wide, rtol=1e-5, atol=1e-3), "S @ bottom != Y_df"
    print("[check] S == S_df, S @ bottom == Y_df at every level, HiGP selects reproduce S")

    # 5) summary
    print(f"[levels] {list(zip(data.level_names, data.level_sizes))} | HiGP {data.higp_model_kwargs()}")
    for name, (a, b) in data.split.items():
        n_win = len(hp.WindowDataset(data, name, window=window, horizon=horizon))
        print(f"[split] {name:5s}: steps {a:3d}-{b - 1:3d} ({b - a:3d} days, "
              f"{data.time_index[a].date()} .. {data.time_index[b - 1].date()}) | "
              f"{n_win} windows (W={window}, H={horizon})")
    deg = np.bincount(data.edge_index[1], minlength=data.n_bottom)
    print(f"[graph] {data.edge_index.shape[1]} directed edges over {data.n_bottom} lanes "
          f"(kNN k={k} on train correlation, symmetrized; degree {deg.min()}-{deg.max()})")
    data.save(out_dir)
    print(f"[saved] {out_dir}")
    return data


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="./data")
    p.add_argument("--out", default="./prepared/traffic")
    p.add_argument("--window", type=int, default=14)
    p.add_argument("--horizon", type=int, default=7)      # Nixtla papers_horizon
    p.add_argument("--test-len", type=int, default=91)    # Nixtla test_size (13 weeks)
    p.add_argument("--val-frac", type=float, default=0.1)
    p.add_argument("--k", type=int, default=10)
    a = p.parse_args()
    main(a.data_dir, a.out, a.window, a.horizon, a.test_len, a.val_frac, a.k)