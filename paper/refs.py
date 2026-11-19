"""Bibliography. Every entry was checked against Crossref (DOI or citation search) or, for Holm (1979),
OpenAlex; see tools/verify_references.py and docs/reference_check.json.

Each value is (plain text, list of (start, end) spans to italicise: journal / proceedings / book titles).
Numbers are assigned in order of first citation by build_paper.py.
"""

def _it(text, *titles):
    spans = []
    for t in titles:
        i = text.index(t)
        spans.append((i, i + len(t)))
    return (text, spans)


REFS = {
    "sanaj2026": _it("M. S. Sanaj, M.-F. Horng, S. S. Shankar, C.-C. Lo, R. Sunder, U. K. Lilhore, S. Simaiya, L. G. Tekeste, H. G. Mohamed, and E. S. Ghith, \"Energy-efficient task scheduling in cloud computing with EcoTaskOpt: A hybrid ant colony and particle swarm optimization approach,\" Int. J. Comput. Intell. Syst., vol. 19, art. no. 64, 2026, doi: 10.1007/s44196-025-01095-w.", "Int. J. Comput. Intell. Syst."),
    "mehta2026a": _it("V. Mehta and A. Gupta, \"A hybrid grey wolf and improved particle swarm optimization technique with Pareto knee selection for energy efficient load balancing in cloud computing,\" Discover Appl. Sci., vol. 8, art. no. 337, 2026, doi: 10.1007/s42452-026-08395-6.", "Discover Appl. Sci."),
    "mandal2026": _it("S. K. Mandal, R. Sau, K. A. Halim, and M. K. Maiti, \"A coordination among PSO, GWO, and ABC using reinforcement learning for continuous optimization,\" Knowl. Inf. Syst., vol. 68, art. no. 249, 2026, doi: 10.1007/s10115-026-02866-3.", "Knowl. Inf. Syst."),
    "li2026": _it("H. Li, T. Zhang, G. Liu, J. Yin, Z. Shi, L. Shen, and Y. Fan, \"Research on multi-objective intelligent unmanned operation scheduling method based on two-layer PSO,\" Cybern. Intell., 2026, doi: 10.26599/CAI.2025.9390011.", "Cybern. Intell."),
    "dossantos2026": _it("G. R. dos Santos, G. C. Machado, A. C. B. Ramos, D. D. Bueno, D. B. Riffel, and A. C. R. Ramos, \"Enhanced weighted target approximation using an improved particle swarm optimization approach,\" IEEE Access, vol. 14, pp. 75642-75656, 2026, doi: 10.1109/ACCESS.2026.3692710.", "IEEE Access"),
    "awad2026": _it("A. I. Awad, M. M. Khashaba, M. M. Fouda, Z. Md Fadlullah, and K. M. Hosny, \"An enhanced golden jackal optimizer for multi-criteria DAG task scheduling in a heterogeneous 6G air-ground-space integrated network,\" IEEE Open J. Commun. Soc., vol. 7, pp. 6672-6702, 2026, doi: 10.1109/OJCOMS.2026.3689759.", "IEEE Open J. Commun. Soc."),
    "abdalhaq2026": _it("B. Abdalhaq, A. Awad, and A. Hawash, \"Toward instance-aware swarm intelligence for TSP via distance uniqueness,\" IEEE Access, vol. 14, pp. 25264-25285, 2026, doi: 10.1109/ACCESS.2026.3664310.", "IEEE Access"),
    "vithana2026": _it("P. Vithanaarchchi, J. Prabhanuka, N. Senanayake, and R. Ratnayake, \"A review of multi-agent coordination strategies for multi-role UAV swarms in search and rescue,\" IEEE Access, vol. 14, pp. 144643-144679, 2026, doi: 10.1109/ACCESS.2026.3734747.", "IEEE Access"),
    "mehta2026b": _it("V. Mehta and A. Gupta, \"Optimized task scheduling in cloud computing environments using adaptive enhanced particle swarm optimization,\" Swarm Evol. Comput., vol. 108, art. no. 102510, 2026, doi: 10.1016/j.swevo.2026.102510.", "Swarm Evol. Comput."),
    "xie2026": _it("H. Xie, D. Ding, K. Kang, L. Zhao, Y. Li, and Y. Jin, \"Reinforcement learning-assisted evolutionary auxiliary optimization for multi-workflow scheduling in clouds,\" Swarm Evol. Comput., vol. 106, art. no. 102422, 2026, doi: 10.1016/j.swevo.2026.102422.", "Swarm Evol. Comput."),
    "kennedy1995": _it("J. Kennedy and R. Eberhart, \"Particle swarm optimization,\" in Proc. IEEE Int. Conf. Neural Networks, Perth, Australia, 1995, vol. 4, pp. 1942-1948, doi: 10.1109/ICNN.1995.488968.", "Proc. IEEE Int. Conf. Neural Networks"),
    "mirjalili2014": _it("S. Mirjalili, S. M. Mirjalili, and A. Lewis, \"Grey wolf optimizer,\" Adv. Eng. Softw., vol. 69, pp. 46-61, 2014.", "Adv. Eng. Softw."),
    "karaboga2007": _it("D. Karaboga and B. Basturk, \"A powerful and efficient algorithm for numerical function optimization: Artificial bee colony (ABC) algorithm,\" J. Global Optim., vol. 39, no. 3, pp. 459-471, 2007.", "J. Global Optim."),
    "dorigo1996": _it("M. Dorigo, V. Maniezzo, and A. Colorni, \"Ant system: Optimization by a colony of cooperating agents,\" IEEE Trans. Syst., Man, Cybern. B, vol. 26, no. 1, pp. 29-41, 1996.", "IEEE Trans. Syst., Man, Cybern. B"),
    "storn1997": _it("R. Storn and K. Price, \"Differential evolution: A simple and efficient heuristic for global optimization over continuous spaces,\" J. Global Optim., vol. 11, no. 4, pp. 341-359, 1997.", "J. Global Optim."),
    "rao2011": _it("R. V. Rao, V. J. Savsani, and D. P. Vakharia, \"Teaching-learning-based optimization: A novel method for constrained mechanical design optimization problems,\" Comput.-Aided Des., vol. 43, no. 3, pp. 303-315, 2011.", "Comput.-Aided Des."),
    "mirjalili2016": _it("S. Mirjalili and A. Lewis, \"The whale optimization algorithm,\" Adv. Eng. Softw., vol. 95, pp. 51-67, 2016.", "Adv. Eng. Softw."),
    "heidari2019": _it("A. A. Heidari, S. Mirjalili, H. Faris, I. Aljarah, M. Mafarja, and H. Chen, \"Harris hawks optimization: Algorithm and applications,\" Future Gener. Comput. Syst., vol. 97, pp. 849-872, 2019.", "Future Gener. Comput. Syst."),
    "tizhoosh2005": _it("H. R. Tizhoosh, \"Opposition-based learning: A new scheme for machine intelligence,\" in Proc. Int. Conf. Comput. Intell. Modelling, Control Autom. (CIMCA), 2005, vol. 1, pp. 695-701.", "Proc. Int. Conf. Comput. Intell. Modelling, Control Autom. (CIMCA)"),
    "wolpert1997": _it("D. H. Wolpert and W. G. Macready, \"No free lunch theorems for optimization,\" IEEE Trans. Evol. Comput., vol. 1, no. 1, pp. 67-82, 1997.", "IEEE Trans. Evol. Comput."),
    "sorensen2015": _it("K. Sörensen, \"Metaheuristics: the metaphor exposed,\" Int. Trans. Oper. Res., vol. 22, no. 1, pp. 3-18, 2015.", "Int. Trans. Oper. Res."),
    "camacho2023": _it("C. L. Camacho-Villalón, T. Stützle, and M. Dorigo, \"Exposing the grey wolf, moth-flame, whale, firefly, bat, and antlion algorithms: Six misleading optimization techniques inspired by bestial metaphors,\" Int. Trans. Oper. Res., vol. 30, no. 6, pp. 2945-2971, 2023.", "Int. Trans. Oper. Res."),
    "crepinsek2013": _it("M. Črepinšek, S.-H. Liu, and M. Mernik, \"Exploration and exploitation in evolutionary algorithms: A survey,\" ACM Comput. Surv., vol. 45, no. 3, pp. 1-33, 2013, doi: 10.1145/2480741.2480752.", "ACM Comput. Surv."),
    "derrac2011": _it("J. Derrac, S. García, D. Molina, and F. Herrera, \"A practical tutorial on the use of nonparametric statistical tests as a methodology for comparing evolutionary and swarm intelligence algorithms,\" Swarm Evol. Comput., vol. 1, no. 1, pp. 3-18, 2011.", "Swarm Evol. Comput."),
    "awad2016": ("N. H. Awad, M. Z. Ali, J. J. Liang, B. Y. Qu, and P. N. Suganthan, \"Problem definitions and evaluation criteria for the CEC 2017 special session and competition on single objective bound constrained real-parameter numerical optimization,\" Nanyang Technol. Univ., Singapore, Tech. Rep., 2016.", []),
    "calheiros2011": _it("R. N. Calheiros, R. Ranjan, A. Beloglazov, C. A. F. De Rose, and R. Buyya, \"CloudSim: A toolkit for modeling and simulation of cloud computing environments and evaluation of resource provisioning algorithms,\" Softw. Pract. Exper., vol. 41, no. 1, pp. 23-50, 2011.", "Softw. Pract. Exper."),
    "fiorito1992": _it("G. Fiorito and P. Scotto, \"Observational learning in Octopus vulgaris,\" Science, vol. 256, no. 5056, pp. 545-547, 1992.", "Science"),
    "norman2001": _it("M. D. Norman, J. Finn, and T. Tregenza, \"Dynamic mimicry in an Indo-Malayan octopus,\" Proc. R. Soc. Lond. B, vol. 268, no. 1478, pp. 1755-1758, 2001.", "Proc. R. Soc. Lond. B"),
    "hanlon2018": _it("R. T. Hanlon and J. B. Messenger, Cephalopod Behaviour, 2nd ed. Cambridge, U.K.: Cambridge Univ. Press, 2018, doi: 10.1017/9780511843600.", "Cephalopod Behaviour"),
    "hochner2012": _it("B. Hochner, \"An embodied view of octopus neurobiology,\" Curr. Biol., vol. 22, no. 20, pp. R887-R892, 2012.", "Curr. Biol."),
    "finn2009": _it("J. K. Finn, T. Tregenza, and M. D. Norman, \"Defensive tool use in a coconut-carrying octopus,\" Curr. Biol., vol. 19, no. 23, pp. R1069-R1070, 2009.", "Curr. Biol."),
    "yang2009": _it("X.-S. Yang and S. Deb, \"Cuckoo search via Lévy flights,\" in Proc. World Congr. Nature Biologically Inspired Comput. (NaBIC), Coimbatore, India, 2009, pp. 210-214.", "Proc. World Congr. Nature Biologically Inspired Comput. (NaBIC)"),
    "hanlon2007": _it("R. T. Hanlon, \"Cephalopod dynamic camouflage,\" Curr. Biol., vol. 17, no. 11, pp. R400-R404, 2007.", "Curr. Biol."),
    "hochner2006": _it("B. Hochner, T. Shomrat, and G. Fiorito, \"The octopus: A model for a comparative analysis of the evolution of learning and memory mechanisms,\" Biol. Bull., vol. 210, no. 3, pp. 308-317, 2006.", "Biol. Bull."),
    # added during this revision (all verified)
    "farek2026": _it("L. Farek and A. Benaidja, \"Octopus camouflage optimization: A population-state-aware metaheuristic,\" Knowl.-Based Syst., vol. 350, art. no. 116583, 2026, doi: 10.1016/j.knosys.2026.116583.", "Knowl.-Based Syst."),
    "pham2024": _it("V. H. S. Pham and L. N. Q. Khoi, \"A novel giant Pacific octopus optimizer for real-world engineering problem,\" Evol. Intell., vol. 17, no. 5-6, pp. 3571-3592, 2024, doi: 10.1007/s12065-024-00945-4.", "Evol. Intell."),
    "mantegna1994": _it("R. N. Mantegna, \"Fast, accurate algorithm for numerical simulation of Lévy stable stochastic processes,\" Phys. Rev. E, vol. 49, no. 5, pp. 4677-4683, 1994, doi: 10.1103/PhysRevE.49.4677.", "Phys. Rev. E"),
    "friedman1937": _it("M. Friedman, \"The use of ranks to avoid the assumption of normality implicit in the analysis of variance,\" J. Amer. Statist. Assoc., vol. 32, no. 200, pp. 675-701, 1937, doi: 10.1080/01621459.1937.10503522.", "J. Amer. Statist. Assoc."),
    "wilcoxon1945": _it("F. Wilcoxon, \"Individual comparisons by ranking methods,\" Biometrics Bull., vol. 1, no. 6, pp. 80-83, 1945, doi: 10.2307/3001968.", "Biometrics Bull."),
    "mannwhitney1947": _it("H. B. Mann and D. R. Whitney, \"On a test of whether one of two random variables is stochastically larger than the other,\" Ann. Math. Statist., vol. 18, no. 1, pp. 50-60, 1947, doi: 10.1214/aoms/1177730491.", "Ann. Math. Statist."),
    "holm1979": _it("S. Holm, \"A simple sequentially rejective multiple test procedure,\" Scand. J. Statist., vol. 6, no. 2, pp. 65-70, 1979.", "Scand. J. Statist."),
    "vanthieu2024": _it("N. Van Thieu, \"Opfunu: An open-source Python library for optimization benchmark functions,\" J. Open Res. Softw., vol. 12, art. no. 8, 2024, doi: 10.5334/jors.508.", "J. Open Res. Softw."),
    "maheswaran1999": _it("M. Maheswaran, S. Ali, H. J. Siegel, D. Hensgen, and R. F. Freund, \"Dynamic mapping of a class of independent tasks onto heterogeneous computing systems,\" J. Parallel Distrib. Comput., vol. 59, no. 2, pp. 107-131, 1999, doi: 10.1006/jpdc.1999.1581.", "J. Parallel Distrib. Comput."),
    "beloglazov2012": _it("A. Beloglazov, J. Abawajy, and R. Buyya, \"Energy-aware resource allocation heuristics for efficient management of data centers for cloud computing,\" Future Gener. Comput. Syst., vol. 28, no. 5, pp. 755-768, 2012, doi: 10.1016/j.future.2011.04.017.", "Future Gener. Comput. Syst."),
}
