---
card: leetcode-patterns
gi: 522
slug: prefix-and-suffix-search
title: Prefix and Suffix Search
---

## 1. What it is

Design a class `WordFilter` that, given a list of `words`, supports `f(prefix, suffix)`: return the largest index of a word in the list that has the given `prefix` **and** the given `suffix` at the same time (return `-1` if none matches). Example: `words = ["apple"]`; `f("a", "e")` → `0` (index 0's word "apple" starts with "a" and ends with "e").

## 2. Why & when

Checking a prefix alone, or a suffix alone, is a direct trie job. Checking **both at once** for the same word needs a trick: encode each word as `suffix + '#' + prefix` (using every possible suffix), and insert all these combined strings into a single trie. Searching for `suffix + '#' + prefix` as a *prefix* of the combined string then answers "does some word have both this prefix and this suffix" in one trie walk — a specialized extension of the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family. Constraints: up to 15,000 words, up to 10,000 calls to `f`.

## 3. Core concept

**Key idea:** for each word `w` (with word index `i`), generate all `len(w) + 1` combined strings of the form `w[k:] + '#' + w` for `k` from `0` to `len(w)` (every suffix of `w`, followed by a separator, followed by the *entire* word `w` as the prefix source). Insert every one of these combined strings into a trie, storing the word's index at each node along the way (overwriting with the latest, largest index as words are processed in order, since later words should take priority in a tie).

To answer `f(prefix, suffix)`: build the query string `suffix + '#' + prefix`, and walk the trie with this exact string. If the walk succeeds all the way through, the node reached holds the largest index of a word matching both the prefix and suffix.

**Steps:**
1. For each word `w` at index `i` (processing words in order, so later indices naturally overwrite earlier ones for tie-breaking), for `k` from `0` to `w.length()`: form `combined = w.substring(k) + "#" + w`.
2. Insert `combined` into the trie, and at **every** node visited along the insertion path, set that node's stored index to `i` (not just at the final node) — every prefix of `combined` also needs the current best index recorded.
3. `f(prefix, suffix)`: walk the trie using `suffix + "#" + prefix`; if the path exists fully, return the final node's stored index; otherwise return `-1`.

**Why storing the index at *every* node along the insertion path (not just the end) is necessary:** the query string `suffix + '#' + prefix` is typically a strict prefix of some longer combined string like `w[k:] + '#' + w`, not the whole thing. Only recording the index at the final (longest) node would miss the fact that an earlier point along that same path already uniquely identifies a valid match.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Encoding every suffix-hash-word combination into one trie, indexed at every node along the way">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">word = "apple" (index 0). generate suffix#word combinations:</text>
    <text x="20" y="45" fill="#8b949e">"apple#apple", "pple#apple", "ple#apple", "le#apple", "e#apple", "#apple"</text>
    <text x="20" y="70" fill="#79c0ff">insert every one into the trie; every node along each path stores index 0</text>
    <text x="20" y="100" fill="#3fb950">f("a","e"): query string = "e#a". walk trie: e -&gt; # -&gt; a. node found, index=0 -&gt; return 0</text>
  </g>
</svg>

Encoding "suffix # prefix" and matching it as a trie prefix finds words satisfying both conditions at once.

## 5. Runnable example

```java
// WordFilter.java
import java.util.*;

public class WordFilter {

    static class TrieNode {
        TrieNode[] children = new TrieNode[27]; // 26 letters + '#'
        int index = -1;
    }

    private final TrieNode root = new TrieNode();

    public WordFilter(String[] words) {
        for (int i = 0; i < words.length; i++) {
            String word = words[i];
            for (int k = 0; k <= word.length(); k++) {
                String combined = word.substring(k) + "#" + word;
                TrieNode node = root;
                node.index = i;
                for (char c : combined.toCharArray()) {
                    int idx = (c == '#') ? 26 : c - 'a';
                    if (node.children[idx] == null) node.children[idx] = new TrieNode();
                    node = node.children[idx];
                    node.index = i; // record at every node along the path
                }
            }
        }
    }

    public int f(String prefix, String suffix) {
        String query = suffix + "#" + prefix;
        TrieNode node = root;
        for (char c : query.toCharArray()) {
            int idx = (c == '#') ? 26 : c - 'a';
            if (node.children[idx] == null) return -1;
            node = node.children[idx];
        }
        return node.index;
    }

    public static void main(String[] args) {
        WordFilter filter = new WordFilter(new String[]{"apple"});
        System.out.println(filter.f("a", "e"));  // 0
        System.out.println(filter.f("b", "e"));  // -1 (no word starts with "b")

        WordFilter filter2 = new WordFilter(new String[]{"apple", "apply", "app"});
        System.out.println(filter2.f("app", "y")); // 1 (largest index with prefix "app", suffix "y")
        System.out.println(filter2.f("app", "")); // 2 (largest index with prefix "app", any suffix -- "" matches all)
    }
}
```

**How to run:** save as `WordFilter.java`, then run `java WordFilter.java`.

## 6. Walkthrough

For `words = ["apple"]` (index 0), trace `f("a", "e")`:

1. During construction, one of the generated combined strings for "apple" (at `k=4`, since `"apple".substring(4) = "e"`) is `"e#apple"`. This gets inserted into the trie, and every node along its path (`e`, `e#`, `e#a`, `e#ap`, `e#app`, `e#appl`, `e#apple`) is stamped with `index = 0`.
2. `f("a", "e")` builds the query string `"e" + "#" + "a" = "e#a"`.
3. Walking the trie with `"e#a"` follows exactly the first 3 characters of the path created above (`e`, `e#`, `e#a`), landing on a node whose stored index is `0`.
4. Return `0`, matching the expected output — `words[0] = "apple"` starts with `"a"` and ends with `"e"`.

## 7. Gotchas & takeaways

> Gotcha: only recording the index at the *final* node of each inserted combined string (instead of every node along the path) breaks most queries, since the query string `suffix + '#' + prefix` is almost always a strict prefix of a longer combined string, not the whole thing — the answer must be readable at that intermediate node.

- Encoding "suffix # prefix" as a single trie key turns a two-condition search (prefix AND suffix) into a single prefix-matching trie walk.
- Processing words in index order and always overwriting each node's stored index means the trie naturally keeps the *largest* matching index for any tie.
- Time: O(L²) to insert one word of length L (L+1 suffixes, each up to length 2L+1), so O(total characters²) in the worst case to build; O(prefix length + suffix length) per `f` query.
