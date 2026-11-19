from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from oioa import demo
from oioa.cloud.io import load_instance, save_instance
from oioa.cloud.scenarios import build_scenario
from oioa.cloud.simulator import objective, heuristic_assignment

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"


def test_round_trip_preserves_the_instance(tmp_path):
    inst = build_scenario("stable", 2)[0]
    save_instance(inst, tmp_path)
    back = load_instance(tmp_path)
    assert np.allclose(back.length, inst.length) and np.allclose(back.arrival, inst.arrival)
    assert np.allclose(back.mips, inst.mips) and np.allclose(back.price, inst.price)
    x = np.array(heuristic_assignment(inst, "FCFS"), float)
    assert objective(back, x) == pytest.approx(objective(inst, x))


def test_missing_column_is_reported(tmp_path):
    save_instance(build_scenario("stable", 0)[0], tmp_path)
    df = pd.read_csv(tmp_path / "tasks.csv").drop(columns=["arrival_s"])
    df.to_csv(tmp_path / "tasks.csv", index=False)
    with pytest.raises(ValueError, match="arrival_s"):
        load_instance(tmp_path)


def test_non_positive_values_are_rejected(tmp_path):
    save_instance(build_scenario("stable", 0)[0], tmp_path)
    df = pd.read_csv(tmp_path / "vms.csv")
    df.loc[0, "mips"] = 0
    df.to_csv(tmp_path / "vms.csv", index=False)
    with pytest.raises(ValueError):
        load_instance(tmp_path)


def test_unsorted_tasks_are_sorted_on_load(tmp_path):
    save_instance(build_scenario("stable", 0)[0], tmp_path)
    df = pd.read_csv(tmp_path / "tasks.csv").iloc[::-1]
    df.to_csv(tmp_path / "tasks.csv", index=False)
    assert np.all(np.diff(load_instance(tmp_path).arrival) >= 0)


def test_shipped_sample_data_loads():
    inst = load_instance(SAMPLE)
    assert inst.n_tasks == 100 and inst.n_vms == 8


def test_demo_runs_on_sample_data(capsys):
    assert demo.main(["--data", str(SAMPLE), "--max-fe", "800", "--algos", "OIOA,DE"]) == 0
    out = capsys.readouterr().out
    assert "MCT" in out and "OIOA" in out


def test_demo_gives_a_clear_error_for_a_bad_folder(tmp_path):
    with pytest.raises(SystemExit) as e:
        demo.main(["--data", str(tmp_path)])
    assert "tasks.csv" in str(e.value)
