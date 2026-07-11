---
card: spring-cloud
gi: 63
slug: feign-loadbalancer
title: "Feign + LoadBalancer"
---

## 1. What it is

Feign clients integrate with Spring Cloud LoadBalancer automatically — the `name` given in `@FeignClient(name = "billing-service")` is resolved through exactly the same discovery-and-select pipeline covered across the earlier LoadBalancer cards, meaning everything already learned there (round-robin/random selection, zone/hint filtering, caching, retry) applies transparently to Feign calls with zero additional configuration.

```java
@FeignClient(name = "billing-service") // this name IS the service name LoadBalancer resolves
public interface BillingClient {
    @GetMapping("/invoices/{id}")
    Invoice getInvoice(@PathVariable String id);
}
```

```
billingClient.getInvoice("42")
    -> Feign builds a request to "http://billing-service/invoices/42"
    -> LoadBalancer resolves "billing-service" to a live instance (round-robin, zone-aware, etc.)
    -> the actual HTTP call goes to that resolved instance
```

## 2. Why & when

This card exists to make explicit what earlier cards left implicit: Feign is not a separate, competing mechanism from `@LoadBalanced RestTemplate`/`WebClient` — it's built directly on top of the same LoadBalancer infrastructure. Understanding this means every LoadBalancer concept (algorithms, zone/hint filtering, caching, retry) is *one* shared mental model across every way of calling another service, not three separate systems to learn independently.

This matters concretely when:

- Debugging Feign call behavior — an unevenly distributed load across instances, or a request landing in the wrong zone, is exactly the same LoadBalancer configuration surface covered earlier, not a Feign-specific concept to learn separately.
- Configuring retry, zone preference, or a custom load-balancing algorithm for Feign calls — all the `spring.cloud.loadbalancer.*` properties from earlier cards apply directly, with no Feign-specific equivalent needed.
- Choosing between Feign and `@LoadBalanced RestTemplate`/`WebClient` for a given call site — the choice is really about calling *style* (declarative interface vs. imperative client calls), since the underlying load-balanced resolution behavior is identical either way.

## 3. Core concept

```
 @FeignClient(name = "billing-service")   @LoadBalanced RestTemplate.getForObject("http://billing-service/...")
              |                                              |
              +------------------  BOTH  --------------------+
                                    |
                          resolve "billing-service" through
                          the SAME Spring Cloud LoadBalancer pipeline
                                    |
              ServiceInstanceListSupplier chain (discovery, health, zone, hint filters)
                                    |
              ReactorLoadBalancer (round-robin / random / custom)
                                    |
                          chosen instance's real address
```

Two different calling styles, one shared underlying resolution mechanism — nothing about load balancing itself differs between them.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Both a Feign client call and a LoadBalanced RestTemplate call for the same service name funnel through the identical shared LoadBalancer instance before a real request is sent">
  <rect x="20" y="20" width="230" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="135" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Feign: billingClient.getInvoice(id)</text>

  <rect x="390" y="20" width="230" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="505" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">RestTemplate.getForObject(...)</text>

  <line x1="135" y1="60" x2="290" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a63)"/>
  <line x1="505" y1="60" x2="350" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a63)"/>

  <rect x="220" y="105" width="200" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="127" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">shared LoadBalancer</text>
  <text x="320" y="143" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">same instance, same state</text>

  <line x1="320" y1="155" x2="320" y2="180" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a63)"/>
  <text x="320" y="188" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">one resolved instance address, sent to whichever client made the call</text>

  <defs><marker id="a63" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two different call sites converge on one shared LoadBalancer instance — the resolution logic and its state are identical regardless of which client style triggered the call.

## 5. Runnable example

The scenario: confirm Feign-style and RestTemplate-style calls to `billing-service` resolve through the identical shared LoadBalancer state. Start with each modeled separately (appearing independent), then unify them behind one shared LoadBalancer, then add zone-aware filtering and confirm both calling styles respect it identically.

### Level 1 — Basic

Feign-style and RestTemplate-style calls modeled with separate, independent instance-selection logic — the misconception this card corrects.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class FeignLoadBalancerLevel1 {
    static List<String> instances = List.of("10.0.2.1:8080", "10.0.2.2:8080");

    static AtomicInteger feignCounter = new AtomicInteger(0); // WRONG model: separate counter per calling style
    static String feignStyleCall(String path) {
        return "GET http://" + instances.get(feignCounter.getAndIncrement() % instances.size()) + path;
    }

    static AtomicInteger restTemplateCounter = new AtomicInteger(0); // a second, independent counter
    static String restTemplateStyleCall(String path) {
        return "GET http://" + instances.get(restTemplateCounter.getAndIncrement() % instances.size()) + path;
    }

    public static void main(String[] args) {
        System.out.println(feignStyleCall("/invoices/1"));       // .1
        System.out.println(restTemplateStyleCall("/invoices/2")); // ALSO .1 -- because it has its OWN separate counter
        System.out.println(feignStyleCall("/invoices/3"));       // .2
    }
}
```

How to run: `java FeignLoadBalancerLevel1.java`

Two separate counters mean the two calling styles don't actually coordinate their round-robin state with each other — this is the *wrong* mental model; in reality, both styles share the exact same underlying LoadBalancer state for a given service.

### Level 2 — Intermediate

Unify both calling styles behind one shared LoadBalancer, correctly modeling that Feign and `@LoadBalanced RestTemplate` resolve through the identical underlying mechanism.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class FeignLoadBalancerLevel2 {
    static List<String> instances = List.of("10.0.2.1:8080", "10.0.2.2:8080");

    static class SharedLoadBalancer { // ONE instance, shared by every calling style
        AtomicInteger counter = new AtomicInteger(0);
        String choose() { return instances.get(counter.getAndIncrement() % instances.size()); }
    }

    static SharedLoadBalancer loadBalancer = new SharedLoadBalancer(); // registered once per service, in a real app

    static String feignStyleCall(String path) {
        return "GET http://" + loadBalancer.choose() + path;
    }

    static String restTemplateStyleCall(String path) {
        return "GET http://" + loadBalancer.choose() + path; // uses the SAME shared instance
    }

    public static void main(String[] args) {
        System.out.println(feignStyleCall("/invoices/1"));        // .1
        System.out.println(restTemplateStyleCall("/invoices/2")); // .2 -- correctly continues the SAME rotation
        System.out.println(feignStyleCall("/invoices/3"));        // .1 again -- wraps correctly
    }
}
```

How to run: `java FeignLoadBalancerLevel2.java`

Both `feignStyleCall` and `restTemplateStyleCall` now call `loadBalancer.choose()` on the *same shared* `SharedLoadBalancer` instance — exactly the correct model of how Spring Cloud LoadBalancer actually works: one `ReactorLoadBalancer` bean per service name, resolved identically regardless of whether the calling code happens to be a Feign client or an `@LoadBalanced RestTemplate`. The round-robin rotation correctly continues seamlessly across both calling styles.

### Level 3 — Advanced

Add zone-aware filtering (from the earlier zone-based balancing card) on top of the shared LoadBalancer, confirming both calling styles respect the exact same filtered candidate list.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class FeignLoadBalancerLevel3 {
    record Instance(String address, String zone) {}

    static List<Instance> allInstances = List.of(
            new Instance("10.0.2.1:8080", "us-east-1a"),
            new Instance("10.0.2.2:8080", "us-east-1a"),
            new Instance("10.0.2.3:8080", "us-east-1b")
    );

    static class SharedLoadBalancer {
        String callerZone;
        AtomicInteger counter = new AtomicInteger(0);
        SharedLoadBalancer(String callerZone) { this.callerZone = callerZone; }

        String choose() {
            List<Instance> sameZone = allInstances.stream()
                    .filter(i -> i.zone().equals(callerZone)).collect(Collectors.toList());
            List<Instance> candidates = sameZone.isEmpty() ? allInstances : sameZone;
            return candidates.get(counter.getAndIncrement() % candidates.size()).address();
        }
    }

    static SharedLoadBalancer loadBalancer = new SharedLoadBalancer("us-east-1a");

    static String feignStyleCall(String path) { return "GET http://" + loadBalancer.choose() + path; }
    static String restTemplateStyleCall(String path) { return "GET http://" + loadBalancer.choose() + path; }
    static String webClientStyleCall(String path) { return "GET http://" + loadBalancer.choose() + path; }

    public static void main(String[] args) {
        System.out.println(feignStyleCall("/invoices/1"));
        System.out.println(restTemplateStyleCall("/invoices/2"));
        System.out.println(webClientStyleCall("/invoices/3"));
        System.out.println(feignStyleCall("/invoices/4"));
        // .3 (zone b) should NEVER appear -- zone filtering applies identically no matter which calling style asks
    }
}
```

How to run: `java FeignLoadBalancerLevel3.java`

All three calling styles — Feign, `RestTemplate`, `WebClient` — go through `loadBalancer.choose()`, which applies zone filtering *before* round-robin selection, exactly as the earlier zone-based balancing card modeled. Across all four calls, only `.1` and `.2` (both `us-east-1a`) ever appear; `.3` (zone `us-east-1b`) is filtered out identically for every calling style, because the filtering logic lives in the shared LoadBalancer, completely independent of which client API initiated the call.

## 6. Walkthrough

Trace the four calls in Level 3.

1. `feignStyleCall("/invoices/1")` runs first — it calls `loadBalancer.choose()`, which computes `sameZone` (filtering `allInstances` to `zone.equals("us-east-1a")`), yielding `[.1, .2]`. Since this isn't empty, `candidates = sameZone`. The counter reads `0`, picks `candidates.get(0 % 2 = 0)` = `.1`, and increments to `1`.
2. `restTemplateStyleCall("/invoices/2")` runs next — it calls the *exact same* `loadBalancer.choose()` method on the *exact same* `loadBalancer` instance. The zone filtering recomputes identically (same `allInstances`, same `callerZone`), yielding the same `[.1, .2]` candidate list. The counter, now `1` (carried over from the previous call, since it's shared state), picks `candidates.get(1 % 2 = 1)` = `.2`, and increments to `2`.
3. `webClientStyleCall("/invoices/3")` runs — same shared `loadBalancer`, same filtering, counter now `2`, picks `candidates.get(2 % 2 = 0)` = `.1` again, wrapping the rotation correctly. Increments to `3`.
4. `feignStyleCall("/invoices/4")` runs — counter `3`, picks `candidates.get(3 % 2 = 1)` = `.2`. Increments to `4`.
5. Across all four calls, spanning three different "calling styles," the rotation is a clean, uninterrupted `.1, .2, .1, .2` — exactly what a single shared round-robin counter over a two-instance zone-filtered candidate list produces, regardless of which client API happened to trigger each individual call. `.3` never appears at all, confirming the zone filter applies uniformly.

```
loadBalancer.choose() called by: Feign, RestTemplate, WebClient, Feign (in that order)
shared counter:  0 -> 1 -> 2 -> 3
candidates (after zone filter, same every time): [.1, .2]
picks:           .1 -> .2 -> .1 -> .2
   (.3, zone us-east-1b, never selected -- filtered out identically for every calling style)
```

## 7. Gotchas & takeaways

> **Gotcha:** because Feign and `@LoadBalanced` clients share the same underlying LoadBalancer state per service name, load-balancing behavior configured for one calling style (a custom algorithm, zone preference, retry settings) automatically applies to every other calling style used for the same service in the same application — this is usually exactly what you want, but it means there's no way to give a Feign client different load-balancing behavior than a `RestTemplate` call to the identical service within one application without more advanced per-client LoadBalancer configuration.

- Feign is not a separate load-balancing system — it's a different, declarative way of expressing HTTP calls that happens to resolve service names through the identical Spring Cloud LoadBalancer pipeline as every other client style.
- Every concept from the earlier LoadBalancer cards — round-robin/random algorithms, zone/hint-based filtering, caching, retry — applies to Feign calls automatically, with zero Feign-specific configuration needed for any of it.
- When debugging Feign call distribution or routing, the mental model to reach for is exactly the LoadBalancer pipeline (supplier chain, then selection algorithm) covered in the earlier cards — not a separate, Feign-specific mechanism.
- Choosing between Feign and `@LoadBalanced RestTemplate`/`WebClient` is purely a decision about calling *ergonomics* (declarative interface vs. imperative calls) — it has no bearing on load-balancing behavior itself, which is identical either way.
