---
card: microservices
gi: 192
slug: discovery-in-container-kubernetes-environments
title: "Discovery in container/Kubernetes environments"
---

## 1. What it is

Kubernetes provides service discovery as a built-in platform feature: a `Service` object gives a stable [DNS name](0191-dns-based-discovery.md) and virtual IP address to a dynamically-changing set of Pods (containers), with Kubernetes' own control plane continuously tracking which Pods are healthy and updating the `Service`'s routing accordingly — this is [server-side discovery](0186-server-side-service-discovery.md) and [third-party registration](0183-service-registration-self-vs-third-party.md), both baked directly into the platform, requiring no application-level registry client at all.

## 2. Why & when

In earlier, VM-based deployments, standing up a dedicated service registry (Eureka, Consul) and integrating a registry client into every service was a genuine, deliberate infrastructure investment. In Kubernetes, this problem is already solved by the platform itself: Pods are inherently ephemeral and get scheduled to different nodes constantly, and Kubernetes' `kubelet` and control plane already track every Pod's lifecycle and health precisely because they need that information to manage scheduling and restarts — service discovery is essentially a byproduct of capabilities the platform needs anyway, exposed to applications through the `Service` abstraction.

Rely on Kubernetes' built-in discovery for any service deployed on Kubernetes, rather than layering a separate registry (Eureka, Consul) on top — doing so would be building redundant infrastructure the platform already provides natively, adding complexity without a corresponding benefit in the common case. Reach for a separate, purpose-built registry within Kubernetes only when a specific capability genuinely isn't covered by Kubernetes' native `Service` and `Endpoints` model (multi-cluster or multi-cloud discovery spanning beyond a single Kubernetes cluster's native reach, for instance).

## 3. Core concept

A `Service` object selects Pods by label, and Kubernetes automatically maintains an `Endpoints` (or `EndpointSlice`) object listing the current healthy Pod IPs matching that selector; DNS resolution of the `Service`'s name, or direct access via its stable virtual IP, transparently routes to whichever Pods are currently healthy, with Kubernetes handling registration, health tracking, and deregistration entirely on the application's behalf.

```yaml
# a Service selects Pods by LABEL -- no application code registers anything
apiVersion: v1
kind: Service
metadata: { name: order-service }
spec:
  selector: { app: order-service }  # matches ANY Pod with this label, automatically
  ports: [{ port: 80, targetPort: 8080 }]
```
```java
// application code: an ORDINARY call to the Service's DNS name -- ZERO Kubernetes-specific code
HttpResponse response = httpClient.call("order-service", 80, "/orders/42");
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Kubernetes automatically tracks which Pods matching a Service's label selector are currently healthy, maintaining an Endpoints list; a caller resolves the Service's stable DNS name and is routed to one of the currently healthy, automatically-tracked Pods, with no application-level registration code involved" >
  <rect x="20" y="70" width="120" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller</text>

  <rect x="220" y="60" width="180" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Service: order-service</text>
  <text x="310" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Endpoints auto-tracked</text>
  <text x="310" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">by the Kubernetes control plane</text>

  <rect x="480" y="20" width="130" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="545" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Pod (healthy)</text>
  <rect x="480" y="80" width="130" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="545" y="100" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Pod (unhealthy)</text>
  <rect x="480" y="140" width="130" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="545" y="160" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Pod (healthy)</text>

  <line x1="140" y1="92" x2="218" y2="92" stroke="#8b949e" marker-end="url(#arr73)"/>
  <line x1="400" y1="80" x2="478" y2="35" stroke="#8b949e" marker-end="url(#arr73)"/>
  <line x1="400" y1="105" x2="478" y2="155" stroke="#8b949e" marker-end="url(#arr73)"/>

  <defs>
    <marker id="arr73" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Kubernetes tracks and updates which Pods are routable automatically; only the healthy ones ever receive traffic.

## 5. Runnable example

Scenario: an order-service deployment that starts with a simulated Eureka-style registry requiring application-level registration code (contrasting with Kubernetes' native approach), models the equivalent Kubernetes `Service`-plus-label-selector mechanism with zero application-level registration code, and finally demonstrates the platform automatically updating the routable Pod set as Pods scale, crash, and fail health checks, entirely outside application code.

### Level 1 — Basic

```java
// File: ApplicationLevelRegistryBaseline.java -- APPLICATION code must EXPLICITLY
// register itself with a separate registry -- the model Kubernetes' native discovery replaces.
public class ApplicationLevelRegistryBaseline {
    static class EurekaStyleRegistry {
        void register(String serviceName, String podId) { System.out.println("[registry] " + podId + " EXPLICITLY registered for " + serviceName); }
    }

    static class OrderServiceApp {
        EurekaStyleRegistry registry;
        OrderServiceApp(EurekaStyleRegistry registry) { this.registry = registry; }
        void onStartup(String podId) {
            System.out.println("[" + podId + "] starting up...");
            registry.register("order-service", podId); // APPLICATION code MUST do this itself
        }
    }

    public static void main(String[] args) {
        EurekaStyleRegistry registry = new EurekaStyleRegistry();
        new OrderServiceApp(registry).onStartup("order-pod-1");
        System.out.println("The APPLICATION's own code contains registration logic -- a real dependency Kubernetes' native model removes.");
    }
}
```

**How to run:** `javac ApplicationLevelRegistryBaseline.java && java ApplicationLevelRegistryBaseline` (JDK 17+).

### Level 2 — Intermediate

```java
// File: KubernetesNativeLabelSelector.java -- models a Kubernetes Service:
// Pods are tracked by LABEL, entirely by the PLATFORM -- ZERO application registration code.
import java.util.*;

public class KubernetesNativeLabelSelector {
    record Pod(String id, Map<String, String> labels, boolean healthy) {}

    // simulates the Kubernetes CONTROL PLANE -- tracks Pods automatically, NOT the application
    static class KubernetesControlPlane {
        List<Pod> allPods = new ArrayList<>();
        void podCreated(Pod pod) { allPods.add(pod); System.out.println("[control plane] observed new Pod: " + pod.id()); } // NOT called by application code

        // the Service's Endpoints: computed AUTOMATICALLY from label selector + health, NEVER from explicit registration
        List<Pod> resolveService(String selectorApp) {
            return allPods.stream().filter(p -> selectorApp.equals(p.labels().get("app")) && p.healthy()).toList();
        }
    }

    public static void main(String[] args) {
        KubernetesControlPlane k8s = new KubernetesControlPlane();

        // the PLATFORM observes Pods starting -- NO application code called ANY registration method
        k8s.podCreated(new Pod("order-pod-1", Map.of("app", "order-service"), true));
        k8s.podCreated(new Pod("order-pod-2", Map.of("app", "order-service"), true));

        List<Pod> endpoints = k8s.resolveService("order-service"); // resolves via LABEL SELECTOR, automatically
        System.out.println("order-service Endpoints: " + endpoints.stream().map(Pod::id).toList());
        System.out.println("NO application code anywhere called a 'register' method -- the PLATFORM tracked this ENTIRELY on its own.");
    }
}
```

**How to run:** `javac KubernetesNativeLabelSelector.java && java KubernetesNativeLabelSelector` (JDK 17+).

Expected output:
```
[control plane] observed new Pod: order-pod-1
[control plane] observed new Pod: order-pod-2
order-service Endpoints: [order-pod-1, order-pod-2]
NO application code anywhere called a 'register' method -- the PLATFORM tracked this ENTIRELY on its own.
```

### Level 3 — Advanced

```java
// File: AutomaticEndpointUpdatesOverTime.java -- Pods SCALE UP, CRASH, and FAIL
// HEALTH CHECKS; the Service's Endpoints update AUTOMATICALLY throughout, with
// ZERO application-level involvement at ANY point.
import java.util.*;

public class AutomaticEndpointUpdatesOverTime {
    record Pod(String id, Map<String, String> labels, boolean healthy) {}

    static class KubernetesControlPlane {
        Map<String, Pod> allPods = new LinkedHashMap<>();
        void podCreated(Pod pod) { allPods.put(pod.id(), pod); }
        void podDeleted(String podId) { allPods.remove(podId); } // e.g. a crash, or scale-down
        void podHealthChanged(String podId, boolean healthy) {
            Pod old = allPods.get(podId);
            allPods.put(podId, new Pod(old.id(), old.labels(), healthy)); // e.g. readiness probe result changes
        }
        List<Pod> resolveService(String selectorApp) {
            return allPods.values().stream().filter(p -> selectorApp.equals(p.labels().get("app")) && p.healthy()).toList();
        }
    }

    static void printEndpoints(KubernetesControlPlane k8s, String label) {
        System.out.println(label + ": " + k8s.resolveService("order-service").stream().map(Pod::id).toList());
    }

    public static void main(String[] args) {
        KubernetesControlPlane k8s = new KubernetesControlPlane();

        k8s.podCreated(new Pod("order-pod-1", Map.of("app", "order-service"), true));
        printEndpoints(k8s, "t=0, after 1 Pod starts");

        k8s.podCreated(new Pod("order-pod-2", Map.of("app", "order-service"), true));
        k8s.podCreated(new Pod("order-pod-3", Map.of("app", "order-service"), true));
        printEndpoints(k8s, "t=1, after SCALE UP to 3 Pods");

        k8s.podHealthChanged("order-pod-2", false); // readiness probe starts failing (e.g. DB connection lost)
        printEndpoints(k8s, "t=2, after order-pod-2 FAILS its health check");

        k8s.podDeleted("order-pod-3"); // order-pod-3 CRASHES / is deleted
        printEndpoints(k8s, "t=3, after order-pod-3 CRASHES");

        k8s.podHealthChanged("order-pod-2", true); // order-pod-2 RECOVERS
        printEndpoints(k8s, "t=4, after order-pod-2 RECOVERS");

        System.out.println("\nThroughout ALL of this, NO application code was ever called to register, deregister, or update health -- ENTIRELY platform-managed.");
    }
}
```

**How to run:** `javac AutomaticEndpointUpdatesOverTime.java && java AutomaticEndpointUpdatesOverTime` (JDK 17+).

Expected output:
```
t=0, after 1 Pod starts: [order-pod-1]
t=1, after SCALE UP to 3 Pods: [order-pod-1, order-pod-2, order-pod-3]
t=2, after order-pod-2 FAILS its health check: [order-pod-1, order-pod-3]
t=3, after order-pod-3 CRASHES: [order-pod-1]
t=4, after order-pod-2 RECOVERS: [order-pod-1, order-pod-2]

Throughout ALL of this, NO application code was ever called to register, deregister, or update health -- ENTIRELY platform-managed.
```

## 6. Walkthrough

1. **Level 1** — `OrderServiceApp.onStartup` explicitly calls `registry.register("order-service", podId)`, meaning the application's own startup sequence contains a required, registry-specific step — this is the baseline application-level registration model that Kubernetes' native discovery replaces.
2. **Level 2, the control plane tracking Pods independently** — `KubernetesControlPlane.podCreated` is called directly by `main` (standing in for Kubernetes' own internal Pod-creation tracking, which happens automatically as part of scheduling a Pod, not as an application-initiated action), and crucially, `OrderServiceApp` doesn't even exist in this version — there's no application class calling any registration method at all.
3. **Level 2, resolution by label selector** — `resolveService` filters `allPods` by checking each Pod's `labels().get("app")` against the requested selector and its `healthy()` status, mirroring exactly how a real Kubernetes `Service`'s `spec.selector` determines its `Endpoints`.
4. **Level 2, the confirmed absence of application involvement** — the final printed statement is directly verifiable: nowhere in this file does any code resembling `OrderServiceApp` or an explicit registration call exist, only Pod creation events fed directly to the control plane.
5. **Level 3, four distinct lifecycle events** — `podCreated` (twice, modeling a scale-up), `podHealthChanged` (modeling a readiness probe transitioning to failing), `podDeleted` (modeling a crash or scale-down), and `podHealthChanged` again (modeling recovery) are all called directly on `k8s`, none of them originating from any application-level code.
6. **Level 3, tracing the Endpoints list through each event** — at `t=1`, all three pods are healthy and present; at `t=2`, `order-pod-2`'s health flips to `false`, and `resolveService`'s filter immediately excludes it, even though the Pod itself is still running (a direct parallel to [health-check-based registration](0188-health-check-based-registration.md)); at `t=3`, `order-pod-3` is removed from `allPods` entirely, mirroring a crash or Kubernetes deleting a Pod during a scale-down; at `t=4`, `order-pod-2`'s health flips back to `true`, and it reappears in the resolved list automatically.
7. **Level 3, what this demonstrates about the platform's native model** — every single one of these four transitions was driven purely by data changes fed into `KubernetesControlPlane`, with `resolveService`'s filtering logic recomputing the correct answer fresh each time — in a real Kubernetes cluster, these exact transitions happen automatically as Pods are scheduled, pass or fail readiness probes, and are deleted, with the `kubelet` and control plane handling all of the corresponding `Endpoints` updates entirely outside any application code, which is precisely why services deployed on Kubernetes typically need no separate registry client or explicit registration logic at all.

## 7. Gotchas & takeaways

> **Gotcha:** Kubernetes' native `Service` discovery is scoped to a single cluster by default — reaching services across multiple clusters or across a hybrid cloud/on-premises boundary requires additional tooling (a service mesh with multi-cluster support, or a dedicated cross-cluster discovery mechanism) layered on top, since the built-in `Service`/`Endpoints` model alone doesn't natively span cluster boundaries.

- Kubernetes provides service discovery as a built-in platform feature: a `Service` object gives a stable name to a dynamically-tracked set of Pods, with the control plane handling registration, health tracking, and deregistration entirely on the application's behalf.
- This is server-side discovery and third-party registration, both native to the platform, meaning applications deployed on Kubernetes typically need no separate registry client or explicit registration code at all.
- The `Service`'s label selector, combined with continuous Pod health tracking, is what keeps its `Endpoints` accurate automatically as Pods scale, crash, restart, or transition between healthy and unhealthy states.
- Relying on this native mechanism, rather than layering a separate registry on top, avoids building redundant infrastructure the platform already provides for services confined to a single cluster.
- Kubernetes' native discovery is scoped to a single cluster by default; multi-cluster or hybrid-environment discovery requires additional tooling beyond the basic `Service`/`Endpoints` model.
