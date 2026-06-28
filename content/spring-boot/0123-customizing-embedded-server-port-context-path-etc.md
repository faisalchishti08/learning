---
card: spring-boot
gi: 123
slug: customizing-embedded-server-port-context-path-etc
title: Customizing embedded server (port, context-path, etc.)
---

## 1. What it is

Spring Boot externalises embedded-server configuration through `application.properties` (or `application.yml`) under the `server.*` namespace. The most common settings are `server.port`, `server.servlet.context-path`, `server.address`, and `server.ssl.*`. All are bound automatically via `ServerProperties` — no Java code needed for everyday tuning.

## 2. Why & when

The embedded server starts with sensible defaults (port 8080, root context path). You change them when:

- **Port conflicts** — another process owns 8080, or you run multiple services on the same host.
- **Context path** — deploying behind a reverse proxy that routes by path prefix (`/api`, `/service-a`).
- **Binding address** — restricting to localhost during development or to a specific NIC in production.
- **Session timeouts / cookie settings** — tightening security.
- **Compression** — enabling HTTP response compression for bandwidth savings.

## 3. Core concept

`ServerProperties` is a `@ConfigurationProperties(prefix = "server")` class. Spring Boot binds every `server.*` property to it, then uses it to configure the `ConfigurableServletWebServerFactory`. The binding is eager and validated at startup — a bad value causes a clear error before the server opens.

Key properties at a glance:

| Property | Default | Effect |
|---|---|---|
| `server.port` | `8080` | TCP port to listen on |
| `server.port=0` | — | Random available port |
| `server.servlet.context-path` | `/` | URL prefix for all mappings |
| `server.address` | `0.0.0.0` | Bind to specific NIC IP |
| `server.servlet.session.timeout` | `30m` | HTTP session timeout |
| `server.compression.enabled` | `false` | GZip response compression |
| `server.error.path` | `/error` | Error-handler route |

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="103" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">application.properties</text>
  <text x="105" y="120" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">server.port=9090</text>
  <text x="105" y="133" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">server.servlet.context-path=/api</text>
  <rect x="270" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="106" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ServerProperties</text>
  <text x="345" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">@ConfigurationProperties</text>
  <rect x="500" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="103" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Embedded Server</text>
  <text x="580" y="120" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">port=9090</text>
  <text x="580" y="135" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">contextPath=/api</text>
  <line x1="192" y1="110" x2="266" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cp)"/>
  <text x="229" y="104" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">binds</text>
  <line x1="422" y1="110" x2="496" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cp2)"/>
  <text x="459" y="104" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">configures</text>
  <defs>
    <marker id="cp" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cp2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Properties bind to `ServerProperties`, which configures the factory before the port opens.

## 5. Runnable example

```java
// ServerConfigApp.java  —  add to a Spring Boot project with spring-boot-starter-web
// Create src/main/resources/application.properties with the properties below.

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.context.WebServerInitializedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class ServerConfigApp {
    public static void main(String[] args) {
        SpringApplication.run(ServerConfigApp.class, args);
    }
}

// application.properties content (create this file):
// server.port=9090
// server.servlet.context-path=/api
// server.servlet.session.timeout=15m
// server.compression.enabled=true
// server.compression.mime-types=application/json,text/plain

@Component
class PortLogger {
    // Fires after the server is fully started — reports the actual bound port
    @EventListener
    public void onServerReady(WebServerInitializedEvent event) {
        System.out.println("Server ready on port: " + event.getWebServer().getPort());
    }
}

@RestController
class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Running on context-path /api — reach me at /api/hello";
    }
}
```

**How to run:** create `src/main/resources/application.properties` with the lines shown in the comments, then start with `./mvnw spring-boot:run`. Access `http://localhost:9090/api/hello` (note: both port *and* context-path changed).

## 6. Walkthrough

- `server.port=9090` overrides the default 8080. Set `server.port=0` for a random port — useful in integration tests to avoid conflicts.
- `server.servlet.context-path=/api` prefixes every controller mapping. `@GetMapping("/hello")` becomes reachable at `/api/hello`.
- `server.servlet.session.timeout=15m` sets the HTTP session inactivity timeout using Spring's duration format (d, h, m, s, ms).
- `server.compression.enabled=true` with `server.compression.mime-types` enables GZip on responses whose `Content-Type` matches. Spring Boot sets a default minimum response size of 2KB before compressing.
- `WebServerInitializedEvent` fires after startup completes. `event.getWebServer().getPort()` reads the actual bound port — the same technique used in tests when `server.port=0` is set.
- All properties map to fields inside `ServerProperties` and its nested classes (`Servlet`, `Session`, `Compression`). You can see all available keys with `./mvnw spring-boot:run -Dspring-boot.run.arguments=--spring.config.additional-location=...` or by running the Actuator `/actuator/configprops` endpoint.

## 7. Gotchas & takeaways

> `server.servlet.context-path` affects Spring MVC mappings, but **not** the Actuator endpoints by default. Actuator uses `management.server.port` and `management.endpoints.web.base-path`. Don't rely on your context path to hide actuator routes.

> If you use `server.port=0` in tests, inject the port via `@LocalServerPort` rather than hardcoding 0 or 8080 in test URLs.

- Profile-specific properties files (`application-prod.properties`) override the base file — great for port differences between environments.
- `server.address=127.0.0.1` binds only to localhost, preventing external access during development.
- Session timeout accepts ISO-8601 durations (`PT15M`) or the shorthand (`15m`); both work.
- `server.ssl.*` enables HTTPS; once `server.ssl.key-store` is set, HTTP is disabled unless you add a second connector via `WebServerFactoryCustomizer`.
