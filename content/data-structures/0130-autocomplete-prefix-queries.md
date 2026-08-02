---
card: data-structures
gi: 130
slug: autocomplete-prefix-queries
title: Autocomplete & prefix queries
---

## 1. What it is

**Autocomplete** takes a partial string the user has typed and returns every stored word that begins with it. Built on a trie, this is a two-step operation: walk down to the node representing the typed prefix, then collect every complete word reachable from that node's subtree.

## 2. Why & when

A search box, IDE, or command-line tool needs to suggest completions as the user types, updating on every keystroke. A trie makes this efficient: finding the prefix's node costs `O(length of prefix)`, and collecting matches only touches the relevant subtree — never the unrelated parts of the dictionary. A hash set could confirm exact matches just as fast, but finding "everything starting with X" would require scanning every stored word.

## 3. Core concept

**How the operation works.** Given a typed prefix:

1. Walk from the root, following one child per character of the prefix (identical to [Insert / search / startsWith](0129-insert-search-startswith.md)'s shared walk). If any character's child is missing, there are no completions at all — return an empty result immediately.
2. If the walk succeeds, run a depth-first traversal starting at the node it landed on, collecting every node marked `isEndOfWord`, and reconstructing the full word for each (the typed prefix plus whatever characters were walked past during the traversal).

**Why this only touches the relevant subtree.** Once you are at the prefix's node, every word reachable below it, by construction, starts with that prefix — the trie's shared-prefix structure guarantees this. So the collection step never has to check "does this word actually start with the prefix?" — that is already guaranteed by which subtree it is searching.

**Bounding the result count.** In production, you almost never want *every* completion (there could be thousands) — you want the top few, ranked by frequency or recency. That extends this pattern with a bounded [top-K heap](0123-top-k-elements-with-a-heap.md) over the collected candidates, instead of returning the full list.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Typing the prefix ca walks to a shared node, from which a depth first search collects cat, car, and cart as the matching completions">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">typed: "ca"</text>
    <circle cx="80" cy="50" r="12" fill="#161b22" stroke="#8b949e"/><text x="80" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">c</text>
    <circle cx="140" cy="50" r="12" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/><text x="140" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">a*</text>
    <line x1="92" y1="50" x2="128" y2="50" stroke="#8b949e"/>
    <text x="140" y="30" fill="#79c0ff" text-anchor="middle" font-size="9">walk lands here</text>
    <circle cx="220" cy="30" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="220" y="34" fill="#e6edf3" text-anchor="middle" font-size="8">t*</text>
    <circle cx="220" cy="70" r="12" fill="#161b22" stroke="#8b949e"/><text x="220" y="74" fill="#e6edf3" text-anchor="middle" font-size="8">r</text>
    <circle cx="280" cy="70" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="280" y="74" fill="#e6edf3" text-anchor="middle" font-size="8">t*</text>
    <line x1="150" y1="45" x2="210" y2="35" stroke="#8b949e"/>
    <line x1="150" y1="55" x2="210" y2="68" stroke="#8b949e"/>
    <line x1="232" y1="70" x2="268" y2="70" stroke="#8b949e"/>
    <text x="200" y="120" fill="#f0883e" text-anchor="middle" font-size="9">DFS from "ca" collects: cat, car, cart</text>
  </g>
</svg>

Typing `"ca"` walks to the shared `a` node; a depth-first search from there collects every reachable complete word: `"cat"`, `"car"`, `"cart"`.

## 5. Runnable example

```java
// AutocompleteDemo.java
import java.util.HashMap;
import java.util.Map;
import java.util.ArrayList;
import java.util.List;

public class AutocompleteDemo {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) current = current.children.computeIfAbsent(c, key -> new TrieNode());
            current.isEndOfWord = true;
        }

        private TrieNode walk(String prefix) {
            TrieNode current = root;
            for (char c : prefix.toCharArray()) {
                current = current.children.get(c);
                if (current == null) return null;
            }
            return current;
        }

        // Basic: find the prefix's node -- the first step of every autocomplete query.
        TrieNode findPrefixNode(String prefix) { return walk(prefix); }

        // Intermediate: depth-first collection of every complete word reachable from a starting node.
        void collectWords(TrieNode node, StringBuilder soFar, List<String> results) {
            if (node.isEndOfWord) results.add(soFar.toString());
            for (Map.Entry<Character, TrieNode> entry : node.children.entrySet()) {
                soFar.append(entry.getKey());
                collectWords(entry.getValue(), soFar, results);
                soFar.deleteCharAt(soFar.length() - 1); // backtrack before trying the next sibling
            }
        }

        // Advanced: the full autocomplete query -- walk, then collect, combining both steps.
        List<String> autocomplete(String prefix) {
            TrieNode node = findPrefixNode(prefix);
            if (node == null) return new ArrayList<>(); // no stored word starts with this prefix at all
            List<String> results = new ArrayList<>();
            collectWords(node, new StringBuilder(prefix), results);
            return results;
        }
    }

    static void basicLevel() {
        Trie trie = new Trie();
        for (String w : new String[]{"cat", "car", "cart", "dog"}) trie.insert(w);

        TrieNode node = trie.findPrefixNode("ca");
        System.out.println("basic: node for prefix 'ca' exists -> " + (node != null));
        System.out.println("basic: node for prefix 'xy' exists -> " + (trie.findPrefixNode("xy") != null));
    }

    static void intermediateLevel() {
        Trie trie = new Trie();
        for (String w : new String[]{"cat", "car", "cart", "dog"}) trie.insert(w);

        List<String> results = new ArrayList<>();
        TrieNode node = trie.findPrefixNode("ca");
        trie.collectWords(node, new StringBuilder("ca"), results);
        java.util.Collections.sort(results);
        System.out.println("intermediate: words completing 'ca' -> " + results);
    }

    static void advancedLevel() {
        Trie trie = new Trie();
        for (String w : new String[]{"cat", "car", "cart", "dog", "dodge"}) trie.insert(w);

        System.out.println("advanced: autocomplete(\"ca\")  -> " + sorted(trie.autocomplete("ca")));
        System.out.println("advanced: autocomplete(\"do\")  -> " + sorted(trie.autocomplete("do")));
        System.out.println("advanced: autocomplete(\"xyz\") -> " + sorted(trie.autocomplete("xyz")) + " (no matches)");
    }

    static List<String> sorted(List<String> list) { java.util.Collections.sort(list); return list; }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `AutocompleteDemo.java`, then run `java AutocompleteDemo.java`.

## 6. Walkthrough

1. `basicLevel()` walks to the node for `"ca"` (shared by `"cat"`, `"car"`, `"cart"`) and confirms it exists. Walking to `"xy"` fails partway (no `x` child from the root at all), correctly returning `null` — meaning no stored word could possibly start with `"xy"`.
2. `intermediateLevel()` runs `collectWords` starting from the `"ca"` node, with `soFar` initialized to `"ca"` (the prefix already walked). The depth-first traversal appends each child's character, checks `isEndOfWord`, recurses, then removes that character before trying the next sibling — correctly producing `["car", "cart", "cat"]` after sorting.
3. `advancedLevel()` runs the combined `autocomplete` method on several prefixes. `"ca"` and `"do"` both find matches by walking then collecting; `"xyz"` fails at the walk step (no such path exists at all), so `autocomplete` short-circuits and returns an empty list without ever attempting a collection.

## 7. Gotchas & takeaways

> Gotcha: forgetting to backtrack (`soFar.deleteCharAt(...)`) after recursing into a child during collection causes characters from one branch to leak into sibling branches' results — the exact same backtracking bug that shows up in path-sum and permutation problems.

- Autocomplete is a two-step trie operation: walk to the prefix's node (or fail fast if it does not exist), then depth-first collect every complete word in that subtree.
- The collection step never needs to re-check the prefix — every word found below the prefix's node is guaranteed, by the trie's structure, to start with that prefix.
- Real autocomplete systems bound the result count (e.g. top 5 by frequency) rather than returning every match — often layered with a [top-K heap](0123-top-k-elements-with-a-heap.md).
- Related concepts: [Insert / search / startsWith](0129-insert-search-startswith.md), [Spell-check & dictionary lookup](0131-spell-check-dictionary-lookup.md).
