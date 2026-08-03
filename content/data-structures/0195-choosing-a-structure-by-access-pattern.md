---
card: data-structures
gi: 195
slug: choosing-a-structure-by-access-pattern
title: Choosing a structure by access pattern
---

## 1. What it is

This page is a decision guide: instead of starting from "which structure do I know," start from "what does my code actually **do** to this data most often," and let that access pattern point directly at the right structure.

## 2. Why & when

The single most common design mistake is picking a structure out of habit (usually `ArrayList` or `HashMap`, because they are familiar) without checking whether the operations you will run most often are actually cheap on that structure. Reasoning from access pattern first — "what operation happens in the hot path, and how often?" — catches this before it becomes a performance problem.

## 3. Core concept

**The decision criteria, as questions to ask about your workload.**
- **Do you look things up by position (index) or by key/value?** Index → array-backed (`ArrayList`). Key → hash-backed (`HashMap`) or tree-backed (`TreeMap`).
- **Do you need the data sorted, or is any order fine?** Sorted → `TreeMap`/`TreeSet`. Any order → `HashMap`/`HashSet` (faster).
- **Do you insert/remove mostly at the ends, or in the middle?** Ends → `ArrayDeque`. Middle, at a known position reached by iteration → `LinkedList`. Middle, by value → usually still `O(n)` regardless of structure, unless it is also keyed for lookup.
- **Do you need "the current minimum/maximum," repeatedly, as the set changes?** → a heap (`PriorityQueue`).
- **Do you need "all values in a range" or "the nearest value to X"?** → a sorted structure (`TreeMap`, [sparse table](0155-sparse-table-static-range-queries.md), [segment tree](0152-segment-tree-range-query-update.md)) — a hash-based structure fundamentally cannot answer this without a full scan.
- **Do you need "which group does this belong to," with merges over time?** → [union-find](0162-disjoint-set-data-structure.md).
- **Do you need string prefix matching?** → a [trie](0126-prefix-tree-trie-structure.md), not a hash map.

**The decision tree, worked as a sequence.** Start with the single most frequent operation in your actual workload. Filter to structures that make that operation cheap. Among the survivors, apply the second most frequent operation as a tie-break. Repeat until one structure remains — this ordered filtering is more reliable than trying to weigh every operation equally at once.

**Why "most frequent operation" beats "asymptotically best for every operation."** No single structure is best at everything (see the [complexity table](0194-time-space-complexity-table-across-structures.md)) — every choice is a tradeoff. Optimizing for the operation that runs a million times a second matters far more than optimizing for one that runs once at startup.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decision tree starting from the dominant access pattern and narrowing down to a specific structure">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="250" y="10" width="140" height="34" fill="#161b22" stroke="#79c0ff"/>
    <text x="320" y="31" text-anchor="middle">most frequent op?</text>

    <rect x="20" y="80" width="140" height="34" fill="#0d1117" stroke="#8b949e"/><text x="90" y="101" text-anchor="middle" font-size="9">index access</text>
    <rect x="180" y="80" width="140" height="34" fill="#0d1117" stroke="#8b949e"/><text x="250" y="101" text-anchor="middle" font-size="9">key lookup</text>
    <rect x="340" y="80" width="140" height="34" fill="#0d1117" stroke="#8b949e"/><text x="410" y="101" text-anchor="middle" font-size="9">min/max repeatedly</text>
    <rect x="500" y="80" width="120" height="34" fill="#0d1117" stroke="#8b949e"/><text x="560" y="101" text-anchor="middle" font-size="9">range query</text>

    <line x1="320" y1="44" x2="90" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="44" x2="250" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="44" x2="410" y2="80" stroke="#79c0ff"/>
    <line x1="320" y1="44" x2="560" y2="80" stroke="#79c0ff"/>

    <text x="90" y="150" text-anchor="middle" font-size="9" fill="#3fb950">ArrayList</text>
    <text x="250" y="150" text-anchor="middle" font-size="9" fill="#3fb950">HashMap</text>
    <text x="410" y="150" text-anchor="middle" font-size="9" fill="#3fb950">PriorityQueue</text>
    <text x="560" y="150" text-anchor="middle" font-size="9" fill="#3fb950">TreeMap / segment tree</text>
  </g>
</svg>

Name the dominant operation first; the structure choice usually follows immediately.

## 5. Runnable example

```java
// AccessPatternSelection.java
import java.util.*;

public class AccessPatternSelection {

    // Basic: index access dominates -> ArrayList is correct, HashMap would be pointless overhead.
    static void basicLevel() {
        List<String> logLines = new ArrayList<>();
        for (int i = 0; i < 1000; i++) logLines.add("log entry " + i);

        String line500 = logLines.get(500); // O(1) -- exactly what ArrayList is for
        System.out.println("basic: index access -> " + line500);
    }

    // Intermediate: key lookup dominates, no ordering needed -> HashMap beats TreeMap here.
    static void intermediateLevel() {
        Map<String, String> userSessions = new HashMap<>();
        userSessions.put("user-42", "session-abc");
        userSessions.put("user-17", "session-xyz");

        System.out.println("intermediate: O(1) key lookup -> " + userSessions.get("user-42"));
    }

    // Advanced: repeated "process the cheapest task next" -> PriorityQueue, not a sorted List re-sorted each time.
    record Task(String name, int cost) {}

    static void advancedLevel() {
        PriorityQueue<Task> taskQueue = new PriorityQueue<>(Comparator.comparingInt(Task::cost));
        taskQueue.offer(new Task("resize image", 50));
        taskQueue.offer(new Task("send email", 5));
        taskQueue.offer(new Task("generate report", 200));

        // A naive approach might re-sort a List after every insert -- O(n log n) each time.
        // PriorityQueue keeps the minimum accessible in O(1) and insert/removal at O(log n).
        while (!taskQueue.isEmpty()) {
            System.out.println("advanced: next cheapest task -> " + taskQueue.poll());
        }
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java AccessPatternSelection.java`

## 6. Walkthrough

**Scenario 1 — a UI needs to render "row 500 of the results" on demand.** The dominant operation is index access. `ArrayList.get(500)` is `O(1)`. Using a `HashMap<Integer, String>` keyed by row number would also work, but adds unnecessary hashing overhead and loses the free, implicit ordering an array already provides — `ArrayList` is strictly the better fit here.

**Scenario 2 — a session store needs "look up this user's session by user ID," with no ordering requirement.** The dominant operation is key lookup, and there is no need for sorted iteration. `HashMap.get(userId)` is `O(1)` average. Choosing `TreeMap` instead would cost `O(log n)` for no benefit, since nothing in the workload ever needs sorted keys.

**Scenario 3 — a job scheduler must always process the cheapest pending task next, as new tasks keep arriving.** The dominant operation is "repeatedly extract the current minimum." A naive approach — keep a `List`, sort it after every insertion — costs `O(n log n)` per insertion just to re-sort. `PriorityQueue` keeps the minimum accessible in `O(1)` and handles both insertion and extraction in `O(log n)`, without ever fully sorting the rest of the data, which the naive approach wastes time doing.

Each scenario followed the same reasoning: name the operation that happens most, then pick the structure that makes exactly that operation cheap, rather than defaulting to whichever structure is most familiar.

**Complexity.** This page is about selection reasoning, not a specific algorithm — refer to the [complexity table](0194-time-space-complexity-table-across-structures.md) for the exact numbers behind each recommendation above.

## 7. Gotchas & takeaways

> Defaulting to `ArrayList` or `HashMap` out of habit, without checking the actual dominant access pattern, is the most common structure-selection mistake — it usually still "works," just slower than it needed to be, which is easy to miss until the data grows large enough to matter.

- When a workload has two genuinely frequent, conflicting operations (say, both fast index access **and** fast key lookup), no single built-in structure gives both for free — consider maintaining two structures in sync (an array plus a parallel index map), accepting the extra memory and update cost for both fast paths.
- Re-evaluate this choice if the workload's dominant operation changes over the life of a project — a structure that was right at launch can become the wrong one as usage patterns shift.
- See [ordered vs unordered tradeoffs](0196-ordered-vs-unordered-structure-tradeoffs.md) next for the specific cost of choosing a sorted structure when you did not actually need sorting.
