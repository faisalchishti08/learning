---
card: spring-boot
gi: 47
slug: startup-failure-analysis-failureanalyzer
title: Startup failure analysis (FailureAnalyzer)
---

## 1. What it is

A **`FailureAnalyzer`** is a Spring Boot interface that converts an exception thrown during application startup into a human-readable failure message with an **action** (what to do to fix it). Spring Boot ships with several built-in `FailureAnalyzer` implementations; you can write your own for custom exceptions from your own libraries.

When startup fails, instead of a raw stack trace, Spring Boot prints a focused message:

```
***************************
APPLICATION FAILED TO START
***************************

Description:

Web server failed to start. Port 8080 was already in use.

Action:

Identify and stop the process that's listening on port 8080 or configure
this application to listen on another port.
```

The interface:
```java
public interface FailureAnalyzer {
    FailureAnalysis analyze(Throwable failure);
}
```

`FailureAnalysis` holds a description string and an action string. `null` return means this analyzer doesn't handle the exception; Spring Boot tries the next analyzer.

## 2. Why & when

A raw `java.net.BindException: Address already in use` buried inside a 50-line stack trace tells experienced developers what happened but is opaque to everyone else. A `FailureAnalyzer` surfaces the root cause and prescribes the fix without requiring the reader to understand the stack trace.

Write a custom `FailureAnalyzer` when:
- Your library or auto-configuration can throw recognisable exceptions during startup (missing required property, invalid configuration value, missing resource file).
- You want users of your library to get actionable messages instead of generic Java exceptions.
- You are building a platform and want consistent startup error messaging across services.

Do not write one for exceptions that are already handled by Spring Boot's built-in analyzers (port-in-use, missing required bean, ambiguous bean, JPA schema validation failure, etc.).

## 3. Core concept

Analogy: a `FailureAnalyzer` is the **mechanic's error code reader** for a car. When the check-engine light comes on (startup exception), you plug in the reader (the analyzer chain). Each analyzer checks if it recognises the fault code (the exception type). The first one that matches gives you a plain-English message ("replace the oxygen sensor") instead of raw hex codes (stack trace).

The mechanism:
1. Spring Boot wraps the startup exception and iterates through all registered `FailureAnalyzer`s (loaded from `META-INF/spring.factories` under the key `org.springframework.boot.diagnostics.FailureAnalyzer`).
2. The first analyzer that returns a non-null `FailureAnalysis` wins.
3. `FailureAnalysisReporter` formats and prints the description and action.
4. The JVM exits (or rethrows for programmatic callers).

`AbstractFailureAnalyzer<T extends Throwable>` is a convenient base class that automatically checks the exception type:
```java
public class MyConfigFailureAnalyzer extends AbstractFailureAnalyzer<MyConfigException> {
    @Override
    protected FailureAnalysis analyze(Throwable rootFailure, MyConfigException cause) {
        return new FailureAnalysis(
            "mylib.api-key is required but missing.",
            "Add mylib.api-key=<your-key> to application.properties.",
            cause);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FailureAnalyzer chain processing a startup exception into a human-readable message">
  <!-- Exception -->
  <rect x="20" y="20" width="200" height="50" rx="6" fill="#3d2020" stroke="#f85149" stroke-width="2"/>
  <text x="120" y="42" fill="#f85149" font-size="11" font-family="monospace" text-anchor="middle">Startup Exception</text>
  <text x="120" y="60" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">BindException / MissingBean…</text>

  <!-- Analyzer chain -->
  <line x1="220" y1="45" x2="258" y2="45" stroke="#f85149" stroke-width="2" marker-end="url(#fa)"/>

  <rect x="260" y="20" width="120" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="44" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">PortInUse</text>
  <text x="320" y="60" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">Analyzer ❌</text>

  <line x1="380" y1="45" x2="418" y2="45" stroke="#8b949e" stroke-width="1.5" marker-end="url(#fa)"/>

  <rect x="420" y="20" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="480" y="44" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">NoSuchBean</text>
  <text x="480" y="60" fill="#6db33f" font-size="10" font-family="monospace" text-anchor="middle">Analyzer ✅</text>

  <!-- Output -->
  <rect x="200" y="130" width="380" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="390" y="156" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">APPLICATION FAILED TO START</text>
  <text x="210" y="180" fill="#e6edf3" font-size="10" font-family="monospace">Description:</text>
  <text x="210" y="198" fill="#8b949e" font-size="10" font-family="monospace">Field 'repo' required a bean of type 'UserRepo'.</text>
  <text x="210" y="216" fill="#e6edf3" font-size="10" font-family="monospace">Action: Consider defining a bean of type 'UserRepo'.</text>

  <!-- Arrow from analyzer to output -->
  <line x1="480" y1="70" x2="390" y2="128" stroke="#6db33f" stroke-width="2" marker-end="url(#fa)"/>

  <defs>
    <marker id="fa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Each analyzer in the chain tries to handle the exception; the first match formats a human-readable description and action.

## 5. Runnable example

```java
// FailureAnalyzerDemo.java
// How to run: java FailureAnalyzerDemo.java  (JDK 17+)
// Simulates the FailureAnalyzer chain pattern:
// a chain of analyzers processes a startup exception until one handles it.

import java.util.*;

// ── domain: startup exception from a custom library ──────────────
class MissingApiKeyException extends RuntimeException {
    MissingApiKeyException(String propertyName) {
        super("Required property '" + propertyName + "' is missing.");
    }
}

// ── FailureAnalysis: description + action ─────────────────────────
record FailureAnalysis(String description, String action, Throwable cause) {}

// ── FailureAnalyzer interface ────────────────────────────────────
interface FailureAnalyzer {
    FailureAnalysis analyze(Throwable failure);
}

// ── Built-in Spring Boot analyzer (port in use) ───────────────────
class PortInUseFailureAnalyzer implements FailureAnalyzer {
    @Override public FailureAnalysis analyze(Throwable failure) {
        if (!(failure instanceof IllegalArgumentException)) return null;
        if (!failure.getMessage().contains("port")) return null;
        return new FailureAnalysis(
            "Web server failed to start. Port 8080 is already in use.",
            "Identify and stop the process listening on port 8080, or set server.port.",
            failure);
    }
}

// ── Custom FailureAnalyzer (from our library) ─────────────────────
class MissingApiKeyFailureAnalyzer implements FailureAnalyzer {
    @Override public FailureAnalysis analyze(Throwable failure) {
        Throwable cause = failure;
        while (cause != null && !(cause instanceof MissingApiKeyException))
            cause = cause.getCause();
        if (cause == null) return null;
        return new FailureAnalysis(
            cause.getMessage(),
            "Add the property to your application.properties or as an environment variable.",
            cause);
    }
}

public class FailureAnalyzerDemo {

    // Registered via META-INF/spring.factories in a real Spring Boot app
    static List<FailureAnalyzer> analyzers = List.of(
        new PortInUseFailureAnalyzer(),
        new MissingApiKeyFailureAnalyzer()
    );

    public static void main(String[] args) {
        System.out.println("=== FailureAnalyzer chain demo ===\n");

        // Scenario 1: port-in-use exception
        System.out.println("--- Scenario 1: port conflict ---");
        process(new IllegalArgumentException("Address already in use on port 8080"));

        System.out.println();

        // Scenario 2: custom library exception (wrapped)
        System.out.println("--- Scenario 2: missing API key ---");
        Exception wrapped = new RuntimeException("Application context refresh failed",
            new MissingApiKeyException("acme.api-key"));
        process(wrapped);

        System.out.println();

        // Scenario 3: unrecognised exception — no analyzer handles it
        System.out.println("--- Scenario 3: unrecognised exception ---");
        process(new NullPointerException("Something internal blew up"));
    }

    static void process(Throwable failure) {
        FailureAnalysis result = null;
        for (FailureAnalyzer analyzer : analyzers) {
            result = analyzer.analyze(failure);
            if (result != null) break;
        }

        if (result != null) {
            System.out.println("***************************");
            System.out.println("APPLICATION FAILED TO START");
            System.out.println("***************************");
            System.out.println("\nDescription:\n  " + result.description());
            System.out.println("\nAction:\n  " + result.action() + "\n");
        } else {
            System.out.println("No FailureAnalyzer handled this exception.");
            System.out.println("Raw exception: " + failure);
        }
    }
}
```

**How to run:** `java FailureAnalyzerDemo.java`

Expected output:
```
=== FailureAnalyzer chain demo ===

--- Scenario 1: port conflict ---
***************************
APPLICATION FAILED TO START
***************************

Description:
  Web server failed to start. Port 8080 is already in use.

Action:
  Identify and stop the process listening on port 8080, or set server.port.

--- Scenario 2: missing API key ---
***************************
APPLICATION FAILED TO START
***************************

Description:
  Required property 'acme.api-key' is missing.

Action:
  Add the property to your application.properties or as an environment variable.

--- Scenario 3: unrecognised exception ---
No FailureAnalyzer handled this exception.
Raw exception: java.lang.NullPointerException: Something internal blew up
```

## 6. Walkthrough

- `analyzers` is the chain; in real Spring Boot it is loaded from `META-INF/spring.factories` under `org.springframework.boot.diagnostics.FailureAnalyzer`.
- `process()` iterates the chain and stops at the first non-null result — identical to `FailureAnalysisReporters`'s loop.
- Scenario 1: `PortInUseFailureAnalyzer` recognises the `IllegalArgumentException` with "port" in the message and returns a `FailureAnalysis`.
- Scenario 2: `MissingApiKeyFailureAnalyzer` walks the cause chain (using a while loop) to find the `MissingApiKeyException` buried inside the wrapper exception. This mirrors `AbstractFailureAnalyzer`'s `findCause()` utility.
- Scenario 3: neither analyzer handles `NullPointerException` — both return `null`. Spring Boot would then fall back to printing the raw stack trace.

## 7. Gotchas & takeaways

> `FailureAnalyzer`s must be registered in `META-INF/spring.factories` (or `META-INF/spring/org.springframework.boot.diagnostics.FailureAnalyzer.imports` in Spring Boot 3.x) — they are loaded before the `ApplicationContext` exists, so Spring cannot discover them via component scanning.

> `FailureAnalyzer.analyze()` must **not** throw. If your analyzer itself throws, Spring Boot catches the exception, logs a warning, and falls back to the raw stack trace. Always guard for null and handle unexpected exception types gracefully.

- Extend `AbstractFailureAnalyzer<MyException>` rather than implementing `FailureAnalyzer` directly — it handles the cause-chain walk and type checking for you.
- The `FailureAnalysis` constructor takes three arguments: description (what went wrong), action (what to do), and the cause exception (logged separately as a debug stack trace).
- Spring Boot's built-in analyzers cover: port conflict, missing required bean, ambiguous bean, JPA schema validation failure, Liquibase migration failure, and more.
- Writing a `FailureAnalyzer` for your library is a sign of polish — it distinguishes library-quality code from application code.
- Test your analyzer with `SpringApplication.run()` in a test and assert the exit message, or call `analyze()` directly with a crafted exception.
