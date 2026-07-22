---
card: leetcode-patterns
gi: 221
slug: letter-combinations-of-a-phone-number
title: Letter Combinations of a Phone Number
---

## 1. What it is

Given a string `digits` (each digit `2`-`9`, matching an old phone keypad's letter groupings), return all possible letter combinations the number could represent — one letter per digit, trying every letter for every digit. Example: `digits = "23"` → `["ad","ae","af","bd","be","bf","cd","ce","cf"]`.

## 2. Why & when

This is a DFS backtracking tree where each POSITION (digit) has a small, FIXED set of choices (its 3 or 4 mapped letters), rather than choosing among the whole remaining input. It is a direct application of "try every choice at this position, recurse to the next position, backtrack" — no `start` index or `used` array needed, since positions are processed strictly left to right and each digit's own letter set is separate.

## 3. Core concept

**Key idea:** a lookup table maps each digit to its letters (e.g. `'2' -> "abc"`). DFS processes `digits` one character at a time; at each position, try every letter in that digit's mapped set, appending it to the partial string, recursing to the NEXT digit, then removing it (backtrack) before trying the next letter.

**Steps:**
1. If `digits` is empty, return an empty result list immediately (no valid combinations, an edge case worth checking first).
2. Build (or hardcode) the digit-to-letters lookup table.
3. Call a recursive helper with an empty partial string (or `StringBuilder`) and an index of `0` into `digits`.
4. Base case: if the index equals `digits.length()`, save a copy of the partial string and return.
5. Otherwise, look up the letters for `digits[index]`, and for each letter: append it, recurse with `index + 1`, then remove the last character (backtrack) before trying the next letter.

**Why it is correct:** processing digits strictly left to right, trying every mapped letter at each position, and recursing to the NEXT digit only after committing to a letter for the CURRENT one, generates every possible combination of one letter per digit exactly once — since each position's choice is independent of the others and the tree's depth exactly matches `digits.length()`.

## 4. Diagram

<svg viewBox="0 0 460 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each digit position branches into its mapped letters; depth equals the number of digits">
  <g font-family="sans-serif" font-size="12">
    <circle cx="100" cy="30" r="4" fill="#e6edf3"/>
    <line x1="100" y1="30" x2="60" y2="70" stroke="#3fb950"/><text x="40" y="85" fill="#3fb950" font-size="10">'a'</text>
    <line x1="100" y1="30" x2="100" y2="70" stroke="#79c0ff"/><text x="100" y="85" fill="#79c0ff" font-size="10">'b'</text>
    <line x1="100" y1="30" x2="140" y2="70" stroke="#e3b341"/><text x="150" y="85" fill="#e3b341" font-size="10">'c'</text>
    <circle cx="60" cy="70" r="4" fill="#e6edf3"/><circle cx="100" cy="70" r="4" fill="#e6edf3"/><circle cx="140" cy="70" r="4" fill="#e6edf3"/>
    <text x="10" y="15" fill="#e6edf3">digit '2' branches into its 3 letters; each child then branches into the NEXT digit's letters</text>
  </g>
</svg>

Each level of the tree corresponds to one digit's position; the branching factor at each level is that digit's number of mapped letters (3 or 4).

## 5. Runnable example

```java
// LetterCombinationsOfAPhoneNumber.java
import java.util.*;

public class LetterCombinationsOfAPhoneNumber {

    // Level 1 -- Brute force: compute the total combination count
    // (product of each digit's letter count) up front, then build each
    // combination via repeated index-math (like converting a number to
    // a mixed-radix representation) instead of recursion. Correct, and
    // actually similarly efficient, but far less readable and harder
    // to adapt to variants with extra constraints than the DFS
    // backtracking shape.

    // KEY INSIGHT: DFS one digit at a time, trying every mapped letter
    // at each position and recursing to the next digit -- a direct,
    // readable mirror of "one choice per position" that generalizes
    // easily.

    // Level 2 -- Optimal: DFS backtracking over positions.
    static final String[] LETTERS = {"", "", "abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"};

    static List<String> letterCombinations(String digits) {
        List<String> result = new ArrayList<>();
        if (digits.isEmpty()) return result;
        dfs(digits, 0, new StringBuilder(), result);
        return result;
    }

    static void dfs(String digits, int index, StringBuilder path, List<String> result) {
        if (index == digits.length()) {
            result.add(path.toString());
            return;
        }
        String letters = LETTERS[digits.charAt(index) - '0'];
        for (char c : letters.toCharArray()) {
            path.append(c);
            dfs(digits, index + 1, path, result);
            path.deleteCharAt(path.length() - 1);
        }
    }

    // Level 3 -- Hardened: the empty-string check at the top of
    // `letterCombinations` avoids returning `[""]` (a single empty
    // combination) for empty input -- the problem expects an empty
    // result list instead.

    public static void main(String[] args) {
        System.out.println(letterCombinations("23"));
        // [ad, ae, af, bd, be, bf, cd, ce, cf]
        System.out.println(letterCombinations(""));
        // []
    }
}
```

**How to run:** `java LetterCombinationsOfAPhoneNumber.java`

## 6. Walkthrough

Trace `dfs("23", 0, "", result)`:

| Call | index | path | letters tried |
|---|---|---|---|
| dfs(0) | 0 | "" | letters for '2' = "abc" |
| → dfs(1) via 'a' | 1 | "a" | letters for '3' = "def" |
| → → dfs(2) via 'd' | 2 | "ad" | index==2==length, save "ad" |
| back, try 'e' | 1 | "a" | save "ae" |
| back, try 'f' | 1 | "a" | save "af" |
| back to dfs(0), try 'b' | 0 | "" | repeat for "bd","be","bf" |
| back to dfs(0), try 'c' | 0 | "" | repeat for "cd","ce","cf" |

All 9 combinations (`3 letters × 3 letters`) are produced. Time complexity is O(4ⁿ · n), where n is the digit count (4 being the max letters per digit, for digits 7 and 9), since there are up to 4ⁿ combinations each costing O(n) to build; space is O(4ⁿ · n) for the output, plus O(n) for the recursion stack.

## 7. Gotchas & takeaways

> Gotcha: forgetting the empty-`digits` check returns `[""]` (treating the empty input as producing one empty combination) instead of the expected empty result list `[]` — an easy edge case to miss since the recursive base case alone does not distinguish "zero digits" from "just finished the last digit."

- No `start` index or `used` array is needed here — positions are processed strictly in order, and each digit contributes its own independent set of choices, unlike subsets/permutations where the SAME set of elements is shared across all positions.
- `StringBuilder` with `append`/`deleteCharAt` is more efficient than string concatenation (`path + c`) for the backtracking add/remove cycle, since string concatenation would allocate a new string at every step.
- Related problems: Generate Parentheses (DFS backtracking with a validity constraint instead of a fixed lookup table), Combinations (DFS backtracking over a shared, single, index-based `start`).
