---
card: java
gi: 314
slug: runnable-interface
title: Runnable interface
---

## 1. What it is

`Runnable` is a functional interface with a single method, `void run()`, representing a task with no arguments and no return value. It's the standard way to describe "a piece of work to execute," used both as the argument to `Thread`'s constructor and, more broadly, anywhere a simple, parameterless action needs to be passed around.

```java
public class RunnableDemo {
    public static void main(String[] args) {
        Runnable task = () -> System.out.println("Task executed by: " + Thread.currentThread().getName());

        task.run();               // runs directly, on the CURRENT thread -- no new thread involved
        new Thread(task).start(); // runs on a NEW thread
    }
}
```

Calling `task.run()` directly executes the code on whichever thread makes the call (here, the main thread) — `Runnable` by itself has nothing to do with threads; wrapping it in `new Thread(task)` and calling `start()` is what actually runs it on a separate thread.

## 2. Why & when

`Thread`'s constructor needs some way to be told *what code to run* — `Runnable` is that "what to run" abstraction, deliberately separated from `Thread` itself (which represents "the mechanism for running it concurrently"). This separation is useful even outside of threading.

- **Decoupling "what" from "how it runs"** — the same `Runnable` task can be run directly (`task.run()`), on a new thread (`new Thread(task).start()`), or submitted to a thread pool (`executor.submit(task)`) without changing the task's code at all.
- **A general-purpose "action" type** — because it's just "no arguments, no return value," `Runnable` is used throughout Java APIs (Swing event handlers, scheduled tasks) wherever a simple callback is needed, independent of threading.
- **Lambda-friendly** — being a functional interface, `Runnable` pairs naturally with lambda expressions, making inline task definitions concise.

Use `Runnable` (typically as a lambda) whenever you need to pass around "a task to run" — whether or not it ends up on a separate thread. Reach for `Thread` specifically when you need that task to run concurrently; for a return value or the ability to throw a checked exception, use `Callable` (from `java.util.concurrent`) instead, since `Runnable.run()` can't return anything or throw checked exceptions.

## 3. Core concept

```java
public class RunnableCore {
    static class PrintTask implements Runnable { // an alternative to a lambda: an explicit class
        private final String message;
        PrintTask(String message) { this.message = message; }
        public void run() {
            System.out.println(message + " from " + Thread.currentThread().getName());
        }
    }

    public static void main(String[] args) {
        Runnable lambdaTask = () -> System.out.println("Lambda task from " + Thread.currentThread().getName());
        Runnable classTask = new PrintTask("Class-based task");

        lambdaTask.run();
        classTask.run();
    }
}
```

A lambda expression and an explicit class both satisfy the same `Runnable` interface — the lambda form is more concise for simple, stateless tasks, while an explicit class (as with `PrintTask`) is useful when the task needs constructor parameters or more elaborate internal state.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same Runnable task can be executed directly, on a new thread, or submitted to an executor, without changing the task itself">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <rect x="240" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="45" fill="#6db33f" font-size="10" text-anchor="middle">Runnable task</text>

  <line x1="270" y1="60" x2="120" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#r1)"/>
  <text x="120" y="115" fill="#8b949e" font-size="9" text-anchor="middle">task.run() directly</text>

  <line x1="300" y1="60" x2="300" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#r2)"/>
  <text x="300" y="115" fill="#8b949e" font-size="9" text-anchor="middle">new Thread(task).start()</text>

  <line x1="330" y1="60" x2="480" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#r3)"/>
  <text x="480" y="115" fill="#8b949e" font-size="9" text-anchor="middle">executor.submit(task)</text>
  <defs>
    <marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="r2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="r3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The task's definition is completely independent of how (or whether) it ends up running concurrently.

## 5. Runnable example

Scenario: a small notification-sending task, evolved from running it directly (no concurrency at all) into running it on a background thread, then into a reusable, parameterized `Runnable` factory that creates multiple independent tasks for different recipients.

### Level 1 — Basic

```java
public class RunnableBasic {
    public static void main(String[] args) {
        Runnable sendNotification = () -> {
            System.out.println("Sending notification... (on " + Thread.currentThread().getName() + ")");
        };

        sendNotification.run(); // runs directly, synchronously, on the main thread
        System.out.println("Notification sent.");
    }
}
```

**How to run:** `java RunnableBasic.java`

Calling `run()` directly executes the task synchronously on the calling thread — no concurrency happens here at all; this establishes the baseline behavior before threads are introduced.

### Level 2 — Intermediate

Same notification task, now run on a background thread via `new Thread(...)`, so the main thread can continue immediately without waiting for it to complete.

```java
public class RunnableIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Runnable sendNotification = () -> {
            try {
                Thread.sleep(100); // simulate a slow network call
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            System.out.println("Notification sent (on " + Thread.currentThread().getName() + ")");
        };

        Thread backgroundThread = new Thread(sendNotification);
        backgroundThread.start();

        System.out.println("Main thread continues immediately, not waiting for the notification.");
        backgroundThread.join(); // wait here just so the program doesn't exit before the thread finishes
    }
}
```

**How to run:** `java RunnableIntermediate.java`

The exact same `sendNotification` task now runs on `backgroundThread` instead of directly — the main thread's `println` reliably prints *before* the notification's, since the background thread is deliberately slowed down by `Thread.sleep(100)`, demonstrating genuine concurrent, non-blocking execution.

### Level 3 — Advanced

Same idea, now generalized into a factory method that creates a distinct, parameterized `Runnable` for each of several recipients, launching one background thread per notification — demonstrating `Runnable` as a reusable task blueprint rather than a single hardcoded action.

```java
public class RunnableAdvanced {
    static Runnable notificationTask(String recipient, int delayMillis) {
        return () -> {
            try {
                Thread.sleep(delayMillis);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
            System.out.println("Notified " + recipient + " (after " + delayMillis + "ms, on " + Thread.currentThread().getName() + ")");
        };
    }

    public static void main(String[] args) throws InterruptedException {
        String[] recipients = {"alice@example.com", "bob@example.com", "carol@example.com"};
        int[] delays = {300, 100, 200};

        Thread[] threads = new Thread[recipients.length];
        for (int i = 0; i < recipients.length; i++) {
            Runnable task = notificationTask(recipients[i], delays[i]);
            threads[i] = new Thread(task);
            threads[i].start();
        }

        for (Thread t : threads) t.join();
        System.out.println("All notifications sent.");
    }
}
```

**How to run:** `java RunnableAdvanced.java`

`notificationTask(recipient, delayMillis)` is a factory that returns a fresh, independent `Runnable` closing over its own `recipient` and `delayMillis` values — three distinct tasks are created and each launched on its own thread, so they run concurrently, and because their delays differ (300ms, 100ms, 200ms), their completion order in the printed output reliably follows the delay order (Bob first, then Carol, then Alice) rather than the order they were started in.

## 6. Walkthrough

Trace `RunnableAdvanced.main` step by step.

**Setup.** `recipients` and `delays` are parallel arrays: Alice with 300ms, Bob with 100ms, Carol with 200ms.

**Task creation and thread launch loop.** For `i = 0`: `notificationTask("alice@example.com", 300)` returns a `Runnable` — a lambda that, when run, sleeps 300ms and then prints a message naming Alice. `threads[0] = new Thread(task)` wraps it; `threads[0].start()` launches it immediately, and the loop moves on without waiting. The same happens for `i = 1` (Bob, 100ms) and `i = 2` (Carol, 200ms) — all three threads are started in rapid succession, essentially simultaneously from the main thread's perspective.

**Concurrent sleeping.** All three background threads are now independently sleeping for their respective durations. Bob's thread, sleeping only 100ms, wakes up first; it prints its message. Carol's thread, at 200ms, wakes up next and prints. Alice's thread, at 300ms, wakes up last and prints.

**The `join` loop.** `for (Thread t : threads) t.join()` waits for `threads[0]` (Alice's thread) first — even though Alice's thread finishes *last* chronologically, the loop still waits for it in array order; since `join()` simply blocks until the target thread is done (regardless of when other threads finish), this loop effectively waits for the *slowest* of all three by the time it's done iterating, even though it checks them in `[Alice, Bob, Carol]` order.

**Final print.** Only after all three threads have genuinely completed does `"All notifications sent."` print — guaranteed by the `join` loop, regardless of the actual completion order of the individual notifications.

```
t=0ms:   start Alice-thread(300ms), Bob-thread(100ms), Carol-thread(200ms)  -- all nearly simultaneous
t=100ms: Bob's thread wakes -> prints "Notified bob..."
t=200ms: Carol's thread wakes -> prints "Notified carol..."
t=300ms: Alice's thread wakes -> prints "Notified alice..."

join() loop waits for all three (in array order, but effectively bounded by the slowest)
-> "All notifications sent." prints last, after t=300ms
```

**Output:**
```
Notified bob@example.com (after 100ms, on Thread-1)
Notified carol@example.com (after 200ms, on Thread-2)
Notified alice@example.com (after 300ms, on Thread-0)
All notifications sent.
```

## 7. Gotchas & takeaways

> Calling `run()` directly on a `Runnable` does **not** start a new thread — it simply executes the method body synchronously on whichever thread makes the call, exactly like calling any other method. Only passing the `Runnable` to `new Thread(...)` and then calling `start()` on that `Thread` actually introduces concurrency. Confusing `run()` with `start()` is one of the most common beginner mistakes with threading.

> A lambda implementing `Runnable` that throws a checked exception (like `InterruptedException` from `Thread.sleep`) must catch it internally, since `Runnable.run()`'s signature declares no checked exceptions — this is exactly why the examples above wrap `Thread.sleep` in a `try`/`catch`, typically re-asserting the interrupt via `Thread.currentThread().interrupt()` so the signal isn't silently swallowed.

- `Runnable` is a functional interface (`void run()`) representing a task with no arguments or return value — independent of any particular way of executing it.
- Calling `run()` directly executes synchronously on the current thread; wrapping in `new Thread(...)` and calling `start()` runs it concurrently.
- The same `Runnable` can be run directly, on a new thread, or submitted to a thread pool, without any change to the task's own code.
- `Runnable.run()` cannot throw checked exceptions or return a value — use `Callable` (from `java.util.concurrent`) when either is needed.
