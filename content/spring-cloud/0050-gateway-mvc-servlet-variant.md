---
card: spring-cloud
gi: 50
slug: gateway-mvc-servlet-variant
title: "Gateway MVC (servlet variant)"
---

## 1. What it is

Spring Cloud Gateway MVC is a Servlet-based (Spring MVC / Tomcat / blocking I/O) implementation of the same routing concepts — routes, predicates, filters — as the original reactive WebFlux/Netty Gateway, for teams whose stack, expertise, or existing codebase is built around the traditional Servlet model rather than reactive programming.

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway-mvc</artifactId>
</dependency>
```

```java
@Bean
RouterFunction<ServerResponse> ordersRoute() {
    return route("orders-route")
            .GET("/orders/**", http())
            .before(rewritePath("/orders/(?<segment>.*)", "/${segment}"))
            .filter(addRequestHeader("X-Gateway-Source", "gateway"))
            .build();
}
```

## 2. Why & when

The reactive Gateway's Netty/WebFlux foundation is a real strength for high-concurrency, I/O-bound gateway workloads (covered in the overview card), but it requires the whole call chain — custom filters, predicates, any code touched — to stay non-blocking, which is a genuine cost for teams without reactive programming experience, or ones that need to call blocking libraries (a JDBC driver with no reactive equivalent, a legacy SDK) from within a filter. Gateway MVC removes that constraint entirely: it's built on the familiar Servlet model, so blocking code is simply normal code, at the cost of the reactive model's higher raw concurrency ceiling.

Reach for Gateway MVC when:

- The team's expertise, existing codebase, and libraries are all built around traditional Spring MVC — adopting reactive Gateway would mean either isolating it as an unfamiliar island or a costly broader shift.
- Custom filters genuinely need to call blocking code (certain database drivers, legacy internal SDKs) — in reactive Gateway this requires careful thread-pool offloading to avoid stalling the event loop; in Gateway MVC it's simply normal, unremarkable code.
- The gateway's expected concurrency and throughput needs don't require Netty's non-blocking advantage — many internal or moderate-traffic gateways are comfortably served by the traditional Servlet model.

## 3. Core concept

```
 Reactive Gateway (WebFlux/Netty):
   route matching + filter chain -> Mono/Flux, non-blocking, small thread pool, high concurrency ceiling
   any blocking code inside a filter risks stalling the shared event loop

 Gateway MVC (Servlet/Tomcat):
   route matching + filter chain -> RouterFunction/HandlerFilterFunction, one thread per request
   blocking code inside a filter is just normal code, no special handling needed
```

Same routing vocabulary — routes, predicates, filters — expressed over a different, more familiar execution model with a different concurrency ceiling.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Reactive Gateway handles many concurrent requests on a small shared thread pool while Gateway MVC dedicates one thread per in-flight request, trading raw concurrency ceiling for a simpler blocking programming model">
  <rect x="30" y="20" width="270" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Reactive Gateway (WebFlux/Netty)</text>
  <rect x="60" y="60" width="210" height="30" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="165" y="79" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">small event-loop thread pool</text>
  <text x="165" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">handles MANY concurrent requests</text>
  <text x="165" y="124" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">must stay non-blocking</text>

  <rect x="340" y="20" width="270" height="140" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Gateway MVC (Servlet/Tomcat)</text>
  <rect x="365" y="60" width="220" height="30" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="79" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">one thread per in-flight request</text>
  <text x="475" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">simpler blocking programming model</text>
  <text x="475" y="124" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">lower raw concurrency ceiling</text>

  <defs><marker id="a50" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same routing concepts, two different execution models — pick based on the team's existing stack and the workload's actual concurrency demands.

## 5. Runnable example

The scenario: route requests to `orders-service` using the Servlet-style, blocking model. Start with a simple blocking route handler, then add a filter that calls genuinely blocking code (unremarkable in this model), then add thread-per-request handling to show the concurrency tradeoff directly.

### Level 1 — Basic

A blocking route handler — no reactive types anywhere, just direct method calls.

```java
public class GatewayMvcLevel1 {
    static String routeAndForward(String path) {
        if (path.startsWith("/orders/")) {
            return callBackendBlocking("orders-service", path);
        }
        return "404";
    }

    static String callBackendBlocking(String service, String path) {
        // a real blocking HTTP client call would happen here -- no Mono, no reactive chaining needed
        return "GET " + service + path + " -> 200 OK";
    }

    public static void main(String[] args) {
        System.out.println(routeAndForward("/orders/42"));
    }
}
```

How to run: `java GatewayMvcLevel1.java`

Nothing here is reactive — `callBackendBlocking` just returns a value directly, the same style as any ordinary Spring MVC controller method, which is exactly Gateway MVC's appeal for teams already comfortable with that model.

### Level 2 — Intermediate

Add a filter that calls genuinely blocking code — a synchronous JDBC-style lookup — completely unremarkable in this model, in contrast to reactive Gateway where this would need careful handling.

```java
import java.util.*;

public class GatewayMvcLevel2 {
    static Map<String, String> apiKeyDatabase = Map.of("key-abc", "acme-corp"); // stands in for a blocking JDBC call

    static String lookupTenantBlocking(String apiKey) {
        // a real implementation might do: jdbcTemplate.queryForObject(...) -- fully synchronous, no special handling
        try { Thread.sleep(20); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); } // simulated DB latency
        return apiKeyDatabase.getOrDefault(apiKey, "unknown");
    }

    static String routeWithTenantFilter(String path, String apiKey) {
        String tenant = lookupTenantBlocking(apiKey); // ordinary blocking call, no reactive wrapping needed
        if ("unknown".equals(tenant)) return "401 Unauthorized";
        return "GET " + path + " -> forwarded for tenant=" + tenant;
    }

    public static void main(String[] args) {
        System.out.println(routeWithTenantFilter("/orders/42", "key-abc"));
        System.out.println(routeWithTenantFilter("/orders/42", "key-invalid"));
    }
}
```

How to run: `java GatewayMvcLevel2.java`

`lookupTenantBlocking` calls `Thread.sleep` directly — standing in for any blocking call (a JDBC query, a legacy synchronous SDK) — with zero special reactive-safety handling required. In reactive Gateway, this exact code would need to run on a dedicated bounded elastic scheduler to avoid stalling the shared event loop; in Gateway MVC, it's simply how filters are written.

### Level 3 — Advanced

Add thread-per-request handling to show the concurrency model directly: multiple concurrent requests, each getting a dedicated thread, and total resource usage scaling with concurrent request count.

```java
import java.util.*;
import java.util.concurrent.*;

public class GatewayMvcLevel3 {
    static Map<String, String> apiKeyDatabase = Map.of("key-abc", "acme-corp", "key-def", "globex");

    static String lookupTenantBlocking(String apiKey) {
        try { Thread.sleep(20); } catch (InterruptedException ignored) { Thread.currentThread().interrupt(); }
        return apiKeyDatabase.getOrDefault(apiKey, "unknown");
    }

    static String handleRequest(String path, String apiKey) {
        String threadName = Thread.currentThread().getName();
        String tenant = lookupTenantBlocking(apiKey);
        return threadName + ": " + path + " -> tenant=" + tenant;
    }

    public static void main(String[] args) throws Exception {
        // Servlet-model thread pool: one thread actively occupied per in-flight request
        ExecutorService requestThreadPool = Executors.newFixedThreadPool(4);

        List<String> apiKeys = List.of("key-abc", "key-def", "key-abc", "key-def");
        List<Future<String>> results = new ArrayList<>();
        for (int i = 0; i < apiKeys.size(); i++) {
            String path = "/orders/" + i;
            String key = apiKeys.get(i);
            results.add(requestThreadPool.submit(() -> handleRequest(path, key)));
        }

        for (Future<String> f : results) System.out.println(f.get());

        requestThreadPool.shutdown();
        System.out.println("peak threads actively blocked on I/O during this burst: up to " + apiKeys.size()
                + " (bounded by pool size " + 4 + ")");
    }
}
```

How to run: `java GatewayMvcLevel3.java`

Each of the four requests is submitted to a fixed thread pool and occupies one thread for its entire duration, including the 20ms it spends blocked inside `lookupTenantBlocking` — this is the direct, tangible cost of the Servlet model: thread count (and therefore memory, context-switching overhead) scales with concurrent in-flight requests, capped by the pool size, in contrast to reactive Gateway where the same 20ms "wait" would free its thread back to the shared event loop pool immediately via a non-blocking equivalent.

## 6. Walkthrough

Trace Level 3's execution.

1. `requestThreadPool`, a fixed pool of 4 threads, is created — this models a Gateway MVC deployment's Tomcat thread pool, sized to handle a known maximum number of concurrent in-flight requests.
2. The loop submits four requests to the pool, each carrying a different path and API key. Because the pool has exactly 4 threads and there are exactly 4 requests, all four can run concurrently — each submission returns immediately with a `Future`.
3. Each running task calls `handleRequest`, which records its own thread name, then calls `lookupTenantBlocking`, which blocks that specific thread for `20ms` (simulating the database round-trip) before returning the resolved tenant.
4. The `for (Future<String> f : results) println(f.get())` loop blocks the *main* thread until each task's result is available, then prints it — the printed thread names (`pool-1-thread-1` through `pool-1-thread-4`, in whatever order they actually complete) show that all four requests genuinely ran on separate, dedicated threads simultaneously.
5. The final `println` names the concrete tradeoff: with a pool of 4, at most 4 requests can be actively in-flight (each holding a thread) at once — a 5th concurrent request would have to wait for a thread to free up, whereas reactive Gateway's event-loop model would accept it immediately and simply schedule its (non-blocking) work whenever the shared threads have capacity.

```
requestThreadPool (size 4):
  thread-1 -> handles req0 (blocks 20ms inside lookupTenantBlocking)
  thread-2 -> handles req1 (blocks 20ms)
  thread-3 -> handles req2 (blocks 20ms)
  thread-4 -> handles req3 (blocks 20ms)
  all 4 run concurrently, each holding its own thread for the full 20ms
```

## 7. Gotchas & takeaways

> **Gotcha:** Gateway MVC and reactive Gateway are not simultaneously usable in the same application — they're alternative starters (`spring-cloud-starter-gateway-mvc` vs `spring-cloud-starter-gateway`) built on incompatible web stacks (Servlet vs WebFlux). Choosing between them is a project-level decision made once, not something mixed route-by-route within one deployment.

- Gateway MVC brings Gateway's routing/predicate/filter vocabulary to teams and codebases already built around traditional Spring MVC, without requiring reactive programming expertise.
- Blocking calls inside filters are unremarkable in Gateway MVC — the exact code that would need careful non-blocking handling in reactive Gateway just works normally here.
- The tradeoff is real: thread-per-request scales concurrency by adding threads (with real memory and context-switching cost per thread), where the reactive model scales by multiplexing many requests over a small, fixed thread pool.
- Choose based on the team's actual constraints — existing codebase and expertise, whether filters need blocking libraries, and whether the expected concurrency genuinely demands Netty's non-blocking ceiling — not as a default "reactive is always better" assumption.
