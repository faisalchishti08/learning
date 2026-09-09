---
card: system-design
gi: 163
slug: autocomplete-typeahead
title: Autocomplete / typeahead
---

## 1. What it is

**Autocomplete** (or typeahead) suggests complete words or phrases as a user types, based on what they have typed so far — a prefix. Typing "data" might suggest "database," "data structures," and "data science." This is a different problem from full-text search: it needs to find, extremely fast, every known term or phrase that *starts with* a given prefix, usually ranked by popularity, and re-run that lookup on every single keystroke.

## 2. Why & when

A user typing into a search box benefits enormously from seeing likely completions before they finish typing, both to save effort and to guide them toward valid or popular queries. This needs a data structure built specifically for fast prefix lookup — a plain [inverted index](0159-inverted-index.md) is built for "which documents contain this exact term," not "which terms start with these characters." Use a dedicated prefix structure like a **trie** (prefix tree) whenever you need type-as-you-go suggestions, which must respond within milliseconds on every keystroke to feel responsive.

## 3. Core concept

- **Trie (prefix tree):** a tree where each node represents one character, and the path from the root to any node spells out a prefix; a word "ends" at a node marked as a complete word, and multiple words sharing a prefix share the same path down to where they diverge.
- **Prefix lookup:** walking the trie one character at a time following the input prefix's characters directly gives you the exact subtree of all words that start with that prefix — no need to scan every stored word.
- **Ranking suggestions:** each word (or word-ending node) commonly stores a popularity score (e.g. how often it has been searched before), so suggestions under a prefix can be shown most-popular-first, not just alphabetically.
- **Collecting completions:** once you have walked down to the node representing the typed prefix, a traversal of that node's subtree collects every complete word beneath it — these are exactly the candidate suggestions.
- **Update as the user types:** each keystroke either narrows the current subtree (typing another matching character) or requires walking from the root again (if the user deletes characters or the prefix no longer matches).

## 4. Diagram

```
   trie storing: "cat" (pop 50), "car" (pop 80), "card" (pop 30), "dog" (pop 60)

                    root
                   /    \
                  c      d
                  |      |
                  a      o
                 / \     |
                t   r    g*  (60)
                *   |
              (50)  d
                    *
                  (30)
              (also "car" ends at 'r', marked * with pop 80)

   typing "ca" -> walk root->c->a -> subtree has "cat"(50), "car"(80), "card"(30)
   ranked by popularity: ["car", "cat", "card"]
```
*Caption: walking the trie by the typed prefix directly reaches the exact subtree of matching words, which are then ranked by popularity.*

## 5. Runnable example

**Level 1 — Basic.** Build a trie from a set of words.

**Level 2 — Prefix lookup.** Walk the trie by a typed prefix and collect every complete word in that subtree.

**Level 3 — Rank suggestions by popularity.** Store a popularity score per word, and return suggestions sorted most-popular-first.

```java
// AutocompleteDemo.java
import java.util.*;

public class AutocompleteDemo {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isWordEnd = false;
        int popularity = 0;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        // Level 1: insert a word, marking its end node and storing its popularity.
        void insert(String word, int popularity) {
            TrieNode node = root;
            for (char c : word.toCharArray()) {
                node = node.children.computeIfAbsent(c, k -> new TrieNode());
            }
            node.isWordEnd = true;
            node.popularity = popularity;
        }

        // Level 2: walk down to the node representing the given prefix.
        private TrieNode walkToPrefix(String prefix) {
            TrieNode node = root;
            for (char c : prefix.toCharArray()) {
                node = node.children.get(c);
                if (node == null) return null; // no word in the trie starts with this prefix
            }
            return node;
        }

        // Collect every complete word in the subtree rooted at `node`, prefixed by `soFar`.
        private void collectWords(TrieNode node, String soFar, List<Map.Entry<String, Integer>> results) {
            if (node.isWordEnd) results.add(Map.entry(soFar, node.popularity));
            for (Map.Entry<Character, TrieNode> entry : node.children.entrySet()) {
                collectWords(entry.getValue(), soFar + entry.getKey(), results);
            }
        }

        // Level 3: prefix lookup + collect + sort by popularity, most popular first.
        List<String> suggest(String prefix) {
            TrieNode prefixNode = walkToPrefix(prefix);
            if (prefixNode == null) return List.of();
            List<Map.Entry<String, Integer>> results = new ArrayList<>();
            collectWords(prefixNode, prefix, results);
            results.sort((a, b) -> b.getValue() - a.getValue()); // highest popularity first
            return results.stream().map(Map.Entry::getKey).toList();
        }
    }

    public static void main(String[] args) {
        Trie trie = new Trie();
        trie.insert("cat", 50);
        trie.insert("car", 80);
        trie.insert("card", 30);
        trie.insert("dog", 60);

        System.out.println("suggestions for \"ca\": " + trie.suggest("ca"));
        System.out.println("suggestions for \"car\": " + trie.suggest("car"));
        System.out.println("suggestions for \"do\": " + trie.suggest("do"));
        System.out.println("suggestions for \"xyz\" (no match): " + trie.suggest("xyz"));
    }
}
```

**How to run:** save as `AutocompleteDemo.java`, then run `java AutocompleteDemo.java`.

## 6. Walkthrough

1. Each `trie.insert` call walks (or creates) a path of `TrieNode`s, one per character; after all four inserts, the trie has a shared path for `"c"` -> `"a"`, which then branches into `"t"` (ending "cat") and `"r"` (ending "car", which itself continues to `"d"` ending "card").
2. `trie.suggest("ca")` calls `walkToPrefix("ca")`, walking `root -> c -> a` and returning that node; `collectWords` then recursively explores every child of that node, finding `"cat"` (via the `t` child), `"car"` (the `a`-node's `r` child is itself a word end), and `"card"` (continuing past `car`'s `r` node to `d`).
3. The three results, `[("cat", 50), ("car", 80), ("card", 30)]`, get sorted by `results.sort((a, b) -> b.getValue() - a.getValue())`, a descending sort on popularity, producing the order `["car", "cat", "card"]` (80, then 50, then 30).
4. `trie.suggest("car")` walks one character further, to the node after `root -> c -> a -> r`; that node is itself a word end (`"car"`, popularity 80) and also has a child continuing to `"card"` (popularity 30), so both are collected and sorted, giving `["car", "card"]` — note `"cat"` is correctly excluded, since it does not share the `"car"` prefix.
5. `trie.suggest("xyz")` calls `walkToPrefix("xyz")`; the very first character lookup, `root.children.get('x')`, returns `null` since no inserted word starts with "x", so `walkToPrefix` immediately returns `null`, and `suggest` returns an empty list without any further traversal.

## 7. Gotchas & takeaways

> Gotcha: a trie's per-character node structure can use significant memory for a huge vocabulary with little shared prefix structure (e.g. many unrelated single long words) — production autocomplete systems often use a more memory-efficient variant (a compressed trie / radix tree, or a precomputed top-N-per-prefix cache) rather than a plain trie at web scale.

- Autocomplete needs a data structure built for fast prefix lookup, which a term-to-document inverted index is not designed for.
- A trie makes prefix lookup a direct walk (one step per typed character), then a subtree traversal to collect matching words — no scanning of unrelated words.
- Ranking suggestions by popularity (or another relevance signal) matters as much as finding them at all — the raw prefix match is only step one.
- Related concepts: [Inverted index](0159-inverted-index.md) (the different structure used for full-text, not prefix, search), [Fuzzy search & typo tolerance](0162-fuzzy-search-typo-tolerance.md) (handling a typo within the typed prefix itself), [Relevance ranking (TF-IDF / BM25)](0161-relevance-ranking-tf-idf-bm25.md) (a different ranking signal, used for full search results rather than prefix suggestions).
