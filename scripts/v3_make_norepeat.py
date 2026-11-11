# -*- coding: utf-8 -*-
"""Create the no-repeat dataset by removing W06-015 and E11-018."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v3"
REMOVE = ["W06-015", "E11-018"]

df = pd.read_csv(DATA / "dataset_v3.csv", encoding="utf-8-sig")
removed = df[df["sent_id"].isin(REMOVE)]
out = df[~df["sent_id"].isin(REMOVE)].copy()
out.to_csv(DATA / "dataset_v3_norepeat.csv", index=False, encoding="utf-8-sig")
print("removed", len(removed), "sentences; remaining", len(out))
print("removed positions", removed[["sent_id", "split"]].to_dict("records"))
print("new split", out["split"].value_counts().to_dict())
