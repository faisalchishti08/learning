---
card: system-design
gi: 36
slug: global-server-load-balancing-geodns-anycast
title: "Global server load balancing (GeoDNS / anycast)"
---

## 1. What it is

**Global Server Load Balancing (GSLB)** routes a client to the best *data center* or *region* out of several, before the request ever reaches a regular, single-region load balancer. Two common mechanisms achieve this: **GeoDNS** (a DNS server that returns a different IP address depending on where the requester is located) and **anycast** (a networking technique where the *same* IP address is announced from multiple physical locations, and normal internet routing sends the client to the nearest one).

## 2. Why & when

A single-region load balancer only spreads traffic across servers *within one data center*. If your users are spread across continents, routing all of them to one region adds unnecessary network latency (recall the latency-numbers tutorial: a cross-continent round trip can cost over 100ms). GSLB solves this by directing each user to the nearest or best-performing region first. You bring this up in a design once a non-functional requirement calls for global users and low latency, or once availability requires surviving the loss of an entire region, not just one server.

## 3. Core concept

**GeoDNS:** a DNS provider looks at the requester's approximate location (usually inferred from their resolver's IP address) and returns a different `A` record depending on where they are — European users get the IP of a European data center; U.S. users get the IP of a U.S. data center. This reuses ordinary DNS resolution (covered earlier in this section), just with location-aware answers instead of a single fixed IP.

**Anycast:** the same IP address is advertised from multiple physical locations using the internet's routing protocol (BGP). Normal internet routing, which already tries to find the shortest network path, naturally delivers each user's traffic to whichever advertised location is topologically closest — no DNS trickery is needed, because it operates at the network-routing layer itself.

**Comparing the two:**

| | GeoDNS | Anycast |
|---|---|---|
| Mechanism | DNS resolver returns different IPs by location | Same IP, routed to nearest location by BGP |
| Failover speed | Limited by DNS TTL (can be slow to propagate) | Near-instant — routing reacts to the closest live announcer |
| Precision | Can route by more specific criteria (e.g. specific ISP) | Follows network topology, not always the true geographic nearest |

**How this fits with regional load balancers:** GSLB is the *first* routing decision — which region — and a normal load balancer inside that chosen region then makes the *second* decision — which specific server. The two work together, one layered on top of the other.

## 4. Diagram

```
                     GLOBAL LAYER (GeoDNS or anycast)
                        picks the best REGION
                              |
              +---------------+---------------+
              v                                v
      US-EAST region                    EU-WEST region
      [regional load balancer]          [regional load balancer]
              |                                |
      +-------+-------+                +-------+-------+
      v       v       v                v       v       v
   server1 server2 server3         server1 server2 server3
      (picks a SERVER within the chosen region)
```
*Caption: GSLB picks the region first; a regular regional load balancer then picks a server within it.*

## 5. Runnable example

### Artifact: a Java simulation of GeoDNS-style region selection based on client location

```java
import java.util.*;

public class GeoDnsSim {

    static final Map<String, String> regionByCountry = Map.of(
        "US", "us-east-1",
        "CA", "us-east-1",
        "DE", "eu-west-1",
        "FR", "eu-west-1",
        "JP", "ap-northeast-1"
    );

    static String resolveRegion(String clientCountry) {
        return regionByCountry.getOrDefault(clientCountry, "us-east-1"); // default fallback region
    }

    public static void main(String[] args) {
        List<String> clientCountries = List.of("US", "DE", "JP", "BR"); // BR has no explicit mapping

        for (String country : clientCountries) {
            String region = resolveRegion(country);
            System.out.println("Client in " + country + " -> DNS resolves to region: " + region);
        }
    }
}
```

**How to run:** save as `GeoDnsSim.java`, run `java GeoDnsSim.java` (JDK 17+).

## 6. Walkthrough

1. `regionByCountry` models the GeoDNS provider's configuration: which region each country's users should be routed to.
2. `resolveRegion` looks up the client's country; if there is no explicit mapping (like Brazil, `BR`, in this example), it falls back to a default region, mirroring how real GeoDNS configurations always need a sensible default for unmapped locations.
3. `main` resolves the region for four different client countries.
4. Output:
```
Client in US -> DNS resolves to region: us-east-1
Client in DE -> DNS resolves to region: eu-west-1
Client in JP -> DNS resolves to region: ap-northeast-1
Client in BR -> DNS resolves to region: us-east-1
```
5. Each client is directed to a different region based purely on location, before any request-level load balancing happens at all — this is the GSLB decision, made first, at the DNS layer, well before a regional load balancer ever sees the request.

## 7. Gotchas & takeaways

> **Gotcha:** relying on GeoDNS alone for fast failover when an entire region goes down. Because DNS answers are cached by resolvers for the record's TTL, a region failure requires waiting out that TTL before all clients pick up the new answer — for faster failover, anycast (which reacts at the routing layer, not the DNS layer) or a very low TTL combined with active health-checked DNS is needed.

- GSLB picks the best region for a client, before a regional load balancer picks a specific server within it.
- GeoDNS uses location-aware DNS answers; anycast uses network routing to reach the nearest announcer of a shared IP.
- Anycast fails over faster than GeoDNS, since it is not limited by DNS caching and TTL propagation delay.
