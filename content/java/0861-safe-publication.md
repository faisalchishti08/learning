---
card: java
gi: 861
slug: safe-publication
title: Safe publication
---

## 1. What it is

**Safe publication** is the guarantee that when one thread constructs an object and makes a reference to it available to other threads, those other threads see the object in a **fully and correctly constructed state** — not a partially-initialized one. Without safe publication, a subtle and specific hazard exists: because constructors can, in principle, have their internal field-assignment steps reordered by the compiler/JIT relative to the point where the constructed reference becomes visible to another thread, another thread could theoretically observe a reference to the new object *before* all of its fields have actually been assigned — seeing default values (`0`, `null`, `false`) for fields the constructor was still in the process of setting. The JMM guarantees safe publication automatically for objects whose fields are all `final` (a special rule specifically carved out for this purpose), and it can also be achieved by publishing the reference itself through a `volatile` field, through proper `synchronized` blocks, or through a thread-safe concurrent collection.

## 2. Why & when

This risk is easy to dismiss as too obscure to matter, but it's a real, JMM-documented hazard, distinct from (and easy to conflate with) plain data races on a field's *value* — this is specifically about whether the *constructed object itself* is safely visible in a fully-initialized state to another thread that only just received a reference to it. Understanding safe publication matters whenever an object is constructed on one thread and handed off to another — a background thread building a configuration object that the main thread will later read, a factory method returning a new object stored into a field other threads access. The reliable fixes are: make every field of the published type `final` (the JLS special-cases this to guarantee safe publication even through an otherwise-unsynchronized plain reference), publish the reference through a `volatile` field or an `AtomicReference`, publish it while holding a lock that the receiving thread also acquires before reading, or store it in a properly thread-safe collection.

## 3. Core concept

```java
// RISKY: a mutable object published through a plain (non-volatile) static field.
class Config {
    int timeout; // NOT final -- mutable
    Config(int timeout) { this.timeout = timeout; }
}
static Config sharedConfig; // plain field
void publisher() { sharedConfig = new Config(30); } // publishing a reference with NO safety guarantee
void reader() { if (sharedConfig != null) System.out.println(sharedConfig.timeout); } // MIGHT see 0, in principle

// SAFE: every field is final -- the JLS guarantees safe publication even through a plain reference.
class ImmutableConfig {
    final int timeout; // final -- special JMM guarantee applies
    ImmutableConfig(int timeout) { this.timeout = timeout; }
}
static ImmutableConfig sharedImmutableConfig; // still a plain field, but SAFE because ImmutableConfig is all-final
void publisher() { sharedImmutableConfig = new ImmutableConfig(30); }
void reader() { if (sharedImmutableConfig != null) System.out.println(sharedImmutableConfig.timeout); } // GUARANTEED to see 30, never 0
```

The difference between the risky and safe versions isn't in how the reference is published — both use a plain static field — it's entirely in whether the published object's fields are `final`, which is the specific condition the JLS attaches its safe-publication guarantee to.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An object with all final fields is guaranteed safely published even through a plain reference; a mutable object needs volatile, synchronized, or a concurrent collection to guarantee safe publication">
  <rect x="30" y="30" width="270" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="165" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">all fields FINAL</text>
  <text x="165" y="75" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">safe even through a plain reference</text>

  <rect x="340" y="30" width="270" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">mutable (non-final) fields</text>
  <text x="475" y="75" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">needs volatile/synchronized/concurrent collection</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">The JLS specifically guarantees safe publication for all-final-field objects, published however they like</text>
</svg>

*`final` fields carry their own JMM safe-publication guarantee; mutable fields need an explicit publication mechanism instead.*

## 5. Runnable example

Scenario: publishing a configuration object from a background initialization thread to be read by other threads, growing from an unsafely-published mutable object, through fixing it with `volatile`, to the alternative fix of making the type immutable and relying on the JLS's final-field guarantee directly.

### Level 1 — Basic

```java
public class UnsafePublicationRisk {
    static class MutableConfig {
        int timeout; // NOT final
        MutableConfig(int timeout) { this.timeout = timeout; }
    }

    static MutableConfig sharedConfig; // plain field -- no safe-publication guarantee

    public static void main(String[] args) throws InterruptedException {
        Thread publisher = new Thread(() -> {
            sharedConfig = new MutableConfig(30); // publishing WITHOUT any safety mechanism
        });
        publisher.start();
        publisher.join(); // NOTE: join() DOES establish a happens-before edge, making THIS specific
                           // example safe in practice -- see Level 2 for the version without it.

        System.out.println("timeout (safe here, because of join()): " + sharedConfig.timeout);
    }
}
```

**How to run:** `java UnsafePublicationRisk.java` (JDK 17+).

Expected output:
```
timeout (safe here, because of join()): 30
```

This particular example happens to be safe, purely because `join()` establishes a happens-before edge covering everything `publisher` did — including the construction and assignment of `sharedConfig`. The next level removes that accidental safety net to expose the genuine underlying risk more directly.

### Level 2 — Intermediate

```java
public class FixedWithVolatile {
    static class MutableConfig {
        int timeout;
        MutableConfig(int timeout) { this.timeout = timeout; }
    }

    static volatile MutableConfig sharedConfig; // volatile reference -- publishes safely

    public static void main(String[] args) throws InterruptedException {
        Thread publisher = new Thread(() -> {
            sharedConfig = new MutableConfig(30); // the volatile WRITE of the reference itself
        });

        Thread reader = new Thread(() -> {
            MutableConfig config;
            while ((config = sharedConfig) == null) { } // volatile READ, busy-waiting for publication
            System.out.println("timeout, safely published via volatile: " + config.timeout);
        });

        reader.start();
        publisher.start();
        publisher.join();
        reader.join();
    }
}
```

**How to run:** `java FixedWithVolatile.java`.

Expected output:
```
timeout, safely published via volatile: 30
```

The real-world concern added: `sharedConfig` is now `volatile`, so the write that publishes the fully-constructed `MutableConfig` reference happens-before any subsequent volatile read of that same field — the reader thread is guaranteed to see `config.timeout` as `30`, never `0`, once it observes a non-`null` reference, because the `volatile` write/read pair on the reference itself carries the full visibility guarantee for everything the constructor set up before that reference was published.

### Level 3 — Advanced

```java
public class FinalFieldGuarantee {
    static final class ImmutableConfig {
        final int timeout; // FINAL -- the JLS's special safe-publication guarantee applies
        final String environment;

        ImmutableConfig(int timeout, String environment) {
            this.timeout = timeout;
            this.environment = environment;
        }
    }

    static ImmutableConfig sharedConfig; // deliberately PLAIN, non-volatile field this time

    public static void main(String[] args) throws InterruptedException {
        Thread publisher = new Thread(() -> {
            sharedConfig = new ImmutableConfig(30, "production"); // published through a PLAIN reference
        });

        Thread reader = new Thread(() -> {
            ImmutableConfig config;
            while ((config = sharedConfig) == null) { } // busy-wait, reading a PLAIN field
            // Despite "sharedConfig" being a plain, non-volatile field, the JLS guarantees
            // config.timeout and config.environment are FULLY visible here, because EVERY
            // field of ImmutableConfig is final.
            System.out.println("timeout: " + config.timeout + ", environment: " + config.environment);
        });

        reader.start();
        publisher.start();
        publisher.join();
        reader.join();
    }
}
```

**How to run:** `java FinalFieldGuarantee.java`.

Expected output:
```
timeout: 30, environment: production
```

This adds the production-flavored hard case: publishing `ImmutableConfig` through a completely plain, non-`volatile` static field — something that would be risky for a mutable type like `MutableConfig` — but is specifically guaranteed safe by the JLS precisely because **every field** of `ImmutableConfig` is `final`. The Java Language Specification carves out a special guarantee: once a constructor for an all-final-field object finishes, any thread that obtains a reference to that object (by whatever means, even a plain field read with no other synchronization) is guaranteed to see all of its `final` fields correctly initialized. This is the theoretical foundation for why immutable objects are considered inherently thread-safe to share, even without any explicit synchronization around their publication.

## 6. Walkthrough

Tracing `FinalFieldGuarantee.main`:

1. `publisher` constructs `new ImmutableConfig(30, "production")` and assigns it to `sharedConfig`, a plain (non-`volatile`) static field.
2. Independently, `reader` busy-waits in a loop, repeatedly reading `sharedConfig` (also a plain field read) until it observes a non-`null` value.
3. The moment `reader`'s loop observes the newly-constructed `ImmutableConfig` reference, the JLS's special rule for final fields guarantees that `config.timeout` and `config.environment` are both fully and correctly visible — `30` and `"production"` respectively — **regardless** of the fact that neither the reference itself nor the individual fields are `volatile`, and regardless of whether any `synchronized` block or other explicit happens-before mechanism connects `publisher` and `reader`.
4. This guarantee specifically applies to the constructor's assignments to `final` fields becoming visible alongside the reference itself becoming visible — it's a narrower, more specific rule than the general happens-before mechanisms (`volatile`, `synchronized`) used in the earlier levels, but it applies automatically and "for free" whenever every field of the published type is `final`.
5. `publisher.join()` and `reader.join()` at the end simply ensure the main thread waits for both to finish before the program exits — by this point, `reader` has already printed the correctly, safely-published values, demonstrating the final-field guarantee held even though this particular publication path used no `volatile` or `synchronized` mechanism at all.

## 7. Gotchas & takeaways

> **Gotcha:** the final-field safe-publication guarantee applies only if the object's fields are genuinely `final` **and** the constructor doesn't leak `this` (a reference to the not-yet-fully-constructed object) to another thread before the constructor finishes — for example, by registering a listener or starting a thread from within the constructor itself, passing `this` along the way. Such a "`this` escape" during construction can defeat the safe-publication guarantee even for an otherwise all-final-field class, since another thread could obtain and use the reference before construction has actually completed.

- Safe publication guarantees an object is seen by other threads in a fully, correctly constructed state — not the same concern as a plain data race on a single field's value, though closely related.
- Objects with every field declared `final` receive a special JLS guarantee: safely published visibility of those fields, even through a plain, non-`volatile`, unsynchronized reference — provided the constructor doesn't leak `this` before finishing.
- Mutable objects (with non-`final` fields) need an explicit publication mechanism — a `volatile` reference field, `synchronized` blocks around both publication and reading, or a thread-safe concurrent collection — to guarantee safe publication.
- This is the theoretical basis for why immutable objects (all-`final`-field classes) are considered inherently thread-safe to freely share across threads without additional synchronization.
- Avoid letting `this` escape during a constructor (registering callbacks, starting threads, or otherwise handing out a reference to the object before its constructor finishes) — doing so can defeat safe-publication guarantees even for classes that would otherwise qualify.
