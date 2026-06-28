---
card: spring-boot
gi: 200
slug: http-exchanges-recording
title: HTTP exchanges recording
---

## 1. What it is

**HTTP exchanges recording** captures a configurable rolling buffer of recent HTTP request/response pairs and exposes them at `/actuator/httpexchanges`. Each entry includes the request URI, method, headers, status code, response time, and session/principal info. Spring Boot auto-configures this when `spring-boot-starter-actuator` is present and you register an `HttpExchangeRepository` bean — the simplest being `InMemoryHttpExchangeRepository`.

## 2. Why & when

`/actuator/httpexchanges` is a **lightweight traffic audit log** for development and staging:
- "What was the last request that caused that 500?" — see the full request URI, headers, and response time without a log search.
- "Why is the mobile app calling `/api/v1/legacy`?" — spot unexpected traffic patterns.
- "Which endpoint is slow right now?" — check actual durations without Prometheus.

It is **not** meant for production-scale request logging (use access logs, distributed tracing, or an API gateway for that). The buffer is fixed-size and in-memory; it's a debugging aid, not an audit trail.

## 3. Core concept

**Enable recording** by registering a repository bean:
```java
@Bean
public HttpExchangeRepository httpExchangeRepository() {
    InMemoryHttpExchangeRepository repo = new InMemoryHttpExchangeRepository();
    repo.setCapacity(200); // default 100; keep last 200 exchanges
    return repo;
}
```

**Expose the endpoint** in `application.properties`:
```properties
management.endpoints.web.exposure.include=httpexchanges
```

**`GET /actuator/httpexchanges`** returns:
```json
{
  "exchanges": [
    {
      "timestamp": "2024-04-01T12:00:01.123Z",
      "request": {
        "uri": "http://localhost:8080/api/orders/42",
        "method": "GET",
        "headers": { "Accept": ["application/json"] }
      },
      "response": {
        "status": 200,
        "headers": { "Content-Type": ["application/json"] }
      },
      "timeTaken": "PT0.045S"
    }
  ]
}
```

**Filter what's recorded** via `application.properties`:
```properties
# exclude Actuator traffic from the recording
management.httpexchanges.recording.include=REMOTE_ADDRESS,TIME_TAKEN,REQUEST_HEADERS,RESPONSE_HEADERS
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HTTP requests flow through Spring's filter; each is stored in InMemoryHttpExchangeRepository; GET /actuator/httpexchanges returns the rolling buffer">
  <!-- Incoming requests -->
  <rect x="10" y="80" width="110" height="50" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="102" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">HTTP Clients</text>
  <text x="65" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">browser / mobile</text>

  <!-- Arrow to filter -->
  <line x1="122" y1="105" x2="185" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#hxa)"/>

  <!-- HttpExchangesFilter -->
  <rect x="190" y="60" width="165" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="272" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">HttpExchangesFilter</text>
  <text x="272" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">(auto-configured)</text>
  <text x="272" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">records: method, uri</text>
  <text x="272" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">status, headers, timeTaken</text>
  <text x="272" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">→ HttpExchangeRepository</text>

  <!-- Pass-through to app -->
  <line x1="357" y1="105" x2="420" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hxb)"/>
  <rect x="425" y="85" width="105" height="40" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="477" y="109" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Your App</text>

  <!-- Store arrow -->
  <line x1="272" y1="153" x2="272" y2="175" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#hxb)"/>

  <!-- Repository -->
  <rect x="175" y="178" width="195" height="22" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="272" y="194" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">InMemoryHttpExchangeRepository (capacity=100)</text>

  <!-- Actuator reads -->
  <line x1="372" y1="189" x2="545" y2="155" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#hxc)"/>
  <rect x="548" y="125" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="608" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator</text>
  <text x="608" y="161" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">/httpexchanges</text>

  <!-- Ops reads -->
  <line x1="670" y1="150" x2="670" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#hxc)"/>
  <text x="672" y="125" fill="#79c0ff" font-size="8" font-family="sans-serif" text-anchor="start">GET</text>

  <text x="340" y="44" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Every request is intercepted, recorded, and viewable without log search</text>

  <defs>
    <marker id="hxa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="hxb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="hxc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Every HTTP request passes through `HttpExchangesFilter`; the last N exchanges are retrievable at `/actuator/httpexchanges`.

## 5. Runnable example

```java
// HttpExchangesRecordingDemo.java — simulates rolling HTTP exchange buffer
// How to run: java HttpExchangesRecordingDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: register InMemoryHttpExchangeRepository @Bean; expose httpexchanges endpoint

import java.time.*;
import java.util.*;

public class HttpExchangesRecordingDemo {

    record HttpExchange(
        Instant timestamp,
        String method,
        String uri,
        Map<String, String> requestHeaders,
        int status,
        Map<String, String> responseHeaders,
        Duration timeTaken
    ) {
        @Override public String toString() {
            return String.format("%s %s → %d  (%dms)  [%s]",
                method, uri, status, timeTaken.toMillis(),
                timestamp.toString().substring(11, 23));
        }
    }

    // Simulates InMemoryHttpExchangeRepository
    static class HttpExchangeRepository {
        private final int capacity;
        private final Deque<HttpExchange> buffer;

        HttpExchangeRepository(int capacity) {
            this.capacity = capacity;
            this.buffer   = new ArrayDeque<>(capacity);
        }

        void add(HttpExchange exchange) {
            if (buffer.size() >= capacity) {
                buffer.pollFirst(); // evict oldest
            }
            buffer.addLast(exchange);
        }

        List<HttpExchange> findAll() {
            return new ArrayList<>(buffer);
        }

        int size() { return buffer.size(); }
    }

    // Simulate the filter wrapping each request
    static HttpExchange simulateRequest(String method, String uri,
                                        Map<String, String> reqHeaders,
                                        int status, long latencyMs) {
        Instant ts = Instant.now();
        Map<String, String> respHeaders = new LinkedHashMap<>();
        respHeaders.put("Content-Type", "application/json");
        respHeaders.put("X-Response-Time", latencyMs + "ms");
        return new HttpExchange(ts, method, uri, reqHeaders, status, respHeaders,
                Duration.ofMillis(latencyMs));
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== HTTP Exchanges Recording Demo ===\n");

        // Simulate InMemoryHttpExchangeRepository with capacity=5
        HttpExchangeRepository repo = new HttpExchangeRepository(5);

        // Simulate a series of incoming HTTP requests
        List<Object[]> requests = List.of(
            new Object[]{"GET",    "/api/orders",       200, 45L},
            new Object[]{"POST",   "/api/orders",       201, 112L},
            new Object[]{"GET",    "/api/orders/42",    200, 23L},
            new Object[]{"DELETE", "/api/orders/40",    204, 18L},
            new Object[]{"GET",    "/api/users/7",      200, 67L},
            new Object[]{"GET",    "/api/orders/99",    404, 8L},
            new Object[]{"POST",   "/api/payments",     500, 2103L},
            new Object[]{"GET",    "/actuator/health",  200, 3L}
        );

        System.out.println("Processing " + requests.size() + " requests (buffer capacity=5)...\n");

        for (Object[] r : requests) {
            Map<String, String> headers = new LinkedHashMap<>();
            headers.put("Accept", "application/json");
            headers.put("User-Agent", "DemoApp/1.0");

            HttpExchange exchange = simulateRequest(
                (String) r[0], (String) r[1], headers, (int) r[2], (long) r[3]);
            repo.add(exchange);
            Thread.sleep(2); // tiny pause so timestamps differ
            System.out.println("  recorded: " + exchange);
        }

        System.out.println("\n=== GET /actuator/httpexchanges ===");
        System.out.println("Buffer holds last " + repo.size() + " of " + requests.size() + " total requests:");
        System.out.println();

        List<HttpExchange> exchanges = repo.findAll();
        for (int i = 0; i < exchanges.size(); i++) {
            HttpExchange ex = exchanges.get(i);
            System.out.printf("[%d] timestamp=%s%n", i + 1, ex.timestamp());
            System.out.printf("    request:  %s %s%n", ex.method(), ex.uri());
            System.out.printf("    response: %d  timeTaken=%dms%n", ex.status(), ex.timeTaken().toMillis());
            System.out.printf("    headers:  %s%n", ex.responseHeaders());
            System.out.println();
        }

        System.out.println("--- Notice: first 3 requests evicted (oldest evicted when buffer full) ---");
        System.out.println();
        System.out.println("--- Spring Boot configuration ---");
        System.out.println("# Register repository bean (application @Configuration):");
        System.out.println("@Bean InMemoryHttpExchangeRepository httpExchangeRepository() {");
        System.out.println("    var r = new InMemoryHttpExchangeRepository();");
        System.out.println("    r.setCapacity(200);");
        System.out.println("    return r;");
        System.out.println("}");
        System.out.println();
        System.out.println("# Expose endpoint:");
        System.out.println("management.endpoints.web.exposure.include=httpexchanges");
        System.out.println();
        System.out.println("# Tune what gets recorded:");
        System.out.println("management.httpexchanges.recording.include=\\");
        System.out.println("  REMOTE_ADDRESS,TIME_TAKEN,REQUEST_HEADERS,RESPONSE_HEADERS,\\");
        System.out.println("  PRINCIPAL,SESSION_ID");
    }
}
```

**How to run:** `java HttpExchangesRecordingDemo.java`

## 6. Walkthrough

- **`HttpExchangeRepository` with `capacity=5`**: accepts 8 requests but only keeps the last 5. When the 6th arrives, the 1st is evicted (`pollFirst()`). This matches `InMemoryHttpExchangeRepository.setCapacity()`.
- **`simulateRequest`**: mirrors what Spring Boot's `HttpExchangesFilter` does: captures timestamp, method, URI, request headers, response status, response headers, and `timeTaken` before and after the filter chain completes.
- **`GET /actuator/httpexchanges` output**: shows that only requests 4-8 remain (the `POST /api/orders`, `GET /api/orders/42`, etc. are evicted). In production, the first 3 `/api/orders` calls would already be gone.
- **The 500 on `/api/payments`** and its 2103ms `timeTaken` stand out — exactly the kind of signal this endpoint surfaces without a log search.
- **Configuration snippet**: shows the real Spring Boot `@Bean` and property keys used.

## 7. Gotchas & takeaways

> `InMemoryHttpExchangeRepository` records **nothing by default** — you must register it as a `@Bean`. Just adding `starter-actuator` and exposing the endpoint is not enough; without the repository bean, `/actuator/httpexchanges` returns 404.

> Request headers may include `Authorization` tokens. Spring Boot **does not** redact sensitive headers automatically. Either exclude `REQUEST_HEADERS` from `management.httpexchanges.recording.include`, or ensure the endpoint is secured so only admins can call it.

- Default capacity is 100 exchanges. Large payloads are not stored (only headers, not bodies).
- Actuator traffic (requests to `/actuator/**`) is typically excluded from recording to avoid noise — configure with `management.httpexchanges.recording.include`.
- `timeTaken` is the full round-trip through the filter chain, including your controller and any downstream calls — it is **not** just controller time.
- For production audit trails or distributed request logging, use access logs (`server.tomcat.accesslog.enabled=true`) or distributed tracing instead — the exchange buffer is in-memory, lost on restart, and has no indexing.
- Custom `HttpExchangeRepository` implementations can persist to Redis or a database for durable cross-node recording.
