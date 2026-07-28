---
card: leetcode-patterns
gi: 545
slug: alien-dictionary
title: Alien Dictionary
---

## 1. What it is

You are given a list of words from an alien language, already sorted according to that language's unknown letter order. Derive a valid ordering of the alphabet's letters that is consistent with the given sorted list. Return any one valid order as a string, or an empty string if the input is inconsistent (no valid order exists). Example: `words = ["wrt","wrf","er","ett","rftt"]` → `"wertf"`.

## 2. Why & when

Comparing each pair of adjacent words letter by letter reveals ordering constraints between individual characters — "this letter must come before that letter" — which is exactly the [topological sort signal](0537-topological-sort-signal-ordering-with-dependency-prerequisit.md) applied to an alphabet instead of tasks. Constraints: up to 100 words, lowercase letters only.

## 3. Core concept

**Key idea:** for every pair of adjacent words, find the first position where their letters differ. That first differing pair gives one ordering constraint: the letter from the earlier word must come before the letter from the later word. Collect all such constraints as edges, then run a standard topological sort over the letters that actually appear.

**Steps:**
1. Initialize an empty adjacency structure and in-degree map for every distinct letter seen across all words.
2. For each pair of adjacent words `(w1, w2)`: walk both strings together up to the shorter word's length. At the first index where the characters differ, add edge `w1[i] -> w2[i]` (if not already present) and stop comparing this pair — later characters give no reliable information once one difference is found.
3. **Special invalid case:** if no difference is found within the shorter length, and `w1` is longer than `w2` (e.g. `"abc"` before `"ab"`), the input is invalid — a valid sorted order never places a longer word with a matching prefix before its shorter prefix.
4. Run Kahn's algorithm over the collected letters. If all letters are processed, return the resulting order as a string; otherwise return `""` (a cycle means contradictory constraints).

**Why only the *first* differing character between adjacent words matters:** in a correctly sorted list, once two words differ at some position, every character after that position is irrelevant to their relative order — the dictionary comparison already stopped there. Scanning past the first difference would derive false, unsupported constraints.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparing wrt and wrf finds their first difference at position 2 (t vs f), giving the constraint t before f">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">"wrt" vs "wrf"</text>
    <text x="20" y="50" fill="#8b949e">position 0: w == w, position 1: r == r, position 2: t != f -&gt; stop here</text>
    <circle cx="200" cy="110" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="200" y="115" fill="#e6edf3" text-anchor="middle">t</text>
    <circle cx="350" cy="110" r="16" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="115" fill="#e6edf3" text-anchor="middle">f</text>
    <line x1="216" y1="110" x2="334" y2="110" stroke="#8b949e" marker-end="url(#a6)"/>
    <defs><marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0L6,3L0,6Z" fill="#8b949e"/></marker></defs>
    <text x="500" y="115" fill="#79c0ff">edge: t -&gt; f (t comes before f)</text>
  </g>
</svg>

The first differing character position between adjacent words gives exactly one ordering constraint; every later character is ignored.

## 5. Runnable example

**Level 1 — Brute force.** Try every permutation of the distinct letters found, and check whether every word pair is consistent with that permutation. Factorial time.

**KEY INSIGHT:** each adjacent word pair contributes exactly one edge between two letters, at their first point of difference — reducing the whole problem to a standard topological sort over those edges.

**Level 2 — Optimal.** Build constraints in one pass over adjacent word pairs, then Kahn's algorithm, O(C) where C is the total character count across all words.

**Level 3 — Hardened.** Detects the invalid "longer word before its own prefix" case, and handles letters that appear in words but have no ordering constraint at all (placed anywhere valid).

```java
// AlienDictionary.java
import java.util.*;

public class AlienDictionary {

    static String alienOrder(String[] words) {
        Map<Character, Set<Character>> graph = new HashMap<>();
        Map<Character, Integer> inDegree = new HashMap<>();
        for (String word : words) {
            for (char c : word.toCharArray()) {
                graph.putIfAbsent(c, new HashSet<>());
                inDegree.putIfAbsent(c, 0);
            }
        }

        for (int i = 0; i < words.length - 1; i++) {
            String w1 = words[i], w2 = words[i + 1];
            int minLen = Math.min(w1.length(), w2.length());
            boolean foundDifference = false;
            for (int j = 0; j < minLen; j++) {
                char c1 = w1.charAt(j), c2 = w2.charAt(j);
                if (c1 != c2) {
                    if (!graph.get(c1).contains(c2)) {
                        graph.get(c1).add(c2);
                        inDegree.merge(c2, 1, Integer::sum);
                    }
                    foundDifference = true;
                    break;
                }
            }
            if (!foundDifference && w1.length() > w2.length()) {
                return ""; // longer word cannot precede its own shorter prefix
            }
        }

        Deque<Character> queue = new ArrayDeque<>();
        for (char c : inDegree.keySet()) {
            if (inDegree.get(c) == 0) queue.add(c);
        }

        StringBuilder order = new StringBuilder();
        while (!queue.isEmpty()) {
            char c = queue.poll();
            order.append(c);
            for (char next : graph.get(c)) {
                inDegree.merge(next, -1, Integer::sum);
                if (inDegree.get(next) == 0) queue.add(next);
            }
        }

        return order.length() == inDegree.size() ? order.toString() : "";
    }

    public static void main(String[] args) {
        System.out.println(alienOrder(new String[]{"wrt", "wrf", "er", "ett", "rftt"})); // wertf
        System.out.println(alienOrder(new String[]{"z", "x", "z"})); // "" (contradiction: z before x, then x before z)
        System.out.println(alienOrder(new String[]{"abc", "ab"})); // "" (invalid: longer word before its prefix)
    }
}
```

**How to run:** save as `AlienDictionary.java`, then run `java AlienDictionary.java`.

## 6. Walkthrough

Trace building constraints from `["wrt","wrf","er","ett","rftt"]`:

| pair | first difference | edge added |
|---|---|---|
| wrt, wrf | position 2: t vs f | t -> f |
| wrf, er | position 0: w vs e | w -> e |
| er, ett | position 1: r vs t | r -> t |
| ett, rftt | position 0: e vs r | e -> r |

Constraints: `t->f`, `w->e`, `r->t`, `e->r`, chaining into `w -> e -> r -> t -> f`. Running Kahn's algorithm on these edges produces the order `"wertf"`.

## 7. Gotchas & takeaways

> Gotcha: continuing to compare characters past the first difference between two adjacent words derives constraints that the sorted order does not actually guarantee — always `break` immediately after the first differing character.

- Signal: "a sorted list implies pairwise ordering constraints between individual symbols" is a topological sort over the symbols, not the words themselves.
- The "longer word before its shorter prefix" case (like `"abc"` before `"ab"`) is invalid input and must be checked separately — it produces no differing character at all.
- Related problems: Course Schedule II, Sequence Reconstruction (a related "is this topological order unique" variant).
