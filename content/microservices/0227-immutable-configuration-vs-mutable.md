---
card: microservices
gi: 227
slug: immutable-configuration-vs-mutable
title: "Immutable configuration vs mutable"
---

## 1. What it is

Immutable configuration is a set of values fixed for the entire lifetime of a running process — resolved once at startup and never changed thereafter — whereas mutable configuration can change while the process runs, as with [dynamic runtime refresh](0223-dynamic-runtime-configuration-refresh.md). The choice between the two, for any given setting, is a deliberate design decision, not an incidental one.

## 2. Why & when

Not every setting benefits from being dynamically changeable, and treating all configuration as uniformly mutable introduces risk where it isn't needed: a value that's read once during a resource's initialization (like the pool size used when a connection pool is constructed) can produce inconsistent, hard-to-reason-about behavior if changed mid-flight without the resource being properly reinitialized to match. Immutability, conversely, gives strong guarantees — a value known to be fixed for a process's lifetime can be safely cached, shared across threads without synchronization concerns specific to that value, and reasoned about without worrying it might change underneath a long-running operation.

Make a setting immutable by default, and deliberately promote it to mutable only when there's a real operational need for it to change without a restart — an emergency kill switch, a tunable threshold under live investigation. Treating every setting as mutable "just in case" adds unnecessary complexity (synchronization, staleness handling) to values that never actually needed to change at runtime.

## 3. Core concept

Immutable configuration is captured once into a final field or an unmodifiable structure at startup; mutable configuration lives behind an indirection (a holder, a supplier) that's read fresh on each use — the structural difference between the two mirrors exactly the "static vs. live holder" distinction covered in [dynamic runtime configuration refresh](0223-dynamic-runtime-configuration-refresh.md), but framed here as an explicit design choice made per setting.

```java
class AppConfig {
    final int connectionPoolSize; // IMMUTABLE -- fixed at construction, safe to use anywhere without re-checking
    final AtomicInteger requestTimeoutMs; // MUTABLE -- deliberately allowed to change at runtime

    AppConfig(int poolSize, int initialTimeout) {
        this.connectionPoolSize = poolSize; // captured ONCE, never reassigned
        this.requestTimeoutMs = new AtomicInteger(initialTimeout); // wrapped so it CAN change safely
    }
}
// connectionPoolSize: read anywhere, always the SAME value for this process's life
// requestTimeoutMs.get(): read anywhere, may return a DIFFERENT value across calls
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Immutable configuration is captured once at startup into a final field and stays fixed; mutable configuration lives in an updatable holder that can change while the process runs, and the choice between the two is made deliberately per setting" >
  <rect x="20" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Immutable: final field</text>
  <text x="155" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fixed for the process's lifetime</text>

  <rect x="350" y="20" width="270" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Mutable: live holder</text>
  <text x="485" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">can change while running</text>

  <rect x="180" y="115" width="280" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="139" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Choose per setting, deliberately</text>

  <line x1="155" y1="75" x2="280" y2="113" stroke="#8b949e" marker-end="url(#arr227)"/>
  <line x1="485" y1="75" x2="360" y2="113" stroke="#8b949e" marker-end="url(#arr227)"/>

  <defs>
    <marker id="arr227" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each setting is deliberately assigned to one category or the other based on whether runtime change is actually needed and safe.

## 5. Runnable example

Scenario: a connection-pool-backed service where treating the pool size as mutable causes an inconsistency (the pool's actual capacity silently diverges from the "configured" size), refactored to correctly split settings into an immutable pool size (fixed at construction) and a genuinely mutable request timeout (safe to change live), and finally demonstrating why the immutable setting's safety guarantee holds even under concurrent access, unlike the mutable one.

### Level 1 — Basic

```java
// File: WronglyMutablePoolSize.java -- treating pool size as mutable
// creates an INCONSISTENCY: the "configured" size no longer matches
// the pool's ACTUAL capacity, since the pool was already built.
import java.util.*;

public class WronglyMutablePoolSize {
    static class ConnectionPool {
        List<String> connections;
        ConnectionPool(int size) {
            connections = new ArrayList<>();
            for (int i = 0; i < size; i++) connections.add("conn-" + i); // capacity fixed HERE, at construction
        }
    }

    static int configuredPoolSize = 5; // WRONGLY treated as if changing this changes anything live

    public static void main(String[] args) {
        ConnectionPool pool = new ConnectionPool(configuredPoolSize); // built with size 5
        System.out.println("Pool actually has " + pool.connections.size() + " connections");

        configuredPoolSize = 20; // "updating" the config -- but the POOL OBJECT never gets rebuilt
        System.out.println("Configured size now says: " + configuredPoolSize);
        System.out.println("But pool ACTUALLY still has: " + pool.connections.size() + " connections -- INCONSISTENT!");
    }
}
```

**How to run:** `javac WronglyMutablePoolSize.java && java WronglyMutablePoolSize` (JDK 17+).

Expected output:
```
Pool actually has 5 connections
Configured size now says: 20
But pool ACTUALLY still has: 5 connections -- INCONSISTENT!
```

### Level 2 — Intermediate

```java
// File: CorrectlySplitImmutableMutable.java -- pool size is now GENUINELY
// immutable (captured once, no field pretends it can change); the
// request timeout, which really CAN change safely, is mutable instead.
import java.util.*;
import java.util.concurrent.atomic.*;

public class CorrectlySplitImmutableMutable {
    static class AppConfig {
        final int connectionPoolSize; // IMMUTABLE -- no setter, no way to change after construction
        final AtomicInteger requestTimeoutMs; // MUTABLE -- deliberately, via an updatable holder

        AppConfig(int poolSize, int initialTimeout) {
            this.connectionPoolSize = poolSize;
            this.requestTimeoutMs = new AtomicInteger(initialTimeout);
        }
    }

    static class ConnectionPool {
        List<String> connections;
        ConnectionPool(int size) {
            connections = new ArrayList<>();
            for (int i = 0; i < size; i++) connections.add("conn-" + i);
        }
    }

    public static void main(String[] args) {
        AppConfig config = new AppConfig(5, 3000);
        ConnectionPool pool = new ConnectionPool(config.connectionPoolSize); // built ONCE, from the immutable value

        System.out.println("Pool size: " + pool.connections.size() + " (matches config.connectionPoolSize: " + config.connectionPoolSize + ")");
        System.out.println("Request timeout: " + config.requestTimeoutMs.get());

        config.requestTimeoutMs.set(8000); // SAFE to change -- nothing else depends on it staying fixed
        System.out.println("Request timeout after live update: " + config.requestTimeoutMs.get());
        System.out.println("Pool size STILL correctly reads: " + pool.connections.size() + " -- because it was NEVER treated as mutable.");
    }
}
```

**How to run:** `javac CorrectlySplitImmutableMutable.java && java CorrectlySplitImmutableMutable` (JDK 17+).

Expected output:
```
Pool size: 5 (matches config.connectionPoolSize: 5)
Request timeout: 3000
Request timeout after live update: 8000
Pool size STILL correctly reads: 5 -- because it was NEVER treated as mutable.
```

### Level 3 — Advanced

```java
// File: ImmutabilitySafeUnderConcurrency.java -- demonstrates that the
// IMMUTABLE field needs NO synchronization to read safely from many
// threads, while the MUTABLE field's correctness depends on using a
// thread-safe holder (AtomicInteger) specifically because it CAN change.
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class ImmutabilitySafeUnderConcurrency {
    static class AppConfig {
        final int connectionPoolSize; // IMMUTABLE -- safe to read from any thread, no synchronization needed
        final AtomicInteger requestTimeoutMs; // MUTABLE -- REQUIRES a thread-safe holder to stay correct

        AppConfig(int poolSize, int initialTimeout) {
            this.connectionPoolSize = poolSize;
            this.requestTimeoutMs = new AtomicInteger(initialTimeout);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        AppConfig config = new AppConfig(5, 3000);
        ExecutorService pool = Executors.newFixedThreadPool(4);
        Set<Integer> poolSizeReadings = ConcurrentHashMap.newKeySet();

        // 4 threads read connectionPoolSize CONCURRENTLY, with no locking, while ANOTHER thread updates the timeout
        for (int i = 0; i < 4; i++) {
            pool.submit(() -> { for (int j = 0; j < 1000; j++) poolSizeReadings.add(config.connectionPoolSize); });
        }
        pool.submit(() -> { for (int j = 0; j < 1000; j++) config.requestTimeoutMs.set(3000 + j); }); // concurrent WRITES

        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);

        System.out.println("Distinct pool size values ever observed across all threads: " + poolSizeReadings);
        System.out.println("(always exactly {5} -- immutability guarantees this with ZERO synchronization code)");
        System.out.println("Final request timeout after concurrent updates: " + config.requestTimeoutMs.get());
    }
}
```

**How to run:** `javac ImmutabilitySafeUnderConcurrency.java && java ImmutabilitySafeUnderConcurrency` (JDK 17+).

Expected output:
```
Distinct pool size values ever observed across all threads: [5]
(always exactly {5} -- immutability guarantees this with ZERO synchronization code)
Final request timeout after concurrent updates: 3999
```

## 6. Walkthrough

1. **Level 1, the inconsistency** — `ConnectionPool`'s constructor fixes `connections`' size permanently at construction time, but `configuredPoolSize` is a separate, independently mutable field that gives the false impression changing it affects the already-built pool; after `configuredPoolSize = 20`, the pool's actual `connections.size()` remains `5`, an inconsistency caused by treating a structurally immutable concern (the pool's built capacity) as if it were mutable configuration.
2. **Level 2, an honest immutable field** — `AppConfig.connectionPoolSize` is declared `final` and set only in the constructor, with no method anywhere that could reassign it; `ConnectionPool` is built directly from this value, so there is no possibility of the earlier inconsistency — the field's immutability is enforced by the language, not just by convention.
3. **Level 2, an honest mutable field** — `requestTimeoutMs` is wrapped in `AtomicInteger`, a container specifically designed to be updated safely; calling `config.requestTimeoutMs.set(8000)` is a deliberate, supported operation, unlike Level 1's `configuredPoolSize` reassignment, which looked similar but was actually meaningless because nothing downstream re-read it.
4. **Level 2, the pool size staying correct** — after updating the timeout, `pool.connections.size()` is printed again and still correctly shows `5`, because `connectionPoolSize`'s immutability was never violated — there's no field anywhere claiming the pool's size can change after construction.
5. **Level 3, immutability's concurrency guarantee** — four threads read `config.connectionPoolSize` one thousand times each, entirely without locks, while a fifth thread concurrently updates `requestTimeoutMs`; because `connectionPoolSize` is `final` and its value was fully established before any thread could observe it (guaranteed by Java's memory model for final fields set during construction), every single read across all four threads observes the identical value `5`, with zero synchronization code needed to guarantee that.
6. **Level 3, why the mutable field needed a special container** — `requestTimeoutMs` is deliberately wrapped in `AtomicInteger` rather than a plain `int` field specifically because it's mutable and read/written from multiple threads; a plain, non-atomic `int` field being concurrently written from one thread and read from others would risk visibility and tearing issues that `AtomicInteger` is specifically designed to prevent — this is the extra cost mutability incurs, in direct contrast to `connectionPoolSize`'s zero-overhead safety, and it's precisely why settings should be immutable by default and promoted to mutable only when there's a genuine need.

## 7. Gotchas & takeaways

> **Gotcha:** a field that's technically mutable in code (not `final`, reassignable) but is never actually intended to change after startup is a trap — as Level 1 shows, something downstream may have already "baked in" the original value (like a pool built from it), so later reassigning the field silently produces an inconsistency rather than a clean update; if a setting isn't genuinely meant to change at runtime, make it `final` and structurally impossible to reassign, don't just avoid reassigning it by convention.

- Immutable configuration is captured once and fixed for a process's entire lifetime; mutable configuration lives behind an updatable holder and can change while the process runs.
- The choice between the two should be deliberate per setting, not a blanket default — values something else has already "baked in" (like a resource's initial sizing) are dangerous to treat as mutable.
- Genuinely immutable settings need no synchronization to read safely from multiple threads, a guarantee Java's memory model provides for properly constructed `final` fields.
- Genuinely mutable settings need a thread-safe container (like `AtomicInteger` or a `volatile` field) specifically because concurrent reads and writes are expected.
- Default to immutability, and promote a setting to mutable only when there's a real, specific operational need for it to change without a restart — unnecessary mutability adds complexity without benefit.
