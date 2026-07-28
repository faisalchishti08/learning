---
card: leetcode-patterns
gi: 528
slug: accounts-merge
title: Accounts Merge
---

## 1. What it is

Each account is a list `[name, email1, email2, ...]`. Two accounts belong to the same person if they share at least one email, and this sharing can chain across more than two accounts. Merge all accounts belonging to the same person into one, with a sorted list of all their distinct emails, prefixed by their name. Example: `[["John","a@x","b@x"], ["John","b@x","c@x"], ["Mary","d@x"]]` → the first two merge into `["John","a@x","b@x","c@x"]` (since they share `b@x`), and `["Mary","d@x"]` stays separate.

## 2. Why & when

"Merge groups if they share something" is a direct [union-find signal](0523-union-find-signal-dynamic-connectivity-or-grouping-by-equiva.md). The tricky part is that account names are not unique identifiers — two different people can share a name — so the merge key must be the emails, not the account index shown to the user. Constraints: up to 1,000 accounts, each with up to 10 emails.

## 3. Core concept

**Key idea:** treat each *account index* (not each email) as a union-find item. For every account, union its index with the index of every other account that already owns one of its emails — tracked with a `Map<String, Integer>` from email to the first account index that claimed it. After processing every account, group email sets by their union-find representative, then sort and format each group.

**Steps:**
1. Initialize union-find over account indices `0..k-1`, and an empty `Map<String, Integer> emailOwner`.
2. For each account `i`: for each of its emails, if `emailOwner` already has that email mapped to some index `j`, `union(i, j)`; otherwise, record `emailOwner[email] = i`.
3. After processing all accounts, group every email by `find(owner index)` into a `Map<Integer, TreeSet<String>>` (a `TreeSet` keeps emails sorted automatically).
4. For each group, prepend that group's account name and output the merged list.

**Why unioning account indices (not emails) is the right item type:** the goal is "which accounts belong to the same person," and account indices map directly to a name and an output row. Unioning emails directly would work too, but then you would need a separate step to recover which account's name to attach to each merged email group.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two John accounts sharing email b@x merge into one group; Mary stays separate">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="220" height="50" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="130" y="40" fill="#e6edf3" text-anchor="middle">account 0: John</text>
    <text x="130" y="58" fill="#8b949e" text-anchor="middle">a@x, b@x</text>
    <rect x="20" y="100" width="220" height="50" rx="6" fill="#161b22" stroke="#3fb950"/>
    <text x="130" y="120" fill="#e6edf3" text-anchor="middle">account 1: John</text>
    <text x="130" y="138" fill="#8b949e" text-anchor="middle">b@x, c@x</text>
    <line x1="130" y1="70" x2="130" y2="100" stroke="#f0883e" stroke-width="2"/>
    <text x="170" y="88" fill="#f0883e" font-size="11">shared b@x -&gt; union(0,1)</text>
    <rect x="420" y="60" width="220" height="50" rx="6" fill="#161b22" stroke="#30363d"/>
    <text x="530" y="80" fill="#e6edf3" text-anchor="middle">account 2: Mary</text>
    <text x="530" y="98" fill="#8b949e" text-anchor="middle">d@x (own group)</text>
  </g>
</svg>

Accounts 0 and 1 share `b@x`, so `union(0, 1)` merges them into one group; account 2 shares no email with anyone, so it stays its own group.

## 5. Runnable example

**Level 1 — Brute force.** Repeatedly scan all account pairs, merging any pair that shares an email, until a full pass makes no more merges. O(k² · e) or worse, where k is the account count and e the emails per account.

**KEY INSIGHT:** unioning account indices as emails are first seen turns "does this chain of shared emails connect these accounts" into one pass with union-find, instead of repeated re-scanning.

**Level 2 — Optimal.** Union-find over account indices plus an email-to-owner map, O(k · e · α(k)) for the union phase, plus O(k · e · log e) to sort emails within each merged group.

**Level 3 — Hardened.** Handles more than two accounts chaining together through shared emails, and accounts that share no email with anyone.

```java
// AccountsMerge.java
import java.util.*;

public class AccountsMerge {

    static class DSU {
        int[] parent;
        DSU(int n) {
            parent = new int[n];
            for (int i = 0; i < n; i++) parent[i] = i;
        }
        int find(int x) {
            if (parent[x] != x) parent[x] = find(parent[x]);
            return parent[x];
        }
        void union(int a, int b) {
            parent[find(a)] = find(b);
        }
    }

    static List<List<String>> accountsMerge(List<List<String>> accounts) {
        int n = accounts.size();
        DSU dsu = new DSU(n);
        Map<String, Integer> emailOwner = new HashMap<>();

        for (int i = 0; i < n; i++) {
            for (int j = 1; j < accounts.get(i).size(); j++) {
                String email = accounts.get(i).get(j);
                if (emailOwner.containsKey(email)) {
                    dsu.union(i, emailOwner.get(email));
                } else {
                    emailOwner.put(email, i);
                }
            }
        }

        Map<Integer, TreeSet<String>> groups = new HashMap<>();
        for (Map.Entry<String, Integer> entry : emailOwner.entrySet()) {
            int root = dsu.find(entry.getValue());
            groups.computeIfAbsent(root, k -> new TreeSet<>()).add(entry.getKey());
        }

        List<List<String>> result = new ArrayList<>();
        for (Map.Entry<Integer, TreeSet<String>> entry : groups.entrySet()) {
            List<String> merged = new ArrayList<>();
            merged.add(accounts.get(entry.getKey()).get(0)); // name
            merged.addAll(entry.getValue());
            result.add(merged);
        }
        return result;
    }

    public static void main(String[] args) {
        List<List<String>> accounts = new ArrayList<>();
        accounts.add(Arrays.asList("John", "a@x", "b@x"));
        accounts.add(Arrays.asList("John", "b@x", "c@x"));
        accounts.add(Arrays.asList("Mary", "d@x"));

        for (List<String> merged : accountsMerge(accounts)) {
            System.out.println(merged);
        }
        // [John, a@x, b@x, c@x]
        // [Mary, d@x]
    }
}
```

**How to run:** save as `AccountsMerge.java`, then run `java AccountsMerge.java`.

## 6. Walkthrough

Trace the union phase over `[["John","a@x","b@x"], ["John","b@x","c@x"], ["Mary","d@x"]]`:

| account i | email | emailOwner before | action | emailOwner after |
|---|---|---|---|---|
| 0 | a@x | {} | not seen, record | {a@x:0} |
| 0 | b@x | {a@x:0} | not seen, record | {a@x:0, b@x:0} |
| 1 | b@x | {a@x:0, b@x:0} | seen at 0 -> union(1,0) | unchanged |
| 1 | c@x | {a@x:0, b@x:0} | not seen, record | {..., c@x:1} |
| 2 | d@x | {...} | not seen, record | {..., d@x:2} |

After unions, `find(0) == find(1)`, so their emails (`a@x`, `b@x`, `c@x`) group together under account 0's name "John," sorted. Account 2 has no shared email, so it stays its own group.

## 7. Gotchas & takeaways

> Gotcha: unioning by account index using only the *first two* accounts that share an email misses longer chains — if account 0 shares an email with account 1, and account 1 shares a different email with account 2, all three must end up in one group; the email-owner map handles this automatically because every new shared email triggers a fresh union against whichever account first claimed it.

- Signal: "merge records if they share a key field" (here, email) is a union-find grouping problem, keyed by record index, not by the shared field itself.
- Use a `TreeSet<String>` per merged group to get sorted, de-duplicated emails for free.
- Related problems: Number of Connected Components in an Undirected Graph, Satisfiability of Equality Equations, Smallest String With Swaps.
