---
card: java
gi: 548
slug: datetimeformatter
title: DateTimeFormatter
---

## 1. What it is

`DateTimeFormatter` converts `java.time` values to and from `String` representations — formatting a `LocalDate` as `"July 9, 2026"` or `"09/07/2026"`, or parsing a string in a known format back into a `LocalDate`/`LocalDateTime`/etc. It replaces the old, notoriously not-thread-safe `SimpleDateFormat`. `DateTimeFormatter` instances are **immutable and thread-safe**, meaning a single formatter can safely be shared and reused across multiple threads without synchronization — a direct fix for one of `SimpleDateFormat`'s most infamous pitfalls.

## 2. Why & when

You reach for `DateTimeFormatter` any time a `java.time` value needs to become human-readable text (for display, logging, reports) or any time text needs to become a `java.time` value (parsing user input, reading a specific file format, consuming an API that uses a non-ISO date format). Built-in constants like `DateTimeFormatter.ISO_LOCAL_DATE` cover the standard formats; `DateTimeFormatter.ofPattern(...)` lets you specify a custom pattern for anything else.

## 3. Core concept

```java
import java.time.*;
import java.time.format.*;

LocalDate date = LocalDate.of(2026, 7, 9);

DateTimeFormatter formatter = DateTimeFormatter.ofPattern("MMMM d, yyyy");
String formatted = date.format(formatter); // "July 9, 2026"

DateTimeFormatter isoFormatter = DateTimeFormatter.ISO_LOCAL_DATE;
String isoFormatted = date.format(isoFormatter); // "2026-07-09"

LocalDate parsed = LocalDate.parse("07/09/2026", DateTimeFormatter.ofPattern("MM/dd/yyyy"));
```

A `DateTimeFormatter` works both directions: `value.format(formatter)` converts to text, `Type.parse(text, formatter)` converts text back into a `java.time` value, and both use the exact same pattern definition.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DateTimeFormatter converts between java.time values and text, in both directions">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">LocalDate</text>
  <line x1="180" y1="35" x2="290" y2="35" stroke="#6db33f" stroke-width="2" marker-end="url(#arrowDF)"/>
  <text x="235" y="25" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.format(...)</text>
  <rect x="300" y="20" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="390" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">"July 9, 2026"</text>

  <rect x="300" y="65" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="390" y="85" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">"07/09/2026"</text>
  <line x1="300" y1="80" x2="190" y2="80" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrowDF2)"/>
  <text x="245" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">.parse(...)</text>
  <rect x="30" y="65" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">LocalDate</text>
  <defs>
    <marker id="arrowDF" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrowDF2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The same `DateTimeFormatter` pattern works both ways: formatting a value into text, or parsing text back into a value.

## 5. Runnable example

Scenario: formatting dates for a user-facing invoice display and parsing dates from a legacy import file — evolved from basic pattern-based formatting, through parsing a custom format, to a version demonstrating thread-safety by sharing one formatter instance across concurrent threads (in contrast to `SimpleDateFormat`'s notorious non-thread-safety).

### Level 1 — Basic

```java
import java.time.*;
import java.time.format.*;

public class DateTimeFormatterBasic {
    public static void main(String[] args) {
        LocalDate invoiceDate = LocalDate.of(2026, 7, 9);

        DateTimeFormatter displayFormat = DateTimeFormatter.ofPattern("MMMM d, yyyy");
        DateTimeFormatter shortFormat = DateTimeFormatter.ofPattern("MM/dd/yyyy");

        System.out.println("Display: " + invoiceDate.format(displayFormat));
        System.out.println("Short: " + invoiceDate.format(shortFormat));
    }
}
```

**How to run:** `java DateTimeFormatterBasic.java`

Expected output:
```
Display: July 9, 2026
Short: 07/09/2026
```

`DateTimeFormatter.ofPattern("MMMM d, yyyy")` defines a pattern: `MMMM` for the full month name, `d` for the day without leading zero, `yyyy` for the four-digit year. `date.format(displayFormat)` applies it, producing `"July 9, 2026"`. `"MM/dd/yyyy"` produces the more compact `"07/09/2026"` — the same date, formatted two different ways using two different formatter instances.

### Level 2 — Intermediate

```java
import java.time.*;
import java.time.format.*;

public class DateTimeFormatterParsing {
    public static void main(String[] args) {
        // A legacy import file uses "DD-Mon-YYYY" style dates.
        DateTimeFormatter legacyFormat = DateTimeFormatter.ofPattern("dd-MMM-yyyy");

        String[] legacyDates = {"09-Jul-2026", "25-Dec-2026", "01-Jan-2027"};

        for (String rawDate : legacyDates) {
            LocalDate parsed = LocalDate.parse(rawDate, legacyFormat);
            System.out.println(rawDate + " -> " + parsed);
        }
    }
}
```

**How to run:** `java DateTimeFormatterParsing.java`

Expected output:
```
09-Jul-2026 -> 2026-07-09
25-Dec-2026 -> 2026-12-25
01-Jan-2027 -> 2027-01-01
```

The real-world concern this adds: parsing dates from an external, non-ISO format — `"dd-MMM-yyyy"` matches strings like `"09-Jul-2026"` (`dd` = zero-padded day, `MMM` = abbreviated month name, `yyyy` = four-digit year). `LocalDate.parse(rawDate, legacyFormat)` converts each raw string into a proper `LocalDate`, which then prints in the standard ISO format (`2026-07-09`) by default, since `LocalDate.toString()` doesn't use the parsing formatter — the formatter is only involved in the conversion, not in how the resulting object displays itself afterward.

### Level 3 — Advanced

```java
import java.time.*;
import java.time.format.*;
import java.util.concurrent.*;
import java.util.*;

public class DateTimeFormatterThreadSafe {
    public static void main(String[] args) throws InterruptedException {
        // ONE formatter instance, shared across multiple threads -- safe, unlike SimpleDateFormat.
        DateTimeFormatter sharedFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

        List<String> results = Collections.synchronizedList(new ArrayList<>());
        ExecutorService executor = Executors.newFixedThreadPool(4);

        for (int i = 0; i < 20; i++) {
            int day = (i % 28) + 1; // keep it within a valid day range for simplicity
            LocalDate date = LocalDate.of(2026, 1, day);
            executor.submit(() -> {
                String formatted = date.format(sharedFormatter); // same formatter, many threads, concurrently
                results.add(formatted);
            });
        }

        executor.shutdown();
        executor.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("Total formatted results: " + results.size());
        System.out.println("All results correctly formatted: " + results.stream().allMatch(s -> s.matches("\\d{4}-\\d{2}-\\d{2}")));
    }
}
```

**How to run:** `java DateTimeFormatterThreadSafe.java`

Expected output:
```
Total formatted results: 20
All results correctly formatted: true
```

This demonstrates `DateTimeFormatter`'s thread-safety directly: a single `sharedFormatter` instance is used concurrently by multiple threads (via an `ExecutorService` with `4` worker threads), each calling `.format(...)` on it simultaneously without any external synchronization. All `20` formatting operations complete correctly, producing well-formed `"yyyy-MM-dd"` strings with no corruption or interference between threads — a stark contrast to the old `SimpleDateFormat`, which is explicitly documented as *not* thread-safe and would require careful external synchronization (or a separate instance per thread) to avoid producing garbled or incorrect output under the exact same concurrent usage pattern.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `sharedFormatter` is created once, with the pattern `"yyyy-MM-dd"`. `results` is a `synchronizedList` (thread-safe for concurrent additions), and `executor` is a fixed thread pool with `4` worker threads.

The `for` loop submits `20` tasks to the executor. Each task captures a specific `LocalDate` (computed from the loop variable `i`, cycling `day` through `1` to `28`) and, when run by one of the `4` worker threads, calls `date.format(sharedFormatter)` — the *same* `sharedFormatter` object instance, referenced by whichever thread happens to execute that particular task.

Because `DateTimeFormatter` is documented as immutable and thread-safe, multiple threads can call `.format(...)` on the same instance simultaneously with no risk of interference: each call to `.format(...)` reads the formatter's internal pattern configuration (which never changes after construction) and produces its own independent output string, with no shared mutable state between concurrent calls that could cause one thread's formatting operation to corrupt another's.

```
sharedFormatter (ONE instance, pattern "yyyy-MM-dd", immutable)

Thread pool (4 workers) processes 20 submitted tasks concurrently:
  worker 1: date.format(sharedFormatter) -> "2026-01-01"
  worker 2: date.format(sharedFormatter) -> "2026-01-02"   (simultaneously, same formatter instance)
  worker 3: date.format(sharedFormatter) -> "2026-01-03"
  worker 4: date.format(sharedFormatter) -> "2026-01-04"
  ... (continues until all 20 tasks complete) ...

No corruption, no interference -- each call is independent despite sharing the formatter.
```

`executor.awaitTermination(5, TimeUnit.SECONDS)` blocks until all submitted tasks finish (or the timeout elapses). Once complete, `results.size()` is `20`, confirming every task successfully added its formatted result. `results.stream().allMatch(s -> s.matches("\\d{4}-\\d{2}-\\d{2}"))` checks that every single formatted string correctly matches the expected `"yyyy-MM-dd"` shape — `true`, confirming that concurrent, shared use of the single `sharedFormatter` instance produced consistently correct results across all `20` operations, with no thread-safety issues at all.

## 7. Gotchas & takeaways

> `SimpleDateFormat`, the pre-Java-8 formatter, is explicitly documented as **not** thread-safe — sharing a single `SimpleDateFormat` instance across multiple threads without external synchronization can silently produce corrupted or incorrect formatted output, a notoriously easy-to-hit bug in older Java code. `DateTimeFormatter` was specifically designed to fix this: instances are immutable, and safe to freely share and reuse across as many threads as needed, with no synchronization required.

- `DateTimeFormatter` converts between `java.time` values and `String` representations in both directions: `.format(formatter)` to text, `Type.parse(text, formatter)` from text.
- `DateTimeFormatter.ofPattern(...)` builds a custom formatter from a pattern string (`yyyy`, `MM`, `dd`, `MMMM`, and other pattern letters control the output format); built-in constants like `ISO_LOCAL_DATE` cover standard formats.
- Unlike the older `SimpleDateFormat`, `DateTimeFormatter` instances are immutable and fully thread-safe — a single instance can be freely shared and reused across multiple threads with no synchronization needed.
- The formatter used to *parse* a value has no lasting effect on how that value later displays itself via `toString()` — parsing and default display formatting are independent.
- Because `DateTimeFormatter` instances are immutable and expensive to reconstruct repeatedly, it's a good practice to create commonly-used formatters once (e.g. as `static final` fields) and reuse them, rather than calling `ofPattern(...)` fresh every time formatting is needed.
