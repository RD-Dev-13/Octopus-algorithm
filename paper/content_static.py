"""Paper text that does not depend on experimental numbers.

Block types (consumed by build_paper.py):
  ("h1", text) ("h2", text)            numbered section / lettered subsection headings
  ("p", text)                          paragraph; {c:key} or {c:key1,key2} become [n] / [n], [m]
  ("eq", unicode_text)                 display equation, numbered automatically
  ("table", caption, header, rows, col_weights)
  ("fig", path, caption, "col"|"span")
  ("algo", caption, [lines])           pseudocode box
Plain ASCII hyphens and commas are used on purpose; no dashes as sentence connectors.
"""

ABSTRACT_PLACEHOLDER = "@@ABSTRACT@@"

KEYWORDS = ("Octopus Imitation Optimization Algorithm, metaheuristic, swarm intelligence, bio-inspired computing, "
            "observational learning, adaptive exploration and exploitation, cloud task scheduling")

INTRO = [
    ("h1", "Introduction"),
    ("p", "Optimization problems in engineering design, machine learning and computing systems are often non-convex, "
          "high-dimensional, constrained and noisy, so exact methods become impractical as the problem grows. "
          "Population-based metaheuristics such as particle swarm optimization (PSO) {c:kennedy1995}, ant colony "
          "optimization {c:dorigo1996}, artificial bee colony (ABC) {c:karaboga2007}, differential evolution (DE) "
          "{c:storn1997} and the grey wolf optimizer (GWO) {c:mirjalili2014} are standard tools, because they need no "
          "gradient information and can leave local optima. Cloud task scheduling is a typical application: mapping "
          "tasks to heterogeneous virtual machines (VMs) while minimizing makespan, energy and cost is NP-hard, and "
          "recent studies keep proposing hybrid swarm schedulers for it {c:sanaj2026,mehta2026a,mehta2026b}. The "
          "no-free-lunch theorems state that no optimizer is best on every problem {c:wolpert1997}, so new search "
          "behaviors are worth studying only when a working mechanism justifies them and not only a metaphor "
          "{c:sorensen2015,camacho2023}."),
    ("p", "Octopuses show several behaviors that map onto search operators. The octopus has a large brain, and most of "
          "its neurons lie in the arms, so each arm controls local movement while the brain sets the overall goal "
          "{c:hochner2012}. Octopus vulgaris can learn by watching another octopus, which is observational learning "
          "{c:fiorito1992}. The mimic octopus changes its body shape, color and movement to imitate other animals and "
          "chooses the impersonation according to the threat it faces {c:norman2001}. Cephalopods use chromatophores "
          "for fast camouflage {c:hanlon2007}, escape by jet propulsion and ink {c:hanlon2018}, and have been seen "
          "carrying coconut shells as defensive tools {c:finn2009}. The common feature is that the animal switches "
          "between clearly different behaviors depending on what it observes."),
    ("p", "The Octopus Imitation Optimization Algorithm (OIOA) turns this into a search procedure. Each candidate solution "
          "is an octopus and its D decision variables are its arms. At every generation OIOA measures three properties "
          "of the search (population diversity, recent progress of the best fitness, and a per-individual stagnation "
          "counter) and uses them to give each octopus one of four behaviors. Imitation moves a solution toward a "
          "fitter peer and an elite. Mimicry copies arms from a structurally different elite. Camouflage makes small "
          "steps around the best solution. Escape relocates an octopus that has stopped improving."),
    ("p", "Octopus-inspired optimizers already exist. A giant Pacific octopus optimizer for engineering problems "
          "{c:pham2024} and a population-state-aware octopus camouflage optimizer {c:farek2026} have been published. "
          "We did not have the full texts or reference code of these two papers, so this paper makes no comparison "
          "with them and claims no difference from them beyond what is described here. The contribution claimed "
          "for OIOA is narrower: a selector that assigns one of four distinct operators to each individual from "
          "three measured indicators, together with a complete and tested open implementation and a "
          "statistically analysed comparison."),
    ("p", "The paper makes five contributions. (i) It defines OIOA, its four operators and the softmax behavior selector. "
          "(ii) It provides a Python implementation in which OIOA and six baselines (PSO, GWO, ABC, the whale "
          "optimization algorithm WOA {c:mirjalili2016}, Harris hawks optimization HHO {c:heidari2019}, and DE) share "
          "one evaluation-budget wrapper, with unit tests. (iii) It reports a CEC 2017 study on 29 functions in 10 "
          "dimensions with 30 independent runs and 100,000 evaluations per run, analysed with Friedman, Wilcoxon and "
          "rank-sum tests {c:derrac2011}. (iv) It reports an ablation of each operator and of the selector. (v) It "
          "evaluates all seven optimizers on a dynamic cloud task-scheduling problem in a small simulator that we "
          "wrote, with four workload scenarios. The study supports UN SDG 9 only in the narrow sense that lower "
          "energy for a scheduled workload is one of the objectives."),
]

SURVEY = [
    ("h1", "Literature Survey"),
    ("p", "The literature relevant to OIOA covers swarm and nature-inspired metaheuristics, learning-based and "
          "imitation-based optimization, cephalopod biology, hybrid and adaptive schedulers for cloud and related "
          "systems, and the methodology used to benchmark new optimizers."),
    ("h2", "Swarm and Nature-Inspired Metaheuristics"),
    ("p", "Kennedy and Eberhart introduced PSO, in which particles adjust their velocity using their own best position "
          "and the best position of the swarm {c:kennedy1995}. Dorigo et al. proposed the ant system, where artificial "
          "ants build solutions guided by pheromone trails {c:dorigo1996}, and Karaboga and Basturk proposed ABC, which "
          "divides the colony into employed, onlooker and scout bees {c:karaboga2007}. Storn and Price presented "
          "differential evolution, a vector-difference scheme for continuous problems {c:storn1997}. More recent "
          "optimizers include GWO with its alpha, beta and delta wolves {c:mirjalili2014}, WOA with bubble-net and "
          "spiral moves {c:mirjalili2016}, and HHO with besiege strategies of different intensity {c:heidari2019}. "
          "Yang and Deb used Levy flights in cuckoo search to obtain occasional long jumps {c:yang2009}. Across these "
          "works the balance between exploration and exploitation decides performance, and it is usually controlled "
          "by a parameter schedule fixed in advance {c:crepinsek2013}."),
    ("h2", "Learning- and Imitation-Based Optimization"),
    ("p", "Rao et al. proposed teaching-learning-based optimization, where learners improve first from a teacher and then "
          "from each other {c:rao2011}. Tizhoosh introduced opposition-based learning, in which the opposite of a "
          "candidate is evaluated as well {c:tizhoosh2005}; the idea is often reused to restart stagnated solutions. "
          "Social learning is also present inside PSO, whose social term pulls a particle toward the best neighbor "
          "{c:kennedy1995}, but it is implicit and has one fixed form. Recent work makes the choice of behavior "
          "explicit. Mandal et al. coordinated PSO, GWO and ABC with reinforcement learning for continuous "
          "optimization {c:mandal2026}, and Xie et al. used reinforcement-learning-assisted evolutionary auxiliary "
          "optimization for multi-workflow scheduling in clouds {c:xie2026}. Abdalhaq et al. selected swarm "
          "strategies according to instance characteristics, using distance uniqueness in the traveling salesman "
          "problem {c:abdalhaq2026}. These studies show the value of switching among behaviors, but they rely on "
          "learned policies or on information available before the run."),
    ("h2", "Cephalopod Biology and Octopus-Inspired Optimizers"),
    ("p", "Fiorito and Scotto showed that Octopus vulgaris learns a visual discrimination task after watching a "
          "demonstrator {c:fiorito1992}. Hochner et al. reviewed the octopus as a model for the evolution of learning "
          "and memory {c:hochner2006}, and Hochner described how its nervous system is embodied, with local control "
          "in the arms coordinated by a central brain {c:hochner2012}. Norman et al. documented dynamic mimicry in an "
          "Indo-Malayan octopus that impersonates several species depending on the situation {c:norman2001}. Hanlon "
          "explained how chromatophores and skin texture give cephalopods rapid camouflage {c:hanlon2007}, Finn et al. "
          "reported defensive tool use in the coconut-carrying octopus {c:finn2009}, and Hanlon and Messenger give a "
          "broad account of cephalopod behavior including escape by jet and ink {c:hanlon2018}. These studies come "
          "from biology. Their value here is the set of behavior categories they describe, which serve as design "
          "guidance for operators and are not evidence that the algorithm works. On the optimization side, a giant "
          "Pacific octopus optimizer {c:pham2024} and an octopus camouflage optimizer described as population-state "
          "aware {c:farek2026} have been published."),
    ("h2", "Hybrid and Adaptive Optimization for Cloud Scheduling"),
    ("p", "Sanaj et al. combined ant colony and particle swarm optimization in EcoTaskOpt for energy-efficient task "
          "scheduling {c:sanaj2026}, and Mehta and Gupta hybridized GWO with an improved PSO and Pareto knee selection "
          "for energy-efficient load balancing {c:mehta2026a}. Li et al. used a two-layer PSO for multi-objective "
          "scheduling of unmanned operations {c:li2026}, and dos Santos et al. improved PSO for weighted target "
          "approximation {c:dossantos2026}. Awad et al. enhanced the golden jackal optimizer for multi-criteria DAG "
          "task scheduling in a heterogeneous 6G air-ground-space network {c:awad2026}, while Mehta and Gupta proposed "
          "an adaptive enhanced PSO for cloud task scheduling {c:mehta2026b}. Vithanaarchchi et al. reviewed "
          "multi-agent coordination strategies for UAV swarms {c:vithana2026}. CloudSim is a widely used toolkit for "
          "modeling cloud environments and evaluating schedulers {c:calheiros2011}. The overall trend is from "
          "single algorithms to hybrid and adaptive frameworks."),
    ("h2", "Benchmarking, Statistical Validation and Novelty Scrutiny"),
    ("p", "The CEC 2017 suite of bound-constrained real-parameter problems, with unimodal, multimodal, hybrid and "
          "composition functions, is a standard benchmark for new optimizers {c:awad2016}. Derrac et al. recommended "
          "non-parametric tests such as the Wilcoxon signed-rank and Friedman tests for comparing evolutionary and "
          "swarm algorithms {c:derrac2011}, and Crepinsek et al. surveyed how exploration and exploitation should be "
          "measured {c:crepinsek2013}. Wolpert and Macready showed that performance must be reported for a defined "
          "class of problems {c:wolpert1997}. Sorensen and Camacho-Villalon et al. criticized metaheuristics that add "
          "animal metaphors without a new mechanism, and asked for clear mathematical descriptions and comparison "
          "with established methods {c:sorensen2015,camacho2023}. This work follows those recommendations by "
          "defining every OIOA operator mathematically, reporting ablation variants, and using statistical tests."),
]

GAP = [
    ("h1", "Research Gap"),
    ("p", "The literature shows a move from individual swarm algorithms to hybrid, adaptive and learning-enabled "
          "frameworks. Cloud scheduling studies have combined several algorithms, tuned algorithm parameters, used "
          "Pareto-optimal selection, or added feedback control {c:sanaj2026,mehta2026a,li2026,mehta2026b}. "
          "Coordinating PSO, GWO and ABC with reinforcement learning shows that choosing among swarm behaviors can "
          "help {c:mandal2026}, but that selector depends on learned rewards. Instance-aware swarm selection for the "
          "traveling salesman problem chooses the algorithm from instance features before optimization starts "
          "{c:abdalhaq2026}. None of these treats imitation of better individuals as an explicit, separately "
          "controllable search behavior."),
    ("p", "In dynamic cloud scheduling the environment can change while the optimizer is running. A scheduler may need "
          "exploitation when the population is diverse and progress is steady, and exploration when progress stalls or "
          "the workload changes. The gap addressed here is a simple run-time controller that reads population "
          "diversity, fitness progress and stagnation, and uses them to bias which of four explicitly defined "
          "behaviors each individual performs, with an evaluation that includes a statistical comparison, an "
          "ablation, and a changing-workload scheduling case study."),
]

PROBLEM = [
    ("h1", "Problem Formulation"),
    ("p", "The optimizer minimizes an objective f(x) over a bounded search space Ω = Π_{j=1..D} [l_j, u_j] ⊂ R^D, "
          "where x = (x_1, ..., x_D) is a candidate solution. The function may be non-convex and multimodal, and each "
          "evaluation counts against a fixed budget of T_max function evaluations. A population of N candidates "
          "is kept, and an algorithm stops when the budget is used. In the dynamic case the objective changes with "
          "time, f_t(x), because the workload or the resources change."),
    ("h2", "Cloud task-scheduling instance"),
    ("p", "A scheduling solution assigns n independent tasks to m VMs, so D = n. Task i has length L_i (million "
          "instructions) and arrival time a_i. VM j has speed s_j (MIPS) and runs its tasks first-in first-out without "
          "pre-emption. If task i is placed on VM j(i), it starts at max(a_i, r_j) and runs for L_i / s_j seconds, "
          "where r_j is the time VM j becomes free. The makespan M is the finish time of the last task. With busy "
          "time B_j, idle power P_j^idle and busy power P_j^max, the energy is"),
    ("eq", "E = Σ_j [ P_j^idle (M − B_j) + P_j^max B_j ]"),
    ("p", "and the cost is C = Σ_j c_j B_j, where c_j is the price per busy second of VM j. The scalar objective is"),
    ("eq", "f(x) = w_1 M(x)/M_ref + w_2 E(x)/E_ref + w_3 C(x)/C_ref"),
    ("p", "with w_1 + w_2 + w_3 = 1, where M_ref, E_ref and C_ref are the values obtained by the minimum completion time (MCT) heuristic "
          "{c:maheswaran1999} on the same instance, so f = 1 means \"as good as MCT\" and f < 1 is an improvement. The "
          "weights are w = (0.5, 0.3, 0.2). The two-state linear power model follows the usual idle-versus-busy "
          "simplification used in energy-aware scheduling {c:beloglazov2012}. A continuous vector x ∈ [−0.5, m − 0.5]^n "
          "is decoded to VM indices by rounding. All task, VM, power and price values are modeling assumptions "
          "chosen for this study and are not measurements of a real data center."),
    ("p", "The optimizer must (a) keep enough diversity to avoid premature convergence, (b) intensify the search around "
          "good regions quickly, (c) recover when the population stagnates or the objective changes, and (d) do so at "
          "small extra cost per generation."),
]

METHOD = [
    ("h1", "Proposed Method"),
    ("h2", "Overview and architecture"),
    ("p", "OIOA keeps a population of N octopuses x_i ∈ Ω with fitness f_i. Fig. 1 shows the generation loop. In "
          "each generation the selector observes the search state, gives every octopus one behavior, the four "
          "operators produce trial vectors, the trials are clipped to the bounds and evaluated, and greedy selection "
          "keeps the better of each octopus and its trial. Fig. 2 shows how the pieces of the study fit together: all "
          "optimizers evaluate candidates only through one budgeted problem wrapper, so every algorithm gets exactly "
          "the same number of function evaluations."),
    ("fig", "figures/fig_oioa_flowchart.png", "Generation loop of OIOA.", "col"),
    ("fig", "figures/fig_architecture.png", "Architecture of the experimental system.", "col"),
    ("h2", "State indicators"),
    ("p", "Three indicators are computed at the start of every generation. The relative diversity compares the "
          "mean distance to the population centroid x̄, normalized by the search-space diagonal, with its value δ_0 "
          "at generation 0:"),
    ("eq", "δ_t = min{ 1, (1/(N·‖u − l‖)) Σ_i ‖x_i − x̄‖ / δ_0 }"),
    ("p", "The progress indicator is the improvement of the best fitness over the last k = min(W, t) generations, "
          "divided by the fitness spread of the population k generations ago:"),
    ("eq", "ρ_t = clip( (f_best(t−k) − f_best(t)) / s_t , 0, 1 )"),
    ("p", "where s_t = f_worst(t−k) − f_best(t−k). The stagnation counter κ_i of octopus i counts consecutive generations without improvement. It is reset "
          "to zero after an improvement and after an escape."),
    ("h2", "Behavior selector"),
    ("p", "Let u_prog = min(1, ρ_t / ρ_ref), u_low = 1 − δ_t and u_stag = min(1, κ_i / κ_max). Each octopus gets a score "
          "for each behavior:"),
    ("eq", "z_imitate = 1 + 1.5 u_prog + (1 − u_low)"),
    ("eq", "z_mimic = 0.5 + 2 u_low"),
    ("eq", "z_camouflage = 0.5 + 2 u_prog"),
    ("eq", "z_escape = 0.5 + 1.5 u_low + u_stag"),
    ("p", "The probabilities are P(b | s_i) = exp(z_b / τ) / Σ_b' exp(z_b' / τ), with temperature τ = 1, and the behavior "
          "is sampled from them. The escape score is used only when κ_i ≥ κ_min; before that z_escape = −∞ and escape has probability zero. Escape is forced when κ_i ≥ κ_max. The score "
          "coefficients are design choices of this study. They encode three rules: high diversity and steady progress "
          "favor imitation, progress favors camouflage, and low diversity favors mimicry and (for stagnated octopuses) "
          "escape. They were fixed once from a small pilot on four functions that are not part of CEC 2017 (sphere, "
          "Rosenbrock, Rastrigin and Ackley) and were not tuned on the benchmark."),
    ("h2", "Behavior operators"),
    ("p", "Imitation moves octopus i toward a peer x_p chosen uniformly among the octopuses with strictly better "
          "fitness rank, and toward an elite x_e chosen uniformly from the best n_e = ⌈0.2 N⌉ octopuses:"),
    ("eq", "x_i' = x_i + r_1 ∘ (x_p − x_i) + r_2 ∘ (x_e − x_i)"),
    ("p", "where r_1, r_2 ~ U(0, 1)^D and ∘ is the element-wise product. Mimicry picks the elite x_m that is farthest "
          "from x_i, which is the structurally most different elite, and each arm copies it with probability p_m:"),
    ("eq", "x_ij' = x_mj  if rand < p_m,  else x_ij"),
    ("p", "At least one arm is always copied. Camouflage samples around the best solution with a step proportional "
          "to the spread of two random octopuses, plus a floor that keeps refinement alive late in the run:"),
    ("eq", "x_i' = x_best + N(0, I) ∘ ( σ_t |x_r1 − x_r2| + φ_t )"),
    ("eq", "σ_t = σ_min + (σ_0 − σ_min)(1 − T/T_max)"),
    ("eq", "φ_t = (u − l) · 10^{−2 − 8q}"),
    ("p", "where T is the number of evaluations used so far and q = T/T_max. Escape relocates an octopus with probability p_opp by "
          "opposition {c:tizhoosh2005} and otherwise by a Levy jump generated with Mantegna's algorithm "
          "{c:mantegna1994}, scaled by the distance to the best solution (at least 1% of the range):"),
    ("eq", "x_i' = l + u − x_i    (probability p_opp)"),
    ("eq", "x_i' = x_i + Lévy(β) ∘ max(|x_i − x_best|, 0.01(u − l))"),
    ("p", "Every trial is clipped to Ω. Selection is greedy for all four behaviors, so an escape move is accepted "
          "only if it improves the octopus; the best solution is therefore never lost."),
    ("algo", "Algorithm 1. OIOA.", [
        "Input: objective f, bounds [l, u], budget T_max, parameters of Table I",
        "1  Initialise N octopuses in Ω; evaluate; κ_i ← 0; δ_0 ← diversity",
        "2  while T < T_max do",
        "3    rank octopuses by fitness; x_best ← best",
        "4    compute δ_t, ρ_t",
        "5    for each octopus i: compute scores z_i,b and probabilities P(b | s_i)",
        "6      sample behavior b_i; if κ_i ≥ κ_max set b_i ← escape",
        "7    build trial x_i' with the operator of b_i; clip to Ω",
        "8    evaluate all trials (T ← T + N)",
        "9    for each i: if f(x_i') < f_i then accept, κ_i ← 0 else κ_i ← κ_i + 1",
        "10     (κ_i ← 0 after an escape move)",
        "11 return best solution found",
    ]),
    ("h2", "Parameters and complexity"),
    ("table", "TABLE I. OIOA PARAMETERS (ALL DESIGN CHOICES OF THIS STUDY)", ["Parameter", "Value"], [
        ["Population size N", "50"],
        ["Progress window W / reference ρ_ref", "5 generations / 0.02"],
        ["Escape thresholds κ_min / κ_max", "5 / 12"],
        ["Elite fraction (n_e = 10)", "0.2"],
        ["Mimic copy probability p_m", "0.5"],
        ["Camouflage σ_0 / σ_min", "0.5 / 0.005"],
        ["Camouflage floor φ (fraction of range)", "10^{-2} to 10^{-10}"],
        ["Opposition probability p_opp / Levy β", "0.3 / 1.5"],
        ["Softmax temperature τ", "1"],
    ], [3.0, 1.6]),
    ("p", "One generation costs N function evaluations plus O(N log N) for ranking, O(N·D) for imitation, camouflage "
          "and escape, and O(N·n_e·D) for the farthest-elite search in mimicry. For expensive objectives the "
          "function evaluations dominate this overhead."),
]

EXPERIMENT = [
    ("h1", "Experimental Methodology"),
    ("h2", "Benchmark and protocol"),
    ("p", "Experiments use the CEC 2017 bound-constrained suite {c:awad2016} through the opfunu package, version "
          "1.0.4 {c:vanthieu2024}. That package numbers the suite F1 to F29 and omits the official F2, so its Fk is "
          "the official F(k+1) for k ≥ 2, and the optimum of its Fk is 100k. Errors are measured against opfunu's own "
          "optimum, so absolute values are not comparable with published CEC 2017 tables. In this numbering F1-F2 are "
          "unimodal, F3-F9 simple multimodal, F10-F19 hybrid and F20-F29 composition functions. All runs use "
          "D = 10, a budget of 100,000 function evaluations (10,000 D), 30 independent runs, and errors below 1e-8 are "
          "set to zero as in the CEC convention."),
    ("h2", "Compared algorithms"),
    ("p", "OIOA is compared with PSO, GWO, ABC, WOA, HHO and DE. All are our own NumPy implementations of the original "
          "update rules, written for this study and not taken from the authors' reference code, and they use the "
          "population size 50 (ABC: 25 food sources) and the textbook parameters of Table II. Every algorithm "
          "evaluates candidates only through the shared budgeted problem wrapper. Run r of function f uses the same "
          "initial population for all algorithms (seed [f, r, 0]) and a separate random stream per algorithm."),
    ("table", "TABLE II. BASELINE SETTINGS", ["Algorithm", "Settings"], [
        ["PSO", "w from 0.9 to 0.4, c1 = c2 = 2, vmax = 20% of range"],
        ["GWO", "a from 2 to 0, three leaders"],
        ["ABC", "25 food sources, limit = 25 D, one scout per cycle"],
        ["WOA", "a from 2 to 0, spiral b = 1"],
        ["HHO", "four besiege strategies with Levy dives"],
        ["DE", "DE/rand/1/bin, F = 0.5, CR = 0.9"],
    ], [1.0, 3.6]),
    ("h2", "Statistical analysis"),
    ("p", "For each function the mean final error over runs is computed. Algorithms are ranked per function (ties get "
          "average ranks) and mean ranks over the 29 functions are reported. The Friedman test {c:friedman1937} checks "
          "whether the algorithms differ overall. OIOA is then compared with each baseline across functions by the "
          "paired Wilcoxon signed-rank test {c:wilcoxon1945} with Holm correction {c:holm1979}, and per function by "
          "the Mann-Whitney rank-sum test {c:mannwhitney1947} at the 0.05 level over the 30 runs, reported as win, "
          "tie and loss counts for OIOA. The significance level is 0.05 throughout."),
    ("h2", "Ablation study"),
    ("p", "Five variants of OIOA are run on all 29 functions with 10 runs each (seeds 0 to 9, the same initial "
          "populations as the main study): without imitation, without mimicry, without camouflage, without escape, "
          "and with a uniform selector that picks uniformly among the available behaviors instead of using the "
          "softmax scores. The ten main-study OIOA runs with the same seeds serve as the reference."),
    ("h2", "Dynamic cloud scheduling study"),
    ("p", "The scheduling study uses our own Python simulator described in Section IV, not CloudSim. There are 8 VMs "
          "with speeds of 1000, 1000, 1500, 1500, 2000, 2000, 2500 and 2500 MIPS, busy power 60 + 0.06 s_j watts "
          "with idle power at 60% of busy power, and a price proportional to speed. Task lengths follow a "
          "clipped log-normal distribution (median 6000 MI) and arrivals a Poisson process. Four scenarios are used. "
          "In the stable scenario 100 tasks are scheduled once. In the burst scenario 60 tasks are scheduled for half "
          "of the budget, then 40 more tasks arrive. In the degradation scenario the two fastest VMs lose half of "
          "their speed at the change point. The combined scenario has both changes. Each run has 30,000 "
          "evaluations, split equally over the two phases when there is a change, and the optimizer continues "
          "from its current population after the change, with new tasks given random VM indices. FCFS, "
          "round robin (RR) and MCT are reported as reference heuristics. There are 30 runs per scenario "
          "and algorithm, and run r uses the same workload for all algorithms."),
    ("h2", "Implementation and reproducibility"),
    ("p", "All code, tests and scripts are in the accompanying repository. Every run is seeded and written to its "
          "own result file, so the study can be resumed and reproduced. A cross-check of the same jobs on two "
          "machines gave results equal to within a relative difference of 2.2e-14, which comes from "
          "floating-point differences between processors."),
]
