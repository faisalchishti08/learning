---
card: spring-cloud
gi: 116
slug: service-discovery-via-kubernetes-api
title: "Service discovery via Kubernetes API"
---

## 1. What it is

Spring Cloud Kubernetes's `DiscoveryClient` implementation queries the Kubernetes API server (or watches it) for `Endpoints`/`EndpointSlice` objects belonging to a named Kubernetes `Service`, returning the current, live set of healthy pod IPs backing that Service — the same `DiscoveryClient.getInstances("order-service")` call application code already uses for Eureka-based discovery (an earlier card), now backed by Kubernetes' own service registry instead of a separately-run Eureka server.

```java
@Autowired DiscoveryClient discoveryClient;

List<ServiceInstance> instances = discoveryClient.getInstances("order-service");
// backed by the Kubernetes API's Endpoints for the Service named "order-service" -- NOT a separate Eureka registry
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order-service
  ports:
    - port: 8080
```

## 2. Why & when

Kubernetes already maintains its own authoritative, continuously-updated registry of which pods are healthy and ready to receive traffic for a given `Service` — this is precisely the `Endpoints`/`EndpointSlice` object the platform updates automatically as pods start, stop, pass, or fail readiness probes. Running a separate Eureka server to duplicate this same "which instances are currently healthy" information inside a Kubernetes cluster is redundant infrastructure solving an already-solved problem; Spring Cloud Kubernetes's discovery implementation queries this native Kubernetes registry directly, so `DiscoveryClient.getInstances(...)` calls resolve against ground truth the platform itself maintains, with no separate registration/heartbeat mechanism (as Eureka requires) needed at all.

Reach for Kubernetes-native discovery when:

- Deploying entirely within Kubernetes and wanting service discovery to be a natural consequence of already-existing Kubernetes `Service` objects, rather than requiring applications to additionally register themselves with a separate Eureka server on top.
- Migrating a Eureka-based Spring Cloud application onto Kubernetes — since both implement the same `DiscoveryClient` interface, existing application code calling `discoveryClient.getInstances(...)` or using `@LoadBalanced` clients typically needs no changes, only a dependency and configuration swap.
- Wanting discovery data to always reflect Kubernetes' own live pod readiness state exactly, with no possibility of drift between "what Eureka's registry says" and "what Kubernetes itself considers healthy" — a discrepancy that can occur with a separately-maintained registry if heartbeat timing or failure detection differs even slightly from Kubernetes' own readiness probing.

## 3. Core concept

```
 Kubernetes Service "order-service" selects pods labeled app=order-service

 Kubernetes CONTINUOUSLY maintains the Endpoints/EndpointSlice for that Service:
   pod-1 (10.244.0.12) passes readiness probe -> ADDED to Endpoints
   pod-2 (10.244.0.13) passes readiness probe -> ADDED to Endpoints
   pod-1 FAILS readiness probe                -> REMOVED from Endpoints (platform does this automatically)

 discoveryClient.getInstances("order-service")
   -> queries the Kubernetes API for the CURRENT Endpoints of Service "order-service"
   -> returns whatever pod IPs are CURRENTLY listed -- always reflects Kubernetes' own live state
```

No application-level heartbeat or self-registration step is required — a pod becomes discoverable purely by matching a Service's label selector and passing its readiness probe, both mechanisms Kubernetes itself already manages independent of Spring Cloud Kubernetes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Kubernetes Service continuously tracks which pods are currently ready via its Endpoints object and a call to getInstances queries the Kubernetes API directly for that live list rather than a separately maintained Eureka registry">
  <rect x="20" y="20" width="150" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="44" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">pod-1 (ready)</text>
  <rect x="20" y="70" width="150" height="40" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="95" y="94" fill="#f85149" font-size="7.5" text-anchor="middle" font-family="sans-serif">pod-2 (NOT ready)</text>

  <rect x="250" y="45" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="65" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Service Endpoints</text>
  <text x="325" y="79" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">only pod-1 listed</text>

  <rect x="480" y="45" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="550" y="73" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">getInstances(...)</text>

  <defs><marker id="a116" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="40" x2="250" y2="65" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a116)"/>
  <line x1="170" y1="90" x2="250" y2="75" stroke="#f85149" stroke-width="1.2" stroke-dasharray="4,3"/>
  <line x1="400" y1="68" x2="480" y2="68" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a116)"/>
</svg>

`pod-2`'s dashed, unmarked line shows it never reaches the Endpoints object at all while unready — `getInstances` only ever sees pod-1.

## 5. Runnable example

The scenario: model a Kubernetes-style Endpoints object that tracks pod readiness dynamically, queried through a `DiscoveryClient`-shaped interface — showing discovery results change automatically as pod readiness changes, with no separate registration call from the application itself. Start with a static snapshot, then add dynamic readiness tracking, then simulate a rolling deployment where old and new pods briefly coexist, correctly reflected in discovery results throughout.

### Level 1 — Basic

A static Endpoints snapshot, queried through a `DiscoveryClient`-shaped interface.

```java
import java.util.*;

public class K8sDiscoveryLevel1 {
    interface DiscoveryClient { List<String> getInstances(String serviceName); }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        Map<String, List<String>> endpoints = Map.of(
                "order-service", List.of("10.244.0.12:8080", "10.244.0.13:8080")
        );
        public List<String> getInstances(String serviceName) {
            return endpoints.getOrDefault(serviceName, List.of());
        }
    }

    public static void main(String[] args) {
        DiscoveryClient discovery = new KubernetesDiscoveryClient();
        System.out.println("order-service instances: " + discovery.getInstances("order-service"));
    }
}
```

How to run: `java K8sDiscoveryLevel1.java`

A fixed `endpoints` map stands in for a real Kubernetes `Endpoints` object's current pod list — `getInstances` simply looks it up, with no application-level registration step involved anywhere in this flow.

### Level 2 — Intermediate

Add dynamic readiness: pods can transition between ready and not-ready, and `getInstances` always reflects the current state, updating automatically as readiness changes.

```java
import java.util.*;

public class K8sDiscoveryLevel2 {
    interface DiscoveryClient { List<String> getInstances(String serviceName); }

    static class PodEndpointRegistry {
        Map<String, Boolean> podReadiness = new LinkedHashMap<>(); // pod -> ready?

        void setReady(String podIp, boolean ready) {
            podReadiness.put(podIp, ready);
            System.out.println(podIp + " readiness set to " + ready);
        }

        // models the Kubernetes control plane continuously recomputing Endpoints from CURRENT readiness
        List<String> currentEndpoints() {
            List<String> ready = new ArrayList<>();
            for (Map.Entry<String, Boolean> entry : podReadiness.entrySet()) {
                if (entry.getValue()) ready.add(entry.getKey());
            }
            return ready;
        }
    }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        PodEndpointRegistry registry;
        KubernetesDiscoveryClient(PodEndpointRegistry registry) { this.registry = registry; }
        public List<String> getInstances(String serviceName) { return registry.currentEndpoints(); } // ALWAYS live
    }

    public static void main(String[] args) {
        PodEndpointRegistry registry = new PodEndpointRegistry();
        DiscoveryClient discovery = new KubernetesDiscoveryClient(registry);

        registry.setReady("10.244.0.12:8080", true);
        registry.setReady("10.244.0.13:8080", true);
        System.out.println("instances: " + discovery.getInstances("order-service"));

        registry.setReady("10.244.0.13:8080", false); // pod-2 FAILS its readiness probe
        System.out.println("instances after pod-2 fails readiness: " + discovery.getInstances("order-service"));
    }
}
```

How to run: `java K8sDiscoveryLevel2.java`

The second `getInstances` call, made after `10.244.0.13:8080`'s readiness flips to `false`, correctly excludes it from the returned list — no explicit "deregister" call was made by the application; `currentEndpoints` simply recomputes from whatever `podReadiness` currently holds, exactly mirroring how a real Kubernetes `Endpoints` object updates automatically the instant the platform's own readiness probing detects a change, with no application-level action required.

### Level 3 — Advanced

Simulate a rolling deployment: new pods (a new version) start and become ready while old pods (the previous version) are still serving traffic, then old pods are terminated one by one — with `getInstances` correctly reflecting the transitional mixed state throughout.

```java
import java.util.*;

public class K8sDiscoveryLevel3 {
    interface DiscoveryClient { List<String> getInstances(String serviceName); }

    record Pod(String ip, String version, boolean ready) {}

    static class PodEndpointRegistry {
        List<Pod> pods = new ArrayList<>();
        void addOrUpdate(Pod pod) {
            pods.removeIf(p -> p.ip().equals(pod.ip()));
            pods.add(pod);
        }
        void remove(String ip) { pods.removeIf(p -> p.ip().equals(ip)); }
        List<String> currentEndpoints() {
            List<String> ready = new ArrayList<>();
            for (Pod p : pods) if (p.ready()) ready.add(p.ip() + "(" + p.version() + ")");
            return ready;
        }
    }

    static class KubernetesDiscoveryClient implements DiscoveryClient {
        PodEndpointRegistry registry;
        KubernetesDiscoveryClient(PodEndpointRegistry registry) { this.registry = registry; }
        public List<String> getInstances(String serviceName) { return registry.currentEndpoints(); }
    }

    public static void main(String[] args) {
        PodEndpointRegistry registry = new PodEndpointRegistry();
        DiscoveryClient discovery = new KubernetesDiscoveryClient(registry);

        // steady state: two v1 pods
        registry.addOrUpdate(new Pod("10.244.0.1", "v1", true));
        registry.addOrUpdate(new Pod("10.244.0.2", "v1", true));
        System.out.println("steady state: " + discovery.getInstances("order-service"));

        // rolling deployment begins: one NEW v2 pod starts and becomes ready, v1 pods still serving
        registry.addOrUpdate(new Pod("10.244.0.3", "v2", true));
        System.out.println("mid-rollout (v1 and v2 coexist): " + discovery.getInstances("order-service"));

        // old v1 pods terminated one by one as the rollout proceeds
        registry.remove("10.244.0.1");
        System.out.println("after removing one v1 pod: " + discovery.getInstances("order-service"));

        registry.remove("10.244.0.2");
        registry.addOrUpdate(new Pod("10.244.0.4", "v2", true));
        System.out.println("rollout complete (only v2 remains): " + discovery.getInstances("order-service"));
    }
}
```

How to run: `java K8sDiscoveryLevel3.java`

The mid-rollout `getInstances` call correctly returns three entries — two `v1` pods and the one new `v2` pod — accurately reflecting that during a real rolling deployment, old and new pod versions genuinely do coexist and both receive traffic for a transitional period; each subsequent call after a `remove`/`addOrUpdate` reflects the registry's state at that exact moment, with no caching or staleness, exactly mirroring how load-balanced calls made through a `@LoadBalanced` client during a real rolling deployment would be distributed across whatever mix of old and new pod versions Kubernetes' Endpoints object currently lists.

## 6. Walkthrough

Trace the mid-rollout state transition in Level 3.

1. After the two initial `addOrUpdate` calls, `registry.pods` contains two `Pod` records, both `version="v1"`, both `ready=true` — `currentEndpoints()` returns both, formatted as `"10.244.0.1(v1)"` and `"10.244.0.2(v1)"`.
2. `registry.addOrUpdate(new Pod("10.244.0.3", "v2", true))` runs — `removeIf` finds no existing pod with IP `"10.244.0.3"` (it's genuinely new), so nothing is removed, and the new `Pod` is appended to `pods`, which now holds three entries: two `v1` and one `v2`.
3. `discovery.getInstances("order-service")` calls `registry.currentEndpoints()`, which iterates all three pods and finds all three `ready=true`, returning all three formatted entries — this is the "mid-rollout" printed line, correctly showing both versions coexisting.
4. `registry.remove("10.244.0.1")` runs `pods.removeIf(p -> p.ip().equals("10.244.0.1"))`, which removes exactly that one `Pod` record, leaving two: one remaining `v1` pod and the one `v2` pod.
5. The subsequent `getInstances` call reflects exactly this two-pod state — one `v1`, one `v2` — again computed fresh from `registry.pods`' current contents, with no memory of the previously-returned three-pod list.
6. The final two calls (`remove("10.244.0.2")` then `addOrUpdate` a second `v2` pod) bring the registry to a state with zero `v1` pods and two `v2` pods, and the final `getInstances` call correctly reflects the completed rollout — this progression, entirely driven by `registry` mutations that model what Kubernetes' own control plane does automatically, required no explicit "rollout complete" signal anywhere in the discovery logic itself.

```
steady state:  [v1-pod-1, v1-pod-2]
+ v2 starts:   [v1-pod-1, v1-pod-2, v2-pod-1]     <- BOTH versions live simultaneously
- v1-pod-1:    [v1-pod-2, v2-pod-1]
- v1-pod-2, + v2-pod-2: [v2-pod-1, v2-pod-2]      <- rollout complete, only v2 remains

each getInstances() call reflects registry state AT THAT MOMENT -- no caching, no staleness
```

## 7. Gotchas & takeaways

> **Gotcha:** Kubernetes-native discovery reflects *readiness*, not merely pod existence — a pod that's running but hasn't yet passed its readiness probe (still starting up, or temporarily failing a health check) is correctly excluded from `Endpoints`/`getInstances` results, which is the desired behavior; assuming `getInstances` should return every pod matching a Service's label selector regardless of readiness state is a misunderstanding of what the Endpoints object actually represents.

- Kubernetes-native discovery eliminates the need for application-level self-registration and heartbeating entirely — a pod becomes discoverable purely by matching a Service's selector and passing its readiness probe, both mechanisms the platform manages independently of the application's own code.
- Because `getInstances` queries live Kubernetes state on every call (or via a watch-based cache kept continuously in sync), discovery results always reflect current reality, including transitional states like a rolling deployment's temporary mix of old and new pod versions.
- Application code written against the `DiscoveryClient` interface (including `@LoadBalanced` REST clients built on top of it, from earlier cards) works identically whether backed by Kubernetes-native discovery or Eureka — the interface, not the implementation, is what application code depends on.
- Readiness probes are the mechanism that actually controls whether a pod appears in discovery results — a misconfigured or overly lenient readiness probe (one that reports "ready" before the application can genuinely handle traffic) undermines discovery's entire value, regardless of how correctly the discovery mechanism itself is configured.
