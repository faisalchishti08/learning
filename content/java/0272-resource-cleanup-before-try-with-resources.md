---
card: java
gi: 272
slug: resource-cleanup-before-try-with-resources
title: Resource cleanup before try-with-resources
---

## 1. What it is

Before Java 7 introduced `try-with-resources` (a dedicated upcoming topic), the standard way to guarantee a resource — a file, a network connection, a database cursor — was properly closed, whether or not an operation on it succeeded, was a manual `try`/`finally` block: open the resource, use it inside `try`, and close it inside `finally`, guarding the `close()` call itself against its own possible failure, exactly as an earlier topic's advanced example demonstrated.

```java
import java.io.FileReader;
import java.io.IOException;

public class ManualCleanupDemo {
    static void readFirstChar(String path) throws IOException {
        FileReader reader = null;
        try {
            reader = new FileReader(path);
            System.out.println("First char code: " + reader.read());
        } finally {
            if (reader != null) { // must check for null, in case the constructor itself failed
                reader.close();
            }
        }
    }
}
```

`reader` is declared *outside* the `try` block (so it remains visible to the `finally` block), initialized to `null` up front, and the `finally` block explicitly checks `reader != null` before calling `close()` — this null check matters because if `new FileReader(path)` itself throws (say, the file doesn't exist), `reader` would still be `null` when `finally` runs, and calling `close()` on `null` would throw a `NullPointerException`, masking the original, more meaningful exception.

## 2. Why & when

Understanding this manual pattern matters for reading older Java codebases (which are still common) and for appreciating exactly what `try-with-resources` automates and simplifies on your behalf.

- **The manual pattern is verbose and easy to get subtly wrong** — declaring the resource variable outside the `try`, remembering the `null` check, and guarding `close()` itself against a secondary failure (as covered in the `try`/`finally` topic) all had to be done correctly, by hand, every single time a resource needed cleanup — a lot of repetitive, error-prone ceremony for something conceptually simple.
- **Multiple resources multiply the complexity** — closing two or more resources correctly (in the right order, with each one's `close()` guarded independently so a failure closing the first doesn't prevent an attempt to close the second) required deeply nested `try`/`finally` blocks that became difficult to read and verify correct at a glance.
- **`try-with-resources` was introduced specifically to eliminate this ceremony** — by requiring resources to implement `AutoCloseable` and letting the `try` statement itself declare and manage them, Java automated exactly this pattern, correctly, every time, without the manual boilerplate — but understanding the manual version first makes clear exactly what problem `try-with-resources` solves and why it matters.

Recognize this manual pattern when reading legacy code, and understand it as the direct motivation for `try-with-resources`, which should be strongly preferred for any new code working with `AutoCloseable` resources — this topic exists specifically to set up that contrast, not to recommend writing new code this way.

## 3. Core concept

```java
import java.io.FileReader;
import java.io.IOException;

public class ManualCleanupCore {
    static void copyFirstChars(String path1, String path2) throws IOException {
        FileReader reader1 = null;
        FileReader reader2 = null;
        try {
            reader1 = new FileReader(path1);
            reader2 = new FileReader(path2); // if THIS fails, reader1 must still be closed!
            System.out.println(reader1.read() + " / " + reader2.read());
        } finally {
            if (reader1 != null) {
                try { reader1.close(); } catch (IOException e) { /* log, don't let it mask anything */ }
            }
            if (reader2 != null) {
                try { reader2.close(); } catch (IOException e) { /* log, don't let it mask anything */ }
            }
        }
    }
}
```

Both resources need independent `null` checks and independently guarded `close()` calls inside the `finally` block, so that a failure closing `reader1` doesn't prevent an attempt to close `reader2`, and so that if `reader2`'s constructor itself failed (leaving it `null`), the code doesn't attempt to close a `null` reference — this nested guarding is exactly the kind of repetitive, careful bookkeeping `try-with-resources` was designed to eliminate.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Manual cleanup requires declaring the resource outside try, null checking it in finally, and guarding the close call itself against its own possible failure, all done by hand for every resource">
  <rect x="8" y="8" width="584" height="184" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="240" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">FileReader reader = null; // outside try</text>

  <rect x="40" y="60" width="240" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">try { reader = new FileReader(...); use it }</text>

  <rect x="40" y="100" width="240" height="65" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="160" y="120" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">finally {</text>
  <text x="160" y="136" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">if (reader != null)</text>
  <text x="160" y="150" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">try { reader.close(); } catch (...) { }</text>

  <text x="450" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All of this manual</text>
  <text x="450" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">bookkeeping is exactly</text>
  <text x="450" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">what try-with-resources</text>
  <text x="450" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">automates for you.</text>
</svg>

Manual cleanup requires careful, repetitive bookkeeping that `try-with-resources` automates entirely.

## 5. Runnable example

Scenario: a simulated resource (standing in for a real file or connection) requiring manual cleanup, evolved from a single-resource pattern into the correctly nested multi-resource version, then hardened with the "don't let a cleanup failure mask the original exception" guard fully worked out.

### Level 1 — Basic

```java
public class ManualCleanupBasic {
    static class Connection implements AutoCloseable {
        String name;
        Connection(String name) {
            this.name = name;
            System.out.println("Opened: " + name);
        }
        void use() { System.out.println("Using: " + name); }
        @Override
        public void close() { System.out.println("Closed: " + name); }
    }

    static void doWork() {
        Connection conn = null;
        try {
            conn = new Connection("DB");
            conn.use();
        } finally {
            if (conn != null) {
                conn.close();
            }
        }
    }

    public static void main(String[] args) {
        doWork();
    }
}
```

**How to run:** `java ManualCleanupBasic.java`

`conn` is declared outside `try` (so `finally` can see it), initialized to `null`, and only closed if it's not `null` — the baseline single-resource manual pattern, guaranteed to close the connection whether `use()` succeeds or fails.

### Level 2 — Intermediate

Same idea, now with two resources, demonstrating the nested structure needed to guarantee both are closed independently, even if opening or using the second one fails.

```java
public class ManualCleanupIntermediate {
    static class Connection implements AutoCloseable {
        String name;
        Connection(String name) {
            this.name = name;
            System.out.println("Opened: " + name);
        }
        void use() { System.out.println("Using: " + name); }
        @Override
        public void close() { System.out.println("Closed: " + name); }
    }

    static void doWork(boolean secondConnectionFails) {
        Connection conn1 = null;
        Connection conn2 = null;
        try {
            conn1 = new Connection("Primary DB");
            conn1.use();

            if (secondConnectionFails) throw new RuntimeException("could not reach secondary DB");
            conn2 = new Connection("Secondary DB");
            conn2.use();
        } finally {
            // Close in REVERSE order of acquisition, each independently guarded
            if (conn2 != null) conn2.close();
            if (conn1 != null) conn1.close(); // still runs even if conn2 was never successfully opened
        }
    }

    public static void main(String[] args) {
        try {
            doWork(true);
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ManualCleanupIntermediate.java`

When `secondConnectionFails` is `true`, `conn2` is never assigned (it remains `null`), so the `finally` block's `if (conn2 != null)` check correctly skips closing it, while `conn1` — which *was* successfully opened — is still correctly closed via the second check; this demonstrates exactly why each resource needs its own independent `null` guard in the manual pattern.

### Level 3 — Advanced

Same two-resource system, now with the full defensive pattern: each `close()` call individually guarded against its own possible failure, so a cleanup exception from one resource cannot prevent the other from being closed, and neither cleanup failure masks the original exception from the `try` block.

```java
public class ManualCleanupAdvanced {
    static class Connection implements AutoCloseable {
        String name;
        boolean closeShouldFail;
        Connection(String name, boolean closeShouldFail) {
            this.name = name;
            this.closeShouldFail = closeShouldFail;
            System.out.println("Opened: " + name);
        }
        void use() { System.out.println("Using: " + name); }
        @Override
        public void close() {
            if (closeShouldFail) throw new RuntimeException("close() failed for " + name);
            System.out.println("Closed: " + name);
        }
    }

    static void doWork() {
        Connection conn1 = null;
        Connection conn2 = null;
        try {
            conn1 = new Connection("Primary DB", true);  // its close() will fail
            conn1.use();
            conn2 = new Connection("Secondary DB", false); // its close() will succeed
            conn2.use();
            throw new RuntimeException("main operation failed"); // the ORIGINAL, most important exception
        } finally {
            // Each close() independently guarded -- a failure in one must not prevent the other,
            // and neither should mask the original exception above.
            if (conn2 != null) {
                try { conn2.close(); } catch (RuntimeException e) { System.out.println("Warning: " + e.getMessage()); }
            }
            if (conn1 != null) {
                try { conn1.close(); } catch (RuntimeException e) { System.out.println("Warning: " + e.getMessage()); }
            }
        }
    }

    public static void main(String[] args) {
        try {
            doWork();
        } catch (RuntimeException e) {
            System.out.println("Original failure correctly propagated: " + e.getMessage());
        }
    }
}
```

**How to run:** `java ManualCleanupAdvanced.java`

Both `close()` calls are wrapped in their own inner `try`/`catch`, so `conn1.close()`'s failure (logged as a warning) does not prevent `conn2.close()` from being attempted (it already ran first, in reverse order, and succeeded), and — critically — neither cleanup failure replaces the original `"main operation failed"` exception, which is exactly what should reach `main`'s outer `catch` block as the primary, most important failure to report.

## 6. Walkthrough

Trace `doWork()` in `ManualCleanupAdvanced` from start to finish.

**`conn1 = new Connection("Primary DB", true)`.** Prints `"Opened: Primary DB"`. `conn1.use()` prints `"Using: Primary DB"`.

**`conn2 = new Connection("Secondary DB", false)`.** Prints `"Opened: Secondary DB"`. `conn2.use()` prints `"Using: Secondary DB"`.

**`throw new RuntimeException("main operation failed")`.** This begins propagating out of the `try` block — but the `finally` block must run first.

**`finally` block: closing `conn2` first (reverse order).** `conn2 != null` is `true`. Inner `try`: `conn2.close()` — `closeShouldFail` is `false`, so it prints `"Closed: Secondary DB"` and returns normally, no exception.

**`finally` block: closing `conn1` next.** `conn1 != null` is `true`. Inner `try`: `conn1.close()` — `closeShouldFail` is `true`, so it throws `RuntimeException("close() failed for Primary DB")`. This is caught by the inner `catch (RuntimeException e)`, printing `"Warning: close() failed for Primary DB"` — contained here, goes no further.

**The `finally` block completes normally** (both inner exceptions, if any, were fully contained). The original, pending `"main operation failed"` exception — which was waiting to propagate since before `finally` even started — now resumes propagating out of `doWork()`.

**Back in `main`'s `try`/`catch`.** The original exception is caught. Prints `"Original failure correctly propagated: main operation failed"`.

```
conn1 = new Connection("Primary DB", true)  -> "Opened: Primary DB"
conn1.use() -> "Using: Primary DB"
conn2 = new Connection("Secondary DB", false) -> "Opened: Secondary DB"
conn2.use() -> "Using: Secondary DB"
throw RuntimeException("main operation failed") -- begins propagating

finally:
  close conn2 (reverse order): closeShouldFail=false -> "Closed: Secondary DB" (no exception)
  close conn1: closeShouldFail=true -> throws -> caught inner -> "Warning: close() failed for Primary DB"

finally completes -> original "main operation failed" resumes propagating
main catches it -> "Original failure correctly propagated: main operation failed"
```

**Final output.**
```
Opened: Primary DB
Using: Primary DB
Opened: Secondary DB
Using: Secondary DB
Closed: Secondary DB
Warning: close() failed for Primary DB
Original failure correctly propagated: main operation failed
```
This demonstrates the complete, correct manual cleanup pattern: both resources get an attempt at cleanup, in reverse acquisition order, each guarded independently, and the original, most important exception is never masked by any secondary cleanup failure — exactly the behaviour `try-with-resources` provides automatically, without all of this hand-written bookkeeping.

## 7. Gotchas & takeaways

> **Forgetting the `null` check on a resource variable inside `finally` is a common bug when a resource's constructor itself can fail** — if `new Connection(...)` throws before the assignment completes, the variable remains `null`, and calling `.close()` on it directly (without the `if (conn != null)` guard) throws `NullPointerException` from inside `finally`, which — per the earlier `finally`-block topic — would silently replace whatever original exception was propagating, masking the real problem entirely.

> **This manual pattern is exactly what motivated `try-with-resources`** — every piece of ceremony shown here (declaring outside `try`, null-checking, guarding `close()` against its own failure, closing in reverse order for multiple resources) is handled automatically and correctly by `try-with-resources`, which should be strongly preferred for any resource implementing `AutoCloseable` in new code; this manual pattern remains important to recognize specifically when reading or maintaining older Java code that predates it.

- Manual resource cleanup requires declaring the resource variable outside the `try` block, initializing it to `null`, and null-checking it inside `finally` before calling `close()`.
- Multiple resources must be closed in reverse order of acquisition, each with its own independent `null` check and its own guarded `try`/`catch` around `close()`, so one resource's cleanup failure doesn't prevent another's.
- This entire pattern is verbose and error-prone to write correctly by hand, which is exactly the problem `try-with-resources` (the next related topic) was introduced to solve automatically.
- Recognize this pattern in legacy code, but prefer `try-with-resources` for any new code working with `AutoCloseable` resources.
