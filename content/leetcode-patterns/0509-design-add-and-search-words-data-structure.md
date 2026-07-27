---
card: leetcode-patterns
gi: 509
slug: design-add-and-search-words-data-structure
title: Design Add and Search Words Data Structure
---

## 1. What it is

Design a data structure supporting `addWord(word)` and `search(word)`, where `search` may contain the wildcard character `.`, matching any single letter. Example: after adding `"bad"`, `"dad"`, `"mad"`, `search("pad")` → `false`, `search(".ad")` → `true`, `search("b..")` → `true`.

## 2. Why & when

This extends the [Implement Trie](0508-implement-trie-prefix-tree.md) structure with wildcard support. A plain iterative walk cannot handle `.`, since it might match any of up to 26 children — the search must become recursive, branching into every child whenever a wildcard is encountered. Constraints: up to 50,000 words added, up to 2 million total characters across all `search` calls, word length up to 25 (with up to 2 wildcards typically appearing per constraints on harder variants).

## 3. Core concept

**Key idea:** build a standard trie for `addWord`, identical to [Implement Trie](0508-implement-trie-prefix-tree.md). For `search`, write a recursive helper that takes the current trie node and the remaining suffix of the word to match. At each character: if it is a regular letter, follow that single child (fail if missing). If it is `.`, try **every** non-null child recursively — the match succeeds if *any* branch eventually succeeds.

**Steps:**
1. `addWord`: identical trie insertion as before.
2. `search(word)`: call a recursive helper `matchFrom(node, word, index)`.
3. Base case: if `index == word.length()`, return `node.isEnd`.
4. If `word.charAt(index)` is a regular letter: look up that one child; if missing, return `false`; otherwise recurse into it with `index + 1`.
5. If `word.charAt(index)` is `.`: loop over all 26 possible children; for each non-null child, recursively try `matchFrom(child, word, index + 1)`; return `true` as soon as any branch succeeds, `false` if none do.

**Why this must be recursive (not the iterative walk from a plain trie):** a `.` does not pick one path — it potentially opens up to 26 different paths, each of which must be explored independently, since a later character in the word might only match through one specific branch. Recursion naturally explores all of them and backtracks when a branch fails.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A wildcard character branching the recursive search into every child node">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">words added: bad, dad, mad. search(".ad")</text>
    <circle cx="350" cy="20" r="14" fill="#161b22" stroke="#79c0ff"/>
    <text x="350" y="25" fill="#e6edf3" text-anchor="middle" font-size="11">root</text>
    <line x1="350" y1="34" x2="250" y2="65" stroke="#8b949e"/>
    <line x1="350" y1="34" x2="350" y2="65" stroke="#8b949e"/>
    <line x1="350" y1="34" x2="450" y2="65" stroke="#8b949e"/>
    <circle cx="250" cy="75" r="14" fill="#161b22" stroke="#f0883e"/>
    <text x="250" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">b</text>
    <circle cx="350" cy="75" r="14" fill="#161b22" stroke="#f0883e"/>
    <text x="350" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">d</text>
    <circle cx="450" cy="75" r="14" fill="#161b22" stroke="#f0883e"/>
    <text x="450" y="80" fill="#e6edf3" text-anchor="middle" font-size="11">m</text>
    <text x="20" y="120" fill="#8b949e">'.' tries all 3 children (b, d, m) in parallel branches</text>
    <text x="20" y="145" fill="#3fb950">each branch continues with "ad" -&gt; a -&gt; d(isEnd) -&gt; found a match -&gt; true</text>
  </g>
</svg>

A wildcard fans out into every existing child; the search succeeds if any single branch completes the match.

## 5. Runnable example

```java
// WordDictionary.java
public class WordDictionary {

    private static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    private final TrieNode root = new TrieNode();

    public void addWord(String word) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) node.children[index] = new TrieNode();
            node = node.children[index];
        }
        node.isEnd = true;
    }

    public boolean search(String word) {
        return matchFrom(root, word, 0);
    }

    private boolean matchFrom(TrieNode node, String word, int index) {
        if (node == null) return false;
        if (index == word.length()) return node.isEnd;

        char c = word.charAt(index);
        if (c != '.') {
            return matchFrom(node.children[c - 'a'], word, index + 1);
        }

        // wildcard: try every non-null child
        for (TrieNode child : node.children) {
            if (child != null && matchFrom(child, word, index + 1)) {
                return true;
            }
        }
        return false;
    }

    public static void main(String[] args) {
        WordDictionary dict = new WordDictionary();
        dict.addWord("bad");
        dict.addWord("dad");
        dict.addWord("mad");

        System.out.println(dict.search("pad"));  // false
        System.out.println(dict.search("bad"));  // true
        System.out.println(dict.search(".ad"));  // true
        System.out.println(dict.search("b.."));  // true
    }
}
```

**How to run:** save as `WordDictionary.java`, then run `java WordDictionary.java`.

## 6. Walkthrough

Trace `search(".ad")` after adding `"bad"`, `"dad"`, `"mad"`:

| call | node | index | char | action |
|---|---|---|---|---|
| matchFrom(root, ".ad", 0) | root | 0 | `.` | try children b, d, m |
| matchFrom(b, ".ad", 1) | b | 1 | `a` | regular letter, go to b->a |
| matchFrom(a, ".ad", 2) | a (under b) | 2 | `d` | regular letter, go to a->d |
| matchFrom(d, ".ad", 3) | d (under b->a) | 3 | index==length | return d.isEnd = true |

The first branch tried (`b`) already succeeds, so `search(".ad")` returns `true` without needing to try the `d` or `m` branches.

## 7. Gotchas & takeaways

> Gotcha: returning `false` as soon as one child branch of a wildcard fails, instead of trying the remaining children, misses valid matches — a wildcard must try every child and only fail if *all* of them fail.

- Builds directly on [Implement Trie](0508-implement-trie-prefix-tree.md); `addWord` is unchanged, only `search` becomes recursive to support `.`.
- Each `.` can fan out into up to 26 recursive branches, so worst-case time is exponential in the number of wildcards — acceptable given the problem's small word-length constraint.
- Time: O(26^d · L) worst case, where d is the number of wildcards and L is the word length; O(L) when there are no wildcards.
