---
card: java
gi: 599
slug: process-api-processhandle-processhandle-info
title: Process API (ProcessHandle, ProcessHandle.Info)
---

## 1. What it is

Java 9 overhauled the process API with two new classes: `ProcessHandle` (a handle to a native operating-system process) and `ProcessHandle.Info` (a snapshot of process metadata at a particular moment). `ProcessHandle` provides methods to list, inspect, and control processes — including getting the PID, checking if a process is alive, retrieving its children or parent, and destroying it. This replaces the pre-Java-9 approach of shelling out to platform-specific commands (`ps`, `tasklist`, `kill`) and parses the output, which was fragile, non-portable, and slow.

## 2. Why & when

Any application that spawns subprocesses (build tools, CI runners, container orchestrators, test harnesses) eventually needs to answer operational questions: "Is the subprocess still running?", "What's its PID?", "How much CPU has it used?", "What are its children?" Before Java 9, the JDK's `Process` class only let you check the exit value (which blocks) or the output streams — there was no portable way to get the PID, let alone list or monitor arbitrary processes. System administrators and DevOps engineers resorted to `Runtime.exec("ps -p " + pid)` on Unix or `Runtime.exec("tasklist /FI ...")` on Windows. `ProcessHandle` provides a unified, operating-system-agnostic API for all of this, eliminating platform-specific hacks.

## 3. Core concept

```java
// Get a handle to the current JVM process
ProcessHandle current = ProcessHandle.current();
System.out.println("PID: " + current.pid());
System.out.println("Alive: " + current.isAlive());

// Get process info (command, user, start time, CPU time)
ProcessHandle.Info info = current.info();
info.command().ifPresent(cmd -> System.out.println("Command: " + cmd));
info.totalCpuDuration().ifPresent(cpu -> System.out.println("CPU: " + cpu));

// List all visible processes (snapshot)
ProcessHandle.allProcesses()
    .limit(5)
    .forEach(ph -> System.out.println(ph.pid() + " " + ph.info().command().orElse("?")));
```

`ProcessHandle.current()` returns a handle to the JVM's own process. `ProcessHandle.allProcesses()` returns a stream of all processes visible to the JVM. `ProcessHandle.Info` is obtained via `.info()` and provides optional metadata fields (command, arguments, start instant, total CPU time, user) because the OS may not provide all fields for all processes.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Java 9 ProcessHandle gives a portable view of native OS processes">
  <rect x="20" y="10" width="580" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="40" y="30" width="120" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="100" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">Java Process</text>

  <text x="175" y="55" fill="#8b949e" font-size="10" font-family="monospace">── handle ──►</text>

  <rect x="270" y="25" width="150" height="50" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="345" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">ProcessHandle</text>
  <text x="345" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">.pid() .isAlive()</text>
  <text x="345" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">.children() .parent()</text>

  <text x="435" y="50" fill="#8b949e" font-size="10" font-family="monospace">── info() ──►</text>

  <rect x="460" y="30" width="130" height="40" rx="4" fill="#0d1117" stroke="#6db33f"/>
  <text x="525" y="55" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace">ProcessHandle.Info</text>

  <text x="40" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">.allProcesses() → Stream of all visible OS processes</text>
  <text x="40" y="118" fill="#8b949e" font-size="10" font-family="sans-serif">.destroy() / .destroyForcibly() → terminate the process</text>
  <text x="40" y="136" fill="#8b949e" font-size="10" font-family="sans-serif">.onExit() → CompletableFuture that completes when process exits</text>

  <text x="40" y="165" fill="#8b949e" font-size="9" font-family="sans-serif">Info fields: command, arguments, startInstant, totalCpuDuration, user — all Optional</text>
</svg>

`ProcessHandle` wraps a native PID; `ProcessHandle.Info` is a point-in-time snapshot of process metadata.

## 5. Runnable example

Scenario: a process monitor that spawns a child process, tracks its PID and metadata, lists all running Java processes, and waits for the child to terminate — starting with a basic PID inspection, extending to process monitoring with info queries, and finally building a process tree walker with lifecycle management.

### Level 1 — Basic

```java
// File: ProcessHandleDemo.java
public class ProcessHandleDemo {
    public static void main(String[] args) {
        ProcessHandle current = ProcessHandle.current();

        System.out.println("Current JVM process:");
        System.out.println("  PID:   " + current.pid());
        System.out.println("  Alive: " + current.isAlive());

        ProcessHandle.Info info = current.info();
        System.out.println("  Command: " + info.command().orElse("(unknown)"));
        System.out.println("  User:    " + info.user().orElse("(unknown)"));
    }
}
```

**How to run:** `java ProcessHandleDemo.java`

Expected output (values vary by system):
```
Current JVM process:
  PID:   12345
  Alive: true
  Command: /usr/bin/java
  User:    faisalchishti
```

The simplest usage: get a handle to the current JVM process, print its PID, check it's alive, and query metadata via `ProcessHandle.Info`. All info fields are `Optional` — they may be empty if the OS doesn't provide that data.

### Level 2 — Intermediate

```java
// File: ChildProcessMonitor.java
import java.io.IOException;
import java.util.concurrent.TimeUnit;

public class ChildProcessMonitor {
    public static void main(String[] args) throws Exception {
        // Spawn a child process (sleeps for 3 seconds)
        ProcessBuilder pb = new ProcessBuilder("sleep", "3");
        Process child = pb.start();

        // Get a ProcessHandle to the child
        ProcessHandle childHandle = child.toHandle();

        System.out.println("Child spawned:");
        System.out.println("  PID:       " + childHandle.pid());
        System.out.println("  Alive:     " + childHandle.isAlive());

        ProcessHandle.Info info = childHandle.info();
        System.out.println("  Command:   " + info.command().orElse("(unknown)"));
        System.out.println("  Start:     " + info.startInstant().orElse(null));
        System.out.println("  Parent PID:" + childHandle.parent().map(ProcessHandle::pid).orElse(-1L));

        // Wait for child to finish (non-blocking check)
        System.out.println("\nWaiting for child to exit...");
        boolean finished = childHandle.onExit().get(5, TimeUnit.SECONDS).isAlive() == false;
        System.out.println("  Child finished: " + finished);
        System.out.println("  Exit code:      " + child.exitValue());
    }
}
```

**How to run:** `java ChildProcessMonitor.java`

Expected output (values vary):
```
Child spawned:
  PID:       67890
  Alive:     true
  Command:   /bin/sleep
  Start:     2026-07-09T12:00:00Z
  Parent PID:12345

Waiting for child to exit...
  Child finished: true
  Exit code:      0
```

The real-world concern added: spawning a child process and monitoring it. `child.toHandle()` bridges from the old `Process` API to the new `ProcessHandle`. `childHandle.parent()` walks up the process tree. `childHandle.onExit()` returns a `CompletableFuture<ProcessHandle>` that completes when the process terminates — a non-blocking alternative to the old `Process.waitFor()`. The `onExit()` future is combined with `get(5, TimeUnit.SECONDS)` for a timeout-guarded wait.

### Level 3 — Advanced

```java
// File: ProcessTreeWalker.java
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class ProcessTreeWalker {

    // Recursively walk the process tree starting from a given handle
    static void printTree(ProcessHandle root, int depth) {
        String indent = "  ".repeat(depth);
        ProcessHandle.Info info = root.info();
        String cmd = info.command().orElse("?").replaceAll(".*/", "");

        System.out.printf("%sPID %d | %s | CPU: %s%n",
            indent,
            root.pid(),
            cmd,
            info.totalCpuDuration().map(Object::toString).orElse("?")
        );

        root.children().forEach(child -> printTree(child, depth + 1));
    }

    // Find all Java processes currently running
    static List<ProcessHandle> findJavaProcesses() {
        return ProcessHandle.allProcesses()
            .filter(ph -> ph.info().command()
                .map(cmd -> cmd.contains("java"))
                .orElse(false))
            .collect(Collectors.toList());
    }

    // Try graceful destroy, fall back to forced after timeout
    static boolean killProcess(ProcessHandle handle) {
        boolean destroyed = handle.destroy();
        if (!destroyed) {
            System.out.println("  Graceful destroy failed, forcing...");
            destroyed = handle.destroyForcibly();
        }
        return destroyed;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== My Process Tree ===");
        ProcessHandle me = ProcessHandle.current();
        printTree(me, 0);

        System.out.println("\n=== Java Processes Running ===");
        findJavaProcesses().forEach(ph -> {
            ProcessHandle.Info info = ph.info();
            System.out.printf("  PID %d | %s | %s%n",
                ph.pid(),
                info.command().orElse("?"),
                info.user().orElse("?")
            );
        });

        System.out.println("\n=== Spawn and Destroy ===");
        Process child = new ProcessBuilder("sleep", "10").start();
        ProcessHandle childHandle = child.toHandle();
        System.out.println("Spawned child PID: " + childHandle.pid());
        System.out.println("Alive before destroy: " + childHandle.isAlive());

        killProcess(childHandle);
        childHandle.onExit().join(); // wait for termination
        System.out.println("Alive after destroy:  " + childHandle.isAlive());
    }
}
```

**How to run:** `java ProcessTreeWalker.java`

Expected output (values vary; the tree shows the process hierarchy visible to the JVM):
```
=== My Process Tree ===
PID 12345 | java | CPU: PT0.5S

=== Java Processes Running ===
  PID 12345 | /usr/bin/java | faisalchishti

=== Spawn and Destroy ===
Spawned child PID: 67890
Alive before destroy: true
Alive after destroy:  false
```

The production-flavoured features: (1) recursive process tree walking via `children()` — each `ProcessHandle` knows its immediate children, so a recursive descent prints the full hierarchy; (2) filtering `allProcesses()` by command to find specific processes (here, all running Java processes) — useful for monitoring and tooling; (3) lifecycle management: `destroy()` (SIGTERM on Unix) for graceful termination, falling back to `destroyForcibly()` (SIGKILL) if needed, followed by `onExit().join()` to wait for the process to actually terminate before checking `isAlive()`.

## 6. Walkthrough

Tracing the Level 3 example from `main` to output:

**Section 1: "My Process Tree"**

1. `ProcessHandle me = ProcessHandle.current()` obtains a handle to the JVM's own process.

2. `printTree(me, 0)` is called. The `info()` snapshot is fetched. The `command` (e.g. `/usr/bin/java`) is extracted and shortened to just `java`. The formatted line `"PID 12345 | java | CPU: PT0.5S"` is printed at depth 0.

3. `root.children()` returns a (possibly empty) stream of direct child processes. If the JVM spawned any subprocesses before this call, they appear here. (In a typical run, there are none, so the recursive call is skipped.) The method returns.

**Section 2: "Java Processes Running"**

4. `findJavaProcesses()` calls `ProcessHandle.allProcesses()` — this is a snapshot of all processes the OS makes visible to the JVM (subject to OS-level permissions). The stream is filtered: only processes whose `command` contains `"java"` are retained. Each is mapped to a formatted line with PID, command, and user, then collected into a list. The list is printed.

**Section 3: "Spawn and Destroy"**

5. `new ProcessBuilder("sleep", "10").start()` spawns a child process running `/bin/sleep 10` (sleeps for 10 seconds). `Process child` is the old-style handle.

6. `child.toHandle()` bridges to the new API, giving `ProcessHandle childHandle`. The child's PID is printed. `childHandle.isAlive()` returns `true` — the child is running.

7. `killProcess(childHandle)` calls `handle.destroy()` (sends SIGTERM). Sleep gracefully exits, so `destroy()` returns `true`. The forced-fallback path is skipped.

8. `childHandle.onExit().join()` blocks until the child actually terminates (the `CompletableFuture` completes when the OS confirms the process exited). After this, `childHandle.isAlive()` returns `false`.

```
ProcessHandle.current()                 → me (PID 12345)
  └── .info().command()                 → "/usr/bin/java"
  └── .children()                       → (empty for this JVM)

ProcessHandle.allProcesses()            → Stream of all visible processes
  └── filter(cmd contains "java")       → Stream of Java processes only
      └── collect(toList())             → [PID 12345, ...]

ProcessBuilder("sleep","10").start()    → Process child
  └── .toHandle()                       → ProcessHandle (PID 67890)
      └── .destroy()                    → SIGTERM → sleep exits
      └── .onExit().join()              → block until exit confirmed
      └── .isAlive()                    → false
```

## 7. Gotchas & takeaways

> `ProcessHandle.allProcesses()` returns a **snapshot** — the stream reflects the state of processes at the moment the terminal operation starts. Processes that start or exit during stream consumption may or may not appear, and calling `isAlive()` on a handle obtained from the snapshot may return `false` even though it was `true` moments earlier. Treat the snapshot as point-in-time, not live.

- `ProcessHandle.Info` fields are all `Optional` because the OS may not provide every field for every process — on some systems, the command or user may be unavailable for processes owned by other users, or the CPU time may not be tracked for short-lived processes.
- `ProcessHandle.destroy()` sends a **graceful** termination request (SIGTERM on Unix, `TerminateProcess` on Windows). `destroyForcibly()` sends a forceful termination (SIGKILL on Unix). Neither is guaranteed — the process may ignore SIGTERM, and even SIGKILL can't kill stuck kernel threads.
- `ProcessHandle.onExit()` is the modern, non-blocking replacement for `Process.waitFor()` — it returns a `CompletableFuture<ProcessHandle>` that can be composed with other async operations, chained with `.thenAccept()`, or combined with `CompletableFuture.anyOf()` for timeouts.
- The parent-child relationship via `.parent()` and `.children()` is a snapshot too — a child process that has already exited may no longer appear in `.children()`; a parent that has exited may return an empty `Optional` from `.parent()`.
- Access to processes is subject to OS-level security — on Unix, the JVM can typically only see processes owned by the same user unless running as root; attempting to `.destroy()` a process owned by another user throws `SecurityException`. 