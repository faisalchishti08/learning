---
card: java
gi: 787
slug: structured-concurrency-4th-preview
title: Structured concurrency (4th preview)
---

## 1. What it is

**Java 24** (JEP 499) is the **fourth preview** of [structured concurrency](0777-structured-concurrency-3rd-preview.md), carrying forward the `StructuredTaskScope.open(Joiner)` API redesign introduced in Java 23's third preview with no further shape changes: `Joiner`, `Subtask<T>` with its `state()`/`get()`/`exception()` accessors, and the built-in `Joiner.awaitAllSuccessfulOrThrow()`/`awaitAll()`/`anySuccessfulResultOrThrow()` factories all behave exactly as they did in the third preview. This round is about **stability confirmation** after a major redesign — proving the new `Joiner`-based shape holds up under continued real-world use — held in lockstep with [scoped values' own fourth preview](0786-scoped-values-4th-preview.md) toward eventual joint standardization.

## 2. Why & when

A major API redesign, like the third preview's move from scope subclassing to `Joiner`, typically needs at least one calm, unchanged follow-up round before standardization — not because problems were found, but because giving the ecosystem a full release cycle to migrate existing code and report friction is exactly how the JDK validates that a redesign was the right call before locking it in permanently. The fourth preview is that calm round: existing `Joiner`-based code from Java 23 needs no changes at all to compile and run under Java 24's preview, and the practical guidance for anyone adopting structured concurrency today is to build directly against the `open(Joiner)` shape, since it's now had two consecutive rounds of stability and is very unlikely to change again before standardization.

## 3. Core concept

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;

try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAllSuccessfulOrThrow())) {
    var user = scope.fork(() -> fetchUser());
    var orders = scope.fork(() -> fetchOrders());

    scope.join(); // unchanged from the 3rd preview

    combine(user.get(), orders.get());
}
```

Identical to the third preview's shape — no source changes needed for code already migrated to `open(Joiner)`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="After the major redesign in the third preview, the fourth preview round keeps the StructuredTaskScope.open(Joiner) API completely unchanged, confirming its stability before standardization" >
  <rect x="20" y="20" width="280" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="160" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 23: 3rd preview</text>
  <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">major redesign: open(Joiner)</text>

  <line x1="300" y1="47" x2="350" y2="47" stroke="#6db33f" stroke-width="2" marker-end="url(#a787)"/>
  <defs><marker id="a787" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>

  <rect x="360" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 24: 4th preview</text>
  <text x="500" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no changes — stability confirmed</text>

  <text x="320" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">An unchanged follow-up round is the JDK's way of validating a redesign before standardizing it</text>
</svg>

*Two consecutive rounds with an identical API shape is the strongest signal a preview feature can give before standardization.*

## 5. Runnable example

Scenario: a dashboard fetch combining a user profile and an orders list with a custom quorum policy, confirming the third preview's full API surface — including custom `Joiner` implementations — carries forward unchanged into the fourth preview.

### Level 1 — Basic

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;

public class DashboardFourthPreviewBasic {
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
            var user = scope.fork(DashboardFourthPreviewBasic::fetchUser);
            var orders = scope.fork(DashboardFourthPreviewBasic::fetchOrders);

            scope.join();

            System.out.println(user.get() + " / " + orders.get());
        }
    }
}
```

**How to run:** `java --enable-preview --source 24 DashboardFourthPreviewBasic.java` (JDK 24+).

Identical code to the third preview's basic example — confirms nothing needed to change to move from Java 23's preview to Java 24's.

### Level 2 — Intermediate

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;

public class DashboardFourthPreviewState {
    static String fetchUser() throws InterruptedException {
        Thread.sleep(100);
        return "user:ada";
    }

    static String fetchOrders() {
        throw new RuntimeException("orders service unavailable");
    }

    public static void main(String[] args) throws Exception {
        try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAll())) {
            Subtask<String> user = scope.fork(DashboardFourthPreviewState::fetchUser);
            Subtask<String> orders = scope.fork(DashboardFourthPreviewState::fetchOrders);

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

**How to run:** `java --enable-preview --source 24 DashboardFourthPreviewState.java`.

The real-world concern added: `Subtask.state()`-based inspection under `Joiner.awaitAll()`, unchanged from the third preview — confirms the `SUCCESS`/`FAILED`/`UNAVAILABLE` state machine carries forward exactly.

### Level 3 — Advanced

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Joiner;
import java.util.concurrent.StructuredTaskScope.Subtask;
import java.util.concurrent.StructuredTaskScope.Subtask.State;
import java.util.*;

public class DashboardFourthPreviewQuorum {
    static <T> Joiner<T, List<T>> quorumOf(int required) {
        return new Joiner<T, List<T>>() {
            private final List<T> successes = Collections.synchronizedList(new ArrayList<>());

            @Override
            public boolean onComplete(Subtask<? extends T> subtask) {
                if (subtask.state() == State.SUCCESS) {
                    successes.add(subtask.get());
                }
                return successes.size() >= required;
            }

            @Override
            public List<T> result() { return List.copyOf(successes); }
        };
    }

    static String fetchMirror(String name, long delayMs, boolean fail) throws InterruptedException {
        Thread.sleep(delayMs);
        if (fail) throw new RuntimeException(name + " failed");
        return name;
    }

    public static void main(String[] args) throws Exception {
        try (var scope = StructuredTaskScope.open(DashboardFourthPreviewQuorum.<String>quorumOf(2))) {
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

**How to run:** `java --enable-preview --source 24 DashboardFourthPreviewQuorum.java`.

This adds the production-flavored hard case: the exact **custom `Joiner`** quorum policy from the third preview, unmodified — proof that not just the built-in policies, but the full extensibility surface for writing your own `Joiner`, remains stable and unchanged across this fourth preview round.

## 6. Walkthrough

Tracing `DashboardFourthPreviewQuorum.main`:

1. `main` opens a scope with a custom quorum-of-2 `Joiner` and forks four subtasks with staggered delays: `mirror-B` (50ms, succeeds), `mirror-C` (100ms, fails), `mirror-A` (300ms, succeeds), `mirror-D` (400ms, succeeds).
2. As each finishes, `onComplete` runs in completion order: `mirror-B` succeeds first, added to `successes` (size 1), quorum not yet met.
3. `mirror-C` fails, contributes nothing, quorum still not met.
4. `mirror-A` succeeds, `successes` reaches size 2, meeting the quorum — `onComplete` returns `true`.
5. `scope.join()` returns without waiting for `mirror-D`, which gets cancelled as part of the scope's cleanup.
6. `join()`'s return value comes from `result()`: `["mirror-B", "mirror-A"]`.

Expected output:
```
quorum reached with: [mirror-B, mirror-A]
```

## 7. Gotchas & takeaways

> **Gotcha:** "unchanged for a second round" is strong evidence of stability, but until the final standardization JEP actually ships, `--enable-preview` remains mandatory and the API is technically still subject to change — don't drop the preview flag from build configurations prematurely just because two rounds in a row showed no differences.

- Fourth preview in Java 24 (JEP 499) — **no API changes** from Java 23's [third preview](0777-structured-concurrency-3rd-preview.md); still requires `--enable-preview`.
- `StructuredTaskScope.open(Joiner)`, `Subtask<T>`, and the built-in and custom `Joiner` extensibility model all carry forward exactly as they were.
- Held in lockstep with [scoped values' fourth preview](0786-scoped-values-4th-preview.md) — both features are expected to standardize together.
- Two consecutive unchanged preview rounds following a major redesign is the strongest practical signal that the redesign is settling into its final shape.
- Code migrated to the third preview's `open(Joiner)` API needs no further changes to compile and run under the fourth preview.
