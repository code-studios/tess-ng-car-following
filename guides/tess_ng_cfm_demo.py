#!/usr/bin/env python3
"""
=========================================================
tess_ng_cfm_demo.py
=========================================================
End-to-end walkthrough: how to get and read the TESS NG
Car-Following Model Benchmark Dataset from Hugging Face.

This script is the public reference implementation that
accompanies the dataset release on Hugging Face
(https://huggingface.co/datasets/eslaughter/tess-ng-car-following)
and the GitHub companion repository
(https://github.com/code-studios/tess-ng-car-following).

It is safe to run as-is on any machine with Python 3.9+
and an internet connection. No absolute file paths, no
private credentials, no OS-specific dependencies.

The script demonstrates seven steps:

  STEP 1   Install the required packages (huggingface_hub, pandas)
  STEP 2   Authenticate with Hugging Face (CLI or env var)
  STEP 3   Inspect the dataset repository structure on the Hub
  STEP 4   Download the manifest (dataset.json)
  STEP 5   Download one trajectory CSV
  STEP 6   Load the CSV with pandas and explore the schema
  STEP 7   Compute per-model summary statistics

Run:
    python tess_ng_cfm_demo.py
"""

# Make sure stdout can print any character even on Windows consoles
# that default to cp1252 (e.g. PowerShell on Win10).
import sys, io
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    # Python < 3.7 fallback (not strictly needed)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                                  errors="replace")

import os
import json
import time
import platform
from pathlib import Path

# Ensure deterministic ASCII output by replacing anything we cannot
# safely print. We use this helper anywhere user-controlled data
# might contain non-ASCII characters (TESS NG exports use Latin-1).
def ascii_safe(s: str) -> str:
    """Replace non-ASCII characters with `?` so the output never
    crashes on a console with a narrow default encoding."""
    return s.encode("ascii", "replace").decode("ascii")


# ===========================================================================
# STEP 1 -- Install required packages
# ===========================================================================
print("=" * 62)
print("STEP 1: Install required packages")
print("=" * 62)
print()

REQUIRED = {
    "huggingface_hub": "huggingface_hub",
    "pandas":          "pandas",
}

for module_name, pip_name in REQUIRED.items():
    try:
        __import__(module_name)
        print(f"  [OK]    '{pip_name}' is already installed")
    except ImportError:
        print(f"  [..]    Installing '{pip_name}' ...")
        import subprocess
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pip_name, "-q"]
        )
        print(f"  [OK]    '{pip_name}' installed")

import pandas as pd
from huggingface_hub import hf_hub_download, HfApi

print()


# ===========================================================================
# STEP 2 -- Authenticate with Hugging Face
# ===========================================================================
print("=" * 62)
print("STEP 2: Authenticate with Hugging Face")
print("=" * 62)
print()
print("  Two equivalent ways to authenticate:")
print()
print("    A) CLI login (one-time, persistent):")
print("         huggingface-cli login")
print("         # paste your HF token when prompted")
print()
print("    B) Environment variable (CI / automated):")
print('         export HF_TOKEN="hf_xxxxxxxxxxxx"')
print()
print("  The Hugging Face Python client will pick up whichever is set.")
print()

api = HfApi()
try:
    identity = api.whoami()
    print(f"  Logged in as : {ascii_safe(identity.get('name', 'unknown'))}")
    print(f"  Email        : {ascii_safe(identity.get('email', 'n/a'))}")
    print("  Auth OK      : True")
except Exception as exc:
    print(f"  AUTH FAILED : {exc}")
    print()
    print("  To fix: run `huggingface-cli login` (option A) or set the")
    print("  HF_TOKEN environment variable (option B), then re-run this script.")
    sys.exit(1)

print()


# ===========================================================================
# STEP 3 -- Inspect the repository
# ===========================================================================
print("=" * 62)
print("STEP 3: Inspect the dataset repository")
print("=" * 62)

REPO_ID = "eslaughter/tess-ng-car-following"
print(f"  Repo URL  : https://huggingface.co/datasets/{REPO_ID}")
print()

# A flat list of every file in the dataset repository.
all_files = list(api.list_repo_files(repo_id=REPO_ID, repo_type="dataset"))
print(f"  Total files in repo : {len(all_files)}")

# Group by top-level folder so a slide audience can see the layout.
folders = {}
root_files = []
for f in all_files:
    if "/" in f:
        top = f.split("/", 1)[0]
        folders.setdefault(top, []).append(f)
    else:
        root_files.append(f)

print(f"  Root-level files    : {root_files}")
print(f"  Top-level folders   : {len(folders)}")
for folder in sorted(folders):
    print(f"    {folder:<20s}  ({len(folders[folder])} files)")
print()


# ===========================================================================
# STEP 4 -- Download the manifest
# ===========================================================================
print("=" * 62)
print("STEP 4: Download the dataset manifest")
print("=" * 62)

# We use the directory of this script as the working area so the user
# always knows where the files go. No absolute paths are baked in.
OUT_DIR = Path(__file__).resolve().parent
print(f"  Working directory   : {OUT_DIR}")
print()

print("  Downloading dataset.json ...")
t0 = time.time()
manifest_path = hf_hub_download(
    repo_id=REPO_ID,
    filename="dataset.json",
    repo_type="dataset",
    local_dir=str(OUT_DIR),
    force_download=False,    # use cache if already present
)
print(f"  Downloaded in {(time.time()-t0):.1f}s")
print(f"  Manifest size       : {os.path.getsize(manifest_path) / 1024:.1f} KB")
print()

with open(manifest_path, encoding="utf-8") as f:
    meta = json.load(f)

study = meta["study"]
sim   = meta["simulation"]
ds    = meta["dataset"]

print("  Study metadata:")
print(f"    Title   : {ascii_safe(study['title'])}")
print(f"    Author  : {ascii_safe(study['author'])} ({study['year']})")
print(f"    License : {study['license']}")
print()
print("  Simulation design:")
print(f"    Simulator      : {sim['simulator']}")
print(f"    CF Models      : {', '.join(sim['car_following_models'])}")
print(f"    Demand levels  : {sim['demand_levels_veh_h']} veh/h")
print(f"    Random seeds   : {sim['random_seeds']}")
print()
print("  Dataset summary:")
print(f"    Total runs  : {ds['total_runs']}")
print(f"    Valid runs  : {ds['valid_runs']}")
print(f"    Total size  : {ds['total_size_mb']} MB")
print(f"    Valid size  : {ds['valid_size_mb']} MB")
print()


# ===========================================================================
# STEP 5 -- Download one trajectory CSV
# ===========================================================================
print("=" * 62)
print("STEP 5: Download one trajectory CSV file")
print("=" * 62)

# Pick one valid run with a small volume so the download is quick.
runs = meta["runs"]
demo_run = next(
    r for r in runs
    if r["model"] == "IDM" and r["seed"] == 10 and r["volume"] == 100
)
traj_rel = demo_run["trajectory"]
print(f"  Demo run       : {demo_run['run_folder']}")
print(f"  Remote path    : {traj_rel}")
print()

print("  Downloading (full file, ~5 MB) ...")
t0 = time.time()
local_traj = hf_hub_download(
    repo_id=REPO_ID,
    filename=traj_rel,
    repo_type="dataset",
    local_dir=str(OUT_DIR),
    force_download=False,
)
print(f"  Downloaded in {(time.time()-t0)*1000:.0f} ms")
print(f"  Local file     : {local_traj}")
print(f"  File size      : {os.path.getsize(local_traj) / 1e6:.2f} MB")
print()

# TESS NG exports use Latin-1 encoding (they contain superscript '2'
# characters and other Latin-1 glyphs that break UTF-8 readers).
df_preview = pd.read_csv(local_traj, nrows=5, encoding="latin-1")
print("  First 5 rows (preview):")
print(df_preview.to_string(max_colwidth=24))
print()


# ===========================================================================
# STEP 6 -- Load and explore with pandas
# ===========================================================================
print("=" * 62)
print("STEP 6: Load the CSV with pandas and explore it")
print("=" * 62)

print("  Loading full trajectory ...")
df = pd.read_csv(local_traj, encoding="latin-1", low_memory=False)
print(f"  Shape           : {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"  Columns         : {list(df.columns)}")
print()

# Column glossary for the slide audience.
print("  Column glossary:")
print("    Time(ms)                                  simulation time in milliseconds")
print("    Vehicle ID                                unique vehicle identifier")
print("    X(m), Y(m), Z(m)                          world position in metres")
print("    Current Speed(m/s)                        instantaneous speed")
print("    Current Acceleration Speed(m/s2)         longitudinal acceleration")
print("    Angle, Lane Angle                         heading / lane-relative angle")
print("    Travel Distance(m)                        cumulative distance travelled")
print("    Road ID / Link/Connector                  network element identifier")
print("    Lane ID, Lane Number                      lane assignment (current / upstream / downstream)")
print()

# Numeric summary
print("  Numeric column summary:")
desc = df.describe().to_string()
print(desc)
print()

# Coverage checks
n_vehicles = df["Vehicle ID"].nunique()
n_rows     = len(df)
time_span  = (df["Time(ms)"].max() - df["Time(ms)"].min()) / 1000  # seconds
hz         = (n_rows / time_span) if time_span > 0 else 0

print(f"  Unique vehicles  : {n_vehicles}")
print(f"  Time span        : {time_span:.1f} s")
print(f"  Rows per vehicle : {n_rows/n_vehicles:.0f}  (sampling ~ {hz:.0f} Hz)")

# Data-quality check
null_counts = df.isnull().sum()
bad_cols    = null_counts[null_counts > 0]
print()
if bad_cols.empty:
    print("  Null values     : none (clean data)")
else:
    print(f"  Null values     : {dict(bad_cols)}")

# ASCII-safe column-name pass (so the next step's headers never crash
# a narrow Windows console)
safe_cols = [ascii_safe(c) for c in df.columns]
df.columns = safe_cols
print()


# ===========================================================================
# STEP 7 -- Per-model summary statistics
# ===========================================================================
print("=" * 62)
print("STEP 7: Per-model summary statistics")
print("=" * 62)

valid_runs = [r for r in runs if r["qc"]["complete"]]
print(f"  {len(valid_runs)} valid runs across "
      f"{len(set(r['model'] for r in valid_runs))} models")
print()

header = (f"  {'Model':<6}  {'Seed':>6}  {'Vol':>5}  {'N_Veh':>6}  "
          f"{'Speed':>7}  {'Density':>8}  {'dt(ms)':>7}")
print(header)
print("  " + "-" * (len(header) - 2))

for model in ["IDM", "OVM", "W74", "W99"]:
    mr = [r for r in valid_runs if r["model"] == model]
    if not mr:
        print(f"  {model:<6}  (no valid runs)")
        continue
    for r in mr:
        nv  = r["qc"].get("n_vehicles") or 0
        sm  = r["qc"].get("speed_mean") or 0
        dn  = r["qc"].get("density")    or 0
        dt  = r["qc"].get("dt_ms")      or 0
        print(f"  {model:<6}  {r['seed']:>6}  {r['volume']:>5}  {nv:>6}  "
              f"{sm:>7.2f}  {dn:>8.2f}  {dt:>7.1f}")
    print()

# Compute speed standard deviation for the downloaded demo run, as
# an example of how to enrich the manifest stats from a real file.
if "Current Speed(m/s)" in df.columns:
    demo_speed_std = df["Current Speed(m/s)"].std()
    demo_speed_max = df["Current Speed(m/s)"].max()
    demo_speed_min = df["Current Speed(m/s)"].min()
    print(f"  Demo-run speed stats (computed from {demo_run['run_folder']}):")
    print(f"    mean = {df['Current Speed(m/s)'].mean():.2f} m/s")
    print(f"    std  = {demo_speed_std:.2f} m/s")
    print(f"    min  = {demo_speed_min:.2f} m/s")
    print(f"    max  = {demo_speed_max:.2f} m/s")
    print()


# ===========================================================================
# Wrap-up: what to do next
# ===========================================================================
print("=" * 62)
print("  Done. Suggested next steps:")
print("    - Plot fundamental diagrams (flow vs density) per model")
print("    - Compare acceleration distributions across the four CF models")
print("    - Compute surrogate safety metrics (TTC, DRAC)")
print("    - Run before/after comparisons across the eight demand levels")
print()
print("  Paper    : https://www.researchgate.net/publication/412751354")
print("  Dataset  : https://huggingface.co/datasets/eslaughter/tess-ng-car-following")
print("  GitHub   : https://github.com/code-studios/tess-ng-car-following")
print("  Platform :", platform.platform())
print("  Python   :", sys.version.split()[0])
print("=" * 62)
