# Getting Started with the Dataset

This folder contains a single, self-contained Python script that walks you
through every step of downloading and reading the TESS NG Car-Following Model
Benchmark Dataset from Hugging Face.

## What you need

* Python 3.9 or newer
* An internet connection
* A free Hugging Face account (only required if you want to upload data; reading the public dataset is anonymous)

## Install (one-time)

```bash
pip install huggingface_hub pandas
```

## Authenticate (one-time)

Choose either of these:

**Option A -- interactive CLI login**

```bash
huggingface-cli login
# paste your HF token when prompted
```

**Option B -- environment variable**

```bash
export HF_TOKEN="hf_xxxxxxxxxxxx"
```

## Run the walkthrough

```bash
python tess_ng_cfm_demo.py
```

The script prints seven clearly-labelled steps:

| Step | What it does |
|------|--------------|
| 1    | Installs `huggingface_hub` and `pandas` if missing |
| 2    | Authenticates with Hugging Face (CLI or env var) |
| 3    | Lists every file in the dataset repository |
| 4    | Downloads `dataset.json` (the manifest) and prints study/simulation/dataset metadata |
| 5    | Downloads one example trajectory CSV (~5 MB) |
| 6    | Loads the CSV with pandas and shows the schema, summary statistics, and data-quality checks |
| 7    | Iterates every valid run in the manifest and prints a per-model summary table |

The demo run is `IDM_10_100` -- the smallest valid run, so it downloads in
under a second.

## Programmatic access (after running the walkthrough)

Once you've run the demo you can drop into a Python REPL and grab any
other run the same way:

```python
from huggingface_hub import hf_hub_download
import pandas as pd

# Replace MODEL, SEED, VOLUME with any of the 64 run folders
local = hf_hub_download(
    repo_id="eslaughter/tess-ng-car-following",
    filename="OVM_300_1500/Trajectory_vehicle_trajectory.csv",
    repo_type="dataset",
)
df = pd.read_csv(local, encoding="latin-1", low_memory=False)
print(df.shape, df["Current Speed(m/s)"].mean())
```

The two CSV files in every run folder are:

* `Trajectory_vehicle_trajectory.csv` -- per-vehicle per-timestep records
  (Time, Vehicle ID, X/Y/Z, Speed, Acceleration, Lane, etc.)
* `Trajectory_vehicle_basic_information.csv` -- per-vehicle static attributes
  (vehicle type, desired speed, etc.)

Both use **Latin-1 encoding** because TESS NG exports contain superscript
characters and other Latin-1 glyphs that break UTF-8 readers.

## Public URLs

* Dataset (read-only): https://huggingface.co/datasets/eslaughter/tess-ng-car-following
* Companion repo: https://github.com/code-studios/tess-ng-car-following
* Paper: see `paper_url` in `dataset.json`

## License

The dataset is released under CC BY 4.0. If you use it in a publication,
please cite the accompanying paper (URL above).
