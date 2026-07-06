---
card: java
gi: 283
slug: system-exit-system-gc
title: System.exit() / System.gc()
---

## 1. What it is

`System.exit(int status)` immediately terminates the entire JVM process, running any registered shutdown hooks first, but skipping all further normal program execution — code after the `System.exit()` call, anywhere in the call stack, never runs. `System.gc()` merely *suggests* to the JVM that now might be a good time to run garbage collection; it is a hint, not a command, and the JVM is free to ignore it entirely.

```java
public class ExitGcDemo {
    public static void main(String[] args) {
        System.out.println("Before exit");
        System.exit(0); // status 0 conventionally means "success"
        System.out.println("This line NEVER runs"); // unreachable — exit already happened
    }
}
```

`System.exit(0)` terminates the JVM immediately, so `"This line NEVER runs"` genuinely never executes — this isn't a warning about a rare edge case, it's a guaranteed, deterministic consequence of calling `System.exit()`, which stops the entire program right there, regardless of what call stack depth it's invoked from.

## 2. Why & when

`System.exit()` provides a way to terminate a program immediately and communicate a specific exit status to whatever launched it (a shell script, another program, an operating system scheduler); `System.gc()` exists mainly as a hint for specific, unusual situations, and is rarely appropriate in typical application code.

- **`System.exit(status)` communicates success or failure to the calling environment** — by convention, `0` means success and any non-zero value indicates some kind of failure (the specific meaning of non-zero codes is up to the application); shell scripts and automation tools routinely check a program's exit status to decide what to do next.
- **`System.exit()` is appropriate for command-line tools that need to terminate early** — a command-line utility that detects invalid arguments, encounters a fatal error, or simply finishes its work might call `System.exit()` directly to stop immediately and report a specific status, rather than letting `main` return normally (which implicitly exits with status `0`).
- **`System.gc()` is rarely appropriate to call directly in application code** — as an earlier topic on `finalize()` touched on, the garbage collector's own heuristics for deciding when to run are generally far better tuned than a manual `System.gc()` call, and calling it can actually hurt performance by forcing a full collection cycle at a suboptimal time; it exists mainly for diagnostic tools, benchmarking scenarios (where you want a "clean" starting memory state before measuring), or very specific, well-understood situations.

Use `System.exit(status)` deliberately in command-line applications and scripts that need to terminate early with a specific status code communicated to the calling environment — but avoid calling it from within library code or deep inside application logic, since it terminates the *entire* JVM unconditionally, which can be surprising and destructive if triggered from code that doesn't "own" the whole application's lifecycle. Avoid `System.gc()` in ordinary application code entirely; reserve it for the narrow diagnostic and benchmarking scenarios where its specific behaviour is genuinely useful.

## 3. Core concept

```java
public class ExitGcCore {
    static void processFile(String path) {
        if (path == null) {
            System.err.println("Fatal: no file path provided");
            System.exit(1); // non-zero status signals failure to the calling shell/script
        }
        System.out.println("Processing: " + path);
    }

    public static void main(String[] args) {
        processFile(null); // triggers the fatal error path, terminates immediately
        System.out.println("This never prints"); // unreachable after System.exit
    }
}
```

`System.exit(1)` inside `processFile` terminates the *entire program*, not just `processFile` itself — control never returns to `main` at all, and the final `println` in `main` never runs; this demonstrates that `System.exit()` can be called from anywhere in the call stack and its effect is always the same: immediate, total program termination.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System.exit terminates the entire JVM immediately regardless of call stack depth, everything after it anywhere in the program never runs, System.gc merely suggests garbage collection which the JVM may ignore">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">main() calls processFile()</text>

  <line x1="150" y1="50" x2="150" y2="75" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="40" y="80" width="220" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="150" y="100" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">System.exit(1) — JVM stops HERE</text>

  <text x="450" y="45" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No further code anywhere</text>
  <text x="450" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">in the program runs —</text>
  <text x="450" y="81" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">not even back in main().</text>

  <text x="300" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">System.gc() only ever suggests collection — the JVM decides whether to actually run it.</text>
</svg>

`System.exit()` terminates the entire JVM instantly, from anywhere in the call stack, with no further code running.

## 5. Runnable example

Scenario: a small command-line validation tool that must communicate success or failure via exit status, evolved from a simple exit call into a version with multiple distinct exit codes, then hardened with a shutdown hook demonstrating what still runs before the JVM fully terminates.

### Level 1 — Basic

```java
public class ExitBasic {
    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Usage: java ExitBasic <name>");
            System.exit(1); // non-zero: failure
        }
        System.out.println("Hello, " + args[0] + "!");
    }
}
```

**How to run:** `java ExitBasic.java` (no arguments, triggers the exit) or `java ExitBasic World` (succeeds normally)

Running with no arguments prints a usage message to `System.err` and exits with status `1`, signaling failure to whatever launched the program; running with an argument proceeds normally and the program exits with the default status `0` when `main` simply returns.

### Level 2 — Intermediate

Same idea, now with multiple distinct exit codes for different failure categories, a common convention in command-line tools for letting calling scripts distinguish between different kinds of failure.

```java
public class ExitIntermediate {
    static final int EXIT_SUCCESS = 0;
    static final int EXIT_MISSING_ARGS = 1;
    static final int EXIT_INVALID_NUMBER = 2;

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Usage: java ExitIntermediate <number>");
            System.exit(EXIT_MISSING_ARGS);
        }

        int value;
        try {
            value = Integer.parseInt(args[0]);
        } catch (NumberFormatException e) {
            System.err.println("Invalid number: " + args[0]);
            System.exit(EXIT_INVALID_NUMBER);
            return; // unreachable, but satisfies the compiler's definite-assignment analysis for 'value'
        }

        System.out.println("Square: " + (value * value));
        System.exit(EXIT_SUCCESS); // explicit, even though returning normally would also exit with 0
    }
}
```

**How to run:** `java ExitIntermediate.java abc` (exits with code `2`) or `java ExitIntermediate.java 7` (prints `49` and exits with code `0`)

Named constants (`EXIT_SUCCESS`, `EXIT_MISSING_ARGS`, `EXIT_INVALID_NUMBER`) make the meaning of each exit code self-documenting in the source, and calling `System.exit(EXIT_SUCCESS)` explicitly at the end, while not strictly necessary here, makes the successful termination path just as explicit as the failure paths.

### Level 3 — Advanced

Same tool, now demonstrating a shutdown hook — code registered to run during JVM termination, even when triggered by `System.exit()` — useful for guaranteed cleanup regardless of how or why the program is ending.

```java
public class ExitAdvanced {
    public static void main(String[] args) {
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("Shutdown hook: cleaning up before JVM terminates");
        }));

        System.out.println("Program starting...");

        if (args.length == 0) {
            System.err.println("No arguments provided, exiting early");
            System.exit(1); // the shutdown hook STILL runs before the process actually terminates
        }

        System.out.println("This runs only if arguments were provided: " + args[0]);
    }
}
```

**How to run:** `java ExitAdvanced.java` (no arguments)

Even though `System.exit(1)` is called, the registered shutdown hook still runs — printing `"Shutdown hook: cleaning up..."` — as part of the JVM's termination sequence, demonstrating that `System.exit()` triggers an orderly shutdown process (running shutdown hooks) rather than an instantaneous, hard halt with zero further code execution at all.

## 6. Walkthrough

Trace `main` in `ExitAdvanced` when run with no arguments (`java ExitAdvanced`).

**`Runtime.getRuntime().addShutdownHook(new Thread(...))`.** Registers a new thread with the JVM, to be started automatically as part of the shutdown sequence whenever the JVM begins terminating — this registration itself does nothing immediately; it only takes effect later, when shutdown actually begins.

**`System.out.println("Program starting...")`.** Prints immediately.

**`args.length == 0` is `true`** (no command-line arguments were provided). `System.err.println("No arguments provided, exiting early")` prints to standard error.

**`System.exit(1)`.** This begins the JVM's shutdown sequence: first, all registered shutdown hooks are started (and the JVM waits for them to finish, within limits) — this runs the previously registered hook, printing `"Shutdown hook: cleaning up before JVM terminates"`. After the shutdown hook completes, the JVM process actually terminates, returning exit status `1` to the operating system.

**The final `println` (`"This runs only if arguments were provided..."`) never executes** — the `System.exit(1)` call prevented it, exactly as it would prevent any code anywhere else in the program from running further.

```
addShutdownHook registered (not yet run)
"Program starting..." printed
args.length==0 -> true
"No arguments provided, exiting early" printed (to stderr)
System.exit(1) called:
  -> JVM begins shutdown sequence
  -> registered shutdown hook runs: "Shutdown hook: cleaning up before JVM terminates"
  -> JVM process terminates with exit status 1
  -> the final println() in main is NEVER reached
```

**Final output (standard output).**
```
Program starting...
Shutdown hook: cleaning up before JVM terminates
```

**Standard error.**
```
No arguments provided, exiting early
```

**Process exit status (visible via `echo $?` in a shell immediately afterward, on Unix-like systems):** `1`

## 7. Gotchas & takeaways

> **Calling `System.exit()` from within library code, deep application logic, or anywhere other than a well-understood, deliberate top-level control point is generally considered bad practice** — it terminates the *entire* JVM process unconditionally, which can be surprising and destructive to any other unrelated work the same JVM might be doing (this matters especially in larger applications, application servers, or anywhere multiple independent components share one JVM process). Reserve `System.exit()` for genuine top-level command-line tool termination, and prefer throwing an exception (letting calling code decide how to respond) for library or internal application code.

> **`System.gc()` is only ever a *suggestion* — the JVM is completely free to ignore it, and in most production JVMs, it very often does, or performs a collection that doesn't actually free the memory you might be expecting.** Calling it in ordinary application code, hoping to "clean up memory" at a specific point, is a common misconception; the garbage collector's own automatic heuristics for timing collections are generally far more effective than manual intervention, and unnecessary `System.gc()` calls can actively hurt performance by forcing unnecessary full collection cycles.

- `System.exit(status)` terminates the entire JVM process immediately (after running registered shutdown hooks), with `0` conventionally meaning success and non-zero values indicating some form of failure.
- Code after a `System.exit()` call, anywhere in the entire program's call stack, never executes — this is a deterministic, guaranteed consequence, not a rare edge case.
- Registered shutdown hooks (via `Runtime.getRuntime().addShutdownHook(...)`) still run during the termination sequence triggered by `System.exit()`, providing a place for guaranteed cleanup regardless of how the program is ending.
- `System.gc()` only ever suggests garbage collection to the JVM, which is free to ignore it entirely — avoid relying on it in ordinary application code; reserve it for narrow diagnostic or benchmarking scenarios.
