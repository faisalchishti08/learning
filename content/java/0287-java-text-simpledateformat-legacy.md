---
card: java
gi: 287
slug: java-text-simpledateformat-legacy
title: java.text.SimpleDateFormat (legacy)
---

## 1. What it is

`java.text.SimpleDateFormat` is the legacy class for converting `Date` objects to and from formatted text, using a pattern string (like `"yyyy-MM-dd"`) to describe the desired format. It predates `java.time` and, critically, is **not thread-safe** — a single `SimpleDateFormat` instance shared across multiple threads without synchronization can produce silently incorrect, corrupted results, one of the most notorious pitfalls in classic Java date handling.

```java
import java.text.SimpleDateFormat;
import java.text.ParseException;
import java.util.Date;

public class SimpleDateFormatDemo {
    public static void main(String[] args) throws ParseException {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd");

        Date now = new Date();
        String formatted = formatter.format(now); // Date -> String
        System.out.println("Formatted: " + formatted);

        Date parsed = formatter.parse("2024-06-15"); // String -> Date
        System.out.println("Parsed: " + parsed);
    }
}
```

`formatter.format(now)` converts a `Date` object into a `String` following the given pattern (`"yyyy-MM-dd"` produces something like `"2024-06-15"`); `formatter.parse("2024-06-15")` does the reverse, converting a correctly-formatted `String` back into a `Date` object — both operations rely entirely on the pattern string matching the actual format being read or produced.

## 2. Why & when

Understanding `SimpleDateFormat` matters for reading and maintaining pre-Java-8 code that formats or parses dates, and — critically — for recognizing its thread-safety pitfall, a real, well-documented source of subtle, hard-to-reproduce bugs in older concurrent applications.

- **Pattern-based formatting was the standard approach for a long time** — before `java.time.format.DateTimeFormatter` (the modern, thread-safe replacement), `SimpleDateFormat`'s pattern syntax (`yyyy` for year, `MM` for month, `dd` for day, `HH:mm:ss` for time, and many more pattern letters) was the standard, widely-used way to control exactly how a date should be displayed or parsed.
- **The thread-safety problem is severe and easy to miss** — `SimpleDateFormat` instances maintain internal mutable state during formatting and parsing operations; sharing one instance across multiple threads (a very natural thing to do, since creating a new formatter for every single call seems wasteful) can cause one thread's in-progress operation to corrupt another's, producing wrong dates silently, with no exception thrown to signal the problem.
- **`ParseException` for malformed input** — unlike `Integer.parseInt`'s `NumberFormatException` (unchecked), `SimpleDateFormat.parse()` throws the *checked* `ParseException`, requiring a `try`/`catch` or a `throws` declaration wherever it's called.

Recognize `SimpleDateFormat` when reading legacy code, and understand its thread-safety issue thoroughly if you must maintain code that uses it (the standard mitigations are covered in the advanced example); for any new code, use `java.time.format.DateTimeFormatter` instead, which is immutable and fully thread-safe by design, eliminating this entire category of bugs.

## 3. Core concept

```java
import java.text.SimpleDateFormat;
import java.text.ParseException;

public class SimpleDateFormatCore {
    public static void main(String[] args) {
        SimpleDateFormat formatter = new SimpleDateFormat("MM/dd/yyyy");
        try {
            java.util.Date date = formatter.parse("13/45/2024"); // clearly invalid: month 13, day 45
        } catch (ParseException e) {
            System.out.println("Parse failed: " + e.getMessage());
        }
    }
}
```

`ParseException` is a *checked* exception, so calling `.parse(...)` requires handling it explicitly, either with a `try`/`catch` (as shown) or by declaring `throws ParseException` on the enclosing method — this reflects the philosophy that malformed date text represents a genuinely expected, "planned for" failure mode (parsing external text input), rather than a programming error, consistent with the checked-exceptions topic covered earlier.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single shared SimpleDateFormat instance used by multiple threads simultaneously can have one threads in progress internal state corrupted by another threads concurrent call, producing silently wrong results with no exception">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">ONE shared SimpleDateFormat</text>

  <line x1="260" y1="55" x2="150" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="340" y1="55" x2="450" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="60" y="95" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread A: format(date1)</text>

  <rect x="360" y="95" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="450" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Thread B: format(date2)</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Concurrent calls can corrupt each other's internal state — silently wrong results, no exception.</text>
</svg>

Concurrent use of a shared `SimpleDateFormat` instance can silently corrupt formatting/parsing results.

## 5. Runnable example

Scenario: a small date-formatting utility, evolved from basic single-threaded formatting into demonstrating the thread-safety pitfall conceptually, then hardened with the standard mitigation of a fresh instance per use.

### Level 1 — Basic

```java
import java.text.SimpleDateFormat;
import java.util.Date;

public class SimpleDateFormatBasic {
    public static void main(String[] args) {
        SimpleDateFormat formatter = new SimpleDateFormat("EEEE, MMMM d, yyyy");
        System.out.println(formatter.format(new Date()));
    }
}
```

**How to run:** `java SimpleDateFormatBasic.java`

The pattern `"EEEE, MMMM d, yyyy"` produces a fully spelled-out date like `"Saturday, June 15, 2024"` — `EEEE` is the full day-of-week name, `MMMM` is the full month name, `d` is the day-of-month without leading zeros, and `yyyy` is the four-digit year.

### Level 2 — Intermediate

Same idea, now parsing several date strings and handling malformed ones, demonstrating `ParseException` as a checked exception requiring explicit handling.

```java
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class SimpleDateFormatIntermediate {
    public static void main(String[] args) {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd");
        String[] inputs = { "2024-06-15", "not-a-date", "2024-12-31" };

        for (String input : inputs) {
            try {
                Date parsed = formatter.parse(input);
                System.out.println("Parsed '" + input + "' -> " + parsed);
            } catch (ParseException e) {
                System.out.println("Failed to parse '" + input + "': " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java SimpleDateFormatIntermediate.java`

Each parse attempt is individually wrapped in its own `try`/`catch`, so one malformed entry (`"not-a-date"`) doesn't prevent the other, validly formatted entries from being parsed successfully — the checked `ParseException` forces this explicit handling at compile time.

### Level 3 — Advanced

Same formatting utility, now demonstrating the standard, safe mitigation for `SimpleDateFormat`'s thread-safety problem: creating a fresh instance per use (or per thread) rather than sharing one instance across concurrent operations, using a small multi-threaded simulation to make the concept concrete.

```java
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class SimpleDateFormatAdvanced {
    // UNSAFE pattern (shown for illustration -- NOT actually run concurrently here to keep output deterministic):
    // static final SimpleDateFormat SHARED_FORMATTER = new SimpleDateFormat("yyyy-MM-dd"); // DANGEROUS if used across threads

    // SAFE pattern: create a fresh instance every time it's needed
    static String formatSafely(Date date) {
        SimpleDateFormat formatter = new SimpleDateFormat("yyyy-MM-dd"); // fresh instance, no sharing risk
        return formatter.format(date);
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        Date[] dates = {
            new Date(0),
            new Date(1_000_000_000_000L),
            new Date(1_700_000_000_000L),
            new Date()
        };

        for (Date date : dates) {
            pool.submit(() -> System.out.println("Formatted: " + formatSafely(date)));
        }

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS); // wait for all tasks to finish before the program exits
    }
}
```

**How to run:** `java SimpleDateFormatAdvanced.java`

`formatSafely` creates a brand-new `SimpleDateFormat` instance every time it's called, so even when four separate thread-pool tasks call it concurrently (each on a different thread), there is no shared, mutable formatter object for them to corrupt each other's state through — this is the standard, simplest fix for `SimpleDateFormat`'s thread-safety problem: never share an instance across threads, even at the cost of some object-creation overhead (or, alternatively, use a `ThreadLocal<SimpleDateFormat>` for a pooled, per-thread instance, a more advanced technique for high-throughput scenarios).

## 6. Walkthrough

Trace `main` in `SimpleDateFormatAdvanced` conceptually (note: the exact interleaving of the four concurrent tasks' output is not deterministic, since they run on a thread pool, but each individual result is guaranteed correct).

**`ExecutorService pool = Executors.newFixedThreadPool(4)`.** Creates a pool of four worker threads ready to execute submitted tasks.

**Four `Date` objects are constructed**, each representing a different point in time: the epoch (`new Date(0)`), two specific historical millisecond values, and the current moment.

**The loop submits four tasks to the pool**, one per date — each task is a lambda calling `formatSafely(date)` and printing the result. Because the pool has four threads, these four tasks may genuinely run concurrently, in parallel, on different threads.

**Inside `formatSafely`, each task creates its own, entirely separate `SimpleDateFormat` instance.** Since no two tasks ever share the same formatter object, there is no possibility of one task's in-progress formatting operation corrupting another's — even though all four tasks are using the identical *pattern* (`"yyyy-MM-dd"`), each has its own independent formatter object to work with.

**Each task's `formatter.format(date)` call completes correctly and independently**, producing the properly formatted date string for its specific `Date` argument, with no cross-contamination between tasks.

**`pool.shutdown()` and `pool.awaitTermination(5, TimeUnit.SECONDS)`.** Signals the pool to stop accepting new tasks and waits (up to five seconds) for all four already-submitted tasks to finish before the program proceeds to exit.

```
Four Date objects: epoch, two fixed historical instants, and "now"

Four tasks submitted to a 4-thread pool, each calling formatSafely(date):
  each task creates its OWN new SimpleDateFormat("yyyy-MM-dd") -- no sharing, no corruption risk
  each task's format(date) call is fully independent and correct

pool.shutdown() + awaitTermination(...) -- waits for all four tasks to finish
```

**Illustrative output** (the four lines may appear in any relative order, since the tasks run concurrently, but each individual line is guaranteed to be correctly formatted):
```
Formatted: 1970-01-01
Formatted: 2001-09-09
Formatted: 2023-11-14
Formatted: 2024-06-15
```

## 7. Gotchas & takeaways

> **Sharing a single `SimpleDateFormat` instance across multiple threads without synchronization is a genuine, well-documented bug — it can silently produce wrong, corrupted dates rather than throwing any exception**, making this class of bug notoriously difficult to detect and reproduce (it often only manifests under real concurrent load, not in simple single-threaded testing). Never store a `SimpleDateFormat` as a shared `static` field accessed by multiple threads unless it is properly synchronized or wrapped in a `ThreadLocal`.

> **The safe mitigations are: create a new instance per use (simplest, shown here), synchronize access to a shared instance (works, but serializes all formatting operations, hurting concurrency), or use a `ThreadLocal<SimpleDateFormat>` (gives each thread its own instance, reused across calls on that thread)** — but the cleanest, modern solution is simply switching to `java.time.format.DateTimeFormatter`, which is immutable and fully thread-safe by design, eliminating the need for any of these workarounds entirely.

- `SimpleDateFormat` converts between `Date` objects and formatted `String`s using a pattern string (`yyyy`, `MM`, `dd`, and many more pattern letters).
- `.parse(String)` throws the checked `ParseException` for malformed input text, requiring explicit handling wherever it's called.
- `SimpleDateFormat` is **not thread-safe** — sharing one instance across multiple threads can silently corrupt formatting or parsing results, a serious, well-documented real-world pitfall.
- Modern code should use `java.time.format.DateTimeFormatter` instead, which is immutable and fully thread-safe, eliminating this entire class of concurrency bug.
