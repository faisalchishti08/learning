---
card: java
gi: 853
slug: thread-scheduling-priorities
title: Thread scheduling & priorities
---

## 1. What it is

Every `Thread` has a priority, an integer between `Thread.MIN_PRIORITY` (1) and `Thread.MAX_PRIORITY` (10), defaulting to `Thread.NORM_PRIORITY` (5), settable via `setPriority(int)`. This priority is passed through to the underlying operating system's thread scheduler as a **hint** about relative importance — but the JVM specification explicitly does not guarantee any particular scheduling behavior based on it. Different operating systems map Java's 1–10 priority scale onto their own native scheduling mechanisms differently (or, on some platforms, largely ignore it), meaning identical priority-setting code can produce noticeably different actual scheduling behavior across different machines, JVMs, and OS versions.

## 2. Why & when

Thread priority exists as a mechanism for expressing relative importance when a program has genuine reason to believe some threads' work matters more than others' — a UI-responsiveness thread versus a low-priority background indexing task, for instance. But because the JVM specification treats it as merely advisory, priority must never be used as a substitute for correct synchronization or as a way to guarantee execution order — a higher-priority thread is not guaranteed to run before, or more often than, a lower-priority one; it's only *more likely* to be favored by whatever scheduler the underlying OS actually uses, and that likelihood itself varies by platform. The reliable tools for controlling execution order and coordination are the ones covered elsewhere in this section — proper synchronization, `join()`, and structured concurrency mechanisms — not priority tuning, which should be treated as a soft, best-effort hint at most, applied cautiously and never relied upon for correctness.

## 3. Core concept

```java
Thread highPriority = new Thread(() -> { /* work */ });
Thread lowPriority = new Thread(() -> { /* work */ });

highPriority.setPriority(Thread.MAX_PRIORITY); // 10 -- a HINT, not a guarantee
lowPriority.setPriority(Thread.MIN_PRIORITY);  // 1 -- also just a hint

highPriority.start();
lowPriority.start();
// There is NO guarantee highPriority finishes first, runs more often, or gets more CPU time.
// The actual scheduling behavior depends entirely on the OS and JVM's underlying implementation.
```

Nothing in this code guarantees any particular execution order or CPU allocation — the priority values are merely suggestions passed down to a scheduler whose actual behavior is implementation-defined and platform-dependent.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Thread priority is passed to the OS scheduler as an advisory hint; the JVM specification does not guarantee any specific resulting scheduling behavior">
  <rect x="40" y="30" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">thread.setPriority(10)</text>
  <text x="150" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a HINT to the JVM</text>

  <line x1="260" y1="55" x2="340" y2="55" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a853)"/>

  <rect x="350" y="30" width="220" height="55" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="460" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OS thread scheduler</text>
  <text x="460" y="72" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">behavior varies BY PLATFORM</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No guaranteed outcome — never rely on priority for correctness or deterministic ordering</text>

  <defs><marker id="a853" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Priority is a hint handed to a platform-dependent scheduler — never a guarantee about actual execution order or CPU share.*

## 5. Runnable example

Scenario: two counting threads set to different priorities, growing from basic priority-setting, through observing that outcomes are not reliably ordered by priority, to the correct alternative — using proper coordination mechanisms instead of priority tuning to express real importance.

### Level 1 — Basic

```java
public class PriorityBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> System.out.println("running with priority: " + Thread.currentThread().getPriority()));

        System.out.println("default priority before setting: " + t.getPriority());
        t.setPriority(Thread.MAX_PRIORITY);
        System.out.println("priority after setPriority(MAX_PRIORITY): " + t.getPriority());

        t.start();
        t.join();
    }
}
```

**How to run:** `java PriorityBasic.java` (JDK 17+).

Expected output:
```
default priority before setting: 5
priority after setPriority(MAX_PRIORITY): 10
running with priority: 10
```

Setting and reading priority works exactly as expected at the API level — the value is stored and retrievable — but this alone says nothing about how the underlying scheduler will actually treat this thread relative to others.

### Level 2 — Intermediate

```java
import java.util.concurrent.atomic.*;

public class PriorityNotAGuarantee {
    public static void main(String[] args) throws InterruptedException {
        AtomicLong highPriorityCount = new AtomicLong();
        AtomicLong lowPriorityCount = new AtomicLong();
        AtomicBoolean keepRunning = new AtomicBoolean(true);

        Thread highPriority = new Thread(() -> {
            while (keepRunning.get()) highPriorityCount.incrementAndGet();
        });
        Thread lowPriority = new Thread(() -> {
            while (keepRunning.get()) lowPriorityCount.incrementAndGet();
        });

        highPriority.setPriority(Thread.MAX_PRIORITY);
        lowPriority.setPriority(Thread.MIN_PRIORITY);

        highPriority.start();
        lowPriority.start();
        Thread.sleep(200);
        keepRunning.set(false);
        highPriority.join();
        lowPriority.join();

        System.out.println("high-priority thread's count: " + highPriorityCount.get());
        System.out.println("low-priority thread's count: " + lowPriorityCount.get());
        System.out.println("-> the HIGHER count is NOT guaranteed to belong to the higher-priority thread");
        System.out.println("-> this result is platform-dependent and must never be relied upon");
    }
}
```

**How to run:** `java PriorityNotAGuarantee.java`. Results vary significantly by operating system, JVM, and machine — on some platforms the high-priority thread's count may indeed be noticeably larger; on others, the two counts may be nearly identical, or even reversed. Both outcomes are valid demonstrations of the same underlying point.

Expected output shape (illustrative only — actual numbers and which count is larger both vary by platform):
```
high-priority thread's count: 48213891
low-priority thread's count: 47998102
-> the HIGHER count is NOT guaranteed to belong to the higher-priority thread
-> this result is platform-dependent and must never be relied upon
```

The real-world concern added: directly measuring whether priority actually produces a meaningfully different CPU allocation — and finding that the answer is "it depends entirely on the platform," which is exactly the JVM specification's own stated position. Code that assumes `MAX_PRIORITY` guarantees noticeably more CPU time, or guarantees the high-priority thread "wins" any particular race, is making an assumption the specification explicitly does not support.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class ProperCoordinationInstead {
    public static void main(String[] args) throws InterruptedException, ExecutionException {
        // WRONG approach: relying on priority to ensure "important" work happens first.
        // (Shown conceptually above in PriorityNotAGuarantee -- not repeated here.)

        // RIGHT approach: use actual coordination mechanisms to guarantee order/completion.
        ExecutorService pool = Executors.newFixedThreadPool(2);

        Future<String> criticalWork = pool.submit(() -> {
            Thread.sleep(50);
            return "critical work result";
        });

        // Genuinely wait for the critical work to complete BEFORE proceeding --
        // a guarantee no amount of priority tuning could provide.
        String result = criticalWork.get();
        System.out.println("guaranteed to have this BEFORE proceeding: " + result);

        Future<String> backgroundWork = pool.submit(() -> {
            Thread.sleep(20);
            return "background work result";
        });

        System.out.println("now safely starting dependent work, using the guaranteed result: " + result);
        System.out.println("background work will complete independently: " + backgroundWork.get());

        pool.shutdown();
    }
}
```

**How to run:** `java ProperCoordinationInstead.java`.

Expected output:
```
guaranteed to have this BEFORE proceeding: critical work result
now safely starting dependent work, using the guaranteed result: critical work result
background work will complete independently: background work result
```

This adds the production-flavored hard case: replacing "hope priority makes the important thing happen first" with "actually wait for the important thing to complete before proceeding," using `Future.get()` as a genuine, guaranteed synchronization point. This is the correct pattern whenever code has a real dependency on another task's completion or ordering — priority was never the right tool for that job in the first place, and this approach provides a hard guarantee priority tuning never could.

## 6. Walkthrough

Tracing `ProperCoordinationInstead.main`:

1. `pool.submit(...)` for `criticalWork` schedules that task on the thread pool and returns a `Future<String>` immediately — the main thread does not block yet.
2. `criticalWork.get()` blocks the main thread until that specific task has genuinely finished executing (here, after its internal 50ms sleep) and returns its result, `"critical work result"` — this is a hard guarantee: the line immediately after `get()` is provably reached only after the critical work has fully completed, something no priority setting could ever promise.
3. Only after that guarantee is satisfied does the code submit `backgroundWork` and proceed to use `result` — the dependency between "critical work must finish first" and "then use its result" is expressed explicitly and enforced by the language's actual concurrency primitives (`Future.get()`), not by hoping a scheduler happens to favor one thread over another.
4. `backgroundWork.get()` is called last, blocking only long enough for that independent task to finish, and its result is printed — demonstrating that ordering and dependency guarantees, when they're actually needed, come from explicit coordination constructs, never from priority tuning.

## 7. Gotchas & takeaways

> **Gotcha:** setting thread priority is one of the few concurrency-related APIs that can appear to "work" consistently during testing on one developer's machine, one JVM, and one OS, while behaving completely differently (or having no visible effect at all) on a different platform in production — because the specification never actually guarantees the behavior being informally observed and relied upon during that testing.

- Thread priority (1–10, default 5) is passed to the OS scheduler as an advisory hint — the JVM specification makes no guarantee about resulting scheduling behavior.
- Actual scheduling behavior based on priority varies by operating system, JVM implementation, and even machine load — code should never depend on any specific outcome from setting it.
- Never use priority as a substitute for correct synchronization or as a way to guarantee execution order, completion timing, or relative CPU allocation between threads.
- For genuine ordering or completion guarantees, use actual coordination mechanisms — `Future.get()`, `join()`, proper synchronization — which provide hard guarantees priority tuning cannot.
- If priority tuning is used at all, treat it as a soft, best-effort suggestion for relative importance, with the explicit understanding that behavior is platform-dependent and unverifiable across environments.
