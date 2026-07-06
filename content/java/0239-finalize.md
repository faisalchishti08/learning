---
card: java
gi: 239
slug: finalize
title: finalize()
---

## 1. What it is

`finalize()` is a `protected` method inherited from `Object` that, historically, the garbage collector would call on an object just before reclaiming its memory, giving it one last chance to clean up resources. It is deprecated since Java 9 and scheduled for eventual removal, because it turned out to be unreliable, slow, and a frequent source of subtle bugs — modern Java code should not override or rely on it.

```java
class NoisyResource {
    @Override
    protected void finalize() throws Throwable { // deprecated since Java 9 — shown for historical understanding only
        System.out.println("finalize() called before garbage collection");
        super.finalize();
    }
}

public class FinalizeDemo {
    public static void main(String[] args) {
        NoisyResource r = new NoisyResource();
        r = null; // eligible for garbage collection now
        System.gc(); // only a HINT — finalize() might run soon, late, or arguably never
        // Output timing (or whether it prints at all) is NOT guaranteed
    }
}
```

`System.gc()` merely *suggests* that the JVM run garbage collection — it does not force it, and even if collection does run, there is no guarantee about *when* `finalize()` executes, or that it executes before the program exits at all; this unpredictability is the central reason `finalize()` is considered unsuitable for real cleanup logic.

## 2. Why & when

`finalize()` is covered here mainly so you can recognize it in older code and understand exactly why it was abandoned — not because you should use it in anything new.

- **Historical intent** — the idea was reasonable on paper: let an object release resources (file handles, network connections, native memory) automatically when it's about to be garbage collected, without requiring the programmer to remember to close them explicitly.
- **Why it failed in practice** — the JVM gives no guarantee about *when*, or even *whether*, `finalize()` runs; an object can sit uncollected indefinitely (or the JVM can shut down without ever running it), meaning resources "cleaned up" only in `finalize()` could leak for a long time or forever.
- **Performance and correctness hazards** — objects with a `finalize()` override are slower for the garbage collector to handle (they typically require an extra collection cycle), and a buggy `finalize()` that "resurrects" an object (by storing `this` somewhere reachable) can create bizarre, hard-to-debug object lifecycle issues.

You should recognize `finalize()` if you encounter it in legacy code, and know that it has been formally deprecated since Java 9 in favor of far more reliable tools: `try-with-resources` combined with `AutoCloseable` (covered in dedicated resource-management topics) for deterministic, immediate cleanup, and `java.lang.ref.Cleaner` for the rare cases needing a GC-triggered fallback cleanup — never write a new `finalize()` override in modern code.

## 3. Core concept

```java
class FileHandle implements AutoCloseable {
    private boolean closed = false;

    void write(String data) {
        if (closed) throw new IllegalStateException("already closed");
        System.out.println("Writing: " + data);
    }

    @Override
    public void close() { // deterministic, explicit cleanup — the modern replacement for finalize()
        closed = true;
        System.out.println("Closed explicitly and immediately");
    }
}

public class ModernCleanupCore {
    public static void main(String[] args) {
        try (FileHandle handle = new FileHandle()) { // try-with-resources
            handle.write("some data");
        } // close() is guaranteed to run HERE, deterministically, not "eventually, maybe"
    }
}
```

Unlike `finalize()`, `try-with-resources` guarantees `close()` runs at a precise, predictable point — the moment the `try` block ends, whether normally or via an exception — which is exactly the reliability guarantee `finalize()` could never provide.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="finalize timing is unpredictable and may never run, compared to try with resources close which is guaranteed to run immediately and deterministically">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <text x="150" y="28" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">finalize() (deprecated)</text>
  <rect x="40" y="35" width="220" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="55" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">object unreachable</text>
  <line x1="150" y1="65" x2="150" y2="90" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="150" y="85" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">? unknown delay, or never</text>
  <rect x="40" y="95" width="220" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="150" y="115" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">finalize() maybe runs</text>

  <text x="450" y="28" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">try-with-resources</text>
  <rect x="360" y="35" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="55" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">try block ends</text>
  <line x1="450" y1="65" x2="450" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <rect x="360" y="95" width="180" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="115" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">close() runs, guaranteed</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">finalize() timing is unpredictable and unguaranteed; try-with-resources cleanup is immediate and deterministic.</text>
</svg>

`finalize()` offers no timing guarantee at all; `try-with-resources` guarantees cleanup at a precise, known point.

## 5. Runnable example

Scenario: a simple resource-tracking counter, shown first the historically tempting (but broken) `finalize()`-based way, then rebuilt correctly with `try-with-resources`, then hardened to show `finalize()`'s unreliability concretely by comparison.

### Level 1 — Basic

```java
public class FinalizeBasic {
    static class LegacyResource {
        String name;
        LegacyResource(String name) {
            this.name = name;
            System.out.println("Opened: " + name);
        }

        @SuppressWarnings("removal")
        @Override
        protected void finalize() throws Throwable { // deprecated, shown ONLY for historical illustration
            System.out.println("finalize() ran for: " + name);
            super.finalize();
        }
    }

    public static void main(String[] args) {
        LegacyResource r = new LegacyResource("legacy-file");
        r = null;
        System.gc(); // just a hint; finalize() may or may not run before the program continues/exits
        System.out.println("Program continues, with no guarantee finalize() has run yet");
    }
}
```

**How to run:** `java FinalizeBasic.java`

The line `"finalize() ran for: legacy-file"` might print before, after, or not at all relative to `"Program continues..."` — this non-determinism is precisely why `finalize()` is unsuitable for anything relying on cleanup happening at a known time, like releasing a file handle promptly.

### Level 2 — Intermediate

The same resource idea, rebuilt the modern, correct way with `AutoCloseable` and `try-with-resources`, which removes the uncertainty entirely.

```java
public class FinalizeIntermediate {
    static class ModernResource implements AutoCloseable {
        String name;
        ModernResource(String name) {
            this.name = name;
            System.out.println("Opened: " + name);
        }

        void use() { System.out.println("Using: " + name); }

        @Override
        public void close() {
            System.out.println("Closed: " + name); // guaranteed to run, deterministically
        }
    }

    public static void main(String[] args) {
        try (ModernResource resource = new ModernResource("modern-file")) {
            resource.use();
        } // close() is GUARANTEED to run exactly here, every single time
        System.out.println("Program continues, resource is DEFINITELY already closed");
    }
}
```

**How to run:** `java FinalizeIntermediate.java`

`"Closed: modern-file"` is guaranteed to print before `"Program continues..."`, every single run, with no reliance on garbage collection timing at all — `try-with-resources` calls `close()` automatically the instant the `try` block finishes.

### Level 3 — Advanced

Both approaches side by side, demonstrating concretely that `finalize()` provides no ordering guarantee relative to program flow, while `try-with-resources` cleanup order is completely predictable, even across multiple resources.

```java
public class FinalizeAdvanced {
    static class ModernResource implements AutoCloseable {
        String name;
        ModernResource(String name) {
            this.name = name;
            System.out.println("Opened: " + name);
        }
        @Override
        public void close() { System.out.println("Closed: " + name); }
    }

    public static void main(String[] args) {
        // Multiple resources: try-with-resources closes them in REVERSE order of acquisition, guaranteed
        try (ModernResource first = new ModernResource("first");
             ModernResource second = new ModernResource("second")) {
            System.out.println("Using both resources");
        }
        // Guaranteed output order: Opened first, Opened second, Using both, Closed second, Closed first

        System.out.println("---");

        // Contrast: a finalize()-based resource gives NO such guarantee
        Object legacy = new Object() {
            @SuppressWarnings("removal")
            @Override
            protected void finalize() throws Throwable {
                System.out.println("finalize() ran (timing NOT guaranteed relative to anything below)");
            }
        };
        legacy = null;
        System.gc();
        System.out.println("This line's position relative to finalize() output above is NOT guaranteed");
    }
}
```

**How to run:** `java FinalizeAdvanced.java`

The `try-with-resources` block's output order is completely deterministic (`Closed: second` always before `Closed: first`, since resources close in reverse acquisition order), while the `finalize()`-based line's position in the output — or its very presence — is not guaranteed by the language specification at all, even though `System.gc()` was called.

## 6. Walkthrough

Trace the guaranteed portion of `FinalizeAdvanced.main` — the `try-with-resources` block — step by step, since that part's behaviour is fully deterministic (the `finalize()` portion afterward has no guaranteed order, by design, so it is described separately).

**`new ModernResource("first")`.** Constructor runs, printing `"Opened: first"`.

**`new ModernResource("second")`.** Constructor runs, printing `"Opened: second"`. Both resources are now open, in acquisition order first, then second.

**`System.out.println("Using both resources")`.** Prints `"Using both resources"` inside the `try` body.

**The `try` block ends.** `try-with-resources` closes resources in the *reverse* of their acquisition order: `second.close()` runs first, printing `"Closed: second"`, then `first.close()` runs, printing `"Closed: first"`. This reverse order matters when resources depend on each other (the second-opened resource is often the one that should be closed first).

**After the `try` block**, `"---"` is printed as a separator.

**The `finalize()`-based portion runs next**, but its printed line (`"finalize() ran..."`), if it appears at all, could in principle appear before, interleaved with, or well after the surrounding lines — the JVM specification simply does not promise anything about its timing, which is exactly the property that makes it unusable for reliable cleanup.

```
try-with-resources (fully deterministic):
  Opened: first
  Opened: second
  Using both resources
  Closed: second   <- reverse order
  Closed: first    <- reverse order

finalize()-based (NOT deterministic):
  "finalize() ran..." -> may print anywhere here, or never, per the JVM's discretion
  "This line's position..." -> guaranteed only relative to itself, not to finalize()'s output
```

**Final output (guaranteed portion).**
```
Opened: first
Opened: second
Using both resources
Closed: second
Closed: first
---
This line's position relative to finalize() output above is NOT guaranteed
```
The `finalize()` line may or may not appear, and its position relative to the guaranteed lines is unspecified — this is the concrete, observable difference between deterministic `try-with-resources` cleanup and non-deterministic `finalize()`-based cleanup.

## 7. Gotchas & takeaways

> **`finalize()` is deprecated since Java 9 (marked `@Deprecated(since="9", forRemoval=true)`) and must never be used in new code.** Relying on it for releasing resources (file handles, sockets, locks) risks those resources staying held far longer than intended, or indefinitely, since the JVM makes no promise about when — or whether — garbage collection, and therefore `finalize()`, ever runs for a given object.

> **`System.gc()` is only ever a suggestion to the JVM, never a command** — calling it does not force garbage collection to happen immediately, or at all, and production code should essentially never call it directly; the garbage collector is designed to make its own timing decisions based on memory pressure and heuristics far better than manual intervention typically achieves.

- `finalize()` was intended to let an object clean up before being garbage collected, but its timing is entirely unpredictable and it may never run.
- It has been formally deprecated since Java 9, specifically for removal — do not override it in new code.
- `try-with-resources` combined with `AutoCloseable` is the modern, deterministic replacement, guaranteeing `close()` runs at a precise, known point.
- For the rare case needing GC-triggered fallback cleanup as a safety net, `java.lang.ref.Cleaner` is the modern, safer mechanism — not `finalize()`.
