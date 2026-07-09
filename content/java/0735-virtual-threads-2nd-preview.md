---
card: java
gi: 735
slug: virtual-threads-2nd-preview
title: Virtual threads (2nd preview)
---

## 1. What it is

**Java 20** (JEP 436) is the **second preview** of [virtual threads](0725-virtual-threads-preview.md), refining the feature first previewed in Java 19. The core programming model — `Thread.ofVirtual()`, `Executors.newVirtualThreadPerTaskExecutor()`, virtual threads mounting onto and unmounting from a small pool of carrier threads around blocking calls — carries forward unchanged. This round's most significant change is behind the scenes: it **removes the "thread-local" object cache** implementation detail some earlier internals relied on, and more importantly, it fixes several cases where a virtual thread would previously stay **pinned** to its carrier thread longer than necessary during blocking operations, improving throughput under real workloads. It also simplifies some of the JEP 425 API surface based on preview feedback. As with all preview features, it still requires `--enable-preview`.

## 2. Why & when

The first preview round of virtual threads shipped with a known, documented limitation: certain blocking operations performed while inside a `synchronized` block, or certain blocking file I/O operations, would **pin** the virtual thread to its carrier — meaning the carrier thread couldn't be freed to run other virtual threads during that block, temporarily defeating the scalability benefit virtual threads exist to provide. This wasn't a correctness bug (the program still produced right answers), but it was a performance trap: code that happened to combine virtual threads with `synchronized`-heavy locking, or with blocking file operations, could see far less throughput improvement than expected, and worse, wouldn't necessarily show an obvious error — just quietly reduced concurrency. JEP 436 addresses part of this by fixing specific pinning cases involving blocking file I/O operations (`java.io` operations like reading and writing files) so those no longer pin the carrier thread. This matters directly to any application using virtual threads for I/O-heavy workloads that include file access, not just network I/O — the class of pinning bugs this round fixes is exactly the kind of thing that's invisible in a small test but shows up as a real throughput ceiling under production load. The `synchronized`-block pinning limitation itself remained a known caveat through this round (fully addressed only in a later JDK), so it's still worth avoiding `synchronized` in code paths meant to run on virtual threads at high concurrency, in favor of `java.util.concurrent.locks.ReentrantLock`.

## 3. Core concept

```java
// Blocking FILE I/O inside a virtual thread — in Java 19's first preview,
// certain file I/O operations could pin the virtual thread to its carrier;
// Java 20's second preview fixes specific cases of this.
Thread.ofVirtual().start(() -> {
    try {
        byte[] data = Files.readAllBytes(Path.of("large-file.dat")); // no longer pins in the fixed cases
    } catch (IOException e) { /* ... */ }
});

// synchronized still pins in this round — prefer ReentrantLock for
// high-concurrency virtual-thread code that needs locking.
private final ReentrantLock lock = new ReentrantLock();
Thread.ofVirtual().start(() -> {
    lock.lock();
    try { /* ... */ } finally { lock.unlock(); } // does NOT pin the carrier
});
```

The programming model is identical to the first preview — this round is about making more blocking operations actually free their carrier thread the way the design always intended.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A pinned virtual thread keeps its carrier thread occupied even while blocked, defeating scalability; Java 20 fixes specific file I/O pinning cases so the carrier is freed as intended, while synchronized-block pinning remains a known caveat" >
  <rect x="20" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="42" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">Pinned (bad)</text>
  <text x="160" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">blocking call inside synchronized</text>
  <text x="160" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">carrier thread stuck, cannot switch</text>

  <rect x="340" y="20" width="280" height="80" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Unmounted (good)</text>
  <text x="480" y="66" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">blocking file I/O (fixed in Java 20)</text>
  <text x="480" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">carrier freed for another virtual thread</text>

  <text x="320" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Same virtual-thread programming model in both cases —</text>
  <text x="320" y="160" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">the difference is purely how efficiently the carrier gets reused</text>
</svg>

Correctness is identical either way; pinning only affects throughput under concurrent load.

## 5. Runnable example

Scenario: a batch file-reading workload — many virtual threads each reading a small file, standing in for I/O-heavy microservice work. It grows from a basic single-virtual-thread file read, to running many concurrent file reads via a virtual-thread-per-task executor and measuring elapsed time to observe genuine concurrency, to a version explicitly contrasting `synchronized` locking against `ReentrantLock` for code that also needs to serialize access to shared state alongside its file I/O.

### Level 1 — Basic

```java
// File: FileReadVirtualBasic.java
// Run with --enable-preview: virtual threads are a 2nd preview feature in
// Java 20.
import java.nio.file.*;

public class FileReadVirtualBasic {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("data", ".txt");
        Files.writeString(file, "hello from a file, read on a virtual thread");

        Thread vt = Thread.ofVirtual().start(() -> {
            try {
                String content = Files.readString(file);
                System.out.println("Read on " + Thread.currentThread() + ": " + content);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
        vt.join();

        Files.deleteIfExists(file);
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview FileReadVirtualBasic.java
java --enable-preview FileReadVirtualBasic
```

Expected output shape (exact virtual thread id varies):
```
Read on VirtualThread[#23]/runnable@ForkJoinPool-1-worker-1: hello from a file, read on a virtual thread
```

### Level 2 — Intermediate

```java
// File: FileReadBatchIntermediate.java
// Reads MANY small files concurrently using one virtual thread per file via
// a virtual-thread-per-task executor, measuring elapsed time to confirm the
// reads genuinely overlap rather than running one after another.
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;

public class FileReadBatchIntermediate {
    public static void main(String[] args) throws Exception {
        int fileCount = 200;
        List<Path> files = new ArrayList<>();
        for (int i = 0; i < fileCount; i++) {
            Path f = Files.createTempFile("data-" + i, ".txt");
            Files.writeString(f, "content of file " + i);
            files.add(f);
        }

        long start = System.currentTimeMillis();
        List<Future<Integer>> futures = new ArrayList<>();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (Path f : files) {
                futures.add(executor.submit(() -> {
                    String content = Files.readString(f);
                    Thread.sleep(10); // simulate a bit of additional per-file work/latency
                    return content.length();
                }));
            }
        } // waits for all reads to complete

        int totalChars = 0;
        for (Future<Integer> fut : futures) totalChars += fut.get();
        long elapsedMs = System.currentTimeMillis() - start;

        System.out.println("Read " + fileCount + " files, " + totalChars + " total chars, in ~" + elapsedMs + "ms");

        for (Path f : files) Files.deleteIfExists(f);
    }
}
```

**How to run:**
```
java --enable-preview FileReadBatchIntermediate.java
```

Expected output (elapsed time close to tens of ms, not 200 x 10ms, proving concurrency):
```
Read 200 files, 3392 total chars, in ~45ms
```

### Level 3 — Advanced

```java
// File: FileReadWithLockAdvanced.java
// Reads files concurrently while also serializing updates to shared summary
// state, contrasting ReentrantLock (does NOT pin the virtual thread's
// carrier) against synchronized (still a known pinning caveat in this
// preview round) for the locking portion of the work.
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.locks.ReentrantLock;

public class FileReadWithLockAdvanced {
    static final ReentrantLock lock = new ReentrantLock();
    static int totalCharsWithLock = 0;

    static synchronized void addSynchronized(int chars) {
        totalCharsWithLock += 0; // no-op counter kept separate to isolate the demonstration
    }

    static void addWithReentrantLock(int chars) {
        lock.lock();
        try {
            totalCharsWithLock += chars;
        } finally {
            lock.unlock();
        }
    }

    public static void main(String[] args) throws Exception {
        int fileCount = 100;
        List<Path> files = new ArrayList<>();
        for (int i = 0; i < fileCount; i++) {
            Path f = Files.createTempFile("data-" + i, ".txt");
            Files.writeString(f, "x".repeat(i + 1));
            files.add(f);
        }

        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (Path f : files) {
                executor.submit(() -> {
                    try {
                        String content = Files.readString(f);
                        addWithReentrantLock(content.length()); // ReentrantLock: carrier stays free for other VTs
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                });
            }
        } // waits for all tasks

        System.out.println("Total chars across " + fileCount + " files (via ReentrantLock-guarded counter): "
                + totalCharsWithLock);

        for (Path f : files) Files.deleteIfExists(f);
    }
}
```

**How to run:**
```
java --enable-preview FileReadWithLockAdvanced.java
```

Expected output:
```
Total chars across 100 files (via ReentrantLock-guarded counter): 5050
```

## 6. Walkthrough

1. `FileReadWithLockAdvanced.main` creates 100 temporary files, each containing a different number of `"x"` characters (file `i` contains `i+1` characters, so the total across all files is `1+2+...+100 = 5050`), and submits one task per file to a virtual-thread-per-task executor.
2. Each submitted task calls `Files.readString(f)` — a blocking file I/O read. This is exactly the operation category JEP 436's pinning fixes target: in this Java 20 second-preview round, this kind of blocking file read no longer keeps the virtual thread pinned to its carrier thread the way it could in the Java 19 first preview, meaning the carrier is free to run a *different* virtual thread's task while this read is actually waiting on the filesystem.
3. After reading, each task calls `addWithReentrantLock(content.length())`, which acquires `lock` (a `ReentrantLock`), adds the file's character count to the shared `totalCharsWithLock` field, and releases the lock — deliberately chosen over the `synchronized`-based `addSynchronized` (present in the code, unused, purely for contrast) because acquiring a `ReentrantLock` does **not** pin the calling virtual thread's carrier the way entering a `synchronized` block still could in this preview round.
4. Because up to 100 virtual threads' tasks can be concurrently reading their respective files (and briefly contending for `lock` around the shared counter update), the executor's `try`-with-resources block waits, via its implicit `close()`, until every submitted task has completed before the block exits.
5. After the block exits, `totalCharsWithLock` holds the sum of every file's character count, computed correctly despite dozens of virtual threads concurrently reading files and briefly synchronizing on the shared counter — `ReentrantLock`'s mutual exclusion guarantees the additions don't race, exactly as `synchronized` would, but without the carrier-pinning side effect this preview round's fixes and remaining caveats are specifically about.
6. The final printed total, `5050`, confirms correctness: every one of the 100 file reads happened, every character count was added exactly once under lock protection, with no lost updates from concurrent access.

```
100 virtual threads, each:
    Files.readString(file)  <- blocking file I/O; carrier freed while waiting (fixed in Java 20)
         |
         v
    addWithReentrantLock(len)
         |
    lock.lock()  <- does NOT pin the carrier
         |
    totalCharsWithLock += len
         |
    lock.unlock()
         |
         v
    (all 100 tasks complete) -> totalCharsWithLock == 5050
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 20** (second preview of virtual threads) — requiring `--enable-preview` for both `javac --release 20` and `java`; the pinning-related fixes in this round targeted specific blocking file I/O cases, while `synchronized`-block pinning remained a known limitation at this point, fully resolved only in a later JDK release.
- Pinning is a **performance** issue, not a **correctness** issue — pinned code still produces the right answer, it simply reduces the concurrency benefit virtual threads are meant to provide by tying up a carrier thread longer than necessary; it's worth profiling for, not treating as a bug that breaks output.
- Prefer `java.util.concurrent.locks.ReentrantLock` over `synchronized` in code paths intended to run at high concurrency on virtual threads, specifically to avoid the still-present `synchronized` pinning caveat in this era of the JVM — this is a real, actionable migration consideration for existing thread-pool-based code being moved onto virtual threads.
- The JDK includes diagnostic support (`-Djdk.tracePinnedThreads=full`, available from the virtual threads preview era onward) for locating exactly which code is pinning a virtual thread's carrier in a running application — useful for auditing an existing codebase before relying heavily on virtual-thread concurrency.
- As with the first preview, the core lesson holds: virtual threads help I/O-bound, high-concurrency workloads specifically, and this round's fixes widen exactly which blocking I/O operations correctly release their carrier thread while waiting — meaning real workloads mixing network I/O and file I/O see a more complete throughput benefit than the first preview alone provided.
