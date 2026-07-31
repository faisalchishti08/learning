---
card: data-structures
gi: 35
slug: char-vs-string
title: char[] vs String
---

## 1. What it is

`char[]` and `String` both represent a sequence of characters, but they differ in one critical way: a `char[]` is a plain, **mutable** array — you can modify individual characters in place — while a `String` is **immutable**, and any apparent modification allocates a whole new object. Choosing between them is a choice between "raw, mutable, fast-to-modify data" and "safe, immutable, shareable data."

## 2. Why & when

Use `char[]` when you need to modify characters in place repeatedly (e.g., building or transforming text in a tight loop without allocating new objects each time), or for sensitive data like passwords, where you want to explicitly overwrite (zero out) the memory when done — something impossible with an immutable `String`, which may linger in memory (or the string pool) until garbage collected. Use `String` for everything else: general text handling, map keys, and any API that already expects one.

## 3. Core concept

**Mutability is the core difference.** `char[] arr = {'h','i'}; arr[0] = 'H';` mutates the array in place — no new object, no copy. The equivalent for a `String`, `s = s.substring(0,0) + 'H' + s.substring(1)` (or similar), allocates a brand-new `String` object every time.

**Security: `char[]` for passwords, never `String`.** Because a `String` is immutable and may be cached in the string pool, there is no reliable way to force its contents out of memory promptly — it can linger until garbage collected, and possibly even appear in a memory dump. A `char[]` password can be explicitly overwritten (`Arrays.fill(passwordChars, '0')`) the instant it is no longer needed, which is exactly why `java.io.Console.readPassword()` and JDBC APIs return/accept `char[]`, not `String`.

**Performance: repeated modification.** A loop that builds up text character by character using `String` concatenation allocates a new object on every iteration (covered fully in [Concatenation cost & why StringBuilder](0036-concatenation-cost-why-stringbuilder.md)). The same loop using a pre-sized `char[]` and direct index writes allocates nothing extra.

**Conversion is cheap and common.** `s.toCharArray()` copies a `String`'s characters into a new, independent `char[]` in O(n). `new String(charArray)` does the reverse, copying a `char[]`'s contents into a new immutable `String`, also O(n).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="char array allowing direct in-place mutation versus String requiring a whole new object for any change">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#8b949e" text-anchor="middle">char[] arr = {'h','i'}; arr[0]='H';</text>
    <rect x="90" y="30" width="40" height="28" fill="#161b22" stroke="#3fb950"/><text x="110" y="49" fill="#e6edf3" text-anchor="middle" font-size="11">H</text>
    <rect x="130" y="30" width="40" height="28" fill="#161b22" stroke="#3fb950"/><text x="150" y="49" fill="#e6edf3" text-anchor="middle" font-size="11">i</text>
    <text x="150" y="80" fill="#79c0ff" text-anchor="middle" font-size="10">mutated in place, no new object</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">String s = "hi"; s = "H" + s.substring(1);</text>
    <rect x="420" y="30" width="40" height="28" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/><text x="440" y="49" fill="#8b949e" text-anchor="middle" font-size="11">h</text>
    <rect x="460" y="30" width="40" height="28" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/><text x="480" y="49" fill="#8b949e" text-anchor="middle" font-size="11">i</text>
    <rect x="420" y="90" width="40" height="28" fill="#0d1117" stroke="#f0883e"/><text x="440" y="109" fill="#e6edf3" text-anchor="middle" font-size="11">H</text>
    <rect x="460" y="90" width="40" height="28" fill="#0d1117" stroke="#f0883e"/><text x="480" y="109" fill="#e6edf3" text-anchor="middle" font-size="11">i</text>
    <text x="450" y="140" fill="#79c0ff" text-anchor="middle" font-size="10">original discarded, an entirely new object built</text>
  </g>
</svg>

`char[]` mutates a single slot directly. `String` must build a whole new object to reflect any "change."

## 5. Runnable example

```java
// CharArrayVsString.java
import java.util.Arrays;

public class CharArrayVsString {

    // Basic: char[] mutates in place; String requires a full new object for the same logical change.
    static void basicLevel() {
        char[] arr = {'h', 'i'};
        arr[0] = 'H'; // direct in-place mutation, no allocation
        System.out.println("basic: mutated char[] -> " + new String(arr));

        String s = "hi";
        s = "H" + s.substring(1); // builds an entirely new String
        System.out.println("basic: rebuilt String -> " + s);
    }

    // Intermediate: conversion both directions is O(n), copying the data.
    static void intermediateLevel() {
        String original = "sequence";
        char[] asChars = original.toCharArray(); // copy into a new char[]
        asChars[0] = 'S';
        String rebuilt = new String(asChars); // copy back into a new String
        System.out.println("intermediate: original untouched -> " + original);
        System.out.println("intermediate: rebuilt from mutated chars -> " + rebuilt);
    }

    // Advanced: passwords as char[] -- explicitly wipe the memory the instant it is no longer needed.
    static boolean checkPassword(char[] attempt, char[] correct) {
        boolean matches = Arrays.equals(attempt, correct); // constant content comparison here for clarity
        Arrays.fill(attempt, '0'); // overwrite the attempt's memory immediately after checking
        return matches;
    }

    static void advancedLevel() {
        char[] correct = {'s', '3', 'c', 'r', '3', 't'};
        char[] attempt = {'s', '3', 'c', 'r', '3', 't'};
        boolean ok = checkPassword(attempt, correct);
        System.out.println("advanced: password matched -> " + ok);
        System.out.println("advanced: attempt array wiped after check -> " + new String(attempt)); // "000000"
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `CharArrayVsString.java`, then run `java CharArrayVsString.java`.

## 6. Walkthrough

1. `basicLevel()` mutates `arr[0]` directly on the `char[]` — one write, no allocation. The `String` version instead builds `"H" + s.substring(1)`, which allocates a `substring` result and then a concatenated result — two new objects for what looks like "one change."
2. `intermediateLevel()` converts `original` to `asChars` with `toCharArray()` (an O(n) copy), mutates the copy, then converts back with `new String(asChars)` (another O(n) copy). `original` itself is provably untouched throughout, since the conversions always copy rather than share memory.
3. `advancedLevel()`'s `checkPassword` compares two `char[]` values, then immediately overwrites `attempt`'s contents with `'0'` using `Arrays.fill`. This scrubs the sensitive data from that specific memory location right away.
4. Printing `attempt` afterward shows `"000000"` — proof the original characters are gone from that array. A `String` holding the same password could not be scrubbed this way, since none of its methods can alter its backing data.

## 7. Gotchas & takeaways

> Gotcha: you cannot reliably "clear" a `String` containing sensitive data — even setting the variable to `null` only removes your one reference; the actual character data may still exist elsewhere in memory (including possibly the string pool) until garbage collected, with no guaranteed timing. Use `char[]` for passwords and similar secrets specifically to avoid this problem.

- `char[]` is mutable and lets you change data in place with no new allocation; `String` is immutable and any "change" allocates a new object.
- Sensitive data like passwords should use `char[]`, so it can be explicitly overwritten the moment it is no longer needed.
- Conversion both ways (`toCharArray()`, `new String(charArray)`) is an O(n) copy, not a shared view.
- Related concepts: [String immutability in Java](0033-string-immutability-in-java.md), [String as a character sequence](0032-string-as-a-character-sequence.md).
