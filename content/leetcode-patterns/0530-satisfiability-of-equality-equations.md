---
card: leetcode-patterns
gi: 530
slug: satisfiability-of-equality-equations
title: Satisfiability of Equality Equations
---

## 1. What it is

You are given a list of equations, each either `"a==b"` or `"a!=b"`, where `a` and `b` are single lowercase letters. Return `true` if there is a way to assign values to every letter so that all equations hold at once, or `false` if the equations are contradictory. Example: `["a==b", "b!=a"]` → `false` (equation 1 says `a` and `b` are equal, equation 2 says they are not — a direct contradiction).

## 2. Why & when

"Are these equality and inequality constraints consistent?" is a direct [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md): equalities merge variables into groups, and inequalities must never point within the same group. Constraints: up to 500 equations, letters restricted to `a`–`z`.

## 3. Core concept

**Key idea:** equality is transitive (if `a == b` and `b == c`, then `a == c` too), which is exactly what union-find groups capture. Inequality is not transitive and cannot be merged — it can only be *checked* against the groups formed by the equalities.

**Steps:**
1. Process every `"a==b"` equation first: `union(a, b)`.
2. After all equalities are unioned, process every `"a!=b"` equation: if `find(a) == find(b)`, the equations are contradictory — return `false` immediately, since the equalities already forced `a` and `b` to be equal.
3. If no inequality equation fails this check, return `true`.

**Why equalities must be processed before any inequality check:** an inequality like `a != b` is only a contradiction if the *equalities* have already forced `a` and `b` into the same group. Checking inequalities before all unions are done could miss a contradiction that a later equality would have created — so the two passes must stay strictly separated, equalities first.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a==b unions a and b into one group; b!=a then checks the same group and finds a contradiction">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">["a==b", "b!=a"]</text>
    <circle cx="150" cy="80" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="150" y="85" fill="#e6edf3" text-anchor="middle">a</text>
    <circle cx="280" cy="80" r="18" fill="#161b22" stroke="#3fb950"/>
    <text x="280" y="85" fill="#e6edf3" text-anchor="middle">b</text>
    <line x1="168" y1="80" x2="262" y2="80" stroke="#3fb950" stroke-width="2"/>
    <text x="215" y="65" fill="#3fb950" font-size="11" text-anchor="middle">union: a==b</text>
    <text x="215" y="130" fill="#f0883e" text-anchor="middle">check b!=a: find(b)==find(a) -&gt; contradiction -&gt; false</text>
  </g>
</svg>

`a==b` merges `a` and `b` into one group. `b!=a` then checks that same group and finds them equal — a contradiction, so the equations are unsatisfiable.

## 5. Runnable example

**Level 1 — Brute force.** Try every possible assignment of small integer values to each of the 26 letters, checking whether every equation holds. Exponential, and impractical even for a handful of letters.

**KEY INSIGHT:** you never need actual variable values — only whether two letters are forced equal by transitivity, which union-find tracks directly.

**Level 2 — Optimal.** Union-find over the 26 letters: union all equalities, then check all inequalities, O(n · α(26)) ≈ O(n).

**Level 3 — Hardened.** Handles a letter equated or compared to itself (`"a==a"` always fine; `"a!=a"` always a contradiction), and equations given in any order.

```java
// EquationsPossible.java
public class EquationsPossible {

    static class DSU {
        int[] parent = new int[26];
        DSU() {
            for (int i = 0; i < 26; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        void union(int a, int b) {
            parent[find(a)] = find(b);
        }
    }

    static boolean equationsPossible(String[] equations) {
        DSU dsu = new DSU();

        for (String eq : equations) {
            if (eq.charAt(1) == '=') {
                int a = eq.charAt(0) - 'a';
                int b = eq.charAt(3) - 'a';
                dsu.union(a, b);
            }
        }

        for (String eq : equations) {
            if (eq.charAt(1) == '!') {
                int a = eq.charAt(0) - 'a';
                int b = eq.charAt(3) - 'a';
                if (dsu.find(a) == dsu.find(b)) {
                    return false; // equalities already forced a == b
                }
            }
        }
        return true;
    }

    public static void main(String[] args) {
        System.out.println(equationsPossible(new String[]{"a==b", "b!=a"})); // false
        System.out.println(equationsPossible(new String[]{"b==a", "a==b"})); // true
        System.out.println(equationsPossible(new String[]{"a==b", "b==c", "a==c"})); // true
        System.out.println(equationsPossible(new String[]{"a!=a"})); // false, self-inequality
    }
}
```

**How to run:** save as `EquationsPossible.java`, then run `java EquationsPossible.java`.

## 6. Walkthrough

Trace `equationsPossible(["a==b", "b!=a"])`:

1. First pass (equalities only): `"a==b"` calls `union('a'-'a'=0, 'b'-'a'=1)`, merging groups `{0}` and `{1}` into `{0,1}`.
2. Second pass (inequalities only): `"b!=a"` calls `find(1)` and `find(0)`. Both now return the same representative, since the first pass already merged them.
3. Since `find(1) == find(0)`, the function returns `false` immediately — the inequality directly contradicts what the equality forced.

## 7. Gotchas & takeaways

> Gotcha: interleaving the two passes (checking an inequality before all equalities are unioned) can miss a contradiction that a later equality would create — always finish unioning every equality before checking any inequality.

- Signal: "equality and inequality constraints, are they consistent" is answered by union-find equalities first, then a same-group check for every inequality.
- Only 26 possible letters means a fixed-size `int[26]` array works — no need for a hash map keyed by character.
- Related problems: Accounts Merge, Evaluate Division (a related but weighted variant), Graph Valid Tree.
