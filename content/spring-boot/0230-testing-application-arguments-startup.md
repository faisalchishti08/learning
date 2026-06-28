---
card: spring-boot
gi: 230
slug: testing-application-arguments-startup
title: Testing application arguments & startup
---

## 1. What it is

Spring Boot exposes command-line arguments as an `ApplicationArguments` bean and lets components implement `ApplicationRunner` or `CommandLineRunner` to execute logic at startup. Testing this means verifying that your runners fire correctly, receive the right arguments, and produce the expected side effects — all without launching a real JVM process.

## 2. Why & when

CLI-style Spring Boot apps (batch jobs, data importers, migration tools) depend heavily on startup argument parsing and runner logic. Testing `ApplicationRunner` ensures the initialization sequence is correct. If a runner throws an exception the whole app fails to start, so testing startup is critical for reliability.

## 3. Core concept

- `ApplicationArguments` — wraps raw `String[]` args; distinguishes option args (`--foo=bar`) from non-option args.
- `ApplicationRunner` — `run(ApplicationArguments args)` fires after context is fully refreshed.
- `CommandLineRunner` — `run(String... args)` fires at the same point with raw strings.

In tests, `@SpringBootTest(args = {"--mode=import", "file.csv"})` passes arguments to the context. Spring creates a real `ApplicationArguments` bean from them and invokes all runners. You can also override runners with `@MockBean` to verify they were called, or use a `@TestConfiguration` stub to capture side effects.

## 4. Diagram

<svg viewBox="0 0 620 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="620" height="280" fill="#1c2430" rx="10"/>
  <!-- Test class -->
  <rect x="20" y="50" width="190" height="70" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="76" text-anchor="middle" fill="#6db33f" font-size="12">@SpringBootTest</text>
  <text x="115" y="96" text-anchor="middle" fill="#8b949e" font-size="11">args = {"--mode=import",</text>
  <text x="115" y="113" text-anchor="middle" fill="#8b949e" font-size="11">        "file.csv"}</text>
  <!-- ApplicationArguments -->
  <rect x="260" y="40" width="180" height="50" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="62" text-anchor="middle" fill="#79c0ff">ApplicationArguments</text>
  <text x="350" y="80" text-anchor="middle" fill="#8b949e" font-size="11">option args + non-option args</text>
  <!-- Runners -->
  <rect x="260" y="120" width="180" height="50" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="143" text-anchor="middle" fill="#6db33f">ApplicationRunner</text>
  <text x="350" y="161" text-anchor="middle" fill="#8b949e" font-size="11">run() called post-refresh</text>
  <!-- Side effects -->
  <rect x="480" y="120" width="120" height="50" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="143" text-anchor="middle" fill="#e6edf3">Side effects</text>
  <text x="540" y="161" text-anchor="middle" fill="#8b949e" font-size="11">DB writes, files</text>
  <!-- arrows -->
  <line x1="210" y1="85" x2="258" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a5)"/>
  <line x1="210" y1="95" x2="258" y2="140" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a5)"/>
  <line x1="440" y1="145" x2="478" y2="145" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a5)"/>
  <!-- Verify label -->
  <rect x="370" y="210" width="220" height="40" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="1"/>
  <text x="480" y="235" text-anchor="middle" fill="#6db33f" font-size="12">Assert side effects in @Test method</text>
  <line x1="540" y1="170" x2="510" y2="208" stroke="#6db33f" stroke-width="1" stroke-dasharray="4 3"/>
  <defs>
    <marker id="a5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_`@SpringBootTest(args=...)` feeds arguments into a real `ApplicationArguments` bean and fires runners._

## 5. Runnable example

```java
// File: ApplicationStartupTest.java
// How to run: place in a Spring Boot 3.x project test source root;
// run: ./mvnw test -Dtest=ApplicationStartupTest

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

// ---- Minimal ApplicationRunner to test ----
// (In a real project this lives in src/main/java)
// @Component
// class ImportRunner implements ApplicationRunner { ... }

// ---- Test ----
@SpringBootTest(
    args = {"--mode=import", "file.csv"},
    // Disable web server; this is a CLI app
    webEnvironment = SpringBootTest.WebEnvironment.NONE
)
class ApplicationStartupTest {

    // Capture runner output via a shared list (test-only bean)
    @TestConfiguration
    static class TestRunnerConfig {
        static final List<String> recorded = new ArrayList<>();

        @Bean
        ApplicationRunner capturingRunner() {
            return args -> {
                recorded.add("mode=" + args.getOptionValues("mode"));
                recorded.add("nonOption=" + args.getNonOptionArgs());
            };
        }
    }

    @Autowired
    ApplicationArguments appArgs;

    @Test
    void optionArgParsed() {
        assertThat(appArgs.getOptionValues("mode"))
            .containsExactly("import");
    }

    @Test
    void nonOptionArgParsed() {
        assertThat(appArgs.getNonOptionArgs())
            .containsExactly("file.csv");
    }

    @Test
    void runnerFiredWithArgs() {
        assertThat(TestRunnerConfig.recorded)
            .anyMatch(s -> s.contains("import"))
            .anyMatch(s -> s.contains("file.csv"));
    }
}
```

**How to run:** `./mvnw test -Dtest=ApplicationStartupTest`. Three tests verify argument parsing and runner invocation.

## 6. Walkthrough

1. `@SpringBootTest(args = {"--mode=import", "file.csv"})` — Boot creates a `DefaultApplicationArguments` bean from the array. Option args start with `--`; the rest are non-option args.
2. `webEnvironment = NONE` — CLI apps don't need a web server; this skips Tomcat startup, making tests faster.
3. `TestRunnerConfig` is a nested `@TestConfiguration` — it registers a `capturingRunner` bean that records what it receives into a `static List`.
4. `appArgs.getOptionValues("mode")` — parses `--mode=import` and returns `["import"]`.
5. `appArgs.getNonOptionArgs()` — returns `["file.csv"]` (no `--` prefix).
6. `runnerFiredWithArgs()` — asserts the runner ran and received the expected values by inspecting the captured list.

## 7. Gotchas & takeaways

> `@SpringBootTest(args = {...})` fires **all** `ApplicationRunner` and `CommandLineRunner` beans in the context. If your production runner has destructive side effects (file deletion, data migration), use `@MockBean` to stub it out and only test the real runner you care about.

> Order matters: multiple runners execute in `@Order` order. Tests verifying runner-triggered state should account for all runners in the context.

> `ApplicationArguments.getOptionValues("key")` returns `null` if the option is absent — not an empty list. Check for `containsOption("key")` before calling `getOptionValues`.

- Use `webEnvironment = NONE` for CLI app tests — avoids loading HTTP stack for no reason.
- `@MockBean ApplicationRunner myRunner` to isolate a single runner and `verify(myRunner).run(any())` with Mockito.
- Combine `@SpringBootTest(args=...)` with `@ActiveProfiles("test")` to use a test property source alongside real args.
- Test startup failure scenarios by providing args that should trigger a validation exception and asserting the context fails to load.
