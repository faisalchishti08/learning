---
card: java
gi: 777
slug: structured-concurrency-3rd-preview
title: Structured concurrency (3rd preview)
---

## 1. What it is

**Java 23** (JEP 480) is the **third preview** of [structured concurrency](0763-structured-concurrency-2nd-preview.md), and unlike the previous round, it brings a **real API redesign**. The old model — subclassing `StructuredTaskScope.ShutdownOnFailure`/`ShutdownOnSuccess` and constructing them directly with `new` — is replaced by a **`Joiner`** strategy object passed to a new static factory, `StructuredTaskScope.open(joiner)`. `scope.fork(...)` now returns a `Subtask<T>` (instead of a `Future<T>`), and the built-in strategies become `Joiner.awaitAllSuccessfulOrThrow()`, `Joiner.awaitAll()`, and `Joiner.anySuccessfulResultOrThrow()`. The underlying idea — subtasks forked inside a scope can never outlive it — is unchanged; only the API surface for choosing *how* the scope waits for and reacts to its subtasks has been reshaped.

## 2. Why & when

Subclassing `ShutdownOnFailure`/`ShutdownOnSuccess` worked for the two built-in policies, but it didn't scale to custom policies cleanly — a third-party "wait for the first two successes" or "wait for a quorum" policy meant writing your own subclass of `StructuredTaskScope`, overriding its internals, which is a much heavier lift than implementing a small interface. JEP 480's redesign extracts the "how do I combine subtask results and decide when to stop waiting" logic into a standalone `Joiner<T, R>` interface, and makes `StructuredTaskScope` itself effectively final and constructed only via `open(...)`. That's a cleaner separation: the scope's job is purely "manage subtask lifetimes and cancellation," and the joiner's job is purely "decide what `join()` returns and when the scope should shut down early." It also fixes an ergonomic rough edge — `Subtask<T>` (replacing raw `Future<T>`) exposes a `state()` (`SUCCESS`, `FAILED`, `UNAVAILABLE`) alongside `get()`, so code inspecting a subtask's outcome doesn't need to catch exceptions from `Future.get()` just to check whether it succeeded.

## 3. Core concept

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;

try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAllSuccessfulOrThrow())) {
    var user = scope.fork(() -> fetchUser());
    var orders = scope.fork(() -> fetchOrders());

    scope.join(); // joiner decides: wait for both, throw if either fails

    combine(user.get(), orders.get());
}
```

`StructuredTaskScope.open(...)` replaces `new StructuredTaskScope.ShutdownOnFailure()`; the `Joiner` (here, `awaitAllSuccessfulOrThrow()`) now carries the waiting/failure policy that used to live in the subclass itself.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The third preview replaces subclassing StructuredTaskScope with passing a Joiner strategy object to a static open factory method">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#0f1620" stroke="#f85149"/>
  <text x="160" y="45" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">old: new ShutdownOnFailure()</text>
  <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">policy baked into a subclass</text>

  <rect x="340" y="20" width="280" height="60" rx="8" fill="#0f1620" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">new: StructuredTaskScope.open(joiner)</text>
  <text x="480" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">policy is a pluggable Joiner object</text>

  <rect x="120" y="120" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="210" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Future&lt;T&gt; (old fork result)</text>

  <rect x="340" y="120" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="430" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Subtask&lt;T&gt; (new fork result)</text>

  <text x="320" y="185" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same "never outlive the scope" guarantee, reshaped API surface</text>
</svg>

*A `Joiner` now owns the waiting/failure policy; `fork` returns a `Subtask` with an explicit `state()`.*

## 5. Runnable example

Scenario: a dashboard fetch combining a user profile and an orders list, growing from the redesigned basic API into a custom `Joiner` that implements a policy the built-ins don't offer.

### Level 1 — Basic

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;

public class DashboardOpenBasic {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(100);
        return "user:ada";
    }

    static String fetchOrders() throws InterruptedException {
        Thread.sleep(150);
        return "orders:[42,43]";
    }

    public static void main(String[] args) throws Exception {
        try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAllSuccessfulOrThrow())) {
            var user = scope.fork(DashboardOpenBasic::fetchUser);
            var orders = scope.fork(DashboardOpenBasic::fetchOrders);

            scope.join();

            System.out.println(user.get() + " / " + orders.get());
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 DashboardOpenBasic.java` (JDK 23+).

`StructuredTaskScope.open(Joiner.awaitAllSuccessfulOrThrow())` replaces `new StructuredTaskScope.ShutdownOnFailure()` — same behavior (wait for both subtasks, throw if either fails), reshaped as a static factory taking a policy object instead of a subclass.

### Level 2 — Intermediate

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;

public class DashboardSubtaskState {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(100);
        return "user:ada";
    }

    static String fetchOrders() {
        throw new RuntimeException("orders service unavailable");
    }

    public static void main(String[] args) throws Exception {
        try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAll())) {
            Subtask<String> user = scope.fork(DashboardSubtaskState::fetchUser);
            Subtask<String> orders = scope.fork(DashboardSubtaskState::fetchOrders);

            scope.join();

            for (var subtask : new Subtask<?>[]{user, orders}) {
                switch (subtask.state()) {
                    case SUCCESS -> System.out.println("ok: " + subtask.get());
                    case FAILED -> System.out.println("failed: " + subtask.exception().getMessage());
                    case UNAVAILABLE -> System.out.println("unavailable");
                }
            }
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 DashboardSubtaskState.java`.

The real-world concern added: `Joiner.awaitAll()` waits for **every** subtask regardless of individual failures (unlike `awaitAllSuccessfulOrThrow`, which throws on the first failure), and each `Subtask<T>`'s `state()` is inspected directly — `SUCCESS`, `FAILED`, or `UNAVAILABLE` — replacing the old pattern of calling `Future.get()` inside a `try`/`catch` just to distinguish "this subtask failed" from "this subtask succeeded."

### Level 3 — Advanced

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;
import java.util.concurrent.StructuredTaskScope.Subtask.State;
import java.util.*;

public class DashboardQuorumJoiner {
    // Custom Joiner: succeed as soon as at least 2 of N subtasks succeed,
    // cancelling the rest — a policy none of the JDK's built-in Joiners provide.
    static <T> Joiner<T, List<T>> quorumOf(int required) {
        return new Joiner<T, List<T>>() {
            private final List<T> successes = Collections.synchronizedList(new ArrayList<>());

            @Override
            public boolean onComplete(Subtask<? extends T> subtask) {
                if (subtask.state() == State.SUCCESS) {
                    successes.add(subtask.get());
                }
                return successes.size() >= required; // true = stop waiting now
            }

            @Override
            public List<T> result() {
                return List.copyOf(successes);
            }
        };
    }

    static String fetchMirror(String name, long delayMs, boolean fail) throws InterruptedException {
        Thread.sleep(delayMs);
        if (fail) throw new RuntimeException(name + " failed");
        return name;
    }

    public static void main(String[] args) throws Exception {
        try (var scope = StructuredTaskScope.open(DashboardQuorumJoiner.<String>quorumOf(2))) {
            scope.fork(() -> fetchMirror("mirror-A", 300, false));
            scope.fork(() -> fetchMirror("mirror-B", 50, false));
            scope.fork(() -> fetchMirror("mirror-C", 100, true));
            scope.fork(() -> fetchMirror("mirror-D", 400, false));

            List<String> result = scope.join();
            System.out.println("quorum reached with: " + result);
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 DashboardQuorumJoiner.java`.

This adds the production-flavored hard case: a **fully custom `Joiner`** implementing a quorum policy — "return as soon as 2 of 4 mirrors respond successfully, cancel the rest" — something none of the built-in `Joiner` factories express. `onComplete` runs once per finished subtask (as they complete, in completion order, not fork order) and returns `true` the moment the quorum is met, telling the scope to stop waiting and cancel any still-running subtasks; `result()` supplies whatever `scope.join()` ultimately returns.

## 6. Walkthrough

Tracing `DashboardQuorumJoiner.main`:

1. `main` opens a scope with a custom `Joiner` requiring 2 successes, then forks four subtasks with staggered delays: `mirror-B` (50ms, succeeds), `mirror-C` (100ms, fails), `mirror-A` (300ms, succeeds), `mirror-D` (400ms, succeeds).
2. As each subtask finishes, the scope calls the joiner's `onComplete(subtask)` **in completion order**, not fork order — `mirror-B` finishes first (50ms) and succeeds, so `onComplete` adds `"mirror-B"` to `successes` (now size 1) and returns `false` (quorum of 2 not yet met, keep waiting).
3. Next, `mirror-C` finishes (100ms) but with `state() == FAILED` — `onComplete`'s `if` branch is skipped (no addition to `successes`), and it returns `false` again (still only 1 success).
4. Next, `mirror-A` finishes (300ms) and succeeds — `successes` becomes `["mirror-B", "mirror-A"]`, size 2, meeting the quorum — `onComplete` returns `true`, telling the scope its waiting condition is satisfied.
5. Because the joiner signaled completion, `scope.join()` returns **without** waiting for `mirror-D` (400ms) — and as part of the scope's cleanup (on exiting the `try`-with-resources block), any subtask still running, here `mirror-D`, is cancelled.
6. `scope.join()`'s return value comes from the joiner's `result()` method, which returns an immutable copy of `successes`: `["mirror-B", "mirror-A"]`.
7. `main` prints the quorum result — reflecting whichever two mirrors happened to succeed first, not necessarily the two forked first.

Expected output (values, but not necessarily order, are deterministic given these fixed delays):
```
quorum reached with: [mirror-B, mirror-A]
```

## 7. Gotchas & takeaways

> **Gotcha:** `onComplete` runs on whichever thread completes each subtask, potentially **concurrently** for different subtasks completing at nearly the same time — mutating shared state inside a custom `Joiner` (like the `successes` list above) needs to be thread-safe (hence `Collections.synchronizedList`), even though the *scope's* own cancellation bookkeeping is handled safely for you. A custom `Joiner` is exactly the kind of code the rest of structured concurrency is designed to let you avoid writing — write it carefully.

- Third preview in Java 23 (JEP 480) — a **real API redesign** from the [second preview](0763-structured-concurrency-2nd-preview.md): `StructuredTaskScope.open(joiner)` replaces subclassing `ShutdownOnFailure`/`ShutdownOnSuccess`.
- `scope.fork(...)` now returns `Subtask<T>` (with an explicit `state()`: `SUCCESS`, `FAILED`, `UNAVAILABLE`) instead of a raw `Future<T>`.
- Built-in policies move to `Joiner` factory methods: `Joiner.awaitAllSuccessfulOrThrow()`, `Joiner.awaitAll()`, `Joiner.anySuccessfulResultOrThrow()`.
- Custom waiting/combining policies are now a matter of implementing the small `Joiner` interface (`onComplete`, `result`) rather than subclassing the scope itself.
- The core safety guarantee — subtasks can never outlive the scope that forked them — is completely unchanged by this redesign; only the API for expressing *how* a scope waits and combines results has moved.
