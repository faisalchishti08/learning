---
card: spring-boot
gi: 59
slug: application-startup-tracking-applicationstartup-bufferingapp
title: Application startup tracking (ApplicationStartup / BufferingApplicationStartup)
---

## 1. What it is

**`ApplicationStartup`** is a Spring Boot interface that records **startup steps** — named phases of the application bootstrap process — with timing information. It lets you see exactly where startup time is spent, down to the level of individual bean instantiation, auto-configuration evaluation, and component scanning.

`BufferingApplicationStartup` is the built-in implementation that buffers recorded steps in memory and exposes them via Spring Boot Actuator's `/actuator/startup` endpoint.

```java
SpringApplication app = new SpringApplication(MyApp.class);
app.setApplicationStartup(new BufferingApplicationStartup(2048));  // buffer up to 2048 steps
app.run(args);
```

Then query:
```
GET /actuator/startup
```

Response: a JSON list of steps with names, start times, and durations. Common step names:
- `spring.boot.application.starting`
- `spring.boot.application.environment-prepared`
- `spring.context.beans.post-process`
- `spring.beans.instantiate` (per-bean)
- `spring.context.component-classes.scan`

## 2. Why & when

Without startup tracking, answering "why does my app take 12 seconds to start?" requires profiling tools and guesswork. `ApplicationStartup` makes the startup timeline observable in production without attaching a profiler.

Use it when:
- Startup time is unexpectedly slow and you need to find the bottleneck (which bean takes longest to instantiate?).
- You want to track startup time trends across deployments (add to CI or canary metrics).
- You are optimising for cold-start time in serverless or Kubernetes environments.
- You want to audit what happens during startup for security or compliance reasons.

Disable it in production if the overhead is a concern (default is `DefaultApplicationStartup` which is a no-op).

## 3. Core concept

Think of `ApplicationStartup` as a **flight data recorder** for the launch. Each phase of the startup process creates a `StartupStep`:

1. The step is opened with `applicationStartup.start("step.name")`.
2. Tags (key-value metadata) are added: `.tag("class", className)`.
3. The step is ended with `.end()`.
4. `BufferingApplicationStartup` stores these steps in a ring buffer.

Spring Framework itself already instruments its core operations (bean instantiation, post-processing, scanning) with startup steps. You can add your own steps in custom code:

```java
StartupStep step = applicationStartup.start("mylib.heavy-init");
step.tag("component", "ReportEngine");
initializeReportEngine();
step.end();
```

The Actuator endpoint serialises the buffered steps as JSON; clients (Spring Boot CLI, IDE plugins, or custom dashboards) visualise the timeline.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Startup tracking: BufferingApplicationStartup recording steps with timings and exposing via Actuator">
  <!-- Startup steps on timeline -->
  <text x="20" y="30" fill="#e6edf3" font-size="12" font-family="monospace">Startup timeline (each bar = one StartupStep)</text>

  <rect x="20" y="44" width="400" height="22" rx="4" fill="#6db33f" fill-opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="30" y="60" fill="#6db33f" font-size="10" font-family="monospace">spring.boot.application.starting (400ms)</text>

  <rect x="20" y="74" width="120" height="22" rx="4" fill="#79c0ff" fill-opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="30" y="90" fill="#79c0ff" font-size="10" font-family="monospace">spring.context.component-classes.scan (120ms)</text>

  <rect x="150" y="74" width="200" height="22" rx="4" fill="#79c0ff" fill-opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="90" fill="#79c0ff" font-size="10" font-family="monospace">spring.beans.instantiate: HeavyService (200ms)</text>

  <rect x="360" y="74" width="60" height="22" rx="4" fill="#8b949e" fill-opacity="0.3" stroke="#8b949e" stroke-width="1"/>
  <text x="370" y="90" fill="#8b949e" font-size="10" font-family="monospace">...etc</text>

  <!-- Buffer box -->
  <rect x="20" y="116" width="300" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="138" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">BufferingApplicationStartup</text>
  <text x="170" y="156" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">ring buffer of N steps (names + tags + timing)</text>

  <!-- Actuator endpoint -->
  <rect x="380" y="116" width="260" height="50" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="138" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">GET /actuator/startup</text>
  <text x="510" y="156" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">→ JSON timeline of all steps</text>

  <line x1="322" y1="141" x2="378" y2="141" stroke="#6db33f" stroke-width="2" marker-end="url(#st)"/>

  <!-- Bottom note -->
  <text x="20" y="200" fill="#8b949e" font-size="10" font-family="monospace">DefaultApplicationStartup (default) = no-op; zero overhead in production</text>
  <text x="20" y="218" fill="#8b949e" font-size="10" font-family="monospace">BufferingApplicationStartup = instrumented; enable during investigation</text>

  <defs>
    <marker id="st" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`BufferingApplicationStartup` records all startup steps in a ring buffer; `/actuator/startup` exposes the timeline as JSON for analysis.

## 5. Runnable example

```java
// StartupTrackingDemo.java
// How to run: java StartupTrackingDemo.java  (JDK 17+)
// Simulates the ApplicationStartup / BufferingApplicationStartup pattern:
// steps are recorded with names, tags, and durations.

import java.util.*;
import java.time.Instant;

public class StartupTrackingDemo {

    // ── Startup step model ────────────────────────────────────────
    record StartupStep(String name, Map<String, String> tags, long durationMs, Instant startTime) {
        @Override public String toString() {
            return String.format("%-54s %4dms  tags=%s", name, durationMs, tags);
        }
    }

    // ── BufferingApplicationStartup simulation ─────────────────────
    static List<StartupStep> buffer = new ArrayList<>();

    static AutoCloseable step(String name, Map<String, String> tags, long simulatedMs) {
        Instant start = Instant.now();
        try { Thread.sleep(simulatedMs); } catch (InterruptedException ignored) {}
        long actual = System.currentTimeMillis() - start.toEpochMilli();
        StartupStep step = new StartupStep(name, tags, actual, start);
        buffer.add(step);
        return () -> {};  // end() is implicit in this simulation
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Starting application (startup tracking enabled) ===\n");

        // Simulate Spring Framework + Spring Boot instrumentation
        step("spring.boot.application.starting",            Map.of(), 10);
        step("spring.boot.application.environment-prepared",Map.of(), 15);
        step("spring.context.component-classes.scan",       Map.of("basePackage", "com.example"), 80);
        step("spring.beans.instantiate",                    Map.of("beanName", "dataSource"), 120);
        step("spring.beans.instantiate",                    Map.of("beanName", "heavyReportService"), 350);
        step("spring.beans.instantiate",                    Map.of("beanName", "requestService"), 10);
        step("spring.context.beans.post-process",           Map.of(), 30);
        step("spring.boot.application.started",             Map.of(), 5);

        // Custom user step (library or app code using applicationStartup directly)
        step("myapp.cache.warm-up",                         Map.of("cacheSize", "1000"), 200);

        step("spring.boot.application.ready",               Map.of(), 5);

        // ── /actuator/startup endpoint simulation ─────────────────
        System.out.println("GET /actuator/startup → step timeline:\n");
        System.out.printf("%-54s %6s  %s%n", "Step name", "ms", "Tags");
        System.out.println("-".repeat(100));

        long total = 0;
        for (StartupStep s : buffer) {
            System.out.println(s);
            total += s.durationMs();
        }
        System.out.println("-".repeat(100));
        System.out.printf("Total startup time: %dms%n", total);

        // Identify bottleneck
        StartupStep slowest = buffer.stream()
            .max(Comparator.comparingLong(StartupStep::durationMs))
            .orElseThrow();
        System.out.println("\nBottleneck: " + slowest.name() + " — " + slowest.durationMs() + "ms "
            + slowest.tags());
    }
}
```

**How to run:** `java StartupTrackingDemo.java`

Expected output (timings approximate):
```
=== Starting application (startup tracking enabled) ===

GET /actuator/startup → step timeline:

Step name                                              ms    Tags
----------------------------------------------------------------------------------------------------
spring.boot.application.starting                        10ms  {}
spring.boot.application.environment-prepared            15ms  {}
spring.context.component-classes.scan                   80ms  {basePackage=com.example}
spring.beans.instantiate                               120ms  {beanName=dataSource}
spring.beans.instantiate                               350ms  {beanName=heavyReportService}
spring.beans.instantiate                                10ms  {beanName=requestService}
spring.context.beans.post-process                       30ms  {}
spring.boot.application.started                          5ms  {}
myapp.cache.warm-up                                    200ms  {cacheSize=1000}
spring.boot.application.ready                            5ms  {}
----------------------------------------------------------------------------------------------------
Total startup time: ~825ms

Bottleneck: spring.beans.instantiate — 350ms {beanName=heavyReportService}
```

## 6. Walkthrough

- Each `step()` call simulates opening a `StartupStep`, waiting the given duration, and closing it. In real Spring Boot, Spring Framework creates steps automatically for its own operations.
- The step names follow the convention `spring.xxx.yyy` for framework steps and `myapp.xxx` for user-defined steps — this separation makes filtering easy.
- Tags provide metadata: `beanName=heavyReportService` lets you know which specific bean caused the delay, not just "some bean".
- The bottleneck analysis (`max(durationMs)`) finds `heavyReportService` at 350ms — this is the actionable finding: this bean should be made lazy or its initialisation optimised.
- `myapp.cache.warm-up` shows a custom step added by application code — you can use `applicationStartup.start("name")` in your own services to track custom startup tasks.

## 7. Gotchas & takeaways

> `BufferingApplicationStartup` must be set **before** `SpringApplication.run()`, not in a `@Configuration` class. By the time `@Configuration` beans are processed, most startup steps have already been recorded.

> The buffer is a ring buffer with a fixed capacity. If startup creates more steps than the capacity (default: 2048 is recommended), the **oldest** steps are discarded. For very slow apps with many beans, increase the buffer size.

- Enable: `app.setApplicationStartup(new BufferingApplicationStartup(2048))` in `main()`.
- Expose: `management.endpoints.web.exposure.include=startup` in `application.properties` (needed if not already exposing all endpoints).
- The `DefaultApplicationStartup` (default) is a no-op — zero memory and CPU overhead. Only use `BufferingApplicationStartup` when investigating.
- After diagnosis, remove `BufferingApplicationStartup` or use Spring Boot's build-time AOT (Ahead-of-Time) processing to eliminate startup overhead entirely.
- Step names are stable within a Spring Boot version but may change between major versions — don't hardcode step names in alert rules.
