---
card: microservices
gi: 191
slug: dns-based-discovery
title: "DNS-based discovery"
---

## 1. What it is

DNS-based discovery uses the Domain Name System itself as the service registry — resolving a logical service name (`order-service.internal`) to one or more IP addresses via ordinary DNS lookups, rather than querying a purpose-built registry like Eureka or Consul through a dedicated client library. This is the mechanism underlying Kubernetes' own built-in service discovery, among other platforms.

## 2. Why & when

Every environment and every programming language already has DNS resolution support built in, with no special client library, no additional dependency, and no new protocol to learn — a huge practical advantage over registry-specific client libraries that need to be integrated per-language and kept in sync with the registry's own API evolution. DNS-based discovery trades away some of a purpose-built registry's richer capabilities (arbitrary [metadata](0190-instance-metadata-tagging.md), fine-grained health status beyond simple presence/absence in the DNS response) in exchange for this near-universal compatibility and operational simplicity.

Use DNS-based discovery when the deployment platform already provides it natively (Kubernetes' `Service` DNS names being the dominant example) or when broad language/tooling compatibility matters more than a registry's richer metadata and query capabilities. Reach for a purpose-built registry (Eureka, Consul) when metadata-driven routing, fine-grained health semantics, or discovery query features beyond simple name resolution are genuinely needed.

## 3. Core concept

A DNS record for a service name resolves to the IP addresses of its current healthy instances; a caller performs an ordinary DNS lookup (the same mechanism used to resolve any internet hostname) to get back this list, and the platform's DNS server is responsible for keeping the record's answer set current as instances come and go.

```java
// an ORDINARY DNS lookup -- no registry-specific client library needed
InetAddress[] addresses = InetAddress.getAllByName("order-service.internal");
// addresses now contains the CURRENT healthy instance IPs, resolved via plain DNS

// this works IDENTICALLY in any language with DNS support -- Java, Python, Go, curl, anything
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caller performs an ordinary DNS lookup for order-service.internal; the platform's DNS server, kept current by the platform's own instance lifecycle tracking, resolves the name to the current set of healthy instance IP addresses" >
  <rect x="20" y="60" width="130" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="85" y="87" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller</text>

  <rect x="230" y="55" width="180" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="78" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">DNS: order-service.internal</text>
  <text x="320" y="94" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">resolves to current IPs</text>

  <rect x="480" y="30" width="130" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="545" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">10.0.1.5</text>
  <rect x="480" y="95" width="130" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/><text x="545" y="115" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">10.0.1.6</text>

  <line x1="150" y1="82" x2="228" y2="82" stroke="#8b949e" marker-end="url(#arr72)"/>
  <line x1="410" y1="72" x2="478" y2="45" stroke="#8b949e" marker-end="url(#arr72)"/>
  <line x1="410" y1="90" x2="478" y2="110" stroke="#8b949e" marker-end="url(#arr72)"/>

  <defs>
    <marker id="arr72" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Plain DNS resolution stands in for a purpose-built registry's lookup step, using infrastructure every environment already has.

## 5. Runnable example

Scenario: a caller reaching order-service that starts with a simulated purpose-built registry client requiring a specific dependency, replaces it with a simulated plain DNS lookup requiring no special client at all, and finally demonstrates DNS-based discovery's practical limitation — no rich metadata support — by contrasting what's possible with a metadata-aware registry versus DNS alone.

### Level 1 — Basic

```java
// File: RegistryClientDependency.java -- reaching order-service REQUIRES a
// SPECIFIC registry client library and its OWN API, a real integration dependency.
import java.util.*;

public class RegistryClientDependency {
    // stands in for a purpose-built registry client -- a SPECIFIC dependency, with its OWN API
    static class EurekaStyleRegistryClient {
        List<String> lookup(String serviceName) {
            return List.of("10.0.1.5:8080", "10.0.1.6:8080"); // simulated registry response
        }
    }

    public static void main(String[] args) {
        EurekaStyleRegistryClient client = new EurekaStyleRegistryClient(); // a DEPENDENCY every service needs
        List<String> instances = client.lookup("order-service"); // registry-SPECIFIC API call
        System.out.println("Instances via registry client: " + instances);
        System.out.println("This required a SPECIFIC client library dependency and its OWN, non-standard API.");
    }
}
```

**How to run:** `javac RegistryClientDependency.java && java RegistryClientDependency` (JDK 17+).

### Level 2 — Intermediate

```java
// File: PlainDnsLookup.java -- resolves the SAME service via ORDINARY DNS --
// NO special client library, just standard java.net API every JVM already has.
import java.net.*;

public class PlainDnsLookup {
    public static void main(String[] args) {
        try {
            // an ORDINARY DNS lookup -- standard java.net.InetAddress, no registry-specific library at all
            InetAddress[] addresses = InetAddress.getAllByName("localhost"); // "localhost" stands in for "order-service.internal"
            System.out.println("Resolved via PLAIN DNS: " + java.util.Arrays.toString(addresses));
            System.out.println("This used ONLY standard java.net -- the SAME mechanism ANY language's DNS resolver uses, no special dependency.");
        } catch (UnknownHostException e) {
            System.out.println("DNS lookup failed: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac PlainDnsLookup.java && java PlainDnsLookup` (JDK 17+).

Expected output (the resolved address depends on your local machine's `localhost` configuration, typically `127.0.0.1` or `::1`):
```
Resolved via PLAIN DNS: [localhost/127.0.0.1]
This used ONLY standard java.net -- the SAME mechanism ANY language's DNS resolver uses, no special dependency.
```

### Level 3 — Advanced

```java
// File: DnsLimitationVsRegistryMetadata.java -- DNS gives back ONLY addresses;
// a purpose-built registry can ALSO return METADATA (region, version, canary) --
// the concrete trade-off DNS-based discovery accepts for its simplicity.
import java.util.*;

public class DnsLimitationVsRegistryMetadata {
    record ServiceInstance(String host, Map<String, String> metadata) {}

    // DNS-based discovery: returns ONLY addresses, NOTHING else
    static List<String> dnsLookup(String serviceName) {
        return List.of("10.0.1.5", "10.0.1.6", "10.0.9.9"); // just IPs -- NO region, version, or canary info AT ALL
    }

    // purpose-built registry: returns addresses PLUS rich metadata
    static List<ServiceInstance> registryLookup(String serviceName) {
        return List.of(
            new ServiceInstance("10.0.1.5", Map.of("region", "us-east", "canary", "false")),
            new ServiceInstance("10.0.1.6", Map.of("region", "us-east", "canary", "true")),
            new ServiceInstance("10.0.9.9", Map.of("region", "eu-west", "canary", "false")));
    }

    public static void main(String[] args) {
        List<String> dnsResults = dnsLookup("order-service");
        System.out.println("DNS lookup result: " + dnsResults);
        System.out.println("A caller using PLAIN DNS has NO WAY to know which of these is same-region, or which is a canary -- that information simply doesn't exist in a DNS response.");

        List<ServiceInstance> registryResults = registryLookup("order-service");
        List<ServiceInstance> sameRegionNonCanary = registryResults.stream()
            .filter(i -> i.metadata().get("region").equals("us-east") && i.metadata().get("canary").equals("false"))
            .toList();
        System.out.println("\nRegistry lookup result: " + registryResults);
        System.out.println("Same-region, non-canary candidates (impossible with plain DNS alone): " + sameRegionNonCanary.stream().map(ServiceInstance::host).toList());
    }
}
```

**How to run:** `javac DnsLimitationVsRegistryMetadata.java && java DnsLimitationVsRegistryMetadata` (JDK 17+).

Expected output:
```
DNS lookup result: [10.0.1.5, 10.0.1.6, 10.0.9.9]
A caller using PLAIN DNS has NO WAY to know which of these is same-region, or which is a canary -- that information simply doesn't exist in a DNS response.

Registry lookup result: [ServiceInstance[host=10.0.1.5, metadata={region=us-east, canary=false}], ServiceInstance[host=10.0.1.6, metadata={region=us-east, canary=true}], ServiceInstance[host=10.0.9.9, metadata={region=eu-west, canary=false}]]
Same-region, non-canary candidates (impossible with plain DNS alone): [10.0.1.5]
```

## 6. Walkthrough

1. **Level 1** — `EurekaStyleRegistryClient` is a stand-in for a specific, non-standard client library that every service needing to call `order-service` would need to include as a dependency; `client.lookup("order-service")` is a registry-specific method, not a language-standard API.
2. **Level 2, standard library resolution** — `InetAddress.getAllByName(...)` is part of `java.net`, present in every JVM without any additional dependency; the identical call pattern would work in any Java application, and every other language has its own directly equivalent standard-library DNS resolution function.
3. **Level 2, the universality claim demonstrated** — the code compiles and runs using only `import java.net.*`, with no external library, directly substantiating the claim that DNS-based discovery requires no special client integration.
4. **Level 3, the DNS response's shape** — `dnsLookup` returns a plain `List<String>` of IP addresses, structurally mirroring what a real DNS `A` record lookup returns: addresses, and nothing more — no region tag, no version, no canary flag, because DNS responses fundamentally don't carry arbitrary structured metadata.
5. **Level 3, the registry response's richer shape** — `registryLookup` returns `List<ServiceInstance>`, where each instance pairs its address with a `Map<String, String> metadata`, directly mirroring [instance metadata & tagging](0190-instance-metadata-tagging.md)'s registration model.
6. **Level 3, the filtering only the registry can support** — `sameRegionNonCanary` is computed via `.filter(i -> i.metadata()...)`, a query that depends entirely on the metadata fields present in `registryLookup`'s result; there is no equivalent operation possible against `dnsResults`, since that list contains no information beyond bare addresses to filter on.
7. **Level 3, the trade-off made concrete** — the printed comparison shows both lookup results side by side, with the registry-based result enabling a specific, useful filtering operation (finding the one same-region, non-canary instance) that the DNS-based result structurally cannot support — this is the precise, demonstrated cost of DNS-based discovery's simplicity: universal compatibility and zero special dependencies, in exchange for giving up the ability to route based on anything beyond an instance's mere presence or absence in the resolved address list.

## 7. Gotchas & takeaways

> **Gotcha:** DNS responses are often cached, both by client-side resolvers and by intermediate caching layers, for a duration controlled by the record's TTL (time-to-live) value — a TTL set too high means DNS-based discovery can lag noticeably behind the platform's actual current instance state, effectively reintroducing a staleness problem similar to (though usually less severe than) a poorly-tuned cache in a purpose-built registry client; TTL needs deliberate tuning against how quickly instances actually change in the given environment.

- DNS-based discovery resolves a logical service name to its current healthy instance addresses via ordinary DNS lookups, using infrastructure and client support every environment and language already has.
- This trades away a purpose-built registry's richer capabilities — arbitrary metadata, fine-grained health semantics, metadata-based filtering — in exchange for broad, near-universal compatibility with no special client library dependency.
- Kubernetes' built-in `Service` DNS names are the dominant real-world example of DNS-based discovery in production use.
- Choose DNS-based discovery when broad compatibility and operational simplicity outweigh the need for richer, metadata-driven routing capabilities; choose a purpose-built registry when those richer capabilities are genuinely needed.
- DNS response caching, governed by record TTL, can introduce its own staleness if not tuned appropriately for how quickly the underlying instance set actually changes.
