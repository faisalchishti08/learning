---
card: microservices
gi: 213
slug: reactorloadbalancer-abstraction
title: "ReactorLoadBalancer abstraction"
---

## 1. What it is

`ReactorLoadBalancer<T>` is the reactive interface Spring Cloud LoadBalancer's implementations (including the default `RoundRobinLoadBalancer`) are built against — its `choose` method returns a `Mono<Response<T>>` rather than a plain `T`, meaning the instance-selection step itself is a non-blocking, reactive operation, consistent with [Spring Cloud Gateway](0171-spring-cloud-gateway-reactive-webflux-based)'s broader reactive foundation and able to incorporate genuinely asynchronous selection logic (an async health check, an external call needed to decide) without blocking a thread while doing so.

## 2. Why & when

A load-balancing decision that's always a simple, synchronous computation (like plain round-robin) doesn't strictly need to be reactive — but a more sophisticated selection strategy might genuinely need to perform I/O as part of deciding (querying a real-time metrics endpoint for current instance load, checking a distributed cache for recent latency data), and if the interface only supported synchronous, blocking selection, that I/O would have to block a thread during the decision itself, undermining the non-blocking guarantees the rest of a reactive gateway or service is built around. `ReactorLoadBalancer<T>` exists specifically to keep the selection step composable with the rest of a reactive call chain, whether the actual selection logic happens to be instant or genuinely asynchronous.

Implement `ReactorLoadBalancer<T>` directly when building a custom load-balancing strategy for a reactive Spring application, particularly one whose selection logic might need to perform asynchronous work. For simple synchronous selection logic, the interface's reactive wrapper (`Mono.just(...)`) is a thin, low-overhead formality — the value is in supporting the cases where selection genuinely needs to be asynchronous, without requiring a different interface for that case.

## 3. Core concept

`ReactorLoadBalancer<T>`'s `choose` method returns `Mono<Response<T>>`; a synchronous selection strategy simply wraps its immediate result in `Mono.just(...)`, while a genuinely asynchronous strategy can compose real reactive operators (`flatMap`, chained async calls) to arrive at its answer, and both integrate identically with the surrounding reactive call chain that ultimately uses the selected instance.

```java
public interface ReactorLoadBalancer<T> {
    Mono<Response<T>> choose(Request request);
}

// SYNCHRONOUS strategy: instant answer, wrapped in Mono.just
class RoundRobinLoadBalancer implements ReactorLoadBalancer<ServiceInstance> {
    public Mono<Response<ServiceInstance>> choose(Request request) {
        ServiceInstance chosen = instances.get(index++ % instances.size());
        return Mono.just(new Response<>(chosen)); // NO real async work, just wrapped
    }
}

// ASYNCHRONOUS strategy: genuinely non-blocking I/O as PART of the decision
class LatencyAwareLoadBalancer implements ReactorLoadBalancer<ServiceInstance> {
    public Mono<Response<ServiceInstance>> choose(Request request) {
        return metricsClient.getLatencies() // a REAL async call
            .map(latencies -> pickLowestLatency(latencies))
            .map(Response::new);
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A synchronous selection strategy wraps its instant result in Mono.just with no real asynchronous work. An asynchronous strategy composes a genuine async call, like fetching current latency metrics, before arriving at its selection. Both return the same Mono type and compose identically into the surrounding reactive chain" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Synchronous strategy</text>
  <rect x="30" y="40" width="240" height="40" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">choose() -&gt; Mono.just(instant result)</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Asynchronous strategy</text>
  <rect x="360" y="40" width="240" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">choose() -&gt; async fetch -&gt; map</text>
  <text x="480" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; Response</text>

  <text x="320" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">both return the SAME Mono&lt;Response&lt;T&gt;&gt; type -- compose identically downstream</text>
</svg>

Both selection styles produce the identical reactive type, composing seamlessly regardless of internal complexity.

## 5. Runnable example

Scenario: a Spring-style reactive call chain that starts with a synchronous-only selection interface (unable to support genuinely async selection logic), refactors to a `ReactorLoadBalancer`-style reactive interface where both synchronous and asynchronous strategies implement the identical contract, and finally demonstrates a genuinely asynchronous, metrics-based selection strategy composing cleanly into the same reactive chain as the simple synchronous one, using simulated reactive operations.

### Level 1 — Basic

```java
// File: SynchronousOnlyInterface.java -- a PLAIN synchronous interface;
// CANNOT accommodate a selection strategy needing genuine async I/O.
import java.util.*;

public class SynchronousOnlyInterface {
    record ServiceInstance(String id) {}
    interface SyncLoadBalancer { ServiceInstance choose(); } // BLOCKING return type -- no room for async work

    static class RoundRobinSync implements SyncLoadBalancer {
        List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"));
        int index = 0;
        public ServiceInstance choose() { return instances.get(index++ % instances.size()); } // fine, SYNCHRONOUS is enough here
    }

    public static void main(String[] args) {
        SyncLoadBalancer balancer = new RoundRobinSync();
        System.out.println("Chose: " + balancer.choose());
        System.out.println("This interface WORKS for simple round-robin, but has NO way to express 'fetch real-time metrics FIRST, THEN decide' without BLOCKING a thread during that fetch.");
    }
}
```

**How to run:** `javac SynchronousOnlyInterface.java && java SynchronousOnlyInterface` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ReactiveInterfaceBothStrategies.java -- a REACTIVE-style interface
// (simulated Mono) that BOTH a synchronous AND an asynchronous strategy can implement IDENTICALLY.
import java.util.*;
import java.util.function.*;

public class ReactiveInterfaceBothStrategies {
    record ServiceInstance(String id) {}

    // a MINIMAL simulated "Mono" -- represents an eventual, possibly-async result
    static class SimulatedMono<T> {
        T value;
        SimulatedMono(T value) { this.value = value; }
        static <T> SimulatedMono<T> just(T value) { return new SimulatedMono<>(value); } // WRAPS an instant value
        <R> SimulatedMono<R> map(Function<T, R> mapper) { return new SimulatedMono<>(mapper.apply(value)); }
        T block() { return value; } // for DEMO purposes only -- real reactive code never actually blocks like this
    }

    interface ReactiveLoadBalancer { SimulatedMono<ServiceInstance> choose(); } // the REACTIVE contract, mirroring ReactorLoadBalancer

    static class RoundRobinReactive implements ReactiveLoadBalancer {
        List<ServiceInstance> instances = List.of(new ServiceInstance("order-a"), new ServiceInstance("order-b"));
        int index = 0;
        public SimulatedMono<ServiceInstance> choose() {
            ServiceInstance chosen = instances.get(index++ % instances.size());
            return SimulatedMono.just(chosen); // SYNCHRONOUS logic, WRAPPED in the reactive type
        }
    }

    public static void main(String[] args) {
        ReactiveLoadBalancer balancer = new RoundRobinReactive();
        System.out.println("Chose (via reactive interface): " + balancer.choose().block());
        System.out.println("SAME synchronous logic, but NOW expressed through a REACTIVE-COMPATIBLE interface -- composable with async strategies too.");
    }
}
```

**How to run:** `javac ReactiveInterfaceBothStrategies.java && java ReactiveInterfaceBothStrategies` (JDK 17+).

Expected output:
```
Chose (via reactive interface): ServiceInstance[id=order-a]
SAME synchronous logic, but NOW expressed through a REACTIVE-COMPATIBLE interface -- composable with async strategies too.
```

### Level 3 — Advanced

```java
// File: AsyncMetricsBasedStrategy.java -- a GENUINELY asynchronous selection
// strategy, composing a SIMULATED async metrics fetch BEFORE deciding -- the
// SAME reactive contract as the synchronous strategy, just with REAL async work inside.
import java.util.*;
import java.util.function.*;

public class AsyncMetricsBasedStrategy {
    record ServiceInstance(String id) {}

    static class SimulatedMono<T> {
        T value;
        SimulatedMono(T value) { this.value = value; }
        static <T> SimulatedMono<T> just(T value) { return new SimulatedMono<>(value); }
        <R> SimulatedMono<R> map(Function<T, R> mapper) { return new SimulatedMono<>(mapper.apply(value)); }
        T block() { return value; }
    }

    interface ReactiveLoadBalancer { SimulatedMono<ServiceInstance> choose(); }

    // simulates an ASYNCHRONOUS metrics client -- in a REAL system, this would be a genuine non-blocking network call
    static class MetricsClient {
        SimulatedMono<Map<String, Double>> getLatencies() {
            System.out.println("  [metrics client] fetching CURRENT latency data (simulated async I/O)...");
            return SimulatedMono.just(Map.of("order-a", 45.0, "order-b", 12.0, "order-c", 30.0));
        }
    }

    static class LatencyAwareReactive implements ReactiveLoadBalancer {
        MetricsClient metricsClient = new MetricsClient();
        public SimulatedMono<ServiceInstance> choose() {
            return metricsClient.getLatencies() // GENUINE async step, part of the DECISION itself
                .map(latencies -> {
                    String lowestLatencyId = latencies.entrySet().stream()
                        .min(Map.Entry.comparingByValue()).map(Map.Entry::getKey).orElseThrow();
                    System.out.println("  [balancer] picked " + lowestLatencyId + " based on FETCHED latency data: " + latencies);
                    return new ServiceInstance(lowestLatencyId);
                });
        }
    }

    public static void main(String[] args) {
        ReactiveLoadBalancer syncBalancer = () -> SimulatedMono.just(new ServiceInstance("order-a")); // trivial sync strategy
        ReactiveLoadBalancer asyncBalancer = new LatencyAwareReactive(); // genuinely async strategy

        System.out.println("Sync strategy result:  " + syncBalancer.choose().block());
        System.out.println("Async strategy result: " + asyncBalancer.choose().block());
        System.out.println("\nBOTH implement the IDENTICAL ReactiveLoadBalancer contract -- the caller doesn't need to know or care WHICH one involves real async work internally.");
    }
}
```

**How to run:** `javac AsyncMetricsBasedStrategy.java && java AsyncMetricsBasedStrategy` (JDK 17+).

Expected output:
```
Sync strategy result:  ServiceInstance[id=order-a]
  [metrics client] fetching CURRENT latency data (simulated async I/O)...
  [balancer] picked order-b based on FETCHED latency data: {order-a=45.0, order-b=12.0, order-c=30.0}
Async strategy result: ServiceInstance[id=order-b]

BOTH implement the IDENTICAL ReactiveLoadBalancer contract -- the caller doesn't need to know or care WHICH one involves real async work internally.
```

## 6. Walkthrough

1. **Level 1** — `SyncLoadBalancer.choose()` returns a plain `ServiceInstance` directly; this works fine for `RoundRobinSync`'s instant computation, but the comment makes explicit that this interface shape has no way to express "fetch data asynchronously, then decide" without that fetch blocking the calling thread.
2. **Level 2, the reactive-shaped interface** — `ReactiveLoadBalancer.choose()` returns `SimulatedMono<ServiceInstance>` (standing in for the real `Mono<Response<T>>`), and `RoundRobinReactive.choose()` implements this by computing its result instantly and wrapping it via `SimulatedMono.just(chosen)`.
3. **Level 2, the formality of wrapping a synchronous result** — no genuine asynchronous work happens inside `RoundRobinReactive.choose()`; the reactive wrapper is a thin, low-overhead formality here, exactly as the "why & when" section describes for simple synchronous selection logic.
4. **Level 3, a metrics client representing genuine async I/O** — `MetricsClient.getLatencies()` prints a message indicating simulated async I/O and returns a `SimulatedMono` wrapping fetched data, standing in for a real non-blocking network call to a metrics service.
5. **Level 3, composing the async step into the decision** — `LatencyAwareReactive.choose()` calls `metricsClient.getLatencies()` and chains a `.map(...)` transforming the fetched latency data into a selected `ServiceInstance`, meaning the actual instance-selection decision is *derived from* the result of a genuinely asynchronous operation, composed using the same reactive chaining style real Reactor code would use.
6. **Level 3, both strategies satisfying the identical interface** — `syncBalancer` (a trivial lambda wrapping an instant value) and `asyncBalancer` (an instance of `LatencyAwareReactive`) are both typed as `ReactiveLoadBalancer`, and `main` calls `.choose()` on each identically, despite one doing zero async work and the other genuinely fetching and processing external data as part of its decision.
7. **Level 3, the payoff for the calling code** — the final printed comment states the core benefit directly: code that ultimately consumes the result of `choose()` never needs to know or care whether the specific implementation behind the interface did trivial, instant work or genuine asynchronous I/O — both compose identically into a larger reactive call chain, which is exactly the flexibility `ReactorLoadBalancer<T>`'s reactive return type provides over a plain synchronous interface that could only ever accommodate the simple case.

## 7. Gotchas & takeaways

> **Gotcha:** an asynchronous selection strategy adds real latency to every single request's routing decision (the time needed to fetch whatever data the strategy depends on) — this cost needs to be weighed against the benefit the additional data provides; a metrics-based strategy that queries a slow external metrics service on every single selection can end up adding more latency through its own decision-making overhead than it saves through smarter routing, unless that metrics data is itself cached or refreshed on a reasonable interval rather than fetched fresh per call.

- `ReactorLoadBalancer<T>` is the reactive interface Spring Cloud LoadBalancer's implementations are built against, with `choose` returning `Mono<Response<T>>` rather than a plain synchronous value.
- This lets both trivial synchronous selection logic and genuinely asynchronous selection logic (needing to perform I/O as part of the decision) implement the identical contract, composing seamlessly into a larger reactive call chain either way.
- A synchronous strategy simply wraps its instant result in `Mono.just(...)`, incurring negligible overhead from the reactive wrapper itself.
- An asynchronous strategy can genuinely chain real reactive operators, incorporating fetched external data (like real-time metrics) directly into its selection decision without blocking a thread.
- Asynchronous selection strategies add real per-request latency from their own data-fetching step, a cost that needs to be weighed against the routing quality improvement that data provides, and often mitigated by caching or periodic refresh rather than fetching fresh on every single call.
