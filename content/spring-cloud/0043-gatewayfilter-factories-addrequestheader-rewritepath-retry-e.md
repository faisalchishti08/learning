---
card: spring-cloud
gi: 43
slug: gatewayfilter-factories-addrequestheader-rewritepath-retry-e
title: "GatewayFilter factories (AddRequestHeader, RewritePath, Retry, etc.)"
---

## 1. What it is

GatewayFilter factories are Gateway's built-in library of route-scoped filters — transformations that only apply to requests matching a specific route. `AddRequestHeader`, `RewritePath`, `Retry`, `AddResponseHeader`, `CircuitBreaker`, `RequestRateLimiter`, `StripPrefix`, and dozens more, each configurable with arguments, so most request/response transformation needs never require custom Java filter code.

```yaml
filters:
  - AddRequestHeader=X-Gateway-Source, gateway
  - RewritePath=/api/orders/(?<segment>.*), /orders/${segment}
  - name: Retry
    args:
      retries: 3
      statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE
      backoff:
        firstBackoff: 50ms
        maxBackoff: 500ms
```

## 2. Why & when

The earlier Routes/Predicates/Filters card modeled the filter-chain mechanism by hand; this card is the actual catalog most real Gateway configurations draw from. A route almost always needs *some* transformation — adding tracing headers, rewriting a public-facing path to the backend's actual path, retrying a transient failure — and the built-in factories cover the overwhelming majority of these needs declaratively.

Reach for specific factories based on what the route actually needs:

- `AddRequestHeader`/`AddResponseHeader` for stamping metadata (a gateway-source marker, a correlation ID) onto requests or responses without touching backend code.
- `RewritePath`/`StripPrefix` when the externally-exposed path doesn't match the backend's actual path structure — very common, since backends are rarely designed with the gateway's public URL scheme in mind.
- `Retry` for transient failures — a backend instance briefly overloaded, a fleeting network blip — retried automatically before the caller ever sees an error.
- `CircuitBreaker` and `RequestRateLimiter` for resilience and traffic shaping (each covered in its own upcoming card).

## 3. Core concept

```
 AddRequestHeader=name,value      -> adds a header to the outgoing request
 AddResponseHeader=name,value     -> adds a header to the response before it reaches the client
 RewritePath=regex,replacement    -> rewrites the request path using a regex capture group
 StripPrefix=N                    -> removes the first N path segments
 Retry=retries,statuses,backoff   -> re-attempts the backend call on matching failure statuses
```

Each factory transforms one specific aspect of the request or response; a route's filter list chains as many as needed, applied in declared order.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request path is rewritten and given a header, forwarded to the backend, and retried automatically if the backend returns a transient failure status">
  <rect x="20" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">/api/orders/42</text>

  <line x1="200" y1="40" x2="240" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a43)"/>

  <rect x="245" y="20" width="180" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="335" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">RewritePath</text>
  <text x="335" y="53" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; /orders/42</text>

  <line x1="425" y1="40" x2="465" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a43)"/>

  <rect x="470" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="545" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">orders-service</text>

  <line x1="545" y1="60" x2="545" y2="90" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#a43)"/>
  <rect x="440" y="95" width="210" height="40" rx="6" fill="#e6494930" stroke="#e64949" stroke-width="1.3"/>
  <text x="545" y="119" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">503 -&gt; Retry filter re-attempts</text>

  <line x1="440" y1="115" x2="335" y2="60" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#a43)"/>

  <defs><marker id="a43" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The path is rewritten before forwarding, and a transient failure response triggers an automatic retry back through the same route.

## 5. Runnable example

The scenario: expose `/api/orders/**` externally while `orders-service` actually expects `/orders/**`. Start with basic path rewriting, then add a request header stamp, then add retry-on-failure with backoff for transient errors.

### Level 1 — Basic

`RewritePath`: translate the public path to the backend's real path.

```java
import java.util.regex.*;

public class GatewayFilterFactoriesLevel1 {
    static String rewritePath(String path, String regex, String replacement) {
        Pattern pattern = Pattern.compile(regex);
        Matcher matcher = pattern.matcher(path);
        return matcher.matches() ? matcher.replaceFirst(replacement) : path;
    }

    public static void main(String[] args) {
        String publicPath = "/api/orders/42";
        String backendPath = rewritePath(publicPath, "/api/orders/(?<segment>.*)", "/orders/${segment}");

        System.out.println("public path:  " + publicPath);
        System.out.println("backend path: " + backendPath);
    }
}
```

How to run: `java GatewayFilterFactoriesLevel1.java`

This mirrors `RewritePath`'s regex-capture-and-replace mechanism directly: `orders-service` never needs to know or care that clients call it through `/api/orders/**` externally.

### Level 2 — Intermediate

Add `AddRequestHeader`, chaining it after the path rewrite — modeling a route's full filter list applied in order.

```java
import java.util.*;
import java.util.regex.*;

public class GatewayFilterFactoriesLevel2 {
    static class Request {
        String path;
        Map<String, String> headers = new LinkedHashMap<>();
        Request(String path) { this.path = path; }
    }

    static Request rewritePath(Request req, String regex, String replacement) {
        Matcher matcher = Pattern.compile(regex).matcher(req.path);
        if (matcher.matches()) req.path = matcher.replaceFirst(replacement);
        return req;
    }

    static Request addRequestHeader(Request req, String name, String value) {
        req.headers.put(name, value);
        return req;
    }

    public static void main(String[] args) {
        Request req = new Request("/api/orders/42");

        req = rewritePath(req, "/api/orders/(?<segment>.*)", "/orders/${segment}");
        req = addRequestHeader(req, "X-Gateway-Source", "gateway");

        System.out.println("final path: " + req.path);
        System.out.println("final headers: " + req.headers);
    }
}
```

How to run: `java GatewayFilterFactoriesLevel2.java`

Each filter function takes the current request state and returns the transformed version, threaded through in declared order — exactly the filter-chaining model from the earlier Routes/Predicates/Filters card, now populated with two real, commonly-used factories.

### Level 3 — Advanced

Add `Retry` with backoff: re-attempt the backend call automatically on a transient failure status, up to a configured retry limit, with increasing delay between attempts.

```java
import java.util.*;
import java.util.function.Supplier;

public class GatewayFilterFactoriesLevel3 {
    record BackendResponse(int status, String body) {}

    static BackendResponse callWithRetry(Supplier<BackendResponse> backendCall, int maxRetries,
                                          Set<Integer> retryableStatuses, long firstBackoffMs, long maxBackoffMs) {
        long backoff = firstBackoffMs;
        BackendResponse last = null;
        for (int attempt = 0; attempt <= maxRetries; attempt++) {
            last = backendCall.get();
            if (!retryableStatuses.contains(last.status())) {
                return last; // success, or a non-retryable failure -- stop immediately
            }
            System.out.println("attempt " + (attempt + 1) + " got " + last.status()
                    + (attempt < maxRetries ? ", retrying after " + backoff + "ms" : ", out of retries"));
            backoff = Math.min(backoff * 2, maxBackoffMs); // exponential backoff, capped
        }
        return last; // exhausted retries, return the last (still-failing) response
    }

    public static void main(String[] args) {
        // simulate a flaky backend: fails twice with 503, then succeeds
        int[] callCount = {0};
        Supplier<BackendResponse> flakyBackend = () -> {
            callCount[0]++;
            if (callCount[0] < 3) return new BackendResponse(503, "Service Unavailable");
            return new BackendResponse(200, "{\"orderId\":42}");
        };

        BackendResponse result = callWithRetry(flakyBackend, 3, Set.of(502, 503), 50, 500);
        System.out.println("final result: " + result.status() + " " + result.body());
    }
}
```

How to run: `java GatewayFilterFactoriesLevel3.java`

`callWithRetry` mirrors the `Retry` filter's real behavior: it re-attempts the backend call whenever the response status is in the configured `retryableStatuses` set, doubling the backoff delay after each failed attempt up to `maxBackoffMs`, and gives up once `maxRetries` is reached. The simulated `flakyBackend` fails its first two calls and succeeds on the third, so the caller ultimately sees a `200` — the two transient `503`s never reach the original client at all.

## 6. Walkthrough

Trace `callWithRetry`'s execution against the flaky backend in Level 3.

1. `attempt=0` runs first — `backendCall.get()` invokes `flakyBackend`, incrementing `callCount` to `1`. Since `1 < 3`, it returns `BackendResponse(503, "Service Unavailable")`. Because `503` is in `retryableStatuses`, the method doesn't return; it prints the retry message and doubles `backoff` from `50` to `100`.
2. `attempt=1` runs next — `flakyBackend` runs again, `callCount` becomes `2`, still `< 3`, so another `503` comes back. Again retryable, so the loop continues, printing the second retry message and doubling `backoff` from `100` to `200`.
3. `attempt=2` runs — `callCount` becomes `3`, which is no longer `< 3`, so `flakyBackend` returns `BackendResponse(200, "{\"orderId\":42}")`. Since `200` is not in `retryableStatuses`, the method returns immediately with this successful response — no further attempts, no further backoff.
4. The final `println` shows `200 {"orderId":42}` — from the calling client's perspective, this whole retry sequence happened transparently inside the gateway; only the eventual success (or, had all attempts failed, the final failure) is ever visible outside.

```
attempt 1 -> 503 (retryable) -> wait 50ms  -> retry
attempt 2 -> 503 (retryable) -> wait 100ms -> retry
attempt 3 -> 200 (not retryable) -> return immediately, client sees 200
```

## 7. Gotchas & takeaways

> **Gotcha:** `Retry` re-sends the request to the backend — for non-idempotent operations (a `POST` that creates a resource, a payment charge), blindly retrying a request that actually succeeded but whose *response* was lost in transit can cause the operation to happen twice. Configure `Retry` methods/statuses carefully, and prefer idempotent backend design (idempotency keys) for anything retried automatically.

- `RewritePath` and `StripPrefix` solve the same general problem — a mismatch between the externally-exposed path and the backend's real path — `RewritePath` for arbitrary regex transformations, `StripPrefix` for the simpler common case of just dropping leading segments.
- Filters chain in declared order, and each one operates on the output of the previous one — the same threading-through model as predicates, just transforming instead of testing.
- Exponential backoff between retries (rather than immediate, rapid re-attempts) reduces the chance that retries themselves overwhelm an already-struggling backend instance.
- `AddRequestHeader`/`AddResponseHeader` are the simplest and safest filters to reach for — they never risk double-executing an operation, unlike `Retry`, since they don't change how many times the backend call itself happens.
