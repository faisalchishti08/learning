---
card: spring-boot
gi: 206
slug: webenvironment-modes-mock-random-port-defined-port-none
title: WebEnvironment modes (MOCK, RANDOM_PORT, DEFINED_PORT, NONE)
---

## 1. What it is

`@SpringBootTest(webEnvironment = ...)` controls **whether and how an HTTP server starts** during an integration test. There are four modes: `MOCK` (default — mock servlet, no port), `RANDOM_PORT` (real server on an OS-assigned port), `DEFINED_PORT` (real server on `server.port`), and `NONE` (no web layer at all). Choosing the right mode determines which test utilities are available and how fast the test runs.

## 2. Why & when

| Mode | Use when |
|---|---|
| `MOCK` | Testing through MockMvc — fast, no real TCP socket |
| `RANDOM_PORT` | Testing real HTTP (filters, codecs, error handling) without port conflicts |
| `DEFINED_PORT` | Compatibility with tools that need a fixed port (some legacy test setups) |
| `NONE` | Testing services with no web layer at all (batch jobs, schedulers) |

`MOCK` is the default and covers most cases. `RANDOM_PORT` is essential when testing WebSocket, streaming responses, or any scenario where MockMvc's servlet mock is insufficient. `NONE` avoids starting a Tomcat/Netty container when the test doesn't touch HTTP at all.

## 3. Core concept

```java
// MOCK — fast, uses MockMvc
@SpringBootTest(webEnvironment = WebEnvironment.MOCK)
@AutoConfigureMockMvc
class MockEnvTest {
    @Autowired MockMvc mockMvc;
    @Test void health() throws Exception {
        mockMvc.perform(get("/actuator/health")).andExpect(status().isOk());
    }
}

// RANDOM_PORT — real HTTP server on a random port
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
class RandomPortTest {
    @Autowired TestRestTemplate rest;
    @LocalServerPort int port;
    @Test void health() {
        var r = rest.getForEntity("/actuator/health", String.class);
        assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
    }
}

// DEFINED_PORT — real server on server.port (default 8080)
@SpringBootTest(webEnvironment = WebEnvironment.DEFINED_PORT)
class DefinedPortTest { ... }

// NONE — no web layer
@SpringBootTest(webEnvironment = WebEnvironment.NONE)
class NoWebTest {
    @Autowired OrderService orderService; // test service in isolation
}
```

`@LocalServerPort` injects the actual port chosen when using `RANDOM_PORT`.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four WebEnvironment modes side by side: MOCK uses MockServletContext, RANDOM_PORT starts real Tomcat on ephemeral port, DEFINED_PORT on fixed port, NONE has no web layer">
  <!-- MOCK -->
  <rect x="10" y="30" width="150" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="85" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">MOCK</text>
  <text x="85" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(default)</text>
  <text x="85" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">MockServletContext</text>
  <text x="85" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no TCP port</text>
  <text x="85" y="113" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use MockMvc</text>
  <text x="85" y="128" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fastest</text>
  <text x="85" y="143" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no filter chain bypasses</text>
  <text x="85" y="155" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">possible (mock)</text>

  <!-- RANDOM_PORT -->
  <rect x="175" y="30" width="150" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="250" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">RANDOM_PORT</text>
  <text x="250" y="67" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Real Tomcat / Netty</text>
  <text x="250" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OS-assigned port</text>
  <text x="250" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use TestRestTemplate</text>
  <text x="250" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">or WebTestClient</text>
  <text x="250" y="127" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">real HTTP stack</text>
  <text x="250" y="142" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@LocalServerPort</text>
  <text x="250" y="155" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">injects chosen port</text>

  <!-- DEFINED_PORT -->
  <rect x="340" y="30" width="150" height="130" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="415" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">DEFINED_PORT</text>
  <text x="415" y="67" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Real Tomcat / Netty</text>
  <text x="415" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">uses server.port (8080)</text>
  <text x="415" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">port conflict risk</text>
  <text x="415" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">parallel tests may fail</text>
  <text x="415" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">use only when fixed</text>
  <text x="415" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">port is required</text>

  <!-- NONE -->
  <rect x="505" y="30" width="165" height="130" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="587" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">NONE</text>
  <text x="587" y="67" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No web layer</text>
  <text x="587" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no Tomcat/Netty</text>
  <text x="587" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no MockMvc</text>
  <text x="587" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">test @Service, @Repository</text>
  <text x="587" y="127" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">batch jobs, schedulers</text>
  <text x="587" y="142" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fastest for non-web</text>

  <text x="340" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">MOCK or NONE preferred — RANDOM_PORT for real HTTP; DEFINED_PORT rarely needed</text>
</svg>

Choose `MOCK` for most tests; `RANDOM_PORT` when real HTTP is needed; `NONE` for service-only tests.

## 5. Runnable example

```java
// WebEnvironmentModesDemo.java — demonstrates the four modes and their test utilities
// How to run: java WebEnvironmentModesDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: combine with @SpringBootTest(webEnvironment = WebEnvironment.XXX)

import java.util.*;

public class WebEnvironmentModesDemo {

    // Simulate an HTTP "server"
    static class FakeServer {
        final int port;
        final boolean realTcp;
        FakeServer(int port, boolean realTcp) { this.port = port; this.realTcp = realTcp; }

        String handle(String method, String path) {
            if (path.equals("/actuator/health")) return "{\"status\":\"UP\"}";
            if (path.startsWith("/api/orders"))  return "{\"id\":\"ORD-1\"}";
            return "{\"error\":\"not found\"}";
        }
    }

    // MOCK mode: no real server, all calls go through MockMvc-like dispatch
    static void mockMode() {
        System.out.println("\n=== MOCK (default) ===");
        // No FakeServer — requests go directly through the dispatcher
        FakeServer server = new FakeServer(0, false);
        System.out.println("  webEnvironment=MOCK: no TCP port bound");
        System.out.println("  Use MockMvc to dispatch requests directly to DispatcherServlet");
        System.out.println("  Response: " + server.handle("GET", "/actuator/health"));
        System.out.println("  Speed: fastest (no network stack overhead)");
        System.out.println("  @LocalServerPort: NOT injected (no port)");
        System.out.println("  Example: @AutoConfigureMockMvc + @Autowired MockMvc");
    }

    static int findFreePort() {
        try (var s = new java.net.ServerSocket(0)) { return s.getLocalPort(); }
        catch (Exception e) { return 8080; }
    }

    // RANDOM_PORT mode: real server on OS-assigned port
    static void randomPortMode() {
        int port = findFreePort();
        System.out.println("\n=== RANDOM_PORT ===");
        FakeServer server = new FakeServer(port, true);
        System.out.println("  webEnvironment=RANDOM_PORT: real server on port " + port);
        System.out.println("  @LocalServerPort injects: " + port);
        System.out.println("  Use TestRestTemplate or WebTestClient");
        System.out.println("  URL: http://localhost:" + port + "/api/orders");
        System.out.println("  Response: " + server.handle("GET", "/api/orders/1"));
        System.out.println("  Speed: slower (real Tomcat / Netty startup)");
        System.out.println("  Best for: WebSocket, SSE, real filter chain testing");
    }

    // DEFINED_PORT mode: uses server.port (default 8080)
    static void definedPortMode() {
        int port = 8080; // reads server.port from properties
        System.out.println("\n=== DEFINED_PORT ===");
        System.out.println("  webEnvironment=DEFINED_PORT: real server on port " + port);
        System.out.println("  Warning: parallel tests risk BindException (port in use)");
        System.out.println("  Only use when an external tool needs a fixed port");
        System.out.println("  URL: http://localhost:" + port + "/api/orders");
    }

    // NONE mode: no web layer
    static void noneMode() {
        System.out.println("\n=== NONE ===");
        System.out.println("  webEnvironment=NONE: no web layer instantiated");
        System.out.println("  No Tomcat/Netty, no DispatcherServlet, no MockMvc");
        System.out.println("  Perfect for: @Service, @Repository, batch, scheduler tests");
        System.out.println("  @SpringBootTest(webEnvironment=NONE) + @Autowired OrderService");
        System.out.println("  Speed: fastest (no web infrastructure)");
    }

    static void summary() {
        System.out.println("\n--- Comparison summary ---");
        System.out.printf("  %-15s %-8s %-20s %-20s%n", "Mode", "Port", "Test utility", "Best for");
        System.out.println("  " + "-".repeat(68));
        System.out.printf("  %-15s %-8s %-20s %-20s%n", "MOCK",         "none",   "MockMvc",            "Most integration tests");
        System.out.printf("  %-15s %-8s %-20s %-20s%n", "RANDOM_PORT",  "random", "TestRestTemplate",   "Real HTTP / WebSocket");
        System.out.printf("  %-15s %-8s %-20s %-20s%n", "DEFINED_PORT", "8080",   "TestRestTemplate",   "Fixed port requirement");
        System.out.printf("  %-15s %-8s %-20s %-20s%n", "NONE",         "none",   "direct @Autowired",  "Service / batch tests");
    }

    public static void main(String[] args) {
        System.out.println("=== WebEnvironment Modes Demo ===");
        mockMode();
        randomPortMode();
        definedPortMode();
        noneMode();
        summary();
    }
}
```

**How to run:** `java WebEnvironmentModesDemo.java`

## 6. Walkthrough

- **MOCK**: no real TCP socket is opened. `MockMvc` dispatches requests directly to the `DispatcherServlet` in the same thread — fast and deterministic. Spring Security filters, request mappings, and converters all run, but no actual HTTP encoding/decoding occurs.
- **RANDOM_PORT**: `findFreePort()` simulates OS port assignment. Spring Boot starts a real `EmbeddedWebServer` (Tomcat or Netty). `@LocalServerPort` injects whatever port was chosen. `TestRestTemplate` sends real HTTP requests over localhost TCP.
- **DEFINED_PORT**: identical to `RANDOM_PORT` but reads `server.port` from properties. Port conflicts when multiple test classes run in parallel — avoid unless you have a specific reason.
- **NONE**: the web infrastructure beans (`DispatcherServlet`, `TomcatServletWebServerFactory`, etc.) are not created. Services and repositories are still wired and testable. Useful for pure business logic integration tests.
- The summary table is a quick cheat-sheet for choosing modes.

## 7. Gotchas & takeaways

> `MOCK` does **not** skip Spring Security or other filters — it runs the full servlet filter chain in a mock environment. If you're seeing authentication failures in `MOCK` mode, security is working correctly.

> With `RANDOM_PORT`, `@LocalServerPort` must be `int` (not `String`). Using it with `MOCK` or `NONE` injects `0`. Always check that your test class uses the right mode when injecting this field.

- `@AutoConfigureMockMvc` is required to inject `MockMvc` even in `MOCK` mode — it's not auto-created by `@SpringBootTest` alone.
- `RANDOM_PORT` with `TestRestTemplate` automatically follows redirects and handles cookies — useful for session-based security tests.
- For reactive (WebFlux) apps, use `WebTestClient` instead of `TestRestTemplate`. Both work with `RANDOM_PORT`.
- Context caching: the same `ApplicationContext` is reused across tests with identical configurations — `webEnvironment` mode is part of the cache key, so `MOCK` and `RANDOM_PORT` tests don't share a context.
