"""Assignment 4: DP and string algorithms (Python 3.12).

Every public function takes the parsed JSON request (a dict) and returns the result
dict. All state is local to a call, nothing is shared between requests, and no
algorithm is recursive (deep trees and long chains are safe).
Strings contain ASCII codes 32..126.
"""
from itertools import accumulate


# ================================================================ 1. LCS
def lcs(request):
    a, b = request["a"], request["b"]
    n, m = len(a), len(b)
    # dp[i][j] = LCS length of the prefixes a[:i] and b[:j]; row/column 0 are the empty prefix.
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        row, prev, ai = dp[i], dp[i - 1], a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                row[j] = prev[j - 1] + 1
            else:
                x, y = prev[j], row[j - 1]
                row[j] = x if x >= y else y
    # Reconstruction: walk back from (n, m).
    out = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    out.reverse()
    return {"length": dp[n][m], "sequence": "".join(out)}


# ======================================================= 2. interval merge
def merge(request):
    sizes = request["sizes"]
    n = len(sizes)
    if n <= 1:
        return {"cost": 0, "plan": []}
    pre = [0] * (n + 1)
    for i, s in enumerate(sizes):
        pre[i + 1] = pre[i] + s
    # cost[l][r] = cheapest way to merge blocks l..r into one; split[l][r] = last split k
    cost = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for l in range(0, n - length + 1):
            r = l + length - 1
            best = None
            bk = l
            cl = cost[l]
            for k in range(l, r):
                c = cl[k] + cost[k + 1][r]
                if best is None or c < best:
                    best, bk = c, k
            cost[l][r] = best + pre[r + 1] - pre[l]
            split[l][r] = bk
    # Chronological plan = post-order of the split tree (children before parent), iteratively.
    plan = []
    stack = [(0, n - 1, False)]
    while stack:
        l, r, done = stack.pop()
        if l == r:
            continue
        k = split[l][r]
        if done:
            plan.append([l, k, r])
        else:
            stack.append((l, r, True))
            stack.append((k + 1, r, False))
            stack.append((l, k, False))        # popped first -> left child planned first
    return {"cost": cost[0][n - 1], "plan": plan}


# ===================================================== 3. tree independent set
def tree(request):
    n = request["n"]
    w = request["weights"]
    if n == 0:
        return {"weight": 0, "selected": []}
    adj = [[] for _ in range(n)]
    for u, v in request["edges"]:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    seen = [False] * n
    order = []
    roots = []
    for s in range(n):                      # a tree is connected; the loop only adds robustness
        if seen[s]:
            continue
        roots.append(s)
        seen[s] = True
        queue = [s]
        for x in queue:                     # BFS order: parents before children
            order.append(x)
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True
                    parent[y] = x
                    queue.append(y)
    take = [0] * n                          # best weight in subtree if v is selected
    skip = [0] * n                          # best weight in subtree if v is not selected
    for v in reversed(order):               # children before parents
        take[v] += w[v]
        p = parent[v]
        if p != -1:
            take[p] += skip[v]
            skip[p] += take[v] if take[v] > skip[v] else skip[v]
    allowed = [True] * n                    # may v be selected? (parent not selected)
    selected = []
    total = 0
    for v in order:
        if allowed[v] and take[v] > skip[v]:
            selected.append(v)
            for y in adj[v]:
                if parent[y] == v:
                    allowed[y] = False
        if parent[v] == -1:
            total += max(take[v], skip[v])
    return {"weight": total, "selected": selected}


# ================================================== 4. exact search (3 ways)
def naive(request):
    text, pat = request["text"], request["pattern"]
    n, m = len(text), len(pat)
    if m == 0:
        return {"positions": list(range(n + 1))}
    out = []
    first = pat[0]
    for i in range(n - m + 1):
        if text[i] != first:
            continue
        j = 1
        while j < m and text[i + j] == pat[j]:
            j += 1
        if j == m:
            out.append(i)
    return {"positions": out}


def kmp(request):
    text, pat = request["text"], request["pattern"]
    n, m = len(text), len(pat)
    if m == 0:
        return {"positions": list(range(n + 1))}
    pi = [0] * m                            # pi[i] = longest proper border of pat[:i+1]
    k = 0
    for i in range(1, m):
        c = pat[i]
        while k and pat[k] != c:
            k = pi[k - 1]
        if pat[k] == c:
            k += 1
        pi[i] = k
    out = []
    k = 0
    for i in range(n):
        c = text[i]
        while k and pat[k] != c:
            k = pi[k - 1]
        if pat[k] == c:
            k += 1
        if k == m:
            out.append(i - m + 1)
            k = pi[k - 1]                   # fall back so overlapping matches are kept
    return {"positions": out}


RK_BASE, RK_MOD = 31, 101


def rk(request):
    text, pat = request["text"], request["pattern"]
    n, m = len(text), len(pat)
    if m == 0:
        return {"positions": list(range(n + 1))}
    if m > n:
        return {"positions": []}
    hp = hw = 0
    for i in range(m):                      # leftmost character gets the highest power
        hp = (hp * RK_BASE + ord(pat[i])) % RK_MOD
        hw = (hw * RK_BASE + ord(text[i])) % RK_MOD
    high = pow(RK_BASE, m - 1, RK_MOD)
    out = []
    for i in range(n - m + 1):
        # Equal hashes are only candidates: every candidate is verified character by character.
        if hw == hp and text[i:i + m] == pat:
            out.append(i)
        if i + m < n:
            hw = ((hw - ord(text[i]) * high) * RK_BASE + ord(text[i + m])) % RK_MOD   # Python % is >= 0
    return {"positions": out}


# ================================================ 5. suffix array + Kasai
def suffix(request):
    text = request["text"]
    n = len(text)
    if n == 0:
        return {"sa": [], "lcp": [], "repeated": ""}
    # Prefix doubling: rank[i] orders suffixes by their first k characters.
    rank = [ord(c) for c in text]
    sa = list(range(n))
    base = max(n, 128) + 2
    k = 1
    while True:
        key = [rank[i] * base + (rank[i + k] + 1 if i + k < n else 0) for i in range(n)]
        sa.sort(key=key.__getitem__)
        new = [0] * n
        r = 0
        for idx in range(1, n):
            if key[sa[idx]] != key[sa[idx - 1]]:
                r += 1
            new[sa[idx]] = r
        rank = new
        if r == n - 1 or k >= n:
            break
        k <<= 1
    # Kasai: lcp[rank[i]] = common prefix of suffix i with its predecessor in sa.
    lcp = [0] * n
    h = 0
    for i in range(n):
        ri = rank[i]
        if ri > 0:
            j = sa[ri - 1]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            lcp[ri] = h
            if h:
                h -= 1
        else:
            h = 0
    best = max(lcp)
    repeated = ""
    if best:
        pos = lcp.index(best)
        repeated = text[sa[pos]:sa[pos] + best]
    return {"sa": sa, "lcp": lcp, "repeated": repeated}


# ================================================== 6. Aho-Corasick
def aho(request):
    patterns, texts = request["patterns"], request["texts"]
    p = len(patterns)
    if not texts:
        return {"counts": []}
    if p == 0:
        return {"counts": [[] for _ in texts]}
    # Trie (dict children, so memory is proportional to total pattern length).
    child = [{}]
    term = [0] * p                          # terminal state of every dictionary position
    for idx, pat in enumerate(patterns):
        s = 0
        for c in pat:
            nxt = child[s].get(c)
            if nxt is None:
                nxt = len(child)
                child[s][c] = nxt
                child.append({})
            s = nxt
        term[idx] = s                       # duplicates share one terminal state
    S = len(child)
    fail = [0] * S
    bfs = []
    for c, v in child[0].items():
        bfs.append(v)
    for u in bfs:                           # BFS: failure link of a node = longest proper suffix in the trie
        for c, v in child[u].items():
            f = fail[u]
            while f and c not in child[f]:
                f = fail[f]
            g = child[f].get(c, 0)
            fail[v] = g if g != v else 0
            bfs.append(v)
    # Failure tree (parent of v is fail[v]) -> Euler tour so that "visits inside the
    # failure subtree of a state" becomes a range sum, computed with one prefix-sum pass.
    kids = [[] for _ in range(S)]
    for v in range(1, S):
        kids[fail[v]].append(v)
    tin = [0] * S
    tout = [0] * S
    t = 0
    stack = [(0, False)]
    while stack:
        v, done = stack.pop()
        if done:
            tout[v] = t
            continue
        tin[v] = t
        t += 1
        stack.append((v, True))
        for c in kids[v]:
            stack.append((c, False))
    counts = []
    for text in texts:                      # independent texts: fresh counters for each
        visit = [0] * (S + 1)
        s = 0
        for c in text:
            while s and c not in child[s]:
                s = fail[s]
            s = child[s].get(c, 0)
            visit[tin[s] + 1] += 1
        pref = list(accumulate(visit))      # pref[x] = visits with tin < x
        counts.append([pref[tout[v]] - pref[tin[v]] for v in term])
    return {"counts": counts}