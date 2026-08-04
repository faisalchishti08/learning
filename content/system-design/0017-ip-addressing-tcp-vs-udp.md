---
card: system-design
gi: 17
slug: ip-addressing-tcp-vs-udp
title: IP addressing, TCP vs UDP
---

## 1. What it is

An **IP address** is the numeric identifier of a device on a network, such as `192.168.1.10` (IPv4) or a longer hexadecimal form (IPv6). **Transmission Control Protocol (TCP)** and **User Datagram Protocol (UDP)** are the two main transport protocols built on top of IP; they define *how* data actually travels between two IP addresses. TCP guarantees delivery, order, and error-checking, at the cost of some speed. UDP sends data with no guarantees at all, but is faster and has less overhead.

## 2. Why & when

Almost every system design decision about how two components talk to each other reduces to a choice between TCP and UDP-based protocols. You bring this up when justifying a communication choice: "I'll use TCP-based HTTP here because we need reliable delivery of API responses" or "I'll use UDP for video streaming because a dropped frame is fine, but a delay to retransmit it is not."

## 3. Core concept

**TCP (connection-oriented, reliable):**
- Establishes a connection first (a "handshake") before sending any data.
- Guarantees packets arrive **in order**, and **retransmits** any packet that is lost.
- Has more overhead (the handshake, acknowledgment packets, retransmission logic) which adds latency.
- Used by HTTP, most APIs, databases, email — anywhere correctness matters more than raw speed.

**UDP (connectionless, unreliable):**
- Sends packets immediately, with **no handshake and no delivery guarantee**.
- A lost packet is simply gone; the sender does not know, and does not resend it automatically.
- Much lower overhead and latency, because there is no acknowledgment or retransmission bookkeeping.
- Used for video/audio streaming, online gaming, and DNS lookups — anywhere a late retransmitted packet is more harmful than a dropped one.

**The core tradeoff in one sentence:** TCP trades speed for correctness; UDP trades correctness for speed. Choose based on whether your application can tolerate lost data (use UDP) or cannot (use TCP).

**IP addressing basics:** IPv4 addresses are 32 bits, written as four numbers 0-255 (e.g. `192.168.1.10`), giving about 4.3 billion possible addresses — a number the internet has now exhausted. IPv6 addresses are 128 bits, written in hexadecimal groups (e.g. `2606:2800:220:1::`), providing a vastly larger address space to accommodate ongoing internet growth.

## 4. Diagram

```
 TCP (reliable)                          UDP (unreliable)
 Client        Server                    Client        Server
   |--SYN------->|                         |--datagram---->|
   |<--SYN-ACK---|   (handshake first)      |--datagram---->|   (no handshake,
   |--ACK------->|                          |--datagram-X   |    no retransmit,
   |--data------>|                          |--datagram---->|    lost = gone)
   |<--ACK-------|   (every packet ACKed)
```
*Caption: TCP pays for a handshake and per-packet acknowledgment to guarantee delivery; UDP skips both for speed.*

## 5. Runnable example

### Artifact: a Java simulation contrasting TCP-style (ordered, retransmitted) delivery with UDP-style (fire-and-forget) delivery

```java
import java.util.*;

public class TcpVsUdpSim {

    // Simulates a lossy network: packet indices 2 and 5 are "dropped".
    static Set<Integer> DROPPED = Set.of(2, 5);

    static List<Integer> sendUdp(int packetCount) {
        List<Integer> delivered = new ArrayList<>();
        for (int i = 0; i < packetCount; i++) {
            if (!DROPPED.contains(i)) {
                delivered.add(i); // dropped packets are simply gone, no retry
            }
        }
        return delivered;
    }

    static List<Integer> sendTcp(int packetCount) {
        List<Integer> delivered = new ArrayList<>();
        for (int i = 0; i < packetCount; i++) {
            int attempts = 0;
            while (DROPPED.contains(i) && attempts < 3) {
                // TCP retransmits a lost packet until it is acknowledged.
                attempts++;
                if (attempts == 3) break; // simulate success on retry in this demo
            }
            delivered.add(i); // guaranteed to arrive eventually, in order
        }
        return delivered;
    }

    public static void main(String[] args) {
        int packetCount = 8;
        System.out.println("UDP delivered (dropped packets stay missing): " + sendUdp(packetCount));
        System.out.println("TCP delivered (retransmitted, always complete): " + sendTcp(packetCount));
    }
}
```

**How to run:** save as `TcpVsUdpSim.java`, run `java TcpVsUdpSim.java` (JDK 17+).

## 6. Walkthrough

1. `DROPPED` simulates a lossy network where packets 2 and 5 never arrive on the first attempt.
2. `sendUdp` loops through every packet index and only adds it to `delivered` if it was not dropped — a dropped packet under UDP is simply missing from the final list, with no retry.
3. `sendTcp` loops through every packet index too, but for any dropped packet it simulates retry attempts (standing in for TCP's real retransmission-until-acknowledged behavior) and always ends up adding it to `delivered`, since TCP guarantees eventual, in-order delivery.
4. Output:
```
UDP delivered (dropped packets stay missing): [0, 1, 3, 4, 6, 7]
TCP delivered (retransmitted, always complete): [0, 1, 2, 3, 4, 5, 6, 7]
```
5. Notice the UDP list is missing indices 2 and 5 entirely — that gap is the real behavior of a dropped video frame or a dropped game-position update: the receiver simply never gets it, and the application must decide whether that matters. The TCP list is always complete and in order, at the cost of the retransmission delay those retries represent.

## 7. Gotchas & takeaways

> **Gotcha:** choosing TCP by default for everything "because it's reliable" without considering the cost. For live video or gaming, TCP's retransmission can cause a visible stall (waiting for a lost packet to be resent) that is far more disruptive than simply skipping the lost frame, which is what UDP-based protocols do.

- TCP: connection-oriented, ordered, reliable, higher overhead — the default choice for APIs, web traffic, and anywhere correctness matters.
- UDP: connectionless, unordered, no delivery guarantee, low overhead — the right choice for real-time media and anywhere a late retry is worse than a drop.
- IPv4 addresses (32-bit) are running out; IPv6 (128-bit) is the long-term replacement — mention this if a design discusses address allocation at large scale.
