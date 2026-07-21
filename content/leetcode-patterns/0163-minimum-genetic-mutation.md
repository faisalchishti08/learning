---
card: leetcode-patterns
gi: 163
slug: minimum-genetic-mutation
title: Minimum Genetic Mutation
---

## 1. What it is

A gene string has length 8 and uses only characters `A`, `C`, `G`, `T`. A single mutation changes exactly one character. Given a `startGene`, an `endGene`, and a `bank` of valid intermediate gene strings (every mutation along the way must be a string that exists in `bank`), return the minimum number of mutations to turn `startGene` into `endGene`, or `-1` if impossible. Example: `startGene = "AACCGGTT"`, `endGene = "AACCGGTA"`, `bank = ["AACCGGTA"]` → `1`.

## 2. Why & when

"Minimum number of transformations/mutations/steps" where each step is a single allowed change is the same signature as Snakes and Ladders and Word Ladder-style problems: treat each valid gene string as a graph node, with an edge between two genes if they differ by exactly one character. BFS from `startGene` finds the shortest sequence of single-character mutations to reach `endGene`, since every edge (mutation) costs exactly one step.

## 3. Core concept

**Key idea:** BFS from `startGene`. At each gene, generate every possible one-character mutation (try all 4 letters at each of the 8 positions) and check if the result is in `bank` and not yet visited — if so, it is a valid neighbor, one mutation away.

**Steps:**
1. Put every string in `bank` into a `HashSet` for O(1) lookup (and to allow removing visited ones, or use a separate `visited` set).
2. If `endGene` is not in `bank`, return `-1` immediately (it can never be reached, since every intermediate AND final gene must be in `bank`).
3. BFS from `startGene`: enqueue it with `mutations = 0`.
4. Dequeue `current`. If `current == endGene`, return the recorded mutation count.
5. For each position `0..7`, and each of the 4 possible letters: build the candidate string with that one position changed. If the candidate is in `bank` and not visited, mark it visited and enqueue it with `mutations + 1`.
6. If the queue empties without finding `endGene`, return `-1`.

**Why it is correct:** each single-character change costs exactly one mutation (an unweighted edge), so BFS's guarantee — the first time a node is dequeued, it was reached via the fewest possible edges — directly translates to "the first time `endGene` is dequeued, it was reached via the fewest possible mutations."

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each valid one-character mutation is an edge in the gene graph">
  <g font-family="sans-serif" font-size="11">
    <rect x="20" y="30" width="110" height="26" fill="#161b22" stroke="#3fb950"/><text x="75" y="47" fill="#e6edf3" text-anchor="middle">AACCGGTT</text>
    <rect x="180" y="30" width="110" height="26" fill="#161b22" stroke="#79c0ff"/><text x="235" y="47" fill="#e6edf3" text-anchor="middle">AACCGGTA</text>
    <line x1="132" y1="43" x2="178" y2="43" stroke="#8b949e"/>
    <text x="135" y="35" fill="#8b949e" font-size="10">1 mutation (last char T-&gt;A)</text>
    <text x="10" y="90" fill="#e6edf3">Trying all 4 letters at each of 8 positions generates every possible one-mutation neighbor.</text>
    <text x="10" y="115" fill="#e6edf3">Only neighbors present in "bank" are valid graph edges -- others are discarded candidates.</text>
    <text x="10" y="145" fill="#e6edf3">BFS from startGene finds endGene via the fewest such edges, or reports -1 if unreachable.</text>
  </g>
</svg>

Only the single character at the last position differs between the two genes, making this a valid one-mutation edge.

## 5. Runnable example

```java
// MinimumGeneticMutation.java
import java.util.*;

public class MinimumGeneticMutation {

    static final char[] GENES = {'A', 'C', 'G', 'T'};

    // Level 1 -- Brute force: DFS trying every possible mutation
    // sequence, tracking the minimum length across all paths that reach
    // endGene. Exponential time in the worst case, since the same gene
    // can be reached via many different mutation orders, each explored
    // separately without early pruning by distance.
    static int bruteForce(String startGene, String endGene, String[] bank) {
        Set<String> bankSet = new HashSet<>(Arrays.asList(bank));
        if (!bankSet.contains(endGene)) return -1;
        int[] best = {Integer.MAX_VALUE};
        dfsExplore(startGene, endGene, bankSet, new HashSet<>(), 0, best);
        return best[0] == Integer.MAX_VALUE ? -1 : best[0];
    }

    static void dfsExplore(String current, String endGene, Set<String> bank, Set<String> visited, int mutations, int[] best) {
        if (current.equals(endGene)) { best[0] = Math.min(best[0], mutations); return; }
        if (mutations >= best[0]) return;
        visited.add(current);
        for (String candidate : bank) {
            if (!visited.contains(candidate) && oneMutationApart(current, candidate)) {
                dfsExplore(candidate, endGene, bank, visited, mutations + 1, best);
            }
        }
        visited.remove(current);
    }

    static boolean oneMutationApart(String a, String b) {
        int diff = 0;
        for (int i = 0; i < a.length(); i++) if (a.charAt(i) != b.charAt(i)) diff++;
        return diff == 1;
    }

    // KEY INSIGHT: generating candidate mutations directly (trying all 4
    // letters at each of the 8 positions) instead of comparing against
    // every string in bank turns each step into O(8 * 4) work, independent
    // of bank's size -- and BFS guarantees the shortest sequence directly.

    // Level 2 -- Optimal: BFS generating mutations by trying all 4
    // letters at each position. O(bank size * gene length * 4) time,
    // O(bank size) space.
    public static int minMutation(String startGene, String endGene, String[] bank) {
        Set<String> bankSet = new HashSet<>(Arrays.asList(bank));
        if (!bankSet.contains(endGene)) return -1;

        Queue<String> queue = new LinkedList<>();
        Set<String> visited = new HashSet<>();
        queue.offer(startGene);
        visited.add(startGene);
        int mutations = 0;

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                String current = queue.poll();
                if (current.equals(endGene)) return mutations;
                char[] chars = current.toCharArray();
                for (int pos = 0; pos < chars.length; pos++) {
                    char original = chars[pos];
                    for (char gene : GENES) {
                        if (gene == original) continue;
                        chars[pos] = gene;
                        String candidate = new String(chars);
                        if (bankSet.contains(candidate) && !visited.contains(candidate)) {
                            visited.add(candidate);
                            queue.offer(candidate);
                        }
                    }
                    chars[pos] = original;
                }
            }
            mutations++;
        }
        return -1;
    }

    // Level 3 -- Hardened: an endGene that is not in bank must return
    // -1 immediately, without even starting the BFS.
    static int hardened(String startGene, String endGene, String[] bank) {
        return minMutation(startGene, endGene, bank);
    }

    public static void main(String[] args) {
        String start = "AACCGGTT";
        String end = "AAACGGTA";
        String[] bank = {"AACCGGTA", "AACCGCTA", "AAACGGTA"};

        System.out.println(bruteForce(start, end, bank));
        System.out.println(minMutation(start, end, bank));

        System.out.println(hardened(start, "TTTTTTTT", bank));
    }
}
```

How to run: save as `MinimumGeneticMutation.java`, then run `java MinimumGeneticMutation.java`.

## 6. Walkthrough

Dry run of `minMutation("AACCGGTT", "AAACGGTA", ["AACCGGTA","AACCGCTA","AAACGGTA"])`:

| mutations | queue at start | processing | newly enqueued |
|---|---|---|---|
| 0 | [AACCGGTT] | try all mutations of AACCGGTT; "AACCGGTA" is in bank | AACCGGTA |
| 1 | [AACCGGTA] | try all mutations of AACCGGTA; "AAACGGTA" is in bank (position 2, C->A) | AAACGGTA |
| 2 | [AAACGGTA] | dequeue, equals endGene | return 2 |

Final answer: `2` mutations (`AACCGGTT -> AACCGGTA -> AAACGGTA`). Time complexity: O(bank size * 8 * 4), since each gene tries 8 positions times 4 letters, and each candidate lookup is O(1) via the hash set. Space complexity: O(bank size) for the visited set and queue.

## 7. Gotchas & takeaways

> Gotcha: forgetting to restore `chars[pos] = original` after trying all 4 replacement letters at that position would corrupt `current`'s character array for every subsequent position tried in the same loop — the mutation must be tried and then reverted, one position at a time, reusing the same `char[]` buffer.

- Checking `endGene` for membership in `bank` BEFORE starting the BFS is a cheap early exit — since every step of a valid mutation sequence (including the final one) must land on a string in `bank`, an `endGene` missing from `bank` can never be reached no matter how the search proceeds.
- Related problems: Snakes and Ladders (the same "each allowed move is one unweighted edge, BFS finds the minimum count" pattern, there for dice rolls instead of character mutations), Rotting Oranges (also uses `levelSize`-per-round BFS to count discrete steps, there minutes instead of mutations).
