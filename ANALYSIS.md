# Assignment 4 — analysis (complete in English)

## Environment and commands

* **Language / runtime:** Python 3.12.3 (CPython), standard library only (`itertools.accumulate`). `submission.json`: `{"language":"Python"}`.
* **Machine used for every number in this file:** Ubuntu 24.04.4 LTS, Linux 6.18.44 x86_64, glibc 2.39, Intel Xeon @ 2.10 GHz, 1 visible core, about 4 GB RAM (a shared cloud sandbox, not a dedicated machine).
* **Build:** none (interpreted). **Source:** `Python/source/algorithms.py`; the supplied `Python/source/main.py` is unchanged.

```
python tools/run.py --setup                        # supplied launch check
python tools/run.py --check                        # supplied public checks (44 cases + repeated mixed batch)
python tests/student/run_tests.py                  # my full test-suite (132 checks) -> tests/student/test_report.txt
python tools/run.py --input tests/student/cases.jsonl     # my inputs through the supplied launcher
python tools/benchmark_search.py                   # naive / KMP / RK comparison -> tests/student/benchmark_output.txt
```

Conventions used by all parts: a request is one parsed JSON dict; every function builds all its state locally (nothing is shared between
requests); there is no recursion anywhere (deep trees are handled with BFS order and explicit stacks); Python integers are exact, so
costs such as `5·10⁹` or `99999·10⁹` cannot overflow; strings are compared character by character with their ASCII codes (case-sensitive,
space and punctuation are ordinary characters).

## Algorithm explanations

### 1. `lcs` — longest common subsequence

* **State.** `dp[i][j]` = length of an LCS of the prefixes `a[:i]` and `b[:j]` (`i` characters of `a`, `j` characters of `b`).
* **Base cases.** `dp[0][j] = dp[i][0] = 0` (an empty prefix has nothing in common with anything).
* **Transition.** If `a[i-1] == b[j-1]`: `dp[i][j] = dp[i-1][j-1] + 1`; otherwise `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
* **Order.** Rows `i = 1..n`, columns `j = 1..m` increasing, so the three cells a cell depends on are already computed.
* **Correctness.** If the last characters are equal, some optimal subsequence ends with that character (exchange argument), so both
  characters can be consumed. If they differ, at least one of them is unused by any common subsequence, so the answer is the better of the two
  smaller problems.
* **Reconstruction and ties.** Start at `(n, m)`: equal characters → emit the character and move diagonally; otherwise move to the larger
  neighbour (ties: move up, i.e. drop a character of `a`). The emitted characters are reversed. Any optimal sequence is accepted.
* **Time / memory.** `O((n+1)(m+1))` time and `O((n+1)(m+1))` memory for the table of Python ints (at most 10⁶ cells by the limit);
  output is `O(L)`, `L` ≤ min(n, m). Empty input: the table is `1×(m+1)` or `(n+1)×1` and the result is `length=0, sequence=""`.
* **Boundary test.** `a="tea_time", b="team"` → `{"length":4,"sequence":"team"}`. It detects an implementation that treats the problem as
  longest common *substring* (it would answer `tea`, length 3).

### 2. `merge` — ordered adjacent block merging (interval DP)

* **State.** `cost[l][r]` = minimum total cost of merging original blocks `l..r` into one block; `split[l][r]` = the `k` of the last merge
  `[l,k] + [k+1,r]` in an optimal plan.
* **Base cases.** `cost[i][i] = 0`. For `n ≤ 1` the answer is `cost=0, plan=[]` and the tables are not built.
* **Transition.** `cost[l][r] = min over k in [l, r-1] of cost[l][k] + cost[k+1][r] + sum(sizes[l..r])`, where the sum comes from prefix sums.
  The last merge of any plan for `l..r` combines a left part `[l,k]` and a right part `[k+1,r]` and always costs the whole interval sum, so the
  two parts can be optimised independently (optimal substructure).
* **Order.** By increasing interval length: both sub-intervals are strictly shorter, hence ready.
* **Reconstruction and ties.** The `split` entries form a binary tree. An explicit stack outputs it in post-order (left subtree, right subtree, then the
  parent), so every child merge appears before its parent merge and each `[l,k,r]` joins two *currently adjacent* blocks. Ties: the smallest `k`
  (strict `<`). Exactly `n-1` merges are emitted. Any optimal plan is accepted.
* **Time / memory.** `O(n³)` time (about `n³/6` inner steps; about 0.1 s for n = 200), `O(n²)` auxiliary memory (two `n×n` tables) plus `O(n)` prefix sums;
  the output plan has `n-1` triples. `O(1)` for `n ≤ 1`.
* **Boundary test.** `sizes=[2,3,4]` → `cost=14, plan=[[0,0,1],[0,1,2]]` (merging 3 and 4 first costs `7+9=16`). Also `[4,1,4,1,4]` →
  cost 33, equal to an exhaustive search over all merge orders. It detects a "merge the two smallest blocks" greedy, a missing prefix-sum term, or a plan
  that lists the parent before its children.

### 3. `tree` — maximum-weight independent set on a tree

* **State.** For a vertex `v` (children relative to a BFS root): `take[v]` = best weight inside the subtree of `v` if `v` is selected;
  `skip[v]` = best weight in the subtree if `v` is not selected.
* **Base / transition.** A leaf: `take = w[v]`, `skip = 0`. In general `take[v] = w[v] + Σ skip[c]` and `skip[v] = Σ max(take[c], skip[c])` over children `c`.
  The answer is `max(take[root], skip[root])`; the empty set is allowed, so an all-negative tree gives weight 0.
* **Order.** BFS order from the root, processed in reverse: every child is finished before its parent, and no recursion is used (a chain of 10⁵ vertices
  is fine). The code loops over all vertices as potential roots only for robustness; the published input is one connected tree.
* **Correctness.** If `v` is selected none of its children may be, so they contribute `skip`; if not, each child independently picks its better state.
  Subtrees of different children share no edges, so the sums are independent. The optimum does not depend on the root (every root gives the maximum over
  the same set of independent sets).
* **Reconstruction and ties.** Top-down in BFS order with a flag `allowed[v]` (parent not selected). `v` is selected iff `allowed[v]` and `take[v] > skip[v]`
  (ties: skip); selecting `v` sets `allowed[c] = False` for its children. Each vertex occurs once; order is BFS order.
* **Time / memory.** `O(n)` time and `O(n)` auxiliary memory (adjacency lists, parent, BFS order, two DP arrays, flags); output `O(n)`. `n = 0` returns immediately.
* **Boundary test.** `weights=[-1,-2,-3]` on a path → `{"weight":0,"selected":[]}`. It detects forcing a non-empty set or treating an empty subtree as `-∞`.
  `[4,9,6]` on a path → `weight=10, selected=[0,2]`, not `[1]` (9).

### 4a. `naive` — baseline search

* **Invariant.** When the loop reaches start `i`, every occurrence start `< i` is already in the output, in increasing order.
* **Steps.** For `i = 0..n-m`: skip quickly if `text[i] != pattern[0]`, otherwise compare characters left to right; a full match appends `i`.
  Overlaps are kept because the next start is always `i+1`. `m = 0` returns `0..n` (all `n+1` boundaries); `m > n` gives an empty range, so `[]`.
* **Correctness.** Every start in `0..n-m` is tested exactly once and a start is reported iff all `m` characters agree.
* **Time / memory.** `O(n·m + n + 1)` worst case (e.g. text `a^n`, pattern `a^k b`), `O(1)` auxiliary memory, `O(z+1)` output.
* **Boundary test.** `aaaaa / aaa` → `[0,1,2]`; it detects skipping ahead by `m` after a match. `"abc" / ""` → `[0,1,2,3]` detects omitting the final boundary.

### 4b. `kmp` — Knuth–Morris–Pratt

* **State.** `pi[i]` = length of the longest *proper* border (prefix that is also a suffix) of `pattern[:i+1]`; during the scan `k` = length of the longest pattern
  prefix that is a suffix of the text read so far (always `< m` after the fallback).
* **Transition.** On mismatch `k ← pi[k-1]` until `k = 0` or the characters agree; on agreement `k ← k+1`. When `k = m` a match starts at `i-m+1`; then `k ← pi[m-1]`
  (fall back to the longest border), which keeps overlapping matches. Prefix function and scan use the same loop.
* **Order.** `pi` is built left to right using only earlier entries; the text is scanned once left to right.
* **Correctness.** Any pattern prefix that is a suffix of `text[:i+1]` followed by the next character must be a border chain element of the current `k`, so
  following `pi` visits all candidates in decreasing length and loses nothing.
* **Time / memory.** `O(n + m + z + 1)` time (`k` grows by at most 1 per text character and every fallback shrinks it, so fallbacks total `O(n)`; building `pi` is `O(m)`);
  `O(m + 1)` auxiliary memory for `pi`; `O(z+1)` output. The empty pattern returns the `n+1` boundaries before any pattern indexing.
* **Boundary test.** `abababa / aba` → `[0,2,4]`; it detects resetting `k` to 0 after a full match (that would give `[0,4]`).

### 4c. `rk` — exact Rabin–Karp (base 31, modulus 101, ASCII codes)

* **State.** `hash(w) = Σ ord(w[i])·31^(m-1-i) mod 101` (leftmost character has the highest power); `hw` = hash of the current window `text[i:i+m]`.
* **Transition.** `hw ← ((hw − ord(text[i])·31^(m-1))·31 + ord(text[i+m])) mod 101`. Python's `%` returns a non-negative remainder, which is exactly the
  required normalisation of negative values.
* **Verification.** Equal hashes make a window only a *candidate*: the window is compared with the pattern character by character (`text[i:i+m] == pattern`, an
  element-wise string comparison executed in C; no search function is used) before `i` is reported. `m = 0` and `m > n` are handled before any window is formed.
* **Correctness.** Different hashes imply different strings, so no true match is skipped; every reported start passed the verification, so no false match is
  reported even though the modulus 101 produces many collisions.
* **Time / memory.** `O(n + m + c·m)` where `c` is the number of equal-hash windows; since `c ≤ n−m+1` this is `O(n·m + n + m + 1)` in the worst case, i.e. quadratic.
  Linear worst-case time is **not** claimed. `O(m+1)` auxiliary memory (the verification slice) plus `O(z+1)` output. The candidate counts measured below
  are `c = 0`, `c = z` and `c ≈ 1 % of the windows` for the three workloads.
* **Boundary test.** `abdj / ab` → `[0]`. Both `ab` and `dj` have hash 75 (`97·31+98 = 3105 ≡ 75` and `100·31+106 = 3206 ≡ 75` mod 101), so window 2 is a
  candidate that must be rejected; an implementation that reports hash matches without verification returns `[0,2]`.

### 5. `suffix` — suffix array (prefix doubling) and Kasai LCP

*Prefix doubling.*
* **State.** After the round with parameter `k`, `rank[i]` is the rank of suffix `i` among all suffixes compared by their first `2k` characters (equal prefixes share a rank);
  initially `rank[i] = ord(text[i])` (`k = 1` compares first characters).
* **Transition.** Sort the indices by the integer key `rank[i]·B + (rank[i+k] + 1 if i+k < n else 0)` with `B = max(n,128)+2`. A suffix that has ended gets second
  key 0, so a shorter suffix sorts before a longer one with the same prefix. New ranks are assigned by comparing the keys of consecutive entries. Then `k ← 2k`; stop
  when all ranks are distinct (`rank_max = n-1`).
* **Correctness.** Sorting by `(rank of first k chars, rank of next k chars)` is sorting by the first `2k` characters; once ranks are distinct the order is the suffix order.
  The output `sa` has exactly the `n` non-empty suffixes (no sentinel, no empty suffix); suffix strings are never materialised.
* **Time / memory.** At most `⌈log₂ n⌉ + 1` rounds, each a comparison sort (`list.sort` with a precomputed key list: Timsort, stable) → `O(n log n)` per round and
  `O(n log² n)` total; `O(n)` memory for `sa`, `rank`, `key`, `new`. Measured: 0.14 s for `a^50000` (the deepest case, 16 rounds). `n = 0` returns three empty values at once.

*Kasai.*
* **State.** `lcp[r]` is the longest common prefix of `sa[r-1]` and `sa[r]`; `lcp[0] = 0`. Suffixes are processed in text order `i = 0..n-1` and `h` carries the current match length.
* **Transition.** For `rank[i] > 0` extend `h` while the characters of suffix `i` and of its predecessor in `sa` agree, store `lcp[rank[i]] = h`, then `h ← max(h-1, 0)`. For
  `rank[i] = 0` set `h = 0`.
* **Correctness / reuse.** If suffix `i` shares `h > 0` characters with its predecessor, then suffix `i+1` shares at least `h-1` with *its* predecessor, so the comparison restarts at `h-1` instead of 0.
* **Time / memory.** `h` is increased at most `2n` times in total (it grows by at most `n` and drops by at most 1 per step), so Kasai is `O(n)` time and `O(n)` memory.

*Longest repeat.* The longest substring that occurs at two different starts equals `max(lcp)`: the longest common prefix of any two suffixes equals the minimum of the
adjacent `lcp` values between them, so the maximum over all pairs is attained by an adjacent pair. `repeated = text[sa[pos] : sa[pos] + max(lcp)]` at the first position with the maximum; the two occurrences may overlap; `max(lcp) = 0` gives `""`.

* **Boundary test.** `aaaa` → `sa=[3,2,1,0], lcp=[0,1,2,3], repeated="aaa"` (occurrences at 0 and 1 overlap). It detects forbidding overlaps or sorting a longer suffix before its own proper suffix.
  `banana` → `sa=[5,3,1,0,4,2], lcp=[0,1,3,0,0,2], repeated="ana"`.

### 6. `aho` — Aho–Corasick dictionary counting

* **Construction (once per request).** A trie whose nodes hold `dict` children (memory proportional to the total pattern length `L`, not `95·S`). `term[idx]` is the terminal
  node of dictionary position `idx`; **duplicate patterns end in the same node** and therefore later receive equal counts. Failure links are computed by BFS: `fail[v]` is the node of the longest proper suffix
  of the string of `v` that is also in the trie (`fail` of depth-1 nodes is the root). Time `O(L + p)` expected (hash maps; the failure computation is amortised per pattern).
* **Why suffix patterns are counted.** Being in state `s` after reading a character means the string of `s` *and every string on the failure chain of `s`* ends here. So a position with state `s` is one
  occurrence of every pattern whose terminal node lies on the failure chain of `s` — in `sheshe` the state `she` also gives an occurrence of `he`.
* **Counting without per-match work.** The failure links form a tree rooted at the root. For a text, count how many times each state was visited, and then the count of pattern `t` is the number of visits inside
  the **failure subtree** of `term[t]`. An Euler tour (`tin`, `tout`, built with an explicit stack) turns this into a range sum: increment `visit[tin[s]+1]` once per text character, take prefix sums with
  `itertools.accumulate` (executed in C), and read `pref[tout[v]] − pref[tin[v]]`. This is the "visit propagation along failure links" aggregation: dense matches (`a^1 … a^440` in texts `a^2000`) never create one record per occurrence.
* **Independent texts.** `visit` and the current state `s` are created inside the loop for every text, so nothing leaks from one text (or one request) to the next; an empty text has all counts 0 because `visit` stays 0.
* **Edge cases.** No patterns → one empty row per text; no texts → `[]`; rows follow the order of `texts`, columns the order of `patterns`.
* **Time / memory.** Per text: `O(|text|)` amortised automaton steps (the depth grows by at most 1 per character, every failure step lowers it) plus `O(S)` for one prefix-sum pass (C speed) plus `O(p)` for reading counts.
  Auxiliary memory `O(S + p)` (dict nodes, `fail`, `tin`, `tout`, `visit`, `term`); output `O(q·(p+1) + 1)`. This is a dict-based variant of the contract's `O(L + 95·S + p)` construction: it follows failure
  links at query time instead of precomputing a full 95-letter transition table.
* **Boundary test.** `patterns=["he","she","he"]`, `texts=["sheshe","sheshe",""]` → `[[2,2,2],[2,2,2],[0,0,0]]`: it detects missing suffix-pattern counts (`he` inside `she`), a duplicate pattern that is
  counted only once, and counters that are not reset between texts.

## Own tests

All commands are run from the repository root. Fixture files are in `tests/student/`: `cases.jsonl` (inputs) and `actual_outputs.jsonl` (the matching outputs, line *i* belongs to line *i*).

| Command | Input or fixture path | Expected result | Actual result / log | What it checks |
|---------|-----------------------|-----------------|---------------------|----------------|
| `python tests/student/run_tests.py` | `tests/student/run_tests.py`, `checkers.py` | exit code 0, every check PASS | **132 passed, 0 failed** (`tests/student/test_report.txt`) | the whole suite below |
| same (group "spec examples") | the mixed 13-request batch stored in `cases.jsonl` | the eight examples of the contracts | `lcs → {"length":4,"sequence":"team"}`; `merge → {"cost":14,"plan":[[0,0,1],[0,1,2]]}`; `tree → {"weight":10,"selected":[0,2]}`; `naive → [0,1,2]`; `kmp → [0,2,4]`; `rk → [0]`; `suffix → sa [5,3,1,0,4,2], lcp [0,1,3,0,0,2], "ana"`; `aho → [[2,2,2],[2,2,2],[0,0,0]]` | exact match with the published examples |
| same (hand-justified) | inline in `run_tests.py` | expected values derived by hand (e.g. `[1,100,1]` merge = 203; `[10,6,6,6]` star = 18; 5-vertex chain of 10⁹ = 3·10⁹) | all PASS | empty inputs, `n=0/1`, empty pattern, pattern longer than text, negative weights, totals beyond 32 bits, case sensitivity, spaces/punctuation, duplicates, empty texts, no patterns, no texts |
| same (checker sanity) | `checkers.py` | accepts alternative optima; rejects invalid witnesses | PASS (adjacent vertices selected, wrong weight and suboptimal weight are rejected) | that the validators can fail |
| same (randomised) | seed 2026, 300 instances | all eight commands agree with brute-force oracles | PASS (`300 random small instances …`) | LCS vs subsequence enumeration, merge vs all merge orders, tree vs all subsets, searches vs `str.find`, suffix vs sorted slices, Aho vs per-pattern counting |
| same (large) | generated inside `run_tests.py` | limits of the contracts, answers verified independently | `lcs` 1000×1000 0.07–0.08 s (vs rolling-row DP); `merge` n=200 0.09–0.10 s (vs Knuth O(n²)); `tree` n=10⁵ chain / star / random 0.12–0.24 s (vs independent DPs); `kmp` 200000×100000 0.04 s; `rk` 10000×2000 all-match < 0.01 s; `suffix` n=50000 random / `a^n` / periodic 0.10 / 0.14 / 0.14 s (random one checked against sorted-suffix oracle and every lcp); `aho` 440 dense patterns × 100 texts 0.03 s (closed form `L−k+1`), 10⁴ random patterns × 100 texts 0.23 s | scale, deep chains, dense matches, overflow |
| same (state reset) | mixed batch of all 8 commands + empty cases | outputs identical on every repetition | PASS (3 repeats in one process; stdin/stdout run with the batch twice) | no state leaks between consecutive requests |
| `python tools/run.py --check` | `tests/public.json` (supplied, 44 cases) | every public case passes, then the state-reset run of two complete batches in one process | **PASS public 1 … PASS public 44 and PASS state reset** (run in the AI's sandbox with the supplied `main.py`, `run.py`, `public_validate.py`; `--setup` also PASS) | supplied public checks and request-state reset |

(Timings in this table are single runs including a JSON round-trip of the request; they vary by about ±30 % between runs on this shared machine.)

## Search comparison

**Setup.** The same input is given to naive, KMP and RK for every row. Correctness is verified *before* timing: the outputs of naive, KMP, RK and an additional RK variant are required to be identical to a `str.find`-based oracle (checked inside the script, which aborts otherwise).
Sizes are in the common domain (`n, m ≤ 3000`): `n ∈ {1000, 2000, 3000}`. Random case A: text uniform over `{a,b}` (`random.Random(4000+n)`), pattern of length 10 uniform over `{a,b}`. Repetitive cases are deterministic: B = text `a^n`, pattern `a^(m-1)b` (no match, worst case for naive), C = text `a^n`, pattern `a^m`
(every window matches), `m = n//3`.
**Timing scope.** `time.perf_counter()` around the algorithm function on an already-parsed request dict; no JSON parsing, no printing; no compilation exists in Python. Warm-up: one untimed call per row, then each of the 5 runs repeats the call enough times for the batch to last ≥ 50 ms and reports the mean per call. Unit: **milliseconds per call**. Command: `python tools/benchmark_search.py`
(raw data in `tests/student/benchmark_results.json`, full output in `tests/student/benchmark_output.txt`). Garbage collection is at its default.

The fourth algorithm line ("RK char-loop verify") is **informational only**: it is the same rolling hash but verifies each candidate with an interpreted character-by-character loop; it is not the submitted function.

| Case | n | m | Seed/generator | Algorithm | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Median | Correct outputs checked |
|---|--:|--:|---|---|--:|--:|--:|--:|--:|--:|---|
| A random | 1000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | naive | 0.082 | 0.083 | 0.085 | 0.083 | 0.083 | **0.083** | 1 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 1000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | KMP | 0.077 | 0.078 | 0.078 | 0.079 | 0.080 | **0.078** | 1 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 1000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | RK (submitted, slice verify) | 0.130 | 0.127 | 0.132 | 0.132 | 0.134 | **0.132** | 1 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 1000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | RK char-loop verify (informational) | 0.135 | 0.131 | 0.132 | 0.132 | 0.130 | **0.132** | 1 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | naive | 10.322 | 10.365 | 10.345 | 10.361 | 10.338 | **10.345** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | KMP | 0.130 | 0.131 | 0.132 | 0.127 | 0.130 | **0.130** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | RK (submitted, slice verify) | 0.125 | 0.125 | 0.125 | 0.125 | 0.126 | **0.125** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | RK char-loop verify (informational) | 0.123 | 0.123 | 0.122 | 0.122 | 0.124 | **0.123** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | naive | 10.348 | 10.287 | 10.357 | 10.567 | 10.433 | **10.357** | 668 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | KMP | 0.164 | 0.194 | 0.145 | 0.107 | 0.108 | **0.145** | 668 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | RK (submitted, slice verify) | 0.154 | 0.178 | 0.185 | 0.184 | 0.184 | **0.184** | 668 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 1000 | 333 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | RK char-loop verify (informational) | 9.975 | 9.906 | 9.875 | 9.840 | 9.867 | **9.875** | 668 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 2000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | naive | 0.159 | 0.158 | 0.162 | 0.165 | 0.162 | **0.162** | 2 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 2000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | KMP | 0.155 | 0.155 | 0.158 | 0.159 | 0.160 | **0.158** | 2 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 2000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | RK (submitted, slice verify) | 0.217 | 0.271 | 0.271 | 0.270 | 0.271 | **0.271** | 2 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 2000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | RK char-loop verify (informational) | 0.266 | 0.265 | 0.256 | 0.254 | 0.265 | **0.265** | 2 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | naive | 46.445 | 44.869 | 43.854 | 44.123 | 44.137 | **44.137** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | KMP | 0.269 | 0.269 | 0.269 | 0.268 | 0.276 | **0.269** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | RK (submitted, slice verify) | 0.255 | 0.255 | 0.254 | 0.255 | 0.254 | **0.255** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | RK char-loop verify (informational) | 0.255 | 0.249 | 0.249 | 0.250 | 0.249 | **0.249** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | naive | 44.970 | 45.137 | 44.766 | 45.127 | 44.906 | **44.970** | 1335 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | KMP | 0.255 | 0.257 | 0.261 | 0.254 | 0.253 | **0.255** | 1335 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | RK (submitted, slice verify) | 0.394 | 0.393 | 0.398 | 0.392 | 0.394 | **0.394** | 1335 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 2000 | 666 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | RK char-loop verify (informational) | 44.786 | 44.979 | 47.108 | 45.624 | 45.289 | **45.289** | 1335 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 3000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | naive | 0.262 | 0.261 | 0.256 | 0.259 | 0.260 | **0.260** | 4 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 3000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | KMP | 0.230 | 0.229 | 0.231 | 0.235 | 0.232 | **0.231** | 4 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 3000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | RK (submitted, slice verify) | 0.342 | 0.327 | 0.378 | 0.407 | 0.397 | **0.378** | 4 matches; naive=KMP=RK=char-loop=str.find oracle |
| A random | 3000 | 10 | seed 4000+n; random.Random; text uniform over {a,b}; pattern: 10 uniform random {a,b} | RK char-loop verify (informational) | 0.391 | 0.386 | 0.318 | 0.314 | 0.400 | **0.386** | 4 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | naive | 80.716 | 80.220 | 80.549 | 80.653 | 89.794 | **80.653** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | KMP | 0.320 | 0.320 | 0.321 | 0.320 | 0.471 | **0.320** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | RK (submitted, slice verify) | 0.379 | 0.385 | 0.384 | 0.376 | 0.380 | **0.380** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| B repetitive, no match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^(m-1)b, m=n//3 | RK char-loop verify (informational) | 0.381 | 0.381 | 0.388 | 0.380 | 0.370 | **0.381** | 0 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | naive | 102.506 | 102.591 | 105.413 | 106.517 | 107.069 | **105.413** | 2001 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | KMP | 0.388 | 0.387 | 0.390 | 0.389 | 0.393 | **0.389** | 2001 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | RK (submitted, slice verify) | 0.660 | 0.672 | 0.662 | 0.667 | 0.676 | **0.667** | 2001 matches; naive=KMP=RK=char-loop=str.find oracle |
| C repetitive, all match | 3000 | 1000 | deterministic (no seed): text a^n, pattern a^m, m=n//3 | RK char-loop verify (informational) | 105.310 | 106.578 | 95.124 | 82.545 | 85.809 | **95.124** | 2001 matches; naive=KMP=RK=char-loop=str.find oracle |

Equal-hash windows `c` for RK: case A: 9, 15, 29 (n = 1000, 2000, 3000); case B: 0, 0, 0; case C: 668, 1335, 2001 (every window).

**Observations (measured, not a proof of complexity).**
* On the repetitive inputs naive grows about quadratically with the input (n = 1000 → 3000 with `m = n/3`: 10.3 → 80.7 ms in case B and 10.4 → 105.4 ms in case C), while KMP stays at 0.13 → 0.32 ms (B) and 0.15 → 0.39 ms (C): about 250× (B) and 270× (C) faster at n = 3000.
* On random binary text with a short pattern the three algorithms are within a small factor of each other (n = 3000: naive 0.26 ms, KMP 0.23 ms, RK 0.38 ms); naive almost never compares more than one or two characters, and RK pays for the extra hash arithmetic on every window.
* RK is as fast as KMP in case B because no window hashes like `a^(m-1)b` (`c = 0`): the rolling hash alone rejects everything. In case C every window is a candidate (`c = n−m+1`). The **submitted** RK stays fast (0.67 ms at n = 3000) because the verification compares the whole window with one C-level
  string comparison, whereas the char-loop variant takes 95.1 ms at n = 3000, matching naive (105.4 ms): this is the `c·m` term of `O(n + m + c·m)` made visible. The measured speed of the submitted RK therefore reflects the Python implementation of the comparison, not a better asymptotic bound.
* The deliberately small modulus 101 produces many false candidates on random text (`c = 29` of 2991 windows for `m = 10`, about 1 %), each costing one rejected comparison. This is a property of this very small modulus chosen for the assignment; a large modulus would make false candidates rare, and nothing here should be generalised to production hash designs.
* The `abdj / ab` collision case (hash 75 for both `ab` and `dj`) is included as a correctness test (`rk abdj/ab` → `[0]`).

## Sources and AI assistance

* **Sources:** the assignment text 
* **AI tool:** Help with understanding the code
* **My own verification:** I verify that i completed this assignment by myself