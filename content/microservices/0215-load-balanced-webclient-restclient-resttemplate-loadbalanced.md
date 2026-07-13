---
card: microservices
gi: 215
slug: load-balanced-webclient-restclient-resttemplate-loadbalanced
title: "Load-balanced WebClient / RestClient / RestTemplate (@LoadBalanced)"
---

## 1. What it is

`@LoadBalanced` is a Spring qualifier annotation that can be attached to a `RestTemplate`, `WebClient.Builder`, or `RestClient.Builder` bean, activating [Spring Cloud LoadBalancer](0202-spring-cloud-loadbalancer-using-the-registry.md) interception for that specific client — the same underlying discovery-plus-selection mechanism applies uniformly across all three HTTP client types, differing only in how each client's blocking-versus-reactive execution model interacts with it.

## 2. Why & when

Spring offers three different HTTP client APIs — the older, blocking `RestTemplate`; the reactive, non-blocking `WebClient`; and `RestClient`, a newer (Spring 6.1+) synchronous, fluent client — and a codebase migrating between them, or choosing one for a new service, needs load-balanced (logical-service-name-based) calling to work identically regardless of which client is in use. `@LoadBalanced` provides exactly that: a single, consistent activation mechanism that plugs Spring Cloud LoadBalancer into whichever client type the bean declaration names, so switching from `RestTemplate` to `WebClient` (for example, to adopt a reactive stack) doesn't require relearning or reimplementing how load-balanced calls are made.

Use `@LoadBalanced RestTemplate` in traditional blocking Spring MVC applications, `@LoadBalanced WebClient.Builder` in reactive Spring WebFlux applications (or anywhere non-blocking calls are wanted), and `@LoadBalanced RestClient.Builder` for new blocking-style code that prefers `RestClient`'s more modern, fluent API over `RestTemplate` — which is itself in maintenance mode. All three achieve the same logical-name resolution; the choice between them is about the surrounding application's execution model, not about load-balancing capability.

## 3. Core concept

`@LoadBalanced` is applied to the bean *builder* for `WebClient` and `RestClient` (since the actual client instance is built from the builder later), but directly to the `RestTemplate` bean itself, because `RestTemplate` has no separate builder step in this pattern — a small but easy-to-miss asymmetry when switching between client types.

```java
@Configuration
public class ClientConfig {
    @Bean
    @LoadBalanced // applied DIRECTLY to the RestTemplate bean
    public RestTemplate restTemplate() { return new RestTemplate(); }

    @Bean
    @LoadBalanced // applied to the BUILDER, not a built WebClient
    public WebClient.Builder loadBalancedWebClientBuilder() { return WebClient.builder(); }

    @Bean
    @LoadBalanced // applied to the BUILDER, not a built RestClient
    public RestClient.Builder loadBalancedRestClientBuilder() { return RestClient.builder(); }
}

// usage: all three resolve "order-service" as a LOGICAL name, identically
restTemplate.getForObject("http://order-service/orders/42", String.class); // BLOCKING
webClientBuilder.build().get().uri("http://order-service/orders/42").retrieve().bodyToMono(String.class); // REACTIVE
restClientBuilder.build().get().uri("http://order-service/orders/42").retrieve().body(String.class); // BLOCKING, fluent
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three client types -- RestTemplate directly, and WebClient.Builder and RestClient.Builder indirectly through their builders -- all route through the same Spring Cloud LoadBalancer interceptor before reaching the resolved instance" >
  <rect x="20" y="15" width="180" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="37" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@LoadBalanced RestTemplate</text>

  <rect x="20" y="60" width="180" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@LoadBalanced WebClient.Builder</text>

  <rect x="20" y="105" width="180" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@LoadBalanced RestClient.Builder</text>

  <rect x="270" y="60" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="83" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Cloud LoadBalancer</text>
  <text x="360" y="99" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">SAME interceptor, all three</text>

  <rect x="500" y="70" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Resolved instance</text>

  <line x1="200" y1="32" x2="268" y2="75" stroke="#8b949e" marker-end="url(#arr215)"/>
  <line x1="200" y1="77" x2="268" y2="90" stroke="#8b949e" marker-end="url(#arr215)"/>
  <line x1="200" y1="122" x2="268" y2="100" stroke="#8b949e" marker-end="url(#arr215)"/>
  <line x1="450" y1="90" x2="498" y2="90" stroke="#8b949e" marker-end="url(#arr215)"/>

  <defs>
    <marker id="arr215" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

All three client types funnel through the same load-balancer interception, whether the client itself blocks or not.

## 5. Runnable example

Scenario: a single "call the order service" scenario, implemented first with a blocking client style (mirroring `RestTemplate`/`RestClient`), then extended to a non-blocking, callback-based style (mirroring `WebClient`), and finally unified behind one interface so calling code doesn't care which style backs a particular client — mirroring how `@LoadBalanced` gives all three real Spring client types the same logical-name resolution regardless of their execution model.

### Level 1 — Basic

```java
// File: BlockingLoadBalancedCall.java -- mirrors @LoadBalanced RestTemplate /
// RestClient: the call BLOCKS the calling thread until a result is ready.
import java.util.*;

public class BlockingLoadBalancedCall {
    record ServiceInstance(String host, int port) {}
    static List<ServiceInstance> registry = List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));
    static int roundRobinIndex = 0;

    static String getForObject(String logicalPath) { // BLOCKS the caller until this returns
        ServiceInstance chosen = registry.get(roundRobinIndex++ % registry.size());
        return "response from " + chosen.host() + ":" + chosen.port() + logicalPath;
    }

    public static void main(String[] args) {
        String result = getForObject("/orders/42"); // caller's thread WAITS here
        System.out.println("Got (blocking): " + result);
    }
}
```

**How to run:** `javac BlockingLoadBalancedCall.java && java BlockingLoadBalancedCall` (JDK 17+).

### Level 2 — Intermediate

```java
// File: NonBlockingLoadBalancedCall.java -- mirrors @LoadBalanced WebClient:
// the SAME logical-name resolution, but the caller registers a callback
// instead of blocking, and the result arrives asynchronously.
import java.util.*;
import java.util.function.*;
import java.util.concurrent.*;

public class NonBlockingLoadBalancedCall {
    record ServiceInstance(String host, int port) {}
    static List<ServiceInstance> registry = List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));
    static int roundRobinIndex = 0;

    // returns IMMEDIATELY with a future; the caller does NOT block
    static CompletableFuture<String> getForObjectAsync(String logicalPath) {
        return CompletableFuture.supplyAsync(() -> {
            ServiceInstance chosen = registry.get(roundRobinIndex++ % registry.size());
            return "response from " + chosen.host() + ":" + chosen.port() + logicalPath;
        });
    }

    public static void main(String[] args) throws Exception {
        CompletableFuture<String> future = getForObjectAsync("/orders/42"); // NON-blocking call
        System.out.println("Call issued, NOT blocked -- doing other work now...");
        future.thenAccept(result -> System.out.println("Got (async callback): " + result)); // runs when ready
        future.get(); // ONLY so the demo waits before main() exits
    }
}
```

**How to run:** `javac NonBlockingLoadBalancedCall.java && java NonBlockingLoadBalancedCall` (JDK 17+).

Expected output:
```
Call issued, NOT blocked -- doing other work now...
Got (async callback): response from 10.0.1.5:8080/orders/42
```

### Level 3 — Advanced

```java
// File: UnifiedLoadBalancedClientInterface.java -- ONE interface, TWO
// implementations (blocking + non-blocking), demonstrating that calling
// code depends only on the shared "logical name in, result out" contract --
// exactly what @LoadBalanced gives RestTemplate/RestClient/WebClient alike.
import java.util.*;
import java.util.concurrent.*;

public class UnifiedLoadBalancedClientInterface {
    record ServiceInstance(String host, int port) {}
    static List<ServiceInstance> registry = List.of(new ServiceInstance("10.0.1.5", 8080), new ServiceInstance("10.0.1.6", 8080));

    interface LoadBalancedClient { CompletableFuture<String> call(String logicalPath); } // shared contract

    static class BlockingStyleClient implements LoadBalancedClient { // mirrors RestTemplate / RestClient
        int roundRobinIndex = 0;
        public CompletableFuture<String> call(String logicalPath) {
            ServiceInstance chosen = registry.get(roundRobinIndex++ % registry.size());
            return CompletableFuture.completedFuture("blocking-style: " + chosen.host() + ":" + chosen.port() + logicalPath);
        }
    }

    static class ReactiveStyleClient implements LoadBalancedClient { // mirrors WebClient
        int roundRobinIndex = 0;
        public CompletableFuture<String> call(String logicalPath) {
            return CompletableFuture.supplyAsync(() -> {
                ServiceInstance chosen = registry.get(roundRobinIndex++ % registry.size());
                return "reactive-style: " + chosen.host() + ":" + chosen.port() + logicalPath;
            });
        }
    }

    static void callAndReport(String label, LoadBalancedClient client) throws Exception {
        System.out.println(label + " -> " + client.call("/orders/42").get());
    }

    public static void main(String[] args) throws Exception {
        // calling code below treats BOTH client types identically -- same interface, same logical path
        callAndReport("RestTemplate/RestClient-style", new BlockingStyleClient());
        callAndReport("WebClient-style", new ReactiveStyleClient());
        System.out.println("Both client styles honored the SAME LoadBalancedClient contract -- calling code never needed to know which one it held.");
    }
}
```

**How to run:** `javac UnifiedLoadBalancedClientInterface.java && java UnifiedLoadBalancedClientInterface` (JDK 17+).

Expected output:
```
RestTemplate/RestClient-style -> blocking-style: 10.0.1.5:8080/orders/42
WebClient-style -> reactive-style: 10.0.1.5:8080/orders/42
Both client styles honored the SAME LoadBalancedClient contract -- calling code never needed to know which one it held.
```

## 6. Walkthrough

1. **Level 1, the blocking baseline** — `getForObject` selects an instance and returns a formatted result synchronously; `main`'s call to it does not proceed to the next line until the method returns, exactly mirroring how `@LoadBalanced RestTemplate.getForObject(...)` (and `RestClient`'s fluent, synchronous `.retrieve().body(...)`) block the calling thread.
2. **Level 2, the non-blocking shift** — `getForObjectAsync` wraps the identical selection logic inside `CompletableFuture.supplyAsync`, returning a `CompletableFuture<String>` immediately rather than the resolved string; `main` prints "doing other work now" *before* the result is available, demonstrating the caller was never blocked — this is the behavior `@LoadBalanced WebClient` gives through its reactive `Mono`/`Flux` return types.
3. **Level 2, callback registration** — `future.thenAccept(...)` registers a callback that runs only once the async computation completes, rather than `main` polling or waiting inline; the final `future.get()` call exists purely so the short demo program doesn't exit before the callback has a chance to run, not as part of the pattern being demonstrated.
4. **Level 3, unifying behind one contract** — `LoadBalancedClient` declares a single `call(String)` method returning `CompletableFuture<String>`, and both `BlockingStyleClient` (which completes its future immediately) and `ReactiveStyleClient` (which completes it asynchronously) implement that same contract.
5. **Level 3, calling code stays uniform** — `callAndReport` accepts any `LoadBalancedClient` and calls it identically regardless of which implementation was passed in; this mirrors how application code that calls `restTemplate.getForObject(...)`, `restClient.get()...`, or `webClient.get()...` all express "call this logical service name" using each client's own idiom, while `@LoadBalanced` handles the underlying resolution consistently in each case.
6. **Level 3, the output confirms uniform treatment** — both calls in `main` produce a correctly resolved instance address despite going through different implementations internally, showing that the *caller's* experience (logical name in, resolved-and-called result out) is what stays constant across `RestTemplate`, `RestClient`, and `WebClient` when each is `@LoadBalanced`.

## 7. Gotchas & takeaways

> **Gotcha:** `@LoadBalanced` is applied to the *builder* for `WebClient` and `RestClient` (`WebClient.Builder`, `RestClient.Builder`) but directly to the finished bean for `RestTemplate` — annotating a built `WebClient` or `RestClient` instance directly (instead of its builder) silently fails to activate load-balancing, a mistake that's easy to make when copying a `RestTemplate` example and adapting it to a different client type.

- `@LoadBalanced` provides the same logical-service-name resolution mechanism across `RestTemplate`, `WebClient`, and `RestClient`, differing only in how each client's execution model (blocking vs. reactive) surfaces the result.
- `RestTemplate` is in maintenance mode; `RestClient` (Spring 6.1+) is the newer, recommended choice for synchronous, fluent-style blocking calls, while `WebClient` remains the choice for reactive, non-blocking code.
- The annotation targets the *builder* bean for `WebClient` and `RestClient`, but the client bean itself for `RestTemplate` — mixing this up is a common source of "load balancing isn't working" confusion.
- Choosing between the three client types is primarily about matching the surrounding application's execution model (blocking Spring MVC vs. reactive WebFlux), not about differing load-balancing capability.
- Regardless of which client type is used, calling code addresses a logical service name and never performs discovery or instance selection itself — that responsibility stays inside the [Spring Cloud LoadBalancer](0202-spring-cloud-loadbalancer-using-the-registry.md) interception layer.
