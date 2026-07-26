---
card: leetcode-patterns
gi: 454
slug: queue-reconstruction-by-height
title: Queue Reconstruction by Height
---

## 1. What it is

Given a list of people `[height, k]`, where `k` is the number of people IN FRONT OF this person who have a height GREATER THAN OR EQUAL to theirs, reconstruct the queue so every person's `k` value is satisfied. Example: `people = [[7,0],[4,4],[7,1],[5,0],[6,1],[5,2]]` → `[[5,0],[7,0],[5,2],[6,1],[4,4],[7,1]]`.

## 2. Why & when

Use this shape whenever a problem describes a constraint that depends on RELATIVE ORDER and RELATIVE VALUE among ALREADY-PLACED items (here, "how many taller-or-equal people come before me"). The greedy rule: process people in an order where each INSERTION is guaranteed correct and PERMANENT — specifically, tallest first, and among equal heights, smallest `k` first — then insert each person directly at index `k` in the result.

## 3. Core concept

**Key idea:** sort people by height DESCENDING, breaking ties by `k` ASCENDING. Then insert each person, in that sorted order, at position `k` in a growing result list.

**Steps:**
1. Sort `people` by height descending; for equal heights, sort by `k` ascending.
2. Build an empty result list.
3. For each person `[height, k]`, in the sorted order, INSERT them at index `k` of the result list (shifting existing entries right, as a normal list insertion does).
4. After processing everyone, the result list is the correctly reconstructed queue.

**Why inserting a shorter person LATER never disturbs an earlier person's `k` value (the exchange argument):** once a taller (or equally tall) person is already placed, inserting a SHORTER person anywhere into the list does not add to that taller person's count of "people in front who are taller-or-equal," since the newly inserted person is shorter. So placing people from TALLEST to SHORTEST, and inserting each one directly at their required index `k` among ONLY the people placed so far (which are all taller or equally tall), is guaranteed to be both correct FOR THAT PERSON and PERMANENT for everyone already placed.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="people processed from tallest to shortest each inserted at index k among the already placed taller people without disturbing their counts">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">sorted: [7,0],[7,1],[6,1],[5,0],[5,2],[4,4] -- tallest first, ties by k ascending</text>
    <text x="10" y="45">insert [7,0] at 0; insert [7,1] at 1; insert [6,1] at 1 (shifts [7,1] right)</text>
    <rect x="10" y="65" width="330" height="24" fill="#3fb950"/><text x="175" y="82" fill="#0d1117" text-anchor="middle" font-size="10">shorter insertions never affect a taller person's already-correct count</text>
  </g>
</svg>

Inserting people from tallest to shortest, directly at their required index, never disturbs any taller person already placed.

## 5. Runnable example

```java
// QueueReconstructionByHeight.java
import java.util.*;

public class QueueReconstructionByHeight {

    // KEY INSIGHT: process tallest-first -- inserting a shorter person
    // later never changes a taller person's "taller-or-equal people in
    // front" count, so each insertion is correct and permanent.

    static int[][] reconstructQueue(int[][] people) {
        Arrays.sort(people, (a, b) -> a[0] != b[0] ? b[0] - a[0] : a[1] - b[1]);

        List<int[]> result = new ArrayList<>();
        for (int[] person : people) {
            result.add(person[1], person);
        }
        return result.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        int[][] people = {{7, 0}, {4, 4}, {7, 1}, {5, 0}, {6, 1}, {5, 2}};
        for (int[] p : reconstructQueue(people)) {
            System.out.print(Arrays.toString(p) + " ");
        }
        System.out.println();
        // [5, 0] [7, 0] [5, 2] [6, 1] [4, 4] [7, 1]
    }
}
```

**How to run:** `java QueueReconstructionByHeight.java`

## 6. Walkthrough

Trace the insertions in sorted order (`[7,0], [7,1], [6,1], [5,0], [5,2], [4,4]`):

| insert | at index | result after |
|---|---|---|
| [7,0] | 0 | [[7,0]] |
| [7,1] | 1 | [[7,0],[7,1]] |
| [6,1] | 1 | [[7,0],[6,1],[7,1]] |
| [5,0] | 0 | [[5,0],[7,0],[6,1],[7,1]] |
| [5,2] | 2 | [[5,0],[7,0],[5,2],[6,1],[7,1]] |
| [4,4] | 4 | [[5,0],[7,0],[5,2],[6,1],[4,4],[7,1]] |

The final result matches the expected answer exactly. Time complexity is O(n^2) in the worst case (sorting is O(n log n), but each insertion into an array-backed list can cost O(n), for O(n) insertions). Space is O(n).

## 7. Gotchas & takeaways

> Gotcha: sorting ties (same height) by `k` ASCENDING, not descending, matters — among people of EQUAL height, a smaller `k` means fewer equally-tall people should be in front, so that person must be inserted FIRST among the tied group, or their own count would end up wrong once the others of the same height are also placed.

- Sorting tallest-first, ties by `k` ascending, then inserting directly at index `k`: the key exchange argument that makes each insertion both correct and permanent.
- Using an array-backed list (like `ArrayList`) makes each insertion O(n) in the worst case; a more advanced structure (like a balanced tree indexed by rank) can reduce this, though it is rarely necessary at typical input sizes.
- Related problems: Dota2 Senate (a different greedy order — turn order in a simulation, rather than a sort-then-insert reconstruction), Hand of Straights (also processes items in a forced order — smallest first — though for a very different reason, consecutive-run formation rather than insertion-based placement).
