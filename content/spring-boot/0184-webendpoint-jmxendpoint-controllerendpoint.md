---
card: spring-boot
gi: 184
slug: webendpoint-jmxendpoint-controllerendpoint
title: "@WebEndpoint / @JmxEndpoint / @ControllerEndpoint"
---

## 1. What it is

While `@Endpoint` exposes an operation over both HTTP and JMX, Spring Boot provides focused specialisations for cases where one transport needs different behaviour:

- **`@WebEndpoint`** — HTTP only. Operations can return `WebEndpointResponse<T>` to control HTTP status codes and headers. JMX ignored.
- **`@JmxEndpoint`** — JMX only. Never registered for HTTP. Useful for ops-tool-only operations.
- **`@ControllerEndpoint` / `@RestControllerEndpoint`** — treat the class like a `@Controller`; use standard Spring MVC annotations (`@GetMapping`, `@RequestBody`, `@PathVariable`) on methods. Deprecated in Spring Boot 3.3+; use `@WebEndpoint` with `@EndpointWebExtension` instead.

## 2. Why & when

**`@WebEndpoint`:** when you need HTTP-specific semantics — returning a 404, streaming a response, or setting custom headers. `@Endpoint` operations can only return POJOs or `void`; `@WebEndpoint` can return `WebEndpointResponse<T>`.

**`@JmxEndpoint`:** when an operation is too dangerous or impractical for HTTP exposure but useful via JMX/JConsole (low-level diagnostic commands, internal drain-and-shutdown sequences).

**`@ControllerEndpoint`:** the "escape hatch" when you need full Spring MVC flexibility (multipart upload, custom content negotiation). Being deprecated, prefer `@WebEndpoint` + `@EndpointWebExtension`.

## 3. Core concept

```java
// HTTP-only; can return WebEndpointResponse for status control
@Component
@WebEndpoint(id = "report")
public class ReportEndpoint {
    @ReadOperation
    public WebEndpointResponse<byte[]> generateReport() {
        byte[] pdf = ...;
        return new WebEndpointResponse<>(pdf, 200);  // sets HTTP status
    }
}

// JMX-only; never on HTTP
@Component
@JmxEndpoint(id = "diagnostics")
public class DiagnosticsEndpoint {
    @ReadOperation
    public String threadSnapshot() { return ...; }
}

// @RestControllerEndpoint — full Spring MVC API (deprecated in 3.3)
@Component
@RestControllerEndpoint(id = "uploads")
public class UploadEndpoint {
    @PostMapping("/upload")
    public ResponseEntity<?> upload(@RequestPart("file") MultipartFile f) { ... }
}
```

`WebEndpointResponse<T>` wraps the body and HTTP status. Useful to return 404 when an entity is not found, or custom headers (e.g., `Content-Disposition` for file downloads).

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three endpoint specialisations: @WebEndpoint HTTP only, @JmxEndpoint JMX only, @ControllerEndpoint HTTP MVC style">
  <!-- @Endpoint (root) -->
  <rect x="270" y="10" width="180" height="38" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="34" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Endpoint (HTTP + JMX)</text>

  <!-- Lines to children -->
  <line x1="270" y1="29" x2="165" y2="78" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="360" y1="50" x2="360" y2="78" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="450" y1="29" x2="555" y2="78" stroke="#6db33f" stroke-width="1.5"/>

  <!-- @WebEndpoint -->
  <rect x="50" y="82" width="220" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="102" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@WebEndpoint</text>
  <text x="160" y="118" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP only</text>
  <text x="160" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">can return WebEndpointResponse&lt;T&gt;</text>
  <text x="160" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">control status codes &amp; headers</text>
  <text x="160" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">NOT exposed on JMX</text>

  <!-- @JmxEndpoint -->
  <rect x="290" y="82" width="140" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="102" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JmxEndpoint</text>
  <text x="360" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JMX only</text>
  <text x="360" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">never on HTTP</text>
  <text x="360" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">diagnostic / low-level ops</text>

  <!-- @ControllerEndpoint -->
  <rect x="450" y="82" width="240" height="90" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="570" y="102" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@ControllerEndpoint</text>
  <text x="570" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">HTTP only (deprecated 3.3)</text>
  <text x="570" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">full Spring MVC annotations</text>
  <text x="570" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@GetMapping / @PostMapping etc.</text>
  <text x="570" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">use @EndpointWebExtension instead</text>
</svg>

Three HTTP/JMX transport options for custom Actuator endpoints; pick the narrowest scope that meets your needs.

## 5. Runnable example

```java
// EndpointSpecialisationDemo.java — demonstrates @WebEndpoint, @JmxEndpoint, @ControllerEndpoint semantics
// How to run: java EndpointSpecialisationDemo.java  (JDK 17+, no dependencies)

import java.util.*;

public class EndpointSpecialisationDemo {

    // Simulated WebEndpointResponse (mirrors Spring's class)
    record WebEndpointResponse<T>(T body, int status, Map<String, String> headers) {
        WebEndpointResponse(T body, int status) {
            this(body, status, Map.of());
        }
    }

    // === @WebEndpoint: HTTP-only, can set status ===
    // @Component @WebEndpoint(id = "report")
    static class ReportEndpoint {
        // @ReadOperation
        WebEndpointResponse<String> generateReport(String format) {
            if (format == null || format.isBlank()) {
                return new WebEndpointResponse<>("format parameter required", 400);
            }
            if (!Set.of("json", "csv").contains(format)) {
                return new WebEndpointResponse<>("unsupported format: " + format, 415);
            }
            return new WebEndpointResponse<>("report-data-in-" + format, 200,
                    Map.of("Content-Type", "application/" + format));
        }
    }

    // === @JmxEndpoint: JMX-only, not HTTP ===
    // @Component @JmxEndpoint(id = "diagnostics")
    static class DiagnosticsEndpoint {
        // @ReadOperation (only via JMX)
        String threadSnapshot() {
            return "Threads: main(RUNNABLE), GC(WAITING), finalizer(WAITING)";
        }

        // @WriteOperation (only via JMX)
        void forceGc() {
            System.gc();
        }
    }

    public static void main(String[] args) {
        System.out.println("=== @WebEndpoint / @JmxEndpoint / @ControllerEndpoint Demo ===\n");

        var report = new ReportEndpoint();
        var diag = new DiagnosticsEndpoint();

        // @WebEndpoint: control HTTP status
        System.out.println("--- @WebEndpoint (HTTP-only) ---");

        WebEndpointResponse<String> r1 = report.generateReport("json");
        System.out.printf("GET /actuator/report?format=json  → %d  body='%s'  headers=%s%n",
                r1.status(), r1.body(), r1.headers());

        WebEndpointResponse<String> r2 = report.generateReport("pdf");
        System.out.printf("GET /actuator/report?format=pdf   → %d  body='%s'%n",
                r2.status(), r2.body());

        WebEndpointResponse<String> r3 = report.generateReport("");
        System.out.printf("GET /actuator/report?format=      → %d  body='%s'%n",
                r3.status(), r3.body());

        System.out.println("\n--- @JmxEndpoint (JMX-only — NOT on HTTP) ---");
        System.out.println("JMX getAttribute diagnostics.ThreadSnapshot:");
        System.out.println("  " + diag.threadSnapshot());
        System.out.println("JMX operation diagnostics.ForceGc: (triggers GC)");
        diag.forceGc();
        System.out.println("  GC requested (not callable via HTTP /actuator/diagnostics)");

        System.out.println("\n--- @ControllerEndpoint (deprecated — @WebEndpoint preferred) ---");
        System.out.println("Allows full @GetMapping/@PostMapping inside the endpoint class.");
        System.out.println("Deprecation reason: mixes Spring MVC routing with Actuator lifecycle.");
        System.out.println("Replacement: @WebEndpoint + @EndpointWebExtension for HTTP customisation.");
    }
}
```

**How to run:** `java EndpointSpecialisationDemo.java`

## 6. Walkthrough

- **`ReportEndpoint`** (simulating `@WebEndpoint`): returns `WebEndpointResponse` with explicit HTTP status. `400` for missing parameter, `415` for unsupported format, `200` for success with a custom `Content-Type` header. `@Endpoint` can't do this — it only serialises the return value.
- **`DiagnosticsEndpoint`** (simulating `@JmxEndpoint`): the methods are callable only through JMX. In Spring Boot, this means they appear as MBean attributes/operations in JConsole but there is no HTTP route at `/actuator/diagnostics`.
- The `@ControllerEndpoint` section explains the deprecation rationale — `@Endpoint` operations have a technology-neutral contract; `@ControllerEndpoint` methods leak Spring MVC concepts into the endpoint, making them untestable outside an HTTP context.
- `@EndpointWebExtension(endpoint = MyEndpoint.class)` is the migration path from `@ControllerEndpoint`: it adds HTTP-specific behaviour to an existing `@Endpoint` bean without changing the core endpoint.

## 7. Gotchas & takeaways

> `@WebEndpoint` operations annotated with `@ReadOperation` that return `WebEndpointResponse<byte[]>` can serve binary content — but they bypass Spring's content negotiation. Set the `Content-Type` header explicitly inside `WebEndpointResponse`.

> `@ControllerEndpoint` is **deprecated in Spring Boot 3.3** and will be removed in a future version. Migrate to `@WebEndpoint` + `WebEndpointResponse<T>` for status control, or `@EndpointWebExtension` for HTTP-specific extensions.

- Choose the narrowest scope: `@Endpoint` if you need both HTTP and JMX; `@WebEndpoint` if HTTP-only suffices; `@JmxEndpoint` for JMX-only diagnostic tools.
- `@WebEndpoint` operations returning `null` → 404 Not Found automatically.
- `@JmxEndpoint` operations are only available when JMX is enabled (`spring.jmx.enabled=true`).
- Test `@WebEndpoint` with `MockMvc` via `@WebMvcTest(includeFilters = ...)` or the Actuator test slice.
- `@EndpointWebExtension(endpoint = FeaturesEndpoint.class)` class adds HTTP-specific behaviour: e.g., a method returning `ResponseEntity<?>` alongside the core `@Endpoint`'s JMX-compatible operations.
