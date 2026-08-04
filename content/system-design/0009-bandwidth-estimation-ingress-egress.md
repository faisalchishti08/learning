---
card: system-design
gi: 9
slug: bandwidth-estimation-ingress-egress
title: Bandwidth estimation (ingress/egress)
---

## 1. What it is

**Bandwidth** is the rate of data flowing across the network, usually measured in bits per second. **Ingress** is data flowing *into* your system (uploads, writes). **Egress** is data flowing *out* of your system (downloads, reads, page loads). Bandwidth estimation multiplies your QPS numbers by the size of each request or response, to find out how much network capacity your servers and load balancers actually need.

Think of it as the difference between how many cars use a road (QPS) and how wide that road needs to be (bandwidth) — a road built for a few large trucks needs different capacity than one built for many small cars, even at the same vehicle count.

## 2. Why & when

Bandwidth estimates decide network provisioning: how much capacity your load balancer and network links need, and whether egress costs (which cloud providers typically charge for) will be significant. You compute this after QPS and storage estimation, since it reuses both: QPS tells you the rate of requests, and per-record size tells you the size of each one.

## 3. Core concept

**The estimation method, step by step:**

1. **Separate reads from writes**, since they usually have different sizes and different QPS. Writes (ingress) often carry just the new data; reads (egress) often carry more, such as a full timeline of many records per response.
2. **Compute ingress:** `write QPS × average request size = ingress bytes/second`.
3. **Compute egress:** `read QPS × average response size = egress bytes/second`. Egress is very often far bigger than ingress, because a single read (like loading a feed) typically returns many records, while a single write submits just one.
4. **Convert bytes/second to bits/second** for stating network capacity (multiply by 8), since network links are conventionally rated in bits per second (e.g. Mbps, Gbps).

**A concrete pattern:** if reading a timeline returns 20 tweets at 500 bytes each, one read response is `20 × 500 = 10,000 bytes = 10 KB`, even though writing one tweet is only 500 bytes. This asymmetry is why egress bandwidth is usually the larger, more important number to size for.

## 4. Diagram

```
 WRITES (ingress)                    READS (egress)
 write QPS x avg write size          read QPS x avg response size
        |                                    |
        v                                    v
   bytes/sec IN                        bytes/sec OUT   <-- usually much bigger
        \                                    /            (one read often returns
         \                                  /              many records)
          \                                /
           total network capacity needed (x8 for bits/sec)
```
*Caption: ingress and egress are computed separately from their own QPS and size; egress is usually the dominant, larger number.*

## 5. Runnable example

### Artifact: a Java bandwidth calculator for ingress and egress

```java
public class BandwidthEstimator {

    static double bytesPerSecond(double qps, double avgBytesPerRequest) {
        return qps * avgBytesPerRequest;
    }

    static double toMbps(double bytesPerSecond) {
        return (bytesPerSecond * 8) / 1_000_000.0;
    }

    public static void main(String[] args) {
        // Writes: posting a tweet.
        double writeQps = 1_200;          // average write QPS
        double avgWriteBytes = 500;       // one tweet + metadata

        // Reads: loading a timeline of 20 tweets per request.
        double readQps = 11_000;          // average read QPS
        double avgReadBytes = 20 * 500;   // 20 tweets per timeline response

        double ingressBps = bytesPerSecond(writeQps, avgWriteBytes);
        double egressBps = bytesPerSecond(readQps, avgReadBytes);

        System.out.printf("Ingress: %.0f bytes/sec (%.2f Mbps)%n", ingressBps, toMbps(ingressBps));
        System.out.printf("Egress:  %.0f bytes/sec (%.2f Mbps)%n", egressBps, toMbps(egressBps));
        System.out.printf("Egress is %.1fx the ingress rate%n", egressBps / ingressBps);
    }
}
```

**How to run:** save as `BandwidthEstimator.java`, run `java BandwidthEstimator.java` (JDK 17+).

## 6. Walkthrough

1. `bytesPerSecond` multiplies a request rate (QPS) by the average size of that request or response, giving raw throughput in bytes per second.
2. `toMbps` converts bytes/second into megabits/second by multiplying by 8 (bits per byte) and dividing by 1,000,000, matching how network links are usually specified.
3. `main` sets up separate numbers for writes (1,200 QPS, 500 bytes each) and reads (11,000 QPS, 10,000 bytes each, since one timeline read returns 20 tweets).
4. It computes ingress and egress independently, then prints both, plus the ratio between them.
5. Output:
```
Ingress: 600000 bytes/sec (4.80 Mbps)
Egress:  110000000 bytes/sec (880.00 Mbps)
Egress is 183.3x the ingress rate
```
6. This large gap is the concrete number behind a common design statement: "this system is egress-heavy, so I'll focus on caching reads and using a Content Delivery Network (CDN) to absorb egress load, rather than optimizing the write path."

## 7. Gotchas & takeaways

> **Gotcha:** estimating bandwidth using only the write path. Because reads often return many records per response, egress can be one or two orders of magnitude larger than ingress — missing this hides the system's real network bottleneck.

- Always estimate ingress and egress separately; they rarely have the same QPS or the same per-request size.
- Remember the ×8 conversion between bytes/second and bits/second before quoting a number in Mbps or Gbps.
- A large egress number is a strong signal to bring up caching, pagination (returning fewer records per response), or a CDN in your design.
