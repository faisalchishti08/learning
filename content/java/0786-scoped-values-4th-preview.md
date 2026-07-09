---
card: java
gi: 786
slug: scoped-values-4th-preview
title: Scoped values (4th preview)
---

## 1. What it is

**Java 24** (JEP 487) is the **fourth preview** of [scoped values](0778-scoped-values-3rd-preview.md), carrying the API forward from Java 23's third preview with no functional changes: `ScopedValue.newInstance()`, `where(...).run(...)`/`.call(...)`, automatic unbinding, and nested rebinding all behave exactly as before. A fourth consecutive preview round is a signal in itself — it means the design has held steady through three rounds of real usage feedback, and the feature is being deliberately kept in lockstep with [structured concurrency's own fourth preview](0787-structured-concurrency-4th-preview.md) in this same release, with both features expected to move toward standardization together rather than independently.

## 2. Why & when

Scoped values and structured concurrency were designed as companion features from the start — a scoped value's main reason for existing is to propagate immutable context cleanly into concurrently forked subtasks — so it makes sense for the JDK to hold both in preview until they're ready to standardize as a pair, rather than finalizing one while the other is still settling. By the fourth round, the risk being managed isn't "does the core API work" (three rounds have answered that), it's "has structured concurrency's API shape (which changed substantially in its own third preview, replacing scope subclassing with `Joiner`) fully stabilized," since scoped values' main real-world use case is bound up with it. Application code adopting scoped values today — for request-scoped logging context, feature flags, or configuration that needs to flow into fanned-out concurrent work — can treat the API as stable in practice, even while it technically remains a preview feature pending that joint standardization.

## 3. Core concept

```java
static final ScopedValue<String> FEATURE_FLAGS = ScopedValue.newInstance();

ScopedValue.where(FEATURE_FLAGS, "new-checkout-flow").run(() -> {
    try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAllSuccessfulOrThrow())) {
        var task = scope.fork(() -> "flags seen: " + FEATURE_FLAGS.get());
        scope.join();
        System.out.println(task.get()); // "flags seen: new-checkout-flow"
    }
});
```

Unchanged from the third preview: a scoped value bound on the forking thread is visible, correctly, inside a subtask forked through structured concurrency's `open(Joiner)` API.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Scoped values and structured concurrency have both reached a fourth preview round in Java 24, with the JDK holding both features together for joint standardization rather than finalizing either independently">
  <rect x="40" y="20" width="240" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="160" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Scoped values</text>
  <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4th preview, Java 24</text>

  <rect x="360" y="20" width="240" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="480" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Structured concurrency</text>
  <text x="480" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4th preview, Java 24</text>

  <line x1="280" y1="47" x2="360" y2="47" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">held together toward joint standardization</text>

  <text x="320" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Four rounds of stability signal readiness even before the flag requirement is lifted</text>
</svg>

*Two companion features, previewed in lockstep, moving toward standardization as a pair.*

## 5. Runnable example

Scenario: a request handler propagating a feature-flag context into concurrently fetched sub-results, confirming the by-now-familiar propagation guarantee holds unchanged in the fourth preview round.

### Level 1 — Basic

```java
public class FeatureFlagsBasic {
    static final ScopedValue<String> FEATURE_FLAGS = ScopedValue.newInstance();

    public static void main(String[] args) {
        ScopedValue.where(FEATURE_FLAGS, "new-checkout-flow").run(() -> {
            System.out.println("active flags: " + FEATURE_FLAGS.get());
        });
    }
}
```

**How to run:** `java --enable-preview --source 24 FeatureFlagsBasic.java` (JDK 24+).

A single, flat binding — the same fundamental shape every preview round has supported, unchanged since Java 21's first preview.

### Level 2 — Intermediate

```java
public class FeatureFlagsRebind {
    static final ScopedValue<String> FEATURE_FLAGS = ScopedValue.newInstance();

    static void log(String message) {
        System.out.println("[" + FEATURE_FLAGS.get() + "] " + message);
    }

    public static void main(String[] args) {
        ScopedValue.where(FEATURE_FLAGS, "new-checkout-flow").run(() -> {
            log("checkout started");

            ScopedValue.where(FEATURE_FLAGS, "new-checkout-flow,fast-payment").run(() -> {
                log("charging card with fast-payment enabled");
            });

            log("checkout finished"); // reverts automatically
        });
    }
}
```

**How to run:** `java --enable-preview --source 24 FeatureFlagsRebind.java`.

The real-world concern added: nested rebinding for a sub-operation that needs an extended flag set — unchanged behavior from the third preview, confirming the rebinding-and-automatic-reversion guarantee still holds.

### Level 3 — Advanced

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.*;

public class FeatureFlagsFanOut {
    static final ScopedValue<String> FEATURE_FLAGS = ScopedValue.newInstance();

    static String fetch(String label) {
        return label + " [" + FEATURE_FLAGS.get() + "]";
    }

    public static void main(String[] args) throws Exception {
        ScopedValue.where(FEATURE_FLAGS, "new-checkout-flow,fast-payment").run(() -> {
            try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAll())) {
                var cart = scope.fork(() -> fetch("cart"));
                var payment = scope.fork(() -> fetch("payment"));
                var shipping = scope.fork(() -> fetch("shipping"));

                scope.join();

                for (var t : List.of(cart, payment, shipping)) {
                    System.out.println(t.get());
                }
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
```

**How to run:** `java --enable-preview --source 24 FeatureFlagsFanOut.java`.

This adds the production-flavored hard case: **three** concurrent subtasks, each forked through structured concurrency's `open(Joiner.awaitAll())`, each independently reading `FEATURE_FLAGS.get()` on its own virtual thread — every one sees the same binding from the single thread that forked them all, confirming fan-out propagation still holds exactly as it did in the third preview, now on the fourth round of both features together.

## 6. Walkthrough

Tracing `FeatureFlagsFanOut.main`:

1. `main` binds `FEATURE_FLAGS` to `"new-checkout-flow,fast-payment"` on the current thread via `ScopedValue.where(...).run(...)`, then opens a structured concurrency scope with `Joiner.awaitAll()`.
2. Three subtasks are forked — `fetch("cart")`, `fetch("payment")`, `fetch("shipping")` — each running on its own virtual thread as part of the dynamic extent of the still-active `where(...).run(...)` block.
3. Inside each `fetch` call, `FEATURE_FLAGS.get()` reads `"new-checkout-flow,fast-payment"`, even though each runs on a different thread than `main` — the propagation mechanism unchanged across all four preview rounds.
4. `Joiner.awaitAll()` waits for every subtask regardless of individual outcome; here all three succeed, so `scope.join()` returns once all three have finished.
5. `main` iterates the three `Subtask` handles and prints each one's result via `.get()`.

Expected output:
```
cart [new-checkout-flow,fast-payment]
payment [new-checkout-flow,fast-payment]
shipping [new-checkout-flow,fast-payment]
```

## 7. Gotchas & takeaways

> **Gotcha:** four rounds of preview stability is a strong signal, but it's still a preview — code depending on `ScopedValue` in production should keep tracking release notes for the eventual standardization JEP, since minor API adjustments remain possible right up until that final round, even if none have materialized across rounds two through four.

- Fourth preview in Java 24 (JEP 487) — **no API changes** from Java 23's [third preview](0778-scoped-values-3rd-preview.md); still requires `--enable-preview`.
- Held in lockstep with [structured concurrency's own fourth preview](0787-structured-concurrency-4th-preview.md) — both are expected to standardize together, reflecting their designed-as-companions relationship.
- Propagation into subtasks forked via `StructuredTaskScope.open(Joiner...)` remains correct for both single-subtask and fan-out cases, with any `Joiner` policy.
- Four consecutive unchanged rounds is itself useful information: the core API is very unlikely to change further before eventual standardization.
- Bind scoped values before opening a `StructuredTaskScope` so every subtask forked from it inherits the binding automatically, exactly as in prior preview rounds.
