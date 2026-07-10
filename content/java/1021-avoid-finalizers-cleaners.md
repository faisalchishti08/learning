---
card: java
gi: 1021
slug: avoid-finalizers-cleaners
title: Avoid finalizers/cleaners
---

## 1. What it is

`Object.finalize()` (deprecated since Java 9, slated for removal) and `java.lang.ref.Cleaner` (its safer successor, added in Java 9) are both mechanisms for running cleanup code when an object becomes unreachable and is garbage-collected. Both are widely considered a trap for resource cleanup: **the JVM gives no guarantee about when — or even whether — a finalizer or cleaner action ever runs**, since it depends entirely on when (or if) garbage collection happens to reclaim that particular object. For anything that needs to reliably release a resource (a file handle, a network socket, a database connection), the correct tool is `try-with-resources` with `AutoCloseable`, not a finalizer or cleaner.

## 2. Why & when

A file handle left open because a finalizer hasn't run yet (and may never run before the JVM exits) can exhaust the operating system's limit on open file descriptors well before garbage collection ever gets around to it — the resource leak happens in real time, on a schedule finalizers and cleaners simply don't guarantee. Finalizers have additional serious problems: they run on a separate, unpredictable finalizer thread that can be starved indefinitely if other finalizers hang, an exception thrown during finalization is silently swallowed, and a subclass can even "resurrect" an object from within `finalize()`, keeping it reachable forever and defeating the point of cleanup entirely. `Cleaner` fixes several of these problems (no resurrection risk, runs on a dedicated thread you don't share with unrelated finalizers) but keeps the fundamental one: timing is still not guaranteed.

Use `try-with-resources` and `AutoCloseable` for anything that needs deterministic, reliable cleanup — which is nearly everything: files, sockets, database connections, locks. Reserve `Cleaner` (never `finalize()`, which should be avoided entirely) purely as a **safety net** — a backstop that catches resource leaks caused by a caller forgetting to close a resource, logging or cleaning up eventually, not as the primary cleanup mechanism.

## 3. Core concept

```
// Wrong: relying on finalize() for cleanup -- deprecated, unpredictable, and dangerous
class LeakyFileHandle {
    private final java.io.FileInputStream stream;
    LeakyFileHandle(String path) throws java.io.IOException { stream = new java.io.FileInputStream(path); }
    @Override protected void finalize() throws Throwable {
        stream.close(); // MIGHT run eventually... or MIGHT NOT run before the JVM exits at all
    }
}

// Right: AutoCloseable + try-with-resources -- deterministic, guaranteed cleanup
class SafeFileHandle implements AutoCloseable {
    private final java.io.FileInputStream stream;
    SafeFileHandle(String path) throws java.io.IOException { stream = new java.io.FileInputStream(path); }
    @Override public void close() throws java.io.IOException { stream.close(); }
}

try (SafeFileHandle handle = new SafeFileHandle("data.txt")) {
    // use handle
} // close() is GUARANTEED to run here, even if an exception is thrown inside the block
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A finalizer's cleanup timing depending on an unpredictable garbage collection cycle versus try-with-resources guaranteeing close is called the instant the block exits">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">finalize(): unpredictable</text>
  <rect x="30" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">object becomes unreachable</text>
  <rect x="30" y="100" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e" stroke-dasharray="4"/>
  <text x="145" y="121" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">finalize() runs... eventually? never?</text>
  <line x1="145" y1="74" x2="145" y2="100" stroke="#f0883e" stroke-dasharray="4" marker-end="url(#a)"/>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">try-with-resources: guaranteed</text>
  <rect x="380" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">try block exits (normally or via exception)</text>
  <rect x="380" y="100" width="230" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="121" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">close() runs IMMEDIATELY</text>
  <line x1="495" y1="74" x2="495" y2="100" stroke="#6db33f" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`finalize()` waits on an unpredictable garbage-collection cycle that may never come; `try-with-resources` calls `close()` the instant the block exits.

## 5. Runnable example

Scenario: a resource wrapper needing reliable cleanup, evolving from a finalizer-based approach whose timing can't be trusted into `try-with-resources`, with `Cleaner` shown only as a last-resort safety net.

### Level 1 — Basic

```java
// File: FinalizerBasic.java
class LeakyResource {
    private final String name;
    private boolean closed = false;

    LeakyResource(String name) {
        this.name = name;
        System.out.println("Opened: " + name);
    }

    void use() { System.out.println("Using: " + name); }

    @Override
    @SuppressWarnings("deprecation")
    protected void finalize() throws Throwable {
        if (!closed) {
            System.out.println("finalize() closing: " + name + " (if this ever runs at all)");
            closed = true;
        }
    }
}

public class FinalizerBasic {
    public static void main(String[] args) {
        LeakyResource resource = new LeakyResource("file-A");
        resource.use();
        // No explicit close -- relying entirely on finalize(), whenever (if ever)
        // garbage collection decides to reclaim this object.
        System.out.println("main() finished; cleanup timing is now completely out of our hands");
    }
}
```

**How to run:** save as `FinalizerBasic.java`, then `javac FinalizerBasic.java && java FinalizerBasic` (JDK 17+, `finalize()` still compiles with a deprecation warning through Java 17).

Expected output:
```
Opened: file-A
Using: file-A
main() finished; cleanup timing is now completely out of our hands
```

Notice the `finalize()` cleanup message never even prints — the JVM exits before garbage collection ever gets around to (or bothers to) finalize `resource`, which is exactly the failure mode that makes finalizers unsuitable for resource cleanup: there's no guarantee it runs before the program ends.

### Level 2 — Intermediate

```java
// File: FinalizerIntermediate.java
class SafeResource implements AutoCloseable {
    private final String name;

    SafeResource(String name) {
        this.name = name;
        System.out.println("Opened: " + name);
    }

    void use() { System.out.println("Using: " + name); }

    @Override
    public void close() {
        System.out.println("Closed: " + name);
    }
}

public class FinalizerIntermediate {
    public static void main(String[] args) {
        try (SafeResource resource = new SafeResource("file-A")) {
            resource.use();
        } // close() is guaranteed to run right here, deterministically
        System.out.println("main() finished; cleanup already happened");
    }
}
```

**How to run:** save as `FinalizerIntermediate.java`, then `javac FinalizerIntermediate.java && java FinalizerIntermediate` (JDK 17+).

Expected output:
```
Opened: file-A
Using: file-A
Closed: file-A
main() finished; cleanup already happened
```

The real-world concern added: `close()` runs deterministically the moment the `try` block exits — no dependency on garbage collection timing at all. `"Closed: file-A"` is guaranteed to print before `"main() finished"`, unlike the finalizer version where cleanup might never print at all.

### Level 3 — Advanced

```java
// File: FinalizerAdvanced.java
import java.lang.ref.Cleaner;

class RobustResource implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();

    // The cleanup logic MUST NOT reference the RobustResource instance itself --
    // only this static inner class and its own fields, to avoid keeping the
    // resource reachable (which would defeat garbage collection entirely).
    private static class ResourceState implements Runnable {
        private final String name;
        private boolean closed = false;
        ResourceState(String name) { this.name = name; }

        @Override public void run() { // the CLEANER's safety-net action
            if (!closed) {
                System.out.println("SAFETY NET: " + name + " was never explicitly closed! Cleaning up now.");
                closed = true;
            }
        }
    }

    private final ResourceState state;
    private final Cleaner.Cleanable cleanable;

    RobustResource(String name) {
        this.state = new ResourceState(name);
        this.cleanable = CLEANER.register(this, state); // registers the safety net
        System.out.println("Opened: " + name);
    }

    void use() { System.out.println("Using: " + state.name); }

    @Override
    public void close() {
        state.closed = true; // mark it closed FIRST so the safety net knows not to act
        System.out.println("Explicitly closed: " + state.name);
        cleanable.clean(); // run the cleanup action NOW, deterministically
    }
}

public class FinalizerAdvanced {
    public static void main(String[] args) {
        // The correct path: explicit try-with-resources -- the safety net never fires.
        try (RobustResource resource = new RobustResource("file-A")) {
            resource.use();
        }

        System.out.println("---");

        // A forgotten resource -- close() never called. The Cleaner is a LAST-RESORT
        // safety net; its timing is still not guaranteed, but at least it doesn't
        // depend on the fragile, deprecated finalize() mechanism.
        RobustResource forgotten = new RobustResource("file-B");
        forgotten.use();
        forgotten = null; // drop the only reference; eligible for GC
        System.gc(); // NOTE: forcing GC like this is only for demonstration -- never rely on
                      // System.gc() in real code, since the JVM is free to ignore the request
        try { Thread.sleep(200); } catch (InterruptedException ignored) {}
    }
}
```

**How to run:** save as `FinalizerAdvanced.java`, then `javac FinalizerAdvanced.java && java FinalizerAdvanced` (JDK 17+). Note: the safety-net line's exact timing (or whether it appears at all before the program exits) is not guaranteed even with `System.gc()` — this demonstrates the *mechanism*, not a timing guarantee.

Expected output (the safety-net line may or may not appear, and its exact position isn't guaranteed):
```
Opened: file-A
Using: file-A
Explicitly closed: file-A
---
Opened: file-B
Using: file-B
SAFETY NET: file-B was never explicitly closed! Cleaning up now.
```

The production-flavored hard case: `RobustResource` uses `Cleaner` purely as a backstop — the *correct* usage (`try-with-resources`) never triggers the safety net at all (`state.closed = true` is set before `cleanable.clean()` runs), while the *forgotten* resource (`forgotten`, never explicitly closed) relies on the safety net to eventually catch the leak — demonstrating why `Cleaner` is a last line of defense, not a substitute for calling `close()`.

## 6. Walkthrough

Tracing the `try (RobustResource resource = new RobustResource("file-A")) { resource.use(); }` block in `FinalizerAdvanced.main`:

1. `new RobustResource("file-A")` constructs a `ResourceState` holding `name = "file-A"`, `closed = false`, then calls `CLEANER.register(this, state)` — this tells the JVM's `Cleaner` mechanism "when the `RobustResource` instance becomes unreachable, run `state.run()`," without `state` itself ever holding a reference back to the `RobustResource` (avoiding a reference cycle that would prevent garbage collection).
2. The constructor prints `"Opened: file-A"`. `resource.use()` prints `"Using: file-A"`.
3. The `try` block ends (no exception thrown), so Java's `try-with-resources` mechanism automatically calls `resource.close()`.
4. Inside `close()`, `state.closed = true` runs *first*, marking the state as already handled. Then `"Explicitly closed: file-A"` prints. Then `cleanable.clean()` is called, which runs `state.run()` immediately, deterministically, right here — but since `state.closed` is already `true`, the `if (!closed)` check inside `run()` is `false`, so the safety-net message is skipped entirely.
5. Compare with `forgotten`: its `close()` is never called at all. `forgotten = null` drops the only reference to it, making it eligible for garbage collection. `System.gc()` is a *request* (not a guarantee) that the JVM run garbage collection soon.
6. If and when the JVM actually collects `forgotten`'s underlying `RobustResource` object, the `Cleaner` mechanism invokes `state.run()` on its own dedicated thread — since `state.closed` is still `false` (nobody ever called `close()`), the `if (!closed)` check passes, printing `"SAFETY NET: file-B was never explicitly closed! Cleaning up now."` — catching the leak that `try-with-resources` was never used to prevent, but with no guarantee of exactly when this happens relative to the rest of the program.

## 7. Gotchas & takeaways

> **Gotcha:** the cleanup logic registered with a `Cleaner` (here, `ResourceState`) must **never** hold a reference back to the object being cleaned up (`RobustResource` itself) — doing so creates a reference cycle that keeps the object permanently reachable, meaning it can never become eligible for collection and the cleanup action never fires at all, silently defeating both the primary cleanup path and the safety net.

- `finalize()` is deprecated and dangerous: it runs (if at all) at an unpredictable time, on a separate thread that can be starved, silently swallows exceptions, and can even be abused to resurrect an unreachable object.
- `Cleaner` fixes several of `finalize()`'s specific dangers (no resurrection, dedicated thread) but keeps the fundamental problem — timing is still not guaranteed, so it must never be the primary way a resource gets released.
- `try-with-resources` with `AutoCloseable` is the correct, deterministic mechanism for anything that needs guaranteed cleanup — files, sockets, connections, locks — and should be the default choice for essentially all resource-management code.
- `Cleaner` is appropriate only as a last-resort safety net catching a caller's mistake (forgetting to close a resource), logging or cleaning up eventually as a backstop — never as the sole cleanup mechanism.
- A `Cleaner`'s registered cleanup action must not reference the object it's cleaning up, to avoid a reference cycle that would prevent the object (and therefore the cleanup) from ever running.
- Don't call `System.gc()` in real production code expecting it to force collection — the JVM is free to ignore the request entirely; it's shown here purely to illustrate the mechanism for a tutorial example.
