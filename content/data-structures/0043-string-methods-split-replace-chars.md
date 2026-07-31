---
card: data-structures
gi: 43
slug: string-methods-split-replace-chars
title: String methods (split, replace, chars)
---

## 1. What it is

`String` has a large built-in API beyond `substring` and `indexOf` for common text transformations. `split(regex)` breaks a string into an array of pieces using a regular-expression delimiter. `replace`/`replaceAll` swap occurrences of one piece of text for another. `chars()` returns a stream of the string's individual characters (as `int` code points), enabling functional-style processing.

## 2. Why & when

These methods cover the everyday text-processing tasks you would otherwise hand-write loops for: parsing CSV-like lines (`split(",")`), sanitizing input (`replaceAll("[^a-zA-Z0-9]", "")`), or counting/filtering characters functionally (`chars().filter(...)`). Knowing their exact behavior (especially `split`'s regex nature and trailing-empty-string handling) avoids subtle bugs.

## 3. Core concept

**`split(regex)` takes a regular expression, not a literal string.** `"a.b.c".split(".")` does NOT split on the literal dot — `.` in regex means "any character," so it splits on every character, producing empty strings. To split on a literal dot, escape it: `split("\\.")`, or use `Pattern.quote(".")`.

**`replace` is literal; `replaceAll` is regex-based.** `s.replace("a.b", "X")` looks for the exact literal text `"a.b"`. `s.replaceAll("a.b", "X")` treats `"a.b"` as a regex, matching `"a"`, any character, then `"b"` — these can silently give different results for the same-looking input if it contains regex metacharacters.

**`split` drops trailing empty strings by default.** `"a,b,,".split(",")` produces `["a", "b"]`, silently dropping the trailing empty pieces — pass a negative limit (`split(",", -1)`) to keep them, if that matters for your data (e.g. parsing a CSV row where trailing empty fields are meaningful).

**`chars()` returns an `IntStream` of code points, not `char`s.** This is a deliberate design choice tied to Unicode: some Unicode characters need more than one `char` (see [Character encoding (UTF-8 / UTF-16)](0038-character-encoding-utf-8-utf-16.md)), so streaming as `int` code points (via `codePoints()`) rather than raw `char` values is the correct way to handle the full character set; `chars()` itself streams UTF-16 code units for simpler, common cases.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="split(a period) treated as regex matching any character, versus split with an escaped period matching a literal dot">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="16" fill="#8b949e" text-anchor="middle">"a.b.c".split(".") -- "." is regex "any char"</text>
    <rect x="60" y="30" width="200" height="26" fill="#161b22" stroke="#f0883e"/><text x="160" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">result: [] (all chars match the delimiter)</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">"a.b.c".split("\\.") -- escaped, literal dot</text>
    <rect x="380" y="30" width="200" height="26" fill="#161b22" stroke="#3fb950"/><text x="480" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">result: [a, b, c]</text>
    <text x="320" y="110" fill="#79c0ff" text-anchor="middle">split() always takes a REGEX -- escape regex metacharacters for literal splitting</text>
  </g>
</svg>

An unescaped `.` in `split()` matches every character, not a literal dot — always escape regex metacharacters when you mean the literal symbol.

## 5. Runnable example

```java
// StringMethodsSplitReplaceChars.java
import java.util.Arrays;

public class StringMethodsSplitReplaceChars {

    // Basic: split on a literal comma (not a regex metacharacter, so no escaping needed).
    static void basicLevel() {
        String csv = "apple,banana,cherry";
        String[] parts = csv.split(",");
        System.out.println("basic: split(\",\") -> " + Arrays.toString(parts));
    }

    // Intermediate: the split(regex) trap -- unescaped "." matches any character.
    static void intermediateLevel() {
        String dotted = "a.b.c";
        String[] wrong = dotted.split(".");     // "." is regex for "any character" -- matches everything
        String[] correct = dotted.split("\\.");  // escaped: matches a literal dot only

        System.out.println("intermediate: split(\".\") (wrong) -> " + wrong.length + " pieces");
        System.out.println("intermediate: split(\"\\\\.\") (correct) -> " + Arrays.toString(correct));
    }

    // Advanced: replace (literal) vs replaceAll (regex), and chars() for functional-style counting.
    static void advancedLevel() {
        String text = "price: $5.99, discount: $1.00";

        String literalReplace = text.replace("$", "USD "); // literal "$" replaced everywhere
        System.out.println("advanced: replace (literal) -> " + literalReplace);

        String regexReplace = text.replaceAll("\\d+\\.\\d+", "X.XX"); // regex: replace all decimal numbers
        System.out.println("advanced: replaceAll (regex) -> " + regexReplace);

        long digitCount = text.chars().filter(Character::isDigit).count(); // functional-style character counting
        System.out.println("advanced: digit count via chars() -> " + digitCount);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StringMethodsSplitReplaceChars.java`, then run `java StringMethodsSplitReplaceChars.java`.

## 6. Walkthrough

1. `basicLevel()` splits `"apple,banana,cherry"` on `","`, a plain character with no special regex meaning, giving the expected `["apple", "banana", "cherry"]`.
2. `intermediateLevel()` splits `"a.b.c"` on `"."` — since `.` is a regex wildcard matching any character, every single character in the string "matches the delimiter," producing an array of only empty strings (length reflects this misuse). Splitting on the escaped `"\\."` instead correctly treats the dot as a literal character, giving `["a", "b", "c"]`.
3. `advancedLevel()`'s `text.replace("$", "USD ")` performs a literal, character-for-character replacement of every `$` — straightforward, no regex involved.
4. `text.replaceAll("\\d+\\.\\d+", "X.XX")` treats its argument as a regex matching "one or more digits, a literal dot, one or more digits" — it finds and replaces both `"5.99"` and `"1.00"` with `"X.XX"`, since both match that decimal-number pattern.
5. `text.chars().filter(Character::isDigit).count()` streams every character of `text` as an `int` code point, keeps only the ones that are digits, and counts them — a concise functional alternative to a manual loop with an `if` check.

## 7. Gotchas & takeaways

> Gotcha: `split(regex)` silently drops trailing empty strings by default — `"a,b,,".split(",")` returns `["a", "b"]`, not `["a", "b", "", ""]`. If trailing empty fields matter (e.g. parsing a CSV row where an empty last column is meaningful), use the two-argument form with a negative limit: `split(",", -1)`.

- `split()` always takes a regular expression — escape regex metacharacters (like `.`, `*`, `+`) when you want a literal split character.
- `replace` does a literal substring replacement; `replaceAll` (and `replaceFirst`) treat their target as a regex — they can behave very differently on the same input.
- `chars()` streams UTF-16 code units as `int` values, enabling functional-style filtering and counting without a manual loop.
- Related concepts: [Substring, indexOf & searching](0037-substring-indexof-searching.md), [Character encoding (UTF-8 / UTF-16)](0038-character-encoding-utf-8-utf-16.md).
