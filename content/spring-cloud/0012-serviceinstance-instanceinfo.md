---
card: spring-cloud
gi: 12
slug: serviceinstance-instanceinfo
title: "ServiceInstance & InstanceInfo"
---

## 1. What it is

`ServiceInstance` is the Commons interface describing one discovered instance of a service — its host, port, whether it's secure (HTTPS), and an arbitrary metadata map — the data type `DiscoveryClient.getInstances()` actually returns. `InstanceInfo` is Eureka's own, older, registry-specific representation carrying the same essential information plus Eureka-specific fields; Commons' `ServiceInstance` exists precisely to give application code one consistent shape regardless of which registry (Eureka, Consul, Kubernetes) actually produced the data.

```java
public interface ServiceInstance {
    String getServiceId();
    String getHost();
    int getPort();
    boolean isSecure();
    URI getUri();
    Map<String, String> getMetadata();
}
```

## 2. Why & when

This closes out the section's discovery coverage: `DiscoveryClient` (an earlier card) returns a `List<ServiceInstance>` — this card is about what's actually inside each one of those. Different registries expose different native representations (Eureka's `InstanceInfo`, Consul's own catalog entry shape) with different field names and structures; `ServiceInstance` is the Commons adapter that normalizes all of them into one consistent shape application code can rely on.

Reach for understanding `ServiceInstance`'s fields when:

- Building anything that needs more than just an address from a discovered instance — reading `getMetadata()` for a version tag, a zone/region label, or a feature-flag-style capability marker.
- Constructing a URI to actually call a discovered instance — `getUri()` already combines scheme (from `isSecure()`), host, and port correctly.
- Debugging why a load balancer or custom selection logic is choosing (or ignoring) certain instances — the answer often lives in `ServiceInstance`'s metadata.

## 3. Core concept

```
 interface ServiceInstance {
     String getServiceId();        -- "payment-service"
     String getHost();              -- "10.0.1.5"
     int getPort();                  -- 8081
     boolean isSecure();              -- false -- http, not https
     URI getUri();                    -- http://10.0.1.5:8081  (built FROM the fields above)
     Map<String, String> getMetadata(); -- { "zone": "us-east-1a", "version": "2.3.1" }
 }

 Eureka's own InstanceInfo has MORE fields (lease renewal timestamps, status, data center info, ...) --
 ServiceInstance exposes only the common subset every registry can supply, PLUS an escape-hatch metadata map.
```

`ServiceInstance` is a deliberately minimal, registry-agnostic view; `getMetadata()` is the extensibility point for anything registry-specific that doesn't fit the common fields.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Eureka InstanceInfo and Consul catalog entries both map down into the same common ServiceInstance shape">
  <rect x="20" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka InstanceInfo</text>

  <rect x="420" y="20" width="200" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="520" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Consul catalog entry</text>

  <line x1="150" y1="65" x2="280" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a32)"/>
  <line x1="490" y1="65" x2="360" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a32)"/>

  <rect x="200" y="105" width="240" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ServiceInstance (common shape)</text>

  <defs><marker id="a32" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Registry-specific representations each map down into the same common `ServiceInstance` shape.

## 5. Runnable example

The scenario: consuming discovered instance data, evolving from directly using a registry-specific representation (tightly coupled), to a normalized `ServiceInstance`-shaped adapter, to a metadata-aware selection function that picks an instance based on a zone tag — the realistic payoff of having a consistent, extensible instance shape regardless of the underlying registry.

### Level 1 — Basic

Show direct usage of a registry-specific representation — the coupling `ServiceInstance` exists to remove.

```java
public class ServiceInstanceLevel1 {
    public static void main(String[] args) {
        EurekaInstanceInfo info = new EurekaInstanceInfo("10.0.1.5", 8081, "UP", "us-east-1a");

        // Application code reads EUREKA-SPECIFIC fields directly.
        System.out.println("Calling http://" + info.ipAddr + ":" + info.port + " (status=" + info.status + ")");
    }
}

// A stand-in for Eureka's own com.netflix.appinfo.InstanceInfo, with Eureka-specific field names.
class EurekaInstanceInfo {
    String ipAddr; int port; String status; String availabilityZone;
    EurekaInstanceInfo(String ipAddr, int port, String status, String availabilityZone) {
        this.ipAddr = ipAddr; this.port = port; this.status = status; this.availabilityZone = availabilityZone;
    }
}
```

How to run: `java ServiceInstanceLevel1.java`

Application code reads `info.ipAddr`/`info.status` — field names specific to this one registry's representation; switching registries later would mean rewriting every place that reads these Eureka-specific fields.

### Level 2 — Intermediate

Add a `ServiceInstance`-shaped adapter that normalizes the Eureka-specific representation into the common Commons shape.

```java
import java.net.*;
import java.util.*;

public class ServiceInstanceLevel2 {
    public static void main(String[] args) throws Exception {
        EurekaInstanceInfo eurekaInfo = new EurekaInstanceInfo("10.0.1.5", 8081, "UP", "us-east-1a");

        ServiceInstance instance = adaptFromEureka(eurekaInfo); // normalize ONCE, at the boundary
        // Application code from here on reads only the COMMON ServiceInstance shape.
        System.out.println("Calling " + instance.getUri() + " (zone=" + instance.getMetadata().get("zone") + ")");
    }

    static ServiceInstance adaptFromEureka(EurekaInstanceInfo info) throws URISyntaxException {
        Map<String, String> metadata = new HashMap<>();
        metadata.put("zone", info.availabilityZone);
        metadata.put("status", info.status);
        return new ServiceInstanceImpl("payment-service", info.ipAddr, info.port, false, metadata);
    }
}

class EurekaInstanceInfo {
    String ipAddr; int port; String status; String availabilityZone;
    EurekaInstanceInfo(String ipAddr, int port, String status, String availabilityZone) {
        this.ipAddr = ipAddr; this.port = port; this.status = status; this.availabilityZone = availabilityZone;
    }
}

// Stands in for org.springframework.cloud.client.ServiceInstance.
interface ServiceInstance {
    String getServiceId(); String getHost(); int getPort(); boolean isSecure();
    URI getUri(); Map<String, String> getMetadata();
}

class ServiceInstanceImpl implements ServiceInstance {
    private final String serviceId, host; private final int port; private final boolean secure;
    private final Map<String, String> metadata;
    ServiceInstanceImpl(String serviceId, String host, int port, boolean secure, Map<String, String> metadata) {
        this.serviceId = serviceId; this.host = host; this.port = port; this.secure = secure; this.metadata = metadata;
    }
    public String getServiceId() { return serviceId; }
    public String getHost() { return host; }
    public int getPort() { return port; }
    public boolean isSecure() { return secure; }
    public URI getUri() { try { return new URI((secure ? "https" : "http") + "://" + host + ":" + port); } catch (Exception e) { throw new RuntimeException(e); } }
    public Map<String, String> getMetadata() { return metadata; }
}
```

How to run: `java ServiceInstanceLevel2.java`

`adaptFromEureka` is the *only* place that reads Eureka-specific field names (`ipAddr`, `availabilityZone`) — everything after that point reads the normalized `ServiceInstance` interface, including `getUri()`, which already correctly combines the scheme, host, and port into a single ready-to-use `URI`.

### Level 3 — Advanced

Add a zone-aware selection function that picks the "closest" instance based on metadata — showing why the normalized metadata map is genuinely useful, not just a compatibility formality.

```java
import java.net.*;
import java.util.*;

public class ServiceInstanceLevel3 {
    public static void main(String[] args) throws Exception {
        List<ServiceInstance> instances = List.of(
            new ServiceInstanceImpl("payment-service", "10.0.1.5", 8081, false, Map.of("zone", "us-east-1a")),
            new ServiceInstanceImpl("payment-service", "10.0.1.6", 8081, false, Map.of("zone", "us-east-1b")),
            new ServiceInstanceImpl("payment-service", "10.0.1.7", 8081, false, Map.of("zone", "us-east-1a"))
        );

        String callerZone = "us-east-1a";
        ServiceInstance chosen = selectPreferringSameZone(instances, callerZone);
        System.out.println("Caller in " + callerZone + " selected: " + chosen.getUri() + " (zone=" + chosen.getMetadata().get("zone") + ")");

        String otherCallerZone = "us-west-2a"; // no matching zone -- falls back to first available
        ServiceInstance fallback = selectPreferringSameZone(instances, otherCallerZone);
        System.out.println("Caller in " + otherCallerZone + " selected: " + fallback.getUri() + " (fallback, zone=" + fallback.getMetadata().get("zone") + ")");
    }

    // Prefers an instance in the SAME zone as the caller, using ONLY the common ServiceInstance metadata map.
    static ServiceInstance selectPreferringSameZone(List<ServiceInstance> instances, String callerZone) {
        return instances.stream()
            .filter(i -> callerZone.equals(i.getMetadata().get("zone")))
            .findFirst()
            .orElse(instances.get(0)); // fallback: any instance, if none match the caller's zone
    }
}

interface ServiceInstance {
    String getServiceId(); String getHost(); int getPort(); boolean isSecure();
    URI getUri(); Map<String, String> getMetadata();
}

class ServiceInstanceImpl implements ServiceInstance {
    private final String serviceId, host; private final int port; private final boolean secure;
    private final Map<String, String> metadata;
    ServiceInstanceImpl(String serviceId, String host, int port, boolean secure, Map<String, String> metadata) {
        this.serviceId = serviceId; this.host = host; this.port = port; this.secure = secure; this.metadata = metadata;
    }
    public String getServiceId() { return serviceId; }
    public String getHost() { return host; }
    public int getPort() { return port; }
    public boolean isSecure() { return secure; }
    public URI getUri() { try { return new URI((secure ? "https" : "http") + "://" + host + ":" + port); } catch (Exception e) { throw new RuntimeException(e); } }
    public Map<String, String> getMetadata() { return metadata; }
}
```

How to run: `java ServiceInstanceLevel3.java`

`selectPreferringSameZone` reads only `getMetadata().get("zone")` — a call that works identically regardless of whether the underlying registry was Eureka, Consul, or anything else, as long as each one's adapter populated the `zone` key consistently — this is the actual payoff of `ServiceInstance`'s metadata map: registry-specific richness (availability zones, versions, capability flags) flows through a single, uniform extension point.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three `ServiceInstance`s are built directly (bypassing the Eureka-adapter step from Level 2 for brevity), two tagged `zone=us-east-1a`, one tagged `zone=us-east-1b`.

`selectPreferringSameZone(instances, "us-east-1a")` filters for instances whose `metadata.get("zone")` equals `"us-east-1a"`, finding the first match — `10.0.1.5:8081`:

```
Caller in us-east-1a selected: http://10.0.1.5:8081 (zone=us-east-1a)
```

`selectPreferringSameZone(instances, "us-west-2a")` runs the same filter, but no instance's zone matches `"us-west-2a"` — the `filter` produces an empty stream, `findFirst()` returns empty, and `orElse(instances.get(0))` falls back to the first instance in the list regardless of its zone:

```
Caller in us-west-2a selected: http://10.0.1.5:8081 (fallback, zone=us-east-1a)
```

In a real Spring Cloud application, zone-aware instance selection like this is exactly what a `LoadBalancerClient` implementation (a later card) can layer on top of raw `DiscoveryClient` results — preferring same-zone instances to reduce cross-zone network latency and cost, falling back gracefully to any available instance when no same-zone option exists, all driven by metadata that different registries populate through their own mechanisms but which application code reads through one consistent `ServiceInstance.getMetadata()` call.

## 7. Gotchas & takeaways

> Gotcha: metadata map keys and their meaning are entirely registry- and configuration-dependent — there's no universal guarantee that every registry populates a `"zone"` key, or that different registries use the same key name for the same concept; code relying on specific metadata keys needs to know what the actual deployed registry configuration provides, not assume it based on this card's examples alone.

> Gotcha: `getUri()` builds a URI purely from `host`, `port`, and `isSecure()` — it has no awareness of any path prefix, context root, or additional routing rules a specific service might need; calling code often needs to append its own path onto the base URI `getUri()` provides.

- `ServiceInstance` is the Commons-normalized shape for one discovered instance, giving application code a consistent view regardless of which registry (Eureka, Consul, Kubernetes) actually produced the underlying data.
- `getUri()` conveniently combines scheme, host, and port into one ready-to-use URI, saving manual string concatenation.
- `getMetadata()` is the extensibility point carrying registry-specific or deployment-specific information (zone, version, custom tags) that doesn't fit the common fixed fields.
- Metadata key names and presence are not guaranteed universally — they depend on what the specific registry and its configuration actually populate, so code depending on particular keys needs to know its actual deployment's conventions.
