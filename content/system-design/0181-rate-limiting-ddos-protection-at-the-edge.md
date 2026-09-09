---
card: system-design
gi: 181
slug: rate-limiting-ddos-protection-at-the-edge
title: Rate limiting & DDoS protection at the edge
---

## 1. What it is

**Rate limiting at the edge** applies request-rate limits (like a [token bucket](0143-token-bucket.md)) at the outermost layer of the infrastructure — a CDN, a load balancer, or a dedicated edge security service — before traffic ever reaches the application servers at all. **DDoS (Distributed Denial-of-Service) protection** defends against attacks where traffic is deliberately generated from many sources at once specifically to overwhelm a service's capacity, using techniques like traffic filtering, absorbing massive volume across a distributed network, and challenging suspicious clients before they reach real application logic.

## 2. Why & when

Applying rate limiting only inside the application (as covered under [rate limiting & throttling](0143-token-bucket.md)) means malicious or excessive traffic still has to travel all the way to your servers, consuming network bandwidth and connection capacity, before being rejected — for a real DDoS attack, the sheer volume can exhaust that capacity long before any individual request is even evaluated. Edge-layer protection rejects or absorbs malicious traffic much earlier, often at infrastructure specifically built to handle massive volume (a CDN's globally distributed network), so it never reaches your actual application servers at all. Use edge-layer defenses for any public-facing service, as a first line of defense layered in front of application-level rate limiting, not as a replacement for it.

## 3. Core concept

- **Layered defense — edge first, application second:** the edge layer handles high-volume, obviously abusive traffic cheaply and at scale; the application layer still applies its own finer-grained, business-aware limits (like [per-user quotas](0148-per-user-vs-global-quotas.md)) for legitimate-looking traffic that gets through.
- **IP-based and pattern-based filtering:** the edge can block or challenge traffic from known-malicious IP ranges, or traffic matching known attack signatures (an unusually high request rate from a single source, malformed requests).
- **Challenge-response (e.g. CAPTCHA, JavaScript challenges):** suspicious clients are given a small computational or interactive challenge before being allowed through — real browsers pass easily, while simple attack scripts often cannot.
- **Absorbing volume via a distributed network:** a CDN's globally distributed points of presence can absorb an enormous volume of traffic across many locations simultaneously, which no single origin server (or even a single data center) could handle alone.
- **Anycast routing:** many DDoS-mitigation networks route traffic to the nearest healthy point of presence, spreading an attack's traffic across many geographically distributed servers instead of concentrating it on one target.

## 4. Diagram

```
   attacker traffic (millions of requests/sec from many sources)
                    |
                    v
   +--------------------------------------------------+
   | EDGE LAYER (CDN / DDoS protection service)         |
   |   - IP reputation filtering                        |
   |   - pattern-based anomaly detection                 |
   |   - challenge-response for suspicious clients       |
   |   - absorbs volume across a distributed network     |
   +--------------------------------------------------+
                    |  (only a tiny fraction of legitimate-looking traffic gets through)
                    v
   +--------------------------------------------------+
   | APPLICATION LAYER                                   |
   |   - per-user / per-API-key rate limiting             |
   |   - business logic                                   |
   +--------------------------------------------------+
```
*Caption: the edge layer absorbs and filters the vast majority of malicious volume before it ever reaches the application, which still applies its own finer-grained limits to what remains.*

## 5. Runnable example

**Level 1 — Basic.** An edge-layer IP-reputation filter, rejecting known-bad sources before any application logic runs.

**Level 2 — Pattern-based anomaly detection.** Flag and block a source sending an abnormally high request rate, even if not previously known-bad.

**Level 3 — Layered defense.** Show traffic passing the edge layer still being checked by a separate, finer-grained application-level limit.

```java
// EdgeDdosProtectionDemo.java
import java.util.*;

public class EdgeDdosProtectionDemo {

    static Set<String> knownMaliciousIps = Set.of("10.0.0.66", "10.0.0.77");
    static Map<String, Integer> requestCountLastSecond = new HashMap<>();
    static final int ANOMALY_THRESHOLD = 50; // requests/sec from a single IP - suspiciously high

    // Level 1: reject known-malicious IPs immediately, before touching anything else.
    static boolean edgeIpReputationCheck(String sourceIp) {
        if (knownMaliciousIps.contains(sourceIp)) {
            System.out.println("  EDGE REJECT (known malicious IP): " + sourceIp);
            return false;
        }
        return true;
    }

    // Level 2: flag a source sending an abnormally high rate, even if it wasn't previously known-bad.
    static boolean edgeAnomalyCheck(String sourceIp) {
        int count = requestCountLastSecond.merge(sourceIp, 1, Integer::sum);
        if (count > ANOMALY_THRESHOLD) {
            System.out.println("  EDGE REJECT (anomalous rate: " + count + " req/sec from " + sourceIp + ")");
            return false;
        }
        return true;
    }

    // Level 3: application-level per-user limit, applied only to traffic that already passed the edge.
    static Map<String, Integer> appLevelRequestCount = new HashMap<>();
    static final int APP_LEVEL_LIMIT = 10;

    static boolean applicationLevelRateLimit(String userId) {
        int count = appLevelRequestCount.merge(userId, 1, Integer::sum);
        if (count > APP_LEVEL_LIMIT) {
            System.out.println("  APPLICATION REJECT (per-user limit exceeded): " + userId);
            return false;
        }
        return true;
    }

    static void handleIncomingRequest(String sourceIp, String userId) {
        if (!edgeIpReputationCheck(sourceIp)) return;
        if (!edgeAnomalyCheck(sourceIp)) return;
        if (!applicationLevelRateLimit(userId)) return;
        System.out.println("  ALLOWED: request from " + sourceIp + " (user " + userId + ") reached the application");
    }

    public static void main(String[] args) {
        System.out.println("legitimate traffic from a normal IP:");
        for (int i = 0; i < 3; i++) handleIncomingRequest("203.0.113.5", "user-17");

        System.out.println("traffic from a KNOWN MALICIOUS IP:");
        handleIncomingRequest("10.0.0.66", "attacker");

        System.out.println("a flood of 55 requests/sec from ONE IP (not previously known-bad):");
        String floodingIp = "198.51.100.9";
        for (int i = 0; i < 55; i++) {
            boolean lastIteration = (i == 54);
            if (lastIteration) handleIncomingRequest(floodingIp, "user-99"); // only print the one that trips the threshold
            else { edgeIpReputationCheck(floodingIp); edgeAnomalyCheck(floodingIp); }
        }

        System.out.println("a legitimate-looking user exceeding the APPLICATION-level limit (passed the edge fine):");
        for (int i = 0; i < 12; i++) handleIncomingRequest("203.0.113.5", "user-17");
    }
}
```

**How to run:** save as `EdgeDdosProtectionDemo.java`, then run `java EdgeDdosProtectionDemo.java`.

## 6. Walkthrough

1. The three requests from `"203.0.113.5"` each pass `edgeIpReputationCheck` (not in `knownMaliciousIps`) and `edgeAnomalyCheck` (well under the 50 req/sec threshold), then reach `applicationLevelRateLimit`, which accumulates a per-user count that stays under `APP_LEVEL_LIMIT` — all three are printed as "ALLOWED".
2. The request from `"10.0.0.66"` fails immediately at `edgeIpReputationCheck`, since it is present in `knownMaliciousIps` — the method returns `false` right there, and `handleIncomingRequest` returns without ever calling `edgeAnomalyCheck` or the application-level check at all.
3. The flood of 55 requests from `floodingIp` each increment `requestCountLastSecond` for that IP via `edgeAnomalyCheck`; once the count exceeds `ANOMALY_THRESHOLD` (50), the 51st and later calls to `edgeAnomalyCheck` for this IP return `false` — the final printed request (the 55th) shows the "EDGE REJECT (anomalous rate...)" message, demonstrating detection based purely on request volume, with no prior knowledge that this specific IP was malicious.
4. The final batch of 12 requests, all from the already-known-good `"203.0.113.5"` and `"user-17"`, easily pass both edge checks each time (the anomaly count is per-IP, and this IP is not flooding) — but `applicationLevelRateLimit` accumulates `user-17`'s count across *all* their earlier requests too (from step 1 and this batch combined), and once it exceeds `APP_LEVEL_LIMIT` (10), the later requests in this batch are rejected specifically at the application layer, with the "APPLICATION REJECT" message.
5. This final scenario is the point of layered defense: `user-17`'s traffic never looked suspicious to the edge layer at all (a normal IP, no abnormal rate), yet the application layer's own finer-grained, business-aware limit (specific to this one user, not a blanket IP-level rule) still caught and rejected the excess — something the edge layer alone was never designed to do.

## 7. Gotchas & takeaways

> Gotcha: relying solely on edge-layer IP and rate-based filtering, with no application-level checks at all, misses attacks that stay under any single-IP rate threshold by spreading requests across many different source IPs (a real distributed denial-of-service, using genuinely many machines) — the edge layer reduces the *volume* problem significantly, but application-level, identity-aware limits (per user, per API key) remain necessary to catch abuse that does not depend on overwhelming volume from one source.

- Edge-layer defenses absorb and filter the bulk of malicious traffic before it ever reaches application servers, which is essential for surviving genuine high-volume attacks.
- Application-level rate limiting still matters even with strong edge protection, since it catches identity-specific abuse that never looks anomalous at the network level.
- Layering both is the real defense — neither alone covers every case the other catches.
- Related concepts: [Token bucket](0143-token-bucket.md) and [Per-user vs global quotas](0148-per-user-vs-global-quotas.md) (the application-level mechanisms this edge layer complements, not replaces), [Round robin & weighted round robin](0037-round-robin-weighted-round-robin.md) (a related edge-layer concern: distributing legitimate traffic once it passes filtering), [OWASP Top 10 awareness](0182-owasp-top-10-awareness.md) (broader application-security concerns beyond just traffic volume).
