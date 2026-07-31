---
card: data-structures
gi: 36
slug: concatenation-cost-why-stringbuilder
title: Concatenation cost & why StringBuilder
---

## 1. What it is

**Concatenation** joins strings together with `+`. Because `String` is immutable, `a + b` always allocates a brand-new `String` containing both contents copied in — it never modifies `a` or `b`. Doing this repeatedly in a loop, once per iteration, means allocating and copying a growing string over and over. `StringBuilder` solves this: it is a **mutable** character buffer that appends new content in place, only producing a final immutable `String` once, when you call `.toString()`.

## 2. Why & when

A single `a + b` outside a loop is fine — the compiler even optimizes simple, fixed concatenation chains internally. The problem is a loop: `result = result + piece;` repeated n times allocates n new strings, each copying all the characters accumulated so far, making the whole loop O(n²) in total characters copied. Use `StringBuilder` (or `StringBuilder.append` in a loop, `toString()` once at the end) whenever you build a string incrementally.

## 3. Core concept

**Why looped concatenation is O(n²).** Suppose you append 1-character pieces n times. The first concatenation copies ~1 character, the second copies ~2, the third ~3, and so on up to ~n — the total copied characters is `1+2+3+...+n`, which is `n(n+1)/2`, an O(n²) quantity. Each individual `+` is O(current length), and the current length grows every iteration.

**Why `StringBuilder.append` avoids this.** `StringBuilder` keeps an internal, resizable `char[]` buffer (working exactly like the dynamic-array doubling covered in [Array resizing & amortized append](0020-array-resizing-amortized-append.md)). `append()` writes new characters into existing free capacity, or grows the buffer (doubling-style) only when it runs out — giving amortized O(1) per append, and O(n) total for n appends, instead of O(n²).

**`toString()` is the one point where an immutable `String` is finally produced.** While you are appending, everything stays in the mutable buffer — no `String` objects are created along the way. Only the final `.toString()` call copies the buffer's contents into one immutable `String`, exactly once.

**When plain `+` is fine.** A fixed number of concatenations known at compile time, like `"Hello, " + name + "!"`, is compiled efficiently (often into a single `StringBuilder` chain automatically) — the O(n²) danger is specifically about repeating concatenation inside a loop whose length is not fixed.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Looped string concatenation copying a growing amount of data each time versus StringBuilder appending into existing free capacity">
  <g font-family="sans-serif" font-size="11">
    <text x="150" y="16" fill="#8b949e" text-anchor="middle">result = result + piece (each iteration)</text>
    <rect x="60" y="30" width="30" height="20" fill="#161b22" stroke="#f0883e"/>
    <rect x="60" y="55" width="60" height="20" fill="#161b22" stroke="#f0883e"/>
    <rect x="60" y="80" width="100" height="20" fill="#161b22" stroke="#f0883e"/>
    <text x="150" y="120" fill="#79c0ff" font-size="10">each step copies everything so far -&gt; O(n^2) total</text>

    <text x="480" y="16" fill="#8b949e" text-anchor="middle">sb.append(piece) (each iteration)</text>
    <rect x="400" y="30" width="160" height="70" fill="none" stroke="#3fb950"/>
    <rect x="405" y="35" width="30" height="20" fill="#0d1117" stroke="#3fb950"/>
    <rect x="440" y="35" width="30" height="20" fill="#0d1117" stroke="#3fb950"/>
    <rect x="475" y="35" width="30" height="20" fill="none" stroke="#8b949e" stroke-dasharray="2,2"/>
    <text x="480" y="120" fill="#79c0ff" font-size="10">writes into existing free buffer space -&gt; O(1) amortized per append</text>
  </g>
</svg>

Naive concatenation recopies everything already built. `StringBuilder` writes into a growing buffer, only rarely needing to copy.

## 5. Runnable example

```java
// ConcatenationCostStringBuilder.java
public class ConcatenationCostStringBuilder {

    // Basic: naive looped concatenation -- O(n^2), each '+' copies the whole string so far.
    static String buildNaive(int n) {
        String result = "";
        for (int i = 0; i < n; i++) {
            result = result + i; // allocates a new String, copying everything built so far, every time
        }
        return result;
    }

    static void basicLevel() {
        long start = System.nanoTime();
        String result = buildNaive(20_000);
        long elapsed = System.nanoTime() - start;
        System.out.println("basic: naive result length -> " + result.length() + " time(ns) -> " + elapsed);
    }

    // Intermediate: StringBuilder.append -- amortized O(1) per append, O(n) total.
    static String buildWithStringBuilder(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            sb.append(i); // writes into the buffer's free space, or triggers an occasional doubling resize
        }
        return sb.toString(); // single conversion to an immutable String, at the end
    }

    static void intermediateLevel() {
        long start = System.nanoTime();
        String result = buildWithStringBuilder(20_000);
        long elapsed = System.nanoTime() - start;
        System.out.println("intermediate: StringBuilder result length -> " + result.length() + " time(ns) -> " + elapsed);
    }

    // Advanced: pre-sizing the StringBuilder's buffer avoids even the occasional internal resize.
    static void advancedLevel() {
        int n = 20_000;
        StringBuilder sb = new StringBuilder(n * 5); // rough estimate of final size, reserved up front
        for (int i = 0; i < n; i++) sb.append(i);
        String result = sb.toString();
        System.out.println("advanced: pre-sized StringBuilder result length -> " + result.length());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `ConcatenationCostStringBuilder.java`, then run `java ConcatenationCostStringBuilder.java`. Compare the two timings — the naive version should be visibly slower.

## 6. Walkthrough

1. `basicLevel()`'s `buildNaive` starts with `result = ""` and repeatedly does `result = result + i`. Each iteration copies every character accumulated so far into a brand-new `String`, plus the new piece — the total copying work across all `n` iterations grows quadratically with `n`.
2. `intermediateLevel()`'s `buildWithStringBuilder` uses one `StringBuilder` and calls `append(i)` each iteration. Most appends just write into already-reserved buffer space; occasionally the buffer fills up and doubles in size (copying its current contents once) — the same amortized-O(1) growth strategy `ArrayList` uses internally.
3. `sb.toString()` is called exactly once at the end, producing the final immutable `String` in one O(n) copy from the buffer.
4. Comparing the two timings for the same `n = 20,000` should show the naive version taking noticeably longer, since its total work scales with `n²` while `StringBuilder`'s scales with `n`.
5. `advancedLevel()` pre-sizes the `StringBuilder`'s internal buffer with `new StringBuilder(n * 5)`, an estimate of the final character count — this avoids even the occasional internal resize-and-copy that the default-growth version in `intermediateLevel()` still performs a handful of times.

## 7. Gotchas & takeaways

> Gotcha: a single `a + b + c` outside a loop is fine and often compiler-optimized — the real danger is `result = result + piece` **inside a loop**, where the string being copied grows every single iteration. Always use `StringBuilder` (or `String.join`, `Collectors.joining`) for loop-based string building.

- Looped `+` concatenation is O(n²) total work, since each concatenation copies everything accumulated so far.
- `StringBuilder.append` is amortized O(1) per call, using a resizable internal buffer, giving O(n) total for n appends.
- Call `.toString()` only once, after all appends, to produce the final immutable `String`.
- Related concepts: [String immutability in Java](0033-string-immutability-in-java.md), [Array resizing & amortized append](0020-array-resizing-amortized-append.md), [StringBuilder vs StringBuffer](0042-stringbuilder-vs-stringbuffer.md).
