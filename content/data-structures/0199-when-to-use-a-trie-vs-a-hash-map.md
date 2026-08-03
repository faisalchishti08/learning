---
card: data-structures
gi: 199
slug: when-to-use-a-trie-vs-a-hash-map
title: When to use a trie vs a hash map
---

## 1. What it is

A [trie](0126-prefix-tree-trie-structure.md) and a `HashMap<String, V>` both store strings and their associated values, but they answer very different questions efficiently. A hash map answers "does this **exact** string exist?" in `O(1)` average. A trie answers "what strings share this **prefix**?" — something a hash map cannot do without scanning every entry.

## 2. Why & when

Use a `HashMap<String, V>` for exact-match lookups: a dictionary of known words, a cache keyed by full strings, checking membership in a fixed set. Use a trie specifically when prefix operations matter: autocomplete ("show all words starting with 'pre'"), IP routing tables (longest-prefix match), or spell-checkers that need to explore "nearby" words character by character.

## 3. Core concept

**The decision criteria.**
- **Do you only ever check for exact string matches?** → `HashMap`. Simpler, and typically faster in raw constant-factor terms for pure exact lookup.
- **Do you need "all strings starting with X" (autocomplete, prefix search)?** → trie. A `HashMap` would need to scan every key checking `startsWith`, costing `O(n * average key length)`.
- **Do you have many strings that share long common prefixes?** → trie can save memory, since shared prefixes are stored once, as shared path segments, rather than duplicated inside every full string key.
- **Is your string alphabet small and fixed (lowercase letters, digits)?** → a trie's array-based children (one slot per possible character) works well. For a large or unbounded alphabet (arbitrary Unicode), a trie's children are usually a `HashMap<Character, Node>` instead, which narrows the memory advantage.

**Why a hash map cannot do prefix search efficiently.** A `HashMap`'s bucket placement is derived from a string's **full** hash code — two strings sharing a prefix (`"apple"`, `"application"`) can hash to completely unrelated buckets, with no structural relationship between them at all. Answering "all keys starting with 'app'" requires checking every single key's prefix individually — an unavoidable `O(n)` scan, regardless of how the hash map internally organizes its buckets.

**Why a trie makes prefix search fast.** A trie stores each string as a path from the root, one node per character, with shared prefixes literally sharing the same nodes. Finding "all strings starting with 'app'" means: walk the 3 nodes for `'a'`, `'p'`, `'p'` (a cost proportional only to the prefix length, `O(prefix length)`), then explore every path below that point — visiting exactly the matching strings, and nothing else.

**The memory tradeoff.** A trie's per-node overhead (a node object per character, often with an array or map of child pointers) means storing a small number of unrelated, short strings can use **more** memory in a trie than the equivalent `HashMap` — the trie's advantage only shows up when many strings share long prefixes, amortizing that per-node cost across shared paths.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A HashMap with unrelated bucket placement for similar strings, versus a trie where shared prefixes share the same path">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">HashMap: unrelated bucket placement</text>
    <rect x="20" y="30" width="80" height="24" fill="#0d1117" stroke="#8b949e"/><text x="60" y="46" text-anchor="middle" font-size="8">bucket 3: apple</text>
    <rect x="120" y="30" width="100" height="24" fill="#0d1117" stroke="#8b949e"/><text x="170" y="46" text-anchor="middle" font-size="8">bucket 17: application</text>
    <text x="10" y="80" font-size="9" fill="#f0883e">"all keys starting with app" -&gt; must check every bucket</text>

    <text x="10" y="120">Trie: shared prefix, shared path</text>
    <circle cx="60" cy="150" r="12" fill="#161b22" stroke="#3fb950"/><text x="60" y="154" text-anchor="middle" font-size="8">a</text>
    <circle cx="110" cy="150" r="12" fill="#161b22" stroke="#3fb950"/><text x="110" y="154" text-anchor="middle" font-size="8">p</text>
    <circle cx="160" cy="150" r="12" fill="#161b22" stroke="#3fb950"/><text x="160" y="154" text-anchor="middle" font-size="8">p</text>
    <line x1="72" y1="150" x2="98" y2="150" stroke="#3fb950"/>
    <line x1="122" y1="150" x2="148" y2="150" stroke="#3fb950"/>
    <circle cx="220" cy="130" r="10" fill="#0d1117" stroke="#8b949e"/><text x="220" y="134" text-anchor="middle" font-size="7">l..e (apple)</text>
    <circle cx="220" cy="170" r="10" fill="#0d1117" stroke="#8b949e"/><text x="220" y="174" text-anchor="middle" font-size="7">l..n (application)</text>
    <line x1="172" y1="145" x2="210" y2="130" stroke="#3fb950"/>
    <line x1="172" y1="155" x2="210" y2="170" stroke="#3fb950"/>
    <text x="10" y="195" font-size="9" fill="#3fb950">walk "app" once (3 hops), then explore both branches</text>
  </g>
</svg>

Hash buckets scatter similar strings randomly; a trie's shared path makes prefix search direct.

## 5. Runnable example

```java
// TrieVsHashMap.java
import java.util.*;

public class TrieVsHashMap {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        boolean isWord = false;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode node = root;
            for (char c : word.toCharArray()) {
                node = node.children.computeIfAbsent(c, k -> new TrieNode());
            }
            node.isWord = true;
        }

        List<String> wordsWithPrefix(String prefix) {
            List<String> results = new ArrayList<>();
            TrieNode node = root;
            for (char c : prefix.toCharArray()) {
                node = node.children.get(c);
                if (node == null) return results; // no words with this prefix at all
            }
            collectWords(node, new StringBuilder(prefix), results);
            return results;
        }

        void collectWords(TrieNode node, StringBuilder current, List<String> results) {
            if (node.isWord) results.add(current.toString());
            for (Map.Entry<Character, TrieNode> entry : node.children.entrySet()) {
                current.append(entry.getKey());
                collectWords(entry.getValue(), current, results);
                current.deleteCharAt(current.length() - 1);
            }
        }
    }

    // Basic: exact match, both structures work identically well.
    static void basicLevel() {
        Map<String, Integer> hashMap = new HashMap<>();
        hashMap.put("apple", 1);
        hashMap.put("application", 2);

        System.out.println("basic: HashMap exact lookup -> " + hashMap.get("apple"));
    }

    // Intermediate: prefix search, where the trie's advantage becomes clear.
    static void intermediateLevel() {
        Trie trie = new Trie();
        for (String word : new String[]{"apple", "application", "apply", "banana", "band"}) trie.insert(word);

        System.out.println("intermediate: words with prefix 'app' -> " + trie.wordsWithPrefix("app"));
        System.out.println("intermediate: words with prefix 'ban' -> " + trie.wordsWithPrefix("ban"));
    }

    // Advanced: the same prefix search using only a HashMap, showing the O(n) scan it forces.
    static List<String> prefixSearchViaHashMap(Set<String> words, String prefix) {
        List<String> results = new ArrayList<>();
        for (String word : words) { // must check every single word -- no shortcut available
            if (word.startsWith(prefix)) results.add(word);
        }
        return results;
    }

    static void advancedLevel() {
        Set<String> words = Set.of("apple", "application", "apply", "banana", "band");
        System.out.println("advanced: HashMap-based prefix search (O(n) scan) -> " + prefixSearchViaHashMap(words, "app"));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java TrieVsHashMap.java`

## 6. Walkthrough

For exact-match lookup (`basicLevel`), a `HashMap` answers `get("apple")` in `O(1)` average — there is no reason to reach for a trie here at all; it would only add complexity for no benefit.

For prefix search (`intermediateLevel`), insert `"apple", "application", "apply", "banana", "band"` into the trie. `wordsWithPrefix("app")` first walks the 3 nodes for `'a'`, `'p'`, `'p'` — a cost of exactly `3` steps, regardless of how many total words the trie holds. From that node, `collectWords` explores every remaining path, correctly finding `["apple", "application", "apply"]` and nothing from the unrelated `"banana"`/`"band"` branch, which shares no path with `"app"` at all.

The `advancedLevel` version does the logically identical prefix search using only a `HashMap`-backed `Set<String>`. Since a hash-based structure has no notion of shared prefixes in its bucket layout, `prefixSearchViaHashMap` has no choice but to check `word.startsWith(prefix)` against **every single word** in the set — for `5` words this is trivial, but for a dictionary of a million words, this becomes a full million-word scan for every single prefix query, versus the trie's cost proportional only to the prefix length plus the number of matches.

**Complexity.** `HashMap`: exact lookup `O(1)` average; prefix search `O(n * average key length)` (must check every key). Trie: exact lookup `O(key length)`; prefix search `O(prefix length + number of matching words)` — dramatically better when there are many total words but few matches.

## 7. Gotchas & takeaways

> Do not reach for a trie just because a workload involves strings — if prefix matching is never actually needed, a `HashMap` is simpler and often faster in raw constant-factor terms for pure exact-match lookups.

- A trie's memory advantage depends on shared prefixes existing in the actual data — a set of short, mostly-unrelated strings can use **more** memory in a trie (due to per-node overhead) than the equivalent `HashMap`.
- Using a `HashMap<Character, TrieNode>` for children (as in the example above) supports any Unicode alphabet at the cost of some memory and constant-factor overhead per node; using a fixed-size array (e.g. `TrieNode[26]` for lowercase English letters) is faster and more memory-efficient when the alphabet is small and known in advance.
- For "longest matching prefix" style problems (IP routing, phone number matching), a trie is the standard, well-suited tool — this pattern comes up frequently enough in networking and telecom systems that it is worth recognizing on sight.
