"""Read and write the cloud scheduling instance as two small CSV files.

tasks.csv : task_id, length_mi, arrival_s
vms.csv   : vm_id, mips, p_idle_w, p_max_w, price_per_s
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .simulator import CloudInstance

TASK_COLS = ["task_id", "length_mi", "arrival_s"]
VM_COLS = ["vm_id", "mips", "p_idle_w", "p_max_w", "price_per_s"]


def save_instance(inst: CloudInstance, folder) -> None:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"task_id": range(inst.n_tasks), "length_mi": inst.length, "arrival_s": inst.arrival}) \
        .to_csv(folder / "tasks.csv", index=False)
    pd.DataFrame({"vm_id": range(inst.n_vms), "mips": inst.mips, "p_idle_w": inst.p_idle, "p_max_w": inst.p_max,
                  "price_per_s": inst.price}).to_csv(folder / "vms.csv", index=False)


def load_instance(folder, weights=(0.5, 0.3, 0.2)) -> CloudInstance:
    folder = Path(folder)
    tasks, vms = pd.read_csv(folder / "tasks.csv"), pd.read_csv(folder / "vms.csv")
    for df, cols, name in ((tasks, TASK_COLS, "tasks.csv"), (vms, VM_COLS, "vms.csv")):
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{name} is missing columns {missing}; expected {cols}")
    if tasks.empty or vms.empty:
        raise ValueError("tasks.csv and vms.csv must each contain at least one row")
    if (tasks["length_mi"] <= 0).any() or (vms["mips"] <= 0).any():
        raise ValueError("task lengths and VM speeds must be positive")
    tasks = tasks.sort_values("arrival_s", kind="stable")
    return CloudInstance(length=tasks["length_mi"].to_numpy(float), arrival=tasks["arrival_s"].to_numpy(float),
                         mips=vms["mips"].to_numpy(float), p_idle=vms["p_idle_w"].to_numpy(float),
                         p_max=vms["p_max_w"].to_numpy(float), price=vms["price_per_s"].to_numpy(float),
                         weights=tuple(weights))
