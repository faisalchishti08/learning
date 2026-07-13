---
card: microservices
gi: 211
slug: load-balancer-as-point-of-failure
title: "Load balancer as point of failure"
---

## 1. What it is

Because a [server-side load balancer](0204-server-side-load-balancing.md) sits in the path of every request it handles, it is itself a single point of failure unless deliberately made highly available — the exact same structural risk already covered for [gateways](0170-single-point-of-failure-concerns-ha-gateways.md) and [service registries](0193-service-registry-high-availability-replication.md), applied here specifically to the load-balancing tier, and it requires the identical solution: running multiple redundant load balancer instances rather than relying on any single one.

## 2. Why & when

A load balancer that concentrates all traffic to a backend fleet through one instance inherits all the availability benefits it provides to that fleet (routing around individual backend failures) while introducing a brand-new, undistributed risk of its own: if the balancer itself goes down, every backend instance it fronts becomes unreachable simultaneously, regardless of how healthy each individual backend is. This is a direct structural consequence of introducing any intermediary component in a request path, and it applies equally whether that intermediary is a load balancer, a gateway, or a service registry — the fix is the same pattern in every case: redundancy, health checking, and automatic failover at the load-balancer tier itself.

Recognize this risk specifically whenever server-side load balancing is chosen — client-side balancing, by contrast, has no equivalent single point of failure, since the balancing logic runs redundantly inside every calling instance already. Deploy load balancers as a redundant, health-checked cluster (or rely on a cloud provider's managed load balancer service, which handles this redundancy internally) for any production deployment where server-side balancing is used.

## 3. Core concept

Multiple load balancer instances run simultaneously, each capable of serving any request identically, with a mechanism above them (DNS with multiple records, a floating/virtual IP with automatic failover, or a cloud provider's managed service) ensuring traffic is directed only to currently-healthy load balancer instances — mirroring exactly the same redundancy pattern applied to the backend instances the load balancer itself fronts.

```java
// a SINGLE load balancer instance -- a single point of failure for the ENTIRE backend fleet
LoadBalancer theOnlyLb = new LoadBalancer(backendInstances);

// REDUNDANT load balancer instances, with a mechanism selecting a HEALTHY one
List<LoadBalancer> lbCluster = List.of(lb1, lb2, lb3);
LoadBalancer activeLb = lbCluster.stream().filter(LoadBalancer::isHealthy).findFirst().orElseThrow();
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single load balancer failing takes down access to an entire, perfectly healthy backend fleet. Multiple redundant load balancer instances mean any single one failing is absorbed by the others, preserving access to the backend fleet" >
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Single LB (risky)</text>
  <rect x="60" y="40" width="180" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="150" y="62" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">LB (DOWN)</text>
  <text x="150" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">entire healthy backend fleet unreachable</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Redundant LB cluster</text>
  <rect x="380" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="2,2"/><text x="420" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">LB-1 (DOWN)</text>
  <rect x="470" y="40" width="80" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/><text x="510" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">LB-2 (up)</text>
  <text x="480" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">backend fleet stays reachable via LB-2</text>

  <defs>
    <marker id="arr90" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Backend health means nothing if the single balancer fronting them is down; redundancy at the balancer tier fixes this.

## 5. Runnable example

Scenario: a fleet of order-service backends fronted by load balancing that starts with a single load-balancer instance, showing total outage of an otherwise-healthy backend fleet when it fails, adds a redundant load-balancer cluster with automatic failover so the fleet stays reachable, and finally demonstrates a rolling restart of the load-balancer tier itself achieving zero downtime, mirroring the exact same operational payoff HA gateway design provides.

### Level 1 — Basic

```java
// File: SingleLoadBalancerOutage.java -- ONE load balancer instance; its
// failure makes an ENTIRE, perfectly HEALTHY backend fleet unreachable.
public class SingleLoadBalancerOutage {
    static boolean loadBalancerIsUp = true;
    static boolean[] backendsHealthy = {true, true, true}; // ALL backends perfectly healthy

    static String routeRequest() {
        if (!loadBalancerIsUp) return "CONNECTION REFUSED -- load balancer unreachable";
        return "200 OK from a healthy backend";
    }

    public static void main(String[] args) {
        System.out.println(routeRequest());

        loadBalancerIsUp = false; // the ONE load balancer crashes
        System.out.println(routeRequest());
        System.out.println("ALL 3 backends are STILL healthy, but EVERY request now fails -- the load balancer itself is the bottleneck.");
    }
}
```

**How to run:** `javac SingleLoadBalancerOutage.java && java SingleLoadBalancerOutage` (JDK 17+).

### Level 2 — Intermediate

```java
// File: RedundantLoadBalancerCluster.java -- MULTIPLE load balancer instances;
// ANY single one failing is ABSORBED by the others, preserving access.
import java.util.*;

public class RedundantLoadBalancerCluster {
    static class LoadBalancerInstance {
        String id;
        boolean up = true;
        LoadBalancerInstance(String id) { this.id = id; }
        String routeRequest() { return "200 OK, via " + id; }
    }

    static class LbClusterFrontend { // stands in for DNS/VIP failover choosing a HEALTHY LB instance
        List<LoadBalancerInstance> lbInstances;
        LbClusterFrontend(List<LoadBalancerInstance> lbInstances) { this.lbInstances = lbInstances; }
        String routeRequest() {
            return lbInstances.stream().filter(lb -> lb.up).findFirst()
                .map(LoadBalancerInstance::routeRequest)
                .orElseThrow(() -> new RuntimeException("ALL load balancer instances down"));
        }
    }

    public static void main(String[] args) {
        LoadBalancerInstance lb1 = new LoadBalancerInstance("lb-1");
        LoadBalancerInstance lb2 = new LoadBalancerInstance("lb-2");
        LbClusterFrontend cluster = new LbClusterFrontend(List.of(lb1, lb2));

        System.out.println(cluster.routeRequest());

        lb1.up = false; // lb-1 CRASHES
        System.out.println("*** lb-1 CRASHED ***");
        System.out.println(cluster.routeRequest() + " (traffic transparently absorbed by lb-2)");
    }
}
```

**How to run:** `javac RedundantLoadBalancerCluster.java && java RedundantLoadBalancerCluster` (JDK 17+).

Expected output:
```
200 OK, via lb-1
*** lb-1 CRASHED ***
200 OK, via lb-2 (traffic transparently absorbed by lb-2)
```

### Level 3 — Advanced

```java
// File: RollingRestartOfLoadBalancerTier.java -- a ROUTINE deployment restarts
// EACH load balancer instance ONE AT A TIME; the cluster's redundancy ensures
// ZERO client-visible downtime -- the SAME payoff HA gateway design provides.
import java.util.*;

public class RollingRestartOfLoadBalancerTier {
    static class LoadBalancerInstance {
        String id; boolean up = true;
        LoadBalancerInstance(String id) { this.id = id; }
        String routeRequest() { return "200 OK, via " + id; }
    }
    static class LbClusterFrontend {
        List<LoadBalancerInstance> lbInstances;
        LbClusterFrontend(List<LoadBalancerInstance> lbInstances) { this.lbInstances = lbInstances; }
        String routeRequest() {
            return lbInstances.stream().filter(lb -> lb.up).findFirst()
                .map(LoadBalancerInstance::routeRequest)
                .orElseThrow(() -> new RuntimeException("ALL load balancer instances down"));
        }
    }

    public static void main(String[] args) {
        List<LoadBalancerInstance> instances = List.of(new LoadBalancerInstance("lb-1"), new LoadBalancerInstance("lb-2"), new LoadBalancerInstance("lb-3"));
        LbClusterFrontend cluster = new LbClusterFrontend(instances);

        int successfulRequests = 0, failedRequests = 0;

        for (LoadBalancerInstance instance : instances) {
            instance.up = false; // taken OFFLINE for its restart
            System.out.println("[deployment] " + instance.id + " taken offline for restart");
            try {
                System.out.println("  " + cluster.routeRequest() + "  <- traffic continues via other LB instances");
                successfulRequests++;
            } catch (RuntimeException e) { failedRequests++; }
            instance.up = true; // back online, upgraded
            System.out.println("[deployment] " + instance.id + " back online\n");
        }

        System.out.println("Successful requests during rolling restart: " + successfulRequests + ", failed: " + failedRequests);
        System.out.println("A FULL rolling restart of the ENTIRE load-balancer tier completed with ZERO failed requests -- identical payoff to HA gateway design.");
    }
}
```

**How to run:** `javac RollingRestartOfLoadBalancerTier.java && java RollingRestartOfLoadBalancerTier` (JDK 17+).

Expected output:
```
[deployment] lb-1 taken offline for restart
  200 OK, via lb-2  <- traffic continues via other LB instances
[deployment] lb-1 back online

[deployment] lb-2 taken offline for restart
  200 OK, via lb-1  <- traffic continues via other LB instances
[deployment] lb-2 back online

[deployment] lb-3 taken offline for restart
  200 OK, via lb-1  <- traffic continues via other LB instances
[deployment] lb-3 back online

Successful requests during rolling restart: 3, failed: 0
A FULL rolling restart of the ENTIRE load-balancer tier completed with ZERO failed requests -- identical payoff to HA gateway design.
```

## 6. Walkthrough

1. **Level 1** — `loadBalancerIsUp` is a single boolean representing the entire load-balancing tier's health; when it becomes `false`, `routeRequest` fails immediately regardless of `backendsHealthy`, which remains entirely `true` throughout, directly demonstrating that backend health is irrelevant if the balancer fronting them is down.
2. **Level 2, multiple independent load balancer instances** — `lb1` and `lb2` are separate `LoadBalancerInstance` objects, each with its own `up` flag; `LbClusterFrontend.routeRequest` filters to the first currently-`up` instance and delegates to it.
3. **Level 2, the failure absorbed** — setting `lb1.up = false` removes it from consideration on the next call; `cluster.routeRequest()` correctly falls through to `lb2`, which handles the request successfully, with no client-visible failure at all.
4. **Level 3, iterating through a full rolling restart** — the `for` loop takes each of the three load balancer instances offline in turn (setting `up = false`), issues a test request during that window, then brings it back online before moving to the next.
5. **Level 3, traffic continuing through every restart step** — because at least two of the three instances remain `up` at any given point in the loop, `cluster.routeRequest()` always finds an available instance, and the printed `<- traffic continues via other LB instances` annotation confirms this for every single restart step.
6. **Level 3, the complete accounting** — across all three restart iterations, covering the entire load-balancer tier, `failedRequests` remains at exactly `0` — every single test request succeeded despite each individual load balancer instance being deliberately taken offline at some point during the loop.
7. **Level 3, the direct parallel to HA gateway design** — the final printed comment makes the connection explicit: this is structurally the identical resilience pattern and identical operational payoff already established for gateways — redundant instances behind a health-aware failover mechanism enable both surviving unplanned crashes and performing routine maintenance with zero downtime, and the fact that this exact same pattern needs to be applied at the load-balancer tier specifically (not just at the backend or gateway tiers) is the core point this topic makes: any intermediary component sitting in a critical request path inherits the same single-point-of-failure risk and needs the same redundancy solution, regardless of what specific role that intermediary plays.

## 7. Gotchas & takeaways

> **Gotcha:** the mechanism selecting *among* redundant load balancer instances (DNS round-robin, a floating/virtual IP, a cloud provider's managed load-balancer-of-load-balancers) is itself a component with its own failure modes and its own consistency/propagation-delay characteristics — redundancy at the load-balancer tier doesn't eliminate the single-point-of-failure question, it just moves it one level up, to whatever mechanism is responsible for directing traffic to a healthy load balancer instance in the first place; that mechanism's own reliability deserves the same scrutiny.

- A server-side load balancer, sitting in the path of every request it handles, is itself a single point of failure unless deployed as a redundant, health-checked cluster rather than a single instance.
- This is the same structural risk already established for gateways and service registries, applied specifically to the load-balancing tier — any intermediary in a critical request path inherits this risk.
- Client-side load balancing has no equivalent single point of failure, since its balancing logic runs redundantly inside every calling instance already, rather than in one shared, centralized component.
- Redundant load-balancer instances, combined with a health-aware failover mechanism, enable both surviving unplanned crashes and performing routine maintenance (rolling restarts) with zero client-visible downtime.
- The mechanism directing traffic to a healthy load-balancer instance (DNS, a floating IP, a managed cloud service) is itself a component with its own reliability characteristics, deserving the same scrutiny as the load-balancer tier it protects.
