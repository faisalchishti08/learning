---
card: java
gi: 284
slug: runtime-class
title: Runtime class
---

## 1. What it is

`java.lang.Runtime` represents the running JVM process itself, giving programmatic access to JVM-level information and operations: available and total memory, the number of available processors, registering shutdown hooks (as the previous topic used), and running external system commands. Unlike `System`'s static methods, `Runtime` is accessed through a singleton instance obtained via `Runtime.getRuntime()` — there is always exactly one `Runtime` object per JVM process.

```java
public class RuntimeDemo {
    public static void main(String[] args) {
        Runtime runtime = Runtime.getRuntime(); // the ONE Runtime instance for this JVM

        System.out.println("Available processors: " + runtime.availableProcessors());
        System.out.println("Total memory: " + runtime.totalMemory() + " bytes");
        System.out.println("Free memory: " + runtime.freeMemory() + " bytes");
        System.out.println("Max memory: " + runtime.maxMemory() + " bytes");
    }
}
```

`Runtime.getRuntime()` always returns the same singleton object for the entire JVM process; its instance methods (`availableProcessors()`, `totalMemory()`, `freeMemory()`, `maxMemory()`) report live, current information about the JVM's actual resource usage and environment at the moment they're called.

## 2. Why & when

`Runtime` provides access to JVM-level facts and operations that don't belong to any particular class or object in your program, but rather to the running process as a whole.

- **Inspecting memory usage** — `totalMemory()` (memory currently allocated to the JVM heap), `freeMemory()` (unused portion of that allocated memory), and `maxMemory()` (the maximum the heap could ever grow to, based on JVM configuration) together give a picture of the JVM's current memory situation, useful for diagnostics, monitoring, or deciding whether to trigger some memory-sensitive behaviour.
- **Discovering available parallelism** — `availableProcessors()` reports how many processor cores the JVM has access to, information commonly used to decide how many worker threads to create for a parallel task, so the program can scale its concurrency to the actual hardware it's running on.
- **Registering shutdown hooks and running external processes** — `addShutdownHook` (used in the previous topic) and `exec(...)` (for launching external system commands or programs from within Java) are both `Runtime` methods, letting a Java program interact with the broader operating system environment beyond its own JVM process.

Use `Runtime.getRuntime()` when you need information about the JVM process itself — available memory, processor count — typically for diagnostics, monitoring, adaptive concurrency (choosing a thread pool size based on `availableProcessors()`), or the rarer need to launch an external system process directly from Java.

## 3. Core concept

```java
public class RuntimeCore {
    static void printMemoryUsage() {
        Runtime runtime = Runtime.getRuntime();
        long total = runtime.totalMemory();
        long free = runtime.freeMemory();
        long used = total - free; // memory ACTUALLY in use right now
        System.out.println("Used memory: " + (used / 1024 / 1024) + " MB");
    }
}
```

`used = total - free` is the standard way to compute actual memory in use: `totalMemory()` reports how much the JVM has currently allocated from the operating system (which can grow up to `maxMemory()`), and `freeMemory()` reports the unused portion of that already-allocated amount — subtracting gives the memory genuinely occupied by live objects and other JVM overhead at this exact moment.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Runtime is a singleton accessed via Runtime.getRuntime, providing methods for total memory, free memory, max memory, available processors, shutdown hooks and running external processes">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="220" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Runtime.getRuntime()</text>

  <rect x="40" y="80" width="150" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">totalMemory/freeMemory</text>

  <rect x="210" y="80" width="150" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="285" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">availableProcessors()</text>

  <rect x="380" y="80" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="100" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">addShutdownHook / exec</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">One singleton Runtime object per JVM, exposing process-level information and operations.</text>
</svg>

`Runtime` is a singleton exposing JVM process-level memory, processor, and lifecycle information.

## 5. Runnable example

Scenario: a small resource-monitoring utility using `Runtime`, evolved from basic memory reporting into a parallelism-aware task planner, then hardened with a simple memory-pressure check before running a memory-intensive operation.

### Level 1 — Basic

```java
public class RuntimeBasic {
    public static void main(String[] args) {
        Runtime runtime = Runtime.getRuntime();
        System.out.println("Processors available: " + runtime.availableProcessors());
    }
}
```

**How to run:** `java RuntimeBasic.java`

`availableProcessors()` reports how many cores the JVM has access to on the machine it's currently running on — this number varies depending on the actual hardware, unlike a hard-coded constant.

### Level 2 — Intermediate

Same idea, now using `availableProcessors()` to decide how many worker "tasks" to conceptually divide work into — a common, realistic use case for adaptive concurrency planning.

```java
public class RuntimeIntermediate {
    static void planWork(int totalItems) {
        int processors = Runtime.getRuntime().availableProcessors();
        int itemsPerWorker = (int) Math.ceil((double) totalItems / processors);
        System.out.println("Processors: " + processors);
        System.out.println("Total items: " + totalItems);
        System.out.println("Items per worker: " + itemsPerWorker);
    }

    public static void main(String[] args) {
        planWork(1000);
    }
}
```

**How to run:** `java RuntimeIntermediate.java`

`itemsPerWorker` is computed by dividing the total work evenly across however many processors are actually available on the current machine — the same source code automatically adapts its planned division of labor to whatever hardware it happens to run on, rather than assuming a fixed number of cores.

### Level 3 — Advanced

Same resource-monitoring idea, now checking available memory before attempting a memory-intensive operation, and reporting a full memory summary — a realistic pattern for defensive resource-aware code.

```java
public class RuntimeAdvanced {
    static boolean hasEnoughFreeMemory(long requiredBytes) {
        Runtime runtime = Runtime.getRuntime();
        long maxMemory = runtime.maxMemory();
        long allocatedMemory = runtime.totalMemory();
        long freeMemory = runtime.freeMemory();
        long actuallyAvailable = freeMemory + (maxMemory - allocatedMemory); // free space plus room to grow

        return actuallyAvailable >= requiredBytes;
    }

    static void printMemorySummary() {
        Runtime runtime = Runtime.getRuntime();
        long mb = 1024 * 1024;
        System.out.println("Max memory: " + (runtime.maxMemory() / mb) + " MB");
        System.out.println("Total allocated: " + (runtime.totalMemory() / mb) + " MB");
        System.out.println("Free (of allocated): " + (runtime.freeMemory() / mb) + " MB");
    }

    public static void main(String[] args) {
        printMemorySummary();

        long requiredForOperation = 10L * 1024 * 1024; // hypothetical: this operation needs ~10 MB
        if (hasEnoughFreeMemory(requiredForOperation)) {
            System.out.println("Proceeding: sufficient memory available for a ~10 MB operation");
        } else {
            System.out.println("Skipping operation: insufficient memory available");
        }
    }
}
```

**How to run:** `java RuntimeAdvanced.java`

`hasEnoughFreeMemory` accounts for both the *currently free* portion of already-allocated memory (`freeMemory()`) and the *additional room the heap could still grow into* (`maxMemory() - totalMemory()`), since the JVM can allocate more memory from the operating system up to its configured maximum as needed — a more complete and realistic picture of "how much memory could actually become available" than checking `freeMemory()` alone.

## 6. Walkthrough

Trace `main` in `RuntimeAdvanced` conceptually (exact byte values vary by machine and JVM configuration, so the walkthrough focuses on the logic, not specific numbers).

**`printMemorySummary()`.** Retrieves the `Runtime` singleton and calls `maxMemory()`, `totalMemory()`, and `freeMemory()`, each divided by `1024 * 1024` to convert bytes into megabytes for readability. Prints three lines summarizing the JVM's current memory configuration and usage — say, hypothetically, `"Max memory: 4096 MB"`, `"Total allocated: 256 MB"`, `"Free (of allocated): 200 MB"`.

**`requiredForOperation = 10L * 1024 * 1024`.** Computes `10,485,760` bytes (10 megabytes), the hypothetical memory need for the upcoming operation.

**`hasEnoughFreeMemory(10485760)`.** Retrieves `maxMemory` (say, `4096` MB worth of bytes), `allocatedMemory` (say, `256` MB worth), and `freeMemory` (say, `200` MB worth). Computes `actuallyAvailable = freeMemory + (maxMemory - allocatedMemory)` — using the hypothetical numbers, this is `200 MB + (4096 MB - 256 MB) = 200 MB + 3840 MB = 4040 MB` worth of bytes, representing both the currently-free portion of allocated memory and the additional room the heap could still grow into. Since `4040` MB is vastly more than the required `10` MB, the method returns `true`.

**Back in `main`, the `if` branch runs.** Prints `"Proceeding: sufficient memory available for a ~10 MB operation"`.

```
printMemorySummary() (illustrative values):
  maxMemory = 4096 MB, totalMemory = 256 MB, freeMemory = 200 MB

hasEnoughFreeMemory(10 MB required):
  actuallyAvailable = freeMemory + (maxMemory - totalMemory)
                    = 200 MB + (4096 MB - 256 MB)
                    = 200 MB + 3840 MB = 4040 MB
  4040 MB >= 10 MB required -> true -> proceed
```

**Illustrative final output** (actual numbers depend entirely on the JVM's configuration and current state at runtime):
```
Max memory: 4096 MB
Total allocated: 256 MB
Free (of allocated): 200 MB
Proceeding: sufficient memory available for a ~10 MB operation
```

## 7. Gotchas & takeaways

> **`freeMemory()` alone significantly underestimates how much memory could actually become available**, since it only reports the unused portion of memory the JVM has *already* allocated from the operating system (`totalMemory()`), not the additional headroom the heap could still grow into, up to `maxMemory()`. A memory-availability check based only on `freeMemory()` could incorrectly conclude memory is scarce, when in fact the JVM simply hasn't needed to allocate more from the OS yet — accounting for `maxMemory() - totalMemory()` as additional available headroom, as `hasEnoughFreeMemory` does, gives a much more accurate picture.

> **These memory figures are inherently approximate and can change from moment to moment, especially in a program actively creating and discarding objects** — garbage collection can run between the time you check `freeMemory()` and the time you actually use that memory, changing the picture entirely; treat these numbers as rough guidance for diagnostics or coarse-grained decisions, not as a precise, real-time guarantee about exactly how much memory will be available at the instant your subsequent code runs.

- `Runtime.getRuntime()` returns the single `Runtime` instance representing the current JVM process, providing access to memory statistics, processor count, shutdown hooks, and external process execution.
- `totalMemory()`, `freeMemory()`, and `maxMemory()` together describe the JVM's current memory allocation, usage, and configured ceiling — subtracting `freeMemory()` from `totalMemory()` gives memory actually in use right now.
- `availableProcessors()` reports the number of processor cores accessible to the JVM, commonly used to adapt a program's concurrency (like thread pool sizing) to the actual hardware it's running on.
- Memory figures reported by `Runtime` are approximate snapshots that can change moment to moment; use them for diagnostics and coarse decisions, not as precise real-time guarantees.
