---
card: java
gi: 48
slug: the-main-method-signature
title: The main() method signature
---

## 1. What it is

**`main()`** is the entry point of every Java application. When you run `java MyApp`, the JVM looks for this exact method signature and calls it to start your program:

```java
public static void main(String[] args) { }
```

Since JDK 21 (preview) and stable in JDK 25, you can also write a **simplified entry point** without a class declaration for single-file scripts:

```java
// JDK 21+ (--enable-preview), finalized in JDK 25
void main() {
    System.out.println("Hello");
}
```

For now, on JDK 17/21 production code, the classic signature is required.

## 2. Why & when

The `main` method signature is the handshake between the OS, the JVM launcher, and your code:
- `public` — the JVM can call it from outside the class.
- `static` — the JVM calls it without creating an instance (no object exists yet at startup).
- `void` — the program signals success/failure via exit code (`System.exit(code)`), not a return value.
- `String[] args` — the JVM passes command-line arguments as a `String` array.

Every runnable Java program starts here. Whether you write a Spring Boot app or a CLI tool, `main()` is the first user code the JVM executes.

## 3. Core concept

```java
// Classic signature (JDK 8–24, and always valid)
public static void main(String[] args) {
    // args[0], args[1], ... are command-line arguments
}

// Valid variations (all accepted by the JVM):
public static void main(String... args) { }   // varargs form (same bytecode)

// JDK 21 preview / JDK 25+: simplified (instance main, no-args main)
class Hello {
    void main() {                 // no public, no static, no args required
        System.out.println("Hi");
    }
}

// JEP 463 (JDK 21 preview) unnamed class:
// save as Hello.java, run with: java --enable-preview --source 21 Hello.java
void main() {
    System.out.println("Hello from unnamed class");
}
```

The JVM launcher (`java` command) searches for `main` in this priority order (JDK 21+):
1. `static void main(String[])` — classic, always wins.
2. `static void main()` — no-args static.
3. `void main(String[])` — instance method with args (JVM creates an instance).
4. `void main()` — instance method, no args.

`System.exit(code)` sets the process exit code: `0` = success, non-zero = error. Without `System.exit`, the JVM exits with `0` after `main` returns if no non-daemon threads remain.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JVM launcher finds main method and calls it, passing command-line args as String array">
  <rect x="8" y="8" width="684" height="194" rx="8" fill="#0d1117"/>

  <!-- OS / shell -->
  <rect x="20" y="60" width="130" height="90" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="80" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Shell</text>
  <text x="30" y="97"  fill="#6db33f" font-size="8" font-family="monospace">java MyApp</text>
  <text x="30" y="111" fill="#6db33f" font-size="8" font-family="monospace">  --port 8080</text>
  <text x="30" y="125" fill="#6db33f" font-size="8" font-family="monospace">  --env prod</text>

  <!-- JVM launcher -->
  <rect x="210" y="60" width="155" height="90" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="287" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JVM Launcher</text>
  <text x="225" y="98"  fill="#8b949e" font-size="8" font-family="sans-serif">1. Load MyApp.class</text>
  <text x="225" y="111" fill="#8b949e" font-size="8" font-family="sans-serif">2. Find main(String[])</text>
  <text x="225" y="124" fill="#8b949e" font-size="8" font-family="sans-serif">3. Build String[] args</text>
  <text x="225" y="137" fill="#8b949e" font-size="8" font-family="sans-serif">4. Call main(args)</text>

  <!-- args array -->
  <rect x="420" y="25" width="245" height="65" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="543" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">String[] args</text>
  <text x="435" y="58"  fill="#e6edf3" font-size="9" font-family="monospace">args[0] = "--port"</text>
  <text x="435" y="72"  fill="#e6edf3" font-size="9" font-family="monospace">args[1] = "8080"</text>
  <text x="435" y="86"  fill="#e6edf3" font-size="9" font-family="monospace">args[2] = "--env"</text>
  <text x="435" y="100" fill="#e6edf3" font-size="9" font-family="monospace">args[3] = "prod"</text>

  <!-- main method -->
  <rect x="420" y="110" width="245" height="80" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="543" y="128" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">public static void main(String[] args)</text>
  <text x="435" y="145" fill="#8b949e" font-size="8" font-family="sans-serif">← JVM calls this first</text>
  <text x="435" y="159" fill="#8b949e" font-size="8" font-family="sans-serif">no return value (void)</text>
  <text x="435" y="173" fill="#8b949e" font-size="8" font-family="sans-serif">exit code via System.exit(N)</text>

  <!-- arrows -->
  <line x1="150" y1="105" x2="206" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#m1)"/>
  <line x1="365" y1="90"  x2="416" y2="57"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#m2)"/>
  <line x1="365" y1="105" x2="416" y2="150" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#m2)"/>

  <defs>
    <marker id="m1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
    <marker id="m2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
  </defs>
</svg>

The JVM launcher loads the named class, finds `main(String[])`, packs the command-line tokens into a `String[]`, and calls it. Your program begins.

## 5. Runnable example

Scenario: a configuration-driven service launcher that reads port, environment, and verbosity from command-line arguments — demonstrating `main(String[] args)` argument parsing at three levels of sophistication.

### Level 1 — Basic

```java
// MainBasic.java — basic main() and args parsing
public class MainBasic {
    public static void main(String[] args) {
        System.out.println("=== main() entry point demo ===");
        System.out.println("Number of args: " + args.length);

        for (int i = 0; i < args.length; i++) {
            System.out.printf("  args[%d] = \"%s\"%n", i, args[i]);
        }

        // Basic named-arg convention: --key value
        String host = "localhost";
        int    port = 8080;

        for (int i = 0; i < args.length - 1; i++) {
            if ("--host".equals(args[i])) host = args[i + 1];
            if ("--port".equals(args[i])) {
                try { port = Integer.parseInt(args[i + 1]); }
                catch (NumberFormatException e) { System.err.println("Invalid port: " + args[i + 1]); }
            }
        }

        System.out.println("\nParsed config:");
        System.out.println("  host = " + host);
        System.out.println("  port = " + port);
        System.out.println("\nStarting service on " + host + ":" + port + "...");
    }
}
```

**How to run:** `java MainBasic.java --host 0.0.0.0 --port 9090`

Expected output:
```
=== main() entry point demo ===
Number of args: 4
  args[0] = "--host"
  args[1] = "0.0.0.0"
  args[2] = "--port"
  args[3] = "9090"

Parsed config:
  host = 0.0.0.0
  port = 9090

Starting service on 0.0.0.0:9090...
```

`args.length` is `0` if no arguments are passed — never throw `ArrayIndexOutOfBoundsException` by accessing `args[0]` without checking length first.

### Level 2 — Intermediate

Same service launcher extended with a `parseArgs` helper that builds a map of `--key value` pairs, validates required arguments, and prints a usage message on error.

```java
// MainIntermediate.java — structured arg parsing with validation
import java.util.*;

public class MainIntermediate {

    record Config(String host, int port, String env, boolean verbose) {
        @Override public String toString() {
            return String.format("Config{host=%s, port=%d, env=%s, verbose=%b}",
                host, port, env, verbose);
        }
    }

    public static void main(String[] args) {
        Config config;
        try {
            config = parseArgs(args);
        } catch (IllegalArgumentException e) {
            System.err.println("ERROR: " + e.getMessage());
            printUsage();
            System.exit(1);   // non-zero exit code = failure
            return;           // compiler: unreachable, but needed so 'config' is definitely assigned
        }

        System.out.println("=== Service starting ===");
        System.out.println("Config: " + config);
        System.out.println("Environment: " + config.env().toUpperCase());

        if (config.verbose()) {
            System.out.println("[VERBOSE] JVM: " + System.getProperty("java.version"));
            System.out.println("[VERBOSE] OS:  " + System.getProperty("os.name"));
            System.out.println("[VERBOSE] PID: " + ProcessHandle.current().pid());
        }

        System.out.printf("Listening on %s:%d%n", config.host(), config.port());
        // → in real code: start server here, block until shutdown
    }

    static Config parseArgs(String[] args) {
        Map<String, String> map = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i++) {
            if (args[i].startsWith("--")) {
                String key = args[i].substring(2);
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    map.put(key, args[++i]);
                } else {
                    map.put(key, "true");   // flag without value → boolean flag
                }
            }
        }

        // Required
        String host = map.getOrDefault("host", "localhost");
        String portStr = map.getOrDefault("port", "8080");
        String env = map.get("env");
        if (env == null) throw new IllegalArgumentException("--env is required (dev|staging|prod)");
        if (!Set.of("dev", "staging", "prod").contains(env))
            throw new IllegalArgumentException("--env must be one of: dev, staging, prod");

        int port;
        try { port = Integer.parseInt(portStr); }
        catch (NumberFormatException e) { throw new IllegalArgumentException("--port must be an integer"); }
        if (port < 1 || port > 65535) throw new IllegalArgumentException("--port must be 1–65535");

        boolean verbose = map.containsKey("verbose");
        return new Config(host, port, env, verbose);
    }

    static void printUsage() {
        System.err.println("Usage: java MainIntermediate.java --env <dev|staging|prod> [--host <h>] [--port <p>] [--verbose]");
        System.err.println("  --env      required: dev, staging, or prod");
        System.err.println("  --host     default: localhost");
        System.err.println("  --port     default: 8080");
        System.err.println("  --verbose  print extra debug info");
    }
}
```

**How to run:** `java MainIntermediate.java --env prod --port 9090 --verbose`

```
=== Service starting ===
Config: Config{host=localhost, port=9090, env=prod, verbose=true}
Environment: PROD
[VERBOSE] JVM: 21.0.2
[VERBOSE] OS:  Mac OS X
[VERBOSE] PID: 12345
Listening on localhost:9090
```

`System.exit(1)` terminates the JVM with exit code 1 — the calling shell sees a non-zero status, which CI systems interpret as a build failure. Always use `System.exit(1)` (not throwing an exception from `main`) for command-line tools that need to signal failure to their caller.

### Level 3 — Advanced

Same launcher grown to support environment-variable fallbacks, `--help`, shutdown hooks (run when the JVM exits), and runtime argument validation with detailed error reporting.

```java
// MainAdvanced.java — production-grade main: env fallbacks, shutdown hook, --help
import java.util.*;
import java.util.stream.*;

public class MainAdvanced {

    record Config(String host, int port, String env, boolean verbose, String logFile) {}

    public static void main(String[] args) throws Exception {
        // --help short-circuit
        if (Arrays.asList(args).contains("--help") || Arrays.asList(args).contains("-h")) {
            printHelp();
            System.exit(0);
        }

        Config config;
        try {
            config = parseArgs(args);
        } catch (IllegalArgumentException e) {
            System.err.println("Error: " + e.getMessage());
            System.err.println("Run with --help for usage.");
            System.exit(2);  // exit code 2 = misuse of command
            return;
        }

        System.out.printf("=== Launcher v1.0 starting ===%n");
        System.out.printf("host=%s port=%d env=%s verbose=%b logFile=%s%n%n",
            config.host(), config.port(), config.env(), config.verbose(), config.logFile());

        // Register shutdown hook (runs when CTRL+C or System.exit is called)
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("[SHUTDOWN] Graceful shutdown complete.");
            // In real code: close DB connections, flush buffers, etc.
        }, "shutdown-hook"));

        // Simulate startup
        System.out.println("Connecting to config service...");
        Thread.sleep(100);
        System.out.println("Loading application context...");
        Thread.sleep(200);
        System.out.printf("Service ready on %s:%d [%s]%n",
            config.host(), config.port(), config.env().toUpperCase());

        // Simulate 1 second of "running"
        Thread.sleep(1000);

        // Clean shutdown
        System.out.println("Shutdown signal received.");
        System.exit(0); // triggers shutdown hook above
    }

    static Config parseArgs(String[] args) {
        Map<String, String> map = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i++) {
            if (args[i].startsWith("--") && args[i].length() > 2) {
                String key = args[i].substring(2);
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    map.put(key, args[++i]);
                } else {
                    map.put(key, "true");
                }
            }
        }

        // env: arg > env var > default
        String env = map.getOrDefault("env",
            Optional.ofNullable(System.getenv("APP_ENV")).orElse("dev"));
        if (!Set.of("dev", "staging", "prod").contains(env))
            throw new IllegalArgumentException("env must be dev|staging|prod, got: " + env);

        // host: arg > env var > default
        String host = map.getOrDefault("host",
            Optional.ofNullable(System.getenv("APP_HOST")).orElse("localhost"));

        // port: arg > env var > default
        String portStr = map.getOrDefault("port",
            Optional.ofNullable(System.getenv("APP_PORT")).orElse("8080"));
        int port;
        try { port = Integer.parseInt(portStr); }
        catch (NumberFormatException e) { throw new IllegalArgumentException("port must be integer: " + portStr); }
        if (port < 1 || port > 65535) throw new IllegalArgumentException("port out of range: " + port);

        boolean verbose = map.containsKey("verbose") || "true".equals(System.getenv("APP_VERBOSE"));
        String logFile = map.getOrDefault("log-file", System.getenv("APP_LOG_FILE"));

        return new Config(host, port, env, verbose, logFile);
    }

    static void printHelp() {
        System.out.println("""
            Usage: java MainAdvanced.java [options]

            Options:
              --env <dev|staging|prod>   environment (env: APP_ENV, default: dev)
              --host <host>              bind address (env: APP_HOST, default: localhost)
              --port <port>              TCP port (env: APP_PORT, default: 8080)
              --log-file <path>          log output file (env: APP_LOG_FILE)
              --verbose                  enable debug output (env: APP_VERBOSE=true)
              -h, --help                 show this help

            Exit codes:
              0  success
              1  runtime error
              2  invalid arguments
            """);
    }
}
```

**How to run:** `java MainAdvanced.java --env prod --port 8080 --verbose`

Or with environment variables: `APP_ENV=staging java MainAdvanced.java`

The shutdown hook (`Runtime.getRuntime().addShutdownHook(...)`) runs automatically when `System.exit()` is called or when the JVM receives `SIGTERM` (Ctrl+C, Docker stop). This is where connection pool teardown, log flushing, and in-progress request draining belong.

## 6. Walkthrough

Execution trace in `MainAdvanced.main`:

**JVM startup.** You run `java MainAdvanced.java --env prod --port 8080 --verbose`. The `java` launcher:
1. Finds `MainAdvanced` class by name.
2. Looks for `public static void main(String[])`.
3. Builds `String[] args = {"--env", "prod", "--port", "8080", "--verbose"}`.
4. Calls `main(args)`.

**`--help` check.** `Arrays.asList(args).contains("--help")` scans the array. Not found → continue.

**`parseArgs(args)`.** The loop walks args two-at-a-time:
- `args[0]="--env"` → key="env", `args[1]="prod"` → `map.put("env", "prod")`, i advances to 2.
- `args[2]="--port"` → key="port", `args[3]="8080"` → `map.put("port", "8080")`, i advances to 4.
- `args[4]="--verbose"` → next token doesn't exist or starts with `--` → `map.put("verbose", "true")`.

**Env-variable fallback.** `map.getOrDefault("env", Optional.ofNullable(System.getenv("APP_ENV")).orElse("dev"))` → "prod" (from map, env var not consulted).

**Validation.** `Set.of("dev","staging","prod").contains("prod")` → true. Port 8080: `Integer.parseInt("8080")` → 8080, range check passes. Config record created.

**Shutdown hook registration.** `Runtime.getRuntime().addShutdownHook(thread)` registers a thread the JVM will start when shutting down. The hook thread must complete within a timeout (default: no fixed timeout, but JVM may force-kill after `--kill-delay`).

**Startup simulation.** Two `Thread.sleep()` calls simulate real startup work (connecting to DB, loading config).

**`System.exit(0)`.** Triggers: (a) all registered shutdown hooks are started in parallel; (b) after they complete, the JVM exits with code 0. The shell sees `$?` = 0 = success.

## 7. Gotchas & takeaways

> **`String[] args` is never null, but it can be empty.** The JVM always passes a non-null array. If no arguments are given, `args.length == 0`. Accessing `args[0]` without checking `args.length > 0` causes `ArrayIndexOutOfBoundsException` — one of the most common beginner crashes.

> **`System.exit()` does NOT wait for non-daemon threads.** If you call `System.exit(0)` from `main()` while other threads are still running, the JVM calls shutdown hooks, then force-terminates everything. Use a proper shutdown signal mechanism (e.g., `CountDownLatch`) to coordinate graceful thread shutdown before calling `System.exit`.

- `args` are always `String` — parse numbers with `Integer.parseInt(args[i])` wrapped in try-catch.
- `System.exit(0)` = success, `System.exit(1)` = general error, `System.exit(2)` = argument misuse — follow POSIX convention.
- Shutdown hooks run on `System.exit()`, SIGTERM, and uncaught exceptions in daemon threads, but NOT on `SIGKILL` (kill -9).
- Varargs `main(String... args)` is identical to `main(String[] args)` at the bytecode level — either works.
- JDK 21+ preview / JDK 25+: `void main()` in unnamed classes removes boilerplate for simple scripts; the classic signature still works everywhere.
