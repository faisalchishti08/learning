# Java Virtual Threads [Java 21]

## Overview

Virtual threads are lightweight, JVM-managed threads introduced as a preview in Java 19 and finalized in **Java 21** (JEP 444). They enable massive concurrency (millions of threads) without the memory cost of platform threads, making thread-per-request servers viable at scale.

---

## 1. Platform Threads vs Virtual Threads

### Visual Diagram — Architecture

```
Platform Thread (OS Thread):
  JVM Thread ──── OS Thread ──── CPU Core
  Each platform thread = ~1MB stack, OS kernel object
  OS kernel schedules them
  Typically limited to thousands (memory + context switch cost)

Virtual Thread:
  Virtual Thread ──── (mounted on) ──── Carrier Thread (platform thread)
                                        └── ForkJoinPool (default)
  
  Virtual thread stack: small, heap-allocated, grows dynamically (~few KB)
  JVM scheduler mounts/unmounts virtual threads on carrier threads
  
  When virtual thread BLOCKS (I/O, sleep, lock):
    JVM unmounts it from carrier thread
    Carrier thread picks up ANOTHER virtual thread
    When I/O completes, virtual thread is re-mounted

  Scale: millions of virtual threads on handful of carrier threads

Platform Thread Pool (old):          Virtual Thread per request (new):
  Request1 → PT1 (blocks on I/O)       Request1 → VT1 (unmounted during I/O)
  Request2 → PT2 (blocks on I/O)       Request2 → VT2 (unmounted during I/O)
  Request3 → WAITS (no free threads!)  Request3 → VT3 (runs on freed carrier)
  Max: ~200 threads in pool            Max: millions of VTs
```

### Example 1 — Creating Virtual Threads

```java
public class VirtualThreadCreation {
    public static void main(String[] args) throws Exception {
        // Method 1: Thread.ofVirtual() builder [Java 21]
        Thread vt = Thread.ofVirtual()
            .name("my-virtual-thread")
            .start(() -> System.out.println("Running in: " + Thread.currentThread()));
        vt.join();

        // Method 2: Thread.startVirtualThread() — quick one-liner
        Thread vt2 = Thread.startVirtualThread(() ->
            System.out.println("Quick virtual thread")
        );
        vt2.join();

        // Method 3: Executors.newVirtualThreadPerTaskExecutor()
        try (var exec = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            exec.submit(() -> System.out.println("Via executor"));
        } // auto-shuts down

        // Check if virtual
        Thread.startVirtualThread(() -> {
            System.out.println("Is virtual: " + Thread.currentThread().isVirtual()); // true
        }).join();

        // Platform thread comparison
        Thread platform = Thread.ofPlatform().name("platform").start(() ->
            System.out.println("Is virtual: " + Thread.currentThread().isVirtual()) // false
        );
        platform.join();
    }
}
```

**What this does:** Four ways to create virtual threads. `isVirtual()` distinguishes them. `newVirtualThreadPerTaskExecutor()` is the recommended way in server frameworks — creates one virtual thread per submitted task.

---

## 2. Scale Demonstration

### Example 1 — One Million Virtual Threads

```java
import java.util.concurrent.*;

public class MillionVirtualThreads {
    public static void main(String[] args) throws Exception {
        int count = 1_000_000;
        CountDownLatch latch = new CountDownLatch(count);

        long start = System.currentTimeMillis();

        try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < count; i++) {
                exec.submit(() -> {
                    try {
                        Thread.sleep(1000); // each sleeps 1 second
                    } catch (InterruptedException e) {}
                    latch.countDown();
                });
            }
            latch.await();
        }

        long elapsed = System.currentTimeMillis() - start;
        System.out.println("1M virtual threads, each sleeping 1s, total: " + elapsed + "ms");
        // ~1000-1100ms — true concurrency!

        // Compare: with platform threads
        // ExecutorService exec = Executors.newFixedThreadPool(200);
        // Would take 1M/200 * 1000ms = 5000 seconds — 5000x slower
    }
}
```

**What this does:** One million threads each sleeping 1 second completes in ~1 second total. Virtual threads are unmounted during sleep — the JVM scheduler reuses carrier threads for others. Platform threads would need 200+ threads and take 5000+ seconds.

### Dry Run — Virtual Thread Scheduling During Blocking I/O

```
Carrier thread CT1 runs virtual threads VT1, VT2, VT3:

t=0:  CT1 mounts VT1 → VT1 starts running
t=1:  VT1 calls Thread.sleep(100ms) → JVM unmounts VT1, stores VT1 state on heap
t=1:  CT1 mounts VT2 → VT2 starts running  (CT1 is not idle!)
t=2:  VT2 calls read() → I/O submitted, JVM unmounts VT2
t=2:  CT1 mounts VT3 → VT3 starts running
t=50: I/O for VT2 completes → VT2 scheduled to re-mount on available carrier
t=101: VT1's sleep expires → VT1 scheduled to re-mount on available carrier
...

Key insight: CT1 never idles while virtual threads block.
One carrier thread can serve thousands of virtual threads.
```

---

## 3. Structured Concurrency [Java 21 Preview → Java 23 Final]

### What is it

`StructuredTaskScope` ensures that when a scope exits, all spawned virtual threads complete. Errors from child threads are contained and aggregated. Prevents "lost" background threads.

### Example 1 — ShutdownOnFailure

```java
import java.util.concurrent.*;
import java.util.concurrent.StructuredTaskScope.*;

public class StructuredConcurrencyDemo {
    static String fetchUser(int id) throws InterruptedException {
        Thread.sleep(50);
        return "User-" + id;
    }

    static String fetchOrder(int userId) throws InterruptedException {
        Thread.sleep(80);
        return "Order for User-" + userId;
    }

    public static void main(String[] args) throws Exception {
        // ShutdownOnFailure: if any subtask fails, cancel all others
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Subtask<String> user  = scope.fork(() -> fetchUser(42));
            Subtask<String> order = scope.fork(() -> fetchOrder(42));

            scope.join();           // wait for all
            scope.throwIfFailed();  // rethrow if any failed

            System.out.println(user.get() + " | " + order.get());
            // User-42 | Order for User-42
        }
        // Scope exits: all virtual threads guaranteed done or cancelled
    }
}
```

**What this does:** `scope.fork()` spawns virtual threads. `scope.join()` waits. If `fetchUser` throws, `fetchOrder` is cancelled — no orphaned threads. `throwIfFailed()` propagates the exception.

### Example 2 — ShutdownOnSuccess (Racing)

```java
import java.util.concurrent.*;
import java.util.concurrent.StructuredTaskScope.*;

public class ShutdownOnSuccess {
    static String fetchFromPrimary() throws InterruptedException {
        Thread.sleep(200); // slow
        return "primary result";
    }

    static String fetchFromBackup() throws InterruptedException {
        Thread.sleep(50); // fast
        return "backup result";
    }

    public static void main(String[] args) throws Exception {
        // ShutdownOnSuccess: return first successful result, cancel others
        try (var scope = new StructuredTaskScope.ShutdownOnSuccess<String>()) {
            scope.fork(() -> fetchFromPrimary());
            scope.fork(() -> fetchFromBackup());

            scope.join();
            System.out.println(scope.result()); // backup result (faster won)
        }
        // Primary is automatically cancelled
    }
}
```

**What this does:** Race two sources — return whichever finishes first. `ShutdownOnSuccess` cancels the losers automatically.

---

## 4. Pitfalls and Best Practices

### What NOT to Do with Virtual Threads

### Example 1 — Thread-Local Pitfall

```java
import java.util.concurrent.*;

public class ThreadLocalPitfall {
    // ThreadLocal is PER-THREAD — with millions of VTs, each has its own copy
    // For large objects, this means millions of copies = memory explosion!
    static ThreadLocal<byte[]> bigBuffer = ThreadLocal.withInitial(() -> new byte[1024 * 1024]); // 1MB

    public static void main(String[] args) throws Exception {
        // BAD: 1M virtual threads × 1MB ThreadLocal = 1TB memory
        try (var exec = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 1000; i++) {
                exec.submit(() -> {
                    byte[] buf = bigBuffer.get(); // 1MB per virtual thread!
                    // use buf...
                });
            }
        }

        // GOOD: use ScopedValue [Java 21 Preview] instead of ThreadLocal
        // Or: pass the resource as a parameter
        // Or: use a pool with Semaphore
    }
}
```

### Example 2 — Pinning (synchronized blocks)

```java
import java.util.concurrent.*;

public class PinningPitfall {
    static final Object lock = new Object();

    public static void main(String[] args) throws Exception {
        // BAD: synchronized block PINS virtual thread to carrier thread
        // The carrier cannot serve other VTs while VT is blocked in synchronized
        Thread.startVirtualThread(() -> {
            synchronized (lock) {
                try { Thread.sleep(1000); } // carrier is PINNED during sleep!
                catch (InterruptedException e) {}
            }
        }).join();

        // GOOD: use ReentrantLock instead — allows unmounting
        var rl = new java.util.concurrent.locks.ReentrantLock();
        Thread.startVirtualThread(() -> {
            rl.lock();
            try {
                Thread.sleep(1000); // VT can be unmounted while waiting
            } catch (InterruptedException e) {}
            finally { rl.unlock(); }
        }).join();
    }
}
```

**What this does:** `synchronized` blocks **pin** virtual threads to their carrier — the carrier cannot be reused for other virtual threads while pinned. Use `ReentrantLock` instead for blocking operations inside virtual threads.

> ⚠️ **Pitfall:** `synchronized` + blocking I/O in a virtual thread = carrier thread pinning = defeats the purpose of virtual threads. JVM flag `-Djdk.tracePinnedThreads=full` reveals pinning.

---

## 5. Practical Migration Pattern

### Example 1 — Thread-Per-Request Server

```java
import java.util.concurrent.*;
import java.net.*;
import java.io.*;

public class VirtualThreadServer {
    public static void main(String[] args) throws Exception {
        // Old way: fixed thread pool limits concurrency
        // ExecutorService old = Executors.newFixedThreadPool(200);

        // New way: virtual thread per request — scales to millions
        try (var executor = Executors.newVirtualThreadPerTaskExecutor();
             var serverSocket = new ServerSocket(8080)) {

            System.out.println("Server started on :8080");

            while (true) {
                Socket socket = serverSocket.accept();
                executor.submit(() -> handleRequest(socket)); // one VT per request
            }
        }
    }

    static void handleRequest(Socket socket) {
        try (socket;
             var in  = new BufferedReader(new InputStreamReader(socket.getInputStream()));
             var out = new PrintWriter(socket.getOutputStream(), true)) {
            // Read/write — blocking I/O here unmounts the virtual thread
            String line = in.readLine();
            out.println("HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nHello");
        } catch (IOException e) { /* handle */ }
    }
}
```

**What this does:** Each incoming request gets its own virtual thread. Blocking I/O (reading from socket) unmounts the virtual thread — no carrier threads are wasted. Thousands of simultaneous connections handled by handful of carrier threads.

---

## 6. Virtual Thread API Summary

```
Creation:
  Thread.ofVirtual().start(r)         create + start
  Thread.ofVirtual().name("n").start(r) named virtual thread
  Thread.startVirtualThread(r)        quick one-liner
  Executors.newVirtualThreadPerTaskExecutor() executor (recommended)

Inspection:
  thread.isVirtual()                  true for virtual threads
  thread.getState()                   lifecycle state (same as platform)

Structured Concurrency [Java 21 Preview]:
  new StructuredTaskScope.ShutdownOnFailure()  fail fast
  new StructuredTaskScope.ShutdownOnSuccess()  race (first wins)
  scope.fork(callable)                spawn virtual thread
  scope.join()                        wait for all
  scope.throwIfFailed()               rethrow on failure
  scope.result()                      get first success (ShutdownOnSuccess)

ScopedValue [Java 21 Preview — replaces ThreadLocal for VT]:
  ScopedValue<T> sv = ScopedValue.newInstance();
  ScopedValue.where(sv, value).run(() -> { sv.get(); });

Best practices:
  DO:    use ReentrantLock (not synchronized) in VT code
  DO:    use newVirtualThreadPerTaskExecutor() for I/O-bound work
  DON'T: use large ThreadLocals with VTs (memory explosion)
  DON'T: pool virtual threads (cheap to create, no need to pool)
  DON'T: use VTs for CPU-bound work (no benefit, still needs CPU)
```

---

## Quick Reference

```
Feature               Java Version    Notes
Virtual Threads       Java 21 (final) JEP 444 — stable API
Structured Concurrency Java 21 (preview) JEP 453 — finalized Java 23
ScopedValue           Java 21 (preview) JEP 446 — replaces ThreadLocal
                      
Carrier threads:      ForkJoinPool (default: #cores parallel)
Stack size:           heap-allocated, few KB initial, grows on demand
Pinning triggers:     synchronized blocks, native methods
Detect pinning:       -Djdk.tracePinnedThreads=full
```
