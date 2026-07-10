---
card: java
gi: 862
slug: final-field-semantics
title: final field semantics
---

## 1. What it is

A `final` field on an object can only be assigned once — normally in the constructor. Beyond that simple rule, the Java Memory Model gives `final` fields a special concurrency guarantee: if an object is **safely published** (its reference isn't leaked to other threads before its constructor finishes), then any other thread that later sees a reference to that object is guaranteed to see the fully initialized values of its `final` fields, without needing any extra synchronization such as `volatile` or `synchronized`. This is called the **final field freeze** — the JVM inserts a memory "freeze" at the end of the constructor so that all `final` field writes become visible to any thread that subsequently reads the object reference.

## 2. Why & when

Without this guarantee, a thread could observe an object in a half-constructed state: the reference might be visible before the constructor's writes to its fields are visible, because normal (non-final, non-volatile) writes can be reordered or cached per-CPU-core. `final` fields close that specific hole for immutable data — configuration objects, value objects like a `Point` or `Money` class, and any object meant to be handed across threads once and never mutated again. Use `final` fields whenever a class represents an immutable value that will be shared between threads; it buys you correctness for free, without locks. It does *not* help if the object itself leaks its own `this` reference during construction (see the "gotcha" below), and it does not make fields that are reassigned or whose *referenced* objects are mutated afterward safe — the guarantee only covers the one-time initialization write.

## 3. Core concept

```java
final class ImmutablePoint {
    final int x;
    final int y;
    ImmutablePoint(int x, int y) {
        this.x = x;
        this.y = y;
        // JVM inserts a "freeze" here, after all final fields are assigned
    }
}
// Once a reference to an ImmutablePoint escapes the constructor safely
// (e.g. returned from a factory, stored in a properly-published field),
// every thread that reads that reference sees x and y fully initialized --
// no torn or half-built object is ever visible, even without volatile/synchronized.
```

The freeze applies only to fields declared `final`; ordinary fields assigned in the same constructor get no such guarantee and can still appear uninitialized to another thread without additional synchronization.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Constructor writes final fields, a freeze barrier is inserted, then the reference is published; another thread reading the reference sees fully initialized final fields">
  <rect x="20" y="30" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="60" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Constructor writes x=3, y=4</text>

  <rect x="230" y="30" width="140" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="300" y="60" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">FREEZE barrier</text>

  <rect x="400" y="30" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Reference published</text>
  <text x="500" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(e.g. stored, returned)</text>

  <line x1="200" y1="55" x2="225" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="370" y1="55" x2="395" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="230" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="150" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Other thread reads x, y</text>
  <text x="320" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">guaranteed: x=3, y=4, never half-built</text>

  <line x1="500" y1="80" x2="330" y2="118" stroke="#79c0ff" stroke-width="2" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The constructor's writes to `final` fields are frozen before the object reference is published, so any thread that later obtains the reference sees fully initialized fields.*

## 5. Runnable example

Scenario: publishing a configuration object across threads without any locking, comparing an unsafe mutable-field version to a safe `final`-field version, then adding a defensively-copied `final` array field for full immutability.

### Level 1 — Basic

```java
public class FinalFieldBasic {
    static class Config {
        final int maxRetries;
        Config(int maxRetries) {
            this.maxRetries = maxRetries;
        }
    }

    static volatile Config sharedConfig; // volatile only to publish the REFERENCE safely

    public static void main(String[] args) throws InterruptedException {
        Thread reader = new Thread(() -> {
            while (sharedConfig == null) { /* wait for publication */ }
            System.out.println("reader sees maxRetries = " + sharedConfig.maxRetries);
        });
        reader.start();

        Thread.sleep(20);
        sharedConfig = new Config(5); // publish after full construction
        reader.join();
    }
}
```

**How to run:** `java FinalFieldBasic.java` (JDK 17+).

Expected output:
```
reader sees maxRetries = 5
```

The `final` field `maxRetries` is guaranteed fully initialized (`5`, never `0` or a torn value) the moment the reader thread observes the `sharedConfig` reference, because the constructor's write to a `final` field is frozen before the reference is published.

### Level 2 — Intermediate

```java
public class FinalFieldMultipleFields {
    static class RetryPolicy {
        final int maxRetries;
        final long backoffMillis;
        final String strategyName;

        RetryPolicy(int maxRetries, long backoffMillis, String strategyName) {
            this.maxRetries = maxRetries;
            this.backoffMillis = backoffMillis;
            this.strategyName = strategyName;
            // all three final fields frozen together at the end of this constructor
        }
    }

    static volatile RetryPolicy policy;

    public static void main(String[] args) throws InterruptedException {
        Runnable consumer = () -> {
            while (policy == null) { Thread.onSpinWait(); }
            System.out.println("policy: " + policy.strategyName
                + ", retries=" + policy.maxRetries + ", backoff=" + policy.backoffMillis + "ms");
        };
        Thread t1 = new Thread(consumer);
        Thread t2 = new Thread(consumer);
        t1.start();
        t2.start();

        policy = new RetryPolicy(3, 250L, "exponential");
        t1.join();
        t2.join();
    }
}
```

**How to run:** `java FinalFieldMultipleFields.java`.

Expected output (order of the two lines may vary):
```
policy: exponential, retries=3, backoff=250ms
policy: exponential, retries=3, backoff=250ms
```

The real-world concern added: multiple `final` fields, and multiple reader threads, all observing the same fully-initialized object simultaneously with no locks on the read side — the freeze guarantee applies to every `final` field written in the constructor, not just one, and to every thread that later reads the reference.

### Level 3 — Advanced

```java
import java.util.Arrays;

public class FinalFieldWithArray {
    static final class ImmutableBatch {
        final int[] values; // final reference, but arrays are still mutable through it!
        final int checksum;

        ImmutableBatch(int[] source) {
            this.values = Arrays.copyOf(source, source.length); // defensive copy -- true immutability
            int sum = 0;
            for (int v : this.values) sum += v;
            this.checksum = sum;
        }
    }

    static volatile ImmutableBatch batch;

    public static void main(String[] args) throws InterruptedException {
        int[] source = {1, 2, 3, 4, 5};

        Thread publisher = new Thread(() -> {
            ImmutableBatch b = new ImmutableBatch(source);
            source[0] = 999; // mutate the ORIGINAL array after construction -- must not affect b
            batch = b; // publish only after construction is fully done
        });

        Thread consumer = new Thread(() -> {
            while (batch == null) { Thread.onSpinWait(); }
            System.out.println("values = " + Arrays.toString(batch.values));
            System.out.println("checksum = " + batch.checksum + " (expected 15, unaffected by later mutation)");
        });

        publisher.start();
        publisher.join();
        consumer.start();
        consumer.join();
    }
}
```

**How to run:** `java FinalFieldWithArray.java`.

Expected output:
```
values = [1, 2, 3, 4, 5]
checksum = 15 (expected 15, unaffected by later mutation)
```

This adds the production-flavored hard case: a `final` field that holds a *reference* to a mutable array. Declaring `values` `final` only freezes the reference itself, not the array's contents — anyone still holding the original `source` array could mutate it after handing it to the constructor. The fix is the defensive copy (`Arrays.copyOf`), which combined with the `final` freeze gives genuine immutability: the object seen by any other thread always has `values = [1,2,3,4,5]` and `checksum = 15`, regardless of what happens to the caller's original array afterward.

## 6. Walkthrough

Tracing `FinalFieldWithArray.main`:

1. The publisher thread's `new ImmutableBatch(source)` call runs the constructor: it defensively copies `source` into `this.values`, then computes `this.checksum` from that copy.
2. At the end of the constructor, the JVM inserts the final-field freeze — both `this.values` and `this.checksum` are now guaranteed visible in their fully-initialized form to any thread that later obtains a reference to this `ImmutableBatch`.
3. Still inside the publisher thread, `source[0] = 999` mutates the *original* array — but since `values` was a defensive copy, this has no effect on the already-frozen `ImmutableBatch`.
4. `batch = b` publishes the reference (via a `volatile` field, so the reference write itself is also visible promptly).
5. The consumer thread's spin-wait loop exits once it observes `batch != null`, and thanks to the final-field freeze, it is guaranteed to see `values = [1,2,3,4,5]` and `checksum = 15` — never a half-built array and never the post-mutation `999`.
6. The two `println` calls confirm both the array contents and the checksum are exactly as computed at construction time.

## 7. Gotchas & takeaways

> **Gotcha:** the final-field freeze is voided if the constructor lets `this` **escape** before it finishes — for example, by registering a listener, starting a thread, or storing `this` into a static field from inside the constructor. Any thread that obtains that leaked `this` reference early can observe fields before they are frozen, `final` or not.

- `final` fields, once safely published, are guaranteed fully initialized to any observing thread — no `volatile` or `synchronized` needed for the fields themselves.
- The reference to the object still needs safe publication (a `volatile` field, a `final` field of another safely-published object, placement in a properly-locked collection, or handoff through a thread-safe queue).
- `final` only freezes the field's own value (or reference); if that value is a reference to a mutable object (like an array or `ArrayList`), the referenced object's contents are not automatically immutable — combine `final` with a defensive copy for true immutability, as in [`ImmutableBatch`](0862-final-field-semantics.md) above.
- Never let `this` escape from inside a constructor (starting threads, registering callbacks, assigning to statics) — it defeats the freeze guarantee for every field, not just the ones touched so far.
- This is one of the cheapest concurrency guarantees in Java: prefer `final` fields for anything meant to be treated as an immutable, cross-thread value.
