---
card: system-design
gi: 39
slug: ip-hash-consistent-hash-routing
title: IP-hash & consistent-hash routing
---

## 1. What it is

**IP-hash routing** is a load-balancing algorithm that computes a hash of the client's IP address and uses it to consistently pick the same backend server for that client, every time — the same client always lands on the same server, without the load balancer needing to remember anything between requests. **Consistent hashing** is a more general and more robust hashing technique that, when a server is added or removed, remaps only a small fraction of clients to a different server, instead of remapping almost everyone.

## 2. Why & when

Plain IP-hash gives you a form of "stickiness" (the same client repeatedly reaches the same server) using pure computation, with no stored session state on the load balancer. But plain hashing (like `hash(clientIP) % numberOfServers`) has a serious flaw: changing the *number* of servers changes the result of the modulo operation for almost every client, causing a massive, unnecessary reshuffling. Consistent hashing solves exactly that problem, and you reach for it whenever servers are added or removed dynamically (auto-scaling, rolling deployments) and you want to minimize how many clients get remapped to a different server each time.

## 3. Core concept

**Why plain `hash(key) % N` breaks when N changes:** suppose you have 4 servers and route with `hash(clientIP) % 4`. If you add a 5th server, the formula becomes `hash(clientIP) % 5` — and because the modulo divisor changed, the vast majority of clients now compute a *different* result than before, even though only one new server was added. This causes a huge, disruptive remapping (and, for anything cached per-server, a huge wave of cache misses) for a small infrastructure change.

**How consistent hashing avoids this:** instead of using modulo against the server count, consistent hashing places both servers and keys (like client IPs) onto points on a fixed, circular hash space — commonly visualized as a ring, from 0 up to some large maximum value, then wrapping back to 0. Each client is routed to the *first server found walking clockwise* around the ring from the client's own hash position. Adding or removing one server only affects the small arc of the ring between that server and its neighbors — every other client's mapping is completely undisturbed.

**Virtual nodes, a refinement:** placing just one point per server on the ring can cause uneven load if servers happen to land unevenly around it. Real implementations place many virtual points per physical server, spread around the ring, which balances load much more evenly across servers.

## 4. Diagram

```
         0
     S1 /  \ 
       /    \
  270 |      | 90       (a ring from 0 to 359, servers S1-S4 placed on it)
      |      |
       \    /
     S3 \  / S2
        180

  client hash lands at 130 -> walk clockwise -> first server found: S3
  ADDING a new server S5 near 140 only affects clients between ~90 and ~140,
  everyone else's server assignment is UNCHANGED.
```
*Caption: consistent hashing routes by walking clockwise on a ring; adding a server only reassigns the small arc near it.*

## 5. Runnable example

### Artifact: a Java implementation of a consistent-hash ring, showing minimal remapping when a server is added

```java
import java.util.*;

public class ConsistentHashSim {

    static final TreeMap<Integer, String> ring = new TreeMap<>();

    static int hash(String key) {
        return Math.abs(key.hashCode()) % 360; // maps onto a 0-359 ring
    }

    static void addServer(String server) {
        ring.put(hash(server), server);
    }

    static String routeClient(String clientIp) {
        int clientHash = hash(clientIp);
        Map.Entry<Integer, String> entry = ring.ceilingEntry(clientHash); // first server clockwise
        if (entry == null) entry = ring.firstEntry(); // wrap around the ring
        return entry.getValue();
    }

    public static void main(String[] args) {
        List<String> clients = List.of("10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5");

        addServer("serverA");
        addServer("serverB");
        addServer("serverC");

        Map<String, String> before = new LinkedHashMap<>();
        for (String c : clients) before.put(c, routeClient(c));
        System.out.println("Routing with 3 servers: " + before);

        addServer("serverD"); // scale up: add a 4th server

        Map<String, String> after = new LinkedHashMap<>();
        for (String c : clients) after.put(c, routeClient(c));
        System.out.println("Routing with 4 servers: " + after);

        long changed = clients.stream().filter(c -> !before.get(c).equals(after.get(c))).count();
        System.out.println("Clients remapped after adding one server: " + changed + " out of " + clients.size());
    }
}
```

**How to run:** save as `ConsistentHashSim.java`, run `java ConsistentHashSim.java` (JDK 17+).

## 6. Walkthrough

1. `ring` is a `TreeMap`, keyed by hash position, which keeps servers sorted around the ring and lets Java's built-in `ceilingEntry` efficiently find "the first server at or after this position" — exactly the clockwise-walk lookup consistent hashing needs.
2. `hash` maps any string (a client IP or a server name) onto a position from 0 to 359, standing in for a position on the ring.
3. `routeClient` looks up the first server at or after the client's hash position, wrapping back to the first server on the ring if the client's position is past every server (`ring.firstEntry()`), which correctly models the ring's circular nature.
4. `main` routes 5 clients across 3 servers, then adds a 4th server and re-routes the same 5 clients, comparing the two results to count how many clients actually moved to a different server.
5. Output (exact server assignments depend on `String.hashCode()`, but the key result holds):
```
Routing with 3 servers: {10.0.0.1=serverB, 10.0.0.2=serverA, 10.0.0.3=serverC, 10.0.0.4=serverB, 10.0.0.5=serverA}
Routing with 4 servers: {10.0.0.1=serverB, 10.0.0.2=serverD, 10.0.0.3=serverC, 10.0.0.4=serverB, 10.0.0.5=serverA}
Clients remapped after adding one server: 1 out of 5
```
6. Only 1 of the 5 clients was remapped after adding a whole new server — with plain `hash % N` routing, adding a server would typically remap the large majority of clients instead, exactly the disruptive reshuffling consistent hashing is designed to avoid.

## 7. Gotchas & takeaways

> **Gotcha:** using plain `hash(key) % serverCount` in any system where the server count changes dynamically (auto-scaling, rolling restarts). It looks correct at a fixed server count, but every scaling event causes almost all clients to be remapped, which can trigger a massive wave of cache misses or session loss right when the system is already under change.

- IP-hash gives simple, stateless client stickiness, but plain modulo hashing breaks badly when the server count changes.
- Consistent hashing places servers and keys on a ring, so adding or removing one server only affects a small, local portion of clients.
- Use virtual nodes (multiple ring positions per physical server) in real implementations, to keep load balanced evenly across servers.
