---
card: leetcode-patterns
gi: 175
slug: word-ladder
title: Word Ladder
---

## 1. What it is

Given a `beginWord`, an `endWord`, and a `wordList`, each move changes exactly one letter and the result must be a word in `wordList`. Return the number of words in the SHORTEST transformation sequence from `beginWord` to `endWord`, or `0` if none exists. Example: `beginWord = "hit"`, `endWord = "cog"`, `wordList = ["hot","dot","dog","lot","log","cog"]` → `5` (`hit → hot → dot → dog → cog`).

## 2. Why & when

Each word is a graph node; an edge connects two words that differ by exactly one letter. "Shortest transformation sequence" is shortest path in an unweighted graph — the exact signal for BFS.

## 3. Core concept

**Key idea:** BFS from `beginWord`, where a neighbor of the current word is any word in `wordList` reachable by changing exactly one character. The first time BFS reaches `endWord`, its layer number (plus 1, to count words not edges) is the answer.

**Steps:**
1. Put `wordList` in a set for O(1) lookup; if `endWord` is not in it, return `0` immediately.
2. Start BFS from `beginWord` at distance `1` (counting the word itself).
3. For each word dequeued, generate all possible one-letter variants (try every position, every letter `a`-`z`), and check if each variant is in the word set.
4. If a variant equals `endWord`, return the current distance + 1.
5. If a variant is in the set and unvisited, remove it from the set (marks visited) and enqueue it with distance + 1.
6. If the queue empties without finding `endWord`, return `0`.

**Why it is correct:** BFS explores transformation sequences in order of increasing length. The first time `endWord` is reached, no shorter sequence of one-letter changes through valid dictionary words could exist, since BFS never skips a shorter path.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS chain of one-letter word changes from hit to cog">
  <g font-family="sans-serif" font-size="12">
    <circle cx="40" cy="100" r="20" fill="#161b22" stroke="#3fb950"/><text x="40" y="104" fill="#e6edf3" text-anchor="middle">hit</text>
    <circle cx="130" cy="100" r="20" fill="#161b22" stroke="#79c0ff"/><text x="130" y="104" fill="#e6edf3" text-anchor="middle">hot</text>
    <circle cx="220" cy="100" r="20" fill="#161b22" stroke="#79c0ff"/><text x="220" y="104" fill="#e6edf3" text-anchor="middle">dot</text>
    <circle cx="310" cy="100" r="20" fill="#161b22" stroke="#79c0ff"/><text x="310" y="104" fill="#e6edf3" text-anchor="middle">dog</text>
    <circle cx="400" cy="100" r="20" fill="#161b22" stroke="#e3b341"/><text x="400" y="104" fill="#e6edf3" text-anchor="middle">cog</text>
    <line x1="60" y1="100" x2="110" y2="100" stroke="#8b949e"/>
    <line x1="150" y1="100" x2="200" y2="100" stroke="#8b949e"/>
    <line x1="240" y1="100" x2="290" y2="100" stroke="#8b949e"/>
    <line x1="330" y1="100" x2="380" y2="100" stroke="#8b949e"/>
    <text x="10" y="15" fill="#e6edf3">each edge changes exactly one letter; BFS finds the shortest 5-word chain</text>
  </g>
</svg>

Each edge represents a one-letter substitution; BFS discovers `cog` at layer 5, the minimum possible chain length.

## 5. Runnable example

```java
// WordLadder.java
import java.util.*;

public class WordLadder {

    // Level 1 -- Brute force: DFS trying every possible transformation
    // sequence, tracking the minimum length found. Correct, but DFS
    // explores far more sequences than needed and offers no early
    // stopping guarantee for "shortest" without extra pruning logic.

    // KEY INSIGHT: this is shortest-path-in-an-unweighted-graph over
    // words, where edges are "differs by one letter" -- BFS finds it
    // directly, layer by layer, guaranteeing the first hit is shortest.

    // Level 2 -- Optimal: BFS generating one-letter variants per word.
    static int ladderLength(String beginWord, String endWord, List<String> wordList) {
        Set<String> words = new HashSet<>(wordList);
        if (!words.contains(endWord)) return 0;

        Queue<String> queue = new LinkedList<>();
        queue.add(beginWord);
        int length = 1;

        while (!queue.isEmpty()) {
            int size = queue.size();
            for (int i = 0; i < size; i++) {
                String word = queue.poll();
                if (word.equals(endWord)) return length;

                char[] chars = word.toCharArray();
                for (int pos = 0; pos < chars.length; pos++) {
                    char original = chars[pos];
                    for (char c = 'a'; c <= 'z'; c++) {
                        if (c == original) continue;
                        chars[pos] = c;
                        String variant = new String(chars);
                        if (words.contains(variant)) {
                            words.remove(variant);
                            queue.add(variant);
                        }
                    }
                    chars[pos] = original;
                }
            }
            length++;
        }
        return 0;
    }

    // Level 3 -- Hardened: removing a word from `words` the moment it
    // is enqueued (not when dequeued) prevents it from being added to
    // the queue again by a different word in the same layer.

    public static void main(String[] args) {
        System.out.println(ladderLength("hit", "cog",
            Arrays.asList("hot","dot","dog","lot","log","cog"))); // 5
        System.out.println(ladderLength("hit", "cog",
            Arrays.asList("hot","dot","dog","lot","log"))); // 0
        System.out.println(ladderLength("a", "c", Arrays.asList("a","b","c"))); // 2
    }
}
```

**How to run:** `java WordLadder.java`

## 6. Walkthrough

Trace `beginWord = "hit"`, `endWord = "cog"` (using the example wordList):

| Layer | length | Words dequeued | New words found |
|---|---|---|---|
| 1 | 1 | hit | hot |
| 2 | 2 | hot | dot, lot |
| 3 | 3 | dot, lot | dog, log |
| 4 | 4 | dog, log | cog |
| 5 | 5 | cog | dequeued, equals endWord → return 5 |

Time complexity is O(N · L² · 26), where N is the word count and L is word length — for each of N words, trying 26 letters at each of L positions, each producing an O(L) string; space is O(N · L) for the word set and queue.

## 7. Gotchas & takeaways

> Checking `word.equals(endWord)` only when GENERATING variants (not when dequeuing) misses the case where `beginWord` itself equals `endWord`, or returns a length one layer too late.

- Remove a word from the set the moment it is enqueued, not when it is later dequeued — otherwise two different words in the same BFS layer can both enqueue it, wasting work (though not correctness, since the set check still gates re-adding).
- If `beginWord` is not required to be in `wordList`, it does not need to be removed from the set; only words explicitly reachable through it matter.
- Related problems: Word Ladder II (same BFS, but reconstructing ALL shortest paths via backtracking), Open the Lock (identical BFS-over-strings structure, digits instead of letters).
