---
card: java
gi: 764
slug: scoped-values-2nd-preview
title: Scoped values (2nd preview)
---

## 1. What it is

**Java 22** (JEP 464) is the **second preview** of [scoped values](0753-scoped-values-preview.md), continuing from its first preview round in Java 21. The core model — immutable, block-scoped bindings via `ScopedValue.where(...).run(...)`, automatically unbound when the block exits, designed to propagate cleanly into structured-concurrency subtasks — carries forward unchanged. This round refines two things based on preview feedback: **rebinding** (temporarily overriding an already-bound scoped value for a nested block, then automatically reverting to the outer binding once that nested block exits) and clearer guarantees about scoped-value visibility across the multi-level nested `StructuredTaskScope` trees introduced in this same release's [structured concurrency (2nd preview)](0763-structured-concurrency-2nd-preview.md).

## 2. Why & when

A recurring real pattern didn't fit cleanly into the first preview's model: a scoped value bound once at the top of a request (say, a logging context) sometimes needs to be **temporarily overridden** for one nested section of work — a sub-operation that should log under a more specific context — and then automatically revert to the original binding once that nested section finishes, without the surrounding code needing to remember or restore the old value manually. This round refines `ScopedValue.where(...)` to support exactly this: calling `where(...)` again for a value that's already bound in an enclosing scope creates a new, temporary rebinding scoped to the nested block, and the instant that block exits, the *original* outer binding is restored automatically — mirroring how nested `try` blocks or nested lexical scopes naturally restack and unstack. Combined with this release's refinements to nested `StructuredTaskScope` trees, this round is specifically about making sure context propagation remains correct and predictable as both scoped values and structured concurrency get used together in genuinely nested, non-trivial shapes.

## 3. Core concept

```java
static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

ScopedValue.where(CONTEXT, "request-handler").run(() -> {
    log(); // "request-handler"

    ScopedValue.where(CONTEXT, "payment-subsystem").run(() -> {
        log(); // "payment-subsystem" — temporarily rebinds CONTEXT
    });

    log(); // "request-handler" — automatically reverted once the nested run() exits
});
```

The nested `where(...).run(...)` doesn't need to know or restore the outer value manually — the rebinding is scoped exactly to its own block, exactly like scoped values always have been for a single binding.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scoped value can be temporarily rebound for a nested block, automatically reverting to the outer binding once the nested block exits">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">CONTEXT = "request-handler" (outer binding)</text>

  <rect x="140" y="80" width="360" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="110" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">nested where(...).run(...): CONTEXT = "payment-subsystem"</text>

  <line x1="320" y1="130" x2="320" y2="150" stroke="#8b949e"/>
  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">nested block exits -&gt; CONTEXT reverts to "request-handler" automatically</text>
</svg>

*Rebinding stacks and unstacks exactly like nested lexical scopes — no manual save/restore.*

## 5. Runnable example

Scenario: a request handler logging under an evolving context, growing from a single flat binding into nested rebinding across sub-operations.

### Level 1 — Basic

```java
public class ContextFlat {
    static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

    static void log(String message) {
        System.out.println("[" + CONTEXT.get() + "] " + message);
    }

    public static void main(String[] args) {
        ScopedValue.where(CONTEXT, "request-handler").run(() -> {
            log("started");
            log("finished");
        });
    }
}
```

**How to run:** `java --enable-preview --source 22 ContextFlat.java` (JDK 22+).

This is the single-binding pattern from the first preview round — one `CONTEXT` value bound for the whole block, unchanged for its entire duration.

### Level 2 — Intermediate

```java
public class ContextRebind {
    static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

    static void log(String message) {
        System.out.println("[" + CONTEXT.get() + "] " + message);
    }

    public static void main(String[] args) {
        ScopedValue.where(CONTEXT, "request-handler").run(() -> {
            log("started");

            ScopedValue.where(CONTEXT, "payment-subsystem").run(() -> {
                log("charging card");
            });

            log("finished"); // back to "request-handler" automatically
        });
    }
}
```

**How to run:** `java --enable-preview --source 22 ContextRebind.java`.

The real-world concern added: a nested `where(...).run(...)` temporarily rebinds `CONTEXT` to `"payment-subsystem"` just for the charge-card sub-operation, and the surrounding `"request-handler"` binding automatically resumes the moment that nested block exits — no manual tracking of "what was the context before I overrode it" anywhere in the code.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ContextNestedConcurrent {
    static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

    static void log(String message) {
        System.out.println("[" + CONTEXT.get() + "] " + message);
    }

    static void chargeCard() throws Exception {
        ScopedValue.where(CONTEXT, "payment-subsystem").run(() -> {
            log("validating card");
            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
                var fraudCheck = scope.fork(() -> {
                    log("running fraud check"); // sees "payment-subsystem", forked within it
                    return "clear";
                });
                try {
                    scope.join();
                    scope.throwIfFailed();
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
                log("fraud check result: " + fraudCheck.get());
            }
        });
    }

    public static void main(String[] args) throws Exception {
        ScopedValue.where(CONTEXT, "request-handler").run(() -> {
            log("started");
            try {
                chargeCard();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
            log("finished");
        });
    }
}
```

**How to run:** `java --enable-preview --source 22 --add-modules jdk.incubator.concurrent ContextNestedConcurrent.java`.

This adds the production-flavored hard case: the rebound `"payment-subsystem"` context is visible not just to sequential code inside its `run(...)` block, but to a **subtask forked from a `StructuredTaskScope`** opened within that same block — demonstrating that rebinding composes correctly with structured concurrency's context propagation, the exact combination this round's refinements targeted.

## 6. Walkthrough

Tracing `ContextNestedConcurrent.main`:

1. `main` binds `CONTEXT` to `"request-handler"` and logs `"started"` — printing `[request-handler] started`.
2. It calls `chargeCard()`. Inside, a nested `ScopedValue.where(CONTEXT, "payment-subsystem").run(...)` temporarily rebinds `CONTEXT`, and `log("validating card")` inside that block prints `[payment-subsystem] validating card`.
3. Still within the rebound block, a `StructuredTaskScope` opens and forks a `fraudCheck` subtask. Because this subtask is forked **within** the dynamic extent of the rebound `run(...)` block, it inherits the **rebound** value, `"payment-subsystem"`, not the original outer `"request-handler"` binding — `log("running fraud check")` inside the subtask prints `[payment-subsystem] running fraud check`.
4. `scope.join()` waits for the subtask to finish; `scope.throwIfFailed()` finds nothing to re-throw. `log("fraud check result: clear")` runs back on the original thread, still within the rebound block, printing `[payment-subsystem] fraud check result: clear`.
5. The nested `run(...)` block (from step 2) exits, and `CONTEXT`'s binding automatically reverts to `"request-handler"` — no code in `chargeCard` or `main` had to save or restore this manually.
6. Back in `main`, `log("finished")` runs after `chargeCard()` returns, printing `[request-handler] finished` — confirming the rebinding was fully undone once its block ended.

Expected output:
```
[request-handler] started
[payment-subsystem] validating card
[payment-subsystem] running fraud check
[payment-subsystem] fraud check result: clear
[request-handler] finished
```

## 7. Gotchas & takeaways

> **Gotcha:** rebinding creates a **new** binding scoped to the nested block — it does not mutate the outer binding in place, and there is no way to "peek" at or restore an outer binding except by simply letting the nested block end naturally. Code that tries to manually save `CONTEXT.get()` before rebinding and pass it around defeats the purpose; let the automatic restoration handle it.

- Second preview round, Java 22 — adds rebinding (nested `where(...)` for an already-bound value) and clarifies propagation through nested `StructuredTaskScope` trees.
- A rebinding is automatically undone the instant its `run`/`call` block exits, restoring whatever binding was in effect before it — exactly like nested lexical scoping.
- Subtasks forked from a `StructuredTaskScope` opened within a rebound block see the **rebound** value, not the original outer one.
- Still a preview — continues converging alongside [structured concurrency (2nd preview)](0763-structured-concurrency-2nd-preview.md) toward eventual standardization of both features together.
- Prefer scoped-value rebinding over manually saving and restoring a value (e.g., via a mutable field) whenever a nested section of code needs a temporarily different context.
