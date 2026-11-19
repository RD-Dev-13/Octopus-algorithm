import numpy as np
import pytest

from oioa.cloud.scenarios import SCENARIOS, adapt_population, build_scenario
from oioa.cloud.simulator import (CloudInstance, decode, heuristic_assignment, make_problem, metrics, objective,
                                  simulate)
from oioa.oioa import oioa


def toy():
    """2 VMs (1000 and 2000 MIPS); 3 tasks arriving at t=0 with 2000, 2000 and 4000 MI."""
    return CloudInstance(length=np.array([2000.0, 2000.0, 4000.0]), arrival=np.zeros(3),
                         mips=np.array([1000.0, 2000.0]), p_idle=np.array([10.0, 20.0]),
                         p_max=np.array([50.0, 100.0]), price=np.array([1.0, 3.0]))


def test_toy_makespan_energy_cost_by_hand():
    # VM0 runs task0 (2 s). VM1 runs task1 (1 s) then task2 (2 s): busy 3 s. Makespan 3 s.
    M, E, C = simulate(toy(), [0, 1, 1])
    assert M == pytest.approx(3.0)
    assert E == pytest.approx(10 * 1 + 50 * 2 + 20 * 0 + 100 * 3)
    assert C == pytest.approx(1 * 2 + 3 * 3)


def test_task_waits_for_its_arrival_time():
    inst = CloudInstance(length=np.array([1000.0, 1000.0]), arrival=np.array([0.0, 5.0]),
                         mips=np.array([1000.0]), p_idle=np.array([1.0]), p_max=np.array([2.0]),
                         price=np.array([1.0]))
    assert simulate(inst, [0, 0])[0] == pytest.approx(6.0)


def test_invalid_assignments_raise():
    with pytest.raises(ValueError):
        simulate(toy(), [0, 1])
    with pytest.raises(ValueError):
        simulate(toy(), [0, 1, 2])


def test_decode_clips_and_rounds():
    assert list(decode(np.array([-0.4, 0.6, 7.9]), 3)) == [0, 1, 2]


def test_mct_scores_exactly_one():
    inst = toy()
    assert objective(inst, np.array(heuristic_assignment(inst, "MCT"), float)) == pytest.approx(1.0)


def test_heuristics_are_valid_and_unknown_raises():
    inst = build_scenario("stable", 0)[0]
    for k in ("FCFS", "RR", "MCT"):
        a = heuristic_assignment(inst, k)
        assert len(a) == inst.n_tasks and a.min() >= 0 and a.max() < inst.n_vms
    with pytest.raises(ValueError):
        heuristic_assignment(inst, "x")


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        CloudInstance(length=np.ones(1), arrival=np.zeros(1), mips=np.ones(1), p_idle=np.ones(1),
                      p_max=np.ones(1), price=np.ones(1), weights=(0.5, 0.5, 0.5))


@pytest.mark.parametrize("name", SCENARIOS)
def test_scenarios_are_reproducible_and_well_formed(name):
    a, b = build_scenario(name, 3), build_scenario(name, 3)
    assert len(a) == (1 if name == "stable" else 2)
    for x, y in zip(a, b):
        assert np.array_equal(x.length, y.length) and np.array_equal(x.arrival, y.arrival)
        assert np.all(np.diff(x.arrival) >= 0)


def test_burst_adds_tasks_and_degradation_slows_vms():
    burst = build_scenario("burst", 1)
    assert burst[0].n_tasks == 60 and burst[1].n_tasks == 100
    deg = build_scenario("degradation", 1)
    assert deg[1].mips[-1] == deg[0].mips[-1] / 2 and deg[1].n_tasks == deg[0].n_tasks


def test_adapt_population_shapes():
    rng = np.random.default_rng(0)
    pop = np.zeros((5, 4))
    assert adapt_population(pop, 7, rng, -0.5, 7.5).shape == (5, 7)
    assert adapt_population(pop, 2, rng, -0.5, 7.5).shape == (5, 2)
    assert np.array_equal(adapt_population(pop, 4, rng, -0.5, 7.5), pop)


def test_oioa_beats_round_robin_on_stable_scenario():
    inst = build_scenario("stable", 0)[0]
    p = make_problem(inst, 4000)
    oioa(p, np.random.default_rng(0))
    rr = objective(inst, np.array(heuristic_assignment(inst, "RR"), float))
    assert p.best_f < rr
    assert metrics(inst, p.best_x)["objective"] == pytest.approx(p.best_f)
