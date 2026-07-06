---
card: java
gi: 315
slug: starting-threads-start-vs-run
title: Starting threads (start vs run)
---

## 1. What it is

`Thread` has two methods that look similar but behave completely differently: `start()` creates a new operating-system-backed thread and runs the task on it, concurrently with the caller; `run()` simply executes the task's code immediately, synchronously, on whichever thread calls it — exactly as if you'd called any ordinary method, with no new thread involved at all.

```java
public class StartVsRunDemo {
    public static void main(String[] args) {
        Thread t = new Thread(() -> System.out.println("Executing on: " + Thread.currentThread().getName()));

        System.out.println("Calling run() directly:");
        t.run(); // NOT a new thread -- runs on the main thread

        Thread t2 = new Thread(() -> System.out.println("Executing on: " + Thread.currentThread().getName()));
        System.out.println("Calling start():");
        t2.start(); // genuinely a new thread
    }
}
```

`t.run()` prints `"main"` as the thread name (because it truly ran on the main thread, having never created a new one); `t2.start()` prints a different thread name (something like `"Thread-0"`), because it genuinely launched a new thread to execute the task.

## 2. Why & when

`Thread` implements `Runnable`, and `run()` is simply the method that contains the task's code — but calling it directly is just an ordinary method call, no different from calling any other method on any other object. `start()` is the method that actually asks the JVM and operating system to allocate and begin a new thread of execution, which then calls `run()` internally, on that new thread.

- **`start()` for concurrency** — this is what you call whenever the point is to run something in parallel with the calling code.
- **`run()` for direct execution** — calling it explicitly is functionally identical to inlining the task's code at that point; occasionally useful when you deliberately want the "same code path" without the overhead or non-determinism of an actual new thread (e.g., a fallback, or testing the task's logic without concurrency).
- **A single `Thread` object can only be started once** — calling `start()` a second time on the same `Thread` object throws `IllegalThreadStateException`, since a `Thread` object represents one specific thread's lifecycle, not a reusable task launcher.

Always use `start()` when your intent is "run this concurrently." Calling `run()` directly is a real, if less common, way to reuse a `Runnable`'s code synchronously, but doing so *by mistake*, believing it starts a thread, is one of the most common and confusing threading bugs — the code compiles fine and often even seems to work in casual testing, since it does execute the task's logic, just without concurrency.

## 3. Core concept

```java
public class StartVsRunCore {
    public static void main(String[] args) throws InterruptedException {
        Thread t = new Thread(() -> {
            for (int i = 0; i < 3; i++) System.out.println("Working: " + i);
        });

        t.start();
        System.out.println("This line may print BEFORE, DURING, or interleaved with 'Working' lines.");
        t.join();
        System.out.println("Guaranteed to print AFTER all 'Working' lines, because of join().");
    }
}
```

After `start()`, the main thread's own `println` calls race against the new thread's `println` calls with no guaranteed ordering between them — only `join()` establishes a definite "happens after" relationship, which is why the final line's ordering guarantee explicitly depends on it, unlike the middle line's.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="run called directly executes on the calling thread with no concurrency, start creates a genuinely separate thread">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="150" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">thread.run()</text>
  <text x="150" y="68" fill="#8b949e" font-size="9" text-anchor="middle">ordinary method call, same thread, no concurrency</text>

  <rect x="310" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="440" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">thread.start()</text>
  <text x="440" y="68" fill="#8b949e" font-size="9" text-anchor="middle">new OS thread, genuinely concurrent</text>

  <text x="20" y="110" fill="#8b949e" font-size="9">Both eventually call the SAME run() method body -- the difference is entirely in HOW it gets invoked.</text>
</svg>

`run()` is just a method; `start()` is what actually creates concurrency.

## 5. Runnable example

Scenario: a small "background task" simulation, evolved from an accidental misuse of `run()` (revealing the bug) into the correct use of `start()`, then into a version that defensively guards against the common mistake of calling `start()` twice on the same `Thread` object.

### Level 1 — Basic

```java
public class StartVsRunBasic {
    public static void main(String[] args) {
        Thread task = new Thread(() -> {
            System.out.println("Task running on: " + Thread.currentThread().getName());
        });

        // BUG (intentional, for demonstration): calling run() instead of start().
        task.run();
        System.out.println("Main thread: " + Thread.currentThread().getName());
    }
}
```

**How to run:** `java StartVsRunBasic.java`

Both lines print `"main"` as the thread name — the task never actually ran on a separate thread, because `run()` was called directly instead of `start()`, a subtle but common mistake this example deliberately reproduces.

### Level 2 — Intermediate

Same task, now correctly using `start()`, demonstrating the difference explicitly by printing distinct thread names.

```java
public class StartVsRunIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Thread task = new Thread(() -> {
            System.out.println("Task running on: " + Thread.currentThread().getName());
        });

        task.start(); // FIXED: genuinely starts a new thread
        task.join();  // wait for it, so output ordering is deterministic for this demo
        System.out.println("Main thread: " + Thread.currentThread().getName());
    }
}
```

**How to run:** `java StartVsRunIntermediate.java`

The task's line now prints a different thread name (like `"Thread-0"`) than the main thread's line (`"main"`) — concrete, visible proof that `start()` genuinely ran the task on a separate thread, unlike Level 1.

### Level 3 — Advanced

Same task, now demonstrating the `IllegalThreadStateException` that results from calling `start()` twice on the same `Thread` object, and the correct fix: creating a fresh `Thread` object each time the task needs to run again.

```java
public class StartVsRunAdvanced {
    public static void main(String[] args) throws InterruptedException {
        Runnable taskLogic = () -> System.out.println("Running on: " + Thread.currentThread().getName());

        Thread t = new Thread(taskLogic);
        t.start();
        t.join();

        try {
            t.start(); // BUG: attempting to restart the SAME Thread object
            System.out.println("Unexpected: second start() succeeded");
        } catch (IllegalThreadStateException e) {
            System.out.println("Caught expected exception: " + e);
        }

        // CORRECT fix: create a brand-new Thread object to run the task again.
        Thread t2 = new Thread(taskLogic);
        t2.start();
        t2.join();
        System.out.println("Second run, via a NEW Thread object, succeeded.");
    }
}
```

**How to run:** `java StartVsRunAdvanced.java`

`t.start()` followed by `t.join()` runs the task once, to completion; calling `t.start()` again on that *same* `Thread` object fails, because a `Thread` object's internal state tracks that it has already been started and terminated — the correct way to "run the task again" is to construct a brand-new `Thread` object (`t2`) wrapping the same `Runnable` (`taskLogic`), since the reusable part is the task's logic, not the `Thread` object itself.

## 6. Walkthrough

Trace `StartVsRunAdvanced.main` step by step.

**First run.** `t = new Thread(taskLogic)` creates a new `Thread` object in the "new" (not-yet-started) state. `t.start()` transitions it to "runnable"/"running," launching a real OS-backed thread that executes `taskLogic`, printing its thread name. `t.join()` blocks until that thread finishes, after which `t`'s internal state becomes "terminated."

**Attempting to restart.** `t.start()` is called again on the same, now-terminated `t` object. Internally, `Thread.start()` checks its own state before doing any work; since `t` is already in the "terminated" state (having run to completion), this check fails, and `start()` throws `IllegalThreadStateException` immediately — no new thread is created, and `taskLogic` does not run a second time via this call.

**Catching the exception.** The `try`/`catch` block catches this exception and prints its message, confirming the expected failure. `System.out.println("Unexpected: ...")` never executes, since the exception was thrown before reaching that line.

**The correct fix.** `t2 = new Thread(taskLogic)` creates a **different** `Thread` object — a fresh one, starting in the "new" state — wrapping the exact same `taskLogic` `Runnable` instance (there's no problem reusing the `Runnable` itself; only `Thread` objects are single-use). `t2.start()` succeeds because `t2` has never been started before. `t2.join()` waits for it to finish, and the final print confirms success.

```
t = new Thread(taskLogic)   [state: NEW]
t.start()                   [state: NEW -> RUNNABLE -> ... ]
t.join()                    [waits; state becomes TERMINATED]

t.start() again             [state is TERMINATED -> IllegalThreadStateException]

t2 = new Thread(taskLogic)  [state: NEW  -- a DIFFERENT Thread object]
t2.start()                  [succeeds, state: NEW -> RUNNABLE -> ...]
t2.join()                   [waits; state becomes TERMINATED]
```

**Output:**
```
Running on: Thread-0
Caught expected exception: java.lang.IllegalThreadStateException
Running on: Thread-1
Second run, via a NEW Thread object, succeeded.
```

## 7. Gotchas & takeaways

> Calling `run()` directly instead of `start()` is a silent bug: the code compiles, the task's logic executes correctly, and casual testing may not reveal anything wrong — the only symptom is the complete absence of actual concurrency, which often only becomes apparent when you specifically check `Thread.currentThread().getName()` or notice that expected parallel speedup never materializes.

> Each `Thread` object can be started exactly once — attempting `start()` a second time (even after the first run has fully completed) throws `IllegalThreadStateException`. To "run the same task again," create a new `Thread` object wrapping the same `Runnable`; the `Runnable` itself is perfectly reusable across as many `Thread` objects as needed.

- `run()` called directly executes synchronously on the calling thread — no new thread, no concurrency, just an ordinary method call.
- `start()` genuinely creates a new thread and runs the task on it concurrently with the caller.
- A `Thread` object can only be started once; attempting to restart a terminated (or already-running) `Thread` throws `IllegalThreadStateException`.
- To run the same task logic again, wrap the same `Runnable` in a brand-new `Thread` object rather than reusing the old one.
