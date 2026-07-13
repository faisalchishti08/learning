---
card: microservices
gi: 447
slug: pods-deployments-services-ingress
title: "Pods, Deployments, Services, Ingress"
---

## 1. What it is

**Pods**, **Deployments**, **Services**, and **Ingress** are four layered Kubernetes building blocks, each solving a different piece of "run this container reliably and let traffic reach it." A **Pod** is the smallest deployable unit — one or more tightly coupled containers sharing a network identity. A **Deployment** declares how many replicas of a Pod template should exist and reconciles toward that count (the mechanism from [container orchestration (Kubernetes) concepts](0446-container-orchestration-kubernetes-concepts.md) applied specifically to Pods). A **Service** gives that shifting set of Pods one stable virtual address and load-balances across whichever replicas are currently healthy. An **Ingress** sits in front of Services and routes external HTTP traffic to the right one based on host or path.

## 2. Why & when

You need all four layers, not just one, because each solves a problem the others don't:

- **Pods alone don't survive failure.** A Pod created directly has no controller watching it — if it crashes, nothing restarts it. You need a Deployment managing Pods as soon as you care about a service staying up without manual intervention.
- **Pod IP addresses change constantly.** Every time a Pod is recreated (a new version deploys, a crashed Pod is replaced), it gets a new IP. Anything that hardcodes a Pod IP breaks the moment that Pod is replaced — you need a Service the moment more than one thing needs to reliably reach a set of Pods.
- **Services alone aren't reachable from outside the cluster** in the general case, and don't do path- or host-based routing. You need an Ingress the moment external clients need to reach multiple services through one entry point, routed by URL path or hostname rather than one Service per exposed port.
- **This layering matters from day one of running anything under Kubernetes** — even a single-service deployment typically needs at least a Deployment (for restart-on-crash) and a Service (for a stable address), with Ingress added as soon as there's external HTTP traffic to route.

## 3. Core concept

Think of an apartment building. A **Pod** is one apartment unit — it might have more than one room (container) inside it, but the whole unit shares one street address and one set of utilities. A **Deployment** is the building management company: it decides how many units of a given floor plan should exist and rebuilds any unit that burns down, without residents needing to notice. A **Service** is the building's single listed phone number — call it, and the front desk connects you to whichever available unit can take the call, even though the specific unit answering can change day to day. An **Ingress** is the city's street directory: it looks at the address you're trying to reach and routes you to the correct *building* (Service) in the first place.

Concretely, requests flow through the layers in this order:

1. **Ingress** receives external traffic and inspects the host/path to decide which Service should handle it.
2. **Service** receives the routed request and load-balances it across its healthy backing Pods, using a stable virtual address so callers never need to know individual Pod IPs.
3. **Deployment** doesn't sit in the request path at all — it operates in the background, continuously reconciling the Pod count and replacing failed Pods, which is *why* the Service always has healthy Pods to route to.
4. **Pod** is where the actual container(s) run and the request is finally handled.

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="External traffic flows through Ingress, which routes by path to a Service, which load-balances across Pods kept alive by a Deployment">
  <rect x="10" y="20" width="110" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="65" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">External client</text>

  <rect x="170" y="20" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="235" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Ingress</text>
  <text x="235" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">routes by path/host</text>

  <rect x="350" y="20" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="415" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Service</text>
  <text x="415" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stable address, LB</text>

  <line x1="120" y1="45" x2="170" y2="45" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="300" y1="45" x2="350" y2="45" stroke="#8b949e" marker-end="url(#a1)"/>

  <rect x="330" y="150" width="60" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="174" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Pod A</text>
  <rect x="410" y="150" width="60" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="440" y="174" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Pod B</text>
  <rect x="490" y="150" width="60" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="520" y="174" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Pod C (down)</text>

  <line x1="415" y1="70" x2="360" y2="150" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="415" y1="70" x2="440" y2="150" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="415" y1="70" x2="520" y2="150" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="440" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Service skips the down Pod</text>

  <rect x="330" y="230" width="220" height="45" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="440" y="252" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Deployment</text>
  <text x="440" y="267" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">watches &amp; replaces Pod C in the background</text>
  <line x1="440" y1="230" x2="520" y2="190" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#a2)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
  </defs>
</svg>

Ingress routes by path to a Service, the Service load-balances across healthy Pods only, and a Deployment works in the background to keep the Pod pool at full strength.

## 5. Runnable example

Scenario: an `order-service` exposed to the outside world. We start with just a Deployment scheduling Pods, add a Service that load-balances across them while skipping unhealthy ones, then add an Ingress that routes two different URL paths to two different Services — and correctly returns an error for one path when its whole Service goes unhealthy, without disturbing the other path.

### Level 1 — Basic

```java
// File: PodsAndDeployments.java -- models the two most basic building
// blocks: a Pod (one or more containers sharing a network identity) and a
// Deployment (declares how many replicas of a Pod template should exist).
import java.util.*;

public class PodsAndDeployments {
    static class Pod {
        final String name;
        final String containerImage;
        Pod(String name, String containerImage) { this.name = name; this.containerImage = containerImage; }
        public String toString() { return name + "[" + containerImage + "]"; }
    }

    static class Deployment {
        final String name;
        final String image;
        int desiredReplicas;
        final List<Pod> pods = new ArrayList<>();
        int nextId = 1;

        Deployment(String name, String image, int desiredReplicas) {
            this.name = name; this.image = image; this.desiredReplicas = desiredReplicas;
        }

        void reconcile() {
            while (pods.size() < desiredReplicas) {
                Pod p = new Pod(name + "-pod-" + nextId++, image);
                pods.add(p);
                System.out.println("Deployment '" + name + "': scheduled " + p);
            }
        }
    }

    public static void main(String[] args) {
        Deployment orderService = new Deployment("order-service", "order-service:2.1", 3);
        orderService.reconcile();
        System.out.println("order-service pods: " + orderService.pods);
    }
}
```

How to run: `java PodsAndDeployments.java`

A `Pod` is just an identity plus the image it runs. A `Deployment` owns a *template* (the image) and a desired count, and `reconcile()` schedules Pods until that count is met — the same reconciliation idea from [container orchestration (Kubernetes) concepts](0446-container-orchestration-kubernetes-concepts.md), scoped specifically to Pods.

### Level 2 — Intermediate

```java
// File: ServiceLoadBalancing.java -- the SAME Deployment concept, now
// fronted by a Service: a stable virtual address that load-balances
// across whichever Pods are currently healthy, skipping unhealthy ones.
import java.util.*;

public class ServiceLoadBalancing {
    static class Pod {
        final String name;
        boolean healthy = true;
        Pod(String name) { this.name = name; }
    }

    static class Service {
        final String name;
        final List<Pod> endpoints;
        int nextIndex = 0;

        Service(String name, List<Pod> endpoints) { this.name = name; this.endpoints = endpoints; }

        String route() {
            List<Pod> healthyEndpoints = endpoints.stream().filter(p -> p.healthy).toList();
            if (healthyEndpoints.isEmpty()) return "NO HEALTHY ENDPOINTS";
            Pod target = healthyEndpoints.get(nextIndex % healthyEndpoints.size());
            nextIndex++;
            return target.name;
        }
    }

    public static void main(String[] args) {
        List<Pod> pods = List.of(new Pod("order-service-pod-1"), new Pod("order-service-pod-2"), new Pod("order-service-pod-3"));
        Service svc = new Service("order-service", pods);

        System.out.println("All pods healthy -- routing 5 requests:");
        for (int i = 0; i < 5; i++) System.out.println("  request " + (i + 1) + " -> " + svc.route());

        pods.get(1).healthy = false; // pod-2 fails a readiness probe
        System.out.println("pod-2 turns unhealthy -- routing 5 more requests:");
        for (int i = 0; i < 5; i++) System.out.println("  request " + (i + 1) + " -> " + svc.route());
    }
}
```

How to run: `java ServiceLoadBalancing.java`

`Service.route()` filters `endpoints` down to only healthy Pods before picking a target round-robin — the Kubernetes Service equivalent of using [health checks for orchestrators](0445-health-checks-for-orchestrators.md) readiness state to decide which endpoints are even eligible for traffic. Once `pod-2` turns unhealthy, it silently drops out of rotation and every request lands on `pod-1` or `pod-3` instead; the Service's address never changes, only which Pods answer behind it.

### Level 3 — Advanced

```java
// File: IngressRoutingAdvanced.java -- the SAME layers stacked together:
// Ingress (path-based external routing) -> Service (load balancing across
// healthy Pods) -> Deployment-managed Pods. Handles a PRODUCTION-FLAVORED
// hard case: one Service's entire pod fleet goes unhealthy, and Ingress
// must correctly surface that as a failure for its path WITHOUT taking
// down routing for the other, unrelated path.
import java.util.*;

public class IngressRoutingAdvanced {
    static class Pod {
        final String name;
        boolean healthy = true;
        Pod(String name) { this.name = name; }
    }

    static class Service {
        final String name;
        final List<Pod> endpoints;
        int nextIndex = 0;
        Service(String name, List<Pod> endpoints) { this.name = name; this.endpoints = endpoints; }

        String route() {
            List<Pod> healthyEndpoints = endpoints.stream().filter(p -> p.healthy).toList();
            if (healthyEndpoints.isEmpty()) return null; // no pod can serve this request
            Pod target = healthyEndpoints.get(nextIndex % healthyEndpoints.size());
            nextIndex++;
            return target.name;
        }
    }

    static class Ingress {
        final Map<String, Service> pathRules = new LinkedHashMap<>();
        void addRule(String path, Service svc) { pathRules.put(path, svc); }

        String handle(String path) {
            Service svc = pathRules.get(path);
            if (svc == null) return "404 NOT FOUND -- no Ingress rule for " + path;
            String pod = svc.route();
            if (pod == null) return "503 SERVICE UNAVAILABLE -- " + svc.name + " has no healthy endpoints";
            return "200 OK -- routed " + path + " to " + svc.name + "/" + pod;
        }
    }

    public static void main(String[] args) {
        Service orders = new Service("order-service", List.of(new Pod("order-pod-1"), new Pod("order-pod-2")));
        Service payments = new Service("payment-service", List.of(new Pod("payment-pod-1"), new Pod("payment-pod-2")));

        Ingress ingress = new Ingress();
        ingress.addRule("/orders", orders);
        ingress.addRule("/payments", payments);

        System.out.println("Steady state:");
        System.out.println("  /orders   -> " + ingress.handle("/orders"));
        System.out.println("  /payments -> " + ingress.handle("/payments"));

        System.out.println("payment-service's entire pod fleet goes unhealthy:");
        for (Pod p : payments.endpoints) p.healthy = false;

        System.out.println("  /payments -> " + ingress.handle("/payments") + "  (fails)");
        System.out.println("  /orders   -> " + ingress.handle("/orders") + "  (unaffected)");
        System.out.println("  /unknown  -> " + ingress.handle("/unknown"));
    }
}
```

How to run: `java IngressRoutingAdvanced.java`

`Ingress.handle` looks up the `Service` for a path, delegates to that Service's own load-balancing, and translates a `null` (no healthy endpoints) into a `503`. The hard case is `payment-service` losing every one of its Pods: `/payments` correctly starts returning `503`, but `/orders` is completely unaffected, because each path's Ingress rule points at an independent `Service` with its own endpoint list — a fault in one Service's Pod fleet never leaks into another Service's routing.

## 6. Walkthrough

Trace `IngressRoutingAdvanced.main` in order. **First**, `orders` and `payments` are built as independent `Service` instances, each with two healthy Pods, and both are registered into `ingress` under separate path rules.

**Next**, the steady-state calls run: `ingress.handle("/orders")` looks up `orders` in `pathRules`, calls `orders.route()`, which finds both Pods healthy and returns `order-pod-1`, formatted as `200 OK`. `ingress.handle("/payments")` does the same against `payments`, returning `payment-pod-1`.

**Then**, the simulated outage runs: the loop sets `healthy = false` on every Pod inside `payments.endpoints`. Critically, this loop never touches `orders.endpoints` at all — the two Services' Pod lists are entirely separate objects.

**Finally**, the three follow-up calls show the consequence. `ingress.handle("/payments")` calls `payments.route()`, which filters to an empty `healthyEndpoints` list and returns `null`; `handle` translates that `null` into `"503 SERVICE UNAVAILABLE"`. `ingress.handle("/orders")` is completely unaffected — `orders.route()` still finds two healthy Pods and returns normally. `ingress.handle("/unknown")` hits a path with no registered rule at all, returning `404`, demonstrating the third possible outcome (no route exists) alongside the other two (route exists and works; route exists but its Service is down).

```
Steady state:
  /orders   -> 200 OK -- routed /orders to order-service/order-pod-1
  /payments -> 200 OK -- routed /payments to payment-service/payment-pod-1
payment-service's entire pod fleet goes unhealthy:
  /payments -> 503 SERVICE UNAVAILABLE -- payment-service has no healthy endpoints  (fails)
  /orders   -> 200 OK -- routed /orders to order-service/order-pod-2  (unaffected)
  /unknown  -> 404 NOT FOUND -- no Ingress rule for /unknown
```

## 7. Gotchas & takeaways

> A Service's "stable address" only stays meaningful if something is actually keeping its backing Pods alive. A Service with zero Deployment (or an under-scaled one) behind it will faithfully load-balance across an ever-shrinking healthy pool until, like `payment-service` in Level 3, there's nothing left to route to — the Service layer doesn't create capacity, it only distributes across whatever capacity the Deployment layer maintains.

- Never hardcode a Pod's IP address or name anywhere a caller might rely on it long-term — Pods are disposable and get replaced with new identities constantly; always address a group of Pods through its Service.
- A Deployment operates entirely outside the request path — it doesn't route traffic, it just keeps the Pod count and health at the declared level in the background, which is what makes the Service layer's job possible.
- Ingress rules are typically evaluated independently per path/host, so a failure isolated to one Service's Pods (as in Level 3) doesn't have to cascade to unrelated paths — but only if each path is actually wired to its own Service, not a shared one.
- Horizontal scaling of the Pod pool behind a Deployment is covered in [Horizontal Pod Autoscaling](0448-horizontal-pod-autoscaling.md); externalizing what each Pod reads at startup is covered in [ConfigMaps & Secrets](0449-configmaps-secrets.md).
- This four-layer stack is also what deployment strategies like [rolling deployment](0450-rolling-deployment.md) and [blue-green deployment](0451-blue-green-deployment.md) operate on: they change which Pods a Deployment or Service points at, without touching Ingress rules at all.
