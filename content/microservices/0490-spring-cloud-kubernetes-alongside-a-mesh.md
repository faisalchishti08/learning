---
card: microservices
gi: 490
slug: spring-cloud-kubernetes-alongside-a-mesh
title: "Spring Cloud Kubernetes alongside a mesh"
---

## 1. What it is

Running **Spring Cloud Kubernetes** alongside a service mesh means keeping [Spring Cloud Kubernetes' integration](0474-spring-cloud-kubernetes-integration.md) — specifically its ConfigMap and Secret-backed configuration loading — while letting the mesh take over service discovery and load balancing, rather than running Spring Cloud Kubernetes' `DiscoveryClient` in parallel with the mesh's own traffic routing. The two tools' capabilities overlap on discovery but not on configuration, so the right combination keeps one and drops the other, per capability.

## 2. Why & when

You need to think through this combination deliberately whenever both Spring Cloud Kubernetes and a service mesh are present in the same cluster, because their capabilities only partially overlap:

- **Spring Cloud Kubernetes' `DiscoveryClient` and the mesh's own traffic routing solve the same problem in different ways.** Once a mesh's sidecar is transparently routing every call to the correct, healthy backing Pod, an application-level `DiscoveryClient` actively querying the Kubernetes API for the same information is redundant — and in some configurations can actively conflict with the mesh's own routing decisions.
- **Spring Cloud Kubernetes' ConfigMap/Secret-backed configuration loading has no mesh equivalent at all.** A service mesh has no concept of application configuration values — it only handles network traffic — so this capability keeps its full value regardless of whether a mesh is present.
- **Simplifying application code to call a Kubernetes Service name directly, rather than going through `DiscoveryClient`, is often the cleanest approach once a mesh is active.** The mesh's sidecar already intercepts and correctly routes calls to a Service name; there's rarely a need for the application to also perform its own discovery step first.
- **You make this decision once, as part of the same mesh-adoption audit** that addresses [where Spring Cloud ends and the mesh begins](0487-where-spring-cloud-ends-and-the-mesh-begins.md) more broadly — it's a specific instance of that general principle, applied to this specific library.

## 3. Core concept

Think of a company that has both an internal mail-sorting room (Spring Cloud Kubernetes' discovery, actively looking up where to send things) and, separately, a building-wide package logistics service that already knows how to deliver anything addressed correctly to the right office (the mesh) — once the building-wide service is running, the internal mail-sorting room's lookup step for *deliveries* becomes redundant, but the mail room's *other* job of maintaining the employee directory (configuration data) is still valuable and has nothing to do with package delivery at all.

Concretely, the recommended split once both are present:

1. **Keep Spring Cloud Kubernetes' ConfigMap and Secret-backed `PropertySource`s** — this continues to populate the application's `Environment` from Kubernetes configuration objects exactly as it did before the mesh was introduced, since the mesh has no bearing on this concern whatsoever.
2. **Simplify or remove `DiscoveryClient`-based service lookup** for calls that the mesh will transparently route anyway — calling a Kubernetes Service's DNS name directly is usually sufficient, letting the mesh's sidecar handle instance selection and health-aware routing underneath.
3. **Verify there's no double load-balancing happening** — if `DiscoveryClient` is still resolving a specific Pod IP and the application is then calling that IP directly, the mesh's sidecar interception and its own load-balancing logic may be bypassed or duplicated, depending on exact configuration; calling the Service name (not a resolved Pod IP) is generally the safer approach under a mesh.
4. **Configuration loading and service discovery are evaluated as two entirely separate decisions** — a service can reasonably drop `DiscoveryClient`-based discovery while keeping ConfigMap-based configuration, since these are unrelated capabilities that happen to be bundled under the same library.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Cloud Kubernetes' ConfigMap configuration loading is kept; its DiscoveryClient-based service discovery is dropped in favor of the mesh's own routing" >
  <rect x="20" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">KEEP: ConfigMap/Secret config</text>
  <text x="165" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no mesh equivalent exists</text>
  <text x="165" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">populates the Spring Environment</text>
  <text x="165" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">unrelated to network traffic</text>

  <rect x="350" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="495" y="42" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">DROP: DiscoveryClient lookup</text>
  <text x="495" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">mesh already routes transparently</text>
  <text x="495" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">call Service DNS name directly</text>
  <text x="495" y="114" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">avoids double load-balancing</text>
</svg>

Configuration loading and service discovery are separate capabilities bundled in one library — evaluate each independently against the mesh.

## 5. Runnable example

Scenario: a service startup sequence that loads configuration from a simulated ConfigMap, then decides how to make an outbound call. We start with a basic pre-mesh version using DiscoveryClient for both discovery and configuration, extend it to a post-mesh version that keeps configuration but simplifies discovery, then handle the hard case: correctly detecting and avoiding a double load-balancing bug where the application resolves a specific Pod IP and the mesh's sidecar tries to load-balance that already-resolved call again.

### Level 1 — Basic

```java
// File: PreMeshSpringCloudKubernetes.java -- models the PRE-MESH world:
// Spring Cloud Kubernetes' DiscoveryClient handles BOTH configuration
// loading AND service discovery, since there's no mesh yet to help with
// the latter.
import java.util.*;

public class PreMeshSpringCloudKubernetes {
    static Map<String, String> loadConfigFromConfigMap() {
        Map<String, String> config = Map.of("cache.ttl-seconds", "300");
        System.out.println("[spring cloud k8s] loaded config from ConfigMap: " + config);
        return config;
    }

    static List<String> discoveryClientLookup(String serviceName) {
        List<String> instances = List.of("10.0.1.5", "10.0.1.9");
        System.out.println("[spring cloud k8s] DiscoveryClient resolved '" + serviceName + "' to: " + instances);
        return instances;
    }

    public static void main(String[] args) {
        loadConfigFromConfigMap();
        List<String> instances = discoveryClientLookup("inventory-service");
        String chosenInstance = instances.get(0);
        System.out.println("[app] calling resolved instance directly: " + chosenInstance);
    }
}
```

How to run: `java PreMeshSpringCloudKubernetes.java`

Both `loadConfigFromConfigMap` and `discoveryClientLookup` are called and used identically — in the pre-mesh world, Spring Cloud Kubernetes is the *only* mechanism handling either concern, and the application calls a specifically-resolved instance IP directly.

### Level 2 — Intermediate

```java
// File: PostMeshSimplifiedDiscovery.java -- the SAME service, now
// deployed WITH a mesh: configuration loading is UNCHANGED (kept), but
// discovery is SIMPLIFIED to just calling the Kubernetes Service NAME
// directly, letting the mesh's sidecar handle instance selection.
import java.util.*;

public class PostMeshSimplifiedDiscovery {
    static Map<String, String> loadConfigFromConfigMap() {
        // UNCHANGED from before the mesh -- configuration loading has nothing to do with the mesh.
        Map<String, String> config = Map.of("cache.ttl-seconds", "300");
        System.out.println("[spring cloud k8s] loaded config from ConfigMap: " + config + " (kept, unaffected by mesh)");
        return config;
    }

    // NO MORE DiscoveryClient call -- just the Service's DNS name, mesh handles the rest.
    static String callViaServiceName(String serviceName) {
        System.out.println("[app] calling Service name directly: " + serviceName + " (no application-level discovery)");
        System.out.println("[mesh sidecar] transparently resolving and load-balancing to a healthy instance");
        return "response from " + serviceName;
    }

    public static void main(String[] args) {
        loadConfigFromConfigMap();
        String result = callViaServiceName("inventory-service");
        System.out.println("[app] received: " + result);
    }
}
```

How to run: `java PostMeshSimplifiedDiscovery.java`

`loadConfigFromConfigMap` is byte-for-byte identical to Level 1 — configuration loading is entirely untouched by the mesh's presence. `callViaServiceName` replaces the old `discoveryClientLookup` + direct-IP-call pattern entirely: the application code no longer resolves a specific instance at all, it just calls the Service's name and lets the mesh's sidecar do that work underneath, transparently.

### Level 3 — Advanced

```java
// File: AvoidDoubleLoadBalancing.java -- the SAME simplified pattern, now
// handling the PRODUCTION-FLAVORED hard case: DETECTING a leftover bug
// where the application STILL resolves a specific Pod IP via
// DiscoveryClient (old habit, not yet cleaned up) and calls it DIRECTLY,
// which BYPASSES the mesh's own load-balancing and health-awareness
// entirely -- a real, subtle correctness bug worth catching explicitly.
import java.util.*;

public class AvoidDoubleLoadBalancing {
    static List<String> allKnownInstances = List.of("10.0.1.5", "10.0.1.9", "10.0.1.14");
    static Set<String> unhealthyInstances = Set.of("10.0.1.9"); // the mesh KNOWS this, but a raw IP call would bypass that

    // The BUGGY pattern: still using DiscoveryClient to resolve a SPECIFIC IP.
    static String buggyDirectIpCall(String serviceName) {
        String resolvedIp = allKnownInstances.get(1); // "10.0.1.9" -- happens to be the unhealthy one!
        System.out.println("[BUG] resolved specific IP via leftover DiscoveryClient call: " + resolvedIp);
        if (unhealthyInstances.contains(resolvedIp)) {
            throw new RuntimeException("call to " + resolvedIp + " FAILED -- mesh's health-awareness was BYPASSED by calling the raw IP directly");
        }
        return "response from " + resolvedIp;
    }

    // The CORRECT pattern: call the Service name, let the mesh route around unhealthy instances.
    static String correctServiceNameCall(String serviceName) {
        System.out.println("[correct] calling Service name: " + serviceName);
        List<String> healthyInstances = new ArrayList<>();
        for (String instance : allKnownInstances) {
            if (!unhealthyInstances.contains(instance)) healthyInstances.add(instance);
        }
        String routedTo = healthyInstances.get(0);
        System.out.println("[mesh sidecar] routed around unhealthy instance(s), selected: " + routedTo);
        return "response from " + routedTo;
    }

    public static void main(String[] args) {
        System.out.println("--- buggy pattern: leftover DiscoveryClient direct-IP call ---");
        try {
            buggyDirectIpCall("inventory-service");
        } catch (RuntimeException e) {
            System.out.println("[app] " + e.getMessage());
        }

        System.out.println();
        System.out.println("--- correct pattern: Service name call, mesh handles health-aware routing ---");
        String result = correctServiceNameCall("inventory-service");
        System.out.println("[app] received: " + result);
    }
}
```

How to run: `java AvoidDoubleLoadBalancing.java`

`buggyDirectIpCall` resolves a hardcoded specific IP (`allKnownInstances.get(1)`, which happens to be `10.0.1.9`) and checks it against `unhealthyInstances` directly in application code — this models the real bug of an application still calling a resolved IP directly, completely bypassing whatever health-awareness the mesh's sidecar would otherwise apply. `correctServiceNameCall`, by contrast, never resolves a specific IP in application code at all; it filters `unhealthyInstances` out and selects among the remainder, modeling the mesh sidecar's own routing logic operating correctly underneath a plain Service-name call.

## 6. Walkthrough

Trace `AvoidDoubleLoadBalancing.main` in order. **First**, the buggy pattern calls `buggyDirectIpCall("inventory-service")`. Inside it, `resolvedIp` is set to `allKnownInstances.get(1)`, which is `"10.0.1.9"` — a value the application code picked without any awareness of health status at the moment of selection.

**Next**, the `if (unhealthyInstances.contains(resolvedIp))` check runs: `unhealthyInstances` contains exactly `"10.0.1.9"`, so this check is `true`. A `RuntimeException` is thrown, explicitly explaining that the mesh's health-awareness was bypassed because the call went directly to a raw, previously-resolved IP rather than through the Service name.

**Then**, back in `main`, the `try`/`catch` around the buggy call catches this exception and prints it — demonstrating concretely that resolving a specific instance in application code, even under a mesh, can still route traffic to an instance the mesh itself already knows is unhealthy, precisely because that direct-IP call sidesteps the mesh's own routing decision entirely.

**After that**, the correct pattern calls `correctServiceNameCall("inventory-service")`. Inside it, the loop over `allKnownInstances` builds `healthyInstances` by filtering out anything present in `unhealthyInstances` — `"10.0.1.9"` is excluded, leaving `healthyInstances` with `["10.0.1.5", "10.0.1.14"]`.

**Finally**, `routedTo` is set to `healthyInstances.get(0)`, which is `"10.0.1.5"` — a healthy instance, selected without the application ever needing to know or check health status itself, since that filtering logic here stands in for what the mesh's sidecar actually does transparently underneath a plain Service-name call. `main` prints the successful result, contrasting directly with the buggy pattern's failure just above it.

```
--- buggy pattern: leftover DiscoveryClient direct-IP call ---
[BUG] resolved specific IP via leftover DiscoveryClient call: 10.0.1.9
[app] call to 10.0.1.9 FAILED -- mesh's health-awareness was BYPASSED by calling the raw IP directly

--- correct pattern: Service name call, mesh handles health-aware routing ---
[correct] calling Service name: inventory-service
[mesh sidecar] routed around unhealthy instance(s), selected: 10.0.1.5
[app] received: response from 10.0.1.5
```

## 7. Gotchas & takeaways

> Leftover `DiscoveryClient`-based direct-IP calls are exactly the kind of subtle bug that survives a mesh migration unnoticed, because the code still "works" most of the time — it only actually fails once an instance the application happened to resolve becomes unhealthy, at which point the mesh's own health-awareness, which would have routed around it, never gets a chance to help.
- Audit application code specifically for any place still calling a `DiscoveryClient`-resolved IP directly, and replace it with a plain Service-name call, once a mesh is confirmed handling that service's traffic.
- Configuration loading via ConfigMaps/Secrets keeps its full value under a mesh — there's no reason to touch or remove this half of Spring Cloud Kubernetes' functionality when adopting a mesh.
- This is a concrete, specific instance of the general principle covered in [where Spring Cloud ends and the mesh begins](0487-where-spring-cloud-ends-and-the-mesh-begins.md) — applied here to exactly one library's two genuinely separate capabilities.
- When in doubt about whether a specific piece of code is bypassing the mesh, check whether it's calling a Kubernetes Service name (safe, mesh-routed) or a specific, previously-resolved Pod IP address (bypasses the mesh's routing and health-awareness entirely).
