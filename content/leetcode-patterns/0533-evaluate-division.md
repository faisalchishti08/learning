---
card: leetcode-patterns
gi: 533
slug: evaluate-division
title: Evaluate Division
---

## 1. What it is

You are given equations like `a / b = 2.0` as pairs `["a","b"]` with values, and a list of queries like `a / c`. Using only the given equations (and their implied inverses and chains), evaluate each query, or return `-1.0` if the query cannot be determined. Example: equations `[["a","b"],["b","c"]]` with values `[2.0, 3.0]`, query `["a","c"]` → `6.0` (since `a/b=2.0` and `b/c=3.0` chain to `a/c=6.0`).

## 2. Why & when

This is [union-find](0524-union-find-template-disjoint-sets-with-union-by-rank-path-co.md), but with a twist: plain union-find only tracks "same group or not." Here you also need the *ratio* between any two variables in the same group — so each parent pointer must carry a **weight**, the multiplicative factor from a node to its parent. This is called weighted union-find. Constraints: up to 20 variables, up to 20 equations and queries.

## 3. Core concept

**Key idea:** treat each variable as a union-find node, but store `weight[x]` = the ratio `x / parent[x]`. `find(x)` follows parent pointers to the representative while multiplying weights along the way, giving `x / representative`. Two variables `a` and `c` in the same group can answer `a / c` as `(a / representative) / (c / representative) = weight[a] / weight[c]`.

**Steps:**
1. For each equation `a / b = v`: if `a` and `b` are new, add them with `parent[a]=a, weight[a]=1` (and same for `b`). Find the representatives of `a` and `b`, tracking the accumulated weight to each (`weightToRootA`, `weightToRootB`) along the way.
2. Attach `rootA` under `rootB`: `parent[rootA] = rootB`, and set `weight[rootA] = v * weightToRootB / weightToRootA` — the ratio that keeps every existing relationship inside `a`'s old group consistent with `b`'s group.
3. For each query `a / b`: if either variable was never seen, return `-1.0`. Otherwise find both representatives with accumulated weights; if they differ, the variables are in different groups (unconnected), return `-1.0`. If they match, return `weightToRootA / weightToRootB`.

**Why `find` must return the accumulated ratio, not just the representative:** the whole point of a query is a number, not a boolean. Path compression still applies, but every compressed pointer must also carry the correct combined weight, or the ratio would be lost.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a/b=2.0 and b/c=3.0 chain through node b, giving a/c=6.0">
  <g font-family="sans-serif" font-size="13">
    <circle cx="120" cy="80" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="120" y="85" fill="#e6edf3" text-anchor="middle">a</text>
    <circle cx="320" cy="80" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="320" y="85" fill="#e6edf3" text-anchor="middle">b</text>
    <circle cx="520" cy="80" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="520" y="85" fill="#e6edf3" text-anchor="middle">c</text>
    <line x1="138" y1="80" x2="302" y2="80" stroke="#8b949e"/>
    <text x="230" y="65" fill="#79c0ff" text-anchor="middle">a/b = 2.0</text>
    <line x1="338" y1="80" x2="502" y2="80" stroke="#8b949e"/>
    <text x="430" y="65" fill="#79c0ff" text-anchor="middle">b/c = 3.0</text>
    <text x="320" y="140" fill="#3fb950" text-anchor="middle">query a/c: chain 2.0 * 3.0 = 6.0</text>
  </g>
</svg>

`a/c` chains through `b`: multiply the ratios along the connecting path, `2.0 * 3.0 = 6.0`.

## 5. Runnable example

**Level 1 — Brute force.** Build a weighted graph (each equation is an edge in both directions, with the ratio and its inverse) and run depth-first search per query, multiplying edge weights along the path. O(q · (V + E)) for q queries.

**KEY INSIGHT:** weighted union-find answers each query in near O(1) after an O(V + E) setup, by storing the accumulated ratio on every parent pointer instead of re-walking a graph per query.

**Level 2 — Optimal.** Weighted union-find with path compression, O((E + q) · α(V)).

**Level 3 — Hardened.** Handles queries with a variable that never appeared in any equation (`-1.0`), and queries between two variables in different groups (`-1.0`).

```java
// EvaluateDivision.java
import java.util.*;

public class EvaluateDivision {

    static Map<String, String> parent = new HashMap<>();
    static Map<String, Double> weight = new HashMap<>();

    static void makeSetIfAbsent(String x) {
        if (!parent.containsKey(x)) {
            parent.put(x, x);
            weight.put(x, 1.0);
        }
    }

    // returns [representative, ratio of x to representative]
    static Object[] find(String x) {
        if (parent.get(x).equals(x)) {
            return new Object[]{x, 1.0};
        }
        Object[] rootResult = find(parent.get(x));
        String root = (String) rootResult[0];
        double ratioParentToRoot = (double) rootResult[1];
        double newRatio = weight.get(x) * ratioParentToRoot;
        parent.put(x, root);       // path compression
        weight.put(x, newRatio);   // update weight to point straight at root
        return new Object[]{root, newRatio};
    }

    static void union(String a, String b, double value) {
        makeSetIfAbsent(a);
        makeSetIfAbsent(b);
        Object[] ra = find(a);
        Object[] rb = find(b);
        String rootA = (String) ra[0], rootB = (String) rb[0];
        double weightToRootA = (double) ra[1], weightToRootB = (double) rb[1];
        if (rootA.equals(rootB)) return;

        parent.put(rootA, rootB);
        // a/rootA=weightToRootA, b/rootB=weightToRootB, a/b=value
        // rootA/rootB = (a/weightToRootA) / (b/weightToRootB) / value ... derived directly:
        weight.put(rootA, value * weightToRootB / weightToRootA);
    }

    static double[] calcEquation(List<List<String>> equations, double[] values, List<List<String>> queries) {
        parent.clear();
        weight.clear();
        for (int i = 0; i < equations.size(); i++) {
            union(equations.get(i).get(0), equations.get(i).get(1), values[i]);
        }

        double[] results = new double[queries.size()];
        for (int i = 0; i < queries.size(); i++) {
            String a = queries.get(i).get(0), b = queries.get(i).get(1);
            if (!parent.containsKey(a) || !parent.containsKey(b)) {
                results[i] = -1.0;
                continue;
            }
            Object[] ra = find(a);
            Object[] rb = find(b);
            if (!ra[0].equals(rb[0])) {
                results[i] = -1.0;
            } else {
                results[i] = (double) ra[1] / (double) rb[1];
            }
        }
        return results;
    }

    public static void main(String[] args) {
        List<List<String>> equations = Arrays.asList(
                Arrays.asList("a", "b"), Arrays.asList("b", "c"));
        double[] values = {2.0, 3.0};
        List<List<String>> queries = Arrays.asList(
                Arrays.asList("a", "c"), Arrays.asList("b", "a"),
                Arrays.asList("a", "e"), Arrays.asList("x", "x"));

        System.out.println(Arrays.toString(calcEquation(equations, values, queries)));
        // [6.0, 0.5, -1.0, -1.0]
    }
}
```

**How to run:** save as `EvaluateDivision.java`, then run `java EvaluateDivision.java`.

## 6. Walkthrough

Trace `union("a", "b", 2.0)` then `union("b", "c", 3.0)`, then query `a/c`:

| step | action | result |
|---|---|---|
| 1 | `union(a,b,2.0)` | both new; `find(a)=(a,1.0)`, `find(b)=(b,1.0)`; attach `parent[a]=b`, `weight[a]=2.0*1.0/1.0=2.0` |
| 2 | `union(b,c,3.0)` | `b` exists, `c` new; `find(b)=(b,1.0)`, `find(c)=(c,1.0)`; attach `parent[b]=c`, `weight[b]=3.0` |
| 3 | query `a/c`: `find(a)` | `a`'s parent is `b` (not root); recurse: `find(b)` returns `(c, 3.0)`; so `a`'s ratio to root `c` is `weight[a]*3.0 = 2.0*3.0=6.0`; compress `parent[a]=c`, `weight[a]=6.0` |
| 4 | `find(c)` | `c` is its own root, returns `(c, 1.0)` |
| 5 | answer | same root `c`; `6.0 / 1.0 = 6.0` |

## 7. Gotchas & takeaways

> Gotcha: attaching `rootA` under `rootB` with the wrong weight formula (e.g. just `value`, ignoring `weightToRootA` and `weightToRootB`) silently corrupts every ratio for variables that were already grouped with `a` or `b` before this union — always derive the new weight from all four known ratios.

- Signal: "a/b = value; evaluate other ratios via known equations" needs weighted union-find, where each parent pointer also stores a multiplicative ratio.
- `find` must return both the representative and the accumulated ratio to it, and path compression must update both together.
- Related problems: Satisfiability of Equality Equations (same grouping idea, without the numeric weight).
