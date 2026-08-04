---
card: system-design
gi: 18
slug: http-1-1-http-2-http-3-quic
title: "HTTP/1.1, HTTP/2, HTTP/3 (QUIC)"
---

## 1. What it is

**HyperText Transfer Protocol (HTTP)** is the protocol web clients and servers use to exchange requests and responses. **HTTP/1.1**, **HTTP/2**, and **HTTP/3** are three successive versions of it, each solving a real performance problem the previous version had. HTTP/3 additionally replaces TCP with a new transport called **QUIC**, built on UDP, to fix a problem that HTTP/2 could not solve while still using TCP.

## 2. Why & when

The HTTP version your system uses directly affects latency, especially for pages or APIs that make many small requests. You bring this up in a design when discussing client-server communication performance, particularly for latency-sensitive, high-request-count use cases like a page loading many small images, or a mobile client on a lossy network.

## 3. Core concept

**HTTP/1.1 — one request at a time per connection (mostly):** each request typically needs to fully complete before the next one starts on the same connection. Browsers work around this by opening multiple parallel TCP connections (commonly 6 per domain), which adds overhead, since each new TCP connection needs its own handshake.

**HTTP/2 — multiplexing over one connection:** many requests and responses share a single TCP connection at the same time, interleaved as small frames, removing the need for many parallel connections. This is a major latency win when a page needs many small resources.

**The problem HTTP/2 still has — head-of-line (HOL) blocking at the TCP layer:** because HTTP/2 still runs on TCP, and TCP guarantees strictly ordered delivery, a single lost packet anywhere in the stream blocks *all* multiplexed requests on that connection until it is retransmitted — even though, logically, the other requests have nothing to do with the lost packet.

**HTTP/3 — QUIC over UDP:** HTTP/3 replaces TCP with **QUIC**, a new transport protocol built on UDP. QUIC multiplexes streams independently, so a lost packet only blocks the one stream it belongs to, not every request on the connection. QUIC also folds the TLS encryption handshake into its own connection handshake, saving a round trip when first connecting.

**When each matters in a design conversation:** HTTP/1.1 is rarely chosen deliberately today, but you may need to explain why upgrading matters. HTTP/2 is a strong, low-risk default for most APIs. HTTP/3 is worth mentioning specifically for clients on unreliable, high-latency networks (mobile), where TCP's head-of-line blocking hurts the most.

## 4. Diagram

```
 HTTP/1.1: multiple TCP connections, one request in flight per connection
 [conn1: req A---resp A][conn2: req B---resp B][conn3: req C---resp C]

 HTTP/2: one TCP connection, requests multiplexed -- but ONE lost packet
         blocks ALL streams (TCP-level head-of-line blocking)
 [conn1: A1 B1 C1 A2 (packet lost!) B2 C2 ...] <- all streams stall here

 HTTP/3 (QUIC/UDP): streams multiplexed independently --
         a lost packet blocks ONLY its own stream
 [streamA: ---X (lost, only A stalls)]
 [streamB: ------------>]   (keeps flowing)
 [streamC: ------------>]   (keeps flowing)
```
*Caption: each HTTP version removes one layer of blocking; HTTP/3's QUIC finally removes head-of-line blocking at the transport level.*

## 5. Runnable example

### Artifact: a Java simulation comparing HTTP/2-style shared-stream blocking against HTTP/3-style independent-stream delivery

```java
import java.util.*;

public class HttpVersionSim {

    // Simulates 3 streams (requests) sharing one connection, with packet #4 lost.
    static final int LOST_PACKET = 4;

    // HTTP/2 over TCP: ANY lost packet blocks every stream until it is resent.
    static Map<String, String> http2Multiplex(List<String> streamNames, int totalPackets) {
        Map<String, String> results = new LinkedHashMap<>();
        boolean blocked = false;
        for (int p = 0; p < totalPackets; p++) {
            if (p == LOST_PACKET) blocked = true; // one lost packet stalls the WHOLE connection
        }
        for (String s : streamNames) {
            results.put(s, blocked ? "STALLED until retransmit completes" : "delivered on time");
        }
        return results;
    }

    // HTTP/3 over QUIC: only the stream that owned the lost packet stalls.
    static Map<String, String> http3Independent(Map<String, Integer> streamOwningPacket) {
        Map<String, String> results = new LinkedHashMap<>();
        for (Map.Entry<String, Integer> e : streamOwningPacket.entrySet()) {
            boolean thisStreamBlocked = e.getValue() == LOST_PACKET;
            results.put(e.getKey(), thisStreamBlocked ? "STALLED (only this stream)" : "delivered on time");
        }
        return results;
    }

    public static void main(String[] args) {
        List<String> streams = List.of("streamA", "streamB", "streamC");

        System.out.println("HTTP/2 (TCP) result:");
        http2Multiplex(streams, 6).forEach((k, v) -> System.out.println("  " + k + ": " + v));

        Map<String, Integer> ownership = Map.of("streamA", 4, "streamB", 2, "streamC", 5);
        System.out.println("HTTP/3 (QUIC) result:");
        http3Independent(ownership).forEach((k, v) -> System.out.println("  " + k + ": " + v));
    }
}
```

**How to run:** save as `HttpVersionSim.java`, run `java HttpVersionSim.java` (JDK 17+).

## 6. Walkthrough

1. `LOST_PACKET` fixes packet index 4 as the one lost in this simulated network transfer, shared by both scenarios for a fair comparison.
2. `http2Multiplex` scans all packets on the shared connection; if the lost packet index is encountered anywhere, it sets `blocked = true` for the entire connection, and every stream is marked stalled — modeling TCP's strict, connection-wide ordering guarantee.
3. `http3Independent` instead tracks which specific stream "owns" each packet; only the stream whose packet was lost (`streamA`, which owned packet 4) is marked stalled, while the others are unaffected.
4. Output:
```
HTTP/2 (TCP) result:
  streamA: STALLED until retransmit completes
  streamB: STALLED until retransmit completes
  streamC: STALLED until retransmit completes
HTTP/3 (QUIC) result:
  streamA: STALLED (only this stream)
  streamB: delivered on time
  streamC: delivered on time
```
5. This is the entire argument for HTTP/3 in one comparison: the same single lost packet stalls all three requests under HTTP/2, but only the one truly affected request under HTTP/3 — the other two keep flowing.

## 7. Gotchas & takeaways

> **Gotcha:** assuming HTTP/2's multiplexing alone solves head-of-line blocking. It solves *application-level* blocking (no longer waiting for one request to finish before starting the next), but a *transport-level* (TCP) lost packet still blocks every multiplexed stream — only QUIC in HTTP/3 fixes that.

- HTTP/1.1: one request per connection at a time (workaround: many parallel connections).
- HTTP/2: multiplexes many requests over one TCP connection, but TCP's ordering still causes connection-wide stalls on packet loss.
- HTTP/3: replaces TCP with QUIC over UDP, giving independent per-stream delivery — the biggest win on lossy, high-latency (mobile) networks.
