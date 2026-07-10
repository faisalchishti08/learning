---
card: spring-framework
gi: 423
slug: test-property-sources-testpropertysource-dynamicpropertysour
title: "Test property sources (@TestPropertySource / @DynamicPropertySource)"
---

## 1. What it is

`@TestPropertySource` adds properties (inline key-value pairs, or a properties file) to a test's `Environment`, taking precedence over the application's normal property sources — the declarative way to override configuration for a specific test. `@DynamicPropertySource` is its runtime counterpart: a static method that registers property values computed at test-startup time, essential when a property's value (like a randomly-assigned port from a test container) isn't known until the test infrastructure is actually running.

```java
@SpringJUnitConfig(Config.class)
@TestPropertySource(properties = "retry.maxAttempts=5")
class RetryConfigTest {
    @Value("${retry.maxAttempts}") int maxAttempts; // resolves to 5, overriding any other source
}
```

## 2. Why & when

Production configuration usually comes from `application.properties`, environment variables, or a config server — none of which are appropriate to depend on in a fast, self-contained test. `@TestPropertySource` lets a test declare exactly the property values it needs, statically and predictably, without touching real configuration files or environment state. `@DynamicPropertySource` exists for the case `@TestPropertySource`'s static values can't handle: when the value itself depends on something only known once a piece of test infrastructure has already started — the classic example being Testcontainers, where a containerized database's mapped host port is randomly assigned by Docker and only known after the container is running.

Use `@TestPropertySource` when:

- A test needs a specific, known-in-advance property value different from production defaults (a shorter timeout, a feature flag forced on/off, a different retry count).
- You want property overrides declared right on the test class, self-documenting and version-controlled alongside the test itself, rather than in a separate test-specific properties file elsewhere (though that's also supported via the `locations` attribute).

Use `@DynamicPropertySource` when:

- The property's value is only known at test runtime — a randomly-assigned container port, a generated temporary file path, anything computed rather than statically known.

## 3. Core concept

```
 Property resolution order for a test (highest wins):
   1. @DynamicPropertySource-registered values   <- resolved at test startup, runtime-computed
   2. @TestPropertySource(properties=...)         <- inline, declared on the test class
   3. @TestPropertySource(locations=...)          <- a test-specific .properties file
   4. normal application property sources         <- application.properties, env vars, etc.

 @Value("${retry.maxAttempts}")
        |
        v
 Environment.resolvePlaceholders(...)
        |
        v
 checks each PropertySource in priority order -> first match wins
```

Both annotations ultimately just add entries to the test's `Environment`'s list of `PropertySource`s — `@TestPropertySource`'s entries are added once, statically, before the context loads; `@DynamicPropertySource`'s registrar method runs even earlier, computing values that then get added the same way.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple property sources layered by priority, test sources on top of application sources">
  <rect x="200" y="15" width="240" height="34" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@DynamicPropertySource (highest)</text>

  <rect x="200" y="60" width="240" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@TestPropertySource(properties)</text>

  <rect x="200" y="105" width="240" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@TestPropertySource(locations)</text>

  <rect x="200" y="150" width="240" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="172" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">application.properties (lowest)</text>
</svg>

Higher boxes win when the same property key exists at multiple levels.

## 5. Runnable example

### Level 1 — Basic

Override a single property with `@TestPropertySource(properties = ...)` and confirm it wins over the "production" default defined in the configuration class.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class TestPropertySourceBasic {

    static class RetryPolicy {
        @Value("${retry.maxAttempts:3}") // default of 3 if not overridden anywhere
        int maxAttempts;
    }

    @Configuration
    static class Config {
        @Bean RetryPolicy retryPolicy() { return new RetryPolicy(); }
    }

    @SpringJUnitConfig(Config.class)
    @TestPropertySource(properties = "retry.maxAttempts=5")
    static class RetryPolicyTest {
        @org.springframework.beans.factory.annotation.Autowired
        RetryPolicy retryPolicy;

        @Test
        void testPropertyOverridesDefault() {
            System.out.println("retry.maxAttempts resolved to: " + retryPolicy.maxAttempts);
            if (retryPolicy.maxAttempts != 5) throw new AssertionError("Expected 5, got " + retryPolicy.maxAttempts);
            System.out.println("testPropertyOverridesDefault -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(RetryPolicyTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: add `spring-test`, `spring-context`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java TestPropertySourceBasic.java`.

Without `@TestPropertySource`, `retry.maxAttempts` would resolve to the `@Value` annotation's own default, `3`. `@TestPropertySource(properties = "retry.maxAttempts=5")` adds a higher-priority property source specifically for this test, overriding that default to `5` — visible in `retryPolicy.maxAttempts` once the context is built and injected.

### Level 2 — Intermediate

Layer `@TestPropertySource`'s inline properties over a `.properties` file it also loads, showing that inline `properties` win over `locations` when both set the same key — and use `@ActiveProfiles` alongside it to show the two mechanisms composing (covered in more depth in the next card).

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

public class TestPropertySourceIntermediate {

    static class ApiClientConfig {
        @Value("${api.timeout:1000}") int timeout;
        @Value("${api.baseUrl:https://prod.example.com}") String baseUrl;
    }

    @Configuration
    static class Config {
        @Bean ApiClientConfig apiClientConfig() { return new ApiClientConfig(); }
    }

    @SpringJUnitConfig(Config.class)
    @TestPropertySource(
            locations = "classpath:test-api.properties", // e.g. contains: api.baseUrl=https://test.example.com
            properties = "api.timeout=50" // inline value wins over anything the file also sets for this key
    )
    @ActiveProfiles("test")
    static class ApiClientConfigTest {
        @org.springframework.beans.factory.annotation.Autowired
        ApiClientConfig config;

        @Test
        void propertiesLayerCorrectly() {
            System.out.println("timeout=" + config.timeout + " baseUrl=" + config.baseUrl);
            if (config.timeout != 50) throw new AssertionError("Expected inline property to win: timeout=50");
            if (!config.baseUrl.equals("https://test.example.com")) throw new AssertionError("Expected file-provided baseUrl");
            System.out.println("propertiesLayerCorrectly -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ApiClientConfigTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, with a `test-api.properties` file on the classpath containing `api.baseUrl=https://test.example.com`; then `java TestPropertySourceIntermediate.java`.

`locations` loads the properties file (providing `api.baseUrl`), while the inline `properties` attribute sets `api.timeout` directly on the test class — both apply simultaneously, and if the file also happened to define `api.timeout`, the inline value would still win, since inline `properties` sit at a higher priority than `locations`-loaded files in the resolution order.

### Level 3 — Advanced

Use `@DynamicPropertySource` to register a property whose value is only known once test infrastructure has started — simulated here with an in-process "fake container" that binds to a random port, mirroring exactly the pattern used with real Testcontainers-backed integration tests.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.io.IOException;
import java.net.ServerSocket;

public class TestPropertySourceAdvanced {

    // Simulates a containerized dependency (e.g. a database or cache) whose port
    // is only assigned once it actually starts -- exactly like a real Testcontainer.
    static class FakeContainer {
        private ServerSocket serverSocket;

        void start() {
            try {
                serverSocket = new ServerSocket(0); // OS assigns a free port -- unknown until now
                System.out.println("FakeContainer started on port " + serverSocket.getLocalPort());
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }

        int getMappedPort() { return serverSocket.getLocalPort(); }

        void stop() {
            try { serverSocket.close(); } catch (IOException ignored) {}
        }
    }

    static final FakeContainer CONTAINER = new FakeContainer();

    static class ServiceClient {
        @Value("${service.port}")
        int port;
    }

    @Configuration
    static class Config {
        @Bean ServiceClient serviceClient() { return new ServiceClient(); }
    }

    @SpringJUnitConfig(Config.class)
    static class DynamicPropertyTest {
        @org.springframework.beans.factory.annotation.Autowired
        ServiceClient serviceClient;

        @org.junit.jupiter.api.BeforeAll
        static void startContainer() {
            CONTAINER.start(); // must run BEFORE @DynamicPropertySource is consulted
        }

        @DynamicPropertySource
        static void registerDynamicProperties(DynamicPropertyRegistry registry) {
            // The port isn't known until CONTAINER.start() has run -- exactly why this
            // can't be a static @TestPropertySource value declared ahead of time.
            registry.add("service.port", CONTAINER::getMappedPort);
        }

        @Test
        void serviceClientGetsTheDynamicallyAssignedPort() {
            System.out.println("ServiceClient resolved port: " + serviceClient.port);
            System.out.println("Container's actual port: " + CONTAINER.getMappedPort());
            if (serviceClient.port != CONTAINER.getMappedPort()) {
                throw new AssertionError("Expected the dynamically registered port to match the container's real port");
            }
            System.out.println("serviceClientGetsTheDynamicallyAssignedPort -- PASS");
        }

        @org.junit.jupiter.api.AfterAll
        static void stopContainer() {
            CONTAINER.stop();
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(DynamicPropertyTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 1, then `java TestPropertySourceAdvanced.java`.

`registry.add("service.port", CONTAINER::getMappedPort)` registers a *supplier*, not a static value — the framework calls this supplier lazily when the property is actually needed, which must be after `startContainer()` (a `@BeforeAll` method) has already assigned the real port. This exact pattern — start a container, then use `@DynamicPropertySource` to wire its runtime-assigned connection details into the Spring `Environment` — is the standard way real Testcontainers-based integration tests connect Spring beans (a `DataSource`, a Redis client) to a containerized dependency without hardcoding a port.

## 6. Walkthrough

Trace `TestPropertySourceAdvanced.DynamicPropertyTest`'s startup sequence:

1. **`@BeforeAll` runs first.** JUnit 5 guarantees `startContainer()` executes before any test method and, critically, before the Spring `ApplicationContext` is built for this test class — `CONTAINER.start()` binds a `ServerSocket` to port `0`, letting the OS assign a genuinely free, previously-unknown port.
2. **`@DynamicPropertySource` method runs.** The TestContext Framework calls `registerDynamicProperties(registry)` as part of preparing the test's `Environment`, before the `ApplicationContext` actually refreshes. `registry.add("service.port", CONTAINER::getMappedPort)` doesn't call `getMappedPort()` immediately — it registers the method reference as a lazy supplier.
3. **Context refresh, property resolution.** When the `ApplicationContext` builds `ServiceClient` and processes its `@Value("${service.port}")` field, the `Environment`'s property resolution reaches the dynamically-registered source, *now* invoking the supplier — calling `CONTAINER.getMappedPort()`, which returns the real port the container bound to in step 1 (which by now has definitely already happened).
4. **Field populated.** `serviceClient.port` is set to that resolved integer value.
5. **Test body verification.** `serviceClientGetsTheDynamicallyAssignedPort` compares `serviceClient.port` against `CONTAINER.getMappedPort()` called directly — both reflect the same real port number, confirming the dynamic property correctly threaded the runtime-only-known value into Spring's configuration system.
6. **`@AfterAll` cleanup.** `stopContainer()` runs after all test methods in the class complete, closing the socket.

```
@BeforeAll: CONTAINER.start()  -> binds to port, e.g. 54231 (unknown until now)
@DynamicPropertySource: registry.add("service.port", CONTAINER::getMappedPort)  -- lazy, not called yet
ApplicationContext refresh:
   ServiceClient's @Value("${service.port}") resolved
     -> dynamic property source invoked NOW -> CONTAINER.getMappedPort() -> 54231
   serviceClient.port = 54231
test: serviceClient.port == CONTAINER.getMappedPort() -- PASS
```

## 7. Gotchas & takeaways

> Gotcha: `@DynamicPropertySource` methods must be `static`, and the value they depend on (here, the container's assigned port) must already exist by the time the `ApplicationContext` is built — which typically means starting the underlying infrastructure (a container, a server) in a `static` field initializer, a `@BeforeAll` method, or a JUnit 5 extension that runs early enough. Registering a dynamic property whose dependency hasn't started yet produces a `NullPointerException` or similar failure the moment the supplier is actually invoked during context refresh, not at declaration time — making the root cause easy to misdiagnose if you don't know to check startup ordering first.

- `@TestPropertySource` overrides configuration with statically known values, declared directly on the test class (`properties`) or loaded from a dedicated file (`locations`) — inline `properties` take priority over `locations` when both set the same key.
- `@DynamicPropertySource` is for values only known at test runtime — most commonly a container's randomly-assigned port — registered as a lazy supplier rather than a static value.
- Both mechanisms sit at a higher priority than normal application property sources, letting tests reliably override production configuration without touching real config files or environment variables.
- Ensure whatever a `@DynamicPropertySource` value depends on has already started before the `ApplicationContext` builds — typically via `@BeforeAll` or an equivalently early lifecycle hook.
