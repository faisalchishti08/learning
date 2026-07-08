---
card: java
gi: 440
slug: more-precise-rethrow
title: More precise rethrow
---

## 1. What it is

"More precise rethrow" is a Java 7 compiler analysis: when a `catch` block catches a broad type (like `Exception`) and immediately rethrows the **same, unmodified** variable (`throw e;`), the compiler traces back through the corresponding `try` block to determine the actual, narrower set of checked exception types that could have reached that catch — and permits the enclosing method to declare only *those* specific types in its `throws` clause, rather than being forced to declare the broad caught type.

## 2. Why & when

Before Java 7, `catch (Exception e) { ...; throw e; }` forced the enclosing method to declare `throws Exception` — even if the `try` block could genuinely only ever throw, say, `IOException` or `SQLException`. This was a real loss of information for callers: they'd have to catch (or declare) the overly broad `Exception`, unable to rely on the method's signature to tell them precisely what could actually go wrong. The only workarounds were either accepting the imprecise `throws Exception`, or writing separate `catch` blocks for each specific type — reintroducing the duplication multi-catch was designed to avoid.

Java 7's more precise rethrow analysis fixes this specific combination: catch broadly (for shared handling logic, logging, or resource cleanup with a single `catch` block), but still let the method's `throws` clause — and therefore its callers — see the precise, narrow set of exception types that can actually occur. You benefit from this automatically any time you write a `catch (Exception e) { ...; throw e; }` pattern with common handling logic and a genuinely narrower set of possible exception types underneath.

## 3. Core concept

```java
import java.io.*;
import java.sql.*;

// Even though the catch declares "Exception e", the compiler proves that ONLY IOException
// or SQLException can actually reach this catch (from the try body below) -- so the method
// is allowed to declare the PRECISE throws clause, not the broader "throws Exception".
static void loadData(boolean fromFile) throws IOException, SQLException {
    try {
        if (fromFile) readFile();  // declares "throws IOException"
        else queryDb();            // declares "throws SQLException"
    } catch (Exception e) {
        log(e);       // shared handling logic, written once
        throw e;       // Java 7+ rethrows this as IOException or SQLException specifically
    }
}
```

This only works when the caught variable is rethrown **unmodified** — the moment you reassign it (`e = new SomeOtherException(...)`) inside the `catch` block, the compiler can no longer trace a precise type through the rethrow, and falls back to requiring the catch parameter's full *declared* type.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The compiler traces which specific checked exception types the try block could actually throw, and permits the method's throws clause to list only those types, even though the catch block itself declares the broader Exception type">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">try block can throw: IOException, SQLException (traced by the compiler)</text>
  <rect x="30" y="38" width="180" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="58" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">catch (Exception e)</text>

  <line x1="210" y1="53" x2="290" y2="53" stroke="#8b949e" marker-end="url(apr1)"/>
  <rect x="290" y="38" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="380" y="58" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">throw e; (unmodified)</text>

  <text x="320" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Method's throws clause: IOException, SQLException -- NOT the broader "Exception"</text>
  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Reassigning e before the throw breaks this -- falls back to the catch parameter's declared type.</text>
</svg>

The `throws` clause reflects what the try block can *actually* throw, not the broader type the catch block happens to declare.

## 5. Runnable example

Scenario: a data-loading routine that can fail in a few genuinely different ways — the same routine, evolved from a basic precise-rethrow with two checked exception types, through adding cleanup logic between the catch and the rethrow, to a realistic production pattern combining precise rethrow with try-with-resources and shared failure-metrics logging across three distinct checked exception types.

### Level 1 — Basic

```java
import java.io.*;
import java.sql.*;

public class PreciseRethrowBasic {
    static void readFile() throws IOException { throw new IOException("disk read failed"); }
    static void queryDb() throws SQLException { throw new SQLException("db down"); }

    static void loadData(boolean fromFile) throws IOException, SQLException {
        try {
            if (fromFile) readFile(); else queryDb();
        } catch (Exception e) {
            System.out.println("Rethrowing: " + e.getClass().getSimpleName());
            throw e; // Java 7+ analyzes this as rethrowing IOException or SQLException specifically
        }
    }

    public static void main(String[] args) {
        try {
            loadData(true);
        } catch (IOException e) {
            System.out.println("Caught IOException: " + e.getMessage());
        } catch (SQLException e) {
            System.out.println("Caught SQLException: " + e.getMessage());
        }
    }
}
```

**How to run:** `java PreciseRethrowBasic.java`

Even though the `catch` block declares the broad `Exception`, `loadData`'s `throws` clause lists only `IOException, SQLException` — the two specific types the `try` block can actually throw — and this compiles cleanly, because `throw e;` rethrows the caught variable completely unmodified.

### Level 2 — Intermediate

```java
import java.io.*;
import java.sql.*;

public class PreciseRethrowWithCleanup {
    static int attempts = 0;

    static void readFile() throws IOException { throw new IOException("disk read failed"); }
    static void queryDb() throws SQLException { throw new SQLException("db down"); }

    static void loadData(boolean fromFile) throws IOException, SQLException {
        try {
            if (fromFile) readFile(); else queryDb();
        } catch (Exception e) {
            attempts++; // real cleanup/bookkeeping work, still between catch and rethrow
            System.out.println("Attempt #" + attempts + " failed: " + e.getMessage());
            throw e; // precise rethrow still works even with extra statements in the catch block
        }
    }

    public static void main(String[] args) {
        for (boolean fromFile : new boolean[]{true, false}) {
            try {
                loadData(fromFile);
            } catch (IOException e) {
                System.out.println("Caller handling IOException specifically");
            } catch (SQLException e) {
                System.out.println("Caller handling SQLException specifically");
            }
        }
        System.out.println("Total failed attempts logged: " + attempts);
    }
}
```

**How to run:** `java PreciseRethrowWithCleanup.java`

Adding real bookkeeping (`attempts++`, a log line) between the `catch` and the `throw e;` doesn't disturb the precise-rethrow analysis — the caught variable is still rethrown unmodified, so the compiler can still trace its precise possible types through to the method's `throws` clause.

### Level 3 — Advanced

```java
import java.io.*;
import java.sql.*;

public class PreciseRethrowProduction {
    static class MetricsResource implements AutoCloseable {
        @Override public void close() { System.out.println("Metrics timer stopped"); }
    }

    static void readFile() throws IOException { throw new IOException("disk read failed"); }
    static void queryDb() throws SQLException { throw new SQLException("db down"); }
    static void parseConfig() throws ClassNotFoundException { throw new ClassNotFoundException("bad config class"); }

    // A common production pattern: a resource is opened, common logging/metrics happen on ANY
    // failure, the resource is always released (try-with-resources), yet the caller still sees
    // the EXACT original checked exception type -- not a broadened "throws Exception".
    static void loadData(int which) throws IOException, SQLException, ClassNotFoundException {
        try (MetricsResource metrics = new MetricsResource()) {
            switch (which) {
                case 0 -> readFile();
                case 1 -> queryDb();
                default -> parseConfig();
            }
        } catch (Exception e) {
            System.out.println("Recording failure metric for: " + e.getClass().getSimpleName());
            throw e; // precise rethrow: caller sees IOException, SQLException, or ClassNotFoundException exactly
        }
    }

    public static void main(String[] args) {
        for (int which = 0; which < 3; which++) {
            try {
                loadData(which);
            } catch (IOException e) {
                System.out.println("Caller: IOException -> " + e.getMessage());
            } catch (SQLException e) {
                System.out.println("Caller: SQLException -> " + e.getMessage());
            } catch (ClassNotFoundException e) {
                System.out.println("Caller: ClassNotFoundException -> " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java PreciseRethrowProduction.java`

This combines try-with-resources (the metrics resource is always closed, whichever of the three operations fails), one shared `catch (Exception e)` block for common failure-metrics logging, and precise rethrow — the method's `throws` clause lists all three specific checked exception types, and each caller `catch` block correctly receives exactly the type it expects.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The loop runs three times, with `which` set to `0`, `1`, and `2`.

**`which = 0`:** `loadData(0)` enters its `try (MetricsResource metrics = new MetricsResource())` block — `metrics` is constructed (no output; its constructor does nothing here). The `switch` selects `case 0 -> readFile();`, which throws `IOException("disk read failed")`. Because this is a try-with-resources statement, `metrics.close()` runs as part of unwinding — printing `"Metrics timer stopped"` — **before** the exception reaches the `catch` block. The `catch (Exception e)` block then runs, printing `"Recording failure metric for: IOException"`, and `throw e;` rethrows the same `IOException` object, unmodified. Back in `main`, the `catch (IOException e)` block catches it, printing `"Caller: IOException -> disk read failed"`.

**`which = 1`:** the same sequence plays out with `queryDb()` throwing `SQLException("db down")` instead — `metrics.close()` runs first, then the shared `catch` block logs `"Recording failure metric for: SQLException"`, rethrows it, and `main`'s `catch (SQLException e)` block catches it, printing `"Caller: SQLException -> db down"`.

**`which = 2`:** the `default` branch calls `parseConfig()`, throwing `ClassNotFoundException("bad config class")`. Again, `metrics.close()` runs first, the shared `catch` block logs `"Recording failure metric for: ClassNotFoundException"`, rethrows it, and `main`'s `catch (ClassNotFoundException e)` block catches it, printing `"Caller: ClassNotFoundException -> bad config class"`.

In every case, the resource is guaranteed to close, the failure is logged through one shared code path, and the caller still gets to `catch` the exact, specific exception type — all made possible by the compiler's precise-rethrow analysis on `loadData`'s `throws` clause.

Expected output:
```
Metrics timer stopped
Recording failure metric for: IOException
Caller: IOException -> disk read failed
Metrics timer stopped
Recording failure metric for: SQLException
Caller: SQLException -> db down
Metrics timer stopped
Recording failure metric for: ClassNotFoundException
Caller: ClassNotFoundException -> bad config class
```

## 7. Gotchas & takeaways

> Precise rethrow **only** works when the caught variable is rethrown completely **unmodified**. The moment you reassign it — even to wrap it in a new exception of a related type, like `e = new IOException("wrapped: " + e.getMessage());` — the compiler can no longer trace a precise type through the `throw`, and falls back to requiring the catch parameter's full *declared* type in the `throws` clause. Attempting `throw e;` after such a reassignment, inside a method declaring only the narrow types, produces a compile error: `"unreported exception Exception; must be caught or declared to be thrown"`.

- More precise rethrow lets a method catch broadly (`Exception`) for shared handling logic, while still declaring — and letting callers rely on — the narrow, actual set of checked exception types the `try` block can throw.
- This only applies to a plain, unmodified `throw e;` of the exact variable that was caught — reassigning it breaks the analysis.
- It works correctly even when the `catch` block contains other statements (logging, metrics, cleanup) between the `catch` and the `throw e;`, as long as the rethrow itself is unmodified.
- It composes cleanly with try-with-resources: a resource can be reliably closed via one shared `catch` block, while callers still see precisely-typed exceptions.
- This feature and multi-catch (the previous tutorial) solve complementary halves of the same underlying problem: handling several exception types with shared logic, without sacrificing type precision for either the handler or the caller.
