---
card: spring-cloud
gi: 30
slug: instance-client-configuration
title: "Instance & client configuration"
---

## 1. What it is

Eureka's default behavior — register under the hostname, heartbeat every 30 seconds, cache the registry for 30 seconds — is tunable through two groups of properties: `eureka.instance.*` (how *this* instance describes itself to the registry) and `eureka.client.*` (how the client talks to the server and consumes the registry).

```properties
eureka.instance.hostname=orders-service-7f9c.internal
eureka.instance.prefer-ip-address=true
eureka.instance.lease-renewal-interval-in-seconds=10
eureka.instance.lease-expiration-duration-in-seconds=30

eureka.client.registry-fetch-interval-seconds=5
eureka.client.service-url.defaultZone=http://eureka1:8761/eureka/,http://eureka2:8761/eureka/
```

## 2. Why & when

`eureka.instance.*` controls what other services see when they discover this one: its hostname or IP, its port, its metadata, and how aggressively it heartbeats. `eureka.client.*` controls how this service talks to Eureka Server: which server(s) to contact, how often to pull down a fresh copy of the registry, and whether to register at all.

Reach for these when:

- The default 30-second heartbeat and 90-second eviction window are too slow for your environment — e.g. containers that need faster failure detection, where shrinking `lease-renewal-interval-in-seconds` and `lease-expiration-duration-in-seconds` together gets dead instances evicted sooner.
- Instances run in containers where the hostname isn't routable, so `prefer-ip-address=true` is needed to register a reachable IP instead.
- You want faster propagation of registry changes to clients, by shrinking `registry-fetch-interval-seconds` below its 30-second default (at the cost of more load on the server).
- A service should discover others but never itself be discoverable — a read-only client sets `eureka.client.register-with-eureka=false`.

## 3. Core concept

```
 eureka.instance.*  -->  describes THIS instance's registration record
     hostname / ip-address, port, lease timing, metadata

 eureka.client.*    -->  describes how THIS process talks to the server(s)
     which server URLs, fetch interval, register-with-eureka on/off,
     fetch-registry on/off
```

Instance properties shape the record other services see about you; client properties shape how you behave as a consumer of the registry.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="eureka.instance properties shape the registration record sent to the server; eureka.client properties shape how the process talks to and polls the server">
  <rect x="30" y="70" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="92" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">eureka.instance.*</text>
  <text x="140" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">hostname, ip, lease timing</text>
  <text x="140" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; the registration record</text>

  <rect x="390" y="70" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="92" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">eureka.client.*</text>
  <text x="500" y="108" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">server urls, fetch interval</text>
  <text x="500" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; how it talks to the server</text>

  <rect x="250" y="10" width="140" height="34" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="31" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka Server</text>

  <line x1="140" y1="70" x2="290" y2="44" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a30)"/>
  <line x1="500" y1="70" x2="360" y2="44" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a30)"/>

  <defs><marker id="a30" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Instance properties describe *what gets sent*; client properties describe *how it gets sent and fetched back*.

## 5. Runnable example

The scenario: model registration and heartbeat timing driven by configurable properties, starting from Eureka's defaults, then customizing the instance record, then customizing client fetch/register behavior for a read-only consumer.

### Level 1 — Basic

Defaults: 30-second heartbeat, 90-second eviction, register under hostname.

```java
public class InstanceConfigLevel1 {
    static class InstanceConfig {
        String hostname = "orders-service.internal"; // eureka.instance.hostname default
        int leaseRenewalIntervalSeconds = 30;          // eureka.instance.lease-renewal-interval-in-seconds
        int leaseExpirationDurationSeconds = 90;        // eureka.instance.lease-expiration-duration-in-seconds
    }

    public static void main(String[] args) {
        InstanceConfig cfg = new InstanceConfig();
        System.out.println("registers as: " + cfg.hostname);
        System.out.println("heartbeats every " + cfg.leaseRenewalIntervalSeconds + "s");
        System.out.println("evicted after " + cfg.leaseExpirationDurationSeconds + "s of silence");
    }
}
```

How to run: `java InstanceConfigLevel1.java`

These three fields are exactly what `eureka.instance.*` controls, shown here at their real-world default values.

### Level 2 — Intermediate

Override the instance record for a containerized deployment: prefer a routable IP address over an unroutable container hostname, and shrink lease timing for faster failure detection.

```java
public class InstanceConfigLevel2 {
    static class InstanceConfig {
        boolean preferIpAddress;
        String hostname;
        String ipAddress;
        int leaseRenewalIntervalSeconds = 30;
        int leaseExpirationDurationSeconds = 90;

        String effectiveAddress() {
            return preferIpAddress ? ipAddress : hostname;
        }
    }

    public static void main(String[] args) {
        // container hostname like "a1b2c3d4e5f6" isn't routable from other containers/hosts
        InstanceConfig cfg = new InstanceConfig();
        cfg.hostname = "a1b2c3d4e5f6";
        cfg.ipAddress = "10.0.1.5";
        cfg.preferIpAddress = true;              // eureka.instance.prefer-ip-address=true
        cfg.leaseRenewalIntervalSeconds = 10;     // faster heartbeat
        cfg.leaseExpirationDurationSeconds = 30;  // faster eviction on failure

        System.out.println("registers as: " + cfg.effectiveAddress());
        System.out.println("heartbeats every " + cfg.leaseRenewalIntervalSeconds + "s, evicted after "
                + cfg.leaseExpirationDurationSeconds + "s");
    }
}
```

How to run: `java InstanceConfigLevel2.java`

`preferIpAddress` flips which field `effectiveAddress()` returns — this mirrors `eureka.instance.prefer-ip-address=true`, essential in containers where the container ID as hostname isn't reachable from outside the container. Shrinking the lease numbers from 30/90 to 10/30 means a crashed instance is now evicted within 30 seconds instead of 90 — three heartbeat intervals either way, just a faster clock.

### Level 3 — Advanced

Add client-side configuration: a read-only consumer that fetches the registry but never registers itself, plus a custom fetch interval — the kind of setup used for a monitoring or gateway process that only needs to *discover*, never be discovered.

```java
import java.util.*;

public class InstanceConfigLevel3 {
    static class InstanceConfig {
        boolean preferIpAddress = true;
        String ipAddress = "10.0.1.5";
        int leaseRenewalIntervalSeconds = 10;
        int leaseExpirationDurationSeconds = 30;
    }

    static class ClientConfig {
        List<String> serverUrls;
        int registryFetchIntervalSeconds = 30; // eureka.client.registry-fetch-interval-seconds
        boolean registerWithEureka = true;       // eureka.client.register-with-eureka
        boolean fetchRegistry = true;            // eureka.client.fetch-registry
    }

    public static void main(String[] args) {
        InstanceConfig instance = new InstanceConfig();

        ClientConfig normalService = new ClientConfig();
        normalService.serverUrls = List.of("http://eureka1:8761/eureka/", "http://eureka2:8761/eureka/");

        ClientConfig readOnlyConsumer = new ClientConfig();
        readOnlyConsumer.serverUrls = normalService.serverUrls;
        readOnlyConsumer.registerWithEureka = false; // never registers itself
        readOnlyConsumer.registryFetchIntervalSeconds = 5; // wants fresher data, polls faster

        System.out.println("normal service: registers=" + normalService.registerWithEureka
                + ", fetches every " + normalService.registryFetchIntervalSeconds + "s");
        System.out.println("read-only consumer: registers=" + readOnlyConsumer.registerWithEureka
                + ", fetches every " + readOnlyConsumer.registryFetchIntervalSeconds + "s, "
                + "instance address=" + instance.ipAddress);
    }
}
```

How to run: `java InstanceConfigLevel3.java`

`readOnlyConsumer` sets `registerWithEureka = false` — this process (say, an admin dashboard) resolves other services' addresses but never publishes its own, matching `eureka.client.register-with-eureka=false`. Its faster `registryFetchIntervalSeconds` of 5 versus the normal service's 30 trades more load on Eureka Server for fresher discovery data — a real tuning tradeoff, not a free win.

## 6. Walkthrough

Trace Level 3's setup and its consequences, since it combines both property groups.

1. `InstanceConfig` is built first, with `preferIpAddress = true` and a real routable `ipAddress` — this is what gets sent in the registration payload the moment a service that uses this config calls `POST /eureka/apps/{appName}`, so other clients discovering it see `10.0.1.5`, not an unroutable hostname.
2. `normalService` (a `ClientConfig`) is built with `registerWithEureka` defaulted to `true` — a service using this config both registers itself and polls the registry every 30 seconds, the standard round-trip: publish presence, consume others' presence.
3. `readOnlyConsumer` is built by copying `normalService`'s server URLs but overriding two fields: `registerWithEureka = false` means no `POST /eureka/apps/...` call ever happens for this process, and `registryFetchIntervalSeconds = 5` means its background poller calls `GET /eureka/apps/` every 5 seconds instead of 30.
4. The two `println` calls show the practical effect: the normal service is both a publisher and a consumer of registry data on a 30-second cadence; the read-only consumer is purely a consumer, polling almost 6x faster, appropriate for something like a live dashboard that wants near-real-time visibility into fleet state without adding itself to that fleet.

```
InstanceConfig  --(registration payload)-->  Eureka Server
     ip=10.0.1.5, lease 10s/30s

ClientConfig (normal)     : register=true,  fetch every 30s
ClientConfig (read-only)  : register=false, fetch every 5s
```

## 7. Gotchas & takeaways

> **Gotcha:** shrinking `lease-renewal-interval-in-seconds` and `registry-fetch-interval-seconds` too aggressively across a large fleet multiplies request volume against Eureka Server linearly with instance count — a fleet of a thousand instances heartbeating every 5 seconds instead of 30 is six times the load on the server for the same fleet size.

- `eureka.instance.*` shapes the record other services see about you; `eureka.client.*` shapes how you consume records about others — don't confuse which knob affects which direction.
- `prefer-ip-address=true` is close to mandatory in containerized/Kubernetes-adjacent deployments where the container hostname isn't independently routable.
- Lease renewal interval and lease expiration duration should generally scale together — halving one without the other changes the number-of-missed-heartbeats-before-eviction ratio in a way that's easy to get wrong.
- `register-with-eureka=false` combined with `fetch-registry=true` is the standard shape for a discovery-only consumer, such as an API gateway or admin tool that must resolve services but should never itself be a routable target.
