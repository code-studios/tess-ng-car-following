#!/usr/bin/env python3
"""
build_dataset_json.py

Reads:
  runs_manifest.csv    – model/volume/seed → run_folder (relative paths)
  dataset_profile.csv  – per-run QC metrics

Outputs:
  dataset.json         – structured, portable dataset manifest

Usage:
    python build_dataset_json.py

Run from the Net001-Copy.tess/ root directory.
Requires: pandas, json (stdlib).

After running, edit dataset.json and set the top-level key:
    "huggingface_url": "https://huggingface.co/datasets/YOUR-USERNAME/..."
to point to your Hugging Face dataset repository.
"""

import json
import os
import pandas as pd

MANIFEST = "runs_manifest.csv"
PROFILE  = "dataset_profile.csv"
OUT_JSON = "dataset.json"


def read_csv(path):
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    raise RuntimeError(f"Could not read {path} with any known encoding.")


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    manifest = read_csv(os.path.join(base, MANIFEST))
    profile  = read_csv(os.path.join(base, PROFILE))

    # Normalise column names
    manifest.columns = [c.strip().lower() for c in manifest.columns]
    profile.columns = [c.strip().lower()   for c in profile.columns]

    # Join on model/volume/seed (unique key across both tables)
    merge_keys = ["model", "volume", "seed"]
    merged = manifest.merge(profile, on=merge_keys, how="left")

    # Build per-run records with portable relative paths
    runs = []
    for _, row in merged.iterrows():
        folder = str(row.get("run_folder", ""))
        # Locate the trajectory CSV inside the folder
        traj_rel = None
        if folder:
            traj_dir = os.path.join(base, folder)
            if os.path.isdir(traj_dir):
                for f in os.listdir(traj_dir):
                    low = f.lower()
                    if "trajectory" in low and "basic" not in low and f.endswith(".csv"):
                        traj_rel = os.path.join(folder, f)
                        break

        record = {
            "model":        str(row["model"]).strip(),
            "volume":       int(row["volume"]),
            "seed":         int(row["seed"]),
            "run_folder":   folder,
            "trajectory":   traj_rel,      # relative path, None if not found
            "qc": {
                "complete":       bool(row["complete"])   if pd.notna(row.get("complete"))   else None,
                "n_vehicles":     int(row["n_vehicles"]) if pd.notna(row.get("n_vehicles")) else None,
                "rows":           int(row["rows"])        if pd.notna(row.get("rows"))       else None,
                "size_mb":        float(row["size_mb"])   if pd.notna(row.get("size_mb"))   else None,
                "duration_s":     float(row["duration_s"]) if pd.notna(row.get("duration_s")) else None,
                "speed_mean":      float(row["speed_mean"]) if pd.notna(row.get("speed_mean")) else None,
                "dt_ms":          float(row["dt_ms"])     if pd.notna(row.get("dt_ms"))     else None,
                "density":        float(row["density"])   if pd.notna(row.get("density"))   else None,
                "id_coverage":    float(row["id_coverage"]) if pd.notna(row.get("id_coverage")) else None,
            }
        }
        runs.append(record)

    # Summary stats
    complete_runs = [r for r in runs if r["qc"]["complete"] is True]
    total_mb = sum(r["qc"]["size_mb"] or 0 for r in runs)
    complete_mb = sum(r["qc"]["size_mb"] or 0 for r in complete_runs)

    n_complete = len(complete_runs)
    complete_by_model = {}
    for r in complete_runs:
        complete_by_model.setdefault(r["model"], []).append(r["volume"])

    out = {
        "_note": (
            "Edit huggingface_url below to point to your Hugging Face dataset repository "
            "after uploading the trajectory files."
        ),
        "huggingface_url": "https://huggingface.co/datasets/YOUR-USERNAME/tess-ng-car-following",
        "study": {
            "title": (
                "Behavioral Fidelity of Built-in Car-Following Models in TESS NG Microsimulation: "
                "A Controlled Work-Zone Bottleneck Characterization"
            ),
            "author": "Eni Solomon Laughter",
            "year": 2026,
            "doi": "10.1007/s13369-026-xxxxx",          # replace with actual DOI
            "paper_url": (
                "https://www.researchgate.net/publication/412751354_Behavioral_Fidelity_"
                "of_Built-in_Car-Following_Models_in_TESS_NG_Microsimulation_"
                "A_Controlled_Work-Zone_Bottleneck_Characterization"
            ),
            "license": "CC BY 4.0",
        },
        "simulation": {
            "simulator":    "TESS NG",
            "scenario":     "Controlled work-zone bottleneck — 3-lane, 300 m link; "
                           "middle segment of lane 3 temporarily closed",
            "vehicle_type": "Passenger car only",
            "run_duration_s": 600,
            "sampling_interval_ms": 33,
            "demand_levels_veh_h": [100, 200, 300, 400, 500, 650, 900, 1500],
            "random_seeds": [10, 300],
            "car_following_models": ["IDM", "OVM", "W74", "W99"],
        },
        "dataset": {
            "total_runs":       len(runs),
            "valid_runs":        n_complete,
            "total_size_mb":     round(total_mb, 1),
            "valid_size_mb":     round(complete_mb, 1),
            "valid_runs_per_model": {m: len(vs) for m, vs in complete_by_model.items()},
            "trajectory_schema": [
                "Time(ms)", "Vehicle ID", "X(m)", "Y(m)", "Z(m)",
                "Current Speed(m/s)", "Current Acceleration Speed(m/s²)",
                "Angle", "Lane Angle", "Travel Distance(m)",
                "Current Road Traveled Distance(m)", "Road ID",
                "Link/Connector",
                "Lane ID/Upstream Lane ID_Downstream Lane ID",
                "Lane Number/Upstream Lane Number_Downstream Lane Number"
            ],
            "qc_note": (
                "A run is VALID (complete=True) when: "
                "(a) time span starts ≤ 10 s and ends ≥ 590 s (export ran the full 600 s), AND "
                "(b) median per-vehicle frame density ≥ 0.85 (no mid-run data thinning). "
                "See the paper (Section 3.5.1) for full QC details."
            ),
        },
        "runs": runs,
    }

    out_path = os.path.join(base, OUT_JSON)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    print(f"Wrote {out_path}")
    print(f"  Total runs  : {len(runs)}")
    print(f"  Valid runs  : {n_complete}")
    print(f"  Total size  : {total_mb:.1f} MB  |  Valid runs size: {complete_mb:.1f} MB")
    print(f"\n  Per-model valid runs:")
    for m, vs in sorted(complete_by_model.items()):
        print(f"    {m}: {len(vs)} runs  volumes: {sorted(vs)}")


if __name__ == "__main__":
    main()
