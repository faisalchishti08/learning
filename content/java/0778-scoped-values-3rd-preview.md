---
card: java
gi: 778
slug: scoped-values-3rd-preview
title: Scoped values (3rd preview)
---

## 1. What it is

**Java 23** (JEP 481) is the **third preview** of [scoped values](0764-scoped-values-2nd-preview.md), carried forward from Java 22's second preview with the core API — `ScopedValue.newInstance()`, `ScopedValue.where(...).run(...)`/`.call(...)`, automatic unbinding, and nested rebinding — **functionally unchanged**. What this round confirms and documents is compatibility with [structured concurrency's third preview](0777-structured-concurrency-3rd-preview.md) redesign in this same release: scoped values bound in a thread still propagate correctly into subtasks forked via the new `StructuredTaskScope.open(Joiner)` API, exactly as they did with the older `ShutdownOnFailure`/`ShutdownOnSuccess` subclasses.

## 2. Why & when

Java 23 shipped its **biggest** structured-concurrency API change yet — replacing scope subclassing with the `Joiner`-based `open(...)` factory — in the very same release where scoped values were already relying on structured concurrency's subtask-forking mechanism to propagate context correctly into concurrent work. A third preview round with no scoped-value API changes exists to make sure that redesign didn't quietly break the propagation guarantee: a scoped value bound in the thread that calls `scope.fork(...)` must still be visible, with the correct value, inside whatever runs on the new `Subtask<T>`'s thread — regardless of which `Joiner` policy the scope uses. This matters directly to any code combining the two features (a request-scoped logging context flowing into fanned-out subtasks is the canonical example) — confirming the interaction still holds is exactly the kind of cross-feature verification a preview round is for.

## 3. Core concept

```java
static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

ScopedValue.where(CONTEXT, "request-42").run(() -> {
    try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAllSuccessfulOrThrow())) {
        var task = scope.fork(() -> CONTEXT.get()); // sees "request-42" on its own thread
        scope.join();
        System.out.println(task.get()); // "request-42"
    }
});
```

The subtask forked through the new `StructuredTaskScope.open(Joiner...)` API still inherits `CONTEXT`'s binding from the thread that forked it — the redesigned scope API doesn't change scoped-value propagation.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scoped value bound on the forking thread propagates into a subtask launched through the redesigned StructuredTaskScope.open(Joiner) API exactly as it did with the old scope subclasses">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">CONTEXT = "request-42" bound on the forking thread</text>

  <rect x="60" y="90" width="220" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="170" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">old: ShutdownOnFailure scope</text>
  <text x="170" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">subtask sees CONTEXT correctly</text>

  <rect x="360" y="90" width="220" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="470" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">new: open(Joiner) scope</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">subtask sees CONTEXT correctly</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Propagation is verified unchanged across the redesigned scope API</text>
</svg>

*Whichever `StructuredTaskScope` API shape forks a subtask, scoped-value propagation into it works the same way.*

## 5. Runnable example

Scenario: a request handler propagating a logging context into concurrently fetched sub-results, growing from a single subtask into a custom-`Joiner` fan-out where every subtask must still see the correct context.

### Level 1 — Basic

```java
public class ContextIntoSubtaskBasic {
    static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

    public static void main(String[] args) throws Exception {
        ScopedValue.where(CONTEXT, "request-42").run(() -> {
            try (var scope = StructuredTaskScope.open(
                    StructuredTaskScope.Joiner.<String>awaitAllSuccessfulOrThrow())) {
                var task = scope.fork(() -> "seen from subtask: " + CONTEXT.get());
                scope.join();
                System.out.println(task.get());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
```

**How to run:** `java --enable-preview --source 23 ContextIntoSubtaskBasic.java` (JDK 23+).

`CONTEXT` is bound on the thread running `main`'s lambda; the subtask forked via the redesigned `StructuredTaskScope.open(...)` API reads `CONTEXT.get()` on its own (different) thread and still sees `"request-42"` — confirming propagation into the new API.

### Level 2 — Intermediate

```java
public class ContextIntoMultipleSubtasks {
    static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

    static String fetch(String label) {
        return label + " [" + CONTEXT.get() + "]";
    }

    public static void main(String[] args) throws Exception {
        ScopedValue.where(CONTEXT, "request-42").run(() -> {
            try (var scope = StructuredTaskScope.open(
                    StructuredTaskScope.Joiner.<String>awaitAll())) {
                var user = scope.fork(() -> fetch("user"));
                var orders = scope.fork(() -> fetch("orders"));
                var inventory = scope.fork(() -> fetch("inventory"));

                scope.join();

                for (var t : new java.util.List.of(user, orders, inventory).stream()
                        .map(s -> (StructuredTaskScope.Subtask<String>) s).toList()) {
                    System.out.println(t.get());
                }
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
```

**How to run:** `java --enable-preview --source 23 ContextIntoMultipleSubtasks.java`.

The real-world concern added: **three** concurrent subtasks, each running on its own virtual thread, each independently calling `CONTEXT.get()` — every one of them sees the same `"request-42"` binding from the single thread that forked them all, confirming that fan-out (not just a single subtask) propagates the scoped value consistently under `Joiner.awaitAll()`.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;

public class ContextWithCustomJoiner {
    static final ScopedValue<String> CONTEXT = ScopedValue.newInstance();

    static <T> Joiner<T, List<T>> collectAllSuccesses() {
        return new Joiner<T, List<T>>() {
            private final List<T> results = Collections.synchronizedList(new ArrayList<>());

            @Override
            public boolean onComplete(Subtask<? extends T> subtask) {
                if (subtask.state() == Subtask.State.SUCCESS) {
                    results.add(subtask.get());
                }
                return false; // never stop early — wait for every subtask
            }

            @Override
            public List<T> result() { return List.copyOf(results); }
        };
    }

    static String fetch(String label) {
        return label + " [" + CONTEXT.get() + "]";
    }

    public static void main(String[] args) throws Exception {
        ScopedValue.where(CONTEXT, "request-42").run(() -> {
            try (var scope = StructuredTaskScope.open(ContextWithCustomJoiner.<String>collectAllSuccesses())) {
                scope.fork(() -> fetch("user"));
                scope.fork(() -> fetch("orders"));
                scope.fork(() -> { throw new RuntimeException("inventory down"); });

                List<String> results = scope.join();
                System.out.println("collected: " + results);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }
}
```

**How to run:** `java --enable-preview --source 23 ContextWithCustomJoiner.java`.

This adds the production-flavored hard case: a **custom `Joiner`** (`collectAllSuccesses`) whose `onComplete` runs on whichever thread finishes each subtask — and even inside that joiner callback, subtasks that call `CONTEXT.get()` (via `fetch(...)`, which runs *inside* the forked task, not inside `onComplete` itself) still see `"request-42"` correctly, showing that scoped-value propagation is tied to the **forked task's** execution, not to which `Joiner` implementation is orchestrating completion around it.

## 6. Walkthrough

Tracing `ContextWithCustomJoiner.main`:

1. `main` binds `CONTEXT` to `"request-42"` on the current thread via `ScopedValue.where(...).run(...)`, then opens a scope with the custom `collectAllSuccesses()` joiner.
2. Three subtasks are forked: `fetch("user")`, `fetch("orders")`, and one that immediately throws. Each runs on its own virtual thread, spawned as part of the *dynamic extent* of the still-active `where(...).run(...)` block on the forking thread — this is exactly the propagation mechanism scoped values rely on, unchanged by the `Joiner` redesign.
3. Inside `fetch("user")`, `CONTEXT.get()` reads `"request-42"` even though this code runs on a different thread than `main` — because scoped-value propagation into `StructuredTaskScope` subtasks was designed to work this way from the very first preview, and this round confirms it still holds under `open(Joiner)`.
4. As each subtask completes, the scope invokes `onComplete(subtask)` on the joiner: for `"user"` and `"orders"`, `subtask.state() == SUCCESS`, so their results are added to `results`; for the failing subtask, `state() == FAILED`, so nothing is added. Every call returns `false`, telling the scope to keep waiting for all three regardless of individual outcomes.
5. Once all three subtasks have completed, `scope.join()` returns, calling the joiner's `result()`, which returns an immutable copy of the two successful results.
6. `main` prints the collected list — the failed `"inventory down"` subtask contributed nothing, but didn't stop the other two from completing and being collected.

Expected output:
```
collected: [user [request-42], orders [request-42]]
```

## 7. Gotchas & takeaways

> **Gotcha:** the joiner's `onComplete` callback and the subtask's own body run in different places — `onComplete` doesn't automatically inherit whatever a subtask observed via `CONTEXT.get()`, and calling `CONTEXT.get()` *inside* `onComplete` itself is only meaningful if `onComplete` runs within the same scoped-value binding's dynamic extent (which it does here, since the whole scope lives inside the `where(...).run(...)` block) — don't assume a `Joiner`'s internals automatically see whatever a subtask saw just because both are "part of the same scope."

- Third preview in Java 23 (JEP 481) — **no scoped-value API changes** from Java 22's [second preview](0764-scoped-values-2nd-preview.md); confirms compatibility with [structured concurrency's redesigned `open(Joiner)` API](0777-structured-concurrency-3rd-preview.md) in this same release.
- A scoped value bound on the thread that calls `scope.fork(...)` remains visible, with the correct value, inside the forked subtask — regardless of which `Joiner` (built-in or custom) the scope uses.
- This holds for fan-out to many subtasks at once, and for custom `Joiner` implementations, not just the built-in policies.
- Still a preview feature, progressing alongside structured concurrency toward eventual joint standardization.
- When combining the two features, bind scoped values *before* opening the `StructuredTaskScope`, so every subtask forked from it inherits the binding automatically.
