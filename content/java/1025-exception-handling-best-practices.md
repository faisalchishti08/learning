---
card: java
gi: 1025
slug: exception-handling-best-practices
title: Exception handling best practices
---

## 1. What it is

Good exception handling means throwing exceptions that carry enough information to diagnose what went wrong, catching only what you can genuinely handle, and never letting an exception disappear silently. Three habits do most of the work: **be specific** (throw and catch the narrowest exception type that fits, not a bare `Exception`), **preserve the cause** (when wrapping one exception in another, always pass the original as the cause, never discard it), and **never swallow silently** (an empty `catch` block that does nothing is one of the most common causes of "impossible" bugs that take hours to trace).

## 2. Why & when

Catching `Exception` broadly (or worse, `Throwable`) catches far more than you intended — it silently swallows genuine programming bugs (a `NullPointerException` from an unrelated typo) alongside the specific failure you meant to handle, hiding real problems behind a generic recovery path that was never designed for them. Discarding the original exception when wrapping one in another (`throw new ServiceException("failed")` instead of `throw new ServiceException("failed", originalException)`) throws away the actual root cause, leaving only a vague message and no stack trace pointing at the real failure. An empty `catch` block is the worst of all — the failure is detected, then actively thrown away, leaving the program to continue in a state the author never actually intended or tested.

Catch a specific exception type when you have a genuine, specific recovery action for it (retry a specific `IOException`, fall back to a default on a specific `NumberFormatException`). Always pass the original exception as the `cause` when wrapping it in a new one. Never leave a `catch` block empty — at minimum, log the exception; ideally, decide explicitly whether to recover, rethrow, or fail.

## 3. Core concept

```
// Bad: catches too broadly, swallows silently, loses the original cause
try {
    riskyOperation();
} catch (Exception e) {
    // empty -- the failure vanishes without a trace
}

// Good: catches a specific exception, logs it, and preserves the cause when wrapping
try {
    riskyOperation();
} catch (IOException e) {
    throw new ServiceException("failed to complete risky operation", e); // 'e' preserved as the CAUSE
}

class ServiceException extends RuntimeException {
    ServiceException(String message, Throwable cause) {
        super(message, cause); // the original stack trace is NOT lost
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An IOException being wrapped in a ServiceException with the cause preserved, versus an empty catch block that discards the exception entirely with no trace">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Swallowed: gone forever</text>
  <rect x="30" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">catch (Exception e) { }</text>
  <text x="145" y="100" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">no trace anywhere the failure ever happened</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Wrapped: cause preserved</text>
  <rect x="380" y="40" width="100" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="430" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">IOException</text>
  <rect x="500" y="40" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ServiceException</text>
  <line x1="480" y1="57" x2="500" y2="57" stroke="#79c0ff" marker-end="url(#a)"/>
  <text x="560" y="100" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">cause chain intact -- full stack trace</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A swallowed exception leaves no trace at all; a properly wrapped exception preserves the full cause chain for diagnosis.

## 5. Runnable example

Scenario: a file-processing service, evolving from silently-swallowed failures into precise, cause-preserving exception handling.

### Level 1 — Basic

```java
// File: ExceptionBasic.java
import java.io.FileReader;
import java.io.IOException;

public class ExceptionBasic {
    static String readFirstLine(String path) {
        try {
            FileReader reader = new FileReader(path);
            int c = reader.read();
            reader.close();
            return String.valueOf((char) c);
        } catch (Exception e) {
            // Swallowed! No log, no rethrow -- the failure vanishes completely.
        }
        return null;
    }

    public static void main(String[] args) {
        String result = readFirstLine("does-not-exist.txt");
        System.out.println("result: " + result);
        System.out.println("program continues as if nothing happened");
    }
}
```

**How to run:** save as `ExceptionBasic.java`, then `javac ExceptionBasic.java && java ExceptionBasic` (JDK 17+).

Expected output:
```
result: null
program continues as if nothing happened
```

The file genuinely didn't exist, and a real `FileNotFoundException` was thrown and caught — but the empty `catch` block discarded it entirely. `readFirstLine` returns `null` with zero indication of *why*, leaving anyone debugging this later with no clue at all.

### Level 2 — Intermediate

```java
// File: ExceptionIntermediate.java
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;

public class ExceptionIntermediate {
    static String readFirstLine(String path) throws IOException {
        try {
            FileReader reader = new FileReader(path);
            int c = reader.read();
            reader.close();
            return String.valueOf((char) c);
        } catch (FileNotFoundException e) {
            // Specific: caught exactly the case we know how to explain.
            throw new IOException("could not find file: " + path, e); // cause preserved
        }
    }

    public static void main(String[] args) {
        try {
            readFirstLine("does-not-exist.txt");
        } catch (IOException e) {
            System.out.println("failed: " + e.getMessage());
            System.out.println("caused by: " + e.getCause().getClass().getSimpleName());
        }
    }
}
```

**How to run:** save as `ExceptionIntermediate.java`, then `javac ExceptionIntermediate.java && java ExceptionIntermediate` (JDK 17+).

Expected output:
```
failed: could not find file: does-not-exist.txt
caused by: FileNotFoundException
```

The real-world concern added: the specific `FileNotFoundException` is caught, wrapped in a more descriptive `IOException`, and — critically — the original exception is passed as the `cause`. Nothing is silently lost; the caller gets both a clear message and full access to the original failure.

### Level 3 — Advanced

```java
// File: ExceptionAdvanced.java
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.logging.Level;
import java.util.logging.Logger;

class FileProcessingException extends RuntimeException {
    FileProcessingException(String message, Throwable cause) { super(message, cause); }
}

public class ExceptionAdvanced {
    private static final Logger LOGGER = Logger.getLogger(ExceptionAdvanced.class.getName());

    static String readFirstLine(FileReader alreadyOpenReader, String label) {
        try {
            int c = alreadyOpenReader.read();
            return String.valueOf((char) c);
        } catch (FileNotFoundException e) {
            // A recoverable, expected case: log at a low severity and provide a fallback.
            LOGGER.log(Level.WARNING, "file not found, using default: " + label, e);
            return "";
        } catch (IOException e) {
            // A genuinely unexpected I/O failure: wrap with full context and escalate.
            throw new FileProcessingException("unexpected I/O failure reading: " + label, e);
        }
    }

    public static void main(String[] args) throws IOException {
        FileReader reader = new FileReader("ExceptionAdvanced.java"); // this source file itself, guaranteed to exist
        String firstChar = readFirstLine(reader, "ExceptionAdvanced.java");
        System.out.println("first char: '" + firstChar + "'");
        reader.close();

        // A SEPARATE reader, closed immediately before any read -- guarantees the
        // next read() hits the closed stream directly, throwing IOException("Stream
        // closed"), never FileNotFoundException, since the file itself still exists.
        FileReader closedReader = new FileReader("ExceptionAdvanced.java");
        closedReader.close();
        try {
            readFirstLine(closedReader, "ExceptionAdvanced.java (closed before use)");
        } catch (FileProcessingException e) {
            System.out.println("escalated failure: " + e.getMessage());
            System.out.println("root cause message: " + e.getCause().getMessage());
        }
    }
}
```

**How to run:** save as `ExceptionAdvanced.java`, then `javac ExceptionAdvanced.java && java ExceptionAdvanced` (JDK 17+, run from the directory containing the saved file).

Expected output:
```
first char: 'i'
escalated failure: unexpected I/O failure reading: ExceptionAdvanced.java (closed before use)
root cause message: Stream closed
```

The production-flavored hard case: two different failure modes of the *same* method are handled completely differently — a missing file is treated as recoverable (logged, a sensible default returned), while reading from an already-closed stream is a genuinely unexpected I/O failure, escalated into a new, more specific exception that still preserves the original as its `cause`.

## 6. Walkthrough

Tracing the second `readFirstLine(closedReader, ...)` call in `ExceptionAdvanced.main`:

1. `closedReader` is constructed via `new FileReader("ExceptionAdvanced.java")` and then `.close()` is called on it immediately, before any read ever happens — the underlying stream is closed from the very first moment `closedReader` is used.
2. `readFirstLine(closedReader, "ExceptionAdvanced.java (closed before use)")` calls `alreadyOpenReader.read()` (bound to `closedReader`) inside its `try` block — reading from an already-closed `FileReader` throws `IOException` with the message `"Stream closed"`, **not** a `FileNotFoundException` (the file itself still exists on disk; it's the *stream* that's no longer usable).
3. Java checks `catch` clauses in order: `catch (FileNotFoundException e)` is checked first, but since the actual thrown type is the broader `IOException` (and this particular instance isn't a `FileNotFoundException`), it doesn't match — control falls through to `catch (IOException e)`.
4. Inside that block, `throw new FileProcessingException("unexpected I/O failure reading: ExceptionAdvanced.java (closed before use)", e)` constructs a new exception, passing the original `IOException` (`"Stream closed"`) as its `cause` — nothing about the original failure is lost.
5. That `FileProcessingException` propagates up out of `readFirstLine` to `main`'s `try` block, caught by `catch (FileProcessingException e)`, which prints the escalated message.
6. `e.getCause().getMessage()` retrieves the original `IOException`'s message directly from the cause chain — printed as `"root cause message: Stream closed"` — confirming that even though the exception was wrapped and given a more descriptive message, the original root cause remains fully accessible for diagnosis.

## 7. Gotchas & takeaways

> **Gotcha:** `catch` clauses are matched in order, and a subclass must be listed *before* its superclass — `catch (IOException e)` before `catch (FileNotFoundException e)` would make the more specific block unreachable (and, in modern Java, a compile error), since every `FileNotFoundException` would already be caught by the broader `IOException` clause first.

- Catch the narrowest exception type you have a genuine, specific recovery action for — catching broadly (`Exception`, `Throwable`) hides real bugs behind a generic recovery path never designed for them.
- Always pass the original exception as the `cause` argument when wrapping it in a new exception — discarding it loses the actual root cause and stack trace forever.
- Never leave a `catch` block empty — at an absolute minimum, log the exception; ideally, make an explicit decision to recover, rethrow, or escalate.
- `finally` blocks guarantee cleanup code runs whether the `try` block succeeds, throws, or even returns early — essential for releasing resources that aren't managed via `try-with-resources`.
- Different failure modes of the same operation can legitimately warrant completely different handling (a recoverable "not found" versus an unexpected I/O failure) — don't collapse distinct cases into one generic handler just to reduce boilerplate.
- See [avoid finalizers/cleaners](1021-avoid-finalizers-cleaners.md) and `try-with-resources` for the preferred, more modern alternative to manual `finally`-based resource cleanup wherever the resource implements `AutoCloseable`.
