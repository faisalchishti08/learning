---
card: data-structures
gi: 169
slug: weighted-union-find-accounts-merge
title: Weighted union-find & accounts merge
---

## 1. What it is

**Weighted union-find** attaches extra data to each item — a name, an email set, or a numeric relationship — so that after merging groups, you can still answer questions about what each group actually represents, not just which items share a root. "Accounts merge" is the classic example: merge user accounts that share any email, then report each merged group's full set of emails.

## 2. Why & when

Plain union-find only answers "are these two items in the same group?" Many real problems need more: "what is the combined set of emails for this merged group?" or "what is the ratio between these two variables, given a chain of known ratios?" Weighted union-find solves this by piggybacking extra bookkeeping onto the same `union`/`find` mechanism — usually a side map from root to combined data, updated every time two groups merge.

## 3. Core concept

**The shape.** The same `parent[]` array as any [disjoint-set](0162-disjoint-set-data-structure.md), plus one extra structure indexed by root: for accounts merge, a `Map<Integer, Set<String>>` from a group's root to that group's combined set of emails.

**The invariant.** Whenever `union(x, y)` actually merges two different roots, the extra data attached to the **losing** root (the one that gets attached under the other) must be merged into the **winning** root's data. If this step is skipped, the winning root's data becomes incomplete.

**Accounts merge, step by step.** Each account has a name and a list of emails. Two accounts belong to the same person if they share at least one email. Build a union-find over account **indices**. For every email, if you have already seen it belonging to another account, `union` the current account with that earlier account. After processing every account, group accounts by their root, and union each group's emails together (sorted, per the problem's usual output format).

**Why this generalizes beyond accounts.** The same pattern — "extra per-group data, merged during `union`" — solves other problems too: tracking each group's total weight (as in [union by size](0164-union-by-rank-size.md) itself), tracking a numeric offset between items in the same group (as in "Evaluate Division," where the extra data is a ratio relative to the root), or tracking the minimum/maximum value seen in each group.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three accounts merging into one group because they share emails, with the merged email set collected at the root">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="20" y="20" width="160" height="50" fill="#161b22" stroke="#79c0ff"/>
    <text x="100" y="38" text-anchor="middle">John (acct 0)</text>
    <text x="100" y="54" text-anchor="middle" font-size="8">john@mail, john2@mail</text>

    <rect x="220" y="20" width="160" height="50" fill="#161b22" stroke="#79c0ff"/>
    <text x="300" y="38" text-anchor="middle">John (acct 1)</text>
    <text x="300" y="54" text-anchor="middle" font-size="8">john2@mail, john3@mail</text>

    <rect x="420" y="20" width="160" height="50" fill="#161b22" stroke="#8b949e"/>
    <text x="500" y="38" text-anchor="middle">Mary (acct 2)</text>
    <text x="500" y="54" text-anchor="middle" font-size="8">mary@mail</text>

    <text x="200" y="100" font-size="9" fill="#f0883e">shared email "john2@mail" -&gt; union(0, 1)</text>
    <line x1="180" y1="45" x2="220" y2="45" stroke="#f0883e" stroke-width="2"/>

    <rect x="120" y="140" width="260" height="60" fill="#0d1117" stroke="#3fb950"/>
    <text x="250" y="160" text-anchor="middle">merged root: John</text>
    <text x="250" y="178" text-anchor="middle" font-size="8">emails: john@mail, john2@mail, john3@mail</text>
    <text x="250" y="192" text-anchor="middle" font-size="8" fill="#8b949e">Mary's account stays a separate group</text>
  </g>
</svg>

A shared email triggers a `union`; the root's email set absorbs the merged account's emails.

## 5. Runnable example

```java
// AccountsMerge.java
import java.util.*;

public class AccountsMerge {

    static class DSU {
        int[] parent, rank;

        DSU(int n) {
            parent = new int[n];
            rank = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }

        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }

        void union(int x, int y) {
            int rootX = find(x), rootY = find(y);
            if (rootX == rootY) return;
            if (rank[rootX] < rank[rootY]) parent[rootX] = rootY;
            else if (rank[rootX] > rank[rootY]) parent[rootY] = rootX;
            else { parent[rootY] = rootX; rank[rootX]++; }
        }
    }

    // Basic: union accounts that share any email, tracking which account index first owned each email.
    static List<List<String>> accountsMerge(List<List<String>> accounts) {
        int n = accounts.size();
        DSU dsu = new DSU(n);
        Map<String, Integer> emailToAccount = new HashMap<>();

        for (int i = 0; i < n; i++) {
            for (int j = 1; j < accounts.get(i).size(); j++) {
                String email = accounts.get(i).get(j);
                if (emailToAccount.containsKey(email)) {
                    dsu.union(i, emailToAccount.get(email));
                } else {
                    emailToAccount.put(email, i);
                }
            }
        }

        Map<Integer, TreeSet<String>> rootToEmails = new HashMap<>();
        for (int i = 0; i < n; i++) {
            int root = dsu.find(i);
            rootToEmails.computeIfAbsent(root, k -> new TreeSet<>()).addAll(accounts.get(i).subList(1, accounts.get(i).size()));
        }

        List<List<String>> result = new ArrayList<>();
        for (Map.Entry<Integer, TreeSet<String>> entry : rootToEmails.entrySet()) {
            List<String> merged = new ArrayList<>();
            merged.add(accounts.get(entry.getKey()).get(0)); // name
            merged.addAll(entry.getValue());
            result.add(merged);
        }
        return result;
    }

    static void basicLevel() {
        List<List<String>> accounts = List.of(
            List.of("John", "john@mail.com", "john2@mail.com"),
            List.of("John", "john2@mail.com", "john3@mail.com"),
            List.of("Mary", "mary@mail.com")
        );
        System.out.println("basic: merged accounts -> " + accountsMerge(accounts));
    }

    // Intermediate: weighted union-find tracking a numeric ratio between items (Evaluate Division style).
    static class WeightedDSU {
        Map<String, String> parent = new HashMap<>();
        Map<String, Double> weight = new HashMap<>(); // ratio of item to its parent

        void makeSetIfAbsent(String x) {
            parent.putIfAbsent(x, x);
            weight.putIfAbsent(x, 1.0);
        }

        String find(String x) {
            if (!parent.get(x).equals(x)) {
                String root = find(parent.get(x));
                weight.put(x, weight.get(x) * weight.get(parent.get(x)));
                parent.put(x, root);
            }
            return parent.get(x);
        }

        void union(String x, String y, double ratio) {
            makeSetIfAbsent(x);
            makeSetIfAbsent(y);
            String rootX = find(x), rootY = find(y);
            if (rootX.equals(rootY)) return;
            parent.put(rootX, rootY);
            weight.put(rootX, ratio * weight.get(y) / weight.get(x));
        }

        double evaluate(String x, String y) {
            if (!parent.containsKey(x) || !parent.containsKey(y)) return -1.0;
            String rootX = find(x), rootY = find(y);
            if (!rootX.equals(rootY)) return -1.0;
            return weight.get(x) / weight.get(y);
        }
    }

    static void intermediateLevel() {
        WeightedDSU dsu = new WeightedDSU();
        dsu.union("a", "b", 2.0); // a / b = 2.0
        dsu.union("b", "c", 3.0); // b / c = 3.0

        System.out.println("intermediate: a/c -> " + dsu.evaluate("a", "c")); // expect 6.0
        System.out.println("intermediate: c/a -> " + dsu.evaluate("c", "a")); // expect ~0.1667
    }

    // Advanced: accounts merge on a larger, more tangled input with three separate identities.
    static void advancedLevel() {
        List<List<String>> accounts = List.of(
            List.of("David", "david0@mail.com", "david1@mail.com"),
            List.of("David", "david1@mail.com", "david2@mail.com"),
            List.of("David", "david2@mail.com", "david3@mail.com"),
            List.of("David", "david4@mail.com")
        );
        List<List<String>> merged = accountsMerge(accounts);
        System.out.println("advanced: merged count (expect 2 groups) -> " + merged.size());
        for (List<String> group : merged) System.out.println("advanced: group -> " + group);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java AccountsMerge.java`

## 6. Walkthrough

Trace `accountsMerge` on the basic example: account `0` (John) has emails `john@mail.com, john2@mail.com`; account `1` (John) has `john2@mail.com, john3@mail.com`; account `2` (Mary) has `mary@mail.com`.

Process account `0`: neither email seen before, so record `john@mail.com -> 0` and `john2@mail.com -> 0`. Process account `1`: `john2@mail.com` was already recorded as belonging to account `0`, so call `union(1, 0)` — accounts `0` and `1` merge. Then record `john3@mail.com -> 1`. Process account `2`: `mary@mail.com` is new, record `mary@mail.com -> 2`, no union needed.

Now group by root: `find(0)` and `find(1)` return the same root, so their emails combine into one sorted set: `{john@mail.com, john2@mail.com, john3@mail.com}`, labeled with account `0`'s name, "John". Account `2` stays its own group: `{mary@mail.com}`, labeled "Mary".

For the weighted version: `union("a", "b", 2.0)` records that `a = 2.0 * b`. `union("b", "c", 3.0)` records `b = 3.0 * c`. Calling `evaluate("a", "c")` finds both roots match (they were merged), and combines the ratios along the path: `a/root * root/c`, which resolves to `2.0 * 3.0 = 6.0` — the chained ratio, computed without ever explicitly storing `a/c`.

**Complexity.** Accounts merge: `O(n * k * α(n))` for `n` accounts with up to `k` emails each, dominated by the email-to-account map lookups and the final sort per group. Weighted union-find (Evaluate Division style): each `union` or `evaluate` costs `O(α(n))` amortized, same as plain union-find, since the weight bookkeeping piggybacks on the same `find` recursion.

## 7. Gotchas & takeaways

> In the weighted version, `find` must update **both** the parent pointer and the weight during path compression (`weight.put(x, weight.get(x) * weight.get(parent.get(x)))`) — updating only the parent pointer leaves the weight stale and silently produces wrong ratios on future queries.

- For accounts merge, always union by **account index**, not by email string directly — the email is only the signal that two accounts belong together, not the item being grouped.
- When merging the extra per-group data (email sets, in this case), always merge the **losing** root's data into the **winning** root's data at the moment of `union` — or, as shown here, defer the merge to a single final pass over `find(i)` results, which is simpler and avoids partial-merge bugs.
- Weighted union-find is the right tool whenever "same group" is not the only question — whenever you also need "what is the relationship between these two items in the same group?"
