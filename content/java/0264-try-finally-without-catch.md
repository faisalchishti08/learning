---
card: java
gi: 264
slug: try-finally-without-catch
title: try-finally without catch
---

## 1. What it is

A `try` block can be paired directly with a `finally` block and no `catch` clause at all — this is entirely legal syntax. It means: run this code, and guarantee the `finally` block executes afterward, but do not attempt to catch or handle any exception here at all; any exception thrown inside the `try` still propagates onward, unimpeded, to whatever caller (or further `try`/`catch`) is positioned to actually handle it.

```java
public class TryFinallyDemo {
    static void withoutCatch() {
        try {
            System.out.println("Doing work...");
            throw new RuntimeException("something failed");
        } finally {
            System.out.println("Cleanup happens here, regardless");
        }
        // no catch clause at all -- the exception is NOT handled here
    }

    public static void main(String[] args) {
        try {
            withoutCatch();
        } catch (RuntimeException e) {
            System.out.println("Handled higher up, in main: " + e.getMessage());
        }
    }
}
```

`withoutCatch` has a `try`/`finally` with no `catch` at all — its `finally` block still runs (printing `"Cleanup happens here, regardless"`), but the `RuntimeException` is never actually caught inside `withoutCatch` itself; it propagates straight out of the method after the `finally` block completes, and is only actually caught up in `main`, one level higher in the call stack.

## 2. Why & when

A `try`/`finally` with no `catch` is used specifically when a method wants to guarantee cleanup happens locally, but has no intention (or ability) to actually handle the exception itself — that responsibility belongs to a caller further up the chain.

- **Separating cleanup responsibility from handling responsibility** — a low-level method that opens a resource often knows exactly how to clean up after itself (close the resource), but has no idea what the *right* response to a failure actually is (retry? show an error? log and continue?) — that decision belongs to code higher up that has more context about the overall operation.
- **Guaranteeing local cleanup without swallowing information** — if `withoutCatch` *did* add a `catch` clause just to log something and then rethrow, that's more verbose and easy to get wrong (forgetting to rethrow, or losing the original stack trace); a plain `try`/`finally` guarantees the cleanup runs while keeping the exception completely intact and unaltered as it propagates.
- **A common pattern in resource-management code** — a method that opens a connection, uses it, and must close it — but does not know what to do if the operation itself fails — is a textbook case for `try`/`finally` without `catch`; the modern `try-with-resources` construct (a dedicated topic ahead) builds directly on this same idea for anything implementing `AutoCloseable`.

Use a plain `try`/`finally` (no `catch`) when a method needs guaranteed local cleanup but should not attempt to interpret or recover from the failure itself — let the exception propagate untouched to a caller that has the context needed to actually decide how to respond.

## 3. Core concept

```java
public class TryFinallyCore {
    static String readFirstLine(java.io.BufferedReader reader) throws java.io.IOException {
        try {
            return reader.readLine(); // might throw IOException
        } finally {
            reader.close(); // ALWAYS close the reader, whether readLine succeeded or threw
        }
        // no catch: readFirstLine does not know how to "handle" an IOException --
        // it just guarantees the reader gets closed, then lets the caller decide what to do
    }
}
```

`readFirstLine` guarantees `reader.close()` runs no matter what — but it declares `throws java.io.IOException` on its own signature (since `IOException` is checked, as covered earlier) rather than catching it, explicitly signaling "I clean up after myself, but interpreting this failure is your job as the caller."

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A try finally block with no catch guarantees local cleanup runs, then lets any exception propagate untouched to a caller further up the call stack that is actually responsible for handling it">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="38" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">readFirstLine()</text>
  <rect x="60" y="45" width="180" height="20" rx="4" fill="#0d1117" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="59" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">try: may throw IOException</text>
  <rect x="60" y="70" width="180" height="20" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="84" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">finally: reader.close() — ALWAYS</text>

  <line x1="260" y1="60" x2="360" y2="60" stroke="#f85149" stroke-width="1.5"/>
  <text x="310" y="50" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">propagates</text>

  <rect x="360" y="40" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="460" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">caller decides how to handle it</text>

  <text x="300" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Cleanup happens locally; the decision about how to respond belongs to a caller higher up.</text>
</svg>

`try`/`finally` guarantees local cleanup while leaving the decision of how to handle the failure to a caller further up the chain.

## 5. Runnable example

Scenario: a layered resource-access system where a low-level method guarantees cleanup without handling failures itself, evolved from a single-layer example into a multi-layer call chain, then hardened with a case where the `finally` cleanup itself could also fail, showing the standard way that scenario is handled.

### Level 1 — Basic

```java
public class TryFinallyBasic {
    static class Connection {
        boolean open = true;
        void query() {
            if (!open) throw new IllegalStateException("connection already closed");
            System.out.println("Querying...");
        }
        void close() { open = false; System.out.println("Connection closed"); }
    }

    static void runQuery(Connection conn) {
        try {
            conn.query();
        } finally {
            conn.close(); // guaranteed cleanup, no catch here
        }
    }

    public static void main(String[] args) {
        Connection conn = new Connection();
        runQuery(conn);
        System.out.println("Connection still open? " + conn.open);
    }
}
```

**How to run:** `java TryFinallyBasic.java`

`runQuery` has no `catch` clause at all — it simply guarantees `conn.close()` runs after `conn.query()`, whether that succeeds or fails; here, `query()` succeeds normally, so `finally` runs immediately afterward with no exception involved at all.

### Level 2 — Intermediate

Same connection idea, now with the query actually failing, demonstrating the exception propagating out of `runQuery` (which never catches it) and being handled only in `main`, one level up.

```java
public class TryFinallyIntermediate {
    static class Connection {
        boolean open = true;
        void query(boolean shouldFail) {
            if (!open) throw new IllegalStateException("connection already closed");
            if (shouldFail) throw new RuntimeException("query execution failed");
            System.out.println("Querying...");
        }
        void close() { open = false; System.out.println("Connection closed"); }
    }

    static void runQuery(Connection conn, boolean shouldFail) {
        try {
            conn.query(shouldFail);
        } finally {
            conn.close(); // still runs, even though the exception below is not caught here
        }
    }

    public static void main(String[] args) {
        Connection conn = new Connection();
        try {
            runQuery(conn, true); // will fail
        } catch (RuntimeException e) {
            System.out.println("Handled in main: " + e.getMessage());
        }
        System.out.println("Connection still open? " + conn.open);
    }
}
```

**How to run:** `java TryFinallyIntermediate.java`

`runQuery` itself never catches the `RuntimeException` from `conn.query(true)` — it only guarantees `conn.close()` runs via `finally` — so the exception propagates all the way out of `runQuery` and is only actually caught in `main`, which is the layer with enough context to decide what "handling" a failed query should actually mean.

### Level 3 — Advanced

Same layered system, now with a realistic complication: what happens if the cleanup code inside `finally` itself throws? This demonstrates the standard defensive pattern of guarding cleanup code so a secondary failure during cleanup doesn't mask (or crash out from under) the original exception.

```java
public class TryFinallyAdvanced {
    static class Connection {
        boolean open = true;
        boolean closeShouldFail;
        Connection(boolean closeShouldFail) { this.closeShouldFail = closeShouldFail; }

        void query(boolean shouldFail) {
            if (!open) throw new IllegalStateException("connection already closed");
            if (shouldFail) throw new RuntimeException("query execution failed");
            System.out.println("Querying...");
        }

        void close() {
            open = false;
            if (closeShouldFail) throw new RuntimeException("close() itself failed too!");
            System.out.println("Connection closed");
        }
    }

    static void runQuery(Connection conn, boolean queryShouldFail) {
        try {
            conn.query(queryShouldFail);
        } finally {
            try {
                conn.close(); // guard the cleanup itself
            } catch (RuntimeException closeError) {
                // Log the secondary failure but do NOT let it silently replace the original exception
                System.out.println("Warning: close() also failed: " + closeError.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        Connection conn = new Connection(true); // close() will ALSO fail
        try {
            runQuery(conn, true); // query() fails too
        } catch (RuntimeException e) {
            System.out.println("Original query failure still correctly propagated: " + e.getMessage());
        }
    }
}
```

**How to run:** `java TryFinallyAdvanced.java`

Wrapping `conn.close()` in its own inner `try`/`catch` inside the `finally` block prevents a secondary failure during cleanup from silently overriding the original, more important exception from `query()` — without this inner guard, an exception thrown directly from `finally` would behave exactly like the `return`-inside-`finally` pitfall from the previous topic: it would completely replace the original exception, and the real cause of the failure (the query itself) would be lost.

## 6. Walkthrough

Trace `main` in `TryFinallyAdvanced` step by step.

**`new Connection(true)`.** Creates a `Connection` with `open = true` and `closeShouldFail = true` (so its `close()` method is configured to also throw).

**`runQuery(conn, true)`.** Inside `runQuery`'s `try` block, `conn.query(true)` is called: `open` is `true` (so the first guard doesn't fire), but `shouldFail` is `true`, so `RuntimeException("query execution failed")` is thrown immediately. This exception begins propagating out of the `try` block.

**Before it can leave `runQuery`, the `finally` block runs.** Inside it, an inner `try` wraps `conn.close()`: this sets `open = false`, then checks `closeShouldFail` — `true`, so it throws its own `RuntimeException("close() itself failed too!")`. This inner exception is immediately caught by the inner `catch (RuntimeException closeError)` clause, which prints `"Warning: close() also failed: close() itself failed too!"` — this secondary failure is logged, but crucially, it does *not* propagate any further and does *not* replace anything.

**The `finally` block completes normally** (its own inner exception was fully handled and contained). Since `finally` did not throw or return anything of its own, the *original* pending exception from `query()` (`"query execution failed"`) is now free to continue propagating out of `runQuery`, completely intact and unaffected by the cleanup failure that occurred.

**Back in `main`'s `try`/`catch`.** The original `RuntimeException("query execution failed")` is caught. Prints `"Original query failure still correctly propagated: query execution failed"`.

```
runQuery(conn, true):
  try: conn.query(true) -> throws RuntimeException("query execution failed") -- begins propagating

  finally block runs:
    inner try: conn.close() -> open=false, closeShouldFail=true -> throws RuntimeException("close() itself failed too!")
    inner catch: catches it, logs "Warning: close() also failed: ..." -- CONTAINED here, goes no further

  finally completes normally -> original "query execution failed" exception resumes propagating

main catches original exception -> prints "Original query failure still correctly propagated: query execution failed"
```

**Final output.**
```
Warning: close() also failed: close() itself failed too!
Original query failure still correctly propagated: query execution failed
```
This demonstrates the standard defensive pattern: guard cleanup code inside `finally` with its own `try`/`catch` so that a secondary failure during cleanup is logged and contained, rather than silently destroying the original, more important exception — exactly the risk the previous topic's "never `return`/`throw` unguarded from `finally`" gotcha warned about.

## 7. Gotchas & takeaways

> **An exception thrown directly from an unguarded `finally` block silently replaces any exception already propagating from the `try` block** — this is the same underlying mechanism as the `return`-inside-`finally` pitfall from the previous topic, just triggered by a `throw` instead. If cleanup code inside `finally` can itself fail, wrap it in its own inner `try`/`catch` (as shown) so a secondary cleanup failure is logged without destroying the original, usually more important, exception.

> **`try`/`finally` without `catch` is not "incomplete" exception handling — it is a deliberate, complete design choice** meaning "this method guarantees its own local cleanup, but has no opinion on how the failure itself should be handled." Recognizing this pattern (rather than assuming every `try` needs a `catch`) is important both for reading other people's code and for correctly separating cleanup responsibility from failure-handling responsibility in your own designs.

- `try`/`finally` with no `catch` clause is legal and common: it guarantees local cleanup runs, while letting any exception propagate untouched to a caller better positioned to handle it.
- This pattern deliberately separates "who cleans up" (the method itself) from "who decides how to respond to the failure" (a caller higher up the call stack).
- If cleanup code inside `finally` can itself throw, guard it with its own inner `try`/`catch` to prevent a secondary failure from silently replacing the original, more important exception.
- The modern `try-with-resources` construct builds directly on this same idea for any resource implementing `AutoCloseable`, automating the guaranteed-cleanup pattern shown here.
