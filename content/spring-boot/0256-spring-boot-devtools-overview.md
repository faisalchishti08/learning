---
card: spring-boot
gi: 256
slug: spring-boot-devtools-overview
title: Spring Boot DevTools overview
---

## 1. What it is

**Spring Boot DevTools** (`spring-boot-devtools`) is a development-time dependency that dramatically speeds up the inner development loop — the cycle of edit → see change. It provides:

- **Automatic restart** — when classpath files change, the application restarts in ~1 second instead of 5–30 seconds, because DevTools keeps a base classloader loaded and only reloads the application layer.
- **LiveReload** — triggers browser refresh automatically when resources (templates, static files) change.
- **Development-friendly property overrides** — disables template caching, enables verbose logging of web requests, and other settings that hurt development but help production.
- **Remote DevTools** — extends restart/reload to apps running on remote servers or inside Docker.

Add it with:

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-devtools</artifactId>
  <optional>true</optional>
</dependency>
```

`<optional>true</optional>` prevents it from being included when this project is used as a library dependency.

## 2. Why & when

Without DevTools, a typical Spring Boot development cycle on a medium-sized app looks like:
- Edit a controller method.
- Wait 15–30 seconds for Maven/Gradle to recompile and for the JVM to restart.
- Reload the browser manually.

With DevTools:
- Edit a controller method.
- IDE recompiles on save (< 1 second).
- DevTools detects the classpath change, restarts in ~1 second using the retained base classloader.
- Browser auto-reloads via LiveReload.

Total: 2–3 seconds instead of 20–30. At 50 cycles per day that saves 15–25 minutes of waiting.

DevTools is meant for **development only** — it disables itself automatically when running from a production JAR (see gi 262 for details).

## 3. Core concept

DevTools uses **two classloaders** to achieve fast restart:

1. **Base classloader** — loads unchanged classes: your dependencies, Spring Framework, Spring Boot itself. This loader is created once and never restarted.
2. **Restart classloader** — loads your code (`target/classes`, `build/classes`). When DevTools detects a change it throws away this loader and creates a new one, leaving the base loader intact.

Think of it like a **browser tab with cached resources**. The static assets (images, fonts, frameworks — your dependencies) load from the browser cache instantly. Only the new HTML (your changed code) is re-fetched. The full page appears immediately because most work was already done.

```
Before DevTools:    [dependencies] + [your code] = 15–30s restart
With DevTools:      [dependencies (cached)] + [your code (reloaded)] = 1–2s restart
```

The split point is the classpath. DevTools watches `target/classes` (Maven) or `build/classes` (Gradle) for changes. Configure additional watch paths via `spring.devtools.restart.additional-paths`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DevTools two-classloader architecture showing fast restart by retaining base classloader">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Base classloader (persistent) -->
  <rect x="30" y="30" width="280" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="170" y="56" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Base ClassLoader (persistent)</text>
  <text x="170" y="74" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Boot, Spring Framework, libraries</text>
  <text x="170" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">~50–200 MB, loaded once, never restarted</text>

  <!-- Restart classloader -->
  <rect x="30" y="120" width="280" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="170" y="146" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Restart ClassLoader (disposable)</text>
  <text x="170" y="164" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Your code: controllers, services, entities</text>
  <text x="170" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Replaced in ~1s when classpath changes</text>

  <!-- File watcher -->
  <rect x="420" y="75" width="240" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="100" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">DevTools File Watcher</text>
  <text x="540" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Watches target/classes</text>
  <text x="540" y="134" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Change detected → restart</text>
  <text x="540" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">only Restart ClassLoader</text>

  <line x1="312" y1="155" x2="418" y2="130" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="418" y1="140" x2="312" y2="160" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arr)"/>

  <text x="350" y="225" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Base classloader survives restart — dependencies don't reload, saving 90% of restart time</text>
</svg>

DevTools discards only the application classloader on restart; the base dependency classloader stays alive, making restarts 10–20x faster.

## 5. Runnable example

```java
// DevToolsOverviewDemo.java — run with: java DevToolsOverviewDemo.java
// Illustrates the DevTools two-classloader model and prints the
// configuration options and quick-start setup steps.

public class DevToolsOverviewDemo {

    public static void main(String[] args) {
        System.out.println("=== Spring Boot DevTools Overview ===\n");
        printSetup();
        printClassloaderModel();
        printKeyProperties();
        printWorkflow();
    }

    static void printSetup() {
        System.out.println("--- pom.xml dependency ---");
        System.out.println("""
            <dependency>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-devtools</artifactId>
              <optional>true</optional>   <!-- excluded from production JARs -->
            </dependency>

            <!-- Gradle: -->
            <!-- developmentOnly 'org.springframework.boot:spring-boot-devtools' -->
            """);
    }

    static void printClassloaderModel() {
        System.out.println("--- Two-classloader restart model ---");

        // Simulate timing
        long fullRestart = 18_000; // ms without DevTools
        long baseLoad    = 15_000; // ms for dependencies (cached)
        long restartLoad =  1_500; // ms for application code

        System.out.printf("  Full restart (no DevTools)       : ~%,d ms%n", fullRestart);
        System.out.printf("  Base classloader (cached, 1st)   : ~%,d ms%n", baseLoad);
        System.out.printf("  Restart classloader (every time) : ~%,d ms%n", restartLoad);
        System.out.printf("  Speedup factor                   : ~%.0fx%n",
            (double) fullRestart / restartLoad);
        System.out.println();
    }

    static void printKeyProperties() {
        System.out.println("--- application.properties / DevTools config ---");
        System.out.println("""
            # Exclude dirs from triggering restart (e.g. static assets)
            spring.devtools.restart.exclude=static/**,public/**,templates/**

            # Add extra paths beyond target/classes
            spring.devtools.restart.additional-paths=src/main/resources

            # Disable restart entirely (keep LiveReload only)
            spring.devtools.restart.enabled=false

            # Poll interval for file changes (default: 1000ms)
            spring.devtools.restart.poll-interval=2s
            spring.devtools.restart.quiet-period=400ms
            """);
    }

    static void printWorkflow() {
        System.out.println("--- Typical DevTools development workflow ---");
        String[] steps = {
            "1. Add devtools dependency and start app with 'mvn spring-boot:run' or from IDE",
            "2. Edit a Java file in your IDE",
            "3. IDE compiles on save → .class appears in target/classes",
            "4. DevTools detects change (~1s poll) → triggers restart",
            "5. App restarts using cached base classloader (~1s)",
            "6. Browser auto-refreshes via LiveReload (if enabled)",
            "7. Total edit-to-see time: 2–3 seconds",
        };
        for (String s : steps) System.out.println("  " + s);
    }
}
```

**How to run:** `java DevToolsOverviewDemo.java`

## 6. Walkthrough

- **`<optional>true</optional>`** — Maven scoping that prevents DevTools from being included when this project is a dependency of another. In Gradle the `developmentOnly` configuration does the same.
- **Restart timing** — the printed numbers reflect real-world measurements on a medium Spring Boot app. The key insight is that `baseLoad` (15 s) is paid once at first start; subsequent restarts only pay `restartLoad` (1.5 s).
- **`spring.devtools.restart.exclude=static/**`** — static files (`CSS`, `JS`, images) should not trigger a full restart; DevTools handles them via LiveReload instead (browser refresh without JVM restart). Exclude them from restart to avoid unnecessary application reloads when only a CSS file changed.
- **`quiet-period`** — DevTools waits `quiet-period` (400 ms default) after the last file change before triggering a restart. This batches rapid saves (e.g., IDE auto-format touching multiple files) into a single restart rather than one per file.
- **`poll-interval`** — how often DevTools checks for classpath changes. Lower values (500 ms) give faster response but use more CPU. For most developers the default 1 s feels instantaneous.

## 7. Gotchas & takeaways

> **DevTools is not DevTools without IDE compilation.** The file watcher looks at `target/classes`, not `.java` files. Your IDE must be set to compile on save (IntelliJ: "Build project automatically" in settings; VS Code: Java Extension auto-compiles). Without auto-compilation, DevTools never sees a change.

> **DevTools disables itself in "production mode"** — when running from a fat JAR (`java -jar`) or when certain production classpath signatures are detected. You don't need to explicitly disable it for production deployments, but understanding *why* prevents confusion when colleagues report "DevTools isn't working in staging" (it's not supposed to).

- DevTools applies development property overrides (disables template caching, etc.) automatically — you don't need to set them manually in `application-dev.properties`.
- Restart is triggered by classpath changes, not source changes — IDEs that don't auto-compile won't trigger it.
- Use `spring.devtools.restart.trigger-file` to control restart manually: DevTools only restarts when a specific file is modified, giving you control over when to apply multi-file changes atomically.
- The restart classloader boundary means beans in your code can't hold references across restarts — DevTools resets `ApplicationContext` listeners and custom singleton caches on each restart.
