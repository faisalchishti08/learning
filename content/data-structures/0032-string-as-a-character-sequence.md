---
card: data-structures
gi: 32
slug: string-as-a-character-sequence
title: String as a character sequence
---

## 1. What it is

A Java `String` is, under the hood, a wrapper around an array of characters (historically `char[]`; since Java 9, often a more compact `byte[]` with an encoding flag). Conceptually, a string is just an ordered sequence of characters with a known length — the same shape as an array, which is why indexing (`charAt`), slicing (`substring`), and length (`length()`) all work the way you would expect for a sequence.

## 2. Why & when

Thinking of a `String` as a character sequence — not a magical built-in type — explains its API and its costs. Every operation you already know from arrays applies conceptually: `charAt(i)` is O(1) random access, `length()` is a stored field read in O(1), and `substring` behaves like slicing an array. This mental model carries directly into string algorithms like two-pointer palindrome checks or sliding-window substring problems.

## 3. Core concept

**Internal layout: a backing array plus a length.** A `String` object holds a reference to its backing character data and (implicitly, via the array's own length) knows how many characters it contains. This mirrors an array's own header-plus-length-plus-data structure, covered in [Arrays as objects in the JVM](0013-arrays-as-objects-in-the-jvm.md).

**`charAt(i)` is O(1) random access.** Because characters are stored contiguously, the JVM computes the exact position of character `i` directly — no scanning required, exactly like array indexing.

**`String` also implements `CharSequence`.** `CharSequence` is a Java interface describing "a readable sequence of `char` values" with `length()`, `charAt(int)`, and `subSequence(int, int)`. `String`, `StringBuilder`, and `StringBuffer` all implement it, which is why methods that accept a `CharSequence` parameter work with any of the three.

**Iterating a string.** You can walk a string's characters with an indexed loop (`for (int i = 0; i < s.length(); i++) s.charAt(i)`) or convert it to a `char[]` with `toCharArray()` for repeated indexed access without the (small) per-call overhead of `charAt`.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A String object as a sequence of characters at contiguous indexed positions, indexed like an array">
  <g font-family="sans-serif" font-size="12">
    <text x="290" y="18" fill="#8b949e" text-anchor="middle">String s = "hello"</text>
    <rect x="90" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="110" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">h</text>
    <rect x="130" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="150" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">e</text>
    <rect x="170" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="190" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">l</text>
    <rect x="210" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="230" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">l</text>
    <rect x="250" y="30" width="40" height="30" fill="#161b22" stroke="#3fb950"/><text x="270" y="50" fill="#e6edf3" text-anchor="middle" font-size="11">o</text>
    <text x="110" y="80" fill="#8b949e" text-anchor="middle" font-size="10">index 0</text>
    <text x="270" y="80" fill="#8b949e" text-anchor="middle" font-size="10">index 4</text>
    <text x="290" y="115" fill="#79c0ff" text-anchor="middle">s.charAt(i) reads index i directly, O(1), same as array indexing</text>
  </g>
</svg>

Each character sits at a fixed, indexed position — `charAt(i)` reaches it directly, the same way `arr[i]` does for an array.

## 5. Runnable example

```java
// StringAsCharacterSequence.java
public class StringAsCharacterSequence {

    // Basic: indexed access and length, same shape as array operations.
    static void basicLevel() {
        String s = "hello";
        System.out.println("basic: length -> " + s.length());
        System.out.println("basic: charAt(1) -> " + s.charAt(1));
        System.out.println("basic: charAt(last) -> " + s.charAt(s.length() - 1));
    }

    // Intermediate: iterate two ways -- charAt in a loop, versus converting to a char[] first.
    static void intermediateLevel() {
        String s = "sequence";
        StringBuilder viaCharAt = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            viaCharAt.append(Character.toUpperCase(s.charAt(i)));
        }
        System.out.println("intermediate: via charAt loop -> " + viaCharAt);

        char[] chars = s.toCharArray(); // one-time O(n) copy into a real array
        StringBuilder viaArray = new StringBuilder();
        for (char c : chars) {
            viaArray.append(Character.toUpperCase(c));
        }
        System.out.println("intermediate: via toCharArray -> " + viaArray);
    }

    // Advanced: CharSequence lets one method accept String, StringBuilder, or StringBuffer alike.
    static boolean startsWithVowel(CharSequence seq) {
        if (seq.length() == 0) return false;
        char first = Character.toLowerCase(seq.charAt(0));
        return "aeiou".indexOf(first) >= 0;
    }

    static void advancedLevel() {
        System.out.println("advanced: String \"Apple\" -> " + startsWithVowel("Apple"));
        System.out.println("advanced: StringBuilder \"Banana\" -> " + startsWithVowel(new StringBuilder("Banana")));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `StringAsCharacterSequence.java`, then run `java StringAsCharacterSequence.java`.

## 6. Walkthrough

1. `basicLevel()` reads `s.length()` (5) and `s.charAt(1)` (`'e'`) directly — both are O(1) operations, since the character data is contiguous and the length is a known, stored value.
2. `intermediateLevel()` builds the same uppercase result two ways: looping with `charAt(i)` directly on the `String`, and converting to a `char[]` first with `toCharArray()` then looping over that array. Both produce `"SEQUENCE"`.
3. The `toCharArray()` approach pays a one-time O(n) cost to copy the characters into a real array, which can be worthwhile when you plan to index into the same string many times in a hot loop.
4. `advancedLevel()`'s `startsWithVowel` takes a `CharSequence` parameter, so it accepts a `String` literal directly, and also accepts a `StringBuilder` without any conversion — both types satisfy the `CharSequence` contract with their own `length()` and `charAt()`.

## 7. Gotchas & takeaways

> Gotcha: `charAt(i)` throws `StringIndexOutOfBoundsException` for `i >= length()` or `i < 0`, exactly like an array's `ArrayIndexOutOfBoundsException` — always check bounds (or rely on a loop condition like `i < s.length()`) before indexing.

- A `String` is conceptually a character sequence backed by contiguous data, giving O(1) `charAt` access and O(1) `length()`.
- `CharSequence` is the shared interface behind `String`, `StringBuilder`, and `StringBuffer`, letting APIs accept any of them.
- Converting to `char[]` with `toCharArray()` is a one-time O(n) cost, worthwhile when repeatedly indexing in a hot loop.
- Related concepts: [String immutability in Java](0033-string-immutability-in-java.md), [char\[\] vs String](0035-char-vs-string.md).
