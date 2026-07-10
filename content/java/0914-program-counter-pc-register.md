---
card: java
gi: 914
slug: program-counter-pc-register
title: Program Counter (PC) register
---

## 1. What it is

Every thread has its own private Program Counter (PC) register — a small piece of per-thread state that tracks the address of the bytecode instruction currently being executed within that thread's current [stack frame](0913-jvm-stacks-stack-frames.md). If the method currently executing is a regular (non-native) Java method, the PC register holds the offset of the current instruction within that method's bytecode; if the currently executing method is native (implemented outside the JVM, typically in C/C++ via JNI), the PC register's value is undefined by the JVM Specification, since native code isn't tracked at the bytecode-instruction level the JVM itself manages.

## 2. Why & when

The PC register is not something Java application code ever directly reads or manipulates — there's no public API to inspect "what is my PC register right now" — but understanding its existence and role explains two things that *are* directly observable: how the JVM correctly resumes execution at the right instruction after a thread is context-switched away and later switched back (each thread's own PC register preserves exactly where it left off, independent of every other thread's), and why stack traces reliably report a precise source line and bytecode offset for where execution currently is within each frame (that reporting is derived directly from each frame's associated PC value). It's genuinely low-level JVM-internal state — this tutorial exists to complete the mental model of "what per-thread execution state exists," alongside the [JVM stack](0913-jvm-stacks-stack-frames.md) and [native method stack](0915-native-method-stacks.md), rather than to teach an API you'll use directly.

## 3. Core concept

```java
// You never read/write the PC register directly -- but its EFFECT is visible
// in every stack trace: each frame's reported line number corresponds to
// where that frame's own PC register was pointing at the moment the trace was captured.

void methodA() {
    methodB(); // PC in methodA's frame points here while methodB executes
}
void methodB() {
    throw new RuntimeException("boom"); // PC in methodB's frame points HERE at the moment of the throw
}
// The resulting stack trace's line numbers are a direct, human-readable reflection
// of each frame's own PC register value at that instant.
```

Each thread's PC register is entirely private to that thread — two threads executing the "same" method concurrently each have their own independent PC register tracking their own, independent progress through that method's bytecode.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two threads executing the same method concurrently, each with its own independent PC register pointing at a different bytecode offset within that shared method's code">
  <rect x="220" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">shared bytecode: sameMethod()</text>
  <text x="320" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">[instr0][instr1][instr2][instr3]</text>

  <rect x="40" y="110" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="130" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 1's PC -&gt; instr1</text>

  <rect x="420" y="110" width="180" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="510" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Thread 2's PC -&gt; instr3</text>

  <line x1="130" y1="108" x2="280" y2="72" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a42)"/>
  <line x1="510" y1="108" x2="360" y2="72" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a42)"/>
  <defs><marker id="a42" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*The same bytecode can be "in progress" at completely different points for different threads simultaneously — each thread's private PC register is what makes that independent progress possible.*

## 5. Runnable example

Scenario: making the PC register's *effect* observable indirectly through stack traces from concurrently-executing threads, growing from a single-threaded demonstration of line-precise stack traces, to two threads independently executing the same shared method and capturing traces showing different in-progress points, to using `Thread.getStackTrace()` to sample a running thread's current execution position from outside that thread.

### Level 1 — Basic

```java
public class LinePreciseStackTraces {
    static void level1() {
        level2();
    }
    static void level2() {
        level3();
    }
    static void level3() {
        throw new RuntimeException("boom"); // exact line where THIS frame's PC was pointing
    }

    public static void main(String[] args) {
        try {
            level1();
        } catch (RuntimeException e) {
            for (StackTraceElement frame : e.getStackTrace()) {
                System.out.println(frame); // each line reflects that frame's PC-derived position
            }
        }
    }
}
```

**How to run:** `java LinePreciseStackTraces.java` (JDK 17+).

Expected output shape (exact line numbers depend on the file's actual formatting):
```
LinePreciseStackTraces.level3(LinePreciseStackTraces.java:9)
LinePreciseStackTraces.level2(LinePreciseStackTraces.java:6)
LinePreciseStackTraces.level1(LinePreciseStackTraces.java:3)
LinePreciseStackTraces.main(LinePreciseStackTraces.java:15)
```

Every single line in this stack trace is a direct, human-readable report of where each frame's own PC register was pointing at the moment the exception was constructed — `level3`'s frame at the exact `throw` line, `level2`'s frame at the exact line it called `level3` from, and so on.

### Level 2 — Intermediate

```java
public class ConcurrentThreadsIndependentProgress {
    static void sharedMethod(String label, int iterations) {
        for (int i = 0; i < iterations; i++) {
            if (i == iterations / 2) {
                // Different threads reach THIS exact line at different real times,
                // each with its OWN PC register independently tracking its own progress
                // through this SAME shared bytecode.
                System.out.println(label + " reached the midpoint (own independent PC position)");
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(() -> sharedMethod("Thread-1", 50_000_000));
        Thread t2 = new Thread(() -> sharedMethod("Thread-2", 10_000_000)); // fewer iterations -- finishes sooner
        t1.start();
        t2.start();
        t1.join();
        t2.join();
        System.out.println("both threads executed the SAME sharedMethod bytecode, independently and concurrently");
    }
}
```

**How to run:** `java ConcurrentThreadsIndependentProgress.java`.

Expected output shape (order depends on relative timing, since the two threads run genuinely independently):
```
Thread-2 reached the midpoint (own independent PC position)
Thread-1 reached the midpoint (own independent PC position)
both threads executed the SAME sharedMethod bytecode, independently and concurrently
```

The real-world concern added: both threads execute the exact same `sharedMethod` bytecode concurrently, but each reaches its own "midpoint" at a different real time, entirely independently of the other — this is only possible because each thread maintains its own private PC register (and stack), tracking its own progress through the shared bytecode without any interference between the two.

### Level 3 — Advanced

```java
public class SamplingAnotherThreadsPosition {
    static volatile boolean keepRunning = true;

    static void busyLoop() {
        long counter = 0;
        while (keepRunning) {
            counter++;
            if (counter % 100_000_000 == 0) {
                doSomeWork(); // a distinct method call, so sampled traces show DIFFERENT frames over time
            }
        }
    }

    static void doSomeWork() {
        // deliberately tiny amount of work, so this frame is only BRIEFLY on the stack
    }

    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(SamplingAnotherThreadsPosition::busyLoop, "worker-thread");
        worker.start();

        // Sample the worker thread's CURRENT execution position from OUTSIDE it, several times,
        // observing that its reported "top frame" (reflecting its PC register's current
        // position) genuinely changes between samples, since it's actively executing.
        for (int i = 0; i < 5; i++) {
            Thread.sleep(20);
            StackTraceElement[] trace = worker.getStackTrace(); // a snapshot of worker's CURRENT frames
            if (trace.length > 0) {
                System.out.println("sample " + i + ": worker's current top frame = " + trace[0]);
            }
        }

        keepRunning = false;
        worker.join();
        System.out.println("worker thread stopped");
    }
}
```

**How to run:** `java SamplingAnotherThreadsPosition.java`.

Expected output shape (the reported top frame may vary between `busyLoop` and `doSomeWork` across samples, reflecting the worker thread's genuinely changing execution position over time):
```
sample 0: worker's current top frame = SamplingAnotherThreadsPosition.busyLoop(SamplingAnotherThreadsPosition.java:6)
sample 1: worker's current top frame = SamplingAnotherThreadsPosition.busyLoop(SamplingAnotherThreadsPosition.java:9)
sample 2: worker's current top frame = SamplingAnotherThreadsPosition.doSomeWork(SamplingAnotherThreadsPosition.java:14)
sample 3: worker's current top frame = SamplingAnotherThreadsPosition.busyLoop(SamplingAnotherThreadsPosition.java:6)
sample 4: worker's current top frame = SamplingAnotherThreadsPosition.busyLoop(SamplingAnotherThreadsPosition.java:9)
worker thread stopped
```

This adds the production-flavored hard case: using `Thread.getStackTrace()` to sample a *different*, concurrently-running thread's current execution position from `main`, at several distinct real-time moments — each sample is effectively a snapshot derived from the worker thread's own current PC register (and stack), and since the worker genuinely continues executing between samples, successive samples can (and typically do) show different top frames, directly demonstrating that the underlying position being reported is real, live, per-thread state that changes continuously as that thread runs, not a static or cached value.

## 6. Walkthrough

Tracing what happens conceptually during `SamplingAnotherThreadsPosition.main`'s sampling loop:

1. `worker.start()` begins running `busyLoop` on its own thread, with its own private PC register beginning to advance through that method's bytecode instructions as the loop iterates.
2. `main`'s loop calls `Thread.sleep(20)`, yielding `main`'s own execution for roughly 20ms while `worker` continues running independently, its PC register advancing the entire time.
3. `worker.getStackTrace()` — called from `main`, targeting a *different* thread object — asks the JVM to produce a snapshot of `worker`'s current call stack, which internally reflects exactly where `worker`'s PC register (and the PC-equivalent position within each of its stack frames) currently sits at the moment the snapshot is taken.
4. Because `worker` is genuinely still running (not paused or waiting for this sampling), by the time `main` requests the *next* sample 20ms later, `worker`'s PC register has advanced further — potentially still within the same method (`busyLoop`, at a different line), or possibly into a different method entirely (`doSomeWork`, if `worker` happened to be executing that call at the sampled instant).
5. Each printed sample line is therefore a real, live report of `worker`'s current execution position at that specific moment — not a static value, and not something `main` computed itself, but something the JVM derived from `worker`'s own private, continuously-advancing PC register.
6. Once `keepRunning` is set to `false`, `worker`'s loop condition eventually evaluates to false (thanks to `volatile`'s visibility guarantee), `busyLoop` returns, and `worker.join()` in `main` returns once the thread has fully terminated — its PC register (along with the rest of its now-discarded stack) ceasing to exist along with the thread itself.

## 7. Gotchas & takeaways

> **Gotcha:** there is no public Java API to directly read a thread's PC register value as a raw number or bytecode offset — everything demonstrated here observes its *effect* (via stack traces and line numbers) rather than the register itself; treat the PC register as a conceptual, JVM-internal detail useful for understanding *why* stack traces and thread sampling behave the way they do, not as something you'll ever manipulate directly in application code.

- Each thread maintains its own private PC register, tracking the current bytecode instruction position within that thread's currently executing frame.
- For native (JNI) methods, the PC register's value is undefined by the JVM Specification, since native code execution isn't tracked at the bytecode-instruction level the JVM itself manages.
- The PC register's effect is directly visible in every stack trace's line numbers, and in tools like `Thread.getStackTrace()` that sample another thread's current execution position — both are ultimately derived from this per-thread state.
- Two threads executing the identical shared method bytecode concurrently make independent progress through it, entirely thanks to each maintaining its own separate PC register (and stack) — there's no shared "current position" for a method across threads.
- See [JVM stacks & stack frames](0913-jvm-stacks-stack-frames.md) and [native method stacks](0915-native-method-stacks.md) for the other per-thread runtime data areas that, together with the PC register, constitute a thread's complete private execution state.
