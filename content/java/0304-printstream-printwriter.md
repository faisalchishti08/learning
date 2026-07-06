---
card: java
gi: 304
slug: printstream-printwriter
title: PrintStream / PrintWriter
---

## 1. What it is

`PrintStream` and `PrintWriter` are convenience output classes that add `print`, `println`, and `printf` methods — formatted, human-readable text output — on top of an underlying byte or character stream. `System.out` and `System.err` are both `PrintStream` instances; `PrintWriter` is the character-stream equivalent, generally preferred for writing formatted text to files.

```java
public class PrintDemo {
    public static void main(String[] args) {
        System.out.println("Hello!");            // PrintStream, byte-oriented
        System.out.printf("Pi is %.2f%n", 3.14159); // formatted output
        System.err.println("This is an error message");
    }
}
```

`System.out` is a `PrintStream` field on the `System` class, already open and ready to use; `printf` accepts a format string (similar to C's `printf`) with placeholders like `%.2f` (a float/double rounded to 2 decimal places) and `%n` (a platform-appropriate newline).

## 2. Why & when

Raw `OutputStream`/`Writer` only offer `write(byte)`/`write(char)`/`write(String)` — no line-ending handling, no automatic type-to-string conversion, no formatted output. `PrintStream`/`PrintWriter` add exactly the conveniences needed for readable, human-facing text output.

- **Console output** — `System.out`/`System.err` are the standard way any Java program writes to the console; every `println` call you've ever written uses `PrintStream`.
- **Formatted output** — `printf`/`format` let you control number precision, field width, and alignment without manual string concatenation.
- **Never throws checked `IOException`** — unlike raw `Writer`/`OutputStream` methods, `PrintStream`/`PrintWriter`'s `print`/`println` methods swallow `IOException` internally (exposing a separate `checkError()` method instead), which is why `System.out.println(...)` never needs a `try`/`catch` or `throws` clause.

Use `PrintWriter` (wrapping a `BufferedWriter` wrapping a `FileWriter`, for example) when writing formatted text to a file; use `System.out`/`System.err` (both `PrintStream`) for console output. Avoid constructing a *new* `PrintStream` for file output in modern code — `PrintWriter` is the character-stream-based, encoding-aware choice for that purpose.

## 3. Core concept

```java
import java.io.PrintWriter;
import java.io.StringWriter;

public class PrintCore {
    public static void main(String[] args) {
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);

        pw.println("Line one");
        pw.printf("Value: %d%n", 42);
        pw.flush(); // PrintWriter buffers internally; flush pushes it through

        System.out.println(sw.toString());
    }
}
```

`PrintWriter` methods never declare `throws IOException` — internally, any I/O error is tracked and can be checked via `pw.checkError()`, but the calling code is never forced to handle it, which trades strict error visibility for the convenience that makes `println`-everywhere code possible.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PrintStream and PrintWriter both add formatted print methods on top of a raw byte or character stream" >
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="57" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">PrintStream (bytes)</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle">System.out / System.err</text>

  <rect x="330" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="450" y="57" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">PrintWriter (chars)</text>
  <text x="450" y="90" fill="#8b949e" font-size="9" text-anchor="middle">preferred for writing formatted text to files</text>
</svg>

Both add `print`/`println`/`printf`; choose based on whether the destination is byte- or character-oriented.

## 5. Runnable example

Scenario: generating a small formatted receipt, evolved from console output with `println` into `printf`-formatted columns, then into writing that same formatted receipt to a file with `PrintWriter` and checking for write errors.

### Level 1 — Basic

```java
public class PrintBasic {
    public static void main(String[] args) {
        System.out.println("Receipt");
        System.out.println("-------");
        System.out.println("Coffee: 4.50");
        System.out.println("Muffin: 3.25");
    }
}
```

**How to run:** `java PrintBasic.java`

Plain `println` calls to the console — simple, but numbers aren't aligned and lack consistent decimal formatting.

### Level 2 — Intermediate

Same receipt, now using `printf` for aligned, consistently formatted columns.

```java
public class PrintIntermediate {
    public static void main(String[] args) {
        System.out.println("Receipt");
        System.out.println("-------");
        System.out.printf("%-10s $%6.2f%n", "Coffee", 4.5);
        System.out.printf("%-10s $%6.2f%n", "Muffin", 3.25);
        System.out.printf("%-10s $%6.2f%n", "Total", 7.75);
    }
}
```

**How to run:** `java PrintIntermediate.java`

`%-10s` left-aligns the item name in a 10-character field; `%6.2f` right-aligns the price in a 6-character field with exactly 2 decimal places, producing neatly aligned columns regardless of name length or price magnitude.

### Level 3 — Advanced

Same formatted receipt, now written to a file using `PrintWriter`, with explicit error checking via `checkError()` after writing (demonstrating the trade-off of `PrintWriter`'s exception-swallowing behavior).

```java
import java.io.PrintWriter;
import java.io.FileWriter;
import java.io.BufferedWriter;
import java.io.IOException;

public class PrintAdvanced {
    record Item(String name, double price) {}

    public static void main(String[] args) throws IOException {
        Item[] items = {new Item("Coffee", 4.5), new Item("Muffin", 3.25), new Item("Bagel", 2.75)};
        double total = 0;
        for (Item item : items) total += item.price();

        try (PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter("receipt.txt")))) {
            writer.println("Receipt");
            writer.println("-------");
            for (Item item : items) {
                writer.printf("%-10s $%6.2f%n", item.name(), item.price());
            }
            writer.printf("%-10s $%6.2f%n", "Total", total);

            if (writer.checkError()) {
                System.out.println("Warning: an error occurred while writing the receipt!");
            } else {
                System.out.println("Receipt written successfully.");
            }
        }
    }
}
```

**How to run:** `java PrintAdvanced.java` (writes `receipt.txt` in the current directory)

`writer.checkError()` returns `true` if any underlying write since the last check has failed — since `PrintWriter`'s `print`/`println`/`printf` methods never throw, this is the *only* way to detect a write failure short of manually flushing and catching exceptions from a lower-level stream, which is exactly the trade-off `PrintWriter` makes for its convenience.

## 6. Walkthrough

Trace `PrintAdvanced.main` step by step.

**Setup.** `items` holds three `Item` records; `total` is accumulated by summing each item's `price()` via the `for` loop — `4.5 + 3.25 + 2.75 = 10.5`.

**Opening the writer.** `new PrintWriter(new BufferedWriter(new FileWriter("receipt.txt")))` layers three wrappers: `FileWriter` is the raw character-to-file connection, `BufferedWriter` adds buffering above it, and `PrintWriter` adds the formatted `print`/`printf` methods on top of that — a write to `writer` flows down through all three layers.

**Writing the header.** `writer.println("Receipt")` and `writer.println("-------")` each write their text followed by a line terminator into the buffered chain.

**Writing each item.** The `for` loop calls `writer.printf("%-10s $%6.2f%n", item.name(), item.price())` once per item. For `Item("Coffee", 4.5)`: `%-10s` renders `"Coffee"` left-aligned padded to 10 characters (`"Coffee    "`), `%6.2f` renders `4.5` as `"  4.50"` (right-aligned, 2 decimals, 6-character field), and `%n` ends the line. The same pattern repeats for `"Muffin"`/`3.25` and `"Bagel"`/`2.75`.

**Writing the total.** `writer.printf("%-10s $%6.2f%n", "Total", total)` renders `"Total     $ 10.50"` using the accumulated sum.

**Error check.** `writer.checkError()` internally flushes the stream and checks whether any `IOException` was silently caught during any write call so far — since the file write succeeded without issue, this returns `false`, so the `else` branch runs, printing the success message to the console (not the file).

**Closing.** The try-with-resources block closes `writer`, which cascades through `BufferedWriter` (flushing its buffer) and `FileWriter` (releasing the file handle) — `receipt.txt` now contains the complete formatted receipt.

```
receipt.txt contents:
Receipt
-------
Coffee    $  4.50
Muffin    $  3.25
Bagel     $  2.75
Total     $ 10.50
```

**Console output:**
```
Receipt written successfully.
```

## 7. Gotchas & takeaways

> `PrintStream`/`PrintWriter` methods silently swallow `IOException` — a write failure (disk full, broken pipe) will **not** throw an exception you can catch around the `print`/`println`/`printf` call itself. The only way to detect it is `checkError()`, which must be called explicitly; code that never calls it can silently lose output with no indication anything went wrong.

> `%n` in a format string produces the platform-appropriate line separator, while a literal `"\n"` in the format string always produces exactly a line-feed character — prefer `%n` in `printf`/`format` calls for portability, consistent with the same reasoning that favors `BufferedWriter.newLine()` over a hardcoded `"\n"`.

- `PrintStream` (byte-oriented, e.g. `System.out`/`System.err`) and `PrintWriter` (character-oriented, preferred for files) both add `print`/`println`/`printf` convenience methods.
- `printf`/`format` use C-style format specifiers (`%s`, `%d`, `%.2f`, `%-10s` for left-aligned width, etc.) for readable, aligned formatted output.
- Neither class's print methods throw checked exceptions — use `checkError()` if you need to detect a write failure.
- Prefer `PrintWriter` (wrapping `BufferedWriter`/`FileWriter`) for writing formatted text to files, keeping `PrintStream` for console output via `System.out`/`System.err`.
