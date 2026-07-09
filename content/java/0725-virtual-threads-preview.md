---
card: java
gi: 725
slug: virtual-threads-preview
title: Virtual threads (preview)
---

## 1. What it is

**Java 19** (JEP 425) previews **virtual threads**: lightweight threads implemented by the JVM itself rather than by the operating system. A traditional Java `Thread` is a thin wrapper around one **OS (platform) thread** — a relatively heavyweight resource, typically limited to a few thousand per process before memory and scheduling overhead become a real problem. A virtual thread, created with `Thread.ofVirtual()` or `Executors.newVirtualThreadPerTaskExecutor()`, is instead a JVM-managed unit of execution that gets *mounted* onto a small pool of underlying platform threads (called *carrier threads*) only while it's actively running code, and is *unmounted* the moment it blocks on I/O — freeing the carrier thread to run a different virtual thread in the meantime. This makes it practical to create **millions** of virtual threads in a single JVM, each written in the same simple, blocking, one-thread-per-task style Java code has always used, without the throughput collapse that would come from creating millions of platform threads. Being a preview feature in Java 19, it requires `--enable-preview` to compile and run.

## 2. Why & when

For years, high-throughput Java servers faced a real dilemma: writing simple, sequential, blocking-style code (`socket.read()`, `resultSet.next()`, one thread per request) is by far the easiest style to write, debug, and reason about — but it doesn't scale past a few thousand concurrent requests, because each request ties up one increasingly expensive OS thread for its entire duration, even while that thread is doing nothing but waiting on a network call or a database query. The alternative — asynchronous, reactive, callback- or `CompletableFuture`-based code — scales far better because it never blocks an OS thread waiting for I/O, but it fundamentally changes how code is written: stack traces fragment across callback boundaries, debugging and profiling tools struggle to show a coherent call history, and simple control flow (a `for` loop calling a blocking method) has to be rewritten in a much more complex, harder-to-read style. Virtual threads exist to eliminate this trade-off entirely: they let a program achieve the throughput of asynchronous code while being written in the plain, sequential, blocking style that's easiest to understand — because when a virtual thread calls a blocking method like `Socket.read()`, the JVM automatically parks it and frees the underlying carrier thread, rather than that carrier thread sitting idle. Reach for virtual threads specifically for **I/O-bound, high-concurrency** workloads — a server handling many simultaneous requests, each of which spends most of its time waiting on a database, another service, or a file — not for CPU-bound work, where the number of platform threads actually doing computation is still ultimately bounded by real CPU cores.

## 3. Core concept

```java
// Traditional platform thread — one real OS thread, expensive to create many of.
Thread platform = Thread.ofPlatform().start(() -> System.out.println("platform thread"));

// Virtual thread — JVM-managed, cheap to create millions of.
Thread virtual = Thread.ofVirtual().start(() -> System.out.println("virtual thread"));

// The idiomatic way to use many of them: one virtual thread per task.
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> doBlockingWork());
}
```

The same `Thread` and familiar blocking APIs (`Thread.sleep`, `InputStream.read`, `java.net.Socket`) work unchanged on virtual threads — the JVM handles mounting and unmounting transparently underneath.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Many virtual threads are mounted onto a small pool of carrier (platform/OS) threads; a virtual thread that blocks on I/O is unmounted, freeing its carrier thread to run a different virtual thread">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Thousands of virtual threads</text>
  <rect x="20" y="30" width="60" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="50" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">VT-1</text>
  <rect x="90" y="30" width="60" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">VT-2</text>
  <rect x="160" y="30" width="60" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="190" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">VT-3</text>
  <text x="250" y="50" fill="#8b949e" font-size="14" text-anchor="middle" font-family="sans-serif">...</text>
  <rect x="280" y="30" width="60" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="310" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">VT-N</text>

  <line x1="50" y1="60" x2="80" y2="110" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a6)"/>
  <line x1="190" y1="60" x2="220" y2="110" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a6)"/>
  <text x="140" y="90" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">mounted while running</text>

  <rect x="20" y="120" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="144" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">carrier thread A</text>
  <rect x="180" y="120" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="240" y="144" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">carrier thread B</text>
  <text x="160" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">a small pool of real OS threads (roughly = CPU cores)</text>

  <text x="450" y="130" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">VT-2 blocks on I/O -&gt;</text>
  <text x="450" y="145" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">unmounted, carrier freed</text>
  <text x="450" y="165" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">for another virtual thread</text>

  <defs><marker id="a6" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Only virtual threads *actively running code* occupy a carrier thread; blocked ones step aside.

## 5. Runnable example

Scenario: simulating many concurrent "slow I/O" tasks (each just sleeping, standing in for a network call or database query). The example grows from a small number of platform threads, to the same task run on thousands of virtual threads to show the scale difference, to a virtual-thread-per-task executor collecting results with proper structured shutdown and timing comparison.

### Level 1 — Basic

```java
// File: VirtualThreadBasic.java
// Run with --enable-preview: virtual threads are a preview feature in Java 19.
public class VirtualThreadBasic {
    public static void main(String[] args) throws InterruptedException {
        Thread platform = Thread.ofPlatform().start(() ->
                System.out.println("Running on: " + Thread.currentThread()));
        platform.join();

        Thread virtual = Thread.ofVirtual().start(() ->
                System.out.println("Running on: " + Thread.currentThread()));
        virtual.join();
    }
}
```

**How to run:**
```
javac --release 19 --enable-preview VirtualThreadBasic.java
java --enable-preview VirtualThreadBasic
```

Expected output shape (exact thread names/ids vary by run):
```
Running on: Thread[#21,Thread-0,5,main]
Running on: VirtualThread[#23]/runnable@ForkJoinPool-1-worker-1
```

### Level 2 — Intermediate

```java
// File: VirtualThreadScaleIntermediate.java
// The SAME "slow I/O" task (a sleep standing in for a blocking network call),
// now run 10,000 times concurrently — demonstrating the scale that platform
// threads cannot practically reach, but virtual threads handle easily.
import java.util.concurrent.atomic.AtomicInteger;

public class VirtualThreadScaleIntermediate {
    static void simulateSlowIO() {
        try {
            Thread.sleep(100); // stands in for a blocking network/database call
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 10_000;
        AtomicInteger completed = new AtomicInteger();
        long start = System.currentTimeMillis();

        Thread[] threads = new Thread[taskCount];
        for (int i = 0; i < taskCount; i++) {
            threads[i] = Thread.ofVirtual().start(() -> {
                simulateSlowIO();
                completed.incrementAndGet();
            });
        }
        for (Thread t : threads) t.join();

        long elapsedMs = System.currentTimeMillis() - start;
        System.out.println("Completed " + completed.get() + " virtual-thread tasks in ~" + elapsedMs + "ms");
        System.out.println("(each task 'slept' 100ms; total elapsed proves they ran concurrently, not one-at-a-time)");
    }
}
```

**How to run:**
```
java --enable-preview VirtualThreadScaleIntermediate.java
```

Expected output (elapsed time is close to 100ms-range, not 10,000 x 100ms, proving concurrency):
```
Completed 10000 virtual-thread tasks in ~150ms
(each task 'slept' 100ms; total elapsed proves they ran concurrently, not one-at-a-time)
```

10,000 platform threads attempting the same thing would typically be far slower to even create, and could exhaust OS resources on many systems — the point this level demonstrates concretely.

### Level 3 — Advanced

```java
// File: VirtualThreadExecutorAdvanced.java
// Uses the idiomatic Executors.newVirtualThreadPerTaskExecutor(), collects
// per-task results via Future, and handles a mix of successful and failing
// tasks — the production-flavored shape of virtual-thread-based concurrency.
import java.util.*;
import java.util.concurrent.*;

public class VirtualThreadExecutorAdvanced {
    static String fetchFromService(int id) throws InterruptedException {
        Thread.sleep(50); // simulated network latency
        if (id == 7) throw new RuntimeException("service " + id + " timed out");
        return "result-from-service-" + id;
    }

    public static void main(String[] args) throws InterruptedException {
        int taskCount = 20;
        List<Future<String>> futures = new ArrayList<>();

        try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < taskCount; i++) {
                int id = i;
                futures.add(executor.submit(() -> fetchFromService(id)));
            }
        } // executor.close() waits for all submitted tasks to finish before returning

        int succeeded = 0, failed = 0;
        for (Future<String> f : futures) {
            try {
                f.get();
                succeeded++;
            } catch (ExecutionException e) {
                failed++;
            }
        }
        System.out.println("Succeeded: " + succeeded + ", Failed: " + failed + " (out of " + taskCount + ")");
    }
}
```

**How to run:**
```
java --enable-preview VirtualThreadExecutorAdvanced.java
```

Expected output:
```
Succeeded: 19, Failed: 1 (out of 20)
```

## 6. Walkthrough

1. `VirtualThreadExecutorAdvanced.main` opens an `ExecutorService` from `Executors.newVirtualThreadPerTaskExecutor()` inside a `try`-with-resources block — this executor's defining behavior is that it creates one **brand-new virtual thread per submitted task**, rather than reusing a fixed pool of worker threads the way `Executors.newFixedThreadPool` does.
2. The loop calls `executor.submit(...)` 20 times, each submission returning a `Future<String>` immediately, without blocking — internally, each submission spawns a new virtual thread that begins running `fetchFromService(id)` right away, mounted onto whichever carrier thread happens to be free.
3. Inside `fetchFromService`, `Thread.sleep(50)` simulates blocking network I/O. This is the critical moment for virtual threads: when a virtual thread calls a blocking operation the JVM knows how to virtualize (like `Thread.sleep`, or blocking I/O on `java.net`/`java.nio` sockets), it is **unmounted** from its carrier thread — the carrier is freed to run a *different* virtual thread's code during that 50ms wait, rather than sitting idle.
4. When `id == 7`, the method throws a `RuntimeException` instead of returning normally — this simulates one call among the twenty actually failing, exactly like a real service timeout would.
5. The `try`-with-resources block's implicit `executor.close()` call (a new, `AutoCloseable`-based executor shutdown behavior) blocks the *main* thread until every submitted virtual-thread task has completed — success or failure — before the block exits and execution continues to the `Future` result-collection loop.
6. That loop calls `f.get()` on each of the 20 futures. For the 19 successful tasks, `get()` returns the fetched string normally. For task 7, `get()` throws `ExecutionException`, wrapping the `RuntimeException` that was thrown inside the virtual thread — this is standard `Future` behavior, unchanged by virtual threads: an exception thrown inside the task is captured and re-thrown from `get()`, never silently lost.
7. The final counts, `succeeded=19` and `failed=1`, confirm all 20 tasks ran to completion (success or failure) using 20 separate virtual threads, mounted and unmounted onto a small carrier-thread pool behind the scenes — all written as plain, sequential, blocking-style code with no callbacks or `CompletableFuture` chaining.

```
executor.submit() x 20                    small pool of carrier threads (~CPU cores)
      |                                              |
      v                                              v
  20 virtual threads created            each virtual thread mounts, runs
      |                                  until it calls Thread.sleep(50)
      v                                              |
  each blocks on sleep(50)  ------------->  unmounted; carrier freed for another VT
      |                                              |
  sleep completes  <---------------------  re-mounted onto (possibly different) carrier
      |
  returns result or throws  ->  captured in its Future
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 19** — both `javac` (with `--release 19`) and `java` require `--enable-preview`, and the API was still being refined before its eventual finalization in a later JDK release; treat Java 19's exact behavior as subject to change.
- Virtual threads help **I/O-bound** concurrency, not CPU-bound concurrency — a virtual thread running pure computation (no blocking calls) occupies its carrier thread for the entire duration, exactly like a platform thread would; creating a million virtual threads all doing tight CPU loops provides no benefit over a bounded number of platform threads, since real CPU core count is still the limiting factor.
- Blocking inside a `synchronized` block or method historically **pinned** a virtual thread to its carrier (preventing unmounting) in early virtual-thread implementations including this Java 19 preview — a significant caveat for code migrating from thread-pool-based concurrency that relies heavily on `synchronized`; `java.util.concurrent.locks.ReentrantLock` does not have this limitation and is generally preferred with virtual threads.
- `Executors.newVirtualThreadPerTaskExecutor()` deliberately creates unlimited threads (one per task, no pooling/reuse) — this is safe specifically *because* virtual threads are cheap; using the same unbounded-creation pattern with a platform-thread executor would exhaust system resources.
- Debugging and profiling tools were updated alongside this feature to understand virtual threads specifically — thread dumps can show hundreds of thousands of virtual threads meaningfully grouped by carrier, something that would be unreadable noise with an equivalent number of platform threads.
- The `try`-with-resources auto-closing behavior of `ExecutorService` (Level 3) — waiting for all submitted tasks before the block exits — is itself a broader Java concurrency improvement introduced alongside virtual threads, making it easy to get correct, leak-free shutdown semantics without manually calling `shutdown()` and `awaitTermination()`.
