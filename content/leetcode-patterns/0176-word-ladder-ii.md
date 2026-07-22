---
card: leetcode-patterns
gi: 176
slug: word-ladder-ii
title: Word Ladder II
---

## 1. What it is

Given `beginWord`, `endWord`, and `wordList`, return ALL shortest transformation sequences from `beginWord` to `endWord`, where each step changes one letter and must land on a word in `wordList`. Example: `beginWord = "hit"`, `endWord = "cog"`, `wordList = ["hot","dot","dog","lot","log","cog"]` → `[["hit","hot","dot","dog","cog"],["hit","hot","lot","log","cog"]]`.

## 2. Why & when

This is Word Ladder's sibling: instead of just the SHORTEST LENGTH, you need every path of that length. A single BFS cannot record multiple parents per node, so this needs two phases: BFS to discover the shortest distance layer-by-layer AND every word's possible parents, then DFS/backtracking over that parent map to reconstruct all shortest paths.

## 3. Core concept

**Key idea:** BFS from `beginWord`, but instead of stopping at the first hit, record for every word ALL the words in the previous layer that can reach it (multiple parents). Once BFS finishes (or reaches `endWord`'s layer), DFS backward from `endWord` through the parent map, building every path back to `beginWord`.

**Steps:**
1. Build a `parents` map: `word -> list of words in the layer immediately before it`, discovered via layer-by-layer BFS from `beginWord`.
2. Within a single BFS layer, only remove a word from the "available" set AFTER the whole layer finishes processing (so multiple same-layer words can all point to the same next-layer word as a parent).
3. Stop BFS once the layer containing `endWord` has been fully processed (no need to search farther, since further layers cannot be part of a SHORTEST path).
4. DFS from `endWord` backward through `parents`, building each path in reverse and reversing it before adding to results, until `beginWord` is reached.
5. Return the collected paths, or an empty list if `endWord` was never reached.

**Why it is correct:** BFS layers guarantee that any word's parents (words one layer earlier that can reach it) lie on SOME shortest path. Backtracking through every recorded parent, from `endWord` to `beginWord`, enumerates exactly the paths that use only shortest-distance edges — no longer path can be reconstructed this way, since parents only exist one layer back.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BFS records multiple parents per word; DFS backtracks through parent map to enumerate all shortest paths">
  <g font-family="sans-serif" font-size="12">
    <circle cx="230" cy="60" r="18" fill="#161b22" stroke="#e3b341"/><text x="230" y="64" fill="#e6edf3" text-anchor="middle">dog</text>
    <circle cx="150" cy="130" r="18" fill="#161b22" stroke="#79c0ff"/><text x="150" y="134" fill="#e6edf3" text-anchor="middle">dot</text>
    <circle cx="310" cy="130" r="18" fill="#161b22" stroke="#79c0ff"/><text x="310" y="134" fill="#e6edf3" text-anchor="middle">log</text>
    <line x1="215" y1="75" x2="163" y2="118" stroke="#8b949e" marker-end="url(#a3)"/>
    <line x1="245" y1="75" x2="297" y2="118" stroke="#8b949e" marker-end="url(#a3)"/>
    <defs><marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
    <text x="10" y="15" fill="#e6edf3">"dog" has TWO parents: "dot" and "log" -- both belong to shortest paths</text>
  </g>
</svg>

`dog` has two valid parents from the previous BFS layer; DFS backtracking must follow both branches to find every shortest path.

## 5. Runnable example

```java
// WordLadderII.java
import java.util.*;

public class WordLadderII {

    // Level 1 -- Brute force: DFS every possible transformation
    // sequence up to some bound, keeping only those matching the
    // globally shortest length (found via a separate BFS pass first).
    // Correct, but re-explores huge portions of the search space that
    // a parent-map lookup would skip entirely.

    // KEY INSIGHT: BFS naturally discovers, for each word, exactly
    // which PREVIOUS-layer words could have produced it -- recording
    // that as a parent map turns "search for all shortest paths" into
    // a much smaller backtrack over only the edges BFS already proved
    // are shortest-path edges.

    // Level 2 -- Optimal: layered BFS building a parent map, then DFS
    // backtracking from endWord.
    static List<List<String>> findLadders(String beginWord, String endWord, List<String> wordList) {
        Set<String> dict = new HashSet<>(wordList);
        List<List<String>> result = new ArrayList<>();
        if (!dict.contains(endWord)) return result;

        Map<String, List<String>> parents = new HashMap<>();
        Set<String> currentLayer = new HashSet<>();
        currentLayer.add(beginWord);
        dict.remove(beginWord);
        boolean found = false;

        while (!currentLayer.isEmpty() && !found) {
            Set<String> nextLayer = new HashSet<>();
            Set<String> toRemove = new HashSet<>();
            for (String word : currentLayer) {
                char[] chars = word.toCharArray();
                for (int pos = 0; pos < chars.length; pos++) {
                    char original = chars[pos];
                    for (char c = 'a'; c <= 'z'; c++) {
                        if (c == original) continue;
                        chars[pos] = c;
                        String variant = new String(chars);
                        if (dict.contains(variant)) {
                            nextLayer.add(variant);
                            toRemove.add(variant);
                            parents.computeIfAbsent(variant, k -> new ArrayList<>()).add(word);
                            if (variant.equals(endWord)) found = true;
                        }
                    }
                    chars[pos] = original;
                }
            }
            dict.removeAll(toRemove);
            currentLayer = nextLayer;
        }

        if (found) {
            LinkedList<String> path = new LinkedList<>();
            path.add(endWord);
            backtrack(endWord, beginWord, parents, path, result);
        }
        return result;
    }

    static void backtrack(String word, String beginWord, Map<String, List<String>> parents,
                           LinkedList<String> path, List<List<String>> result) {
        if (word.equals(beginWord)) {
            result.add(new ArrayList<>(path));
            return;
        }
        for (String parent : parents.getOrDefault(word, Collections.emptyList())) {
            path.addFirst(parent);
            backtrack(parent, beginWord, parents, path, result);
            path.removeFirst();
        }
    }

    // Level 3 -- Hardened: words are removed from `dict` only AFTER
    // the whole layer finishes (via `toRemove`), so two words in the
    // SAME layer can both correctly record the same next-layer word as
    // a parent, instead of racing to claim it first.

    public static void main(String[] args) {
        System.out.println(findLadders("hit", "cog",
            Arrays.asList("hot","dot","dog","lot","log","cog")));
        // [[hit, hot, dot, dog, cog], [hit, hot, lot, log, cog]]
        System.out.println(findLadders("hit", "cog",
            Arrays.asList("hot","dot","dog","lot","log"))); // []
    }
}
```

**How to run:** `java WordLadderII.java`

## 6. Walkthrough

Trace layers for `beginWord = "hit"`, `endWord = "cog"`:

| Layer | Words | Parents recorded |
|---|---|---|
| 0 | hit | — |
| 1 | hot | hot ← hit |
| 2 | dot, lot | dot ← hot; lot ← hot |
| 3 | dog, log | dog ← dot; log ← lot |
| 4 | cog | cog ← dog; cog ← log; `found = true`, stop |

Backtrack from `cog`: `cog ← dog ← dot ← hot ← hit` and `cog ← log ← lot ← hot ← hit`, reversed to give both paths. Time complexity is O(N · L² · 26) for the BFS phase plus the cost of enumerating all shortest paths in the backtrack phase, which can itself be exponential in the worst case; space is O(N · L) for the parent map.

## 7. Gotchas & takeaways

> Removing a word from `dict` as soon as it is found (inside the per-word loop, not after the whole layer) prevents a SECOND same-layer word from also recording it as a child, silently dropping valid shortest paths.

- The `toRemove` set — deferring dictionary removal until the layer completes — is the detail that makes multi-parent recording correct.
- Stop BFS as soon as `endWord` is found in a layer; continuing further layers wastes work, since those words can no longer be part of a SHORTEST path.
- Related problems: Word Ladder (same BFS, but single shortest length only), All Paths From Source to Target (DFS backtracking to enumerate every path, no BFS pre-filtering needed since the graph is small and acyclic).
