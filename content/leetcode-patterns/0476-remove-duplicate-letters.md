---
card: leetcode-patterns
gi: 476
slug: remove-duplicate-letters
title: Remove Duplicate Letters
---

## 1. What it is

Given a string `s`, remove duplicate letters so that every letter appears exactly once, the result keeps the smallest possible lexicographic order, and the relative order of the remaining letters matches their first appearance. Example: `s = "cbacdcbc"` → `"acdb"`.

## 2. Why & when

This extends [Remove K Digits](0475-remove-k-digits.md): it is another greedy-removal problem from the [monotonic-stack signal](0466-monotonic-stack-signal-next-greater-smaller-element-or-histo.md) family, but instead of a fixed removal budget `k`, the rule is "you may only pop a letter if it appears again later" — you cannot afford to lose a letter for good. Constraints: `s` has up to 10,000 lowercase letters.

## 3. Core concept

**Key idea:** scan left to right, keeping a stack of letters seen so far, each appearing at most once. Before pushing a new letter, pop any stack-top letter that is bigger than the new one — but ONLY if that bigger letter occurs again later in the string (so removing it now does not lose it forever).

**Steps:**
1. Count the total occurrences of every letter in `s` (a frequency map), so you can check "does this letter still occur later."
2. Track a `boolean[] inStack` (or a set) of letters currently on the stack, to skip letters you have already included.
3. Scan each character `c`: decrement its remaining count. If `c` is already on the stack, skip it entirely (do not push a duplicate).
4. Otherwise, while the stack is not empty, its top is greater than `c`, and the top's remaining count is greater than `0` (it appears again later), pop the top and mark it not in the stack.
5. Push `c` and mark it in the stack.

**Why the "occurs again later" check is essential:** without it, popping a bigger letter that never reappears would delete it from the answer permanently — every letter must appear in the final result exactly once, so you can only trade a letter away if a later copy of it will restore it to the stack.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Increasing stack popping bigger letters only when they still occur later in the string">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">s = "cbacdcbc"</text>
    <text x="20" y="45" fill="#8b949e">i=0 'c': push. stack="c"</text>
    <text x="20" y="65" fill="#8b949e">i=1 'b': 'c'&gt;'b' and 'c' reappears at i=7 -&gt; pop 'c'. push 'b'. stack="b"</text>
    <text x="20" y="85" fill="#8b949e">i=2 'a': 'b'&gt;'a' and 'b' reappears at i=6 -&gt; pop 'b'. push 'a'. stack="a"</text>
    <text x="20" y="105" fill="#8b949e">i=3 'c': 'a' not &gt; 'c', push. stack="ac"</text>
    <text x="20" y="125" fill="#8b949e">i=4 'd': push. stack="acd"</text>
    <text x="20" y="145" fill="#8b949e">i=6 'b': top 'd'&gt;'b' but 'd' never reappears (lastIndex=4) -&gt; keep 'd', push 'b'</text>
    <text x="20" y="170" fill="#3fb950">final stack: "acdb"</text>
  </g>
</svg>

A bigger letter is only popped when a later copy of it guarantees it can be pushed again.

## 5. Runnable example

**Level 1 — Brute force.** Try every subset of unique letters that preserves relative order, and keep the smallest one lexicographically. Exponential, infeasible beyond tiny strings.

**KEY INSIGHT:** a bigger letter blocking a smaller one should be removed now, but only if it is guaranteed to reappear later — the frequency count and the "already in stack" check together make that safe.

**Level 2 — Optimal.** Increasing monotonic stack with a remaining-count check and a "currently in stack" guard, O(n).

**Level 3 — Hardened.** Handles a string where no removal is possible (all letters strictly increasing) and repeated letters with no smaller letter ever displacing them.

```java
// RemoveDuplicateLetters.java
public class RemoveDuplicateLetters {

    // Level 2 & 3: increasing monotonic stack with occurrence lookahead, O(n)
    static String removeDuplicateLetters(String s) {
        int[] lastIndex = new int[26];
        for (int i = 0; i < s.length(); i++) {
            lastIndex[s.charAt(i) - 'a'] = i; // remember the LAST position of each letter
        }

        boolean[] inStack = new boolean[26];
        StringBuilder stack = new StringBuilder();

        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (inStack[c - 'a']) continue; // this letter is already in the result

            while (stack.length() > 0
                    && stack.charAt(stack.length() - 1) > c
                    && lastIndex[stack.charAt(stack.length() - 1) - 'a'] > i) {
                // the top letter is bigger AND it reappears after index i -- safe to drop now
                inStack[stack.charAt(stack.length() - 1) - 'a'] = false;
                stack.deleteCharAt(stack.length() - 1);
            }

            stack.append(c);
            inStack[c - 'a'] = true;
        }

        return stack.toString();
    }

    public static void main(String[] args) {
        System.out.println(removeDuplicateLetters("cbacdcbc")); // "acdb"
        System.out.println(removeDuplicateLetters("bcabc"));    // "abc"
        System.out.println(removeDuplicateLetters("abcd"));     // "abcd" (already optimal)
    }
}
```

**How to run:** save as `RemoveDuplicateLetters.java`, then run `java RemoveDuplicateLetters.java`.

## 6. Walkthrough

`lastIndex` for `"cbacdcbc"` (0-indexed): `c` → 7, `b` → 6, `a` → 2, `d` → 4.

| i | char | stack before | check | action | stack after |
|---|---|---|---|---|---|
| 0 | c | "" | not in stack | push | "c" |
| 1 | b | "c" | top 'c'>'b' and lastIndex[c]=7>1 | pop 'c'; push 'b' | "b" |
| 2 | a | "b" | top 'b'>'a' but lastIndex[b]=6>2 | pop 'b'; push 'a' | "a" |
| 3 | c | "a" | 'a' not > 'c' | push | "ac" |
| 4 | d | "ac" | 'c' not > 'd' | push | "acd" |
| 5 | c | "acd" | already in stack | skip | "acd" |
| 6 | b | "acd" | top 'd'>'b' but lastIndex[d]=4, not >6 | keep 'd'; push 'b' | "acdb" |
| 7 | c | "acdb" | already in stack | skip | "acdb" |

Final result: `"acdb"`, matching the expected output. (At `i=2`, `b` does get popped because `lastIndex[b]=6 > 2` — a later `b` still exists, so it is safe to drop it now and pick it up again at `i=6`.)

## 7. Gotchas & takeaways

> Gotcha: popping a stack-top letter without checking `lastIndex[top] > i` can permanently delete a letter that never reappears, producing a result missing that letter entirely — always check the letter still has a future occurrence before popping it.

- This builds on [Remove K Digits](0475-remove-k-digits.md): same increasing-stack shape, but the removal condition is "reappears later," not a fixed count `k`.
- Skip a character entirely if it is already in the stack — every letter appears exactly once in the final answer.
- Time: O(n) — one pass to record last indices, one pass to build the stack; the alphabet size (26) bounds any nested work.
