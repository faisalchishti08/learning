---
card: microservices
gi: 479
slug: sidecar-proxy-envoy
title: "Sidecar proxy (Envoy)"
---

## 1. What it is

A **sidecar proxy** is a small network proxy process deployed alongside every application instance — in Kubernetes, as a second container inside the same Pod — through which all of that instance's inbound and outbound traffic is transparently routed. **Envoy** is the most widely used proxy for this role (it's the data-plane proxy underlying [Istio](0486-istio-linkerd-overview.md) and several other meshes), chosen for its rich, dynamically-configurable feature set: retries, circuit breaking, load balancing, mTLS termination, and detailed telemetry, all without the application knowing it's there.

## 2. Why & when

You deploy a sidecar proxy specifically to intercept traffic at the network layer, transparently, without any application-level integration:

- **A proxy running as a separate process (or library) elsewhere requires the application to know it exists and route through it explicitly.** A true sidecar, by contrast, uses network-level traffic redirection (`iptables` rules, in many Kubernetes-based meshes) so the application's normal outbound calls are captured automatically, with zero code changes.
- **Colocating the proxy in the same Pod keeps the extra network hop cheap.** Communication between the application container and its sidecar happens over `localhost`, which is fast and reliable — the proxy adds functionality without adding meaningful network latency to that first hop.
- **Per-instance deployment means per-instance failure isolation.** One Pod's sidecar crashing or misbehaving doesn't directly affect any other Pod's proxy — each instance's mesh behavior is independently scoped to that instance.
- **You use this specifically as the data-plane mechanism of a service mesh**, established as soon as you adopt one — it's the concrete "how" behind the abstract [data plane](0478-data-plane-vs-control-plane.md) concept.

## 3. Core concept

Think of airport security screening: every passenger (every network packet) passes through a checkpoint (the sidecar proxy) positioned right at their own gate, before continuing to their destination — the checkpoint doesn't require the passenger to do anything special, it's simply positioned in their path, checking and, if needed, redirecting them, entirely transparently to their travel plans.

Concretely:

1. **The sidecar (Envoy) is deployed as a second container in the same Pod** as the application container, sharing the Pod's network namespace.
2. **Traffic redirection rules route the application's outbound and inbound traffic through the sidecar** — the application makes a normal call to a service name, and network-level rules transparently send that traffic to the local proxy first, rather than directly out.
3. **The proxy applies its configured behavior** — load balancing across the destination's healthy instances, retrying on failure, terminating or originating mTLS, and recording telemetry about the call.
4. **The proxy forwards the (possibly retried, possibly load-balanced) request to the destination's own sidecar**, which applies its own inbound handling before finally passing the request to the actual destination application.
5. **The application, on both ends, never directly touches the network for mesh-managed traffic** — it makes and receives what look like completely ordinary local calls, with all the proxy-layer behavior happening invisibly around it.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application container and its sidecar proxy share a Pod; the application's traffic is transparently redirected through the local sidecar before leaving the Pod">
  <rect x="20" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Pod</text>

  <rect x="40" y="60" width="110" height="55" rx="6" fill="#141a22" stroke="#79c0ff"/>
  <text x="95" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">app container</text>

  <rect x="170" y="60" width="110" height="55" rx="6" fill="#141a22" stroke="#f0883e"/>
  <text x="225" y="83" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Envoy</text>
  <text x="225" y="98" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">sidecar proxy</text>

  <line x1="150" y1="87" x2="170" y2="87" stroke="#8b949e" marker-end="url(#a1)"/>
  <text x="160" y="80" fill="#8b949e" font-size="7" font-family="sans-serif">localhost</text>

  <line x1="300" y1="87" x2="420" y2="87" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>
  <text x="360" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">to destination's sidecar</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The application container's outbound traffic is redirected to the local Envoy sidecar over `localhost` before leaving the Pod.

## 5. Runnable example

Scenario: an application making a call that gets transparently intercepted by a local sidecar. We start with a basic transparent redirect, extend it to the sidecar applying load balancing across multiple destination instances, then handle the hard case: the sidecar detecting an unhealthy destination instance and excluding it from load balancing, without the calling application ever knowing.

### Level 1 — Basic

```java
// File: SidecarRedirectBasic.java -- models an application making a
// NORMAL call, transparently REDIRECTED through a local sidecar proxy --
// the application code never explicitly references the proxy at all.
public class SidecarRedirectBasic {
    static class EnvoySidecar {
        String forward(String destination, String request) {
            System.out.println("[envoy sidecar] intercepted outbound call to '" + destination + "', forwarding");
            return "response from " + destination;
        }
    }

    // Simulates network-level redirection: ALL app traffic passes through the local sidecar.
    static EnvoySidecar localSidecar = new EnvoySidecar();

    static String appMakeCall(String destination, String request) {
        // The app calls what LOOKS like the destination directly...
        System.out.println("[app] calling '" + destination + "' normally");
        // ...but network rules actually route it through the local sidecar first.
        return localSidecar.forward(destination, request);
    }

    public static void main(String[] args) {
        String response = appMakeCall("inventory-service", "check-stock");
        System.out.println("[app] received: " + response);
    }
}
```

How to run: `java SidecarRedirectBasic.java`

`appMakeCall` represents the application's own code, which never references `localSidecar` by name in a real system — here it's shown explicitly for clarity, but the comment marks where real traffic redirection (`iptables` rules) would make this happen transparently, with the application's code looking identical to a direct call.

### Level 2 — Intermediate

```java
// File: SidecarLoadBalancing.java -- the SAME redirect model, now with
// the sidecar applying LOAD BALANCING across MULTIPLE destination
// instances -- a capability entirely invisible to the calling application.
import java.util.*;

public class SidecarLoadBalancing {
    static class EnvoySidecar {
        List<String> knownInstances = List.of("inventory-pod-1", "inventory-pod-2", "inventory-pod-3");
        int roundRobinIndex = 0;

        String forward(String destination, String request) {
            String targetInstance = knownInstances.get(roundRobinIndex % knownInstances.size());
            roundRobinIndex++;
            System.out.println("[envoy sidecar] load-balanced '" + destination + "' call to instance: " + targetInstance);
            return "response from " + targetInstance;
        }
    }

    static EnvoySidecar localSidecar = new EnvoySidecar();

    static String appMakeCall(String destination) {
        return localSidecar.forward(destination, "check-stock");
    }

    public static void main(String[] args) {
        for (int i = 1; i <= 4; i++) {
            System.out.println("[app] call " + i);
            String response = appMakeCall("inventory-service");
            System.out.println("[app] received: " + response);
        }
    }
}
```

How to run: `java SidecarLoadBalancing.java`

`appMakeCall` is called identically four times with the same `"inventory-service"` argument — the application never picks a specific instance. `forward`'s internal `roundRobinIndex` cycles through `knownInstances`, so the four calls land on `inventory-pod-1`, `inventory-pod-2`, `inventory-pod-3`, and back to `inventory-pod-1` — load-balancing logic entirely owned and executed by the sidecar, never by the application.

### Level 3 — Advanced

```java
// File: SidecarHealthAwareLoadBalancing.java -- the SAME load-balancing
// sidecar, now handling the PRODUCTION-FLAVORED hard case: ONE known
// instance becomes UNHEALTHY (failing its own health checks). The sidecar
// must EXCLUDE it from load balancing automatically, routing calls only
// to healthy instances -- with the calling application completely
// unaware any instance ever had a problem.
import java.util.*;

public class SidecarHealthAwareLoadBalancing {
    static class EnvoySidecar {
        Map<String, Boolean> instanceHealth = new LinkedHashMap<>();
        int roundRobinIndex = 0;

        EnvoySidecar() {
            instanceHealth.put("inventory-pod-1", true);
            instanceHealth.put("inventory-pod-2", true);
            instanceHealth.put("inventory-pod-3", true);
        }

        void markUnhealthy(String instance) {
            instanceHealth.put(instance, false);
            System.out.println("[envoy sidecar] health check failed for " + instance + " -- excluding from load balancing");
        }

        String forward(String destination) {
            List<String> healthyInstances = new ArrayList<>();
            for (Map.Entry<String, Boolean> entry : instanceHealth.entrySet()) {
                if (entry.getValue()) healthyInstances.add(entry.getKey());
            }
            if (healthyInstances.isEmpty()) {
                throw new RuntimeException("no healthy instances available for " + destination);
            }
            String targetInstance = healthyInstances.get(roundRobinIndex % healthyInstances.size());
            roundRobinIndex++;
            System.out.println("[envoy sidecar] routed '" + destination + "' call to healthy instance: " + targetInstance);
            return "response from " + targetInstance;
        }
    }

    static EnvoySidecar localSidecar = new EnvoySidecar();

    static String appMakeCall(String destination) {
        return localSidecar.forward(destination);
    }

    public static void main(String[] args) {
        appMakeCall("inventory-service");
        appMakeCall("inventory-service");

        System.out.println();
        System.out.println("[incident] inventory-pod-2 starts failing health checks");
        localSidecar.markUnhealthy("inventory-pod-2");

        System.out.println();
        System.out.println("--- app keeps calling normally, unaware of the unhealthy instance ---");
        for (int i = 1; i <= 4; i++) {
            appMakeCall("inventory-service");
        }
    }
}
```

How to run: `java SidecarHealthAwareLoadBalancing.java`

`forward` rebuilds `healthyInstances` from `instanceHealth` on every call, filtering out anything marked `false`. After `markUnhealthy("inventory-pod-2")` runs, every subsequent call to `forward` only ever selects from the two remaining healthy instances — `inventory-pod-2` never appears in any routed call again, and `appMakeCall`, representing the application's own code, is completely unchanged and unaware across the entire sequence.

## 6. Walkthrough

Trace `SidecarHealthAwareLoadBalancing.main` in order. **First**, two calls to `appMakeCall` run while all three instances are healthy — `forward`'s `healthyInstances` list contains all three, and round-robin selection picks `inventory-pod-1` then `inventory-pod-2`.

**Next**, `markUnhealthy("inventory-pod-2")` runs, setting `instanceHealth.put("inventory-pod-2", false)` and printing the exclusion message — this is the only state change in the entire program; `appMakeCall` and `forward`'s code are never modified.

**Then**, the loop of four more calls begins. On each call, `forward` rebuilds `healthyInstances` fresh from `instanceHealth`, which now only includes `inventory-pod-1` and `inventory-pod-3` — `inventory-pod-2` is filtered out by the `if (entry.getValue())` check every single time, since its stored value is now `false`.

**After that**, `roundRobinIndex % healthyInstances.size()` cycles through just the two remaining healthy instances across the four calls, alternating between `inventory-pod-1` and `inventory-pod-3` — `inventory-pod-2` never appears as a selected target again, anywhere in the output.

**Finally**, the program completes having routed every post-incident call correctly and automatically around the unhealthy instance, with `appMakeCall`'s own code never once referencing health status, instance names, or any awareness that anything had changed.

```
[envoy sidecar] routed 'inventory-service' call to healthy instance: inventory-pod-1
[envoy sidecar] routed 'inventory-service' call to healthy instance: inventory-pod-2

[incident] inventory-pod-2 starts failing health checks
[envoy sidecar] health check failed for inventory-pod-2 -- excluding from load balancing

--- app keeps calling normally, unaware of the unhealthy instance ---
[envoy sidecar] routed 'inventory-service' call to healthy instance: inventory-pod-3
[envoy sidecar] routed 'inventory-service' call to healthy instance: inventory-pod-1
[envoy sidecar] routed 'inventory-service' call to healthy instance: inventory-pod-3
[envoy sidecar] routed 'inventory-service' call to healthy instance: inventory-pod-1
```

## 7. Gotchas & takeaways

> A sidecar proxy adds a real, measurable amount of resource overhead per Pod — CPU, memory, and a small amount of latency for every hop through it — multiplied across every single Pod in the mesh. This is a genuine cost of the sidecar model, not a rounding error, and it's part of what a mesh adoption decision needs to weigh honestly.
- Envoy's popularity as a sidecar comes from its dynamic configuration API (xDS) — it can receive and apply new routing, health, and security configuration from a [control plane](0478-data-plane-vs-control-plane.md) without restarting, which is essential for a mesh that needs to react to changing conditions quickly.
- The `localhost` hop between an application container and its sidecar is fast, but it's still a real hop — for extremely latency-sensitive paths, this overhead is worth measuring rather than assuming is negligible.
- Health-aware load balancing (Level 3) happening entirely inside the proxy is a direct illustration of the mesh's core value: this exact logic would otherwise need to be written, tested, and maintained inside every single calling application's own code.
- Sidecars are deployed per-instance, not shared — this gives strong failure isolation (one Pod's proxy issue doesn't cascade to another Pod) at the cost of running one proxy process per application instance, rather than one shared proxy for a whole node.
- When traffic behaves unexpectedly in a mesh, checking the sidecar's own logs and configuration (not just the application's) is usually the faster path to a root cause, since so much of the actual traffic-handling logic lives in the proxy rather than the application.
