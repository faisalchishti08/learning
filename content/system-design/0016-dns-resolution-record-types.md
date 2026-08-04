---
card: system-design
gi: 16
slug: dns-resolution-record-types
title: DNS resolution & record types
---

## 1. What it is

The **Domain Name System (DNS)** is the internet's phone book. It translates a human-readable name, like `example.com`, into the numeric **Internet Protocol (IP) address** a computer needs to actually connect to a server, like `93.184.216.34`. **DNS resolution** is the step-by-step lookup process that performs this translation. A **DNS record** is one entry in that phone book, and different record **types** store different kinds of answers (an IP address, a mail server, an alias, and more).

## 2. Why & when

Every request to a named service — a browser loading a website, a mobile app calling an API — starts with a DNS lookup before any actual data can be exchanged. In a design interview, DNS comes up when you discuss how a client first finds your service, and when you discuss load balancing or failover at the DNS level (e.g. routing users to the nearest data center by returning different IP addresses to different regions).

## 3. Core concept

**The resolution process, step by step**, when a browser looks up `www.example.com`:

1. The browser checks its own **cache** first; if it recently resolved this name, it reuses the answer.
2. If not cached, it asks a **recursive resolver** (usually run by your Internet Service Provider (ISP), or a public one like `8.8.8.8`) to do the full lookup.
3. The resolver asks a **root name server**, which does not know the answer but points to the server responsible for `.com`.
4. The resolver asks that **`.com` Top-Level Domain (TLD) name server**, which points to the **authoritative name server** for `example.com`.
5. The resolver asks the **authoritative name server**, which returns the actual IP address.
6. The resolver caches the answer (for a duration called **Time To Live (TTL)**) and returns it to the browser.

**Common DNS record types:**

| Record | Stores | Example use |
|---|---|---|
| `A` | An IPv4 address | `example.com -> 93.184.216.34` |
| `AAAA` | An IPv6 address | `example.com -> 2606:2800:220:1::` |
| `CNAME` | An alias to another domain name | `www.example.com -> example.com` |
| `MX` | The mail server for a domain | routes email for `@example.com` |
| `TXT` | Arbitrary text, often for verification | domain ownership proof |
| `NS` | The authoritative name servers for a domain | delegates a subdomain |

**Design relevance — TTL and caching:** a low TTL (e.g. 60 seconds) lets you redirect traffic quickly (useful during a failover), but forces more frequent lookups. A high TTL (e.g. 24 hours) reduces lookup load but means changes propagate slowly.

## 4. Diagram

```
 Browser  --"example.com?"-->  Recursive Resolver
                                       |
                    +------------------+------------------+
                    v                  v                   v
              Root server      .com TLD server     example.com's
              "ask .com"       "ask example.com's    authoritative
                                authoritative"        server
                                                       "-> 93.184.216.34"
                                       |
                                       v
                          Resolver caches answer (TTL),
                          returns IP to Browser
```
*Caption: DNS resolution walks from root, to TLD, to the authoritative server, one delegation at a time.*

## 5. Runnable example

### Artifact: a Java simulation of DNS resolution over an in-memory record store

```java
import java.util.*;

public class DnsResolverSim {

    // Simulated authoritative records: domain -> IP.
    static final Map<String, String> A_RECORDS = Map.of(
        "example.com", "93.184.216.34",
        "api.example.com", "93.184.216.40"
    );

    // Simulated resolver cache with TTL in seconds.
    static class CacheEntry {
        String ip;
        long expiresAtEpochSecond;
        CacheEntry(String ip, long expiresAtEpochSecond) {
            this.ip = ip;
            this.expiresAtEpochSecond = expiresAtEpochSecond;
        }
    }

    static final Map<String, CacheEntry> cache = new HashMap<>();

    static String resolve(String domain, long nowEpochSecond, int ttlSeconds) {
        CacheEntry cached = cache.get(domain);
        if (cached != null && cached.expiresAtEpochSecond > nowEpochSecond) {
            System.out.println("  cache HIT for " + domain);
            return cached.ip;
        }
        System.out.println("  cache MISS for " + domain + ", walking root -> TLD -> authoritative");
        String ip = A_RECORDS.get(domain);
        if (ip == null) throw new IllegalArgumentException("NXDOMAIN: " + domain);
        cache.put(domain, new CacheEntry(ip, nowEpochSecond + ttlSeconds));
        return ip;
    }

    public static void main(String[] args) {
        long t0 = 1_000_000L;
        System.out.println("Lookup 1 at t=" + t0 + ":");
        System.out.println("  -> " + resolve("example.com", t0, 60));

        long t1 = t0 + 10; // 10 seconds later, still within the 60s TTL
        System.out.println("Lookup 2 at t=" + t1 + ":");
        System.out.println("  -> " + resolve("example.com", t1, 60));

        long t2 = t0 + 120; // 120 seconds later, TTL expired
        System.out.println("Lookup 3 at t=" + t2 + ":");
        System.out.println("  -> " + resolve("example.com", t2, 60));
    }
}
```

**How to run:** save as `DnsResolverSim.java`, run `java DnsResolverSim.java` (JDK 17+).

## 6. Walkthrough

1. `A_RECORDS` simulates the authoritative name server's data: each domain maps to one IP address.
2. `resolve` first checks the local `cache` map. If a cached entry exists and has not passed its `expiresAtEpochSecond`, it is a cache hit and no full lookup is needed.
3. On a cache miss, the code simulates the full root → TLD → authoritative walk (printed as one line, standing in for the multi-hop process shown in the diagram), looks up the IP, and stores it in the cache with a new expiry based on the TTL.
4. `main` runs three lookups: the first is a guaranteed miss (nothing cached yet), the second happens 10 seconds later and hits the cache (well within the 60-second TTL), and the third happens 120 seconds later, after the TTL has expired, forcing a fresh miss.
5. Output:
```
Lookup 1 at t=1000000:
  cache MISS for example.com, walking root -> TLD -> authoritative
  -> 93.184.216.34
Lookup 2 at t=1000010:
  cache HIT for example.com
  -> 93.184.216.34
Lookup 3 at t=1000120:
  cache MISS for example.com, walking root -> TLD -> authoritative
  -> 93.184.216.34
```
6. This mirrors real DNS behavior exactly: the first request pays the full multi-hop resolution cost, nearby requests within the TTL window are served instantly from cache, and once the TTL passes, the next request pays the full cost again.

## 7. Gotchas & takeaways

> **Gotcha:** assuming a DNS record change takes effect instantly everywhere. Resolvers around the world may have cached the old answer for up to the old TTL's duration — a failover plan that relies on DNS must lower the TTL well *before* the planned change, not during it.

- DNS resolution is a chain of delegations: root, then TLD, then the authoritative server for the specific domain.
- TTL controls the tradeoff between fast propagation of changes (low TTL) and fewer repeated lookups (high TTL).
- `A`/`AAAA` records map names to IPs; `CNAME` aliases one name to another; know these two well, the rest are situational.
