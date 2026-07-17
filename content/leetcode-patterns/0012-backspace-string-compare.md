---
card: leetcode-patterns
gi: 12
slug: backspace-string-compare
title: Backspace String Compare
---

## 1. What it is

Given two strings `s` and `t`, where `#` means a backspace character (it deletes the previous character, if any), return `true` if the two strings are equal after applying all the backspaces. Example: `s = "ab#c"`, `t = "ad#c"` → both become `"ac"`, so return `true`.

## 2. Why & when

The brute-force approach builds the final string for each input using a stack (push normal characters, pop on `#`), then compares the two results — O(n + m) time and O(n + m) space for the two stacks. The two-pointers trick avoids building either final string, by comparing both strings **from the back**, using O(1) extra space: the last character is the one least affected by earlier backspaces, so reading backward is exactly what lets each pointer resolve its own pending backspaces on the fly.

## 3. Core concept

**Key idea:** reading a string backward, a `#` means "skip the next real character I encounter," because that character will end up deleted once you account for the backspace. This is same-direction two pointers, but both pointers move backward together instead of forward.

**Steps:**
1. Define a helper: given a string and a starting index, walk backward, and return the index of the next "surviving" character (skipping any that are cancelled out by a pending `#`).
2. Set `i = s.length() - 1`, `j = t.length() - 1`.
3. Loop: find the next surviving character in `s` at or before `i`, and in `t` at or before `j`, using the helper.
4. If one string has a surviving character and the other does not, they differ — return `false`.
5. If both have none left, they are equal — return `true`.
6. Otherwise compare the two surviving characters; if they differ, return `false`; if they match, move both `i` and `j` one step past the found position and repeat.

**Why it is correct:** processing from the back means every `#` you see immediately tells you which upcoming (leftward) character to discard, with no need to know about backspaces that come *later* (rightward) — those have already been consumed. This mirrors how a stack processes the string forward and pops on `#`, but walking backward removes the need to actually store the stack.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Backspace compare scanning from the back with skip counters">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "ab#c"   read backward: c, #, b, a</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">a</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">b</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">#</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">c</text>
    <text x="20" y="95" fill="#8b949e">i=3 'c' survives (no skip pending) -&gt; compare directly</text>
    <text x="20" y="118" fill="#8b949e">i=2 '#' -&gt; skip=1, i=1 'b' cancelled by skip -&gt; i=0 'a' survives</text>
    <text x="20" y="141" fill="#8b949e">no stack built -- backward scan resolves backspaces on the fly</text>
  </g>
</svg>

Scanning backward, each `#` sets up a pending skip that cancels the next real character encountered.

## 5. Runnable example

```java
// BackspaceCompare.java
public class BackspaceCompare {

    // Level 1 -- Brute force: build each final string with a stack, then
    // compare. O(n + m) time, O(n + m) space for the two stacks.
    static boolean bruteForce(String s, String t) {
        return build(s).equals(build(t));
    }

    private static String build(String str) {
        StringBuilder stack = new StringBuilder();
        for (char c : str.toCharArray()) {
            if (c == '#') {
                if (stack.length() > 0) stack.deleteCharAt(stack.length() - 1);
            } else {
                stack.append(c);
            }
        }
        return stack.toString();
    }

    // KEY INSIGHT: reading backward, a '#' only ever needs to cancel the
    // NEXT character encountered going backward -- so a single skip counter
    // per string replaces the whole stack.

    // Level 2 -- Optimal: two pointers from the back. O(n + m) time, O(1)
    // extra space.
    public static boolean backspaceCompare(String s, String t) {
        int i = s.length() - 1, j = t.length() - 1;
        while (i >= 0 || j >= 0) {
            i = nextSurvivor(s, i);
            j = nextSurvivor(t, j);
            boolean iHas = i >= 0, jHas = j >= 0;
            if (iHas != jHas) return false;
            if (!iHas) return true; // both exhausted, equal so far
            if (s.charAt(i) != t.charAt(j)) return false;
            i--;
            j--;
        }
        return true;
    }

    // Walks backward from index `start`, skipping characters cancelled by
    // '#', and returns the index of the next surviving character, or -1.
    private static int nextSurvivor(String str, int start) {
        int skip = 0;
        while (start >= 0) {
            char c = str.charAt(start);
            if (c == '#') {
                skip++;
                start--;
            } else if (skip > 0) {
                skip--;
                start--;
            } else {
                return start;
            }
        }
        return -1;
    }

    // Level 3 -- Hardened: strings that are all backspaces (e.g. "###")
    // correctly resolve to empty, since nextSurvivor returns -1 immediately.
    static boolean hardened(String s, String t) {
        if (s == null || t == null) throw new IllegalArgumentException("s and t must not be null");
        return backspaceCompare(s, t);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("ab#c", "ad#c"));
        System.out.println("optimal:     " + backspaceCompare("ab#c", "ad#c"));
        System.out.println("all backspaces equal empty: " + hardened("a#c#", "b#c#"));
        System.out.println("different result: " + backspaceCompare("a#c", "b"));
    }
}
```

How to run: save as `BackspaceCompare.java`, then run `java BackspaceCompare.java`.

## 6. Walkthrough

Dry run of `backspaceCompare("ab#c", "ad#c")`:

| step | nextSurvivor(s) | nextSurvivor(t) | s char | t char | action |
|---|---|---|---|---|---|
| 1 | i=3 ('c') | j=3 ('c') | c | c | match, i=2, j=2 |
| 2 | i: skip '#' at 2, cancel 'b' at 1, land i=0 ('a') | j: skip '#' at 2, cancel 'd' at 1, land j=0 ('a') | a | a | match, i=-1, j=-1 |
| 3 | i=-1 | j=-1 | — | — | both exhausted, loop condition false, return true |

Both strings resolve to `"ac"`, confirmed without ever building that string. Time complexity: O(n + m). Space complexity: O(1) extra, beyond the input strings themselves.

## 7. Gotchas & takeaways

> Gotcha: comparing lengths of the built strings alone is not enough — `"ab#c"` and `"a#bc"` both build to different results (`"ac"` vs `"bc"`) despite similar-looking inputs, so you always need the actual character comparison, not just a length check.

- The backward scan needs a **per-pointer** skip counter — do not share one skip variable between `s` and `t`, since their backspaces are independent.
- The `iHas != jHas` check handles the case where one string still has characters left and the other has been fully cancelled out.
- Related problems: Valid Parentheses (stack-based), Remove All Adjacent Duplicates in String, Build Final String from Typing Sequence.
