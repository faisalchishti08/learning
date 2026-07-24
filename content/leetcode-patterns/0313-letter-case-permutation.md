---
card: leetcode-patterns
gi: 313
slug: letter-case-permutation
title: Letter Case Permutation
---

## 1. What it is

Given a string `s`, return all strings that can be formed by changing the case of any subset of its LETTERS (digits stay unchanged). Return the results in any order. Example: `s = "a1b2"` → `["a1b2","a1B2","A1b2","A1B2"]`.

## 2. Why & when

This is a binary-choice backtracking problem: for each LETTER, you have exactly 2 choices (lowercase or uppercase); digits have exactly 1 choice (leave unchanged). Use this shape whenever every position in the input independently offers a small, fixed set of choices, and you want every combination of those choices.

## 3. Core concept

**Key idea:** build the result one character at a time. At each position, if the character is a digit, there is only one choice (keep it); if it is a letter, branch into two choices (lowercase and uppercase).

**Steps:**
1. Define `backtrack(index, currentChars)`, where `currentChars` is a mutable character array being built.
2. **Base case:** if `index == s.length()`, the whole string has been decided — record `new String(currentChars)` as one result, and return.
3. **If `s.charAt(index)` is a digit:** set `currentChars[index] = s.charAt(index)` (no choice to make), recurse to `index + 1` (no un-choose needed, since nothing was branched).
4. **If `s.charAt(index)` is a letter:** try `currentChars[index] = toLowerCase(...)`, recurse; then try `currentChars[index] = toUpperCase(...)`, recurse.

**Why it is correct:** every position independently contributes either 1 choice (digit) or 2 choices (letter) to the final string, and the recursion explores every COMBINATION of these independent choices across all positions, since each recursive call fixes exactly one more position before moving to the next. Because `currentChars` is fully overwritten at each index (not appended), there is no need for a separate un-choose step — the next branch at the same position simply overwrites the same slot.

## 4. Diagram

<svg viewBox="0 0 480 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Binary branching tree for the string a1b, showing 2 choices at each letter position and 1 choice at the digit position">
  <g font-family="sans-serif" font-size="12" fill="#e6edf3">
    <text x="10" y="20" font-weight="bold">s = "a1b"</text>
    <text x="10" y="45">index 0 ('a', letter): branch into 'a' and 'A'</text>
    <text x="10" y="65">index 1 ('1', digit): only one choice, '1'</text>
    <text x="10" y="85">index 2 ('b', letter): branch into 'b' and 'B'</text>
    <rect x="10" y="100" width="260" height="24" fill="#3fb950"/><text x="140" y="117" fill="#0d1117" text-anchor="middle" font-size="10">results: a1b, a1B, A1b, A1B</text>
  </g>
</svg>

Digits contribute a single forced choice; letters double the number of branches at their position.

## 5. Runnable example

```java
// LetterCasePermutation.java
import java.util.*;

public class LetterCasePermutation {

    // KEY INSIGHT: each position offers either 1 choice (digit) or 2
    // choices (letter, upper/lower); overwriting the same array index
    // at each branch avoids needing an explicit un-choose step.

    static List<String> letterCasePermutation(String s) {
        List<String> results = new ArrayList<>();
        backtrack(s.toCharArray(), 0, results);
        return results;
    }

    static void backtrack(char[] chars, int index, List<String> results) {
        if (index == chars.length) {
            results.add(new String(chars));
            return;
        }

        char c = chars[index];
        if (Character.isDigit(c)) {
            backtrack(chars, index + 1, results); // only one choice, no branch
        } else {
            chars[index] = Character.toLowerCase(c);
            backtrack(chars, index + 1, results);  // choice 1: lowercase

            chars[index] = Character.toUpperCase(c);
            backtrack(chars, index + 1, results);  // choice 2: uppercase
        }
    }

    public static void main(String[] args) {
        System.out.println(letterCasePermutation("a1b2"));
        // [a1b2, a1B2, A1b2, A1B2]
        System.out.println(letterCasePermutation("3z4"));
        // [3z4, 3Z4]
    }
}
```

**How to run:** `java LetterCasePermutation.java`

## 6. Walkthrough

Trace `letterCasePermutation("a1b")`:

| index | char | choices | branches taken |
|---|---|---|---|
| 0 | 'a' (letter) | 'a', 'A' | recurse into both |
| 1 (from 'a' branch) | '1' (digit) | '1' only | recurse forward |
| 2 (from 'a','1' branch) | 'b' (letter) | 'b', 'B' | recurse into both -&gt; records "a1b" and "a1B" |
| 1 (from 'A' branch) | '1' (digit) | '1' only | recurse forward |
| 2 (from 'A','1' branch) | 'b' (letter) | 'b', 'B' | recurse into both -&gt; records "A1b" and "A1B" |

Final results: `["a1b", "a1B", "A1b", "A1B"]`. Time complexity is O(2^L · L), where `L` is `s.length()` and `L` is the number of LETTERS specifically: `2^L` results, each O(s.length()) to construct as a string. Space is O(s.length()) for the recursion depth and the character array.

## 7. Gotchas & takeaways

> Gotcha: overwriting `chars[index]` directly (instead of building a NEW array or string at each branch) means you must fully set `chars[index]` before EVERY recursive call at that position — forgetting to set it for the digit case (assuming it is "already correct" from the original string) would only work because the array was initialized from `s.toCharArray()`, which happens to be true here but is a fragile assumption to rely on.

- This is one of the simplest backtracking problems: no pruning is ever needed, since every choice at every position is always valid.
- The branching factor here is determined by CHARACTER TYPE (digit = 1 branch, letter = 2 branches), a useful pattern whenever different positions in an input have different numbers of valid choices.
- Related problems: Subsets (binary choice: include or exclude each element), Combinations (a bounded selection from a pool, using a `start` index instead of a fixed choice count per position).
