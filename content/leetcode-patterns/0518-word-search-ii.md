---
card: leetcode-patterns
gi: 518
slug: word-search-ii
title: Word Search II
---

## 1. What it is

Given an `m x n` grid of characters and a list of `words`, find every word from the list that can be traced out by moving to horizontally or vertically adjacent cells, never reusing the same cell twice within one word. Example: a 4x4 grid with `words = ["oath","pea","eat","rain"]` → `["eat","oath"]`.

## 2. Why & when

Searching for many words at once in a grid, where words share prefixes, is a textbook case for combining a trie with backtracking DFS — the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family's "autocomplete" idea applied to grid traversal. Running a separate DFS per word (checking against each word individually) repeats work on shared prefixes; a single trie lets one DFS explore all words simultaneously, pruning any branch that no longer matches *any* word's prefix. Constraints: up to 12x12 grid, up to 30,000 words total across all characters.

## 3. Core concept

**Key idea:** insert every word into a trie. From each grid cell, start a DFS that walks the trie in lockstep with the grid: at each step, only continue exploring a neighbor if the trie has a child matching that neighbor's letter. Whenever the current trie node marks `isEnd`, a whole word has been found — record it and mark that trie node as already found (to avoid reporting duplicates).

**Steps:**
1. Insert all words into a trie; store the full word string at each `isEnd` node (for easy retrieval), instead of just a boolean.
2. For each grid cell `(r, c)`, start a DFS if the root has a child matching `grid[r][c]`.
3. In the DFS: if the current trie node has a stored word, add it to the results and clear the stored word (to prevent duplicate reporting).
4. Mark the current grid cell as visited (e.g. temporarily overwrite it with a sentinel character), then recurse into all 4 neighbors whose letter matches a child of the current trie node.
5. Restore the grid cell after recursing (backtrack), so other DFS paths can still use it.

**Why clearing a found word's slot (instead of just recording it once) matters for correctness:** a word can be traceable through more than one path in the grid. Without clearing `next.word` to `null` after the first report, the same word could be added to the results multiple times. As a further optimization beyond this base solution, a node with no children and no stored word left can also be unlinked from its parent, so later DFS calls stop walking down that now-useless branch entirely.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DFS through the grid constrained by a trie, so all words are searched for simultaneously">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">grid DFS constrained by trie children (searching for "oath", "eat", ...)</text>
    <text x="20" y="45" fill="#8b949e">start at cell 'o': trie has child 'o' -&gt; continue</text>
    <text x="20" y="65" fill="#8b949e">neighbor 'a': trie node 'o' has child 'a' -&gt; continue</text>
    <text x="20" y="85" fill="#8b949e">neighbor 't': trie node 'oa' has child 't' -&gt; continue</text>
    <text x="20" y="105" fill="#3fb950">neighbor 'h': trie node 'oat' has child 'h', and 'oath' node has isEnd -&gt; found "oath"</text>
    <text x="20" y="135" fill="#f0883e">any neighbor with no matching trie child is pruned immediately -&gt; no wasted exploration</text>
  </g>
</svg>

The trie constrains which grid neighbors are worth exploring, pruning paths that cannot lead to any word.

## 5. Runnable example

```java
// WordSearchII.java
import java.util.*;

public class WordSearchII {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        String word = null; // non-null exactly at nodes where a word ends
    }

    static List<String> findWords(char[][] board, String[] words) {
        TrieNode root = new TrieNode();
        for (String word : words) {
            TrieNode node = root;
            for (char c : word.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            node.word = word;
        }

        List<String> result = new ArrayList<>();
        int rows = board.length, cols = board[0].length;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                dfs(board, r, c, root, result);
            }
        }
        return result;
    }

    static void dfs(char[][] board, int r, int c, TrieNode node, List<String> result) {
        if (r < 0 || r >= board.length || c < 0 || c >= board[0].length) return;
        char ch = board[r][c];
        if (ch == '#' || node.children[ch - 'a'] == null) return;

        TrieNode next = node.children[ch - 'a'];
        if (next.word != null) {
            result.add(next.word);
            next.word = null; // avoid duplicate reporting
        }

        board[r][c] = '#'; // mark visited
        dfs(board, r + 1, c, next, result);
        dfs(board, r - 1, c, next, result);
        dfs(board, r, c + 1, next, result);
        dfs(board, r, c - 1, next, result);
        board[r][c] = ch; // backtrack
    }

    public static void main(String[] args) {
        char[][] board = {
            {'o', 'a', 'a', 'n'},
            {'e', 't', 'a', 'e'},
            {'i', 'h', 'k', 'r'},
            {'i', 'f', 'l', 'v'}
        };
        String[] words = {"oath", "pea", "eat", "rain"};
        System.out.println(findWords(board, words));
        // [oath, eat] (order may vary)
    }
}
```

**How to run:** save as `WordSearchII.java`, then run `java WordSearchII.java`.

## 6. Walkthrough

Trace the DFS starting at cell `(0,0)` = `'o'`, searching for `"oath"`:

| step | cell | letter | trie node reached | word found? |
|---|---|---|---|---|
| 1 | (0,0) | o | root -> o | no |
| 2 | (0,1) | a | o -> a | no |
| 3 | (1,1) | t | o -> a -> t | no |
| 4 | (2,1) | h | o -> a -> t -> h | **yes, "oath"** |

(The DFS also tries the neighbor `(1,0)='e'` from `(0,0)`, but the trie's `o` node has no child `e`, so that branch is pruned immediately without further exploration.)

The path `(0,0) -> (0,1) -> (1,1) -> (2,1)` spells `"oath"`, matching a stored word at that trie node — it is added to the result and the node's `word` is cleared.

## 7. Gotchas & takeaways

> Gotcha: forgetting to restore `board[r][c]` after the recursive calls (skipping the backtrack step) leaves cells permanently marked as visited, breaking every subsequent DFS that should be able to reuse that cell for a different word or starting position.

- One trie built once serves every starting cell's DFS, instead of repeating a separate word-by-word search for each of up to 30,000 words.
- Clearing a trie node's `word` field after reporting it prevents the same word from being added to the result more than once.
- Time: O(rows · cols · 4^L) worst case, where L is the longest word length — pruning the trie as branches are exhausted keeps this fast in practice.
