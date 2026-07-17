---
card: leetcode-patterns
gi: 15
slug: reverse-vowels-of-a-string
title: Reverse Vowels of a String
---

## 1. What it is

Given a string `s`, reverse only the vowels (`a, e, i, o, u`, both cases) and leave every other character in its original position. Example: `s = "hello"` → `"holle"` (the `e` and `o` swap; consonants stay put).

## 2. Why & when

This is opposite-ends two pointers with an added filter: instead of swapping every outer pair unconditionally (like Reverse String), you swap only when *both* pointers are sitting on vowels — skipping consonants without moving them.

## 3. Core concept

**Key idea:** consonants are invisible to this algorithm; only the relative order of vowels matters, and reversing that order in place is exactly a filtered version of the Reverse String swap.

**Steps:**
1. Convert `s` to a `char[]` so it can be mutated (Java strings are immutable).
2. Set `left = 0`, `right = s.length() - 1`.
3. While `left < right`:
   - If `chars[left]` is not a vowel, `left++`, continue.
   - If `chars[right]` is not a vowel, `right--`, continue.
   - Otherwise both are vowels — swap them, then `left++`, `right--`.
4. Return the array as a new string.

**Why it is correct:** skipping non-vowels independently on each side means each pointer only stops on positions that need to participate in a swap. Since both pointers only ever move inward, and a swap only happens when both are on vowels, every vowel gets paired with its mirror-position vowel exactly once.

## 4. Diagram

<svg viewBox="0 0 700 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reverse vowels skipping consonants">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="24" fill="#e6edf3">s = "hello"</text>
    <rect x="20" y="40" width="40" height="30" fill="#161b22" stroke="#79c0ff"/>
    <rect x="60" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="100" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="140" y="40" width="40" height="30" fill="#161b22" stroke="#30363d"/>
    <rect x="180" y="40" width="40" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="40" y="60" fill="#e6edf3" text-anchor="middle">h</text>
    <text x="80" y="60" fill="#e6edf3" text-anchor="middle">e</text>
    <text x="120" y="60" fill="#e6edf3" text-anchor="middle">l</text>
    <text x="160" y="60" fill="#e6edf3" text-anchor="middle">l</text>
    <text x="200" y="60" fill="#e6edf3" text-anchor="middle">o</text>
    <text x="20" y="100" fill="#8b949e">'h' not a vowel -&gt; left++ (skip, no swap)</text>
    <text x="20" y="122" fill="#8b949e">'e' and 'o' both vowels -&gt; swap -&gt; "holle"</text>
  </g>
</svg>

Each pointer independently skips consonants; a swap only fires once both land on vowels.

## 5. Runnable example

```java
// ReverseVowels.java
public class ReverseVowels {

    private static boolean isVowel(char c) {
        c = Character.toLowerCase(c);
        return c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u';
    }

    // Level 1 -- Brute force: collect all vowel positions and values into a
    // list, reverse the list, then write the reversed values back at the
    // recorded positions. O(n) time, O(n) extra space for the list.
    static String bruteForce(String s) {
        char[] chars = s.toCharArray();
        java.util.List<Integer> positions = new java.util.ArrayList<>();
        java.util.List<Character> vowels = new java.util.ArrayList<>();
        for (int i = 0; i < chars.length; i++) {
            if (isVowel(chars[i])) {
                positions.add(i);
                vowels.add(chars[i]);
            }
        }
        java.util.Collections.reverse(vowels);
        for (int k = 0; k < positions.size(); k++) {
            chars[positions.get(k)] = vowels.get(k);
        }
        return new String(chars);
    }

    // KEY INSIGHT: skipping non-vowels independently on each pointer, then
    // swapping only when both land on vowels, reverses just the vowels'
    // order in one in-place pass -- no separate list needed.

    // Level 2 -- Optimal: two pointers with a skip condition. O(n) time,
    // O(n) space only for the mutable char array (required since Java
    // strings are immutable); O(1) beyond that.
    public static String reverseVowels(String s) {
        char[] chars = s.toCharArray();
        int left = 0, right = chars.length - 1;
        while (left < right) {
            if (!isVowel(chars[left])) { left++; continue; }
            if (!isVowel(chars[right])) { right--; continue; }
            char tmp = chars[left];
            chars[left] = chars[right];
            chars[right] = tmp;
            left++;
            right--;
        }
        return new String(chars);
    }

    // Level 3 -- Hardened: a string with no vowels, or all vowels, both
    // work with the same loop -- no vowels means the swap branch never
    // fires; all vowels means it fires on every step, same as Reverse String.
    static String hardened(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        return reverseVowels(s);
    }

    public static void main(String[] args) {
        System.out.println("brute force: " + bruteForce("hello"));
        System.out.println("optimal:     " + reverseVowels("hello"));
        System.out.println("no vowels:   " + hardened("xyz"));
    }
}
```

How to run: save as `ReverseVowels.java`, then run `java ReverseVowels.java`.

## 6. Walkthrough

Dry run of `reverseVowels("hello")`, starting from `chars = ['h','e','l','l','o']`:

| step | left | right | chars[left] | chars[right] | action |
|---|---|---|---|---|---|
| 1 | 0 | 4 | h (not vowel) | o | left++ |
| 2 | 1 | 4 | e (vowel) | o (vowel) | swap -> chars = [h,o,l,l,e]; left++, right-- |
| 3 | 2 | 3 | l (not vowel) | l | left++ |

After step 3, `left = 3 = right`, so the loop stops. Final string: `"holle"`. Time complexity: O(n). Space complexity: O(n) for the mutable copy, O(1) auxiliary.

## 7. Gotchas & takeaways

> Gotcha: checking only lowercase vowels (`a, e, i, o, u`) misses uppercase ones like `'A'` or `'E'` — always lowercase the character (or check both cases) before comparing.

- Java strings are immutable, so you must convert to a `char[]` (or `StringBuilder`) before doing in-place swaps.
- This is Reverse String plus a skip condition on each pointer — recognizing that relationship means you do not need to re-derive the logic from scratch.
- Related problems: Reverse String, Valid Palindrome, Reverse Words in a String.
