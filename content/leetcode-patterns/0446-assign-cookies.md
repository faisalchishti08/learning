---
card: leetcode-patterns
gi: 446
slug: assign-cookies
title: Assign Cookies
---

## 1. What it is

Each child `i` has a greed factor `g[i]` (the smallest cookie size that satisfies them). Each cookie `j` has a size `s[j]`. Assign at most one cookie per child, to maximize the number of CONTENT children. Example: `g = [1,2,3]`, `s = [1,1]` → `1`.

## 2. Why & when

Use this shape whenever a problem asks you to MATCH two sets of values against each other (needs vs. resources), maximizing how many needs get satisfied, where any resource that meets or exceeds a need can satisfy it. Sorting both sides first, then matching greedily, is the classic solution.

## 3. Core concept

**Key idea:** sort BOTH `g` (greed factors) and `s` (cookie sizes). Walk through both arrays with two pointers, always trying to satisfy the CURRENT least-greedy unsatisfied child with the CURRENT smallest unused cookie.

**Steps:**
1. Sort `g` and `s` in ascending order.
2. Use pointers `child = 0` and `cookie = 0`. While both pointers are in range: if `s[cookie] >= g[child]`, this cookie satisfies this child — advance BOTH pointers. Otherwise, this cookie is too small for ANY remaining child (since children are sorted by increasing greed) — advance only `cookie`.
3. Return `child` (the count of satisfied children) once either pointer runs out.

**Why the greedy match is correct (the exchange argument):** giving the smallest sufficient cookie to the LEAST-greedy remaining child never hurts — any bigger cookie saved for this child could instead satisfy a MORE-greedy child later, while a smaller cookie could never have satisfied that more-greedy child anyway. So matching smallest-to-smallest first can only be as good as, or better than, any other matching order.

## 4. Diagram

<svg viewBox="0 0 480 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two sorted arrays greed factors and cookie sizes with two pointers advancing together whenever a cookie satisfies a child">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">g (sorted) = [1, 2, 3]; s (sorted) = [1, 1]</text>
    <text x="10" y="45">cookie[0]=1 satisfies g[0]=1 -- both pointers advance</text>
    <text x="10" y="65">cookie[1]=1 does NOT satisfy g[1]=2 -- only cookie pointer advances</text>
    <rect x="10" y="85" width="240" height="24" fill="#3fb950"/><text x="130" y="102" fill="#0d1117" text-anchor="middle" font-size="10">cookies run out -- 1 child satisfied</text>
  </g>
</svg>

Matching the smallest sufficient cookie to the least-greedy child, in sorted order, never wastes a resource.

## 5. Runnable example

```java
// AssignCookies.java
import java.util.Arrays;

public class AssignCookies {

    // KEY INSIGHT: sort both arrays, then match the smallest
    // sufficient cookie to the least-greedy remaining child -- never
    // wastes a bigger cookie on a child who needed less.

    static int findContentChildren(int[] g, int[] s) {
        Arrays.sort(g);
        Arrays.sort(s);
        int child = 0, cookie = 0;
        while (child < g.length && cookie < s.length) {
            if (s[cookie] >= g[child]) child++;
            cookie++;
        }
        return child;
    }

    public static void main(String[] args) {
        System.out.println(findContentChildren(new int[]{1, 2, 3}, new int[]{1, 1}));
        // 1
        System.out.println(findContentChildren(new int[]{1, 2}, new int[]{1, 2, 3}));
        // 2
    }
}
```

**How to run:** `java AssignCookies.java`

## 6. Walkthrough

Trace `findContentChildren([1,2,3], [1,1])`:

| child ptr | cookie ptr | g[child] | s[cookie] | match? | action |
|---|---|---|---|---|---|
| 0 | 0 | 1 | 1 | yes | child++, cookie++ |
| 1 | 1 | 2 | 1 | no | cookie++ |
| 1 | 2 | — | (out of cookies) | — | loop ends |

Final `child = 1`, matching the expected answer. Time complexity is O(n log n) (dominated by the two sorts). Space is O(1) beyond the sort's own space.

## 7. Gotchas & takeaways

> Gotcha: without sorting BOTH arrays first, a smaller cookie could get wasted on a more-greedy child while a less-greedy child goes unsatisfied — the greedy "smallest sufficient cookie" rule is ONLY correct once both sides are in matching sorted order.

- Two pointers over two sorted arrays: the standard shape for "match smallest sufficient resource to smallest need" greedy problems.
- Advancing only the COOKIE pointer on a mismatch (not the child pointer) is what correctly skips a too-small cookie without giving up on the current child.
- Related problems: Lemonade Change (a different kind of greedy matching, giving exact change with the fewest large bills), Can Place Flowers (a different greedy signal — checking local feasibility left to right, not a two-array match).
