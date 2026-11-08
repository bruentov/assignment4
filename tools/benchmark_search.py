"""Naive vs KMP vs exact Rabin-Karp (base 31, mod 101).  Run from the repo root:  python tools/benchmark_search.py
Timer: time.perf_counter().  Boundary: the algorithm function on an already-parsed request dict
(no JSON parsing, no printing).  Every input is generated from fixed seeds; the three outputs are
checked to be identical (and equal to a str.find oracle) BEFORE anything is timed."""
import json, os, platform, random, statistics, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Python", "source"))
import algorithms as A

REPS, TARGET = 5, 0.05            # 5 repetitions; each repetition runs the call enough times to last >= 50 ms
SIZES = [1000, 2000, 3000]        # |text|; the pattern is |text|/3 (common domain of all three: <= 3000)


def rk_charloop(req):
    """INFORMATIONAL variant only (not the submitted rk): identical rolling hash, but each equal-hash
    candidate is verified with an interpreted character-by-character loop instead of a C-level slice
    comparison. It shows the c*m term of the O(n+m+c*m) bound that the slice comparison hides."""
    text, pat = req["text"], req["pattern"]
    n, m = len(text), len(pat)
    hp = hw = 0
    for i in range(m):
        hp = (hp * 31 + ord(pat[i])) % 101
        hw = (hw * 31 + ord(text[i])) % 101
    high = pow(31, m - 1, 101)
    out = []
    for i in range(n - m + 1):
        if hw == hp:
            j = 0
            while j < m and text[i + j] == pat[j]:
                j += 1
            if j == m:
                out.append(i)
        if i + m < n:
            hw = ((hw - ord(text[i]) * high) * 31 + ord(text[i + m])) % 101
    return {"positions": out}


def candidates(t, p):
    """Number of windows whose hash equals the pattern hash (the c of the analysis)."""
    m = len(p)
    hp = 0
    for ch in p:
        hp = (hp * 31 + ord(ch)) % 101
    c = 0
    for i in range(len(t) - m + 1):
        h = 0
        for ch in t[i:i + m]:
            h = (h * 31 + ord(ch)) % 101
        c += (h == hp)
    return c


def oracle(t, p):
    out, i = [], t.find(p)
    while i != -1:
        out.append(i); i = t.find(p, i + 1)
    return out


def workloads(n):
    rg = random.Random(4000 + n)
    m = n // 3
    return [
        ("A random binary text, random pattern m=10", "".join(rg.choice("ab") for _ in range(n)), "".join(rg.choice("ab") for _ in range(10))),
        (f"B text a^n, pattern a^(m-1)b, m={m} (no match; naive worst case)", "a" * n, "a" * (m - 1) + "b"),
        (f"C text a^n, pattern a^m, m={m} (every window matches; z=n-m+1)", "a" * n, "a" * m),
    ]


def per_call(fn, req):
    fn(req)                                           # warm-up, not recorded
    k, t0 = 1, time.perf_counter()
    while True:
        for _ in range(k):
            fn(req)
        dt = time.perf_counter() - t0
        if dt >= TARGET:
            break
        k *= 2; t0 = time.perf_counter()
    k = max(1, k)
    runs = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        for _ in range(k):
            fn(req)
        runs.append((time.perf_counter() - t0) / k)
    return runs


rows = []
for n in SIZES:
    for name, t, p in workloads(n):
        req = {"text": t, "pattern": p}
        res = [A.naive(req)["positions"], A.kmp(req)["positions"], A.rk(req)["positions"], rk_charloop(req)["positions"]]
        assert res[0] == res[1] == res[2] == res[3] == oracle(t, p), "outputs differ"
        row = {"n": n, "m": len(p), "workload": name, "matches": len(res[0]), "rk_candidate_windows": candidates(t, p)}
        for label, fn in (("naive", A.naive), ("kmp", A.kmp), ("rk", A.rk), ("rk_charloop", rk_charloop)):   # interleaving not needed: runs are independent
            runs = per_call(fn, req)
            row[label + "_median_ms"] = round(statistics.median(runs) * 1000, 3)
            row[label + "_runs_ms"] = [round(x * 1000, 3) for x in runs]
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if not k.endswith("runs_ms")}))
json.dump(rows, open(os.path.join(HERE, "..", "tests", "student", "benchmark_results.json"), "w"), indent=1)
print(f"\nPython {platform.python_version()} on {platform.platform()}; processor: {platform.processor() or 'n/a'}")
GEN = {"A": "seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b}",
       "B": "deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3",
       "C": "deterministic (no seed): text a^n, pattern a^m, m=n//3"}
lines = ["| Case | n | m | Seed/generator | Algorithm | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Median | Correct outputs checked |",
         "|---|--:|--:|---|---|--:|--:|--:|--:|--:|--:|---|"]
for r in rows:
    case = r["workload"][0]
    kind = {"A": "A random", "B": "B repetitive, no match", "C": "C repetitive, all match"}[case]
    for label, shown in (("naive", "naive"), ("kmp", "KMP"), ("rk", "RK (submitted, slice verify)"), ("rk_charloop", "RK char-loop verify (informational)")):
        runs = " | ".join(f"{x:.3f}" for x in r[label + "_runs_ms"])
        lines.append(f"| {kind} | {r['n']} | {r['m']} | {GEN[case]} | {shown} | {runs} | **{r[label + '_median_ms']:.3f}** | "
                     f"{len(r['workload']) and r['matches']} matches; naive=KMP=RK=char-loop=str.find oracle |")
table = "\n".join(lines)
open(os.path.join(HERE, "..", "tests", "student", "benchmark_table.md"), "w").write(table + "\n")
print("\nTable (unit: milliseconds per call):\n" + table)
print("\nRK candidate windows c (equal-hash windows): " + ", ".join(f"n={r['n']} case {r['workload'][0]}: {r['rk_candidate_windows']}" for r in rows))
