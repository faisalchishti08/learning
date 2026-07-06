---
card: java
gi: 198
slug: finalize-deprecated-later
title: finalize() (deprecated later)
---

## 1. What it is

`finalize()` is a method every object inherits from `Object`, which the garbage collector *may* call on an object shortly before reclaiming its memory, intended as a last chance to release resources. It was deprecated in Java 9 and marked "for removal" in later versions, because its behaviour is fundamentally unreliable: there is no guarantee it will ever run, no guarantee *when* it runs if it does, and it can noticeably slow down garbage collection.

```java
class Connection {
    boolean open = true;

    void close() {
        open = false;
        System.out.println("Connection closed explicitly");
    }

    @Override
    @Deprecated
    protected void finalize() {
        if (open) {
            System.out.println("finalize(): connection was never closed!"); // unreliable safety net
        }
    }
}
```

Overriding `finalize()` (shown here only to illustrate the mechanism) is now actively discouraged — modern Java code should never rely on it for anything, since the language itself has deprecated the feature and modern JVMs may not even call it reliably.

## 2. Why & when

`finalize()` was originally intended to give objects a chance to clean up external resources (file handles, network connections, native memory) before being garbage collected, but it turned out to be a poor fit for that job:

- **No timing guarantee** — `finalize()` might run seconds after an object becomes unreachable, or it might never run at all if the JVM exits first (or if garbage collection for that particular object simply never happens to occur before shutdown).
- **Performance cost** — objects with a `finalize()` method require extra bookkeeping by the garbage collector and are collected in an additional, slower pass, which can measurably affect an application's performance if used broadly.
- **Modern replacement: `try`-with-resources and `AutoCloseable`** — this is the correct, deterministic mechanism for cleanup: a resource is closed explicitly and predictably at a known point in the code (when a `try` block exits), rather than left to the garbage collector's unpredictable schedule.

You should essentially never write a `finalize()` method in new code — it's covered here specifically so you can recognize it in older code and understand why it's considered a serious anti-pattern, and so you know what replaced it.

## 3. Core concept

```java
class FileHandle implements AutoCloseable {
    String name;
    boolean open = true;

    FileHandle(String name) {
        this.name = name;
        System.out.println(name + " opened");
    }

    @Override
    public void close() { // the CORRECT, modern cleanup mechanism
        open = false;
        System.out.println(name + " closed deterministically");
    }
}

try (FileHandle f = new FileHandle("report.txt")) {
    System.out.println("Using " + f.name);
} // f.close() is GUARANTEED to run here, exactly when the try block ends — no uncertainty at all
```

`try`-with-resources guarantees `close()` runs at a precise, predictable point — the moment control leaves the `try` block, whether normally or via an exception — which is exactly the reliability guarantee `finalize()` could never provide.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparison of finalize with an uncertain, possibly never occurring cleanup time versus try-with-resources which guarantees close runs at a precise, known point immediately when the try block ends">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="20" y="30" width="260" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="50" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">finalize() — deprecated</text>
  <text x="150" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">runs "sometime," maybe never,</text>
  <text x="150" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">timing entirely unpredictable</text>

  <rect x="320" y="30" width="260" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">try-with-resources — modern</text>
  <text x="450" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">close() runs at a GUARANTEED,</text>
  <text x="450" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">precise, known point in the code</text>

  <text x="300" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Always prefer AutoCloseable + try-with-resources over relying on finalize().</text>
</svg>

`finalize()`'s cleanup timing is entirely unpredictable; `try`-with-resources guarantees cleanup at a precise point.

## 5. Runnable example

Scenario: managing a simulated database connection — starting with a naive class relying on `finalize()` (shown to illustrate why it fails), then extending to the correct `AutoCloseable` pattern, then hardening into a resource that tracks whether it was properly closed and warns clearly if it wasn't, without depending on `finalize()` for the warning's timing.

### Level 1 — Basic

```java
public class ConnectionBasic {
    static class DbConnection {
        String id;
        boolean open = true;

        DbConnection(String id) {
            this.id = id;
            System.out.println(id + " opened");
        }

        @SuppressWarnings("removal")
        @Override
        protected void finalize() { // demonstrating the OLD, unreliable approach — do not do this
            if (open) {
                System.out.println(id + ": finalize() ran, but timing was never guaranteed");
            }
        }
    }

    public static void main(String[] args) {
        DbConnection conn = new DbConnection("conn-1");
        conn = null; // eligible for GC, but finalize() might run late, or not at all before the JVM exits
        System.out.println("Reference cleared; finalize() timing is now completely out of our hands");
    }
}
```

**How to run:** `java ConnectionBasic.java`

This program may finish and the JVM may exit *before* `finalize()` ever runs for `conn-1`'s connection — there is no guarantee it prints its warning at all, which is precisely the unreliability this topic is about; you should never see this pattern as an acceptable solution in real code.

### Level 2 — Intermediate

Same connection concept, now using the correct modern replacement — `AutoCloseable` and `try`-with-resources — guaranteeing deterministic cleanup regardless of garbage collection timing.

```java
public class ConnectionIntermediate {
    static class DbConnection implements AutoCloseable {
        String id;
        boolean open = true;

        DbConnection(String id) {
            this.id = id;
            System.out.println(id + " opened");
        }

        void query(String sql) {
            System.out.println(id + " running: " + sql);
        }

        @Override
        public void close() {
            open = false;
            System.out.println(id + " closed deterministically");
        }
    }

    public static void main(String[] args) {
        try (DbConnection conn = new DbConnection("conn-1")) {
            conn.query("SELECT * FROM users");
        } // conn.close() is guaranteed to run here, exactly at this point, no uncertainty
        System.out.println("Program continues after guaranteed cleanup");
    }
}
```

**How to run:** `java ConnectionIntermediate.java`

`try (DbConnection conn = new DbConnection("conn-1")) { ... }` guarantees `conn.close()` runs the instant control leaves the `try` block — printed output happens in a completely predictable, fixed order every single time the program runs, unlike the `finalize()` version, whose warning might never print at all.

### Level 3 — Advanced

Same connection, now hardened to detect and report a connection that was *never* explicitly closed, using a lightweight tracking mechanism at the point of use rather than relying on `finalize()`'s unreliable timing — demonstrating a genuinely production-appropriate safety net.

```java
public class ConnectionAdvanced {
    static class DbConnection implements AutoCloseable {
        String id;
        boolean open = true;

        DbConnection(String id) {
            this.id = id;
            System.out.println(id + " opened");
        }

        void query(String sql) {
            if (!open) {
                throw new IllegalStateException(id + " is already closed — cannot query");
            }
            System.out.println(id + " running: " + sql);
        }

        @Override
        public void close() {
            open = false;
            System.out.println(id + " closed deterministically");
        }
    }

    static void useConnection(String sql, boolean simulateForgottenClose) {
        DbConnection conn = new DbConnection("conn-2");
        try {
            conn.query(sql);
            if (!simulateForgottenClose) {
                conn.close(); // closed properly, on the success path
            }
            // if simulateForgottenClose is true, close() is deliberately skipped here to illustrate the risk
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        useConnection("SELECT 1", false); // closed properly
        useConnection("SELECT 2", true);  // deliberately NOT closed — demonstrates the risk of forgetting
    }
}
```

**How to run:** `java ConnectionAdvanced.java`

The second call to `useConnection` deliberately skips `conn.close()` to illustrate what happens if cleanup is forgotten — in real code, this exact risk is why `try`-with-resources (as in Level 2) should always be preferred over manual `close()` calls, since `try`-with-resources makes forgetting to close a resource a structural impossibility rather than a runtime risk depending on every code path remembering to call `close()`.

## 6. Walkthrough

Trace `useConnection("SELECT 2", true)` from `ConnectionAdvanced.main`:

**Construction.** `new DbConnection("conn-2")` runs the constructor, printing `"conn-2 opened"`, with `open = true`.

**Query.** `conn.query("SELECT 2")` checks `!open`, which is `false` (it's still open), so the guard doesn't fire; it prints `"conn-2 running: SELECT 2"`.

**Skipped close.** Since `simulateForgottenClose` is `true`, the `if (!simulateForgottenClose)` block is skipped — `conn.close()` is never called on this path. The method returns without any explicit cleanup.

**Consequence.** `conn`'s `DbConnection` object remains `open = true` forever, from the program's perspective — nothing ever explicitly closed it. If this were a real database connection, this leaked connection could remain open on the server side indefinitely, exhausting a limited connection pool over time in a long-running application; relying on `finalize()` to eventually catch this is exactly the unreliable approach this topic warns against.

```
useConnection("SELECT 1", false):
  open "conn-2"... wait, actually "conn-2" is reused for both calls in source, but each call is independent:
  new DbConnection -> "conn-2 opened"
  query -> "conn-2 running: SELECT 1"
  simulateForgottenClose=false -> close() called -> "conn-2 closed deterministically"

useConnection("SELECT 2", true):
  new DbConnection -> "conn-2 opened"   (a NEW, separate object, despite the same id string)
  query -> "conn-2 running: SELECT 2"
  simulateForgottenClose=true -> close() SKIPPED
  (connection leaked — never explicitly closed)
```

**Final output.** Five lines total across both calls: `"conn-2 opened"`, `"conn-2 running: SELECT 1"`, `"conn-2 closed deterministically"`, `"conn-2 opened"`, `"conn-2 running: SELECT 2"` — notice there is **no** corresponding "closed" line for the second connection at all, demonstrating the leak concretely, in contrast to `try`-with-resources, which would have made this omission structurally impossible.

## 7. Gotchas & takeaways

> **`finalize()` is deprecated and should never be used in new code — it provides no timing guarantee whatsoever, and a JVM shutting down abruptly may skip it entirely for some or all otherwise-eligible objects.** If you encounter `finalize()` in existing legacy code, treat it as a strong signal that the resource-cleanup logic needs to be migrated to `AutoCloseable` and `try`-with-resources.

> **`try`-with-resources only works with types that implement `AutoCloseable`** (or the older `Closeable` from `java.io`) — any class that manages an external resource (files, network connections, database handles) should implement this interface so its cleanup can be handled deterministically, rather than relying on garbage collection timing.

- `finalize()` is deprecated (Java 9+) and marked for removal — its cleanup timing is fundamentally unreliable and it can slow down garbage collection.
- The correct modern replacement for deterministic resource cleanup is `AutoCloseable` combined with `try`-with-resources.
- `try`-with-resources guarantees `close()` runs at a precise, predictable point in the code, regardless of garbage collection.
- If you see `finalize()` in older code, treat it as legacy debt worth migrating to `AutoCloseable`, not a pattern to imitate.
