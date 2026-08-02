---
card: data-structures
gi: 129
slug: insert-search-startswith
title: Insert / search / startsWith
---

## 1. What it is

These are the three core operations every trie implementation supports: **insert** a word, **search** for an exact word, and **startsWith** check whether any stored word begins with a given prefix. All three share the same walk-down-the-tree mechanism; they only differ in what they check once the walk finishes.

## 2. Why & when

These three operations are the trie's public API — almost every trie-based feature (autocomplete, spell-check, word games) is built entirely out of calls to these three methods. Understanding exactly how they differ, despite sharing nearly identical code, is the key to implementing a correct trie from scratch, which is a very common interview exercise (LeetCode's "Implement Trie" problem).

## 3. Core concept

**How the operation works — the shared walk.** All three methods start at the root and, for each character in the input string, follow the child link for that character. `insert` creates a missing child if needed; `search` and `startsWith` return `false` immediately if a needed child is missing.

**Where they differ, precisely.** After the walk reaches the end of the input string (either creating or following every needed link):

- **`insert`** marks the final node's `isEndOfWord = true`.
- **`search`** returns `true` only if the final node exists **and** `isEndOfWord` is `true`.
- **`startsWith`** returns `true` if the final node simply **exists** — it does not check `isEndOfWord` at all, since a prefix does not need to be a complete word itself.

**Why the isEndOfWord check is the only difference between search and startsWith.** Both walk identically and can fail identically (a missing child partway through). The only place they diverge is the very last check: `search` additionally demands the path represents a *complete* stored word, while `startsWith` is satisfied by the path merely *existing*.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A trie storing app and apple, showing that search of app is true, search of appl is false, but startsWith of appl is true because the path exists even though it is not itself a stored word">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">stored: "app", "apple"</text>
    <circle cx="80" cy="50" r="12" fill="#161b22" stroke="#8b949e"/><text x="80" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">a</text>
    <circle cx="140" cy="50" r="12" fill="#161b22" stroke="#8b949e"/><text x="140" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">p</text>
    <circle cx="200" cy="50" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="200" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">p*</text>
    <circle cx="260" cy="50" r="12" fill="#161b22" stroke="#79c0ff"/><text x="260" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">l</text>
    <circle cx="320" cy="50" r="12" fill="#0d1117" stroke="#f0883e" stroke-width="2"/><text x="320" y="54" fill="#e6edf3" text-anchor="middle" font-size="8">e*</text>
    <line x1="92" y1="50" x2="128" y2="50" stroke="#8b949e"/>
    <line x1="152" y1="50" x2="188" y2="50" stroke="#8b949e"/>
    <line x1="212" y1="50" x2="248" y2="50" stroke="#8b949e"/>
    <line x1="272" y1="50" x2="308" y2="50" stroke="#8b949e"/>
    <text x="200" y="95" fill="#f0883e" text-anchor="middle" font-size="9">search("app") -> true (node exists AND isEndOfWord)</text>
    <text x="260" y="120" fill="#79c0ff" text-anchor="middle" font-size="9">search("appl") -> false (node exists but isEndOfWord is false)</text>
    <text x="260" y="145" fill="#79c0ff" text-anchor="middle" font-size="9">startsWith("appl") -> true (node exists -- isEndOfWord not checked)</text>
  </g>
</svg>

The node after `"appl"` exists (it is on the path to `"apple"`) but is not marked `isEndOfWord`; `search` rejects it while `startsWith` accepts it, since only `search` additionally requires a complete word.

## 5. Runnable example

```java
// TrieOperations.java
import java.util.HashMap;
import java.util.Map;

public class TrieOperations {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isEndOfWord = false;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        // Basic: insert -- walk down, creating missing nodes, then mark the final node.
        void insert(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) {
                current = current.children.computeIfAbsent(c, key -> new TrieNode());
            }
            current.isEndOfWord = true;
        }

        // Shared walk helper: returns the node for `word`, or null if any character along the path is missing.
        private TrieNode walk(String word) {
            TrieNode current = root;
            for (char c : word.toCharArray()) {
                current = current.children.get(c);
                if (current == null) return null; // missing child -- neither exact match nor any prefix beyond here exists
            }
            return current;
        }

        // Intermediate: search -- the walk must succeed AND the final node must be a complete word.
        boolean search(String word) {
            TrieNode node = walk(word);
            return node != null && node.isEndOfWord;
        }

        // Intermediate: startsWith -- the walk must succeed; isEndOfWord is irrelevant.
        boolean startsWith(String prefix) {
            return walk(prefix) != null;
        }
    }

    static void basicLevel() {
        Trie trie = new Trie();
        trie.insert("app");
        trie.insert("apple");
        System.out.println("basic: inserted 'app' and 'apple'");
    }

    static void intermediateLevel() {
        Trie trie = new Trie();
        trie.insert("app");
        trie.insert("apple");

        System.out.println("intermediate: search(\"app\")    -> " + trie.search("app"));     // true: node exists AND isEndOfWord
        System.out.println("intermediate: search(\"appl\")   -> " + trie.search("appl"));    // false: node exists but NOT isEndOfWord
        System.out.println("intermediate: startsWith(\"appl\") -> " + trie.startsWith("appl")); // true: node merely needs to exist
        System.out.println("intermediate: search(\"appz\")   -> " + trie.search("appz"));    // false: no such node at all
    }

    // Advanced: a realistic combination -- count how many stored words share a given prefix.
    static int countWithPrefix(TrieNode node) {
        int count = node.isEndOfWord ? 1 : 0;
        for (TrieNode child : node.children.values()) count += countWithPrefix(child);
        return count;
    }

    static void advancedLevel() {
        Trie trie = new Trie();
        for (String w : new String[]{"app", "apple", "application", "apt", "bat"}) trie.insert(w);

        TrieNode prefixNode = trie.walk("app");
        int count = prefixNode == null ? 0 : countWithPrefix(prefixNode);
        System.out.println("advanced: number of stored words starting with \"app\" -> " + count);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `TrieOperations.java`, then run `java TrieOperations.java`.

## 6. Walkthrough

1. `basicLevel()` inserts `"app"` then `"apple"`. Inserting `"app"` creates four nodes (`a, p, p`) and marks the last as `isEndOfWord`. Inserting `"apple"` reuses those same three nodes, then creates two more (`l, e`), marking the final `e` node as `isEndOfWord` — while the earlier `p` node (end of `"app"`) keeps its own `isEndOfWord = true` unaffected.
2. `intermediateLevel()` calls `search` and `startsWith` on the same tree. `search("app")` walks successfully to the second `p` node and finds `isEndOfWord = true`, returning `true`. `search("appl")` walks successfully to the `l` node, but that node's `isEndOfWord` is `false` (only a prefix of `"apple"`, never inserted alone), so it returns `false`. `startsWith("appl")` performs the identical walk but skips the `isEndOfWord` check entirely, returning `true` simply because the node exists.
3. `advancedLevel()` first walks to the node representing `"app"`, then recursively counts every `isEndOfWord = true` node in that subtree — `"app"`, `"apple"`, and `"application"` all count, since all three start with `"app"`, giving a result of `3`.

## 7. Gotchas & takeaways

> Gotcha: implementing `startsWith` by copy-pasting `search` and forgetting to drop the `isEndOfWord` check is a common bug — it silently makes `startsWith` behave exactly like `search`, breaking every prefix-based feature (autocomplete, prefix counting) built on top of it.

- All three operations share one walk-down-the-tree mechanism; they differ only in what happens after the walk finishes.
- `insert` creates missing nodes as it walks; `search` and `startsWith` fail immediately if any needed node is missing.
- `search` requires both "the node exists" and "`isEndOfWord` is true"; `startsWith` requires only "the node exists."
- Related concepts: [Prefix tree (trie) structure](0126-prefix-tree-trie-structure.md), [Autocomplete & prefix queries](0130-autocomplete-prefix-queries.md).
