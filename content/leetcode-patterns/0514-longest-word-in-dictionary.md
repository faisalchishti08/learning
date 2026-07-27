---
card: leetcode-patterns
gi: 514
slug: longest-word-in-dictionary
title: Longest Word in Dictionary
---

## 1. What it is

Given an array of `words`, find the longest word that can be built one character at a time by other words in the list (every prefix of the word, of every length, must also exist somewhere in `words`). If there are multiple such words of the same longest length, return the lexicographically smallest one. Example: `words = ["w","wo","wor","worl","world"]` → `"world"` (every prefix "w", "wo", "wor", "worl" is also present).

## 2. Why & when

"Every prefix of this word must also be a word in the list" is a "buildable path" condition on a trie, part of the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family — insert every word, then find the longest path from the root where **every** node along the way (not just the final one) is marked `isEnd`. Constraints: up to 1000 words, each up to 105 characters.

## 3. Core concept

**Key idea:** insert all words into a trie. Then explore the trie with a depth-first search (or breadth-first search) that only continues into a child if that child's node is marked `isEnd` — a node representing an intermediate prefix that is not itself a complete word is a dead end, since building past it would create a word with a missing prefix.

**Steps:**
1. Insert every word into a trie.
2. Do a DFS from the root. At each node, only recurse into children whose `isEnd` is `true` (this enforces the "every prefix must exist" rule one level at a time).
3. Track the best word found so far: prefer a longer word; if lengths tie, prefer the lexicographically smaller one.
4. To make the "lexicographically smallest" tie-break automatic, process a node's children in alphabetical order (`a` to `z`) and only update the best answer with a strict "longer than" comparison (never replacing on a tie), so the first (alphabetically smallest) word found at the longest length wins.

**Why only recursing into `isEnd` children enforces the buildability rule:** a word is "buildable" exactly when every one of its prefixes (of every length) is also in the dictionary. Refusing to step into a child unless it itself completes a valid word guarantees that every character added along the DFS path corresponds to a real, already-verified word — never skipping past a missing prefix.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS only continuing through nodes marked as complete words">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">words = [w, wo, wor, worl, world]</text>
    <text x="20" y="45" fill="#8b949e">w(isEnd) -&gt; wo(isEnd) -&gt; wor(isEnd) -&gt; worl(isEnd) -&gt; world(isEnd)</text>
    <text x="20" y="70" fill="#3fb950">every step is a complete word -&gt; "world" is fully buildable, length 5</text>
    <text x="20" y="100" fill="#f0883e">if "worl" were missing from the list: DFS could not step past "wor"</text>
    <text x="20" y="120" fill="#f0883e">-&gt; "world" (and "worl") would be rejected as not buildable</text>
  </g>
</svg>

The DFS only advances through nodes that are themselves complete words, one prefix length at a time.

## 5. Runnable example

```java
// LongestWordInDictionary.java
import java.util.*;

public class LongestWordInDictionary {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    static void insert(TrieNode root, String word) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            int index = c - 'a';
            if (node.children[index] == null) node.children[index] = new TrieNode();
            node = node.children[index];
        }
        node.isEnd = true;
    }

    static String best = "";

    static void dfs(TrieNode node, StringBuilder path) {
        String current = path.toString();
        if (current.length() > best.length()
            || (current.length() == best.length() && current.compareTo(best) < 0 && !current.isEmpty())) {
            if (!current.isEmpty()) best = current;
        }
        for (int i = 0; i < 26; i++) {
            TrieNode child = node.children[i];
            if (child != null && child.isEnd) {
                path.append((char) ('a' + i));
                dfs(child, path);
                path.deleteCharAt(path.length() - 1);
            }
        }
    }

    static String longestWord(String[] words) {
        TrieNode root = new TrieNode();
        for (String word : words) insert(root, word);
        best = "";
        dfs(root, new StringBuilder());
        return best;
    }

    public static void main(String[] args) {
        System.out.println(longestWord(new String[]{"w", "wo", "wor", "worl", "world"})); // world
        System.out.println(longestWord(new String[]{"a", "banana", "app", "appl", "ap", "apply", "apple"})); // apple
        System.out.println(longestWord(new String[]{"abc"})); // "" (missing prefixes "a", "ab")
    }
}
```

**How to run:** save as `LongestWordInDictionary.java`, then run `java LongestWordInDictionary.java`.

## 6. Walkthrough

For `words = ["w", "wo", "wor", "worl", "world"]`, the DFS explores in alphabetical child order (only one branch exists here):

| path so far | node.isEnd | continue? | best updated |
|---|---|---|---|
| "w" | true | yes | best = "w" (length 1) |
| "wo" | true | yes | best = "wo" (length 2) |
| "wor" | true | yes | best = "wor" (length 3) |
| "worl" | true | yes | best = "worl" (length 4) |
| "world" | true | no more children | best = "world" (length 5) |

Final answer: `"world"`, matching the expected output. For `["abc"]`, the DFS reaches node `"a"` — but `"a"` was never inserted as its own word, so `isEnd` is `false` there, and the DFS never advances past the root at all, giving `""`.

## 7. Gotchas & takeaways

> Gotcha: exploring every trie node (not just `isEnd` ones) and checking buildability only at the end misses the point of the problem — a word can only be "buildable" if the DFS path itself never passes through a non-word node, so the `isEnd` check must gate *every* recursive step, not just the final one.

- Processing children in alphabetical order and only replacing `best` on a strictly longer match automatically produces the lexicographically smallest word among ties.
- A single missing prefix anywhere breaks buildability for every longer word built on top of it.
- Time: O(total characters across all words) — the trie is built once, and the DFS visits each node at most once.
