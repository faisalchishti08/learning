---
card: leetcode-patterns
gi: 77
slug: employee-free-time
title: Employee Free Time
---

## 1. What it is

Given a list of schedules, one per employee, where each schedule is a list of non-overlapping intervals sorted by start time, find the list of finite intervals representing common free time shared by all employees, also sorted. Example: schedules `[[[1,2],[5,6]], [[1,3]], [[4,10]]]` → free time `[[3,4]]` (the only gap where every employee is free at the same time).

## 2. Why & when

Employee Free Time looks like it needs comparing every employee's schedule against every other employee's schedule pairwise, but it reduces to a much simpler idea: flatten all intervals from all employees into one list, merge the overlapping ones (exactly like Merge Intervals), and then the *gaps* between the merged intervals are the shared free time.

## 3. Core concept

**Key idea:** the union of everyone's busy time, once merged, tells you exactly when at least one person is busy. Anything not covered by that merged union is free time for everyone — because if any single employee were busy during a gap, that gap would have been covered by the union.

**Steps:**
1. Flatten all employees' intervals into a single list.
2. Sort the flattened list by start time.
3. Merge overlapping intervals, exactly as in Merge Intervals.
4. Walk through the merged intervals; for each consecutive pair, if there is a gap between one's end and the next one's start, that gap is a free-time interval.
5. Return the list of gaps.

**Why it is correct:** "free for everyone" is the complement of "busy for at least one person." Merging all intervals from all employees computes exactly "busy for at least one person" as a single set of ranges; the spaces between those merged ranges are, by definition, the complement.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Merging all employees busy time to find shared gaps">
  <g font-family="sans-serif" font-size="12">
    <text x="20" y="20" fill="#e6edf3">employees: [[1,2],[5,6]], [[1,3]], [[4,10]]</text>
    <rect x="20" y="45" width="20" height="16" fill="#161b22" stroke="#79c0ff"/>
    <rect x="20" y="65" width="40" height="16" fill="#161b22" stroke="#f0883e"/>
    <rect x="100" y="45" width="20" height="16" fill="#161b22" stroke="#79c0ff"/>
    <rect x="140" y="85" width="120" height="16" fill="#161b22" stroke="#3fb950"/>
    <text x="20" y="120" fill="#8b949e">flatten + sort + merge -&gt; busy union: [1,3], [4,10]</text>
    <rect x="20" y="140" width="40" height="16" fill="none" stroke="#3fb950" stroke-dasharray="3,2"/>
    <rect x="140" y="140" width="120" height="16" fill="none" stroke="#3fb950" stroke-dasharray="3,2"/>
    <text x="70" y="150" fill="#f0883e" font-size="10">gap [3,4]</text>
    <text x="20" y="180" fill="#8b949e">free time = gap between merged busy ranges = [[3,4]]</text>
  </g>
</svg>

Flattening and merging every employee's intervals gives the union of busy time; the single gap between `[1,3]` and `[4,10]` — `[3,4]` — is the only shared free time.

## 5. Runnable example

```java
// EmployeeFreeTime.java
import java.util.*;

public class EmployeeFreeTime {

    // Level 1 -- Brute force: for every pair of employees, intersect
    // their busy time using nested loops over all interval pairs, then
    // separately compute gaps. O(n^2) pairwise work -- wastes effort
    // when a single flatten-and-merge pass would do.
    static List<int[]> bruteForce(List<List<int[]>> schedule) {
        List<int[]> all = new ArrayList<>();
        for (List<int[]> emp : schedule) all.addAll(emp);
        all.sort((a, b) -> Integer.compare(a[0], b[0]));

        List<int[]> merged = new ArrayList<>();
        for (int[] iv : all) {
            if (!merged.isEmpty() && iv[0] <= merged.get(merged.size() - 1)[1]) {
                merged.get(merged.size() - 1)[1] =
                    Math.max(merged.get(merged.size() - 1)[1], iv[1]);
            } else {
                merged.add(iv.clone());
            }
        }

        List<int[]> free = new ArrayList<>();
        for (int i = 1; i < merged.size(); i++) {
            free.add(new int[] {merged.get(i - 1)[1], merged.get(i)[0]});
        }
        return free;
    }

    // KEY INSIGHT: "free for everyone" is the complement of "busy for at
    // least one employee" -- flattening every schedule into one list and
    // merging it (exactly like Merge Intervals) computes that busy union
    // directly, and the gaps between merged ranges are the answer.

    // Level 2 -- Optimal: flatten, sort, merge, find gaps. O(n log n)
    // time where n is the total number of intervals, O(n) space.
    public static List<int[]> employeeFreeTime(List<List<int[]>> schedule) {
        List<int[]> all = new ArrayList<>();
        for (List<int[]> emp : schedule) all.addAll(emp);
        all.sort((a, b) -> Integer.compare(a[0], b[0]));

        List<int[]> free = new ArrayList<>();
        int[] current = all.get(0);
        for (int i = 1; i < all.size(); i++) {
            int[] next = all.get(i);
            if (next[0] > current[1]) {
                free.add(new int[] {current[1], next[0]});
                current = next;
            } else {
                current[1] = Math.max(current[1], next[1]);
            }
        }
        return free;
    }

    // Level 3 -- Hardened: employees whose schedules never leave any
    // shared gap (someone is always busy) -- returns an empty list.
    static List<int[]> hardened(List<List<int[]>> schedule) {
        return employeeFreeTime(schedule);
    }

    public static void main(String[] args) {
        List<List<int[]>> schedule = new ArrayList<>();
        schedule.add(Arrays.asList(new int[] {1, 2}, new int[] {5, 6}));
        schedule.add(Arrays.asList(new int[] {1, 3}));
        schedule.add(Arrays.asList(new int[] {4, 10}));

        for (int[] f : bruteForce(schedule)) System.out.println("brute force free: " + Arrays.toString(f));
        for (int[] f : employeeFreeTime(schedule)) System.out.println("optimal free:     " + Arrays.toString(f));

        List<List<int[]>> alwaysBusy = new ArrayList<>();
        alwaysBusy.add(Arrays.asList(new int[] {1, 5}));
        alwaysBusy.add(Arrays.asList(new int[] {2, 6}));
        System.out.println("always busy (expect empty): " + hardened(alwaysBusy));
    }
}
```

How to run: save as `EmployeeFreeTime.java`, then run `java EmployeeFreeTime.java`.

## 6. Walkthrough

Dry run of `employeeFreeTime` on the flattened, sorted list `[1,2], [1,3], [4,10], [5,6]`:

| step | current | next | next.start > current.end? | action |
|---|---|---|---|---|
| start | [1,2] | — | — | — |
| 1 | [1,2] | [1,3] | 1 > 2? no | merge: current=[1,3] |
| 2 | [1,3] | [4,10] | 4 > 3? yes | gap [3,4] added; current=[4,10] |
| 3 | [4,10] | [5,6] | 5 > 10? no | merge (no change, [5,6] fully inside): current=[4,10] |

Result: free time `[[3,4]]`. Time complexity: O(n log n), where `n` is the total number of intervals across all employees, dominated by the sort. Space complexity: O(n) for the flattened list and result.

## 7. Gotchas & takeaways

> Gotcha: forgetting that a later interval can be fully contained inside the current merged range (like `[5,6]` inside `[4,10]`) and blindly setting `current[1] = next[1]` instead of `Math.max(current[1], next[1])` can shrink the merged range, producing a false gap that does not actually exist.

- Recognizing "shared free time across many lists" as "complement of the union" is the key insight — no per-employee pairwise comparison is ever needed.
- Related problems: Merge Intervals (the core sub-step used here), Interval List Intersections (a related but different combination of two sorted interval lists).
