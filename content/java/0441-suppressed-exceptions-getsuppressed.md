---
card: java
gi: 441
slug: suppressed-exceptions-getsuppressed
title: Suppressed exceptions (getSuppressed)
---

## 1. What it is

When a try-with-resources block's body throws an exception, **and** closing one or more of its resources *also* throws, Java doesn't discard either one. The body's exception becomes the **primary** exception (the one actually propagated and caught), while each resource's `close()` failure is attached to it as a **suppressed** exception via `Throwable.addSuppressed(...)`, retrievable later with `getSuppressed()`. Both failures are preserved — nothing is silently lost.

## 2. Why & when

Before this mechanism existed (and before try-with-resources itself), the classic problem was: a `try` block throws, and the corresponding `finally` block's cleanup code *also* throws — and since only one exception can actually propagate out of a `try`/`finally`, the `finally` block's exception would silently **replace** the original one, permanently losing the real root cause of the failure. Debugging "why did this fail" becomes much harder when the actual triggering exception vanished, replaced by an unrelated `close()` failure.

Suppressed exceptions solve this by keeping the *first* meaningful failure (the body's) as primary — since it's almost always the more informative one, being the actual cause of the whole cascade — while still preserving every subsequent `close()` failure, retrievable through `getSuppressed()` for anyone who needs the full picture (thorough logging, debugging tools). You benefit from this automatically any time you use try-with-resources; understanding `getSuppressed()` matters mainly for writing complete logging or diagnostic code that doesn't discard this extra information.

## 3. Core concept

```java
try {
    try (FlakyResource r = new FlakyResource()) {
        throw new RuntimeException("body failed");   // this becomes the PRIMARY exception
    }                                                  // r.close() ALSO throws here
} catch (Exception e) {
    System.out.println(e.getMessage());               // "body failed" -- the primary exception
    for (Throwable suppressed : e.getSuppressed()) {
        System.out.println(suppressed.getMessage());  // the close() failure, preserved, not lost
    }
}
```

The body's exception "wins" and is what you actually catch; every `close()` failure that happened while unwinding is still there, just attached rather than propagated separately.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="When both the try body and a resource's close method throw, the body's exception becomes primary and is what propagates, while the close failure is attached to it as a suppressed exception rather than being lost">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="35" width="180" height="34" rx="6" fill="#1c2430" stroke="#f85149"/><text x="120" y="57" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">body throws "body failed"</text>

  <rect x="30" y="90" width="180" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/><text x="120" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">close() throws too</text>

  <rect x="330" y="60" width="260" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="460" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Primary: "body failed" (propagates)</text>
  <line x1="210" y1="50" x2="325" y2="70" stroke="#6db33f" marker-end="url(asp1)"/>

  <rect x="330" y="105" width="260" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4,3"/><text x="460" y="125" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Suppressed: "close() failed" (attached)</text>
  <line x1="210" y1="105" x2="325" y2="115" stroke="#79c0ff" marker-end="url(asp2)"/>

  <defs><marker id="asp1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker><marker id="asp2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Both failures survive — the body's exception propagates as primary, the close failure rides along, attached and retrievable.

## 5. Runnable example

Scenario: a resource whose `close()` is unreliable — the same failure scenario, evolved from a single resource where both the body and `close()` throw, through multiple resources each failing to close (collecting several suppressed exceptions), to manually replicating what try-with-resources does automatically, to see exactly how much boilerplate it saves.

### Level 1 — Basic

```java
public class SuppressedBasic {
    static class FlakyResource implements AutoCloseable {
        @Override
        public void close() throws Exception {
            throw new Exception("close() failed");
        }
    }

    public static void main(String[] args) {
        try {
            try (FlakyResource r = new FlakyResource()) {
                throw new RuntimeException("body failed"); // the body ALSO throws
            }
        } catch (Exception e) {
            System.out.println("Primary exception: " + e.getMessage());
            for (Throwable suppressed : e.getSuppressed()) {
                System.out.println("Suppressed: " + suppressed.getMessage());
            }
        }
    }
}
```

**How to run:** `java SuppressedBasic.java`

The body's `RuntimeException("body failed")` becomes the primary exception (what's actually caught), while `close()`'s `Exception("close() failed")` is attached as a suppressed exception rather than replacing or being lost alongside it.

### Level 2 — Intermediate

```java
public class SuppressedMultiple {
    static class FlakyResource implements AutoCloseable {
        private final String name;
        FlakyResource(String name) { this.name = name; }
        @Override
        public void close() throws Exception {
            throw new Exception(name + " failed to close");
        }
    }

    public static void main(String[] args) {
        try {
            try (FlakyResource a = new FlakyResource("A");
                 FlakyResource b = new FlakyResource("B")) {
                throw new RuntimeException("body failed");
            }
        } catch (Exception e) {
            System.out.println("Primary exception: " + e.getMessage());
            for (Throwable suppressed : e.getSuppressed()) {
                System.out.println("Suppressed: " + suppressed.getMessage());
            }
        }
    }
}
```

**How to run:** `java SuppressedMultiple.java`

Both `a` and `b` fail to close, and **both** failures show up in `getSuppressed()` — in the order they were actually closed, which is the reverse of declaration order (`b` first, then `a`), exactly matching try-with-resources' normal closing order.

### Level 3 — Advanced

```java
public class SuppressedManual {
    static class FlakyResource implements AutoCloseable {
        private final String name;
        FlakyResource(String name) { this.name = name; }
        @Override
        public void close() throws Exception {
            throw new Exception(name + " failed to close");
        }
    }

    // Manually replicating what try-with-resources does automatically -- notice how much
    // more code this takes, and how easy it would be to get subtly wrong.
    static void manualVersion() throws Exception {
        FlakyResource a = new FlakyResource("A");
        FlakyResource b = new FlakyResource("B");
        Throwable primary = null;
        try {
            throw new RuntimeException("body failed");
        } catch (Throwable t) {
            primary = t;
            throw t;
        } finally {
            for (AutoCloseable resource : new AutoCloseable[]{b, a}) { // reverse order, matching try-with-resources
                try {
                    resource.close();
                } catch (Throwable closeFailure) {
                    if (primary != null) {
                        primary.addSuppressed(closeFailure); // manually attach it as suppressed
                    }
                }
            }
        }
    }

    public static void main(String[] args) {
        try {
            manualVersion();
        } catch (Exception e) {
            System.out.println("Primary exception: " + e.getMessage());
            for (Throwable suppressed : e.getSuppressed()) {
                System.out.println("Suppressed: " + suppressed.getMessage());
            }
        }
    }
}
```

**How to run:** `java SuppressedManual.java`

This manually reproduces exactly what try-with-resources does automatically: track the primary exception, close resources in reverse order inside `finally`, and call `addSuppressed(...)` on any close failure rather than letting it silently replace the primary exception. The output is identical to Level 2's — but achieving it by hand takes considerably more code and is far easier to get subtly wrong (forgetting the reverse order, or forgetting the `null` check on `primary`).

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, calling `manualVersion()` inside a `try`/`catch`.

Inside `manualVersion`, `a` and `b` are constructed (no output; their constructors do nothing special). The inner `try` block immediately throws `RuntimeException("body failed")`. This is caught by `catch (Throwable t)`: `primary` is assigned this exception, and `throw t;` rethrows it — but before it can actually propagate out of the method, the `finally` block runs.

Inside `finally`, the loop iterates over `{b, a}` — deliberately in **reverse** of their construction order, `b` before `a`, matching how try-with-resources closes resources. `b.close()` throws `Exception("B failed to close")`; this is caught by the inner `catch (Throwable closeFailure)`, and since `primary` is non-null (it holds the original `RuntimeException`), `primary.addSuppressed(closeFailure)` attaches `b`'s failure to it. The loop continues to `a.close()`, which throws `Exception("A failed to close")`; this is likewise caught and attached via `addSuppressed`.

Once the `finally` block finishes, the `throw t;` from inside the `catch` block (which was "in progress" before `finally` ran) actually propagates `primary` — now carrying two suppressed exceptions — out of `manualVersion`.

Back in `main`, the `catch (Exception e)` block catches this. `e.getMessage()` returns `"body failed"` (the primary exception's own message, unaffected by the suppressed ones). The `for (Throwable suppressed : e.getSuppressed())` loop then visits the two attached exceptions in the order they were added: `"B failed to close"` first, then `"A failed to close"`.

Expected output:
```
Primary exception: body failed
Suppressed: B failed to close
Suppressed: A failed to close
```

## 7. Gotchas & takeaways

> If you write your own `finally`-block cleanup logic **without** try-with-resources and without using `addSuppressed(...)`, a `close()` (or similar cleanup) failure will **silently replace** the original exception — the classic pre-Java-7 bug this whole mechanism exists to prevent. Always prefer try-with-resources for anything implementing `AutoCloseable`; if you genuinely can't (some legacy resource type, or unusual manual cleanup), replicate the `addSuppressed` pattern by hand exactly as the Level 3 example does, rather than letting a secondary failure clobber the real root cause.

- When both a try-with-resources body and one of its resources' `close()` calls throw, the body's exception becomes primary (what's actually caught) and each `close()` failure is attached via `addSuppressed`, retrievable with `getSuppressed()`.
- Multiple resources' close failures all get collected as suppressed exceptions, in the order they were actually closed (reverse of declaration order).
- This entirely prevents the classic pre-Java-7 failure mode where a cleanup exception would silently replace and hide the real, originally-triggering exception.
- `getSuppressed()` returns an array — often empty, since suppression only happens when *both* the body and a `close()` call fail — so always check it rather than assuming it's empty for thorough logging or diagnostics.
- This mechanism is automatic and free with try-with-resources; manually replicating it (as Level 3 shows) requires meaningfully more code and more discipline to get right, which is a strong argument for using try-with-resources whenever possible rather than hand-written `finally` cleanup.
