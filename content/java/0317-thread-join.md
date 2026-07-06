---
card: java
gi: 317
slug: thread-join
title: Thread.join()
---

## 1. What it is

`thread.join()` blocks the **calling** thread until the target `thread` finishes executing (or, with a timeout argument, until that much time has elapsed, whichever comes first). It's the standard way to say "wait here until that other thread is done" — the exact synchronization tool needed whenever one thread's next steps depend on another thread having genuinely completed.

```java
public class JoinDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            System.out.println("Worker starting...");
            try { Thread.sleep(500); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            System.out.println("Worker finished.");
        });

        worker.start();
        worker.join(); // main thread waits HERE until worker completes
        System.out.println("Main thread continues, worker is guaranteed done.");
    }
}
```

`worker.join()` is called from the main thread, so it's the main thread that pauses — it will not print its final line until the worker thread has genuinely finished running (including its half-second sleep), guaranteeing a strict "worker finishes, then main continues" ordering.

## 2. Why & when

`start()` returns immediately, without waiting for the new thread's work to complete — so code that needs to use a result the other thread computes, or simply needs to know "is this background work definitely done," needs a way to wait for that specific thread. `join()` is exactly that mechanism.

- **Waiting for a result** — if a background thread computes something the main thread needs, `join()` before reading that result guarantees it's actually been computed (and that the write is visible, per `join()`'s documented memory-visibility guarantee).
- **Coordinating multiple threads** — waiting for several worker threads to all finish before combining their individual results (as seen when parallelizing a sum across threads).
- **Clean shutdown** — ensuring background threads have fully wound down before a program exits, rather than the JVM potentially terminating them abruptly.

Call `join()` whenever subsequent code's correctness depends on a specific thread having actually finished — reading a value a thread computes without a preceding `join()` (or other synchronization) on that thread is a race condition. `join()` can optionally take a timeout in milliseconds, returning even if the thread hasn't finished yet, useful when you don't want to wait indefinitely for a thread that might be stuck.

## 3. Core concept

```java
public class JoinCore {
    public static void main(String[] args) throws InterruptedException {
        Thread slowWorker = new Thread(() -> {
            try { Thread.sleep(2000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        slowWorker.start();
        slowWorker.join(500); // wait AT MOST 500ms, not the full 2000ms

        System.out.println("Still alive after 500ms wait? " + slowWorker.isAlive());
    }
}
```

`join(500)` returns after at most 500 milliseconds even though `slowWorker` actually takes 2000ms to finish — the timeout means `join` gives up waiting and returns control to the caller, but note that it does **not** stop or cancel the other thread; `slowWorker.isAlive()` confirms it's still running in the background after `join` returns.

## 4. Diagram

<svg viewBox="0 0 600 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The calling thread blocks at join until the target thread finishes, then both continue">
  <rect x="8" y="8" width="584" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10" font-family="monospace">worker:  ----running work--------|finished</text>
  <text x="20" y="65" fill="#79c0ff" font-size="10" font-family="monospace">main:    --start(worker)--join()==blocked====|continues</text>
  <text x="20" y="105" fill="#8b949e" font-size="9">main's join() call blocks exactly until worker's vertical line (finished) is reached.</text>
</svg>

`join()` is the explicit rendezvous point where one thread's timeline waits on another's completion.

## 5. Runnable example

Scenario: a multi-stage data pipeline where a download stage must fully complete before a processing stage begins, evolved from a basic two-thread handoff into a multi-stage pipeline, then into a version using a timeout to detect and report a stage that's taking too long.

### Level 1 — Basic

```java
public class JoinBasic {
    static String downloadedData;

    public static void main(String[] args) throws InterruptedException {
        Thread downloader = new Thread(() -> {
            try { Thread.sleep(300); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            downloadedData = "raw-data-contents";
            System.out.println("Download complete.");
        });

        downloader.start();
        downloader.join(); // wait for download before using downloadedData

        System.out.println("Processing: " + downloadedData);
    }
}
```

**How to run:** `java JoinBasic.java`

`downloader.join()` guarantees `downloadedData` has been assigned before the main thread reads it — without this `join()`, the main thread might print `"Processing: null"`, reading the variable before the downloader thread had a chance to set it.

### Level 2 — Intermediate

Same pipeline, now with three sequential stages (download, then process, then upload), each running on its own thread, with `join()` enforcing the correct order between stages.

```java
public class JoinIntermediate {
    static String data;

    static Thread stage(String name, int delayMillis, Runnable action) {
        return new Thread(() -> {
            try { Thread.sleep(delayMillis); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            action.run();
            System.out.println(name + " complete.");
        });
    }

    public static void main(String[] args) throws InterruptedException {
        Thread download = stage("Download", 300, () -> data = "raw-data");
        Thread process = stage("Process", 200, () -> data = data.toUpperCase());
        Thread upload = stage("Upload", 250, () -> System.out.println("Uploaded: " + data));

        download.start();
        download.join(); // must finish before process starts

        process.start();
        process.join(); // must finish before upload starts

        upload.start();
        upload.join();

        System.out.println("Pipeline finished.");
    }
}
```

**How to run:** `java JoinIntermediate.java`

Each stage is started only after the previous one's `join()` returns, enforcing a strict sequential order across three separate threads — even though each stage runs on its own thread, the `join()` calls chain them together so `process` never starts before `download` has genuinely finished setting `data`.

### Level 3 — Advanced

Same pipeline, now using a timeout on `join()` to detect a stage that's taking unexpectedly long, reporting a warning without indefinitely blocking the rest of the program.

```java
public class JoinAdvanced {
    static String data;

    static Thread stage(String name, int delayMillis, Runnable action) {
        return new Thread(() -> {
            try { Thread.sleep(delayMillis); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            action.run();
        }, name);
    }

    static boolean runStageWithTimeout(Thread stage, long timeoutMillis) throws InterruptedException {
        stage.start();
        stage.join(timeoutMillis);
        if (stage.isAlive()) {
            System.out.println("WARNING: " + stage.getName() + " exceeded " + timeoutMillis + "ms, still running...");
            stage.join(); // fall back to waiting for it fully, since we still need its result
            return false;
        }
        return true;
    }

    public static void main(String[] args) throws InterruptedException {
        Thread download = stage("Download", 300, () -> data = "raw-data");
        Thread process = stage("Process", 1500, () -> data = data.toUpperCase()); // unexpectedly slow!

        boolean downloadOnTime = runStageWithTimeout(download, 500);
        System.out.println("Download " + (downloadOnTime ? "finished on time" : "was slow"));

        boolean processOnTime = runStageWithTimeout(process, 500);
        System.out.println("Process " + (processOnTime ? "finished on time" : "was slow"));

        System.out.println("Final data: " + data);
    }
}
```

**How to run:** `java JoinAdvanced.java`

`runStageWithTimeout` calls `stage.join(timeoutMillis)`, which returns after at most `timeoutMillis`, then checks `stage.isAlive()` to distinguish "finished within the timeout" from "still running" — for `process` (deliberately set to take 1500ms against a 500ms timeout), the check finds it still alive, prints a warning, and then calls the no-argument `stage.join()` to wait for it to actually finish, since the pipeline still genuinely needs `data` to be correctly uppercased before printing the final result.

## 6. Walkthrough

Trace `JoinAdvanced.main` step by step.

**Download stage.** `runStageWithTimeout(download, 500)` starts the download thread and calls `download.join(500)`. Since `download` only takes 300ms (less than the 500ms timeout), `join` returns once the thread actually finishes, well before the timeout would have elapsed. `download.isAlive()` is `false` at that point, so the method returns `true` without printing any warning. `downloadOnTime` is `true`.

**Process stage.** `runStageWithTimeout(process, 500)` starts the process thread (which sleeps 1500ms) and calls `process.join(500)`. This time, 500ms elapses with `process` still sleeping, so `join(500)` returns *without* the thread having finished. `process.isAlive()` is `true`, so the warning prints, and `stage.join()` (no timeout this time) is called — this blocks for the *remaining* ~1000ms until `process` genuinely finishes, at which point `data` is correctly transformed to uppercase. The method returns `false`.

**Reporting.** `downloadOnTime` is `true`, so `"Download finished on time"` prints. `processOnTime` is `false`, so `"Process was slow"` prints — but critically, by the time this line runs, `process` has still fully completed (thanks to the fallback `join()`), so `data` is guaranteed correct.

**Final print.** `data` is `"RAW-DATA"` — the download's `"raw-data"` correctly transformed to uppercase by the (delayed, but eventually completed) process stage.

```
download: sleep(300), sets data="raw-data"           [join(500) catches it in time]
process:  sleep(1500), sets data=data.toUpperCase()  [join(500) times out; fallback join() waits the rest]

Timeline for process stage:
  t=0ms:    process.start(), process.join(500) begins waiting
  t=500ms:  join(500) returns; process.isAlive() -> true -> WARNING printed
  t=500ms:  fallback process.join() begins waiting (no timeout)
  t=1500ms: process thread finishes, data="RAW-DATA"; fallback join() returns
```

**Output:**
```
Download finished on time
WARNING: Process exceeded 500ms, still running...
Process was slow
Final data: RAW-DATA
```

## 7. Gotchas & takeaways

> `join(timeoutMillis)` returning does **not** mean the target thread has stopped or been cancelled — it simply means `join` gave up waiting after the timeout. The thread keeps running in the background regardless; always check `isAlive()` after a timed `join()` if you need to know whether it actually finished, and don't assume a timed-out `join()` means the work is done or safe to ignore.

> Reading data written by another thread without a preceding `join()` (or other proper synchronization) on that thread is a race condition, even if the data "usually" appears correct in casual testing — visibility of another thread's writes is not guaranteed without an explicit synchronization point like `join()`, a lock, or `volatile`.

- `thread.join()` blocks the calling thread until `thread` finishes; it's the standard way to wait for another thread's work to genuinely complete before depending on its results.
- An optional timeout argument (`join(millis)`) bounds the wait — but the target thread may still be running after it returns; check `isAlive()` to find out.
- Chaining `start()`/`join()` pairs across multiple threads enforces a strict sequential order between otherwise-independent stages of work.
- Never read a value written by another thread without a `join()` (or equivalent synchronization) establishing that the write is visible — otherwise it's a genuine race condition.
