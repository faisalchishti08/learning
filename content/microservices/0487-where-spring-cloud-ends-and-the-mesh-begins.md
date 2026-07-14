---
card: microservices
gi: 487
slug: where-spring-cloud-ends-and-the-mesh-begins
title: "Where Spring Cloud ends and the mesh begins"
---

## 1. What it is

When a Spring Cloud microservices system adopts a service mesh, several capabilities Spring Cloud traditionally provided at the **application layer** — client-side load balancing, retries, circuit breaking, mTLS — become **redundant** with what the mesh now provides at the **infrastructure layer**. Deciding "where Spring Cloud ends and the mesh begins" means deliberately choosing, for each overlapping capability, which layer actually owns it, rather than running both simultaneously and uncoordinated.

## 2. Why & when

You need to draw this line explicitly whenever a Spring Cloud system is deployed into a mesh-enabled Kubernetes cluster, because several concerns genuinely overlap:

- **Running the same resiliency policy at both layers can compound unpredictably.** A Spring Cloud client retrying 3 times, wrapping a mesh-level proxy that also retries 3 times, can turn one logical failure into up to 9 actual attempts against an already-struggling downstream — worse than either layer alone.
- **Client-side load balancing becomes redundant once [mesh-level traffic management](0480-traffic-management-routing-splitting-mirroring.md) is present.** Spring Cloud's client-side load balancer picks an instance from a discovered list; a mesh's [sidecar proxy](0479-sidecar-proxy-envoy.md) already does exactly this, transparently, for every call — running both means duplicated logic making potentially conflicting decisions.
- **[Mesh-level mTLS](0482-mesh-level-mtls-security.md) makes application-configured TLS for internal service-to-service calls largely redundant** — the mesh already encrypts and authenticates every hop; application-level TLS configuration for the same internal calls adds complexity without adding real additional security.
- **You draw this line explicitly at mesh adoption time, service by service if needed** — not by leaving every existing Spring Cloud mechanism untouched and just adding a mesh on top, which is precisely the uncoordinated overlap that causes problems.

## 3. Core concept

Think of a company that has both an internal security team providing building-wide access control, and individual departments that each used to run their own separate door locks before the building-wide system existed — once the building-wide system is in place, keeping every department's old separate lock still active doesn't add security, it just adds confusion about which system is actually in charge of any given door, and occasionally the two systems disagree about who should be let in.

Concretely, the typical division of responsibility once a mesh is adopted:

1. **Service discovery**: Spring Cloud's `DiscoveryClient` can be backed by Kubernetes directly (via [Spring Cloud Kubernetes](0474-spring-cloud-kubernetes-integration.md)) or effectively superseded, since the mesh's sidecars already route to healthy instances transparently — many teams simplify to calling a Kubernetes Service name directly and letting the mesh handle the rest.
2. **Client-side load balancing**: typically disabled or removed once mesh-level load balancing is active, since the mesh's proxy is already making this decision on every call.
3. **Retries, timeouts, circuit breaking**: the baseline, uniform policy moves to the mesh; application-level ([Resilience4j](0484-service-mesh-vs-library-based-resiliency-resilience4j.md)) logic is kept specifically for cases needing business-aware fallback behavior, not duplicated generic retry policy.
4. **mTLS**: application-level TLS configuration for internal service-to-service calls is typically removed entirely, since the mesh already provides stronger, centrally-managed mTLS for every hop.
5. **What Spring Cloud keeps doing regardless**: application-level configuration management, business logic, and any Spring-specific integration (like `@ConfigurationProperties` binding) — the mesh has no opinion about, or ability to affect, these.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A table showing which resiliency concerns move from Spring Cloud to the mesh, and which stay owned by Spring Cloud" >
  <rect x="20" y="20" width="300" height="170" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="170" y="42" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">moves to the MESH</text>
  <text x="170" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">client-side load balancing</text>
  <text x="170" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">baseline retries / timeouts</text>
  <text x="170" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">baseline circuit breaking</text>
  <text x="170" y="136" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">service-to-service mTLS</text>

  <rect x="340" y="20" width="300" height="170" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">stays with SPRING CLOUD</text>
  <text x="490" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">business-aware fallbacks</text>
  <text x="490" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">config management (@ConfigurationProperties)</text>
  <text x="490" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">application-level metrics with business context</text>
  <text x="490" y="136" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">business logic, of course</text>
</svg>

Infrastructure-level, generic concerns move to the mesh; application-aware, business-specific concerns stay with Spring Cloud.

## 5. Runnable example

Scenario: a service call path that, before mesh adoption, handled retries and load balancing entirely at the application layer. We start with the pre-mesh Spring-Cloud-only version, extend it to the post-mesh version with duplicated, uncoordinated retries (the problem), then handle the hard case: correctly rearchitecting responsibility so the mesh owns the baseline retry and the application only adds business-aware fallback on top, without duplicating the retry count.

### Level 1 — Basic

```java
// File: PreMeshSpringCloudOnly.java -- models the PRE-MESH world: Spring
// Cloud's client handles retries and load balancing ENTIRELY at the
// application layer, since there's no mesh yet to do it.
import java.util.*;

public class PreMeshSpringCloudOnly {
    static List<String> knownInstances = List.of("inventory-pod-1", "inventory-pod-2");
    static int roundRobinIndex = 0;

    static String clientSideLoadBalancedCall(String sku) {
        String instance = knownInstances.get(roundRobinIndex % knownInstances.size());
        roundRobinIndex++;
        System.out.println("[spring cloud client] load-balanced to " + instance);
        return "in-stock: " + sku;
    }

    static String callWithClientSideRetry(String sku, int maxRetries) {
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            System.out.println("[spring cloud client] attempt " + attempt);
            return clientSideLoadBalancedCall(sku); // simplified: succeeds immediately in this demo
        }
        throw new RuntimeException("retries exhausted");
    }

    public static void main(String[] args) {
        String result = callWithClientSideRetry("sku-123", 3);
        System.out.println("[app] " + result);
    }
}
```

How to run: `java PreMeshSpringCloudOnly.java`

Both `clientSideLoadBalancedCall` and `callWithClientSideRetry` live entirely inside the application, modeling classic Spring Cloud client-side resiliency — before a mesh exists, this is the *only* layer providing load balancing and retries at all.

### Level 2 — Intermediate

```java
// File: PostMeshDuplicatedRetries.java -- the SAME service, now deployed
// INSIDE A MESH, but with the application's OLD Spring Cloud retry logic
// left UNCHANGED and UNCOORDINATED with the mesh's OWN retry policy --
// demonstrating the PROBLEM: retries compound instead of composing.
public class PostMeshDuplicatedRetries {
    static int meshLevelAttempts = 0;
    static int downstreamCallCount = 0;

    // The MESH's sidecar proxy: retries up to 3 times on its own, transparently.
    static String meshProxyCallWithRetry(String sku) {
        int meshMaxRetries = 3;
        for (int attempt = 1; attempt <= meshMaxRetries; attempt++) {
            downstreamCallCount++;
            System.out.println("[mesh sidecar] attempt " + attempt + " (actual downstream call #" + downstreamCallCount + ")");
            if (downstreamCallCount < 5) {
                continue; // simulates transient failures, retried internally by the mesh
            }
            return "in-stock: " + sku;
        }
        throw new RuntimeException("mesh retries exhausted");
    }

    // The APPLICATION's OLD Spring Cloud retry logic -- left in place, UNAWARE the mesh also retries.
    static String appLevelCallWithOldRetryLogic(String sku, int appMaxRetries) {
        for (int attempt = 1; attempt <= appMaxRetries; attempt++) {
            System.out.println("[spring cloud client -- STILL ACTIVE] app-level attempt " + attempt);
            try {
                return meshProxyCallWithRetry(sku);
            } catch (RuntimeException e) {
                System.out.println("[spring cloud client] app-level retry triggered on top of the mesh's own retries");
            }
        }
        throw new RuntimeException("app-level retries exhausted too");
    }

    public static void main(String[] args) {
        String result = appLevelCallWithOldRetryLogic("sku-123", 3);
        System.out.println("[app] " + result);
        System.out.println("[analysis] total actual downstream calls made: " + downstreamCallCount + " (far more than either layer's retry count alone)");
    }
}
```

How to run: `java PostMeshDuplicatedRetries.java`

`appLevelCallWithOldRetryLogic` (the leftover Spring Cloud logic) wraps `meshProxyCallWithRetry` (the mesh's own retry logic) inside its own retry loop — both layers are actively retrying the same logical failure, and `downstreamCallCount` at the end shows the actual, compounded number of real attempts made, which is exactly the uncoordinated-overlap problem this topic is about.

### Level 3 — Advanced

```java
// File: PostMeshCorrectlyRearchitected.java -- the SAME service, now
// CORRECTLY rearchitected for the mesh: the MESH owns the baseline,
// generic retry policy; the APPLICATION layer is rewritten to add ONLY
// business-aware fallback on top, with NO duplicated retry loop of its
// own -- the two layers compose cleanly instead of compounding.
public class PostMeshCorrectlyRearchitected {
    static int downstreamCallCount = 0;

    // The MESH's sidecar proxy: owns the baseline retry policy, exactly as before.
    static String meshProxyCallWithRetry(String sku) {
        int meshMaxRetries = 3;
        for (int attempt = 1; attempt <= meshMaxRetries; attempt++) {
            downstreamCallCount++;
            System.out.println("[mesh sidecar] attempt " + attempt + " (actual downstream call #" + downstreamCallCount + ")");
            if (downstreamCallCount < 5) {
                continue;
            }
            return "in-stock: " + sku;
        }
        throw new RuntimeException("mesh retries exhausted -- downstream is genuinely down");
    }

    // The REARCHITECTED application layer: calls the mesh-fronted service EXACTLY ONCE,
    // and only adds a BUSINESS-AWARE fallback if the mesh's own retries are fully exhausted.
    static String checkStockWithBusinessFallback(String sku) {
        try {
            return meshProxyCallWithRetry(sku); // called ONCE -- the mesh already retried internally
        } catch (RuntimeException e) {
            System.out.println("[app resiliency layer] mesh exhausted its retries -- applying business-aware fallback, NOT retrying again");
            return "stock-status-unknown: showing as temporarily unavailable";
        }
    }

    public static void main(String[] args) {
        String result = checkStockWithBusinessFallback("sku-123");
        System.out.println("[app] " + result);
        System.out.println("[analysis] total actual downstream calls made: " + downstreamCallCount + " (matches the mesh's own retry policy exactly, no duplication)");
    }
}
```

How to run: `java PostMeshCorrectlyRearchitected.java`

`checkStockWithBusinessFallback` calls `meshProxyCallWithRetry` exactly once — no surrounding retry loop of its own. If the mesh's internal retries succeed, that result is returned directly; if the mesh's retries are fully exhausted and it throws, the `catch` block applies a business-aware fallback instead of retrying again from the application layer. `downstreamCallCount` at the end reflects only the mesh's own retry count, with no application-level duplication inflating it further.

## 6. Walkthrough

Trace `PostMeshCorrectlyRearchitected.main` in order. **First**, `checkStockWithBusinessFallback("sku-123")` is called and enters its `try` block, calling `meshProxyCallWithRetry("sku-123")` exactly once.

**Next**, inside `meshProxyCallWithRetry`, the loop runs its own three attempts: `downstreamCallCount` increments to `1`, `2`, then `3` across those attempts, and since `downstreamCallCount < 5` remains `true` for all three, each iteration hits `continue` rather than returning — the loop exhausts its three attempts without success and falls through to `throw new RuntimeException(...)`.

**Then**, that exception propagates directly out of `meshProxyCallWithRetry` and is caught by the `catch` block in `checkStockWithBusinessFallback` — critically, this `catch` block does *not* call `meshProxyCallWithRetry` again; it applies the business-aware fallback string and returns it immediately.

**After that**, `main` prints the fallback result, and then the analysis line, reading `downstreamCallCount`.

**Finally**, `downstreamCallCount` shows exactly `3` — the mesh's own retry count, and nothing more — because the application layer never added its own retry loop on top. Contrast this directly with Level 2's `PostMeshDuplicatedRetries`, where the same underlying failure pattern produced a much higher `downstreamCallCount`, purely because the old Spring Cloud retry logic was left running uncoordinated alongside the mesh's own retries.

```
[mesh sidecar] attempt 1 (actual downstream call #1)
[mesh sidecar] attempt 2 (actual downstream call #2)
[mesh sidecar] attempt 3 (actual downstream call #3)
[app resiliency layer] mesh exhausted its retries -- applying business-aware fallback, NOT retrying again
[app] stock-status-unknown: showing as temporarily unavailable
[analysis] total actual downstream calls made: 3 (matches the mesh's own retry policy exactly, no duplication)
```

## 7. Gotchas & takeaways

> Adopting a mesh without auditing and adjusting existing Spring Cloud resiliency configuration is a common, easy-to-miss mistake — the system will *work*, which makes the redundancy easy to overlook, but it silently multiplies retry attempts against already-struggling downstream services exactly when they can least afford it.
- Audit every Spring Cloud resiliency mechanism (client-side load balancing, retry, circuit breaker, TLS configuration) explicitly when adopting a mesh, and make a deliberate decision for each: disable it in favor of the mesh, or keep it specifically for business-aware behavior the mesh can't provide.
- The correct post-mesh pattern, as Level 3 demonstrates, is to call the mesh-fronted service once and let the mesh's own [resiliency policy](0481-mesh-level-resiliency-retries-timeouts-circuit-breaking.md) run its course — application code only adds a fallback *after* the mesh has already exhausted its own retries, never a competing retry loop of its own.
- This isn't unique to Spring Cloud — any framework's application-level resiliency, service discovery, or client-side load balancing mechanism faces the exact same overlap question once a mesh enters the picture.
- Revisit this boundary as your mesh configuration or Spring Cloud usage evolves — a policy that was correctly divided at initial mesh adoption can drift out of alignment if either layer's configuration changes independently later without the other being reconsidered.
