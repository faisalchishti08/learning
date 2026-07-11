---
card: spring-cloud
gi: 55
slug: load-balancing-algorithms-round-robin-random
title: "Load balancing algorithms (round-robin, random)"
---

## 1. What it is

Spring Cloud LoadBalancer ships two built-in selection algorithms: `RoundRobinLoadBalancer` (the default — cycles through instances in order, one after another) and `RandomLoadBalancer` (picks uniformly at random from the candidate list on every call). Both implement the `ReactorLoadBalancer` interface from the previous card, so either can be plugged in without touching the supplier chain that feeds them instances.

```java
@Bean
ReactorLoadBalancer<ServiceInstance> randomLoadBalancer(
        Environment environment, LoadBalancerClientFactory factory) {
    String serviceId = environment.getProperty(LoadBalancerClientFactory.PROPERTY_NAME);
    return new RandomLoadBalancer(
            factory.getLazyProvider(serviceId, ServiceInstanceListSupplier.class), serviceId);
}
```

## 2. Why & when

Round-robin's appeal is predictability: with N instances, every one of them receives exactly one in every N calls, guaranteeing an even long-run distribution with zero randomness and trivially cheap state (just a counter). Random trades that guarantee for simplicity of a different kind — no shared mutable counter to coordinate across concurrent callers — and over a large enough number of calls, converges to roughly the same even distribution, just with more short-term variance.

Choose between them based on:

- Round-robin (the default, and usually the right choice) when even, predictable distribution matters and instance counts are relatively stable — the overwhelming majority of internal service-to-service traffic.
- Random when many independent, uncoordinated callers exist (many separate JVMs, each running their own LoadBalancer instance with its own counter) — round-robin's guarantee only holds *per caller*, so with many independent callers each starting their counter differently, random's simplicity can be just as effective in practice without any coordination concerns.
- Neither, in favor of a custom `ReactorLoadBalancer`, when the workload genuinely needs something more sophisticated — weighted balancing (covered conceptually via zone/hint-based balancing in the next card), least-connections, or response-time-aware selection.

## 3. Core concept

```
 RoundRobinLoadBalancer:
   counter starts at 0, increments on every call
   pick = instances[counter % instances.size()]
   -> deterministic cycle: instance 0, 1, 2, ..., N-1, 0, 1, 2, ...

 RandomLoadBalancer:
   pick = instances[random.nextInt(instances.size())]
   -> no state needed between calls, converges to even distribution over many calls
```

Both algorithms are stateless with respect to instance health or load — they only know the *count* of candidate instances, not anything about which one is currently least busy.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Round robin cycles deterministically through instances one after another while random picks uniformly and unpredictably from the same list on each call">
  <rect x="20" y="20" width="280" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Round Robin</text>
  <text x="160" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call 1-&gt;.1  call 2-&gt;.2  call 3-&gt;.3</text>
  <text x="160" y="76" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call 4-&gt;.1  call 5-&gt;.2  ...</text>

  <rect x="340" y="20" width="280" height="70" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Random</text>
  <text x="480" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call 1-&gt;.3  call 2-&gt;.1  call 3-&gt;.1</text>
  <text x="480" y="76" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">call 4-&gt;.2  call 5-&gt;.3  ...</text>

  <text x="320" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">both converge to roughly even distribution over MANY calls;</text>
  <text x="320" y="136" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">round robin guarantees it every N calls, random only in the long run</text>

  <defs><marker id="a55" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Round-robin's short-term distribution is exact; random's is only exact on average, given enough calls.

## 5. Runnable example

The scenario: compare round-robin and random distribution behavior for calls to `billing-service`'s three instances. Start with each algorithm implemented directly, then measure their distribution over many calls, then simulate concurrent callers to show round-robin's guarantee is per-caller, not global.

### Level 1 — Basic

Both algorithms implemented directly, side by side.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class LoadBalancingAlgorithmsLevel1 {
    static List<String> instances = List.of("10.0.2.1", "10.0.2.2", "10.0.2.3");

    static AtomicInteger rrCounter = new AtomicInteger(0);
    static String roundRobinPick() {
        return instances.get(rrCounter.getAndIncrement() % instances.size());
    }

    static Random random = new Random(7); // fixed seed for reproducible example output
    static String randomPick() {
        return instances.get(random.nextInt(instances.size()));
    }

    public static void main(String[] args) {
        System.out.println("round robin: ");
        for (int i = 0; i < 6; i++) System.out.print(roundRobinPick() + " ");
        System.out.println();

        System.out.println("random: ");
        for (int i = 0; i < 6; i++) System.out.print(randomPick() + " ");
        System.out.println();
    }
}
```

How to run: `java LoadBalancingAlgorithmsLevel1.java`

Round-robin's output is a strict repeating cycle; random's output (even with a fixed seed for reproducibility here) has no guaranteed pattern call-to-call — this is the fundamental behavioral difference between the two.

### Level 2 — Intermediate

Measure the actual distribution of each algorithm over many calls, confirming both converge to roughly even coverage.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class LoadBalancingAlgorithmsLevel2 {
    static List<String> instances = List.of("10.0.2.1", "10.0.2.2", "10.0.2.3");

    static AtomicInteger rrCounter = new AtomicInteger(0);
    static String roundRobinPick() { return instances.get(rrCounter.getAndIncrement() % instances.size()); }

    static Random random = new Random(7);
    static String randomPick() { return instances.get(random.nextInt(instances.size())); }

    static Map<String, Integer> distribution(int calls, java.util.function.Supplier<String> picker) {
        Map<String, Integer> counts = new TreeMap<>();
        for (int i = 0; i < calls; i++) counts.merge(picker.get(), 1, Integer::sum);
        return counts;
    }

    public static void main(String[] args) {
        int calls = 3000;
        System.out.println("round robin over " + calls + " calls: " + distribution(calls, LoadBalancingAlgorithmsLevel2::roundRobinPick));
        System.out.println("random over " + calls + " calls:      " + distribution(calls, LoadBalancingAlgorithmsLevel2::randomPick));
    }
}
```

How to run: `java LoadBalancingAlgorithmsLevel2.java`

With 3000 calls across 3 instances, round-robin produces *exactly* 1000 calls to each instance (a mathematical guarantee, since 3000 is evenly divisible by 3), while random produces something close to 1000 each but not identical — typically within a couple percent, the expected statistical variance of independent random draws. Over a small number of calls this variance would be much more pronounced; at this scale it's already converging tightly.

### Level 3 — Advanced

Simulate multiple concurrent, independent callers (each modeling a separate JVM instance calling `billing-service`, each with its own `LoadBalancer` and thus its own counter) to show round-robin's guarantee is per-caller, not fleet-wide — a subtlety worth understanding before assuming round-robin alone guarantees perfectly even load across a whole fleet of callers.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class LoadBalancingAlgorithmsLevel3 {
    static List<String> instances = List.of("10.0.2.1", "10.0.2.2", "10.0.2.3");

    // each "caller" is a separate JVM with its OWN independent round-robin counter
    static class Caller {
        AtomicInteger counter = new AtomicInteger(0);
        String pick() { return instances.get(counter.getAndIncrement() % instances.size()); }
    }

    public static void main(String[] args) {
        Caller callerA = new Caller();
        Caller callerB = new Caller();
        Caller callerC = new Caller();

        // each caller happens to only make ONE call in this snapshot -- e.g. right after all three just started up
        Map<String, Integer> hits = new TreeMap<>();
        for (Caller c : List.of(callerA, callerB, callerC)) {
            String picked = c.pick();
            hits.merge(picked, 1, Integer::sum);
        }

        System.out.println("hits from 3 independent callers' FIRST call each: " + hits);
        // every independent caller's counter starts at 0 -- they can all pick the SAME first instance!
    }
}
```

How to run: `java LoadBalancingAlgorithmsLevel3.java`

Because `callerA`, `callerB`, and `callerC` each maintain their *own* independent counter starting at `0`, their first call each resolves to `instances.get(0)` — the same instance, `10.0.2.1`, for all three. Round-robin's even-distribution guarantee only holds within a single caller's own sequence of calls over time; it says nothing about coordination *across* multiple independent callers, especially right after a synchronized startup (many instances of the same calling service deploying at once) where every caller's counter happens to start from the same state.

## 6. Walkthrough

Trace Level 3's execution.

1. Three independent `Caller` objects are created, each with its own `AtomicInteger counter` starting at `0` — this models three separate running instances of, say, `orders-service`, each independently calling `billing-service` and each running its own in-process `LoadBalancer` with its own state, since LoadBalancer state isn't shared across JVMs.
2. The loop calls `c.pick()` once for each caller, in order `callerA`, `callerB`, `callerC`. Each call to `pick()` reads its *own* `counter`, currently `0` for all three, computes `instances.get(0 % 3 = 0)`, which is `10.0.2.1` — the very first instance in the list — and then increments that caller's own counter.
3. Because all three callers happen to be making their first-ever call at this snapshot, all three independently land on the exact same instance, `10.0.2.1` — the `hits` map ends up `{10.0.2.1=3}`, not the evenly-spread `{10.0.2.1=1, 10.0.2.2=1, 10.0.2.3=1}` someone might naively expect from "round-robin load balancing."
4. This is not a bug — it's the direct, correct consequence of each caller's round-robin state being local to that caller. Over time, as each caller continues making more calls, each one's *own* traffic evenly distributes; but at any given instant, especially right after correlated startup events, momentary skew like this is expected and normal.

```
callerA.counter=0 -> pick .1 -> counter becomes 1
callerB.counter=0 -> pick .1 -> counter becomes 1   (independent counter, also starts at 0)
callerC.counter=0 -> pick .1 -> counter becomes 1   (same)

hits: {.1: 3, .2: 0, .3: 0}   <- all three callers' first calls landed on the same instance
```

## 7. Gotchas & takeaways

> **Gotcha:** round-robin's "every instance gets an even share" guarantee is per-caller, not fleet-wide — if many independent caller instances restart simultaneously (a coordinated rolling deploy, a scale-out event), their round-robin counters can all reset to the same starting point and momentarily correlate their picks, producing a brief, real load spike on whichever instance happens to be first in each caller's list. This tends to smooth out quickly as calls continue, but it's worth being aware of for latency-sensitive systems right after a synchronized deploy.

- Round-robin gives an exact, guaranteed distribution *within one caller's own sequence of calls*; random gives an approximate distribution that only converges with enough calls, but has no correlated-startup skew risk since each pick is independent of the others.
- Neither algorithm considers instance health, current load, or response time — they only know how many candidate instances exist, having already been filtered by whatever `ServiceInstanceListSupplier` chain fed them (the previous card).
- The default is round-robin, and it's the right choice for the overwhelming majority of workloads — reach for random or a custom algorithm only when there's a specific, understood reason to.
- Understanding that LoadBalancer state is per-JVM-instance (not centrally coordinated) explains a class of "why isn't load actually even across my fleet" questions that a purely algorithmic view of round-robin doesn't answer.
