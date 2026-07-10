---
card: java
gi: 850
slug: process-vs-thread
title: Process vs thread
---

## 1. What it is

A **process** is an independent, operating-system-level unit of execution with its own private memory address space — two processes cannot directly read or write each other's variables; they must communicate through explicit OS mechanisms (files, pipes, sockets, shared memory regions set up deliberately). A **thread** is a unit of execution *within* a process — every thread in the same JVM process shares that process's heap memory directly, meaning two threads can read and write the exact same object's fields without any explicit communication mechanism at all. A single Java program is one OS process that typically runs many threads (at minimum, one: the "main" thread), all sharing one heap, one set of loaded classes, and one set of open file handles.

## 2. Why & when

Sharing memory directly (threads) is dramatically cheaper than copying data between isolated memory spaces (processes) — passing a reference to an object between two threads costs nothing extra, while getting equivalent data from one process to another requires serialization, an IPC mechanism, and deserialization on the other end. This is why concurrent work *within* a single application almost always uses threads: a web server handling many requests concurrently, a UI staying responsive while background work happens, parallel computation splitting work across CPU cores. Processes matter for a different concern entirely: isolation and fault containment — if one process crashes, it doesn't take down another; if a `ProcessBuilder`-launched subprocess (like a separate command-line tool) misbehaves, it can't corrupt the launching JVM's own memory. Reach for separate processes specifically when isolation itself is the goal (running untrusted or unstable code, achieving crash containment, running a genuinely separate program), and threads for everything else concurrency-related within one program.

## 3. Core concept

```java
// Threads: DIRECT shared access to the same object, no communication mechanism needed.
int[] sharedCounter = {0};
Thread t1 = new Thread(() -> sharedCounter[0]++);
Thread t2 = new Thread(() -> sharedCounter[0]++);
// Both threads can read/write sharedCounter[0] directly -- it's the SAME array in the SAME heap.

// Processes: NO direct memory sharing -- must communicate via an explicit channel.
ProcessBuilder pb = new ProcessBuilder("echo", "hello from a separate process");
Process process = pb.start();
// The parent JVM cannot read the child process's variables directly.
// It can only read what the child WRITES to a shared channel, like its standard output stream.
```

There's no way to give the `ProcessBuilder`-launched process direct access to `sharedCounter` — the only communication path is through the channels the OS explicitly provides between processes (here, the subprocess's stdout, read via `process.getInputStream()`).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads within one process share the same heap memory directly; two separate processes each have their own isolated memory and can only communicate through an explicit channel">
  <g font-family="sans-serif">
    <rect x="30" y="20" width="270" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="165" y="38" fill="#8b949e" font-size="10" text-anchor="middle">ONE process</text>
    <rect x="50" y="50" width="100" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
    <text x="100" y="75" fill="#e6edf3" font-size="10" text-anchor="middle">thread 1</text>
    <rect x="170" y="50" width="100" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
    <text x="220" y="75" fill="#e6edf3" font-size="10" text-anchor="middle">thread 2</text>
    <rect x="50" y="100" width="220" height="30" rx="6" fill="#0f1620" stroke="#3fb950"/>
    <text x="160" y="120" fill="#3fb950" font-size="9" text-anchor="middle">shared heap -- both read/write directly</text>
  </g>

  <g font-family="sans-serif">
    <rect x="340" y="20" width="130" height="120" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
    <text x="405" y="80" fill="#e6edf3" font-size="10" text-anchor="middle">process A</text>
    <text x="405" y="100" fill="#8b949e" font-size="9" text-anchor="middle">own memory</text>

    <rect x="490" y="20" width="130" height="120" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
    <text x="555" y="80" fill="#e6edf3" font-size="10" text-anchor="middle">process B</text>
    <text x="555" y="100" fill="#8b949e" font-size="9" text-anchor="middle">own memory</text>

    <line x1="470" y1="80" x2="490" y2="80" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a850)"/>
    <text x="480" y="65" fill="#f0883e" font-size="8" text-anchor="middle">IPC only</text>
  </g>
  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Threads share everything by default; processes share nothing without an explicit channel</text>

  <defs><marker id="a850" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

*Threads default to shared memory; processes default to isolation and require an explicit channel to exchange anything.*

## 5. Runnable example

Scenario: a task counter shared between concurrent workers, growing from direct thread-based sharing, through the contrast of process-level isolation via `ProcessBuilder`, to measuring the real cost difference between spawning threads and spawning processes for equivalent work.

### Level 1 — Basic

```java
import java.util.concurrent.atomic.*;

public class ThreadSharedMemory {
    public static void main(String[] args) throws InterruptedException {
        AtomicInteger sharedCounter = new AtomicInteger(0);

        Thread t1 = new Thread(() -> {
            for (int i = 0; i < 1000; i++) sharedCounter.incrementAndGet();
        });
        Thread t2 = new Thread(() -> {
            for (int i = 0; i < 1000; i++) sharedCounter.incrementAndGet();
        });

        t1.start();
        t2.start();
        t1.join();
        t2.join();

        System.out.println("final shared counter value: " + sharedCounter.get());
        System.out.println("-> both threads directly read/wrote the SAME object, no communication setup needed");
    }
}
```

**How to run:** `java ThreadSharedMemory.java` (JDK 17+).

Expected output:
```
final shared counter value: 2000
-> both threads directly read/wrote the SAME object, no communication setup needed
```

Both threads reference the exact same `AtomicInteger` object living in the JVM's single shared heap — no serialization, no explicit channel, just direct shared access (made safe here by `AtomicInteger`'s built-in atomicity).

### Level 2 — Intermediate

```java
import java.io.*;

public class ProcessIsolation {
    public static void main(String[] args) throws IOException, InterruptedException {
        // A separate OS PROCESS -- has its OWN memory, cannot see anything in this JVM directly.
        ProcessBuilder pb = new ProcessBuilder("java", "-version");
        pb.redirectErrorStream(true);
        Process process = pb.start();

        // The ONLY way to get information back is through an explicit channel: its output stream.
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }
        int exitCode = process.waitFor();

        System.out.println("subprocess exit code: " + exitCode);
        System.out.println("subprocess output (received via explicit channel, not shared memory):");
        System.out.println(output);
    }
}
```

**How to run:** `java ProcessIsolation.java`. Output varies by installed JDK version.

Expected output shape:
```
subprocess exit code: 0
subprocess output (received via explicit channel, not shared memory):
openjdk version "21.0.1" 2023-10-17
...
```

The real-world concern added: launching an entirely separate OS process via `ProcessBuilder`, which has its own independent memory space — the only way to observe anything about what it does is through the explicit output-stream channel the OS provides between parent and child processes, in stark contrast to `ThreadSharedMemory`'s direct shared-object access between two threads in the same process.

### Level 3 — Advanced

```java
import java.io.*;
import java.util.concurrent.*;

public class CreationCostComparison {
    public static void main(String[] args) throws Exception {
        int count = 20;

        long threadStart = System.currentTimeMillis();
        Thread[] threads = new Thread[count];
        for (int i = 0; i < count; i++) {
            threads[i] = new Thread(() -> {
                try { Thread.sleep(10); } catch (InterruptedException ignored) {}
            });
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        long threadElapsed = System.currentTimeMillis() - threadStart;

        long processStart = System.currentTimeMillis();
        Process[] processes = new Process[count];
        for (int i = 0; i < count; i++) {
            processes[i] = new ProcessBuilder("java", "-version").redirectErrorStream(true).start();
        }
        for (Process p : processes) p.waitFor();
        long processElapsed = System.currentTimeMillis() - processStart;

        System.out.println("creating and running " + count + " threads: " + threadElapsed + " ms");
        System.out.println("creating and running " + count + " separate JVM processes: " + processElapsed + " ms");
        System.out.println("-> spawning a new OS process (a whole new JVM here) costs FAR more than spawning a thread");
    }
}
```

**How to run:** `java CreationCostComparison.java`. Exact timings vary significantly by machine, but the *relative* gap — processes costing far more to create than threads — is the consistent, expected result, since each subprocess here launches an entirely separate JVM instance.

Expected output shape:
```
creating and running 20 threads: ~15 ms
creating and running 20 separate JVM processes: ~4000 ms
-> spawning a new OS process (a whole new JVM here) costs FAR more than spawning a thread
```

This adds the production-flavored hard case: directly measuring the cost difference. Creating a thread within an existing process is cheap — the OS just needs to allocate a stack and register it with the scheduler, reusing the process's existing memory space and loaded resources. Creating a new process (especially, as here, one that starts an entirely new JVM instance) is dramatically more expensive — a new address space, a new copy of the runtime, no memory or resources shared with the parent by default. This cost difference is exactly why concurrent work *within* an application defaults to threads, reserving separate processes for genuine isolation needs.

## 6. Walkthrough

Tracing `CreationCostComparison.main`:

1. The first loop creates and starts 20 `Thread` objects, each sleeping for 10ms before finishing; `join()` on each waits for that thread to terminate before measuring total elapsed time.
2. Because these threads all run within the *same* JVM process, creating each one is relatively cheap — the JVM allocates a thread stack and hands it to the OS scheduler, but no new memory space, no new copy of loaded classes, and no separate runtime initialization is needed. All 20 threads share the identical heap, class metadata, and JVM runtime state the main thread already has.
3. The second loop launches 20 separate `Process` instances via `ProcessBuilder("java", "-version")`, each one starting an entirely independent JVM. Each subprocess requires the OS to allocate a completely fresh address space, and each spawned JVM must perform its own startup sequence (class loading, JIT warm-up considerations, and so on) — none of which is shared with the parent JVM or with any of the other spawned processes.
4. `waitFor()` on each process blocks until that specific subprocess has fully exited, and the elapsed time captures the full cost of all 20 process launches plus their JVM startup and `-version` execution and exit.
5. Comparing the two elapsed times directly demonstrates the practical consequence of the conceptual distinction: threads are cheap to create *because* they share nearly everything with their parent process, while processes are expensive to create *because* they deliberately share almost nothing, requiring the OS to set up an entirely separate execution environment for each one.

## 7. Gotchas & takeaways

> **Gotcha:** because threads share the same heap by default, any shared mutable state accessed by multiple threads **without proper synchronization** is a genuine correctness risk — the very feature that makes threads cheap and convenient (direct shared memory) is also exactly what makes concurrent bugs (data races, visibility issues) possible in the first place. Processes don't have this risk at all, precisely because they don't share memory — but that isolation is also why processes can't communicate as cheaply or directly as threads can.

- A process has its own isolated memory space; a thread runs within a process and shares that process's heap directly with every other thread in the same process.
- Threads are cheap to create and communicate through directly (shared objects, no serialization); processes are expensive to create and can only communicate through explicit OS-provided channels (pipes, files, sockets).
- Use threads for concurrency *within* an application — parallelizing work, staying responsive, handling many requests — where the cost of direct memory sharing is a benefit, not a risk to be managed.
- Use separate processes specifically when isolation itself is the goal: fault containment, running untrusted code, or launching genuinely independent programs.
- A single Java program is always exactly one OS process, potentially running many threads — every concurrency topic in the rest of this section (thread lifecycle, synchronization, atomics) concerns coordination *within* that one shared-memory process.
