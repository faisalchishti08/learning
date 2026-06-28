---
card: spring-boot
gi: 257
slug: automatic-restart
title: Automatic restart
---

## 1. What it is

**Automatic restart** is the core feature of Spring Boot DevTools that restarts the application whenever files on the classpath change. Unlike a full JVM restart (which takes 15–30 seconds for a medium app), DevTools' automatic restart takes 1–3 seconds by keeping the dependency classloader alive and only reloading the application classloader.

DevTools monitors the classpath directories — `target/classes` (Maven) or `build/classes` (Gradle) — and when a `.class` file is written, it waits for a quiet period (400 ms default), then triggers a restart.

It works alongside normal `mvn spring-boot:run` or IDE launch — no special configuration is required to enable it; adding the devtools dependency is sufficient.

## 2. Why & when

Automatic restart is useful in the **inner development loop**: writing code, observing the running application, fixing bugs, and repeating. The key benefit is eliminating manual stop/start cycles.

Automatic restart is appropriate when:
- You're actively editing application code (controllers, services, entities).
- You're working in an IDE with auto-compile (IntelliJ, Eclipse, VS Code + Java Extension).
- You want changes visible in < 3 seconds without hitting a run button.

It's not appropriate when:
- You change only static resources (CSS, JS, images) — LiveReload handles those without a restart.
- You're running in production (automatic restart is disabled in production mode automatically).
- You're debugging a startup condition — the restart loop may make it hard to observe startup logs.

## 3. Core concept

The restart mechanism works in three stages:

1. **Watch** — a background thread polls classpath directories every `poll-interval` (1 s default) for file modification timestamps.
2. **Quiet period** — after detecting a change, DevTools waits `quiet-period` (400 ms) for more changes to settle, batching multiple file saves into one restart.
3. **Restart** — the current application classloader is discarded; a new restart classloader is created from the updated classpath. Spring's `ApplicationContext` is re-created using the new classloader.

The key config properties:

```properties
spring.devtools.restart.enabled=true               # on by default
spring.devtools.restart.poll-interval=1s
spring.devtools.restart.quiet-period=400ms
spring.devtools.restart.additional-paths=src/main/resources
spring.devtools.restart.exclude=static/**,templates/**
spring.devtools.restart.trigger-file=.restart
```

`trigger-file` is particularly useful: set it to a file name and DevTools won't restart until that specific file is modified — giving you control over when a multi-file change is applied as a unit.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Automatic restart timeline: file change detected, quiet period, restart triggered">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Timeline line -->
  <line x1="30" y1="120" x2="670" y2="120" stroke="#8b949e" stroke-width="1.5"/>

  <!-- Edit -->
  <circle cx="80" cy="120" r="6" fill="#79c0ff"/>
  <text x="80" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Edit saved</text>
  <text x="80" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">IDE compiles</text>
  <text x="80" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.class written</text>

  <!-- Poll detects -->
  <circle cx="200" cy="120" r="6" fill="#79c0ff"/>
  <text x="200" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Poll detects</text>
  <text x="200" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">up to 1s later</text>

  <!-- Quiet period bar -->
  <rect x="200" y="130" width="120" height="20" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="260" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">quiet period (400ms)</text>

  <!-- Restart -->
  <circle cx="340" cy="120" r="8" fill="#6db33f"/>
  <text x="340" y="105" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Restart</text>
  <text x="340" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">classloader</text>
  <text x="340" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">discarded</text>

  <!-- New context bar -->
  <rect x="340" y="130" width="160" height="20" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="145" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ApplicationContext created (~1s)</text>

  <!-- App ready -->
  <circle cx="530" cy="120" r="8" fill="#6db33f"/>
  <text x="530" y="105" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Ready</text>
  <text x="530" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">~2s total</text>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Full cycle from .class write to running app: typically 1.5–3 seconds</text>
</svg>

Edit → IDE compile → DevTools poll → quiet period → context restart → app ready in ~2 seconds total.

## 5. Runnable example

```java
// AutoRestartDemo.java — run with: java AutoRestartDemo.java
// Simulates the automatic restart polling logic and demonstrates
// the trigger-file and exclude patterns.

import java.io.*;
import java.nio.file.*;
import java.util.Set;

public class AutoRestartDemo {

    // Paths DevTools watches (simplified)
    static final Path CLASSES_DIR   = Path.of("target/classes");
    static final long POLL_MS       = 1000;
    static final long QUIET_MS      = 400;
    static final String TRIGGER     = ".restart"; // optional trigger file

    // Excluded patterns (won't trigger restart even if changed)
    static final Set<String> EXCLUDES = Set.of(
        "static/", "public/", "templates/", "META-INF/maven/"
    );

    public static void main(String[] args) throws Exception {
        System.out.println("=== Automatic Restart Demo ===\n");

        printConfig();
        simulateRestartCycle();
        demonstrateTriggerFile();
    }

    static void printConfig() {
        System.out.println("--- Key application.properties settings ---");
        System.out.println("""
            spring.devtools.restart.poll-interval=1s
            spring.devtools.restart.quiet-period=400ms

            # Only restart when this file changes (batch control):
            # spring.devtools.restart.trigger-file=.restart

            # Exclude from restart (handle via LiveReload instead):
            spring.devtools.restart.exclude=static/**,public/**,templates/**

            # Add non-classpath paths to watch:
            spring.devtools.restart.additional-paths=config/
            """);
    }

    static void simulateRestartCycle() throws InterruptedException {
        System.out.println("--- Simulated restart cycle ---");

        System.out.println("  [0ms]    Edit saved in IDE → .class written to target/classes");
        Thread.sleep(200);

        System.out.println("  [~1000ms] Poll detects change in target/classes");
        System.out.println("  [~1000ms] Checking if path is excluded...");

        String changedFile = "com/example/OrderController.class";
        boolean excluded = EXCLUDES.stream().anyMatch(changedFile::startsWith);
        System.out.println("  [~1000ms] " + changedFile + " → excluded=" + excluded);

        System.out.println("  [~1000ms] Waiting for quiet period (400ms)...");
        Thread.sleep(400);

        System.out.println("  [~1400ms] Quiet period elapsed → triggering restart");
        System.out.println("  [~1400ms] Restart classloader discarded");
        System.out.println("  [~1400ms] New ApplicationContext starting...");
        Thread.sleep(500);

        System.out.println("  [~1900ms] Application ready — all beans wired");
        System.out.println("  [~1900ms] LiveReload triggered → browser refreshes\n");
    }

    static void demonstrateTriggerFile() {
        System.out.println("--- Trigger-file pattern (for atomic multi-file changes) ---");
        System.out.println("""
            When spring.devtools.restart.trigger-file=.restart is set:

              1. Edit 5 Java files (IDE compiles all to .class)
              2. DevTools detects changes but DOES NOT restart yet
              3. Touch the trigger file:   touch .restart
              4. DevTools NOW triggers a single restart with all 5 changes applied

            Useful when a feature spans multiple files that must be consistent.
            Without trigger-file, DevTools might restart after file 1 is compiled,
            before files 2-5 are ready — leaving the app in an inconsistent state.
            """);
    }
}
```

**How to run:** `java AutoRestartDemo.java`

## 6. Walkthrough

- **Exclusion check** — DevTools skips the restart if the changed path matches an exclude pattern. `static/**` and `templates/**` are excluded by default because those files are served or rendered at runtime; their changes take effect without a JVM restart (templates are reloaded per-request when caching is disabled, which DevTools also sets).
- **Quiet period** — the 400 ms pause after the last detected change prevents "restart storms" when an IDE saves 10 files in quick succession (e.g., on reformat). DevTools waits until file writes have settled before restarting.
- **Trigger file** — the most underused DevTools feature. When you're refactoring across many files, set `trigger-file=.restart` so all files are compiled before the restart. Without it, DevTools restarts after the first compiled file, potentially in an inconsistent state where some new code calls a method that doesn't exist yet in the old code.
- **Restart classloader discarded** — the restart classloader holds all application class objects. Discarding it garbage-collects all your controllers, services, and entities. The new classloader creates fresh instances from the updated `.class` files.

## 7. Gotchas & takeaways

> **Automatic restart does not pick up changes to `src/main/resources` by default** in some configurations. If you're editing `application.properties` and don't see changes, add `spring.devtools.restart.additional-paths=src/main/resources` to your devtools configuration (`~/.config/spring-boot/spring-boot-devtools.properties`).

> **IntelliJ IDEA requires "Build project automatically" to be enabled** (`Settings → Build, Execution, Deployment → Compiler`) AND, for running apps, "Allow auto-make to start even if developed application is currently running" (`Registry... → compiler.automake.allow.when.app.running`). Without both, `.class` files are not written while the app is running.

- DevTools restart is not a full JVM restart — static state in classes (static fields initialised at class-load time) persists across restarts unless the class is excluded from the restart classloader.
- Use `spring.devtools.restart.trigger-file` for any multi-file refactoring to prevent intermediate inconsistent states.
- Restart is ~1–3 s; a full cold start is 10–30 s. Invest 5 minutes in configuring IDE auto-compile to get this speedup.
- If restart is interfering with debugging, set `spring.devtools.restart.enabled=false` in `application-dev.properties` to disable it while keeping other DevTools features.
