---
card: java
gi: 724
slug: deprecate-finalization-for-removal
title: Deprecate finalization for removal
---

## 1. What it is

**Java 18** (JEP 421) marks **finalization** — `Object.finalize()` and the whole mechanism of overriding it to run cleanup code before an object is garbage collected — as **deprecated for removal**. This is the strongest level of deprecation the JDK uses: it signals that `finalize()` isn't just discouraged, it is on a concrete path to being deleted from the language entirely in a future release (which later JDKs went on to do). Compiling code that overrides `finalize()` on Java 18+ now produces a compiler warning, and running such code produces a runtime warning the first time finalization actually triggers. The JEP also adds a way to disable finalization JVM-wide (`--finalization=disabled`), for applications that want to prove they no longer depend on it at all.

## 2. Why & when

Finalization was Java's original answer to "run cleanup code when an object is about to be discarded," dating back to Java 1.0. In practice it turned out to be a poor mechanism on almost every axis: finalizer methods run on a dedicated, unpredictable finalizer thread at a time entirely up to the garbage collector — not "soon after the object becomes unreachable," but "whenever the GC gets around to it," which could be immediately or could be minutes later, or in some GC configurations, potentially never if the process exits first. Objects with a `finalize()` method also survive at least one extra garbage collection cycle (they must be resurrectable during finalization, per the original design), which hurts GC performance for the whole application, not just the finalized object. Worse, a finalizer that throws an exception is silently swallowed, a finalizer can "resurrect" its object by storing a reference to `this` somewhere reachable, and multiple finalizers queued up can create unpredictable, hard-to-reproduce ordering bugs. The Java ecosystem largely already knew all this — `try`-with-resources and `AutoCloseable` (deterministic, explicit cleanup) had been the recommended replacement since Java 7, and `java.lang.ref.Cleaner` (introduced in Java 9, running cleanup on phantom-reference queues rather than actual finalization) had been the recommended replacement for the narrower "cleanup as a safety net if a resource wasn't explicitly closed" case. JEP 421 formalizes what had already become established best practice: never rely on `finalize()`. Use `try`-with-resources and `AutoCloseable` for anything with a deterministic lifetime (which is almost everything), and `Cleaner` only for the safety-net case of catching resources a caller forgot to close explicitly.

## 3. Core concept

```java
// Deprecated for removal since Java 18 — do not write new code like this:
class OldResource {
    @Override
    protected void finalize() throws Throwable {
        System.out.println("cleaning up (unpredictable timing!)");
    }
}

// The modern replacement: deterministic, explicit cleanup.
class NewResource implements AutoCloseable {
    @Override
    public void close() {
        System.out.println("cleaning up (deterministic, immediate)");
    }
}
try (NewResource r = new NewResource()) {
    // use r
} // close() runs HERE, guaranteed, exactly when the block exits
```

`Cleaner` sits between the two: a safety net for resources with no guaranteed explicit `close()` call, run via phantom references rather than the deprecated finalization mechanism.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="finalize is deprecated for removal because its cleanup timing is unpredictable; try-with-resources with AutoCloseable gives deterministic cleanup, and Cleaner gives a safety net using phantom references instead of finalization">
  <rect x="20" y="20" width="180" height="80" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="110" y="42" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">finalize()</text>
  <text x="110" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">runs whenever GC</text>
  <text x="110" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">decides — unpredictable</text>

  <rect x="230" y="20" width="180" height="80" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">try-with-resources</text>
  <text x="320" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">close() runs at the</text>
  <text x="320" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">exact end of the block</text>

  <rect x="440" y="20" width="180" height="80" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Cleaner</text>
  <text x="530" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">safety-net cleanup via</text>
  <text x="530" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">phantom references</text>

  <text x="320" y="130" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Deprecated for removal (Java 18) --&gt; use the other two instead</text>
</svg>

`finalize()` is being phased out in favor of two mechanisms with well-defined, understood behavior.

## 5. Runnable example

Scenario: a resource class representing a file handle, first shown with the deprecated `finalize()` approach (for contrast, demonstrating its unpredictable timing), then migrated to `try`-with-resources with `AutoCloseable` for deterministic cleanup, then extended with `Cleaner` as a safety net that still triggers cleanup even if a caller forgets to call `close()` explicitly.

### Level 1 — Basic

```java
// File: FinalizeDemo.java
// Demonstrates the deprecated approach and WHY it's unreliable — the
// finalizer's timing depends on garbage collection, not program logic.
@SuppressWarnings("removal") // finalize() is deprecated for removal since Java 18
public class FinalizeDemo {
    static class OldResource {
        private final String name;
        OldResource(String name) { this.name = name; System.out.println("opened: " + name); }

        @Override
        protected void finalize() {
            System.out.println("finalized (cleanup ran): " + name);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        OldResource r = new OldResource("file-A");
        r = null; // drop the only reference

        System.out.println("Requesting GC — but finalize() timing is NOT guaranteed...");
        System.gc();
        Thread.sleep(200); // best-effort wait; still no real guarantee finalize() has run

        System.out.println("Program ending — cleanup may or may not have printed above this line.");
    }
}
```

**How to run:**
```
java --enable-preview FinalizeDemo.java
```

Expected output (the finalized line's presence and position are NOT guaranteed — this unpredictability is the entire point):
```
opened: file-A
Requesting GC — but finalize() timing is NOT guaranteed...
finalized (cleanup ran): file-A
Program ending — cleanup may or may not have printed above this line.
```
Compiling also emits a warning such as: `warning: [removal] finalize() in Object has been deprecated and marked for removal`.

### Level 2 — Intermediate

```java
// File: AutoCloseableDemo.java
// The SAME resource concept, migrated to AutoCloseable + try-with-resources —
// cleanup now happens at a precise, guaranteed point in the code.
public class AutoCloseableDemo {
    static class ManagedResource implements AutoCloseable {
        private final String name;
        ManagedResource(String name) { this.name = name; System.out.println("opened: " + name); }

        void use() { System.out.println("using: " + name); }

        @Override
        public void close() {
            System.out.println("closed (cleanup ran): " + name);
        }
    }

    public static void main(String[] args) {
        try (ManagedResource r = new ManagedResource("file-A")) {
            r.use();
        } // close() is GUARANTEED to run here, in order, every single time

        System.out.println("Program continuing — cleanup already happened, deterministically.");
    }
}
```

**How to run:**
```
java AutoCloseableDemo.java
```

Expected output (identical every run, unlike Level 1):
```
opened: file-A
using: file-A
closed (cleanup ran): file-A
Program continuing — cleanup already happened, deterministically.
```

### Level 3 — Advanced

```java
// File: CleanerSafetyNetDemo.java
// Combines AutoCloseable (the primary, deterministic path) with Cleaner (a
// safety net in case a caller forgets to call close()) — the recommended,
// production-flavored pattern replacing finalize() entirely.
import java.lang.ref.Cleaner;

public class CleanerSafetyNetDemo {
    private static final Cleaner CLEANER = Cleaner.create();

    static class ManagedResource implements AutoCloseable {
        // State captured by the cleanup action must NOT reference the
        // ManagedResource itself, or the object could never become unreachable.
        private static class ResourceState implements Runnable {
            final String name;
            ResourceState(String name) { this.name = name; }
            @Override public void run() {
                System.out.println("cleaner ran safety-net cleanup for: " + name + " (close() was never called!)");
            }
        }

        private final ResourceState state;
        private final Cleaner.Cleanable cleanable;
        private boolean closed = false;

        ManagedResource(String name) {
            this.state = new ResourceState(name);
            this.cleanable = CLEANER.register(this, state);
            System.out.println("opened: " + name);
        }

        void use() { System.out.println("using: " + state.name); }

        @Override
        public void close() {
            if (!closed) {
                closed = true;
                cleanable.clean(); // runs the cleanup action immediately, deterministically
                System.out.println("closed explicitly: " + state.name);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // Path 1: caller behaves correctly and closes explicitly.
        try (ManagedResource r = new ManagedResource("file-A")) {
            r.use();
        }

        // Path 2: caller forgets to close — Cleaner is the safety net that still fires.
        ManagedResource forgotten = new ManagedResource("file-B");
        forgotten.use();
        forgotten = null; // dropped without close() — Cleaner will eventually catch this

        System.gc();
        Thread.sleep(200);
        System.out.println("Program ending.");
    }
}
```

**How to run:**
```
java CleanerSafetyNetDemo.java
```

Expected output (the file-A lines are always in this exact order and guaranteed; the file-B cleaner line's exact timing depends on GC, but WILL eventually fire, unlike finalize()'s unreliable guarantees):
```
opened: file-A
using: file-A
closed explicitly: file-A
opened: file-B
using: file-B
cleaner ran safety-net cleanup for: file-B (close() was never called!)
Program ending.
```

## 6. Walkthrough

1. `CleanerSafetyNetDemo` starts by creating a single JVM-wide `Cleaner` instance via `Cleaner.create()` — a `Cleaner` manages a background thread that watches for objects becoming phantom-reachable (a GC-tracked state distinct from finalization) and runs registered cleanup actions when that happens.
2. `main`'s first block constructs a `ManagedResource("file-A")` inside a `try`-with-resources statement. Inside the constructor, `CLEANER.register(this, state)` tells the `Cleaner`: "if this `ManagedResource` object is ever garbage collected without `clean()` having already run, execute `state.run()` then." This registration returns a `Cleanable` handle, `cleanable`, stored on the resource.
3. `r.use()` runs normally. When the `try` block ends, `close()` is called automatically (this is what `try`-with-resources guarantees) — inside `close()`, `cleanable.clean()` runs the cleanup action **immediately and deterministically**, right there in the calling thread, and also marks the registration as already-run so the `Cleaner`'s background machinery will never invoke it again later. This is why the output shows `closed explicitly: file-A`, not the cleaner's safety-net message.
4. `main`'s second block constructs `ManagedResource("file-B")`, uses it, but then sets the only reference (`forgotten`) to `null` **without calling `close()`** — deliberately simulating a caller bug (a forgotten resource, an exception path that skipped cleanup, etc.).
5. `System.gc()` requests garbage collection; once the JVM actually reclaims the now-unreachable `ManagedResource` object, the `Cleaner`'s background thread detects the associated phantom reference has been enqueued and invokes `state.run()` — printing the safety-net message. Crucially, `ResourceState` is a **separate, static nested class** holding only the data cleanup needs (`name`), not a reference back to `ManagedResource` itself — if the cleanup action held a reference to the resource object, that object could never become unreachable in the first place, defeating the whole mechanism (the same "resurrection" hazard that made `finalize()` unsafe).
6. The `Thread.sleep(200)` is a pragmatic wait for the demo's output ordering only — real code must never depend on `Cleaner` running by any particular deadline; like the old `finalize()`, its background thread runs on its own schedule. The difference from `finalize()` is not "faster" or "more predictable timing" — it's that `Cleaner` has none of finalization's other hazards (no silent exception-swallowing that corrupts an unrelated finalizer queue, no forced extra GC generation for every instance, no possibility of "resurrecting" the object), and it is explicitly documented and supported as the safety-net mechanism going forward.

```
Path 1 (correct caller):  new ManagedResource -> use() -> close() [try-with-resources]
                                                              |
                                                     cleanable.clean() runs NOW
                                                     Cleaner's background action: never fires (already run)

Path 2 (forgetful caller): new ManagedResource -> use() -> reference dropped, no close()
                                                              |
                                                    object becomes unreachable, GC'd
                                                              |
                                                    Cleaner's background thread detects this
                                                              |
                                                    runs state.run() as a SAFETY NET
```

## 7. Gotchas & takeaways

> `finalize()` being **deprecated for removal** — the strongest deprecation category — means it is not merely discouraged; it is scheduled for actual deletion from the language in a future release (which later JDKs carried out). Any code still overriding `Object.finalize()` should be migrated now, not treated as a stylistic warning to defer indefinitely.
- The replacement is a **two-tier strategy**, not a single API swap: use `AutoCloseable` + `try`-with-resources as the primary, deterministic cleanup mechanism for anything with a well-defined lifetime (which covers the overwhelming majority of cleanup needs), and reserve `Cleaner` purely as a safety net for the narrower case of "catch it if the caller forgot to close explicitly."
- A `Cleaner`'s registered cleanup action must **never** hold a reference back to the object being cleaned — doing so prevents that object from ever becoming unreachable, silently defeating the entire mechanism; this is exactly why `ResourceState` in Level 3 is a separate static class holding only the data cleanup needs.
- Java 18 also adds a `--finalization=disabled` runtime flag, letting an application prove (by intentionally breaking) that it no longer depends on any code path that relies on `finalize()` ever actually running — useful for auditing large legacy codebases before finalization is fully removed.
- Like `finalize()`, `Cleaner`'s background thread runs on its own schedule with **no timing guarantee** — the difference is not "runs sooner," it's "has none of finalization's correctness hazards" (exception swallowing, object resurrection, forced extra GC cycles per instance). Never write code whose correctness — as opposed to best-effort cleanup — depends on a `Cleaner` action having run by a specific point.
