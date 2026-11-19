"""Check each bibliography entry against Crossref (title, year, container, volume, pages).

Usage:  python tools/verify_references.py            (prints a report and writes docs/reference_check.json)

Entries with a DOI are looked up directly. Entries without one are searched by their citation text and the
best match is shown for human review. Nothing here edits the paper; it only reports.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = "oioa-reference-check/1.0 (research code; Crossref REST API client)"

# (key, kind, value, expected title fragment)
REFS = [
    ("sanaj2026", "doi", "10.1007/s44196-025-01095-w", "EcoTaskOpt"),
    ("mehta2026a", "doi", "10.1007/s42452-026-08395-6", "Pareto knee"),
    ("mandal2026", "doi", "10.1007/s10115-026-02866-3", "coordination among PSO"),
    ("li2026", "doi", "10.26599/CAI.2025.9390011", "two-layer PSO"),
    ("dossantos2026", "doi", "10.1109/ACCESS.2026.3692710", "Weighted Target Approximation"),
    ("awad2026", "doi", "10.1109/OJCOMS.2026.3689759", "Golden Jackal"),
    ("abdalhaq2026", "doi", "10.1109/ACCESS.2026.3664310", "Distance Uniqueness"),
    ("vithana2026", "doi", "10.1109/ACCESS.2026.3734747", "Multi-Agent Coordination"),
    ("mehta2026b", "doi", "10.1016/j.swevo.2026.102510", "Adaptive Enhanced Particle Swarm"),
    ("xie2026", "doi", "10.1016/j.swevo.2026.102422", "multi-workflow scheduling"),
    ("kennedy1995", "q", "Kennedy Eberhart Particle swarm optimization 1995 IEEE International Conference on Neural Networks", "Particle swarm optimization"),
    ("mirjalili2014", "q", "Mirjalili Grey wolf optimizer Advances in Engineering Software 2014", "Grey Wolf"),
    ("karaboga2007", "q", "Karaboga Basturk powerful and efficient algorithm for numerical function optimization artificial bee colony", "bee colony"),
    ("dorigo1996", "q", "Dorigo Maniezzo Colorni Ant system optimization by a colony of cooperating agents", "Ant system"),
    ("storn1997", "q", "Storn Price Differential evolution simple and efficient heuristic for global optimization over continuous spaces", "Differential Evolution"),
    ("rao2011", "q", "Rao Savsani Vakharia Teaching-learning-based optimization novel method constrained mechanical design", "Teaching"),
    ("mirjalili2016", "q", "Mirjalili Lewis The whale optimization algorithm Advances in Engineering Software 2016", "Whale"),
    ("heidari2019", "q", "Heidari Mirjalili Faris Harris hawks optimization algorithm and applications", "Harris hawks"),
    ("tizhoosh2005", "q", "Tizhoosh Opposition-based learning a new scheme for machine intelligence", "Opposition"),
    ("wolpert1997", "q", "Wolpert Macready No free lunch theorems for optimization", "free lunch"),
    ("sorensen2015", "q", "Sorensen Metaheuristics the metaphor exposed", "metaphor"),
    ("camacho2023", "q", "Camacho-Villalon Stutzle Dorigo Exposing the grey wolf moth-flame whale firefly bat antlion algorithms", "grey wolf"),
    ("crepinsek2013", "doi", "10.1145/2480741.2480752", "Exploration and exploitation"),
    ("derrac2011", "q", "Derrac Garcia Molina Herrera practical tutorial on the use of nonparametric statistical tests", "nonparametric"),
    ("calheiros2011", "q", "Calheiros Ranjan Beloglazov De Rose Buyya CloudSim toolkit for modeling and simulation of cloud computing", "CloudSim"),
    ("fiorito1992", "q", "Fiorito Scotto Observational learning in Octopus vulgaris Science 1992", "Observational"),
    ("norman2001", "q", "Norman Finn Tregenza Dynamic mimicry in an Indo-Malayan octopus", "mimicry"),
    ("hochner2012", "q", "Hochner An embodied view of octopus neurobiology Current Biology 2012", "embodied"),
    ("finn2009", "q", "Finn Tregenza Norman Defensive tool use in a coconut-carrying octopus", "coconut"),
    ("yang2009", "q", "Yang Deb Cuckoo search via Levy flights NaBIC 2009", "Cuckoo"),
    ("hanlon2007", "q", "Hanlon Cephalopod dynamic camouflage Current Biology 2007", "camouflage"),
    ("hochner2006", "q", "Hochner Shomrat Fiorito The octopus a model for a comparative analysis of the evolution of learning and memory mechanisms", "octopus"),
    ("hanlon2018", "doi", "10.1017/9780511843600", "Cephalopod Behaviour"),
    # candidates for new citations
    ("mantegna1994", "doi", "10.1103/PhysRevE.49.4677", "Fast, accurate algorithm"),
    ("holm1979", "q", "Holm A simple sequentially rejective multiple test procedure Scandinavian Journal of Statistics 1979", "multiple test"),
    ("friedman1937", "doi", "10.1080/01621459.1937.10503522", "ranks"),
    ("wilcoxon1945", "doi", "10.2307/3001968", "Individual comparisons"),
    ("mannwhitney1947", "doi", "10.1214/aoms/1177730491", "stochastically larger"),
    ("opfunu", "doi", "10.5334/jors.508", "opfunu"),
    ("maheswaran1999", "doi", "10.1006/jpdc.1999.1581", "Dynamic mapping"),
    ("beloglazov2012", "doi", "10.1016/j.future.2011.04.017", "Energy-aware"),
]


def get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def summarize(item: dict) -> dict:
    issued = (item.get("issued", {}).get("date-parts") or [[None]])[0][0]
    authors = ", ".join(f"{a.get('family', '?')}" for a in item.get("author", [])[:4])
    return {"title": (item.get("title") or [""])[0], "year": issued,
            "container": (item.get("container-title") or [""])[0], "volume": item.get("volume"),
            "issue": item.get("issue"), "page": item.get("page") or item.get("article-number"),
            "authors": authors, "doi": item.get("DOI")}


def main():
    out = {}
    for key, kind, val, frag in REFS:
        try:
            if kind == "doi":
                item = get("https://api.crossref.org/works/" + urllib.parse.quote(val))["message"]
                s = summarize(item)
                ok = frag.lower() in s["title"].lower() or frag.lower() in json.dumps(item).lower()
                status = "DOI-OK" if ok else "DOI-MISMATCH?"
            else:
                items = get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(val))["message"]["items"]
                cands = [summarize(i) for i in items]
                s = next((c for c in cands if frag.lower() in c["title"].lower()), cands[0] if cands else {})
                status = "MATCH" if s and frag.lower() in s["title"].lower() else "NO-MATCH"
            out[key] = {"status": status, **s}
        except Exception as exc:                         # report, keep going
            out[key] = {"status": f"ERROR {exc!r}"}
        r = out[key]
        print(f"{key:15s} {r['status']:14s} {r.get('year')} | {r.get('container', '')[:38]:38s} v{r.get('volume')} "
              f"i{r.get('issue')} p{r.get('page')} | {r.get('title', '')[:70]}")
        time.sleep(0.3)
    dest = Path(__file__).resolve().parents[1] / "docs" / "reference_check.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    bad = [k for k, v in out.items() if v["status"] not in ("DOI-OK", "MATCH")]
    print("\nneeds review:", bad or "none")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
