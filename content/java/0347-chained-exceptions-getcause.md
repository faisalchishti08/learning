---
card: java
gi: 347
slug: chained-exceptions-getcause
title: Chained exceptions (getCause)
---

## 1. What it is

Exception chaining preserves the original cause of a failure when it's caught and re-thrown as a different exception type — instead of losing the original exception's information, the new exception carries a reference to it, retrievable via `getCause()`. This is essential when a low-level failure (say, a `SQLException`) needs to be reported as a higher-level, more meaningful exception (say, a custom `OrderProcessingException`) without discarding exactly what went wrong underneath.

```java
public class GetCauseDemo {
    public static void main(String[] args) {
        try {
            riskyOperation();
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
            System.out.println("Caused by: " + e.getCause());
        }
    }

    static void riskyOperation() {
        try {
            throw new ArithmeticException("/ by zero");
        } catch (ArithmeticException original) {
            throw new RuntimeException("Operation failed", original); // wraps the original as the cause
        }
    }
}
```

Passing `original` as the second argument to `new RuntimeException(message, cause)` links the two exceptions — `e.getCause()` on the outer exception returns the exact original `ArithmeticException` instance, preserving full detail about what actually went wrong first.

## 2. Why & when

Different layers of an application often need to translate low-level, implementation-specific exceptions into higher-level, more meaningful ones — a repository layer might catch a `SQLException` and throw a `DataAccessException`, since callers shouldn't need to know or care that the underlying storage happens to be a SQL database. Without chaining, that translation would silently discard the original exception's message, type, and stack trace — critical information for actually diagnosing the failure.

- **Translating between abstraction layers** — converting a low-level exception (network, database, file I/O) into a higher-level, domain-meaningful one, while keeping the original failure detail available for logging and debugging.
- **Debugging and logging** — a printed stack trace of a chained exception shows both the outer exception and, beneath a `"Caused by:"` line, the original exception's own stack trace, letting you trace the failure back to its true root cause.
- **Avoiding silent information loss** — catching an exception and throwing a *new*, unrelated one without passing the original as a cause ("swallowing" it) destroys the ability to diagnose what actually happened.

`getCause()` returns `null` if no cause was ever set — not every exception is part of a chain — so code that walks a cause chain (looking for a specific underlying exception type, for instance) must handle reaching the end of the chain, not assume it can always go one level deeper.

## 3. Core concept

```java
public class GetCauseCore {
    public static void main(String[] args) {
        try {
            loadConfig();
        } catch (RuntimeException e) {
            Throwable current = e;
            int depth = 0;
            while (current != null) {
                System.out.println("  ".repeat(depth) + current.getClass().getSimpleName() + ": " + current.getMessage());
                current = current.getCause(); // walk the chain until it ends (getCause returns null)
                depth++;
            }
        }
    }

    static void loadConfig() {
        try {
            parseFile();
        } catch (RuntimeException e) {
            throw new RuntimeException("Failed to load config", e);
        }
    }

    static void parseFile() {
        try {
            Integer.parseInt("not-a-number");
        } catch (NumberFormatException e) {
            throw new RuntimeException("Failed to parse file contents", e);
        }
    }
}
```

**How to run:** `java GetCauseCore.java`

Walking `current = current.getCause()` in a loop until it returns `null` traces the entire chain from the outermost, most general exception down to the innermost, most specific root cause — here revealing three layers: the config-loading failure, the parsing failure, and the original `NumberFormatException`.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each exception in a chain holds a reference to its cause, forming a linked list traceable back to the original root-cause exception">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="50" width="150" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="72" fill="#79c0ff" font-size="9" text-anchor="middle">RuntimeException (outer)</text>

  <text x="185" y="72" fill="#8b949e" font-size="12">getCause() →</text>

  <rect x="260" y="50" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="335" y="72" fill="#8b949e" font-size="9" text-anchor="middle">RuntimeException (middle)</text>

  <text x="425" y="72" fill="#8b949e" font-size="12">getCause() →</text>

  <rect x="480" y="50" width="110" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="72" fill="#6db33f" font-size="9" text-anchor="middle">NumberFormatException</text>
</svg>

## 5. Runnable example

Scenario: an order lookup service, evolved from silently swallowing an underlying error, into one that wraps it while preserving the cause, into a production-style handler that inspects the full cause chain to decide how to respond and logs the complete chain for diagnosis.

### Level 1 — Basic

```java
public class OrderLookupBasic {
    public static void main(String[] args) {
        try {
            lookupOrder("bad-id");
        } catch (RuntimeException e) {
            System.out.println("Lookup failed: " + e.getMessage()); // original detail is gone
        }
    }

    static void lookupOrder(String id) {
        try {
            Integer.parseInt(id); // simulates parsing an ID that should be numeric
        } catch (NumberFormatException original) {
            throw new RuntimeException("Order lookup failed"); // BUG: original not passed as cause
        }
    }
}
```

**How to run:** `java OrderLookupBasic.java`

The new `RuntimeException` is thrown without passing `original` as its cause, so `e.getCause()` would return `null` — the fact that the real problem was a malformed numeric ID is completely lost, leaving only a generic "Order lookup failed" message to debug from.

### Level 2 — Intermediate

```java
public class OrderLookupIntermediate {
    public static void main(String[] args) {
        try {
            lookupOrder("bad-id");
        } catch (RuntimeException e) {
            System.out.println("Lookup failed: " + e.getMessage());
            System.out.println("Root cause: " + e.getCause());
        }
    }

    static void lookupOrder(String id) {
        try {
            Integer.parseInt(id);
        } catch (NumberFormatException original) {
            throw new RuntimeException("Order lookup failed for id: " + id, original); // cause preserved
        }
    }
}
```

**How to run:** `java OrderLookupIntermediate.java`

Passing `original` as the second constructor argument preserves the full chain — `e.getCause()` now returns the actual `NumberFormatException`, giving a caller (or a log reader) the precise underlying reason the lookup failed, not just a generic message.

### Level 3 — Advanced

```java
public class OrderLookupAdvanced {
    public static void main(String[] args) {
        handleLookup("bad-id");
        handleLookup("404"); // valid number format, but simulates "not found" downstream
    }

    static void handleLookup(String id) {
        try {
            lookupOrder(id);
            System.out.println("Order " + id + " found.");
        } catch (RuntimeException e) {
            if (hasCauseOfType(e, NumberFormatException.class)) {
                System.out.println("Rejecting '" + id + "': malformed order ID.");
            } else {
                System.out.println("Order " + id + " lookup failed for another reason: " + e.getMessage());
                logFullChain(e);
            }
        }
    }

    static void lookupOrder(String id) {
        int numericId;
        try {
            numericId = Integer.parseInt(id);
        } catch (NumberFormatException original) {
            throw new RuntimeException("Order lookup failed for id: " + id, original);
        }
        if (numericId == 404) {
            throw new RuntimeException("Order " + numericId + " does not exist in the system");
        }
    }

    static boolean hasCauseOfType(Throwable t, Class<? extends Throwable> type) {
        while (t != null) {
            if (type.isInstance(t)) return true;
            t = t.getCause();
        }
        return false;
    }

    static void logFullChain(Throwable t) {
        System.out.println("  Full chain:");
        while (t != null) {
            System.out.println("    " + t.getClass().getSimpleName() + ": " + t.getMessage());
            t = t.getCause();
        }
    }
}
```

**How to run:** `java OrderLookupAdvanced.java`

`hasCauseOfType` walks the entire chain checking each exception's actual type against `NumberFormatException`, letting `handleLookup` react differently to "malformed input" (a chain containing a `NumberFormatException`) versus "a different underlying failure" (any other chain), and `logFullChain` prints every layer for full diagnostic detail when the failure isn't the specifically-handled case.

## 6. Walkthrough

Execution starts in `main`, which calls `handleLookup("bad-id")` first.

Inside `handleLookup`, `lookupOrder("bad-id")` attempts `Integer.parseInt("bad-id")`, which throws `NumberFormatException` because `"bad-id"` isn't a valid integer. The `catch` block wraps it: `throw new RuntimeException("Order lookup failed for id: bad-id", original)` — this new `RuntimeException` is thrown up to `handleLookup`'s own `try/catch`.

`handleLookup`'s `catch (RuntimeException e)` runs. `hasCauseOfType(e, NumberFormatException.class)` walks the chain: it first checks `e` itself (a `RuntimeException`, not a `NumberFormatException` — `false`), then `t = t.getCause()` moves to the original `NumberFormatException`, which *is* an instance of `NumberFormatException.class` — returns `true` immediately. So `handleLookup` prints `Rejecting 'bad-id': malformed order ID.` without printing the full chain, since this specific, expected failure mode has its own clear message.

`main` then calls `handleLookup("404")`. This time, `Integer.parseInt("404")` succeeds (returns `404`), so no `NumberFormatException` is thrown at all — but `lookupOrder`'s own logic then checks `if (numericId == 404)` and throws a fresh `RuntimeException("Order 404 does not exist in the system")` with **no** cause argument (this exception has no wrapped underlying exception; it's the original failure itself, not a translation of a lower-level one).

Back in `handleLookup`'s `catch` block, `hasCauseOfType(e, NumberFormatException.class)` walks the chain: `e` itself isn't a `NumberFormatException`, and `e.getCause()` is `null` (since this exception was thrown directly, not wrapping anything), so the `while` loop's `t != null` condition ends the search — the method returns `false`. `handleLookup`'s `else` branch runs: it prints `Order 404 lookup failed for another reason: Order 404 does not exist in the system`, then calls `logFullChain(e)`, which prints just this one exception (`RuntimeException: Order 404 does not exist in the system`), since `getCause()` is `null` and the `while` loop in `logFullChain` exits after the first entry.

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="bad-id produces a chain ending in NumberFormatException, detected and handled specially; 404 produces a standalone exception with no cause, falling through to the generic handler and full chain logging">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#f85149" font-size="10">"bad-id": parseInt throws NumberFormatException -&gt; wrapped as RuntimeException(cause=NFE)</text>
  <text x="20" y="52" fill="#6db33f" font-size="10">  hasCauseOfType(..., NumberFormatException) walks chain -&gt; finds NFE -&gt; true -&gt; specific message</text>
  <text x="20" y="85" fill="#79c0ff" font-size="10">"404": parseInt succeeds -&gt; numericId==404 check throws RuntimeException (NO cause)</text>
  <text x="20" y="107" fill="#f85149" font-size="10">  hasCauseOfType(..., NumberFormatException) walks chain -&gt; getCause() is null -&gt; false -&gt; generic path</text>
  <text x="20" y="129" fill="#8b949e" font-size="10">  logFullChain prints just the one exception, since there is no deeper cause to descend into</text>
</svg>

## 7. Gotchas & takeaways

> Catching an exception and throwing a *different* one without passing the original as the cause (`throw new SomeException("message")` instead of `throw new SomeException("message", original)`) silently discards the real failure information — the resulting stack trace shows only the new exception, with no way to know what actually triggered it underneath.

- Always pass the original exception as the `cause` argument when translating one exception type into another, unless you have a specific, deliberate reason not to.
- `getCause()` returns `null` when there is no wrapped cause — not every exception is part of a chain, and code walking a chain must handle reaching the end.
- A printed stack trace of a chained exception shows the outer exception first, followed by one or more `"Caused by:"` sections for each link in the chain, down to the original root cause.
- Walking `while (t != null) { ...; t = t.getCause(); }` is the standard pattern for inspecting or logging an entire exception chain, whether checking for a specific cause type or printing full diagnostic detail.
- Distinguish an exception with no cause (a genuinely original failure) from one with a cause (a translated/wrapped failure) when deciding how to log or handle it — they represent different situations even though both may be the same outer exception type.
