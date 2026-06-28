---
card: spring-boot
gi: 229
slug: testconfiguration-vs-import
title: "@TestConfiguration vs @Import"
---

## 1. What it is

`@TestConfiguration` marks a class as a supplementary configuration that adds or overrides beans only in tests — it is never picked up by component scanning in the main application. `@Import` (from core Spring) pulls any `@Configuration` class or bean into the current context explicitly. Together they give you precise control over which beans a test context contains.

## 2. Why & when

Sometimes you want a fake clock, a stub email sender, or a special `ObjectMapper` only in tests. Putting those beans in main configuration pollutes production builds. `@TestConfiguration` is the right home: it exists in `src/test/` and is invisible to the production context. Use `@Import` when you need to pull in a specific configuration class without relying on component scanning.

## 3. Core concept

| | `@TestConfiguration` | `@Import` |
|---|---|---|
| Scope | Test source root only | Any context |
| How to activate | Nest inside test class, or `@Import` it explicitly | Annotate the test class |
| Component scan? | Excluded from main scan | N/A — explicit |
| Replaces beans? | Can override existing beans | Adds/merges |

When `@TestConfiguration` is nested inside a test class, Spring uses it automatically. When it lives in a separate file (e.g., `TestEmailConfig.java`), you must `@Import(TestEmailConfig.class)` on the test class to activate it.

Both annotations work with `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`, and any slice test.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="280" fill="#1c2430" rx="10"/>
  <!-- main src -->
  <rect x="20" y="40" width="200" height="80" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="68" text-anchor="middle" fill="#8b949e">src/main/java</text>
  <rect x="35" y="80" width="170" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="120" y="101" text-anchor="middle" fill="#e6edf3" font-size="12">AppConfig (@Configuration)</text>
  <!-- test src -->
  <rect x="20" y="150" width="200" height="100" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="120" y="174" text-anchor="middle" fill="#6db33f">src/test/java</text>
  <rect x="35" y="185" width="170" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="206" text-anchor="middle" fill="#6db33f" font-size="12">@TestConfiguration</text>
  <text x="120" y="222" text-anchor="middle" fill="#8b949e" font-size="11">TestEmailConfig.java</text>
  <!-- Test context -->
  <rect x="280" y="70" width="200" height="140" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="380" y="100" text-anchor="middle" fill="#79c0ff">Test Context</text>
  <rect x="295" y="112" width="170" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="380" y="133" text-anchor="middle" fill="#e6edf3" font-size="12">AppConfig beans</text>
  <rect x="295" y="150" width="170" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="171" text-anchor="middle" fill="#6db33f" font-size="12">TestEmailConfig beans</text>
  <!-- @Import label -->
  <rect x="500" y="130" width="120" height="40" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="560" y="155" text-anchor="middle" fill="#79c0ff">@Import</text>
  <!-- arrows -->
  <line x1="220" y1="115" x2="278" y2="135" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a4)"/>
  <line x1="220" y1="220" x2="278" y2="175" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a4)"/>
  <line x1="500" y1="150" x2="465" y2="162" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a4)"/>
  <text x="490" y="118" text-anchor="middle" fill="#8b949e" font-size="11">activates</text>
  <defs>
    <marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_`@TestConfiguration` lives in test sources and merges into the test context via `@Import` or nesting._

## 5. Runnable example

```java
// File: TestConfigVsImportTest.java
// How to run: place in a Spring Boot 3.x project's test source root;
// run: ./mvnw test -Dtest=TestConfigVsImportTest

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.assertj.core.api.Assertions.assertThat;

// ---- Standalone TestConfiguration (lives in its own file in reality) ----
@TestConfiguration   // invisible to main app component scan
class FixedClockConfig {
    @Bean
    Clock fixedClock() {
        // Fixed to 2024-01-01T00:00:00Z for deterministic tests
        return Clock.fixed(Instant.parse("2024-01-01T00:00:00Z"), ZoneOffset.UTC);
    }
}

// ---- Test class ----
@SpringBootTest
@Import(FixedClockConfig.class)  // pull in the test-only bean explicitly
class TestConfigVsImportTest {

    @Autowired
    Clock clock;

    // ----- Alternative: nested @TestConfiguration is auto-applied -----
    @TestConfiguration
    static class LocalOverrides {
        // Adds a second bean directly inside the test class
        @Bean(name = "labelBean")
        String label() { return "test-label"; }
    }

    @Autowired(required = false)
    String labelBean;

    @Test
    void fixedClockInjected() {
        // The bean from FixedClockConfig is active because of @Import
        assertThat(clock.instant()).isEqualTo(Instant.parse("2024-01-01T00:00:00Z"));
    }

    @Test
    void nestedTestConfigurationAppliedAutomatically() {
        // Nested @TestConfiguration is picked up without @Import
        assertThat(labelBean).isEqualTo("test-label");
    }
}
```

**How to run:** `./mvnw test -Dtest=TestConfigVsImportTest`. Both tests should pass; the `fixedClock` and `labelBean` beans are test-only.

## 6. Walkthrough

1. `FixedClockConfig` is annotated with `@TestConfiguration` — it lives in `src/test/java` and is excluded from the main component scan so it never reaches production.
2. `@Import(FixedClockConfig.class)` on the test class tells the test context to include the beans defined there. Spring merges them on top of beans from `@SpringBootTest`.
3. `fixedClock()` returns a `Clock` fixed at 2024-01-01. Because this overrides any `Clock` bean that might be in the production context, date-sensitive logic is deterministic in tests.
4. `LocalOverrides` is a nested `static` class annotated `@TestConfiguration` — Spring detects it automatically when it is an inner class of the test. No `@Import` needed.
5. `labelBean` is injected from `LocalOverrides.label()`. The `required = false` guard handles cases where this pattern is used in an isolated unit test slice.

## 7. Gotchas & takeaways

> `@TestConfiguration` on a **top-level** class is NOT auto-applied — you must `@Import` it. Only **nested** `@TestConfiguration` classes inside a test class are applied automatically.

> `@TestConfiguration` does not replace beans by default. To override an existing bean, add `@Bean` plus set the bean name to match the production bean's name, and enable `spring.main.allow-bean-definition-overriding=true` in `application-test.properties`.

> Avoid placing `@TestConfiguration` classes in packages that your main `@ComponentScan` covers — even with the annotation, some setups may still pick them up.

- Use `@TestConfiguration` (not `@Configuration`) for any bean that should never appear in production.
- Prefer nested `@TestConfiguration` for per-test customizations; a standalone file with `@Import` for reusable test infrastructure (fixed clocks, stub services).
- `@Import` also works for regular `@Configuration` classes — handy for pulling in infrastructure config shared across test suites.
- Combine `@TestConfiguration` with `@MockBean` when you want some real beans and some fakes in the same test context.
