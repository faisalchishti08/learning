---
card: microservices
gi: 558
slug: spring-cloud-gateway-vs-gateway-mvc
title: "Spring Cloud Gateway vs Gateway MVC"
---

## 1. What it is

**Spring Cloud Gateway** (discussed earlier) is built on [WebFlux](0535-spring-webflux-reactor-for-reactive-scalability.md) and Project Reactor's reactive, non-blocking model. **Spring Cloud Gateway MVC** is a newer, alternative implementation of the same routing/predicate/filter concepts, built instead on traditional, blocking Spring MVC and the classic servlet model. Both provide the same declarative route-predicate-filter API discussed for [edge routing](0543-spring-cloud-gateway-edge-routing.md); the difference is entirely in the underlying execution model — reactive/non-blocking versus traditional/blocking — letting you choose the gateway implementation that matches your team's existing expertise and your actual throughput requirements, rather than forcing every gateway deployment into the reactive model regardless of whether it's needed.

## 2. Why & when

You choose between the two gateway implementations based on your team's familiarity and your actual scale requirements, not by default assuming reactive is always the better choice:

- **The original Spring Cloud Gateway's reactive model earns its complexity specifically at high concurrency, I/O-heavy scale**, as discussed for [WebFlux](0535-spring-webflux-reactor-for-reactive-scalability.md) — a small, fixed thread pool serving very high request volumes without needing a large thread-per-request pool. If your gateway's actual traffic doesn't approach that scale, this benefit may never materialize in practice, while the complexity cost (harder-to-debug reactive stack traces, the requirement that every custom filter avoid blocking calls) is paid regardless.
- **Gateway MVC uses the traditional, blocking servlet model your team may already have far more experience debugging and reasoning about** — ordinary stack traces, no risk of accidentally blocking an event-loop thread inside a custom filter (since there's no event loop to block), and a simpler mental model for teams without existing deep WebFlux expertise.
- **Both expose the same declarative routing DSL and filter concepts** discussed for [edge routing](0543-spring-cloud-gateway-edge-routing.md) — predicates, filters, `lb://` discovery-based destinations — so the *configuration* experience is largely the same; the difference is purely in the underlying request-handling model and its associated trade-offs.
- **You reach for Gateway MVC when your team is more comfortable with traditional Spring MVC**, your gateway's actual traffic doesn't demand WebFlux's high-concurrency benefits, or you want to avoid the specific operational risk of a blocking call accidentally creeping into a reactive gateway's event-loop-bound filter chain; you reach for the original reactive Gateway when you genuinely need to serve very high concurrent request volumes with a small, fixed thread pool.

## 3. Core concept

Recall the assembly-line-with-sensors analogy from [WebFlux](0535-spring-webflux-reactor-for-reactive-scalability.md): reactive processing frees a small crew to service far more stations by never having anyone stand and wait. The traditional model — one worker fully dedicated to one station for its full duration, including any waiting — is simpler to reason about and debug (you can always point to exactly which worker is doing exactly what, at exactly which station, right now), even though it needs proportionally more workers to handle the same station count under heavy concurrent load. Choosing Gateway MVC over the reactive Gateway is choosing the simpler, more traditional crew model deliberately, when your actual station-count (concurrent request volume) doesn't demand the reactive crew's specific advantage.

Concretely:

1. **Spring Cloud Gateway (reactive)** is built on WebFlux; a request being proxied doesn't tie up a dedicated thread for the downstream call's full round-trip, at the cost of every custom filter needing to avoid blocking operations.
2. **Spring Cloud Gateway MVC** is built on traditional Spring MVC and the classic servlet thread-per-request model; a request being proxied does tie up a thread for the downstream call's duration, exactly like any traditional blocking web application, but custom filters can use ordinary blocking code freely without any special caution.
3. **Both share the same route DSL concepts** (`RouteLocatorBuilder`-style predicates and filters, or equivalent functional route definitions for MVC) — migrating a route definition's *logic* between the two is often more about the underlying dependency and runtime model than about rewriting the routing rules themselves.
4. **The choice is a deliberate trade-off, not a strict "one is always better"** — reactive Gateway wins at very high concurrent I/O-bound scale; Gateway MVC wins on debuggability and team familiarity when that scale isn't actually the binding constraint.

## 4. Diagram

<svg viewBox="0 0 660 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Cloud Gateway (reactive) uses a small non-blocking thread pool; Gateway MVC uses the traditional thread-per-request model, both exposing the same route DSL">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Cloud Gateway (reactive)</text>
  <rect x="20" y="35" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">WebFlux, small event-loop pool</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">high concurrency, requires non-blocking filters</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Gateway MVC</text>
  <rect x="380" y="35" width="260" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring MVC, thread-per-request</text>
  <text x="510" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">simpler debugging, freely blocking filters OK</text>

  <text x="330" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Both: same route predicate/filter DSL concepts</text>
</svg>

Both implementations share the same routing concepts; the choice is about the underlying execution model matching your team's needs and actual scale.

## 5. Runnable example

Scenario: the same routing rule expressed under each model. We start with a plain Java model contrasting thread-per-request versus event-loop request handling for a proxying gateway, extend it to show the blocking-filter risk specific to the reactive model, then show both real Gateway configurations side by side.

### Level 1 — Basic

```java
// File: ThreadModelContrast.java -- contrasts how MANY concurrent
// in-flight proxy requests a THREAD-PER-REQUEST model versus a SMALL
// EVENT-LOOP POOL can handle with the SAME number of underlying threads.
public class ThreadModelContrast {
    static final int AVAILABLE_THREADS = 4;

    static int maxConcurrentBlockingRequests() {
        return AVAILABLE_THREADS; // thread-per-request: 1 thread tied up per in-flight request, for its FULL duration
    }

    static int maxConcurrentNonBlockingRequests(int simulatedFanoutPerThread) {
        // a small event-loop pool can juggle MANY more in-flight requests, since no thread blocks waiting
        return AVAILABLE_THREADS * simulatedFanoutPerThread;
    }

    public static void main(String[] args) {
        System.out.println("Gateway MVC (thread-per-request), " + AVAILABLE_THREADS + " threads -> max concurrent: " + maxConcurrentBlockingRequests());
        System.out.println("Reactive Gateway, " + AVAILABLE_THREADS + " threads -> max concurrent (illustrative): " + maxConcurrentNonBlockingRequests(500));
    }
}
```

How to run: `java ThreadModelContrast.java`

With the same 4 available threads, the thread-per-request model caps concurrent in-flight requests at 4 (one thread fully tied up per request for its whole duration), while the event-loop model can juggle far more concurrent in-flight requests (illustrated here as 500 per thread), since no thread sits idle waiting on a downstream response — exactly the trade-off discussed for WebFlux, applied specifically to a gateway's proxying workload.

### Level 2 — Intermediate

```java
// File: BlockingFilterRisk.java -- models the SPECIFIC risk of a
// blocking call inside a REACTIVE gateway's filter -- it ties up an
// event-loop thread that would otherwise serve MANY other requests.
public class BlockingFilterRisk {
    static final int EVENT_LOOP_THREADS = 4;

    static void simulateBlockingFilterCall(int concurrentRequestsHittingBlockingFilter) {
        if (concurrentRequestsHittingBlockingFilter > EVENT_LOOP_THREADS) {
            System.out.println(concurrentRequestsHittingBlockingFilter + " requests hit a BLOCKING filter simultaneously, "
                + "but only " + EVENT_LOOP_THREADS + " event-loop threads exist -- the rest QUEUE, stalling the ENTIRE gateway,");
            System.out.println("not just requests going through this one filter -- a MUCH bigger blast radius than the same mistake in a thread-per-request model.");
        } else {
            System.out.println("Within capacity for now, but this is fragile -- ANY spike past " + EVENT_LOOP_THREADS + " concurrent blocking calls stalls everything.");
        }
    }

    public static void main(String[] args) {
        simulateBlockingFilterCall(10); // more concurrent requests than event-loop threads hit the blocking filter
    }
}
```

How to run: `java BlockingFilterRisk.java`

With only 4 event-loop threads and 10 concurrent requests hitting a filter that (mistakenly) performs a blocking call, all 4 threads become tied up waiting on that blocking operation, and every *other* request the gateway is handling — not just requests going through this specific filter — stalls behind them, since there are no free event-loop threads left to process anything else at all; this is the specific, severe risk a blocking call introduces into a reactive gateway that Gateway MVC's traditional model doesn't share.

### Level 3 — Advanced

```java
// File: BothGatewayShapesRealConfig.java -- the SAME routing rule,
// expressed under BOTH the reactive Gateway and Gateway MVC configuration shapes.
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

public class BothGatewayShapesRealConfig {

    // --- REACTIVE Spring Cloud Gateway (spring-cloud-starter-gateway) ---
    @Configuration
    static class ReactiveGatewayConfig {
        @Bean
        public org.springframework.cloud.gateway.route.RouteLocator reactiveRoutes(
                org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder builder) {
            return builder.routes()
                .route("orders", r -> r.path("/api/orders/**")
                    .filters(f -> f.stripPrefix(1))
                    .uri("lb://order-service"))
                .build();
        }
    }

    // --- Gateway MVC (spring-cloud-starter-gateway-mvc), traditional Spring MVC underneath ---
    @Configuration
    static class GatewayMvcConfig {
        // real Gateway MVC route definition (functional style):
        // @Bean
        // public RouterFunction<ServerResponse> mvcRoutes() {
        //     return GatewayRouterFunctions.route("orders")
        //         .route(RequestPredicates.path("/api/orders/**"), HandlerFunctions.http())
        //         .filter(StripPrefixFilterFunctions.stripPrefix(1))
        //         .filter(LoadBalancerFilterFunctions.lb("order-service"))
        //         .build();
        // }
    }
}
```

How to run: requires `spring-cloud-starter-gateway` for the reactive version (run via `mvn spring-boot:run` on WebFlux), or `spring-cloud-starter-gateway-mvc` for the MVC version (run via `mvn spring-boot:run` on traditional Spring MVC/Tomcat); both expose functionally equivalent routing for `GET /api/orders/42`, forwarding to a load-balanced `order-service` instance with the `/api` prefix stripped — the *routing behavior* observed by an external caller is the same either way.

Both configurations express the identical routing intent — match `/api/orders/**`, strip the first path segment, forward to `order-service` via load-balanced discovery — but `ReactiveGatewayConfig` runs on WebFlux's non-blocking model, while the (illustrated) Gateway MVC equivalent runs on traditional Spring MVC's thread-per-request model; the external behavior is the same, but the internal execution model, and its associated trade-offs around concurrency and blocking-call risk, differ entirely.

## 6. Walkthrough

Trace the same `GET /api/orders/42` request through each gateway implementation, contrasting what happens to threads along the way:

**Reactive Spring Cloud Gateway:**

1. **The request arrives and is handled by one of a small, fixed number of WebFlux event-loop threads.**
2. **The route matches, filters apply (strip prefix), and the destination is resolved** via load-balanced discovery, all without blocking the event-loop thread.
3. **The proxied request to the resolved `order-service` instance is issued non-blockingly** — the event-loop thread handling this request is freed to process other requests' work while waiting for `order-service`'s response.
4. **When `order-service`'s response arrives, some event-loop thread (not necessarily the original one) resumes processing this specific request** and writes the response back to the original caller.

**Gateway MVC:**

1. **The request arrives and is assigned a dedicated thread from Spring MVC's (larger) thread pool.**
2. **The route matches, filters apply, and the destination is resolved**, exactly as above — but this time, using ordinary blocking Spring MVC filter code.
3. **The proxied request to `order-service` is issued using a blocking HTTP client call** — the thread handling this request blocks, waiting for `order-service`'s response, unable to do any other work in the meantime.
4. **When `order-service`'s response arrives, the same thread that's been blocked resumes**, and writes the response back to the caller, then becomes free to handle a new incoming request.

Under low-to-moderate concurrent load, both approaches perform comparably from an external caller's perspective — the response arrives, correctly routed, either way. Under very high concurrent load (many thousands of simultaneous in-flight proxy requests), the reactive Gateway's small event-loop pool continues serving all of them without needing a correspondingly larger thread pool, while Gateway MVC would need to scale its thread pool size (and the associated memory overhead per thread) roughly in proportion to the number of concurrent in-flight requests it needs to sustain.

## 7. Gotchas & takeaways

> **Gotcha:** choosing the reactive Gateway "by default," assuming it's simply the newer or more modern option, without an actual concurrency requirement that justifies it, means paying its full complexity cost (careful custom-filter authoring to avoid blocking calls, harder-to-read stack traces during debugging) without ever realizing its throughput benefit — Gateway MVC is not a lesser or legacy option; it's the right deliberate choice whenever your gateway's actual traffic doesn't demand the reactive model's specific advantage.

- Both Spring Cloud Gateway (reactive) and Gateway MVC expose the same declarative routing DSL concepts — predicates, filters, discovery-based destinations — differing primarily in their underlying execution model.
- The reactive Gateway earns its complexity at genuinely high concurrent, I/O-heavy scale; Gateway MVC offers simpler debugging and no risk of an accidental blocking call stalling the entire gateway's event loop.
- A blocking call inside a reactive gateway's custom filter has an outsized blast radius — it can stall every request the gateway is handling, not just requests going through that one filter, since there are only a handful of event-loop threads shared across all traffic.
- Choose based on your team's actual expertise and your gateway's actual measured (or realistically projected) concurrency needs, not by defaulting to whichever implementation seems more modern.
