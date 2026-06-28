---
card: spring-boot
gi: 57
slug: application-exit-exit-codes-exitcodegenerator
title: Application exit & exit codes (ExitCodeGenerator)
---

## 1. What it is

**Exit codes** are integers returned by a process to the operating system when it terminates. `0` means success; anything else means failure. Spring Boot provides `SpringApplication.exit()` and the `ExitCodeGenerator` interface to control which exit code the JVM returns.

```java
@SpringBootApplication
public class MyApp {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(MyApp.class);
        System.exit(SpringApplication.exit(app.run(args)));
    }
}
```

`SpringApplication.exit(ConfigurableApplicationContext, ExitCodeGenerator...)` collects exit codes from all registered `ExitCodeGenerator` beans and returns the first non-zero code, or `0` if all return `0`.

Implement `ExitCodeGenerator` to provide a custom exit code:
```java
@Component
public class BatchJobExitCodeGenerator implements ExitCodeGenerator {
    @Override
    public int getExitCode() { return jobFailed ? 1 : 0; }
}
```

## 2. Why & when

Exit codes matter in automation: shell scripts, CI/CD pipelines, and process supervisors all check the exit code to decide whether to continue, retry, or alert.

Use exit codes when:
- Writing batch jobs where failure must be visible to the orchestrator (`exit code != 0` fails a CI step).
- Running Spring Boot in a container where the restart policy depends on exit code.
- Providing distinct exit codes for different error categories (e.g. `1` = missing config, `2` = data validation failure, `3` = external service down).
- Hooking into `ExitCodeEvent` for structured logging of why the app exited.

## 3. Core concept

Think of exit codes as the **final report card** the app hands to whoever ran it. A parent process (CI server, shell script, container runtime) reads this code to decide what to do next. Spring Boot automates exit code collection so individual components can each vote on the exit status.

The exit code resolution flow:

1. `System.exit(SpringApplication.exit(context))` triggers context close.
2. Spring Boot calls `context.close()`, which fires `ContextClosedEvent`.
3. All beans implementing `ExitCodeGenerator` have their `getExitCode()` called.
4. All beans implementing `ExitCodeExceptionMapper` have a chance to translate exceptions to codes.
5. Spring Boot takes the **highest** non-zero code (or `0` if all return `0`).
6. The JVM exits with that code.

Special case: if a `CommandLineRunner` or `ApplicationRunner` throws an `ExitCodeGeneratingException`, the exception itself carries the exit code without needing a separate `ExitCodeGenerator` bean.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Exit code collection from ExitCodeGenerator beans and ExitCodeExceptionMapper into System.exit">
  <!-- Runners -->
  <rect x="20" y="20" width="200" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="42" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">BatchJobRunner</text>
  <text x="120" y="58" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">throws ExitCodeException(2)</text>

  <rect x="20" y="80" width="200" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="102" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">ExitCodeGenerator bean</text>
  <text x="120" y="118" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">getExitCode() → 1</text>

  <rect x="20" y="140" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="162" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">AnotherGenerator bean</text>
  <text x="120" y="178" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">getExitCode() → 0</text>

  <!-- Collector -->
  <rect x="280" y="80" width="160" height="60" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="360" y="104" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">SpringApplication</text>
  <text x="360" y="122" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">.exit(context)</text>

  <!-- Result -->
  <rect x="510" y="90" width="130" height="40" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="575" y="115" fill="#e6edf3" font-size="12" font-family="monospace" text-anchor="middle">System.exit(2)</text>

  <!-- Arrows -->
  <line x1="220" y1="45" x2="278" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ec)"/>
  <line x1="220" y1="105" x2="278" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ec)"/>
  <line x1="220" y1="165" x2="278" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ec)"/>
  <line x1="440" y1="110" x2="508" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#ec)"/>
  <text x="474" y="102" fill="#6db33f" font-size="10" font-family="sans-serif" text-anchor="middle">max(2,1,0)=2</text>

  <defs>
    <marker id="ec" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`SpringApplication.exit()` collects exit codes from all generators, takes the highest non-zero value, and returns it to `System.exit()`.

## 5. Runnable example

```java
// ExitCodeDemo.java
// How to run: java ExitCodeDemo.java  (JDK 17+)
// Simulates ExitCodeGenerator bean collection and System.exit() resolution.

import java.util.*;

public class ExitCodeDemo {

    // ── ExitCodeGenerator interface ───────────────────────────────
    interface ExitCodeGenerator { int getExitCode(); }

    // ── Simulated beans ───────────────────────────────────────────
    static class ValidationFailureGenerator implements ExitCodeGenerator {
        private final boolean failed;
        ValidationFailureGenerator(boolean failed) { this.failed = failed; }
        @Override public int getExitCode() { return failed ? 1 : 0; }
    }

    static class DataNotFoundGenerator implements ExitCodeGenerator {
        private final boolean notFound;
        DataNotFoundGenerator(boolean notFound) { this.notFound = notFound; }
        @Override public int getExitCode() { return notFound ? 2 : 0; }
    }

    static class ExternalServiceDownGenerator implements ExitCodeGenerator {
        private final boolean serviceDown;
        ExternalServiceDownGenerator(boolean serviceDown) { this.serviceDown = serviceDown; }
        @Override public int getExitCode() { return serviceDown ? 3 : 0; }
    }

    // ── SpringApplication.exit() simulation ───────────────────────
    static int collectExitCode(List<ExitCodeGenerator> generators) {
        return generators.stream()
            .mapToInt(ExitCodeGenerator::getExitCode)
            .max()
            .orElse(0);
    }

    public static void main(String[] args) {
        System.out.println("=== Exit code scenarios ===\n");

        // Scenario 1: all OK
        List<ExitCodeGenerator> scenario1 = List.of(
            new ValidationFailureGenerator(false),
            new DataNotFoundGenerator(false),
            new ExternalServiceDownGenerator(false)
        );
        runScenario("All OK", scenario1);

        // Scenario 2: validation failed only
        List<ExitCodeGenerator> scenario2 = List.of(
            new ValidationFailureGenerator(true),
            new DataNotFoundGenerator(false),
            new ExternalServiceDownGenerator(false)
        );
        runScenario("Validation failure", scenario2);

        // Scenario 3: multiple failures — highest code wins
        List<ExitCodeGenerator> scenario3 = List.of(
            new ValidationFailureGenerator(true),   // 1
            new DataNotFoundGenerator(true),         // 2
            new ExternalServiceDownGenerator(true)   // 3
        );
        runScenario("Multiple failures (max code)", scenario3);
    }

    static void runScenario(String name, List<ExitCodeGenerator> generators) {
        System.out.println("--- " + name + " ---");
        generators.forEach(g ->
            System.out.println("  " + g.getClass().getSimpleName() + ".getExitCode() → " + g.getExitCode()));
        int code = collectExitCode(generators);
        System.out.println("  System.exit(" + code + ")  → " + (code == 0 ? "✅ success" : "❌ failure"));
        System.out.println();
    }
}
```

**How to run:** `java ExitCodeDemo.java`

Expected output:
```
=== Exit code scenarios ===

--- All OK ---
  ValidationFailureGenerator.getExitCode() → 0
  DataNotFoundGenerator.getExitCode() → 0
  ExternalServiceDownGenerator.getExitCode() → 0
  System.exit(0)  → ✅ success

--- Validation failure ---
  ValidationFailureGenerator.getExitCode() → 1
  DataNotFoundGenerator.getExitCode() → 0
  ExternalServiceDownGenerator.getExitCode() → 0
  System.exit(1)  → ❌ failure

--- Multiple failures (max code) ---
  ValidationFailureGenerator.getExitCode() → 1
  DataNotFoundGenerator.getExitCode() → 2
  ExternalServiceDownGenerator.getExitCode() → 3
  System.exit(3)  → ❌ failure
```

## 6. Walkthrough

- Each `ExitCodeGenerator` bean returns `0` for success and a non-zero code for a specific failure category. This lets the caller know exactly what went wrong from the exit code alone.
- `collectExitCode()` takes the maximum value across all generators — mirroring Spring Boot's selection strategy. The highest code propagates.
- Scenario 1: all generators return `0` → `System.exit(0)` → CI pipeline passes.
- Scenario 2: one generator returns `1` → `System.exit(1)` → CI pipeline fails with "validation error" signal.
- Scenario 3: three generators each signal a different failure; code `3` (external service down) is the highest and is returned. Operators can look up what code `3` means in your service's runbook.

## 7. Gotchas & takeaways

> `SpringApplication.exit()` must be called explicitly — it does not happen automatically when `main()` returns. The standard pattern is `System.exit(SpringApplication.exit(SpringApplication.run(MyApp.class, args)))`. Omitting `System.exit()` means the exit code is always `0` regardless of failures.

> `ExitCodeGenerator.getExitCode()` is called during context close, after all `DisposableBean.destroy()` and `@PreDestroy` methods run. If a destroy method throws, the exit code may still be collected correctly — but test this in your specific scenario.

- Convention: exit code `0` = success, `1` = general error, `2`+ = domain-specific error categories. Document your exit codes.
- `ExitCodeExceptionMapper` lets you map specific exception types to exit codes — useful when exceptions propagate out of runners.
- In Kubernetes: use `restartPolicy: OnFailure` on batch Job pods so the Job retries only on non-zero exit codes.
- `ExitCodeEvent` is published before `System.exit()` — listen for it to log the exit code to a structured log or metrics system.
- For long-running services (web apps), exit codes are less important than health probes. Batch jobs and CLI tools are the primary users of this feature.
