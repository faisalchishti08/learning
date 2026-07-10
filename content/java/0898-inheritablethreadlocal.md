---
card: java
gi: 898
slug: inheritablethreadlocal
title: InheritableThreadLocal
---

## 1. What it is

`InheritableThreadLocal<T>` is a subclass of `ThreadLocal<T>` with one difference: when a thread creates a **child** thread (via `new Thread(...)`), the child automatically inherits a *copy* of the parent thread's value for that variable at the moment of the child's construction — retrieved via an overridable `childValue(T parentValue)` hook (default: just returns the parent's value as-is). A plain `ThreadLocal` gives every thread, parent or child, a completely separate, independently-initialized value; `InheritableThreadLocal` instead propagates the parent's current value down into any thread it spawns.

## 2. Why & when

Use `InheritableThreadLocal` when you have per-thread context that should naturally flow from a parent thread into any worker threads it spawns to help with the same logical unit of work — a request-tracing ID that should appear in logs from any child thread doing sub-work for that request, or a security context that child threads should inherit rather than needing to rediscover. It solves a specific gap plain `ThreadLocal` leaves: without it, a newly created child thread's `ThreadLocal.get()` calls would return the type's default initial value (`null`, or whatever the `withInitial` supplier produces), with no automatic connection to whatever the *creating* thread had set. This only fires once, at child-thread creation time — it's a one-time snapshot copy, not an ongoing link, so later changes to the parent's value are not reflected in already-created children, and changes the child makes to its own inherited copy don't propagate back to the parent either.

## 3. Core concept

```java
static final InheritableThreadLocal<String> TRACE_ID = new InheritableThreadLocal<>();

TRACE_ID.set("trace-abc123"); // set on the current (parent) thread

Thread child = new Thread(() -> {
    System.out.println(TRACE_ID.get()); // automatically inherits "trace-abc123" -- no explicit passing needed
});
child.start();
```

The child thread's inherited value is captured at the moment `new Thread(...)` runs — a snapshot, not a live link back to the parent.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Parent thread sets an InheritableThreadLocal value, then spawns a child thread which automatically receives a copy of that value at creation time; later parent changes do not propagate to the already-created child">
  <rect x="20" y="20" width="220" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Parent: TRACE_ID.set("abc123")</text>

  <rect x="20" y="80" width="220" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Parent: new Thread(...).start()</text>

  <rect x="380" y="80" width="220" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="490" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Child: TRACE_ID.get() = "abc123"</text>

  <line x1="130" y1="60" x2="130" y2="78" stroke="#8b949e" stroke-width="2" marker-end="url(#a30)"/>
  <line x1="240" y1="100" x2="376" y2="100" stroke="#8b949e" stroke-width="2" stroke-dasharray="4" marker-end="url(#a30)"/>
  <text x="308" y="90" fill="#8b949e" font-size="9" font-family="sans-serif">copied at creation</text>

  <rect x="20" y="140" width="220" height="20" fill="none"/>
  <text x="130" y="150" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Parent later: TRACE_ID.set("xyz") -- child STILL sees "abc123"</text>
  <defs><marker id="a30" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The child gets a one-time snapshot at creation — not a live, ongoing connection to the parent's value.*

## 5. Runnable example

Scenario: propagating a request-tracing ID from a main handler thread into worker threads it spawns for sub-tasks, growing from plain `ThreadLocal` (which fails to propagate), to `InheritableThreadLocal` (which does), to a version demonstrating the one-time-snapshot behavior and the `childValue` override for transformation on inheritance.

### Level 1 — Basic

```java
public class PlainThreadLocalDoesNotPropagate {
    static final ThreadLocal<String> TRACE_ID = new ThreadLocal<>(); // does NOT propagate to children

    public static void main(String[] args) throws InterruptedException {
        TRACE_ID.set("trace-abc123");
        System.out.println("main thread trace ID: " + TRACE_ID.get());

        Thread worker = new Thread(() -> {
            System.out.println("worker thread trace ID: " + TRACE_ID.get()); // null -- NOT inherited
        });
        worker.start();
        worker.join();
    }
}
```

**How to run:** `java PlainThreadLocalDoesNotPropagate.java` (JDK 17+).

Expected output:
```
main thread trace ID: trace-abc123
worker thread trace ID: null
```

The plain `ThreadLocal` gives the worker thread its own, entirely separate storage — with nothing ever set on it, `get()` returns `null`, even though the main thread that created it clearly had a trace ID set.

### Level 2 — Intermediate

```java
public class InheritableThreadLocalPropagates {
    static final InheritableThreadLocal<String> TRACE_ID = new InheritableThreadLocal<>();

    public static void main(String[] args) throws InterruptedException {
        TRACE_ID.set("trace-abc123");
        System.out.println("main thread trace ID: " + TRACE_ID.get());

        Thread worker = new Thread(() -> {
            System.out.println("worker thread trace ID: " + TRACE_ID.get()); // automatically inherited!
        });
        worker.start();
        worker.join();
    }
}
```

**How to run:** `java InheritableThreadLocalPropagates.java`.

Expected output:
```
main thread trace ID: trace-abc123
worker thread trace ID: trace-abc123
```

The real-world concern added: the worker thread automatically inherits the exact trace ID the main thread had set at the moment `new Thread(...)` was constructed — no explicit parameter passing or manual propagation code needed.

### Level 3 — Advanced

```java
public class SnapshotBehaviorAndChildValueOverride {
    // Override childValue to derive a NEW value for the child, rather than just copying the parent's exactly --
    // here, appending a sub-task marker to make it clear in logs which thread a message came from.
    static final InheritableThreadLocal<String> TRACE_ID = new InheritableThreadLocal<>() {
        @Override
        protected String childValue(String parentValue) {
            return parentValue + "-subtask";
        }
    };

    public static void main(String[] args) throws InterruptedException {
        TRACE_ID.set("trace-abc123");

        Thread worker = new Thread(() -> {
            System.out.println("worker (at creation time) trace ID: " + TRACE_ID.get());
        });
        worker.start();
        worker.join();

        // Demonstrate the ONE-TIME SNAPSHOT nature: changing the parent's value AFTER a child
        // is created does NOT retroactively affect that already-created child's inherited value.
        TRACE_ID.set("trace-abc123"); // reset to the same base value for a clean second demonstration
        Thread earlyChild = new Thread(() -> {
            try { Thread.sleep(100); } catch (InterruptedException ignored) {}
            System.out.println("early-created child, checked LATER, still sees: " + TRACE_ID.get());
        });
        earlyChild.start();

        Thread.sleep(20); // give earlyChild time to be constructed and start, inheriting the CURRENT value
        TRACE_ID.set("trace-CHANGED"); // parent changes ITS OWN value -- too late to affect earlyChild

        earlyChild.join();
        System.out.println("main thread's own current trace ID: " + TRACE_ID.get());
    }
}
```

**How to run:** `java SnapshotBehaviorAndChildValueOverride.java`.

Expected output:
```
worker (at creation time) trace ID: trace-abc123-subtask
early-created child, checked LATER, still sees: trace-abc123-subtask
main thread's own current trace ID: trace-CHANGED
```

This adds the production-flavored hard case: overriding `childValue()` to *transform* the inherited value rather than copy it verbatim (appending `"-subtask"` here, useful for distinguishing sub-task log lines from the parent's own), and demonstrating that the inheritance is a one-time snapshot taken at thread-construction time — even though `earlyChild` doesn't actually check its value until 100ms later, and the main thread changes its own `TRACE_ID` in the meantime, `earlyChild` still reports the value it inherited at creation, completely unaffected by the parent's later change.

## 6. Walkthrough

Tracing the second half of `SnapshotBehaviorAndChildValueOverride.main`:

1. `TRACE_ID.set("trace-abc123")` sets the main thread's own value.
2. `new Thread(() -> {...})` for `earlyChild` triggers `InheritableThreadLocal`'s internal machinery: at this exact construction moment, it calls `childValue("trace-abc123")` (the overridden version), producing `"trace-abc123-subtask"`, and stores that as `earlyChild`'s own, now entirely independent copy.
3. `earlyChild.start()` begins running the child thread, which immediately sleeps 100ms before checking its value — but the *value it will eventually read* was already fixed at step 2, regardless of what happens next.
4. `Thread.sleep(20)` in `main` ensures `earlyChild` has had a chance to actually be constructed and begin running before `main` proceeds — though by this point in the code, the snapshot has already been taken regardless of timing, since it happens synchronously during the `new Thread(...)` call itself, not lazily on first access.
5. `TRACE_ID.set("trace-CHANGED")` changes only the **main thread's own** value — since `InheritableThreadLocal` copied a value into `earlyChild` at construction time and there is no ongoing link back to the parent, this change has zero effect on `earlyChild`'s already-established, independent copy.
6. When `earlyChild` finally wakes up from its 100ms sleep and calls `TRACE_ID.get()`, it correctly reports `"trace-abc123-subtask"` — the value it inherited at its own creation time, entirely unaffected by the main thread's subsequent change.
7. `main`'s own final `TRACE_ID.get()` correctly reports `"trace-CHANGED"`, its own current value — demonstrating that after the snapshot moment, parent and child `ThreadLocal` storage are completely independent, exactly as with a plain `ThreadLocal`, except for that one initial, one-time copy.

## 7. Gotchas & takeaways

> **Gotcha:** `InheritableThreadLocal` propagation happens only at `Thread` **construction** time, and only for genuine parent→child relationships via `new Thread(...)` — it does **not** work with `ExecutorService`-managed thread pools in the way you might expect, since a pool's worker threads are typically created once, up front, long before any specific task (and its `InheritableThreadLocal` context) exists; a task submitted to an existing pool thread does not trigger any new inheritance at all.

- `InheritableThreadLocal<T>` extends `ThreadLocal<T>`, automatically copying the creating thread's current value into any child thread it spawns via `new Thread(...)`.
- The propagation is a one-time snapshot taken at child construction — later changes to the parent's value never retroactively affect an already-created child, and the child's own changes never propagate back to the parent.
- Override `childValue(T parentValue)` to transform the value on inheritance rather than copying it exactly — useful for appending context markers or deriving a scoped variant.
- It generally does **not** help with thread-pool-based concurrency, since pool threads are typically long-lived and created independently of any specific task's context — for that use case, explicit context-passing (or wrapping submitted tasks to manually copy context) is usually necessary instead.
- For a more careful, structurally safer way to hand off contextual, effectively-final data to child tasks (especially in conjunction with virtual threads and [structured concurrency](0903-structured-concurrency.md)), consider [scoped values](0904-scoped-values.md), a newer JDK feature designed partly to address `InheritableThreadLocal`'s limitations and pitfalls; also review [`ThreadLocal` memory leaks](0899-threadlocal-memory-leaks.md) for a related, important cleanup concern.
