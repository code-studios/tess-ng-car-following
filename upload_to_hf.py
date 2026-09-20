#!/usr/bin/env python3
"""
upload_to_hf.py
Uploads all run folders from this directory to Hugging Face.
Run from the Net001-Copy.tess/ root.
"""

import os, time
from huggingface_hub import HfApi

BASE   = os.path.dirname(os.path.abspath(__file__))
REPO   = "eslaughter/tess-ng-car-following"
CHUNK  = 4          # upload this many folders per commit

def run_folders():
    api = HfApi()
    folders = sorted([
        d for d in os.listdir(BASE)
        if os.path.isdir(os.path.join(BASE, d))
        and not d.startswith("_")
        and d not in ("Workspace", ".git")
    ])
    total = len(folders)
    print(f"Found {total} run folders\n")

    for i in range(0, total, CHUNK):
        chunk = folders[i : i + CHUNK]
        labels = ", ".join(chunk)
        print(f"[{i+1}–{min(i+CHUNK, total)}/{total}] Uploading {labels} ...")
        t0 = time.time()
        try:
            for folder in chunk:
                folder_path = os.path.join(BASE, folder)
                api.upload_folder(
                    folder_path=folder_path,
                    repo_id=REPO,
                    repo_type="dataset",
                    commit_message=f"Upload {labels}",
                )
        except Exception as e:
            print(f"  ERROR: {e}")
            # Retry one by one
            for folder in chunk:
                print(f"  Retrying {folder} ...")
                try:
                    api.upload_folder(
                        folder_path=os.path.join(BASE, folder),
                        repo_id=REPO,
                        repo_type="dataset",
                        commit_message=f"Upload {folder}",
                    )
                    print(f"    OK: {folder}")
                except Exception as e2:
                    print(f"    FAILED: {folder} — {e2}")
        print(f"  Done in {time.time()-t0:.0f}s\n")

    print("All uploads complete.")

if __name__ == "__main__":
    run_folders()
