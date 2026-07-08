---
card: java
gi: 438
slug: autocloseable-closeable-interfaces
title: AutoCloseable / Closeable interfaces
---

## 1. What it is

`AutoCloseable`, added in Java 7, is the interface that makes an object eligible for try-with-resources (the previous tutorial): implement `close()` (which may throw any `Exception`) and the object can be declared in a `try(...)` statement. `Closeable` (which predates Java 7, from `java.io`) was retrofitted in Java 7 to **extend** `AutoCloseable`, narrowing its `close()` method to only throw `IOException` specifically, and — per its documented contract — recommending that `close()` be safe to call more than once (idempotent).

## 2. Why & when

`AutoCloseable` is deliberately the broadest possible contract: `close() throws Exception` accommodates *any* kind of resource, including ones whose cleanup can genuinely fail with a checked exception unrelated to I/O (a database transaction rollback failing, say). `Closeable`, being older and I/O-specific, has the narrower, more precise contract that most file- and stream-like resources actually have: cleanup can only fail with `IOException`. This distinction matters for callers: code that only ever deals with `Closeable` resources can catch `IOException` specifically, rather than being forced to catch the broader `Exception` (and potentially swallow unrelated runtime errors it didn't mean to catch).

You implement `AutoCloseable` directly for a custom resource whose cleanup might throw something other than `IOException` (or nothing checked at all); you implement `Closeable` specifically when your resource is I/O-like and you want callers to be able to rely on catching exactly `IOException`. Additionally, `Closeable`'s documented contract recommends `close()` be idempotent — safe to call multiple times without ill effect — a discipline worth following even for your own `AutoCloseable` implementations, since real-world code sometimes ends up calling `close()` more than once (a bug in calling code, or overlapping cleanup paths).

## 3. Core concept

```java
import java.io.*;

// AutoCloseable: the broadest contract -- close() may throw ANY Exception
class Transaction implements AutoCloseable {
    @Override
    public void close() throws Exception { /* ... */ }
}

// Closeable: extends AutoCloseable, but NARROWS close() to only throw IOException
class SimpleFile implements Closeable {
    @Override
    public void close() throws IOException { /* ... */ }
}
```

Every `Closeable` **is** an `AutoCloseable` (since it extends it), but not every `AutoCloseable` is a `Closeable` — the relationship is one-directional, matching the fact that `Closeable`'s contract is strictly narrower and more specific.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Closeable extends AutoCloseable, narrowing close() to throw only IOException instead of any Exception; every Closeable is also an AutoCloseable, but not the reverse">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="180" y="30" width="280" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">AutoCloseable: close() throws Exception</text>

  <rect x="220" y="100" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="320" y="125" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Closeable: close() throws IOException</text>

  <line x1="320" y1="70" x2="320" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(acl1)"/>
  <text x="320" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends, narrows</text>
  <defs><marker id="acl1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Closeable` is a stricter, I/O-specific specialization of the more general `AutoCloseable` contract.

## 5. Runnable example

Scenario: a resource cleanup helper distinguishing broad and narrow resource types — the same idea, evolved from defining both an `AutoCloseable` and a `Closeable` resource side by side, through a helper method that leverages `Closeable`'s narrower contract to catch `IOException` precisely, to demonstrating why `close()` idempotency matters in practice.

### Level 1 — Basic

```java
import java.io.*;

public class CloseableBasic {
    // AutoCloseable: close() may throw ANY Exception (the broadest possible contract)
    static class Transaction implements AutoCloseable {
        @Override
        public void close() throws Exception {
            System.out.println("Transaction rolled back / committed");
        }
    }

    // Closeable: extends AutoCloseable, but NARROWS close() to only throw IOException
    static class SimpleFile implements Closeable {
        @Override
        public void close() throws IOException {
            System.out.println("File handle released");
        }
    }

    public static void main(String[] args) throws Exception {
        try (Transaction tx = new Transaction()) {
            System.out.println("Doing work inside transaction");
        }
        try (SimpleFile file = new SimpleFile()) {
            System.out.println("Doing work with file");
        }
    }
}
```

**How to run:** `java CloseableBasic.java`

Both resource types work identically inside try-with-resources — `Closeable` being a stricter `AutoCloseable` doesn't change how it's *used*, only what callers can assume about how its `close()` might fail.

### Level 2 — Intermediate

```java
import java.io.*;
import java.util.*;

public class CloseableCatchPrecision {
    static class SimpleFile implements Closeable {
        private final String name;
        SimpleFile(String name) { this.name = name; }
        @Override
        public void close() throws IOException {
            throw new IOException("disk error closing " + name);
        }
    }

    // Because the parameter type is Closeable, callers know EXACTLY which checked
    // exception close() can throw -- IOException -- and can catch it specifically.
    static void releaseAll(List<Closeable> resources) {
        for (Closeable resource : resources) {
            try {
                resource.close();
            } catch (IOException e) { // precise catch -- only possible because of Closeable's narrower contract
                System.out.println("Failed to close: " + e.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        releaseAll(List.of(new SimpleFile("a.txt"), new SimpleFile("b.txt")));
    }
}
```

**How to run:** `java CloseableCatchPrecision.java`

Because `releaseAll` accepts `List<Closeable>` rather than `List<AutoCloseable>`, the `catch (IOException e)` block is guaranteed to catch everything `close()` could possibly throw — if the parameter type were `AutoCloseable` instead, this method would need `catch (Exception e)` (or to declare `throws Exception` itself), losing that precision.

### Level 3 — Advanced

```java
import java.io.*;

public class CloseableIdempotency {
    // Closeable's contract RECOMMENDS close() be idempotent -- safe to call more than once.
    static class IdempotentFile implements Closeable {
        private boolean closed = false;
        @Override
        public void close() throws IOException {
            if (closed) {
                System.out.println("close() called again -- already closed, doing nothing");
                return;
            }
            closed = true;
            System.out.println("Actually releasing the file handle now");
        }
    }

    // A naive AutoCloseable with NO such guard -- double-closing causes a real problem
    static class FragileConnection implements AutoCloseable {
        private int openConnections = 1;
        @Override
        public void close() {
            openConnections--; // no guard against being called twice
            System.out.println("Connection count after close(): " + openConnections);
        }
    }

    public static void main(String[] args) throws Exception {
        IdempotentFile file = new IdempotentFile();
        file.close();
        file.close(); // safe -- does nothing the second time

        System.out.println();

        FragileConnection conn = new FragileConnection();
        conn.close();
        conn.close(); // BUG: decrements past what's meaningful, since there's no idempotency guard
    }
}
```

**How to run:** `java CloseableIdempotency.java`

`IdempotentFile` follows `Closeable`'s recommended contract with a `closed` flag guard — calling `close()` twice is harmless. `FragileConnection`, a naive `AutoCloseable` with no such guard, quietly produces a nonsensical negative connection count on the second call — a real bug that a discipline of idempotent `close()` methods would have prevented.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `file` is a fresh `IdempotentFile` with `closed = false`.

`file.close()` (first call): `closed` is `false`, so the `if` branch is skipped. `closed` is set to `true`, and `"Actually releasing the file handle now"` is printed — the real cleanup work happens here, exactly once.

`file.close()` (second call): `closed` is now `true`, so the `if` branch runs: `"close() called again -- already closed, doing nothing"` is printed, and the method returns immediately without re-running any cleanup logic. This is `Closeable`'s recommended idempotent behavior in action — calling `close()` an extra time is completely harmless.

`conn` is a fresh `FragileConnection` with `openConnections = 1`. `conn.close()` (first call): `openConnections--` makes it `0`, printed as `"Connection count after close(): 0"` — this looks correct, representing "the one open connection is now closed."

`conn.close()` (second call): there's no guard checking whether it was already closed, so `openConnections--` runs again unconditionally, making it `-1` — printed as `"Connection count after close(): -1"`. A negative connection count is meaningless and signals a real bug: without an idempotency guard, calling `close()` more than once (perhaps due to overlapping cleanup code paths elsewhere in a larger application) silently corrupts this object's internal state.

Expected output:
```
Actually releasing the file handle now
close() called again -- already closed, doing nothing

Connection count after close(): 0
Connection count after close(): -1
```

## 7. Gotchas & takeaways

> `AutoCloseable`'s own documentation explicitly notes that implementations are **not required** to be idempotent, unlike `Closeable`, whose documentation **recommends** idempotency. Don't assume every `AutoCloseable` you didn't write yourself is safe to `close()` more than once — check its documentation or source, and when writing your own, prefer the idempotent, guarded pattern (`IdempotentFile` above) regardless of which interface you implement, since it costs almost nothing and prevents an entire category of double-close bugs.

- `AutoCloseable.close()` may throw any `Exception`; `Closeable.close()` (which extends `AutoCloseable`) narrows this to only `IOException`.
- Every `Closeable` is an `AutoCloseable`, but not every `AutoCloseable` is a `Closeable` — the relationship is one-directional, matching the fact that `Closeable`'s contract is a strict subset.
- Accepting `Closeable` (rather than `AutoCloseable`) in a method signature lets callers catch `IOException` specifically, rather than the broader `Exception` — a meaningful precision gain for I/O-heavy code.
- `Closeable`'s documented contract recommends idempotent `close()` methods (safe to call more than once); `AutoCloseable`'s does not require this, so don't assume it without checking.
- Implementing your own resources with an idempotency guard (a simple `boolean closed` flag) is a cheap, worthwhile discipline regardless of which interface you're implementing, since it prevents subtle bugs from an accidental double-close.
