---
card: spring-boot
gi: 56
slug: using-the-applicationrunner-commandlinerunner
title: Using the ApplicationRunner / CommandLineRunner
---

## 1. What it is

`ApplicationRunner` and `CommandLineRunner` are interfaces for running code **once, immediately after the Spring ApplicationContext is fully started**. Any `@Component` implementing either interface has its `run()` method called automatically after context refresh and before the `ApplicationReadyEvent`.

```java
@Component
public class DataLoader implements CommandLineRunner {
    @Override
    public void run(String... args) throws Exception {
        // runs once on startup — args are raw command-line strings
        System.out.println("Loading seed data...");
    }
}

@Component
public class ReportStarter implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) throws Exception {
        // same timing, but receives parsed ApplicationArguments
        if (args.containsOption("generate-report")) {
            System.out.println("Generating report...");
        }
    }
}
```

The difference: `CommandLineRunner.run(String... args)` receives raw strings; `ApplicationRunner.run(ApplicationArguments args)` receives the already-parsed `ApplicationArguments` (tutorial 55).

## 2. Why & when

These interfaces fill a specific gap: code that needs to run **after all beans are wired** (so it can use `@Autowired` services) but **before the application is declared ready** (so startup-time errors abort the launch rather than silently failing later).

Use them for:
- Loading seed data or populating caches on startup.
- Running database migrations before the app accepts traffic.
- Starting background tasks or schedulers that depend on injected services.
- Generating reports or processing files when the app is used as a CLI tool.
- Verifying external service availability before declaring readiness.

Prefer `ApplicationRunner` when you need the structured argument access from `ApplicationArguments`. Use `CommandLineRunner` for simple cases where raw strings suffice.

## 3. Core concept

Think of `CommandLineRunner` and `ApplicationRunner` as the **opening ceremonies** after a new restaurant kitchen is set up. The kitchen (context) is fully equipped (all beans wired). Only then does the head chef (`run()`) walk in to do the first-day checklist (seed data, health checks, etc.) before opening to customers (`ApplicationReadyEvent`).

Key rules:
1. Both interfaces are discovered by `SpringApplication` via the standard `ApplicationContext.getBeansOf(interface)` call — no explicit registration needed.
2. Execution order: if multiple runners exist, use `@Order(N)` to control which runs first (lower N = first).
3. If `run()` throws an exception, `SpringApplication` propagates it and the application exits — startup failure is the right outcome for a broken startup task.
4. In tests with `@SpringBootTest`, runners execute by default. To skip them, use `@MockBean` for the runner or set `@SpringBootTest(classes = ...)` to exclude the runner bean.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Startup timeline showing CommandLineRunner and ApplicationRunner executing between context refresh and ApplicationReadyEvent">
  <!-- Timeline -->
  <line x1="20" y1="100" x2="640" y2="100" stroke="#8b949e" stroke-width="2" marker-end="url(#cr)"/>

  <!-- Context refresh -->
  <rect x="20" y="60" width="130" height="32" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="81" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">context refresh</text>
  <line x1="85" y1="92" x2="85" y2="100" stroke="#79c0ff" stroke-width="1.5"/>

  <!-- Runners phase -->
  <rect x="170" y="40" width="300" height="52" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="62" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">runners execute (in @Order)</text>
  <text x="215" y="82" fill="#8b949e" font-size="10" font-family="monospace">@Order(1) DataLoader.run()</text>
  <text x="360" y="82" fill="#8b949e" font-size="10" font-family="monospace">@Order(2) ReportStarter.run()</text>
  <line x1="320" y1="92" x2="320" y2="100" stroke="#6db33f" stroke-width="2"/>

  <!-- ApplicationReadyEvent -->
  <rect x="500" y="60" width="120" height="32" rx="5" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="560" y="81" fill="#e6edf3" font-size="10" font-family="monospace" text-anchor="middle">ApplicationReady</text>
  <line x1="560" y1="92" x2="560" y2="100" stroke="#6db33f" stroke-width="2"/>

  <!-- Labels below timeline -->
  <text x="85" y="130" fill="#79c0ff" font-size="9" font-family="sans-serif" text-anchor="middle">all beans ready</text>
  <text x="320" y="130" fill="#6db33f" font-size="9" font-family="sans-serif" text-anchor="middle">startup tasks run here</text>
  <text x="560" y="130" fill="#e6edf3" font-size="9" font-family="sans-serif" text-anchor="middle">traffic accepted</text>

  <defs>
    <marker id="cr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Runners execute after all beans are created but before the app declares readiness; `@Order` controls execution sequence.

## 5. Runnable example

```java
// RunnerDemo.java
// How to run: java RunnerDemo.java  (JDK 17+)
// Demonstrates CommandLineRunner and ApplicationRunner patterns with @Order.

import java.util.*;

// ── Simulated annotations ─────────────────────────────────────────
@interface Component {}
@interface Order { int value(); }

// ── Interfaces ────────────────────────────────────────────────────
@FunctionalInterface interface CommandLineRunner {
    void run(String... args) throws Exception;
}

@FunctionalInterface interface ApplicationRunner {
    void run(List<String> optionNames, List<String> nonOptionArgs) throws Exception;
}

// ── @Order(1): loads seed data first ──────────────────────────────
@Component @Order(1)
class DataLoader implements CommandLineRunner {
    @Override public void run(String... args) throws Exception {
        System.out.println("[DataLoader] Inserting seed data into DB (CommandLineRunner)");
        System.out.println("[DataLoader] Raw args: " + Arrays.toString(args));
    }
}

// ── @Order(2): cache warm-up second ───────────────────────────────
@Component @Order(2)
class CacheWarmer implements CommandLineRunner {
    @Override public void run(String... args) throws Exception {
        System.out.println("[CacheWarmer] Pre-loading product catalogue into Redis");
    }
}

// ── @Order(3): optional report generation (uses parsed args) ──────
@Component @Order(3)
class ReportStarter implements ApplicationRunner {
    @Override public void run(List<String> options, List<String> nonOptions) throws Exception {
        System.out.println("[ReportStarter] Options: " + options + " | Files: " + nonOptions);
        if (options.contains("generate-report")) {
            System.out.println("[ReportStarter] Generating startup report...");
        } else {
            System.out.println("[ReportStarter] --generate-report not set; skipping report");
        }
    }
}

public class RunnerDemo {

    public static void main(String[] args) throws Exception {
        // Simulate: java -jar app.jar --generate-report input.csv
        String[] simulatedArgs = {"--generate-report", "input.csv"};
        List<String> options    = new ArrayList<>();
        List<String> nonOptions = new ArrayList<>();
        for (String a : simulatedArgs) {
            if (a.startsWith("--")) options.add(a.substring(2).split("=")[0]);
            else nonOptions.add(a);
        }

        System.out.println("=== Context refreshed — executing runners in @Order ===\n");

        // Spring Boot discovers and sorts these; we run them in order manually
        List<Object> runners = List.of(new DataLoader(), new CacheWarmer(), new ReportStarter());

        for (Object runner : runners) {
            if (runner instanceof CommandLineRunner clr) {
                clr.run(simulatedArgs);
            } else if (runner instanceof ApplicationRunner ar) {
                ar.run(options, nonOptions);
            }
            System.out.println();
        }

        System.out.println("=== ApplicationReadyEvent published — app is live ===");
    }
}
```

**How to run:** `java RunnerDemo.java`

Expected output:
```
=== Context refreshed — executing runners in @Order ===

[DataLoader] Inserting seed data into DB (CommandLineRunner)
[DataLoader] Raw args: [--generate-report, input.csv]

[CacheWarmer] Pre-loading product catalogue into Redis

[ReportStarter] Options: [generate-report] | Files: [input.csv]
[ReportStarter] Generating startup report...

=== ApplicationReadyEvent published — app is live ===
```

## 6. Walkthrough

- `DataLoader` is `@Order(1)` — it runs first and loads seed data before other runners or traffic.
- `CacheWarmer` is `@Order(2)` — it populates the cache after seed data exists.
- `ReportStarter` implements `ApplicationRunner` and receives parsed arguments. It checks for the `--generate-report` option flag and acts accordingly — more ergonomic than parsing `String[]`.
- All three run before `ApplicationReadyEvent`, so any thrown exception prevents the app from declaring readiness — a startup failure rather than a silent runtime problem.
- In real Spring Boot, discovery is automatic: any bean implementing either interface has its `run()` called. The simulation manually lists and calls them in order.

## 7. Gotchas & takeaways

> If a `CommandLineRunner` or `ApplicationRunner` throws, the application exits with `SpringApplication.exit()` returning code `1`. This is intentional — broken startup tasks should not leave the app in a half-initialised state serving traffic. Wrap retryable failures in try/catch and handle recovery explicitly.

> In `@SpringBootTest` integration tests, all runners execute by default, including `DataLoader`. This can slow tests or corrupt test data. Mock or exclude runners you don't need in tests: `@MockBean DataLoader dataLoader;`

- `CommandLineRunner` is simpler; `ApplicationRunner` is richer — choose based on whether you need structured argument access.
- Use `@Order` to sequence dependent runners (seed data before cache warm-up).
- Both interfaces are interchangeable for most use cases; Spring Boot handles them identically except for the argument type.
- Multiple runners are common in real apps — one per concern (migration, seeding, warm-up, verification).
- Runners are not re-executed on `@RefreshScope` refresh events — they are one-shot startup hooks.
