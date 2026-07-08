---
card: java
gi: 415
slug: stringbuilder-non-synchronized
title: StringBuilder (non-synchronized)
---

## 1. What it is

`StringBuilder`, added in Java 5, is a mutable sequence of characters — you can `append`, `insert`, `delete`, and `reverse` its contents in place, without creating a new object each time. It has essentially the same API as the older `StringBuffer`, but its methods are **not synchronized**: no internal locking, no thread-safety overhead. For single-threaded use (the overwhelming majority of string-building code), this makes `StringBuilder` measurably faster than `StringBuffer` while behaving identically.

## 2. Why & when

Java's `String` is immutable — every `+` concatenation (`result = result + "more text"`) actually creates a **brand-new** `String` object, copying all the previous characters plus the new ones. Building up a large string through repeated concatenation in a loop is quadratic: each iteration copies everything accumulated so far, all over again. `StringBuilder` solves this by maintaining a resizable internal character array that new content is appended into directly, without discarding and recopying everything each time.

`StringBuffer` (from Java 1.0) already solved the mutability problem, but its every method is `synchronized` — meant for the rare case of one buffer genuinely shared and mutated by multiple threads. Since that's an unusual scenario (most string-building happens entirely within one thread, one method, one loop), `StringBuilder` was introduced specifically to drop that locking overhead. The rule of thumb: **use `StringBuilder` unless you specifically know the same instance is mutated by multiple threads concurrently** — in which case, either use `StringBuffer` or (more commonly, and better) confine the `StringBuilder` to one thread's local scope entirely.

## 3. Core concept

```java
StringBuilder sb = new StringBuilder();

sb.append("Hello");        // mutates IN PLACE -- no new object created per append
sb.append(", ");
sb.append("world");
sb.insert(0, ">> ");        // insert at a specific position
sb.append("!");
sb.deleteCharAt(sb.length() - 1); // remove the last character
sb.reverse();               // reverse the whole thing in place

String result = sb.toString(); // convert to an immutable String only once, at the end
```

Each `append`/`insert`/`delete` call modifies the same underlying character array (growing it if needed) — contrast this with `String` concatenation, where every `+` silently allocates an entirely new `String`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String concatenation in a loop creates a new object each iteration, copying everything so far; StringBuilder appends into the same growing buffer">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">String += in a loop: new object EVERY time, full recopy</text>
  <rect x="30" y="38" width="60" height="24" fill="#1c2430" stroke="#f85149"/><text x="60" y="55" fill="#f85149" font-size="9" text-anchor="middle">"a"</text>
  <rect x="100" y="38" width="80" height="24" fill="#1c2430" stroke="#f85149"/><text x="140" y="55" fill="#f85149" font-size="9" text-anchor="middle">"ab" (new)</text>
  <rect x="190" y="38" width="100" height="24" fill="#1c2430" stroke="#f85149"/><text x="240" y="55" fill="#f85149" font-size="9" text-anchor="middle">"abc" (new)</text>

  <text x="20" y="100" fill="#6db33f" font-size="11" font-family="sans-serif">StringBuilder.append() in a loop: SAME buffer, grows in place</text>
  <rect x="30" y="112" width="260" height="24" fill="#1c2430" stroke="#6db33f"/><text x="160" y="129" fill="#6db33f" font-size="9" text-anchor="middle">[a][b][c] -- one buffer, appended into</text>
</svg>

`String` concatenation discards and recreates; `StringBuilder` grows the same buffer.

## 5. Runnable example

Scenario: generating an HTML-ish report row by row for a list of items — the same report-building task, evolved from slow `String` concatenation, through `StringBuilder.append` in a loop, to a version using `insert`/`delete`/`reverse` and a size cap to keep the report from growing unbounded.

### Level 1 — Basic

```java
public class ReportStringConcat {
    public static void main(String[] args) {
        String report = "";
        for (int i = 1; i <= 5; i++) {
            report = report + "Row " + i + ": item-" + i + "\n"; // new String object every single iteration
        }
        System.out.print(report);
    }
}
```

**How to run:** `java ReportStringConcat.java`

This works correctly for 5 rows, but each `+` concatenation copies the *entire* string built so far into a brand-new object — for a report with thousands of rows, this becomes quadratically slow, since row 1000 requires recopying roughly 999 previous rows' worth of characters all over again.

### Level 2 — Intermediate

```java
public class ReportStringBuilder {
    public static void main(String[] args) {
        StringBuilder report = new StringBuilder();
        for (int i = 1; i <= 5; i++) {
            report.append("Row ").append(i).append(": item-").append(i).append("\n"); // appends into ONE buffer
        }
        System.out.print(report.toString());
    }
}
```

**How to run:** `java ReportStringBuilder.java`

`append` calls chain fluently (each returns `this`) and all write into the same growing internal buffer — no intermediate `String` objects are created per row, so building a report with thousands of rows scales linearly instead of quadratically. `toString()` is called exactly once, at the very end, to produce the final immutable `String`.

### Level 3 — Advanced

```java
public class ReportBuilderAdvanced {
    static final int MAX_LENGTH = 60; // cap the report to demonstrate delete/truncation

    public static void main(String[] args) {
        StringBuilder report = new StringBuilder();
        report.append(">> REPORT START >>\n"); // insert a header after the fact -- see below

        for (int i = 1; i <= 10; i++) {
            String row = "Row " + i + ": item-" + i + "\n";
            if (report.length() + row.length() > MAX_LENGTH) {
                report.append("... (truncated)\n");
                break;
            }
            report.append(row);
        }

        // Insert a timestamp right after the header line, without rebuilding the whole thing
        int headerEnd = report.indexOf("\n") + 1;
        report.insert(headerEnd, "Generated at: 2026-01-01\n");

        // Remove the trailing newline if present
        if (report.charAt(report.length() - 1) == '\n') {
            report.deleteCharAt(report.length() - 1);
        }

        System.out.println(report);
        System.out.println("Final length: " + report.length());
    }
}
```

**How to run:** `java ReportBuilderAdvanced.java`

`insert()` places text at a specific index without rebuilding the whole buffer from scratch, `deleteCharAt()` trims a single trailing character in place, and the length check inside the loop demonstrates using `StringBuilder`'s live `.length()` to cap growth — all operating on one mutable buffer throughout, with `toString()` (implicitly via `println`) only materializing the final `String` once.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `report` starts as an empty `StringBuilder`; `append(">> REPORT START >>\n")` makes its contents `">> REPORT START >>\n"` (20 characters).

The `for` loop builds candidate rows one at a time. For `i=1`, `row = "Row 1: item-1\n"` (14 characters). The check `report.length() + row.length() > MAX_LENGTH` is `20 + 14 = 34 > 60`? No — so `report.append(row)` runs, bringing the buffer to 34 characters. This continues for `i=2` (row length 14, running total 48), which also fits (`48 <= 60`).

For `i=3`, `row = "Row 3: item-3\n"` is again 14 characters; `48 + 14 = 62 > 60` — this time the check **fails**, so instead of appending row 3, the code appends `"... (truncated)\n"` and `break`s out of the loop early. The report now ends with a truncation marker rather than all 10 rows.

Next, `report.indexOf("\n")` finds the position of the *first* newline character — the one right after `">> REPORT START >>"` — and adding `1` moves past it, giving `headerEnd`, the index where the second line begins. `report.insert(headerEnd, "Generated at: 2026-01-01\n")` splices this new line in at exactly that position, shifting everything after it forward — without needing to rebuild the buffer from scratch or manually recompute the rest of the content.

Finally, `report.charAt(report.length() - 1)` checks whether the very last character is a newline (it is, since the truncation marker ended with `"\n"`); `deleteCharAt(report.length() - 1)` removes just that one trailing character in place.

`System.out.println(report)` implicitly calls `report.toString()` to print the final content, and `report.length()` reports the buffer's final character count.

Expected output:
```
>> REPORT START >>
Generated at: 2026-01-01
Row 1: item-1
Row 2: item-2
... (truncated)
Final length: 87
```

## 7. Gotchas & takeaways

> `StringBuilder` is **not thread-safe** — if the same instance is genuinely mutated by multiple threads concurrently, its internal array can be corrupted (lost appends, or worse). If you need a shared, thread-safe mutable string buffer, use `StringBuffer` instead, or — usually the better design — keep each `StringBuilder` confined to a single thread and combine results afterward.

- `StringBuilder` mutates in place; `String` concatenation (`+`) always creates a new object — prefer `StringBuilder` for building strings incrementally, especially in loops.
- `StringBuilder` and `StringBuffer` share the same API; `StringBuilder`'s methods are not synchronized, making it faster for the common single-threaded case.
- `append`, `insert`, `delete`, `deleteCharAt`, and `reverse` all mutate the buffer directly and return `this`, enabling fluent chaining.
- Call `toString()` only once you actually need an immutable `String` (e.g. to print, store, or pass to an API expecting `String`) — don't convert back and forth repeatedly inside a loop.
- For simple string concatenation across a handful of values, the compiler often optimizes `+` into `StringBuilder` calls automatically anyway — the performance concern is specifically about concatenation **inside loops**, where the compiler cannot perform that optimization across iterations.
