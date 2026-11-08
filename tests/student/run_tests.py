"""Run from the repository root:  python tests/student/run_tests.py
Writes cases.jsonl (inputs), actual_outputs.jsonl (outputs) and prints PASS/FAIL for every check."""
import json, os, random, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "Python", "source")
sys.path.insert(0, SRC)
sys.path.insert(0, HERE)
import algorithms as A


def handle(request):
    """Same dispatch as the supplied main.py (which is a script and cannot be imported); the supplied main.py itself
    is exercised end-to-end through stdin/stdout further below."""
    return {"status": "ready"} if request["task"] == "ping" else getattr(A, request["task"])(request)


import checkers as C

passed = failed = 0
log_in, log_out = [], []


def record(name, ok, extra=""):
    global passed, failed
    passed += bool(ok)
    failed += (not ok)
    print(("PASS " if ok else "FAIL ") + name + (" " + extra if extra else ""))


def run(req, store=True):
    out = handle(json.loads(json.dumps(req)))          # same JSON round-trip as the real adapter
    if store:
        log_in.append(req); log_out.append(out)
    return out


def expect(name, req, want):
    out = run(req)
    record(name, out == want, "" if out == want else f"got {out} want {want}")


def valid(name, fn, *a, **k):
    try:
        fn(*a, **k); record(name, True)
    except C.Invalid as e:
        record(name, False, str(e))


def rejects(name, fn, *a, **k):
    try:
        fn(*a, **k); record(name, False, "checker accepted an invalid witness")
    except C.Invalid:
        record(name, True)


# =============================== 1. LCS ===============================
print("== LCS ==")
for name, a, b, L in [("spec tea_time/team", "tea_time", "team", 4), ("both empty", "", "", 0), ("a empty", "", "xyz", 0),
                      ("b empty", "xyz", "", 0), ("identical", "abcabc", "abcabc", 6), ("disjoint", "abc", "xyz", 0),
                      ("textbook AGGTAB/GXTXAYB (GTAB)", "AGGTAB", "GXTXAYB", 4), ("case-sensitive", "ABC", "abc", 0),
                      ("spaces and punctuation are ordinary characters", "a, b", " b", 2),
                      ("non-contiguous (a_b_c vs abc)", "a_b_c", "abc", 3), ("single char repeated", "aaaa", "aa", 2)]:
    out = run({"task": "lcs", "a": a, "b": b})
    valid(f"lcs {name}", C.check_lcs, a, b, out, L)
out = run({"task": "lcs", "a": "", "b": ""})
record("lcs empty gives sequence ''", out == {"length": 0, "sequence": ""})

# =============================== 2. merge ===============================
print("== Merge ==")
expect("merge n=0", {"task": "merge", "sizes": []}, {"cost": 0, "plan": []})
expect("merge n=1", {"task": "merge", "sizes": [7]}, {"cost": 0, "plan": []})
expect("merge spec [2,3,4] (cost 14, not 16)", {"task": "merge", "sizes": [2, 3, 4]}, {"cost": 14, "plan": [[0, 0, 1], [0, 1, 2]]})
for name, sz, want in [("zeros", [0, 0, 0], 0), ("[1,100,1] is 203 either way", [1, 100, 1], 203),
                       ("four ones (balanced 2+2+4)", [1, 1, 1, 1], 8), ("n=2", [5, 6], 11),
                       ("sizes 1e9 (cost beyond 32 bits: 5e9)", [10**9] * 3, 5 * 10**9),
                       ("adjacency matters: greedy smallest-two is wrong on [4,1,4,1,4]", [4, 1, 4, 1, 4], None)]:
    out = run({"task": "merge", "sizes": sz})
    valid(f"merge {name}", C.check_merge, sz, out, want if want is not None else C.merge_bruteforce(sz))
out = run({"task": "merge", "sizes": [10**9] * 200}, store=False)
valid("merge n=200 sizes 1e9 valid plan (199 merges)", C.check_merge, [10**9] * 200, out)

# =============================== 3. tree ===============================
print("== Tree independent set ==")
expect("tree n=0", {"task": "tree", "n": 0, "weights": [], "edges": []}, {"weight": 0, "selected": []})
expect("tree spec", {"task": "tree", "n": 3, "weights": [4, 9, 6], "edges": [[0, 1], [1, 2]]}, {"weight": 10, "selected": [0, 2]})
expect("tree n=1 positive", {"task": "tree", "n": 1, "weights": [5], "edges": []}, {"weight": 5, "selected": [0]})
expect("tree n=1 negative -> empty set", {"task": "tree", "n": 1, "weights": [-3], "edges": []}, {"weight": 0, "selected": []})
expect("tree all negative -> 0", {"task": "tree", "n": 3, "weights": [-1, -2, -3], "edges": [[0, 1], [1, 2]]}, {"weight": 0, "selected": []})
for name, n, w, e, want in [
        ("star, leaves beat centre (18 vs 10)", 4, [10, 6, 6, 6], [[0, 1], [0, 2], [0, 3]], 18),
        ("star, centre wins", 4, [20, 6, 6, 6], [[0, 1], [0, 2], [0, 3]], 20),
        ("zero weights", 3, [0, 0, 0], [[0, 1], [1, 2]], 0),
        ("totals beyond 32 bits (3e9)", 5, [10**9] * 5, [[0, 1], [1, 2], [2, 3], [3, 4]], 3 * 10**9),
        ("negative middle vertex skipped", 3, [5, -100, 5], [[0, 1], [1, 2]], 10),
        ("edges not rooted at 0 (reversed endpoints)", 4, [1, 8, 1, 8], [[1, 0], [2, 1], [3, 2]], 16)]:
    out = run({"task": "tree", "n": n, "weights": w, "edges": e})
    valid(f"tree {name}", C.check_tree, n, w, e, out, want)
rejects("tree checker rejects adjacent selection", C.check_tree, 2, [1, 1], [[0, 1]], {"weight": 2, "selected": [0, 1]})
rejects("tree checker rejects wrong weight", C.check_tree, 2, [1, 1], [[0, 1]], {"weight": 5, "selected": [0]})
rejects("tree checker rejects suboptimal weight", C.check_tree, 3, [4, 9, 6], [[0, 1], [1, 2]], {"weight": 9, "selected": [1]}, 10)

# ======================= 4. naive / kmp / rk ==========================
print("== Exact search (naive, KMP, Rabin-Karp) ==")
cases = [("spec overlaps aaaaa/aaa", "aaaaa", "aaa", [0, 1, 2]), ("spec abababa/aba", "abababa", "aba", [0, 2, 4]),
         ("spec RK collision abdj/ab (dj hashes like ab)", "abdj", "ab", [0]), ("empty pattern -> every boundary 0..n", "abc", "", [0, 1, 2, 3]),
         ("both empty -> [0]", "", "", [0]), ("pattern longer than text", "ab", "abc", []), ("empty text, nonempty pattern", "", "a", []),
         ("pattern equals text", "hello", "hello", [0]), ("last valid start is found", "xxab", "ab", [2]), ("no match", "abcabc", "abd", []),
         ("case sensitive", "Ab", "aB", []), ("spaces are ordinary", "a b a b", "a b", [0, 4]), ("single char pattern", "banana", "a", [1, 3, 5]),
         ("punctuation", "a.b.c", ".", [1, 3])]
for name, t, p, want in cases:
    for algo in ("naive", "kmp", "rk"):
        expect(f"{algo} {name}", {"task": algo, "text": t, "pattern": p}, {"positions": want})
# explicit hash-collision check: both windows have hash 75, only one is a real match
record("collision premise: hash('ab') == hash('dj') == 75 (base 31, mod 101)",
       (97 * 31 + 98) % 101 == 75 and (100 * 31 + 106) % 101 == 75)

# ===================== 5. suffix array + Kasai ========================
print("== Suffix array and Kasai LCP ==")
expect("suffix banana (spec)", {"task": "suffix", "text": "banana"}, {"sa": [5, 3, 1, 0, 4, 2], "lcp": [0, 1, 3, 0, 0, 2], "repeated": "ana"})
expect("suffix empty", {"task": "suffix", "text": ""}, {"sa": [], "lcp": [], "repeated": ""})
expect("suffix n=1", {"task": "suffix", "text": "a"}, {"sa": [0], "lcp": [0], "repeated": ""})
expect("suffix aaaa (overlapping repeat aaa)", {"task": "suffix", "text": "aaaa"}, {"sa": [3, 2, 1, 0], "lcp": [0, 1, 2, 3], "repeated": "aaa"})
expect("suffix abc (no repeat)", {"task": "suffix", "text": "abc"}, {"sa": [0, 1, 2], "lcp": [0, 0, 0], "repeated": ""})
for t in ["mississippi", "a b a b", "abracadabra", "AaAa", "zzzzy"]:
    valid(f"suffix '{t}' vs oracle", C.check_suffix, t, run({"task": "suffix", "text": t}), C.suffix_oracle(t))

# ============================ 6. Aho-Corasick ==========================
print("== Aho-Corasick ==")
expect("aho spec (suffix pattern + duplicate + empty text)", {"task": "aho", "patterns": ["he", "she", "he"], "texts": ["sheshe", "sheshe", ""]},
       {"counts": [[2, 2, 2], [2, 2, 2], [0, 0, 0]]})
expect("aho no patterns -> empty row per text", {"task": "aho", "patterns": [], "texts": ["abc", ""]}, {"counts": [[], []]})
expect("aho no texts -> []", {"task": "aho", "patterns": ["a"], "texts": []}, {"counts": []})
expect("aho no patterns and no texts", {"task": "aho", "patterns": [], "texts": []}, {"counts": []})
expect("aho overlaps aa in aaaa -> 3", {"task": "aho", "patterns": ["aa"], "texts": ["aaaa"]}, {"counts": [[3]]})
expect("aho nested patterns a, ab, bab, bc, bca, c, caa", {"task": "aho", "patterns": ["a", "ab", "bab", "bc", "bca", "c", "caa"], "texts": ["abccab"]},
       {"counts": [C.aho_oracle(["a", "ab", "bab", "bc", "bca", "c", "caa"], ["abccab"])[0]]})
expect("aho repeated texts are independent", {"task": "aho", "patterns": ["ab"], "texts": ["abab", "abab", "ab"]}, {"counts": [[2], [2], [1]]})
expect("aho space and punctuation patterns", {"task": "aho", "patterns": [" ", ".", "a b"], "texts": ["a b. a b."]}, {"counts": [[3, 2, 2]]})

# ============================ randomized ================================
print("== Randomized differential tests (seeded) ==")
rnd = random.Random(2026)
bad = 0
for it in range(300):
    try:
        alpha = rnd.choice(["ab", "abc", "a b", "xyz.A"])
        a = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 9)))
        b = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 9)))
        C.check_lcs(a, b, run({"task": "lcs", "a": a, "b": b}, store=it < 15), C.lcs_bruteforce_len(a, b))
        sz = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 6))]
        C.check_merge(sz, run({"task": "merge", "sizes": sz}, store=it < 15), C.merge_bruteforce(sz) if len(sz) > 1 else 0)
        n = rnd.randint(0, 11)
        w = [rnd.randint(-6, 9) for _ in range(n)]
        e = [[rnd.randrange(i), i] if rnd.random() < .5 else [i, rnd.randrange(i)] for i in range(1, n)]   # random tree
        C.check_tree(n, w, e, run({"task": "tree", "n": n, "weights": w, "edges": e}, store=it < 15), C.tree_bruteforce(n, w, e))
        t = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 30)))
        p = "".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 5)))
        want = C.search_oracle(t, p)
        for algo in ("naive", "kmp", "rk"):
            got = run({"task": algo, "text": t, "pattern": p}, store=it < 15)["positions"]
            C.need(got == want, f"{algo} {t!r} {p!r}: {got} != {want}")
        C.check_suffix(t, run({"task": "suffix", "text": t}, store=it < 15), C.suffix_oracle(t))
        pats = ["".join(rnd.choice(alpha) for _ in range(rnd.randint(1, 4))) for _ in range(rnd.randint(0, 6))]
        texts = [("".join(rnd.choice(alpha) for _ in range(rnd.randint(0, 20)))) for _ in range(rnd.randint(0, 4))]
        got = run({"task": "aho", "patterns": pats, "texts": texts}, store=it < 15)["counts"]
        C.need(got == C.aho_oracle(pats, texts), f"aho {pats} {texts}")
    except C.Invalid as ex:
        bad += 1
        print("   mismatch:", ex)
record("300 random small instances: all eight commands vs brute-force oracles", bad == 0)

# ============================ state reset ===============================
print("== State reset ==")
batch = [{"task": "ping"},
         {"task": "lcs", "a": "tea_time", "b": "team"}, {"task": "merge", "sizes": [2, 3, 4]},
         {"task": "tree", "n": 3, "weights": [4, 9, 6], "edges": [[0, 1], [1, 2]]},
         {"task": "naive", "text": "aaaaa", "pattern": "aaa"}, {"task": "kmp", "text": "abababa", "pattern": "aba"},
         {"task": "rk", "text": "abdj", "pattern": "ab"}, {"task": "suffix", "text": "banana"},
         {"task": "aho", "patterns": ["he", "she", "he"], "texts": ["sheshe", "sheshe", ""]},
         {"task": "aho", "patterns": ["zz"], "texts": ["zz"]}, {"task": "suffix", "text": ""},
         {"task": "tree", "n": 0, "weights": [], "edges": []}, {"task": "lcs", "a": "", "b": "q"}]
first = [handle(json.loads(json.dumps(b))) for b in batch]
again = [handle(json.loads(json.dumps(b))) for _ in range(3) for b in batch]
record("mixed batch repeated 3x in one process gives identical outputs", again == first * 3)
log_in.extend(batch); log_out.extend(first)
lines = "\n".join(json.dumps(x, separators=(",", ":")) for x in batch + batch) + "\n"
p = subprocess.run([sys.executable, os.path.join(SRC, "main.py")], input=lines, capture_output=True, text=True)
outs = [json.loads(l) for l in p.stdout.splitlines()]
record("stdin/stdout: one line per request, nothing else on stdout/stderr", p.returncode == 0 and len(outs) == 2 * len(batch) and p.stderr == "")
record("stdin/stdout: second pass equals first pass", outs[:len(batch)] == outs[len(batch):])

# ============================ domain limits ==============================
print("== Full published domains ==")
rg = random.Random(99)


def timed(name, req, check):
    t0 = time.perf_counter()
    out = handle(json.loads(json.dumps(req)))
    dt = time.perf_counter() - t0
    ok = True
    try:
        check(out)
    except (C.Invalid, AssertionError) as ex:
        ok = False; print("   ", ex)
    record(name, ok, f"[{dt:.2f}s incl. request JSON round-trip]")
    return out


def rs(n, alpha):
    return "".join(rg.choice(alpha) for _ in range(n))


a, b = rs(1000, "abcd"), rs(1000, "abcd")
timed("lcs 1000x1000 random: optimal length vs independent rolling-row DP", {"task": "lcs", "a": a, "b": b}, lambda o: C.check_lcs(a, b, o, C.lcs_len_rolling(a, b)))
timed("lcs 1000x1000 identical strings", {"task": "lcs", "a": "a" * 1000, "b": "a" * 1000}, lambda o: C.check_lcs("a" * 1000, "a" * 1000, o, 1000))
long_a = rs(1000, "ab"); long_b = rs(1000, "ab")
timed("lcs 1000x1000 binary alphabet: optimal length vs independent DP", {"task": "lcs", "a": long_a, "b": long_b}, lambda o: C.check_lcs(long_a, long_b, o, C.lcs_len_rolling(long_a, long_b)))
sz = [rg.randint(0, 10**9) for _ in range(200)]
timed("merge n=200 random sizes up to 1e9: valid plan, optimal cost vs Knuth O(n^2)", {"task": "merge", "sizes": sz}, lambda o: C.check_merge(sz, o, C.merge_knuth(sz)))
sz0 = [rg.choice([0, 0, 1, 10**9]) for _ in range(200)]
timed("merge n=200 many zero blocks: optimal cost vs Knuth O(n^2)", {"task": "merge", "sizes": sz0}, lambda o: C.check_merge(sz0, o, C.merge_knuth(sz0)))
for _ in range(60):
    szr = [rg.randint(0, 20) for _ in range(rg.randint(2, 7))]
    assert C.merge_knuth(szr) == C.merge_bruteforce(szr), szr
record("oracle sanity: Knuth optimisation == brute force on 60 random small inputs", True)


def tree_check(n, w, e, expected=None):
    return lambda o: C.check_tree(n, w, e, o, expected)


N = 100000
w = [rg.randint(-10**9, 10**9) for _ in range(N)]
chain = [[i, i + 1] for i in range(N - 1)]


def chain_dp(w):
    take, skip = 0, 0
    for x in w:                        # independent chain DP written separately from the solution
        take, skip = skip + x, max(take, skip)
    return max(take, skip, 0)


timed("tree chain n=1e5 (deep, no recursion; vs independent chain DP)", {"task": "tree", "n": N, "weights": w, "edges": chain},
      tree_check(N, w, chain, chain_dp(w)))
star = [[0, i] for i in range(1, N)]
wpos = [10**9] * N
timed("tree star n=1e5 (leaves total 99999e9)", {"task": "tree", "n": N, "weights": wpos, "edges": star}, tree_check(N, wpos, star, (N - 1) * 10**9))
rnd_edges = [[rg.randrange(i), i] for i in range(1, N)]
timed("tree random n=1e5 valid independent set", {"task": "tree", "n": N, "weights": w, "edges": rnd_edges}, tree_check(N, w, rnd_edges))
# random tree vs an independent iterative DP in a different (index) order: parents have smaller index
def tree_index_dp(n, w, edges):
    par = [-1] * n
    for u, v in edges:
        par[v] = u
    take = list(w); skip = [0] * n
    for v in range(n - 1, 0, -1):
        take[par[v]] += skip[v]; skip[par[v]] += max(take[v], skip[v])
    return max(take[0], skip[0])
timed("tree random n=1e5 optimum vs independent index-order DP", {"task": "tree", "n": N, "weights": w, "edges": rnd_edges},
      tree_check(N, w, rnd_edges, tree_index_dp(N, w, rnd_edges)))

T3 = "a" * 3000
timed("naive text 3000 x pattern 1000 (worst case a^n vs a^k b)", {"task": "naive", "text": T3, "pattern": "a" * 1000 + "b"},
      lambda o: C.need(o["positions"] == [], "should be empty"))
timed("naive text 3000 x pattern 3000 equal", {"task": "naive", "text": T3, "pattern": T3}, lambda o: C.need(o["positions"] == [0], "[0]"))
timed("naive empty pattern on text 3000 -> 3001 starts", {"task": "naive", "text": T3, "pattern": ""}, lambda o: C.need(o["positions"] == list(range(3001)), "boundaries"))
big_t = rs(200000, "ab"); big_p = rs(14, "ab")
timed("kmp text 200000 random binary, pattern 14", {"task": "kmp", "text": big_t, "pattern": big_p}, lambda o: C.need(o["positions"] == C.search_oracle(big_t, big_p), "kmp != oracle"))
bt, bp = "a" * 200000, "a" * 100000
timed("kmp text 200000, pattern 100000 all 'a' (100001 overlapping starts)", {"task": "kmp", "text": bt, "pattern": bp},
      lambda o: C.need(o["positions"] == list(range(100001)), "kmp dense"))
timed("kmp empty pattern on text 200000 -> 200001 starts", {"task": "kmp", "text": bt, "pattern": ""}, lambda o: C.need(len(o["positions"]) == 200001, "boundaries"))
timed("rk 10000 x 2000 all 'a' (every window is a verified match; |t||p|=2e7)", {"task": "rk", "text": "a" * 10000, "pattern": "a" * 2000},
      lambda o: C.need(o["positions"] == list(range(8001)), "rk dense"))
rt, rp = rs(10000, "abc"), rs(8, "abc")
timed("rk random 10000 x 8 (many hash collisions with mod 101)", {"task": "rk", "text": rt, "pattern": rp},
      lambda o: C.need(o["positions"] == C.search_oracle(rt, rp), "rk != oracle"))
cmp_t, cmp_p = rs(3000, "ab"), rs(5, "ab")
res = [handle({"task": x, "text": cmp_t, "pattern": cmp_p})["positions"] for x in ("naive", "kmp", "rk")]
record("naive, kmp and rk agree on a 3000-char common-domain input", res[0] == res[1] == res[2] == C.search_oracle(cmp_t, cmp_p))

st = rs(50000, "abcdefghij")
def chk_random_suffix(o):
    C.check_suffix(st, o)
    ref = sorted(range(50000), key=lambda i: st[i:i + 60])      # 60 random letters decide every comparison
    C.need(o["sa"] == ref, "sa differs from sorted-suffix oracle")
    for r in range(1, 50000):
        a_, b_ = st[o["sa"][r - 1]:o["sa"][r - 1] + 200], st[o["sa"][r]:o["sa"][r] + 200]
        h = 0
        while h < min(len(a_), len(b_)) and a_[h] == b_[h]:
            h += 1
        C.need(o["lcp"][r] == h, f"lcp[{r}] wrong")
    C.need(len(o["repeated"]) == C.longest_repeat_len_fast(st), "repeated length not maximal")


timed("suffix n=50000 random 10 letters (sa and every lcp vs oracle)", {"task": "suffix", "text": st}, chk_random_suffix)
timed("suffix n=50000 'a'*50000 (worst depth: 16 doubling rounds)", {"task": "suffix", "text": "a" * 50000},
      lambda o: C.need(o["sa"] == list(range(49999, -1, -1)) and o["lcp"] == list(range(50000)) and o["repeated"] == "a" * 49999, "all-a"))
per = "ab" * 25000
timed("suffix n=50000 'ab'*25000 (periodic, longest repeat has length 49998)", {"task": "suffix", "text": per},
      lambda o: (C.check_suffix(per, o), C.need(len(o["repeated"]) == 49998 and o["repeated"] in ("ab" * 24999, "ba" * 24999), "periodic repeat")))
mid = rs(2000, "ab")
timed("suffix n=2000 binary: exact match with sorted-suffix oracle", {"task": "suffix", "text": mid},
      lambda o: C.check_suffix(mid, o, C.suffix_oracle(mid)))

fib = ["a", "ab"]
while len(fib[-1]) < 1500:
    fib.append(fib[-1] + fib[-2])
for name, t in [("Fibonacci word (1597 chars)", fib[-1]), ("'ab'*1000 periodic", "ab" * 1000), ("'a'*1500", "a" * 1500), ("'abc'*400 + 'x'", "abc" * 400 + "x")]:
    timed(f"suffix {name}: sa, lcp and repeated vs oracle", {"task": "suffix", "text": t}, lambda o, t=t: C.check_suffix(t, o, C.suffix_oracle(t)))

# aho: dense matches with closed-form answers
pats = ["a" * k for k in range(1, 441)]                 # 440 patterns, total length 97 460
texts = ["a" * 2000 for _ in range(100)]                # total 200 000
want = [[max(2000 - k + 1, 0) for k in range(1, 441)] for _ in range(100)]
timed("aho dense: 440 patterns a^k, 100 texts a^2000 (closed form L-k+1)", {"task": "aho", "patterns": pats, "texts": texts},
      lambda o: C.need(o["counts"] == want, "dense aho"))
many = ["".join(rg.choice("ab") for _ in range(rg.randint(1, 18))) for _ in range(10000)]
tl = sum(map(len, many))
record(f"(info) aho random dictionary has 10000 patterns, total length {tl} <= 100000", tl <= 100000)
tx = [rs(2000, "ab") for _ in range(100)]
timed("aho 10000 random patterns (duplicates likely), 100 texts x 2000", {"task": "aho", "patterns": many, "texts": tx},
      lambda o: C.need(o["counts"][:5] == C.aho_oracle(many, tx[:5]) and len(o["counts"]) == 100, "aho vs oracle (first 5 texts)"))
tx_all = tx[:20]
small = many[:1500]
timed("aho 1500 patterns x 20 texts: all counts vs oracle", {"task": "aho", "patterns": small, "texts": tx_all},
      lambda o: C.need(o["counts"] == C.aho_oracle(small, tx_all), "aho full compare"))

with open(os.path.join(HERE, "cases.jsonl"), "w") as f:
    for x in log_in:
        f.write(json.dumps(x, separators=(",", ":")) + "\n")
with open(os.path.join(HERE, "actual_outputs.jsonl"), "w") as f:
    for x in log_out:
        f.write(json.dumps(x, separators=(",", ":")) + "\n")
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
