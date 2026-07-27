---
card: leetcode-patterns
gi: 510
slug: map-sum-pairs
title: Map Sum Pairs
---

## 1. What it is

Design a class `MapSum` supporting `insert(key, val)` (inserting a key-value pair, overwriting any existing value for that key) and `sum(prefix)` (returning the sum of every value whose key starts with `prefix`). Example: `insert("apple", 3)`, `sum("ap")` → `3`; `insert("app", 2)`, `sum("ap")` → `5`.

## 2. Why & when

"Sum of values for all keys sharing a prefix" is exactly the trie's prefix-matching strength, extended with a value stored at each word's end node — building on the [trie template](0506-trie-template-tree-of-character-bit-nodes-with-an-end-marker.md). Constraints: up to 1000 insert/sum calls.

## 3. Core concept

**Key idea:** each `TrieNode` stores a `value` (not just `isEnd`). Insert a key by walking/creating nodes as usual, storing `val` at the final node. To answer `sum(prefix)`, walk to the prefix's node, then recursively sum every `value` in the subtree rooted there (every key extending from that node contributes its stored value).

**Steps:**
1. `insert(key, val)`: also keep a separate `Map<String, Integer>` of raw key-to-value pairs, to correctly handle overwriting an existing key (the trie alone does not easily support "subtract the old value, add the new one" without extra bookkeeping).
2. Insert into the trie: walk/create nodes for each character of `key`; mark the final node's `isEnd = true`.
3. `sum(prefix)`: walk to the prefix's node; if the path does not exist, return `0`. Otherwise, do a depth-first traversal of that node's subtree, summing `value` at every node where `isEnd` is true, using the up-to-date values from the separate map.

**Why a separate raw map is the simplest way to handle overwrites:** if `insert("apple", 3)` is followed by `insert("apple", 5)`, the trie's `apple` end node must reflect `5`, not `3 + 5`. Tracking the current value per key in a plain hash map, and using that map (not a stale value baked into the trie) during the `sum` traversal, sidesteps the need to "undo" a previous insertion inside the trie itself.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Summing every value in the subtree beneath a prefix's node">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">insert("apple", 3), insert("app", 2). sum("ap")</text>
    <text x="20" y="45" fill="#8b949e">trie path a -&gt; p -&gt; p (this node = end of "app", value 2)</text>
    <text x="20" y="65" fill="#8b949e">continuing -&gt; l -&gt; e (end of "apple", value 3)</text>
    <text x="20" y="90" fill="#79c0ff">sum("ap") walks to the second 'p' node, then explores its whole subtree</text>
    <text x="20" y="115" fill="#3fb950">finds end nodes for "app" (2) and "apple" (3) -&gt; total 5</text>
  </g>
</svg>

Walking to the prefix's node, then summing every stored value in its subtree, answers the query.

## 5. Runnable example

```java
// MapSum.java
import java.util.*;

public class MapSum {

    private static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
        String key = null; // stores the full key at its end node, for lookup in rawValues
    }

    private final TrieNode root = new TrieNode();
    private final Map<String, Integer> rawValues = new HashMap<>();

    public void insert(String key, int val) {
        rawValues.put(key, val); // overwrite handled automatically by the map

        TrieNode node = root;
        for (char c : key.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) node.children[index] = new TrieNode();
            node = node.children[index];
        }
        node.isEnd = true;
        node.key = key;
    }

    public int sum(String prefix) {
        TrieNode node = root;
        for (char c : prefix.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) return 0;
            node = node.children[index];
        }
        return sumSubtree(node);
    }

    private int sumSubtree(TrieNode node) {
        int total = 0;
        if (node.isEnd) total += rawValues.get(node.key);
        for (TrieNode child : node.children) {
            if (child != null) total += sumSubtree(child);
        }
        return total;
    }

    public static void main(String[] args) {
        MapSum mapSum = new MapSum();
        mapSum.insert("apple", 3);
        System.out.println(mapSum.sum("ap"));  // 3

        mapSum.insert("app", 2);
        System.out.println(mapSum.sum("ap"));  // 5

        mapSum.insert("apple", 5); // overwrite
        System.out.println(mapSum.sum("ap"));  // 7 (5 + 2)
    }
}
```

**How to run:** save as `MapSum.java`, then run `java MapSum.java`.

## 6. Walkthrough

1. `insert("apple", 3)`: `rawValues = {"apple": 3}`. Trie path `a-p-p-l-e` created, `e` node marked `isEnd`, `key="apple"`.
2. `sum("ap")`: walk to the second `p` node (end of `"ap"` as a prefix, not a stored key). Its subtree contains the `e` node (end of "apple", value looked up as `rawValues.get("apple") = 3`). Total: `3`.
3. `insert("app", 2)`: `rawValues = {"apple": 3, "app": 2}`. The second `p` node itself becomes an end node (`isEnd=true`, `key="app"`).
4. `sum("ap")`: now the subtree includes both the second `p` node itself (`isEnd=true`, value `2`) and the `e` node beneath it (value `3`). Total: `5`.
5. `insert("apple", 5)`: `rawValues.put("apple", 5)` overwrites the old value. `sum("ap")` now sums `2` (from "app") and the updated `5` (from "apple"), giving `7`.

## 7. Gotchas & takeaways

> Gotcha: storing the value directly at the trie node and adding to it on every `insert` (instead of overwriting) double-counts when the same key is inserted twice — the problem requires the *latest* value to replace the old one, not accumulate.

- Builds on the [trie template](0506-trie-template-tree-of-character-bit-nodes-with-an-end-marker.md), adding a value (via a companion hash map) at each end-of-word node.
- A separate raw key-to-value map cleanly handles overwrites without needing to "undo" a stale value baked into the trie.
- Time: O(L) for `insert`, O(L + subtree size) for `sum`, where L is the key/prefix length.
