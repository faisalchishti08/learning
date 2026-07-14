---
card: microservices
gi: 478
slug: data-plane-vs-control-plane
title: "Data plane vs control plane"
---

## 1. What it is

The **data plane** is the collection of [sidecar proxies](0479-sidecar-proxy-envoy.md) that actually handle every request — the component sitting in the direct path of every service-to-service call, applying routing, retries, and mTLS to real traffic in real time. The **control plane** is the separate, centralized component that configures the data plane — computing routing rules, security policies, and certificates, and pushing that configuration out to every proxy — but never touches application traffic itself.

## 2. Why & when

You need to understand this split because it explains both a mesh's power and its most common source of confusion during an incident:

- **Separating "what handles traffic" from "what decides how traffic should be handled" lets each scale and fail independently.** The data plane must be fast and low-latency, since it sits on the critical path of every request; the control plane can be slower and less latency-sensitive, since it's only pushing configuration updates periodically, not handling live traffic itself.
- **A control plane outage should not mean a data plane outage.** Proxies typically cache their last-received configuration and keep operating on it even if they temporarily lose contact with the control plane — meaning existing traffic keeps flowing correctly even during a control-plane hiccup, though *new* configuration changes won't propagate until it recovers.
- **Debugging requires knowing which plane a problem is actually in.** "Traffic isn't routing correctly" could mean a data-plane proxy is misbehaving, or it could mean the control plane pushed the wrong configuration to it — these are different failures requiring different fixes, and conflating them wastes debugging time.
- **You need this mental model as soon as you're operating any real service mesh** — [Istio](0486-istio-linkerd-overview.md), Linkerd, and virtually every mesh implementation share this exact architectural split, even though the specific component names differ.

## 3. Core concept

Think of an air traffic control system: the actual airplanes (the data plane) are what physically carry passengers and cargo along their routes in real time, while air traffic control (the control plane) decides the routes, altitudes, and clearances every plane should follow, communicating those instructions to the planes — but control doesn't fly the planes itself, and a plane already in the air with valid clearance keeps flying safely for a while even if it briefly loses radio contact.

Concretely:

1. **The control plane computes desired configuration** — which services can talk to which, what retry policy applies to a given route, what certificates are valid — typically derived from higher-level configuration (mesh policy objects, Kubernetes resources) that an operator declares.
2. **The control plane pushes that configuration out to every proxy in the data plane**, usually over a dedicated configuration protocol (Envoy's proxies, for example, use the xDS API to receive configuration updates from a control plane like Istio's `istiod`).
3. **Each data-plane proxy receives and caches its configuration locally**, applying it to every request it actually handles — routing decisions, retry attempts, TLS handshakes all happen inside the proxy, using the configuration it was last given.
4. **Live traffic flows entirely through the data plane** — the control plane is never in the request path; a service-to-service call never has to "ask" the control plane anything in real time.
5. **Configuration changes propagate asynchronously** — an operator updates a policy, the control plane recomputes the relevant configuration, and pushes it to the affected proxies, which then start applying the new behavior on their next requests, with some propagation delay between "the policy changed" and "every proxy is enforcing it."

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The control plane pushes configuration to data-plane proxies, but never sits in the path of actual request traffic, which flows directly between proxies" >
  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">control plane</text>

  <rect x="40" y="130" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">proxy A</text>
  <text x="120" y="172" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">data plane</text>

  <rect x="460" y="130" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">proxy B</text>
  <text x="540" y="172" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">data plane</text>

  <line x1="290" y1="70" x2="150" y2="130" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#a1)"/>
  <text x="185" y="100" fill="#8b949e" font-size="8" font-family="sans-serif">config push</text>
  <line x1="370" y1="70" x2="510" y2="130" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#a1)"/>
  <text x="460" y="100" fill="#8b949e" font-size="8" font-family="sans-serif">config push</text>

  <line x1="200" y1="160" x2="460" y2="160" stroke="#6db33f" stroke-width="2" marker-end="url(#a2)"/>
  <text x="330" y="150" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">actual request traffic -- control plane NOT in this path</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
  </defs>
</svg>

The control plane pushes configuration to proxies asynchronously; actual request traffic flows proxy-to-proxy, never through the control plane.

## 5. Runnable example

Scenario: a simulated control plane pushing routing configuration to proxies that then handle live traffic independently. We start with a basic config-push-then-handle-traffic sequence, extend it to show traffic continuing to flow correctly using cached config, then handle the hard case: the control plane being temporarily unreachable, where the data plane must keep serving traffic on its last-known-good configuration rather than failing.

### Level 1 — Basic

```java
// File: ControlPlaneConfigPush.java -- models a control plane pushing
// routing configuration to a proxy, which then uses THAT configuration to
// handle live traffic -- two clearly separate steps.
import java.util.*;

public class ControlPlaneConfigPush {
    static class Proxy {
        Map<String, String> routingConfig = new HashMap<>();

        void receiveConfig(Map<String, String> config) {
            routingConfig = config;
            System.out.println("[proxy] received config from control plane: " + config);
        }

        String handleRequest(String serviceName) {
            String target = routingConfig.get(serviceName);
            System.out.println("[proxy] routing request for '" + serviceName + "' to " + target + " (using locally cached config)");
            return target;
        }
    }

    public static void main(String[] args) {
        Proxy proxy = new Proxy();

        System.out.println("[control plane] computing and pushing routing configuration");
        proxy.receiveConfig(Map.of("inventory-service", "inventory-v2"));

        proxy.handleRequest("inventory-service");
    }
}
```

How to run: `java ControlPlaneConfigPush.java`

`receiveConfig` and `handleRequest` are entirely separate method calls — the control plane's push (`receiveConfig`) happens once, and `handleRequest` afterward only ever reads from `routingConfig`, the proxy's own local copy, never reaching back out to anything resembling a control plane while actually handling a request.

### Level 2 — Intermediate

```java
// File: DataPlaneUsesCachedConfig.java -- the SAME push-then-serve model,
// now handling MULTIPLE requests over time using the SAME cached config,
// with the control plane pushing an UPDATE partway through -- showing
// configuration changes take effect only from the next request onward.
import java.util.*;

public class DataPlaneUsesCachedConfig {
    static class Proxy {
        Map<String, String> routingConfig = new HashMap<>();

        void receiveConfig(Map<String, String> config) {
            routingConfig = config;
            System.out.println("[proxy] config updated: " + config);
        }

        String handleRequest(String requestId, String serviceName) {
            String target = routingConfig.get(serviceName);
            System.out.println("[proxy] request " + requestId + " for '" + serviceName + "' -> " + target);
            return target;
        }
    }

    public static void main(String[] args) {
        Proxy proxy = new Proxy();
        proxy.receiveConfig(Map.of("inventory-service", "inventory-v1"));

        proxy.handleRequest("req-1", "inventory-service");
        proxy.handleRequest("req-2", "inventory-service");

        System.out.println();
        System.out.println("[control plane] operator updates the routing policy -- pushing new config");
        proxy.receiveConfig(Map.of("inventory-service", "inventory-v2"));

        proxy.handleRequest("req-3", "inventory-service");
    }
}
```

How to run: `java DataPlaneUsesCachedConfig.java`

`req-1` and `req-2` are both routed to `inventory-v1`, using the config pushed before either request arrived. Only after `receiveConfig` is called a second time does `routingConfig` change — `req-3`, arriving after that push, is routed to `inventory-v2`. No request ever waits on or queries the control plane directly; each simply reads whatever `routingConfig` currently holds at the moment it's handled.

### Level 3 — Advanced

```java
// File: DataPlaneSurvivesControlPlaneOutage.java -- the SAME
// push-then-serve model, now handling the PRODUCTION-FLAVORED hard case:
// the CONTROL PLANE becomes temporarily UNREACHABLE. The data plane MUST
// keep serving live traffic correctly using its LAST KNOWN GOOD
// configuration -- a control plane outage should never mean the data
// plane stops handling requests, only that NEW config changes can't
// propagate until it recovers.
import java.util.*;

public class DataPlaneSurvivesControlPlaneOutage {
    static class ControlPlane {
        boolean reachable = true;
        Map<String, String> latestConfig = new HashMap<>();

        Map<String, String> pushConfigIfReachable(Map<String, String> newConfig) {
            if (!reachable) {
                System.out.println("[control plane] UNREACHABLE -- cannot push config right now");
                return null;
            }
            latestConfig = newConfig;
            System.out.println("[control plane] pushed config: " + newConfig);
            return newConfig;
        }
    }

    static class Proxy {
        Map<String, String> routingConfig = new HashMap<>(); // last-known-good, cached locally

        void tryReceiveConfig(ControlPlane controlPlane, Map<String, String> desiredConfig) {
            Map<String, String> pushed = controlPlane.pushConfigIfReachable(desiredConfig);
            if (pushed != null) {
                routingConfig = pushed;
                System.out.println("[proxy] config updated from control plane");
            } else {
                System.out.println("[proxy] control plane unreachable -- CONTINUING with last-known-good config: " + routingConfig);
            }
        }

        String handleRequest(String requestId, String serviceName) {
            String target = routingConfig.get(serviceName);
            System.out.println("[proxy] request " + requestId + " for '" + serviceName + "' -> " + target + " (data plane unaffected by control plane state)");
            return target;
        }
    }

    public static void main(String[] args) {
        ControlPlane controlPlane = new ControlPlane();
        Proxy proxy = new Proxy();

        proxy.tryReceiveConfig(controlPlane, Map.of("inventory-service", "inventory-v1"));
        proxy.handleRequest("req-1", "inventory-service");

        System.out.println();
        System.out.println("[incident] control plane becomes unreachable");
        controlPlane.reachable = false;

        System.out.println("[control plane] operator tries to push an update during the outage");
        proxy.tryReceiveConfig(controlPlane, Map.of("inventory-service", "inventory-v2"));

        System.out.println();
        System.out.println("--- live traffic continues to be served correctly during the control plane outage ---");
        proxy.handleRequest("req-2", "inventory-service");
        proxy.handleRequest("req-3", "inventory-service");
    }
}
```

How to run: `java DataPlaneSurvivesControlPlaneOutage.java`

`tryReceiveConfig` calls `controlPlane.pushConfigIfReachable`, which returns `null` once `reachable` is set to `false` — the `if (pushed != null)` check then routes to the `else` branch, explicitly keeping `routingConfig` unchanged and logging that the proxy is continuing on its last-known-good state. Crucially, `handleRequest` never checks `controlPlane.reachable` at all — it only ever reads `routingConfig`, so `req-2` and `req-3`, both handled during the simulated outage, are routed exactly as correctly as `req-1` was before the outage began.

## 6. Walkthrough

Trace `DataPlaneSurvivesControlPlaneOutage.main` in order. **First**, `proxy.tryReceiveConfig(controlPlane, Map.of("inventory-service", "inventory-v1"))` runs while `controlPlane.reachable` is still `true` — `pushConfigIfReachable` returns the config, `routingConfig` is updated to `inventory-v1`, and `req-1` is handled correctly using it.

**Next**, the simulated incident sets `controlPlane.reachable = false`, representing a real network partition or control-plane crash — nothing about the proxy's own state changes at this point.

**Then**, the operator's attempted update calls `tryReceiveConfig` again, this time with `inventory-v2` as the desired config. Inside `pushConfigIfReachable`, the `if (!reachable)` check is now `true`, so it prints the unreachable message and returns `null` without touching `latestConfig`. Back in `tryReceiveConfig`, `pushed` is `null`, so the `else` branch runs: `routingConfig` is explicitly left unchanged, still holding `inventory-v1`, and the proxy logs that it's continuing on its last-known-good state.

**After that**, `req-2` and `req-3` both call `handleRequest`, which reads `routingConfig.get("inventory-service")` exactly as it did for `req-1` — since `routingConfig` was never actually updated during the outage, both requests are routed to `inventory-v1`, correctly and without any error, exception, or degraded behavior.

**Finally**, the program ends having demonstrated that a complete control-plane outage, spanning an attempted (and failed) configuration push, had zero impact on the data plane's ability to keep serving live traffic — the *new* `inventory-v2` policy simply never took effect, which is the one and only consequence of the outage.

```
[control plane] pushed config: {inventory-service=inventory-v1}
[proxy] config updated from control plane
[proxy] request req-1 for 'inventory-service' -> inventory-v1 (data plane unaffected by control plane state)

[incident] control plane becomes unreachable
[control plane] operator tries to push an update during the outage
[control plane] UNREACHABLE -- cannot push config right now
[proxy] control plane unreachable -- CONTINUING with last-known-good config: {inventory-service=inventory-v1}

--- live traffic continues to be served correctly during the control plane outage ---
[proxy] request req-2 for 'inventory-service' -> inventory-v1 (data plane unaffected by control plane state)
[proxy] request req-3 for 'inventory-service' -> inventory-v1 (data plane unaffected by control plane state)
```

## 7. Gotchas & takeaways

> During a control-plane outage, it's easy to panic about "the mesh being down" when actually only *configuration propagation* is down — live traffic is very likely still flowing correctly on cached configuration. Confirm which plane is actually affected before assuming an incident is worse than it is.
- The data plane's resilience to control-plane outages is a deliberate design property of virtually every real mesh implementation, not an accident — proxies are built to operate safely on stale-but-valid configuration rather than failing open or closed the instant they lose contact.
- Configuration propagation delay is real and worth monitoring — "I updated the policy" and "every proxy is enforcing the new policy" are two different points in time, with a gap between them that matters during incident response or a security-sensitive change.
- [Sidecar proxies](0479-sidecar-proxy-envoy.md) are the data plane's concrete implementation — understanding this split is what makes sense of why a proxy restart, not a control-plane restart, is usually the right response to a single misbehaving service's traffic handling.
- When debugging mesh behavior, separate the two questions clearly: "is the configuration that was pushed correct?" (a control-plane question) versus "is the proxy applying its received configuration correctly?" (a data-plane question) — conflating them wastes debugging time chasing the wrong component.
- This is not unique to service meshes — Kubernetes itself has the same split (the API server and controllers as the control plane, kubelet and running Pods as the data plane), and the same reasoning about independent failure and cached state applies there too.
