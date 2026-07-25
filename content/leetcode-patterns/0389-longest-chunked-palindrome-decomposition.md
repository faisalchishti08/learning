---
card: leetcode-patterns
gi: 389
slug: longest-chunked-palindrome-decomposition
title: Longest Chunked Palindrome Decomposition
---

## 1. What it is

Given a string `text`, split it into the MAXIMUM number of consecutive, non-empty substrings (chunks) `subs[0], subs[1], ..., subs[k-1]` such that concatenating them reproduces `text`, and the sequence of chunks is itself a "chunked palindrome": `subs[i] == subs[k-1-i]` for every valid `i`. Return the largest possible `k`. Example: `text = "ghiabcdefhelloadamhelloabcdefghi"` → `7`.

## 2. Why & when

Unlike the other problems in this section, the accepted solution here is GREEDY, not a full DP table — but it belongs to the palindrome family because it relies on the SAME "compare a growing prefix against a growing suffix" idea as expand-around-center, just applied to whole chunks instead of single characters. Use the greedy approach whenever a problem asks to MAXIMIZE the number of matching chunk pairs from the outside in, since taking the SHORTEST possible match at each step is always at least as good as waiting for a longer one.

## 3. Core concept

**Key idea:** walk two pointers inward from both ends, growing a candidate PREFIX chunk from the left and a candidate SUFFIX chunk from the right. The moment the prefix and suffix chunks become EQUAL, commit them as a matched pair and reset both candidates to empty, continuing inward.

**Steps:**
1. Set `i = 0`, `j = text.length() - 1`, `count = 0`, and two empty running chunks `prefix` and `suffix`.
2. While `i < j`: append `text.charAt(i)` to `prefix`, increment `i`; prepend `text.charAt(j)` to `suffix`, decrement `j`.
3. If `prefix.equals(suffix)`: increment `count` by `2` (one for the prefix chunk, one for the matching suffix chunk), and reset `prefix` and `suffix` to empty.
4. After the loop ends (`i >= j`): if there is a leftover UNMATCHED middle (either `prefix` is non-empty, or `i == j` meaning one character is stranded exactly in the center), increment `count` by `1` for that final unpaired middle chunk.
5. Return `count`.

**Why the GREEDY choice is correct:** whenever the growing prefix first equals the growing suffix, committing them as a matched pair IMMEDIATELY is always at least as good as waiting to grow a LONGER matching pair instead — a shorter matched pair uses fewer characters per chunk, leaving MORE characters available in the middle to form MORE additional matched pairs later. Waiting never helps: any decomposition that uses a longer first pair can always be REFINED into one using the earliest match instead, without decreasing the total chunk count.

## 4. Diagram

<svg viewBox="0 0 480 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two pointers growing a prefix and suffix chunk inward, committing a match as soon as the two chunks become equal">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20">text="antaprezatepzapreza..."; i=0,j=end</text>
    <text x="10" y="45">grow prefix="a", suffix="a" -- equal! commit, count+=2, reset</text>
    <text x="10" y="65">grow prefix="n", suffix="z" -- not equal, keep growing</text>
    <text x="10" y="85">grow prefix="nt", suffix="za" -- not equal, keep growing...</text>
    <rect x="10" y="105" width="260" height="24" fill="#3fb950"/><text x="140" y="122" fill="#0d1117" text-anchor="middle" font-size="10">commit the EARLIEST possible match each time</text>
  </g>
</svg>

Growing both sides together and committing at the first equality maximizes the number of chunks found.

## 5. Runnable example

```java
// LongestChunkedPalindromeDecomposition.java
public class LongestChunkedPalindromeDecomposition {

    // KEY INSIGHT: greedily commit the SHORTEST matching prefix/suffix
    // pair as soon as it appears -- this is the palindrome-matching
    // idea applied to whole chunks, and it never loses potential
    // future matches.

    static int longestDecomposition(String text) {
        int i = 0, j = text.length() - 1;
        int count = 0;
        StringBuilder prefix = new StringBuilder();
        StringBuilder suffix = new StringBuilder();

        while (i < j) {
            prefix.append(text.charAt(i));
            suffix.insert(0, text.charAt(j));
            i++; j--;

            if (prefix.toString().equals(suffix.toString())) {
                count += 2;
                prefix.setLength(0);
                suffix.setLength(0);
            }
        }
        if (prefix.length() > 0 || i == j) {
            count += 1;
        }
        return count;
    }

    public static void main(String[] args) {
        System.out.println(longestDecomposition("ghiabcdefhelloadamhelloabcdefghi"));
        // 7
        System.out.println(longestDecomposition("merchant"));
        // 1
    }
}
```

**How to run:** `java LongestChunkedPalindromeDecomposition.java`

## 6. Walkthrough

Trace `longestDecomposition("antaprezatepzapreza")` conceptually (illustrative):

1. `i=0, j=19`: grow `prefix="a"`, `suffix="a"` — equal! `count=2`, reset.
2. Continue growing from `i=1, j=18`: eventually `prefix="ntap"`, `suffix="pzap"` mismatch continues to grow until a match is found, committing another pair.
3. This continues inward, committing matched chunk pairs as early as possible each time.
4. When `i >= j`, any leftover partially-built `prefix` (or the single stranded middle character when `i == j`) becomes ONE final unmatched middle chunk.

For `"merchant"` (no repeated structure), no prefix/suffix match is ever found before `i` and `j` cross, so the entire string becomes a single leftover chunk: `count = 1`. Time complexity is O(n^2) in the worst case (string comparison at each step can cost up to O(n), repeated up to O(n) times). Space is O(n) for the growing `prefix`/`suffix` buffers.

## 7. Gotchas & takeaways

> Gotcha: forgetting the FINAL check after the main loop (`prefix.length() > 0 || i == j`) undercounts by exactly one whenever there is a leftover, unmatched middle portion — this includes the common case of an ODD-length decomposition needing one unpaired center chunk.

- This problem is solved GREEDILY, not with a DP table, because the "commit the earliest match" strategy is PROVABLY optimal here — unlike most of this section's problems, which need to explore all possible splits via DP because no such greedy exchange argument holds for them.
- Comparing `StringBuilder` contents with `.toString().equals(...)` on every growth step is simple but not the most time-efficient; a rolling hash comparison can reduce the worst-case string-comparison cost, though it is unnecessary for typical constraints.
- Related problems: Valid Palindrome II (also uses a two-pointer greedy idea, but for a SINGLE string against itself, not chunk matching), Palindrome Partitioning II (a true DP problem, needed because no greedy shortcut exists for minimizing palindrome PARTITION cuts).
