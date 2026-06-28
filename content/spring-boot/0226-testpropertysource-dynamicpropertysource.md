---
card: spring-boot
gi: 226
slug: testpropertysource-dynamicpropertysource
title: "@TestPropertySource & @DynamicPropertySource"
---

## 1. What it is

`@TestPropertySource` lets you override application properties in a test with static values from a `.properties` file or inline key-value pairs. `@DynamicPropertySource` is the dynamic counterpart: a static method annotated with it runs before context creation and registers property values that aren't known until runtime — for example, the port assigned by a Docker container.

## 2. Why & when

Tests often need a different database URL, feature flag, or timeout than production. Hard-coding these inside the test is fragile. `@TestPropertySource` is ideal for simple, known overrides. `@DynamicPropertySource` is essential when the value is generated at runtime — container ports, random credentials, or any infrastructure spun up in a `@BeforeAll`-style hook.

## 3. Core concept

Spring's `Environment` is assembled from a layered stack of `PropertySource` objects. Test annotations add extra layers at the top, so test properties override everything below them.

- `@TestPropertySource(properties = "my.key=value")` — inserts a `MapPropertySource` near the top of the stack before context startup.
- `@DynamicPropertySource` — a `static void` method receives a `DynamicPropertyRegistry`; call `registry.add("key", supplier)` to lazily register values evaluated just before the context is refreshed.

## 4. Diagram

<svg viewBox="0 0 620 320" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="620" height="320" fill="#1c2430" rx="10"/>
  <!-- Property stack -->
  <text x="310" y="28" text-anchor="middle" fill="#8b949e" font-size="12">Spring Environment — PropertySource stack (top wins)</text>
  <!-- layers -->
  <rect x="120" y="40" width="380" height="38" rx="5" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="65" text-anchor="middle" fill="#6db33f">@DynamicPropertySource  (runtime values, e.g. container port)</text>
  <rect x="120" y="86" width="380" height="38" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="111" text-anchor="middle" fill="#79c0ff">@TestPropertySource / inline properties</text>
  <rect x="120" y="132" width="380" height="38" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="310" y="157" text-anchor="middle" fill="#8b949e">application-test.properties / yml</text>
  <rect x="120" y="178" width="380" height="38" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="310" y="203" text-anchor="middle" fill="#8b949e">application.properties / yml</text>
  <rect x="120" y="224" width="380" height="38" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="310" y="249" text-anchor="middle" fill="#8b949e">System / OS environment</text>
  <!-- arrows showing resolution order -->
  <text x="40" y="65" text-anchor="middle" fill="#6db33f" font-size="20">1</text>
  <text x="40" y="111" text-anchor="middle" fill="#79c0ff" font-size="20">2</text>
  <text x="40" y="157" text-anchor="middle" fill="#8b949e" font-size="20">3</text>
  <text x="40" y="203" text-anchor="middle" fill="#8b949e" font-size="20">4</text>
  <text x="40" y="249" text-anchor="middle" fill="#8b949e" font-size="20">5</text>
  <text x="310" y="295" text-anchor="middle" fill="#8b949e" font-size="12">Higher layers shadow lower ones</text>
</svg>

_Test property sources sit at the top of Spring's `Environment` stack, shadowing all app defaults._

## 5. Runnable example

```java
// File: PropertySourceDemoTest.java
// How to run: place inside a Spring Boot 3.x project's test source root;
// run: ./mvnw test -Dtest=PropertySourceDemoTest

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.TestPropertySource;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
// Override a static property — useful for known values
@TestPropertySource(properties = {
    "app.feature.enabled=true",
    "app.timeout=30"
})
class PropertySourceDemoTest {

    @Value("${app.feature.enabled}")
    boolean featureEnabled;

    @Value("${app.timeout}")
    int timeout;

    @Value("${app.db.url}")
    String dbUrl;

    // DynamicPropertySource: runs before context creation
    // Simulates a container assigning a random port at runtime
    @DynamicPropertySource
    static void registerDynamicProps(DynamicPropertyRegistry registry) {
        int simulatedContainerPort = 54321; // in real use: container.getMappedPort(5432)
        registry.add("app.db.url",
                     () -> "jdbc:postgresql://localhost:" + simulatedContainerPort + "/testdb");
    }

    @Test
    void staticPropertiesOverrideDefaults() {
        assertThat(featureEnabled).isTrue();
        assertThat(timeout).isEqualTo(30);
    }

    @Test
    void dynamicPropertyInjected() {
        assertThat(dbUrl).startsWith("jdbc:postgresql://localhost:54321");
    }
}
```

**How to run:** Add to a Spring Boot 3.x test source root and run `./mvnw test -Dtest=PropertySourceDemoTest`.

## 6. Walkthrough

1. `@SpringBootTest` — loads full application context.
2. `@TestPropertySource(properties = {...})` — registers `app.feature.enabled=true` and `app.timeout=30` in a `MapPropertySource` that sits above `application.properties` in the stack.
3. `registerDynamicProps` is `static` and annotated with `@DynamicPropertySource` — Spring calls it during context preparation (before beans are created). `registry.add("app.db.url", supplier)` stores a `Supplier<Object>`, evaluated lazily when the property is first resolved.
4. The simulated port `54321` would in production be `container.getMappedPort(5432)` from Testcontainers.
5. `@Value` fields are injected at bean creation time — by then both static and dynamic sources are fully registered.
6. Assertions confirm each source overrides the defaults that would come from `application.properties`.

## 7. Gotchas & takeaways

> `@DynamicPropertySource` methods **must** be `static` — they run before the Spring context exists, so there is no instance to call an instance method on.

> `@TestPropertySource` values are **static** at compile time. If the value depends on infrastructure state (container port, random token), always use `@DynamicPropertySource` instead.

> Mixing `@TestPropertySource` with `@SpringBootTest(properties = {...})` can be confusing — `@SpringBootTest.properties` takes higher precedence than `@TestPropertySource`. Pick one style per test class.

- Use `@TestPropertySource` for known, environment-independent overrides (feature flags, timeouts).
- Use `@DynamicPropertySource` whenever a test dependency (Testcontainers, WireMock) provides a value at runtime.
- Both annotations respect Spring Boot's context caching — context is reused across tests with the same effective property set.
- Prefer `@ActiveProfiles` + a dedicated `application-test.properties` when many tests need the same overrides.
