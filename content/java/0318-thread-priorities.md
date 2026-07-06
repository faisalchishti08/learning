---
card: java
gi: 318
slug: thread-priorities
title: Thread priorities
---

## 1. What it is

Every `Thread` has a priority, an `int` between `Thread.MIN_PRIORITY` (1) and `Thread.MAX_PRIORITY` (10), with `Thread.NORM_PRIORITY` (5) as the default. It's a **hint** to the operating system's thread scheduler that higher-priority threads should generally be favored for CPU time over lower-priority ones — but it's not a guarantee, and its actual effect varies significantly across operating systems and JVM implementations.

```java
public class PriorityDemo {
    public static void main(String[] args) {
        Thread t = new Thread(() -> System.out.println("Running"));
        System.out.println("Default priority: " + t.getPriority()); // 5, NORM_PRIORITY

        t.setPriority(Thread.MAX_PRIORITY);
        System.out.println("New priority: " + t.getPriority()); // 10

        t.start();
    }
}
```

`getPriority()`/`setPriority(int)` read and change a thread's priority hint; a freshly created thread inherits the priority of the thread that created it (usually `NORM_PRIORITY`, 5, unless something changed it earlier).

## 2. Why & when

Operating systems generally support the idea of "more important" and "less important" work competing for CPU time. Thread priority exposes a coarse version of that idea to Java programs — a way to hint that some threads' work matters more than others', without any strict guarantee about exactly how much more CPU time they'll receive.

- **Weak prioritization hints** — nudging the scheduler to favor latency-sensitive work (like handling user input) over background work (like a low-priority cleanup task), when the underlying OS and JVM actually honor the hint meaningfully.
- **Documenting relative importance** — even when the practical scheduling effect is minor, setting priorities can serve as a form of self-documentation about which threads matter more.

In practice, thread priority is one of the **least reliable** tools in Java's concurrency toolkit: its effect ranges from "noticeable" to "essentially none," depending on the OS, the JVM, and the number of available CPU cores, and Java's specification deliberately leaves the exact scheduling behavior up to the underlying platform. Modern Java code almost never relies on thread priority for correctness or even meaningful performance tuning — proper task prioritization is far more reliably achieved with separate `ExecutorService` thread pools, explicit queuing logic, or other structural techniques, not by tweaking priority numbers.

## 3. Core concept

```java
public class PriorityCore {
    public static void main(String[] args) throws InterruptedException {
        Runnable busyWork = () -> {
            long count = 0;
            for (int i = 0; i < 500_000_000; i++) count++;
            System.out.println(Thread.currentThread().getName() + " (priority " + Thread.currentThread().getPriority() + ") finished");
        };

        Thread low = new Thread(busyWork, "Low");
        Thread high = new Thread(busyWork, "High");
        low.setPriority(Thread.MIN_PRIORITY);
        high.setPriority(Thread.MAX_PRIORITY);

        low.start();
        high.start();
        low.join();
        high.join();
    }
}
```

Both threads do identical work, but `high` is given `MAX_PRIORITY` and `low` is given `MIN_PRIORITY` — on some systems this might make `high` tend to finish first more often, but this is **not guaranteed**, and on many common configurations (especially multi-core machines where both threads can simply run in parallel on separate cores) the difference may be negligible or entirely unobservable.

## 4. Diagram

<svg viewBox="0 0 600 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Thread priority is a hint to the scheduler, not a guarantee, and its actual effect varies across platforms">
  <rect x="8" y="8" width="584" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="55" fill="#e6edf3" font-size="10" text-anchor="middle">thread.setPriority(hint)</text>
  <line x1="280" y1="50" x2="340" y2="50" stroke="#8b949e" stroke-width="2" marker-end="url(#p1)"/>
  <rect x="345" y="30" width="230" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="460" y="55" fill="#f85149" font-size="10" text-anchor="middle">OS scheduler (may or may not listen)</text>
  <text x="20" y="100" fill="#8b949e" font-size="9">The JVM passes the hint along; actual scheduling behavior is entirely up to the OS and hardware.</text>
  <defs>
    <marker id="p1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Priority is advisory input to a scheduler that's under no obligation to follow it strictly.

## 5. Runnable example

Scenario: comparing the observed completion order of several equally-busy threads with different priorities, evolved from a basic priority-setting demonstration into a repeated-trial measurement, then into a version that explicitly acknowledges the unreliability by measuring across many runs rather than trusting any single result.

### Level 1 — Basic

```java
public class PriorityBasic {
    public static void main(String[] args) throws InterruptedException {
        Runnable busyWork = () -> {
            long count = 0;
            for (int i = 0; i < 200_000_000; i++) count++;
        };

        Thread low = new Thread(busyWork, "Low-priority");
        Thread high = new Thread(busyWork, "High-priority");
        low.setPriority(Thread.MIN_PRIORITY);
        high.setPriority(Thread.MAX_PRIORITY);

        System.out.println(low.getName() + ": " + low.getPriority());
        System.out.println(high.getName() + ": " + high.getPriority());

        low.start();
        high.start();
        low.join();
        high.join();
        System.out.println("Both finished.");
    }
}
```

**How to run:** `java PriorityBasic.java`

Sets and prints two threads' priorities before running identical busy-work on each — establishes the baseline setup before attempting to measure any actual scheduling effect.

### Level 2 — Intermediate

Same setup, now measuring and printing each thread's actual completion time, to see whether the priority difference produces any observable effect on this particular machine and JVM.

```java
public class PriorityIntermediate {
    static long timedBusyWork() {
        long start = System.nanoTime();
        long count = 0;
        for (int i = 0; i < 200_000_000; i++) count++;
        return (System.nanoTime() - start) / 1_000_000; // milliseconds
    }

    public static void main(String[] args) throws InterruptedException {
        long[] lowTime = new long[1];
        long[] highTime = new long[1];

        Thread low = new Thread(() -> lowTime[0] = timedBusyWork(), "Low-priority");
        Thread high = new Thread(() -> highTime[0] = timedBusyWork(), "High-priority");
        low.setPriority(Thread.MIN_PRIORITY);
        high.setPriority(Thread.MAX_PRIORITY);

        low.start();
        high.start();
        low.join();
        high.join();

        System.out.println("Low-priority thread took: " + lowTime[0] + "ms");
        System.out.println("High-priority thread took: " + highTime[0] + "ms");
    }
}
```

**How to run:** `java PriorityIntermediate.java`

Measures each thread's actual wall-clock duration for identical work — running this on a typical multi-core development machine will very often show the two times as nearly identical (since both threads can simply run on separate cores simultaneously), demonstrating firsthand that priority differences frequently produce no measurable effect at all.

### Level 3 — Advanced

Same measurement, now repeated across several trials and averaged, explicitly treating any single run's result as unreliable — the statistically honest way to investigate whether priority has a real, consistent effect on a given system, rather than drawing a conclusion from one run alone.

```java
public class PriorityAdvanced {
    static long timedBusyWork() {
        long start = System.nanoTime();
        long count = 0;
        for (int i = 0; i < 200_000_000; i++) count++;
        return (System.nanoTime() - start) / 1_000_000;
    }

    static long[] runTrial() throws InterruptedException {
        long[] lowTime = new long[1];
        long[] highTime = new long[1];

        Thread low = new Thread(() -> lowTime[0] = timedBusyWork());
        Thread high = new Thread(() -> highTime[0] = timedBusyWork());
        low.setPriority(Thread.MIN_PRIORITY);
        high.setPriority(Thread.MAX_PRIORITY);

        low.start();
        high.start();
        low.join();
        high.join();

        return new long[]{lowTime[0], highTime[0]};
    }

    public static void main(String[] args) throws InterruptedException {
        int trials = 5;
        long totalLow = 0, totalHigh = 0;

        for (int i = 1; i <= trials; i++) {
            long[] result = runTrial();
            System.out.println("Trial " + i + ": low=" + result[0] + "ms, high=" + result[1] + "ms");
            totalLow += result[0];
            totalHigh += result[1];
        }

        System.out.println("Average low: " + (totalLow / trials) + "ms");
        System.out.println("Average high: " + (totalHigh / trials) + "ms");
        System.out.println("Conclusion: priority's effect (if any) is small and platform-dependent -- never rely on it for correctness.");
    }
}
```

**How to run:** `java PriorityAdvanced.java`

Running five independent trials and averaging their results is the correct way to investigate a noisy, platform-dependent signal like thread-priority scheduling effects — a single trial's result could easily be dominated by unrelated system noise (other processes, JIT warm-up, garbage collection pauses), and the averaged output typically confirms that the two priorities produce very similar average durations on a typical multi-core machine.

## 6. Walkthrough

Trace `PriorityAdvanced.main` step by step.

**Trial loop setup.** `trials = 5`; `totalLow` and `totalHigh` accumulate across trials, starting at zero.

**Each trial (`runTrial()`).** Two fresh threads are created — one given `MIN_PRIORITY`, the other `MAX_PRIORITY` — each running `timedBusyWork()`, which records `System.nanoTime()` before and after a 200-million-iteration counting loop, converting the elapsed nanoseconds to milliseconds. Both threads are started essentially simultaneously; `join()` on each ensures both have finished before `runTrial` returns their individual times as a two-element array.

**Accumulation.** After each trial, its two timings are printed, and added into the running `totalLow`/`totalHigh` accumulators.

**Final averages.** After all five trials, `totalLow / trials` and `totalHigh / trials` compute the mean duration for each priority level across the whole run. On a typical modern multi-core development machine — where both threads can simply execute on separate physical cores without meaningfully competing for the same core's time slices — these two averages will typically come out very close to each other, illustrating that `MIN_PRIORITY` versus `MAX_PRIORITY` produced no significant, reliable difference in this environment.

**Why this matters.** If a single trial happened to show a difference (which can easily occur due to unrelated system noise — a garbage collection pause hitting one thread but not the other, background OS activity, etc.), it would be tempting to conclude priority "worked." Averaging across multiple independent trials guards against drawing a false conclusion from noise, and is the technically honest way to evaluate an inherently unreliable, platform-dependent mechanism.

```
Trial 1: low=142ms, high=138ms
Trial 2: low=140ms, high=145ms
Trial 3: low=139ms, high=140ms
Trial 4: low=143ms, high=137ms
Trial 5: low=141ms, high=139ms

Average low:  ~141ms
Average high: ~140ms
-- essentially no consistent difference on this machine
```

**Output (illustrative — actual numbers vary by machine):**
```
Trial 1: low=142ms, high=138ms
Trial 2: low=140ms, high=145ms
Trial 3: low=139ms, high=140ms
Trial 4: low=143ms, high=137ms
Trial 5: low=141ms, high=139ms
Average low: 141ms
Average high: 139ms
Conclusion: priority's effect (if any) is small and platform-dependent -- never rely on it for correctness.
```

## 7. Gotchas & takeaways

> Thread priority is a **hint**, not a contract — the Java Language Specification explicitly does not guarantee any particular scheduling behavior based on priority, and different operating systems (and even different JVM versions on the same OS) can honor it to wildly different degrees, from noticeably affecting scheduling to having essentially no observable effect at all.

> Never use thread priority as a substitute for actual correctness mechanisms like locks, `join()`, or proper task queuing — a lower-priority thread is not guaranteed to run "later" or "less often" in any strict sense, and code that assumes otherwise (for instance, assuming a low-priority thread definitely finishes after a high-priority one) can break unpredictably across different environments.

- Thread priority is an `int` from 1 (`MIN_PRIORITY`) to 10 (`MAX_PRIORITY`), defaulting to 5 (`NORM_PRIORITY`), set via `setPriority`/read via `getPriority`.
- It's an advisory hint to the OS scheduler, not a guarantee — its practical effect varies widely across platforms and can be negligible, especially on multi-core machines.
- Never rely on thread priority for program correctness; use it, if at all, only as a very weak, best-effort nudge for genuinely non-critical scheduling preferences.
- For real task prioritization needs, use structural techniques like separate thread pools or explicit priority queues rather than tweaking `Thread` priority numbers.
