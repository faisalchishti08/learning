---
card: leetcode-patterns
gi: 10
slug: reverse-string
title: Reverse String
---

## 1. What it is

Given a character array `s`, reverse it in place, using O(1) extra memory. Example: `s = ['h','e','l','l','o']` → after the operation, `['o','l','l','e','h']`.

## 2. Why & when

"Reverse in place" with "O(1) extra memory" is the purest form of the opposite-ends two-pointers signal: no target sum, no condition — just swap the outermost pair, then the next pair inward, and so on.

## 3. Core concept

**Key idea:** reversing an array means the element at position `i` and the element at position `length - 1 - i` should trade places, for every `i` up to the midpoint.

**Steps:**
1. Set `left = 0` and `right = s.length - 1`.
2. While `left < right`: swap `s[left]` and `s[right]`, then `left++`, `right--`.
3. Stop when `left >= right` — the middle element (if the length is odd) never needs to move.

**Why it is correct:** each swap places both `s[left]` and `s[right]` in their final reversed position simultaneously. Since `left` and `right` sweep inward and meet in the middle, every pair gets swapped exactly once, and the loop naturally stops before swapping a pair twice (which would undo the work).

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reverse string swapping outer pairs inward">
  <g font-family="sans-serif" font-size="13">
    <rect x="20" y="20" width="44" height="34" fill="#161b22" stroke="#79c0ff"/>
    <rect x="64" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="108" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="152" y="20" width="44" height="34" fill="#161b22" stroke="#30363d"/>
    <rect x="196" y="20" width="44" height="34" fill="#161b22" stroke="#f0883e"/>
    <text x="42" y="43" fill="#e6edf3" text-anchor="middle">h</text>
    <text x="86" y="43" fill="#e6edf3" text-anchor="middle">e</text>
    <text x="130" y="43" fill="#e6edf3" text-anchor="middle">l</text>
    <text x="174" y="43" fill="#e6edf3" text-anchor="middle">l</text>
    <text x="218" y="43" fill="#e6edf3" text-anchor="middle">o</text>
    <path d="M42,60 C42,90 218,90 218,60" stroke="#8b949e" fill="none" marker-end="url(#a2)"/>
    <path d="M218,10 C218,-10 42,-10 42,10" stroke="#8b949e" fill="none" marker-end="url(#a2)" transform="translate(0,20)"/>
    <text x="130" y="115" fill="#8b949e" text-anchor="middle">swap(left, right), then move both inward</text>
  </g>
  <defs>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each swap fixes one pair into its final reversed position; the pointers meet at the middle.

## 5. Runnable example

```java
// ReverseString.java
import java.util.Arrays;

public class ReverseString {

    // Level 1 -- Brute force: build a new array by reading the input
    // backward. O(n) time, O(n) space -- ignores the O(1) space constraint.
    static char[] bruteForce(char[] s) {
        char[] result = new char[s.length];
        for (int i = 0; i < s.length; i++) {
            result[i] = s[s.length - 1 - i];
        }
        return result;
    }

    // KEY INSIGHT: reversing is a pure position swap between mirrored
    // indices -- no comparison or condition needed, just walk both ends
    // inward and trade values.

    // Level 2 -- Optimal: two pointers, in-place swap. O(n) time, O(1) space.
    public static void reverseString(char[] s) {
        int left = 0, right = s.length - 1;
        while (left < right) {
            char tmp = s[left];
            s[left] = s[right];
            s[right] = tmp;
            left++;
            right--;
        }
    }

    // Level 3 -- Hardened: empty array and single-character array both
    // satisfy left < right trivially (false immediately), so no separate
    // case is needed.
    static void hardened(char[] s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        reverseString(s);
    }

    public static void main(String[] args) {
        char[] s = {'h', 'e', 'l', 'l', 'o'};
        System.out.println("brute force: " + Arrays.toString(bruteForce(s)));

        reverseString(s);
        System.out.println("optimal:     " + Arrays.toString(s));

        char[] single = {'x'};
        hardened(single);
        System.out.println("single char: " + Arrays.toString(single));
    }
}
```

How to run: save as `ReverseString.java`, then run `java ReverseString.java`.

## 6. Walkthrough

Dry run of `reverseString({'h','e','l','l','o'})`:

| step | left | right | swap | array after |
|---|---|---|---|---|
| 1 | 0 | 4 | 'h' <-> 'o' | [o,e,l,l,h] |
| 2 | 1 | 3 | 'e' <-> 'l' | [o,l,l,e,h] |
| 3 | 2 | 2 | loop stops (left == right) | [o,l,l,e,h] |

Final array: `['o','l','l','e','h']`. The middle character `'l'` at index 2 never moves, because the loop stops once `left` and `right` meet. Time complexity: O(n), each pointer traverses half the array. Space complexity: O(1).

## 7. Gotchas & takeaways

> Gotcha: using `left <= right` instead of `left < right` swaps the middle character with itself on an odd-length array — harmless here, but it signals a misunderstanding of the loop invariant and can cause real bugs in similar patterns where the middle needs special handling.

- This is the simplest possible opposite-ends two-pointers problem: no comparison logic, just an unconditional swap.
- The same swap-and-converge idea appears any time a problem says "reverse in place" or "mirror an array."
- Related problems: Reverse Vowels of a String (swap only vowel positions), Valid Palindrome, Rotate Array.
