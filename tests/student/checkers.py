"""Validators for non-unique answers + independent brute-force oracles (different methods from the solution)."""
import itertools
import re


class Invalid(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise Invalid(msg)


def is_subsequence(s, t):
    it = iter(t)
    return all(c in it for c in s)


# ------------------------------------------------------------------ LCS
def lcs_bruteforce_len(a, b):
    """Try every subsequence of the shorter string (tiny inputs only)."""
    if len(a) > len(b):
        a, b = b, a
    for L in range(len(a), -1, -1):
        for idx in itertools.combinations(range(len(a)), L):
            if is_subsequence("".join(a[i] for i in idx), b):
                return L
    return 0


def check_lcs(a, b, out, expected_len=None):
    need(isinstance(out["length"], int) and not isinstance(out["length"], bool), "length must be an int")
    s = out["sequence"]
    need(len(s) == out["length"], "length != len(sequence)")
    need(is_subsequence(s, a) and is_subsequence(s, b), "sequence is not a common subsequence")
    if expected_len is not None:
        need(out["length"] == expected_len, f"length {out['length']} != optimum {expected_len}")


# ---------------------------------------------------------------- merge
def merge_bruteforce(sizes):
    """Minimum over ALL orders of adjacent merges of the block list (n <= 7)."""
    best = {}

    def go(blocks):
        if len(blocks) <= 1:
            return 0
        key = tuple(blocks)
        if key in best:
            return best[key]
        res = None
        for i in range(len(blocks) - 1):
            nb = blocks[:i] + [blocks[i] + blocks[i + 1]] + blocks[i + 2:]
            c = blocks[i] + blocks[i + 1] + go(nb)
            if res is None or c < res:
                res = c
        best[key] = res
        return res
    return go(list(sizes))


def check_merge(sizes, out, expected=None):
    n = len(sizes)
    plan = out["plan"]
    need(len(plan) == max(n - 1, 0), "plan must contain n-1 merges")
    blocks = [(i, i) for i in range(n)]               # current blocks as original intervals, in order
    total = 0
    for l, k, r in plan:
        pos = None
        for i in range(len(blocks) - 1):
            if blocks[i] == (l, k) and blocks[i + 1] == (k + 1, r):
                pos = i
                break
        need(pos is not None, f"merge [{l},{k},{r}] does not combine two adjacent current blocks")
        total += sum(sizes[l:r + 1])
        blocks[pos:pos + 2] = [(l, r)]
    need(len(blocks) <= 1, "plan leaves several blocks")
    need(total == out["cost"], f"cost {out['cost']} != cost of the plan {total}")
    if expected is not None:
        need(out["cost"] == expected, f"cost {out['cost']} != optimum {expected}")


# ----------------------------------------------------------------- tree
def tree_bruteforce(n, w, edges):
    best = 0
    for mask in range(1 << n):
        ok = all(not ((mask >> u) & 1 and (mask >> v) & 1) for u, v in edges)
        if ok:
            best = max(best, sum(w[i] for i in range(n) if mask >> i & 1))
    return best


def check_tree(n, w, edges, out, expected=None):
    sel = out["selected"]
    need(len(set(sel)) == len(sel), "vertex selected twice")
    need(all(0 <= v < n for v in sel), "vertex id out of range")
    s = set(sel)
    need(all(not (u in s and v in s) for u, v in edges), "two adjacent vertices selected")
    need(sum(w[v] for v in sel) == out["weight"], "weight != sum of selected weights")
    if expected is not None:
        need(out["weight"] == expected, f"weight {out['weight']} != optimum {expected}")


# ---------------------------------------------------------- exact search
def search_oracle(text, pat):
    """Overlapping occurrences via str.find (an oracle only; the solution may not use it)."""
    n, m = len(text), len(pat)
    if m == 0:
        return list(range(n + 1))
    out, i = [], text.find(pat)
    while i != -1:
        out.append(i)
        i = text.find(pat, i + 1)
    return out


# --------------------------------------------------------------- suffix
def suffix_oracle(text):
    n = len(text)
    sa = sorted(range(n), key=lambda i: text[i:])
    lcp = [0] * n
    for r in range(1, n):
        a, b = text[sa[r - 1]:], text[sa[r]:]
        h = 0
        while h < len(a) and h < len(b) and a[h] == b[h]:
            h += 1
        lcp[r] = h
    return sa, lcp


def longest_repeat_len(text):
    """Longest length L such that some substring of length L starts at two distinct positions."""
    n = len(text)
    for L in range(n - 1, 0, -1):
        seen = set()
        for i in range(n - L + 1):
            sub = text[i:i + L]
            if sub in seen:
                return L
            seen.add(sub)
    return 0


def check_suffix(text, out, ref=None):
    n = len(text)
    sa, lcp, rep = out["sa"], out["lcp"], out["repeated"]
    need(sorted(sa) == list(range(n)), "sa is not a permutation of 0..n-1")
    need(len(lcp) == n, "lcp length")
    if ref:
        need(sa == ref[0], "sa differs from sorted-suffix oracle")
        need(lcp == ref[1], "lcp differs from oracle")
        need(len(rep) == longest_repeat_len(text), "repeated has not the longest possible length")
    if rep:
        need(len(re.findall("(?=" + re.escape(rep) + ")", text)) >= 2, "repeated does not occur twice")
    else:
        need(n == 0 or (max(lcp) == 0), "repeated empty but a repeat exists")


# ------------------------------------------------------------------ aho
def aho_oracle(patterns, texts):
    return [[len(search_oracle(t, p)) for p in patterns] for t in texts]


def longest_repeat_len_fast(text):
    """Binary search on L (a repeated substring of length L implies one of every shorter length)."""
    lo, hi = 0, len(text) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        seen = set()
        found = False
        for i in range(len(text) - mid + 1):
            sub = text[i:i + mid]
            if sub in seen:
                found = True
                break
            seen.add(sub)
        if found:
            lo = mid
        else:
            hi = mid - 1
    return lo


def lcs_len_rolling(a, b):
    """Independent LCS length: two rolling rows, built differently from the solution's full table."""
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def merge_knuth(sizes):
    """Independent optimum via Knuth's optimisation, O(n^2): opt[l][r-1] <= opt[l][r] <= opt[l+1][r]."""
    n = len(sizes)
    if n <= 1:
        return 0
    pre = [0]
    for s in sizes:
        pre.append(pre[-1] + s)
    cost = [[0] * n for _ in range(n)]
    opt = [[0] * n for _ in range(n)]
    for i in range(n):
        opt[i][i] = i
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            best, bk = None, l
            for k in range(opt[l][r - 1], min(opt[l + 1][r], r - 1) + 1):
                c = cost[l][k] + cost[k + 1][r]
                if best is None or c < best:
                    best, bk = c, k
            cost[l][r] = best + pre[r + 1] - pre[l]
            opt[l][r] = bk
    return cost[0][n - 1]
