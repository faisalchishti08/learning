---
card: java
gi: 625
slug: string-repeat-int
title: String.repeat(int)
---

## 1. What it is

`String.repeat(int n)` is a Java 11 method that returns a new string consisting of the original string **repeated `n` times**. If `n` is zero, it returns the empty string `""`. If `n` is negative, it throws `IllegalArgumentException`. The method is a simple, concise replacement for the various manual repetition patterns developers used before Java 11 — `String.join("", Collections.nCopies(n, str))`, `new String(new char[n]).replace("\0", str)`, `StringBuilder` loops, or Apache Commons Lang's `StringUtils.repeat()`. The implementation is optimised: it uses `System.arraycopy` internally to double the buffer size at each step, achieving `O(log n)` copy operations for a result of length `n * str.length()`.

## 2. Why & when

String repetition is a surprisingly common operation: generating indentation (repeating spaces or tabs), drawing simple ASCII art or separators, padding numbers with leading zeros, creating test data of a certain size, or formatting console output with dividers. Before `repeat()`, every solution was either verbose (a `for` loop with a `StringBuilder`), obscure (the `replace("\0", str)` trick depends on `\0` not appearing in the original string), or required an external library. `repeat()` provides a one-method, readable, and efficient solution in the standard library. Use it whenever you need to build a string by repeating a pattern.

## 3. Core concept

```java
"abc".repeat(3);    // "abcabcabc"
"*".repeat(10);     // "**********"
" ".repeat(4);      // "    "  (four spaces — great for indentation)
"hello".repeat(0);  // ""  (empty string)
"x".repeat(1);      // "x"  (n=1 returns the string itself)

// Negative → exception
"x".repeat(-1);     // throws IllegalArgumentException
```

The method takes a single `int` parameter (`count`) and returns the concatenated result. The maximum practical `n` is limited by the maximum array size (Integer.MAX_VALUE - a few bytes) divided by the string length; requesting a result larger than `Integer.MAX_VALUE - 8` bytes throws `OutOfMemoryError`.

## 4. Diagram

<svg viewBox="0 0 540 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="repeat() concatenates the string n times using efficient array doubling">
  <rect x="10" y="10" width="520" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="110" height="35" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="75" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"ab"</text>

  <text x="140" y="47" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">.repeat(3)</text>

  <text x="225" y="47" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>

  <rect x="250" y="25" width="130" height="35" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="315" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"ababab"</text>

  <text x="20" y="80" fill="#8b949e" font-size="10" font-family="monospace">n = 0  → ""</text>
  <text x="160" y="80" fill="#8b949e" font-size="10" font-family="monospace">n = 1  → original string</text>
  <text x="340" y="80" fill="#8b949e" font-size="10" font-family="monospace">n &lt; 0 → IllegalArgumentException</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">Uses array-doubling internally: repeats 1x, 2x, 4x, 8x ... to build result in O(log n) copies</text>
  <text x="20" y="118" fill="#3fb950" font-size="9" font-family="sans-serif">Widely used for: indentation, ASCII art, separators, padding, test-data generation</text>
</svg>

`repeat()` is a simple but frequently-used utility: give it a string and a count, get back the concatenated result.

## 5. Runnable example

Scenario: building a console-based progress bar and report formatter — starting with basic repetition, extending to a reusable formatting utility, and finally handling edge cases and performance.

### Level 1 — Basic

```java
// File: RepeatDemo.java
public class RepeatDemo {
    public static void main(String[] args) {
        String line = "-".repeat(40);
        String indent = " ".repeat(4);

        System.out.println(line);
        System.out.println(indent + "REPORT HEADING");
        System.out.println(line);

        System.out.println(indent + "Section A" + ".".repeat(20) + "[OK]");
        System.out.println(indent + "Section B" + ".".repeat(20) + "[OK]");
        System.out.println(indent + "Section C" + ".".repeat(20) + "[FAIL]");

        System.out.println(line);
    }
}
```

**How to run:** `java RepeatDemo.java`

Expected output:
```
----------------------------------------
    REPORT HEADING
----------------------------------------
    Section A....................[OK]
    Section B....................[OK]
    Section C....................[FAIL]
----------------------------------------
```

The simplest usage: `repeat()` generates separator lines and indentation concisely. The dots between section names and status are filled dynamically.

### Level 2 — Intermediate

```java
// File: ProgressBar.java
public class ProgressBar {
    public static void main(String[] args) throws InterruptedException {
        int total = 50;
        int barWidth = 30;

        System.out.println("Downloading...\n");

        for (int i = 0; i <= total; i++) {
            int percent = i * 100 / total;
            int filled = i * barWidth / total;
            int empty = barWidth - filled;

            String bar = "\r[" +
                "#".repeat(filled) +
                " ".repeat(empty) +
                "] " + percent + "%";

            // Print on same line (\r brings cursor to start)
            System.out.write(bar.getBytes());
            System.out.flush();
            Thread.sleep(50);  // simulate work
        }
        System.out.println("\n\nDownload complete!");
    }
}
```

**How to run:** `java ProgressBar.java`

Expected output (animated on one line):
```
Downloading...

[##############################] 100%

Download complete!
```

The real-world concern: dynamic progress bars. `repeat()` makes it trivial to compose a visual bar from `#` and space characters based on a current/total ratio. The same technique works for any proportional visualisation — star ratings, capacity bars, volume indicators.

### Level 3 — Advanced

```java
// File: RepeatAdvanced.java
public class RepeatAdvanced {

    public static void main(String[] args) {
        System.out.println("=== Indentation helper ===\n");

        // TREE: build hierarchical text output
        printTree("root", 0);
        printTree("src", 1);
        printTree("main", 2);
        printTree("java", 3);
        printTree("tests", 2);
        printTree("resources", 2);

        System.out.println("\n=== Table formatting ===\n");

        // Tabular output with dynamic column widths
        String[][] data = {
            {"Item", "Qty", "Price", "Total"},
            {"Apple", "3", "0.50", "1.50"},
            {"Banana", "12", "0.30", "3.60"},
            {"Cherry", "100", "0.05", "5.00"},
        };

        // Print table with separator
        String sep = "+" + "-".repeat(10) + "+" + "-".repeat(6) + "+" + "-".repeat(8) + "+" + "-".repeat(8) + "+";
        System.out.println(sep);
        for (String[] row : data) {
            System.out.printf("| %-8s | %-4s | %-6s | %-6s |%n",
                row[0], row[1], row[2], row[3]);
            if (row == data[0]) System.out.println(sep); // header separator
        }
        System.out.println(sep);

        System.out.println("\n=== Edge cases ===\n");

        // n = 0: always returns empty string
        System.out.println("'hello'.repeat(0) = '" + "hello".repeat(0) + "'");
        System.out.println("''.repeat(5)      = '" + "".repeat(5) + "'");

        // n = 1: returns the string itself (same reference? not guaranteed)
        String s = "test";
        System.out.println("repeat(1) equals original: " + s.repeat(1).equals(s));

        // Negative n
        try {
            "x".repeat(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("repeat(-1) throws IllegalArgumentException: " + e.getMessage());
        }

        // Large n (be careful!)
        System.out.println("\n'x'.repeat(100) length: " + "x".repeat(100).length());
    }

    static void printTree(String name, int depth) {
        String indent = "  ".repeat(depth);
        String branch = depth > 0 ? "├─ " : "";
        System.out.println(indent + branch + name);
    }
}
```

**How to run:** `java RepeatAdvanced.java`

Expected output:
```
=== Indentation helper ===

root
  ├─ src
    ├─ main
      ├─ java
    ├─ tests
    ├─ resources

=== Table formatting ===

+----------+------+--------+--------+
| Item     | Qty  | Price  | Total  |
+----------+------+--------+--------+
| Apple    | 3    | 0.50   | 1.50   |
| Banana   | 12   | 0.30   | 3.60   |
| Cherry   | 100  | 0.05   | 5.00   |
+----------+------+--------+--------+

=== Edge cases ===

'hello'.repeat(0) = ''
''.repeat(5)      = ''
repeat(1) equals original: true
repeat(-1) throws IllegalArgumentException: count is negative: -1

'x'.repeat(100) length: 100
```

The production-flavoured hard cases: (1) Tree-printing uses `repeat()` for depth-based indentation — a common need in CLI tools, file-system visualisers, and debug output. (2) Table formatting uses `repeat()` for dynamic separator lines based on column widths. (3) Edge cases: `n=0` returns `""`, `n=1` returns the string itself (possibly the same instance), negative `n` throws `IllegalArgumentException` with a descriptive message.

## 6. Walkthrough

Tracing `"#".repeat(5)`:

1. The JVM invokes `repeat(5)` on the string `"#"`. The method first checks the argument: `if (count < 0) throw new IllegalArgumentException(...)`. `5` is not negative, so it passes.

2. `if (count == 1) return this;` — `5` is not 1, so this shortcut is skipped.

3. The method calculates the result length: `len * count` = `1 * 5` = `5`. It allocates a `byte[]` of size 5 (or `new byte[5]`).

4. The encoding-specific inner loop (e.g. `StringLatin1.repeat`) copies the original string's bytes into the target array using `System.arraycopy`. The algorithm doubles the copied region: after first copy, the buffer contains `"#"` (1 byte filled); after second, `"##"` (2 bytes); after third, `"####"` (4 bytes); then the remaining 1 byte is copied to reach 5. This is 3 copy operations instead of 4 — the `O(log n)` optimisation.

5. A new `String` is constructed from the filled byte array and returned. The original string `"#"` is unchanged.

For `"".repeat(5)`: the result length is `0 * 5 = 0`, so the method short-circuits and returns `""` immediately — no allocation.

## 7. Gotchas & takeaways

> `repeat()` with a very large count can produce an `OutOfMemoryError` if the result exceeds `Integer.MAX_VALUE - 8` bytes (approximately 2 GB). Always validate user-supplied repeat counts before calling `repeat()` — an attacker could pass `Integer.MAX_VALUE` as a repeat count to exhaust server memory.

- `repeat(0)` always returns `""` (the empty string), and `repeat(1)` returns the string itself. Both are useful short-circuit behaviours that avoid unnecessary allocation.
- The method is null-hostile: calling `repeat()` on a `null` reference throws `NullPointerException` — guard with a null check if the string source is untrusted.
- `repeat()` complements `String.join()` for building repeated patterns: `String.join("", Collections.nCopies(n, str))` is now obsoleted by `str.repeat(n)`.
- The internal implementation uses array-doubling, not a naive loop. For large `n`, this makes `repeat()` significantly faster than a manual `StringBuilder` loop.
- Use `" ".repeat(n)` for indentation instead of hard-coding spaces or tabs — the intent is clearer and the indentation width can be parameterised.
