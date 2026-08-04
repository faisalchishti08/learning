---
card: system-design
gi: 38
slug: least-connections-least-response-time
title: Least connections / least response time
---

## 1. What it is

**Least connections** is a load-balancing algorithm that routes each new request to whichever backend server currently has the *fewest active connections* in progress, instead of following a fixed rotation like round-robin. **Least response time** goes further, routing to the server with the best combination of few active connections *and* the fastest recent response times, actively favoring servers that are currently performing well.

## 2. Why & when

Round-robin assumes every request takes roughly the same amount of work, but real requests vary enormously — some finish in milliseconds, others take seconds. If one server happens to get a run of slow requests, round-robin keeps sending it new requests at the same fixed rate anyway, piling on more work while it is already behind. Least connections and least response time adapt to actual, current server load, which is a better fit whenever request processing times vary significantly.

## 3. Core concept

**Least connections, step by step:** the load balancer tracks how many requests are *currently in flight* (started but not yet finished) on each backend server. When a new request arrives, it goes to whichever server has the smallest count. As a request finishes, that server's count drops, making it more likely to receive the next request.

**Why this handles uneven request cost better than round-robin:** imagine server A is currently handling three slow requests, and server B just finished all its work and is idle. Round-robin would still send the next request to whichever server is "next in line", possibly server A, adding to its backlog. Least connections would correctly send it to server B, the one with capacity to spare right now.

**Least response time, step by step:** this algorithm additionally factors in each server's recent average response time, not just its current connection count. A server might have few active connections but still be responding slowly (perhaps due to a resource issue unrelated to request count, like a slow disk). Least response time avoids sending more traffic to a server that is struggling, even if its raw connection count looks low.

**The tradeoff versus round-robin:** both least-connections algorithms require the load balancer to maintain live state about every backend server (current connection counts, or response time history), which is more bookkeeping than round-robin's simple, stateless cycling. In exchange, they route more intelligently under uneven or fluctuating load.

## 4. Diagram

```
 Server A: [====3 active====]  (busy, slow requests in flight)
 Server B: [==0 active==]      (idle, just finished)
 Server C: [==1 active==]      (lightly loaded)

 Round-robin: next request -> whichever is NEXT in fixed order (ignores the above)
 Least connections: next request -> Server B (fewest active: 0)
```
*Caption: least connections adapts to real-time load, sending new requests to whichever server has the most spare capacity right now.*

## 5. Runnable example

### Artifact: a Java implementation of least-connections routing over a tracked connection-count map

```java
import java.util.*;

public class LeastConnectionsSim {

    static final Map<String, Integer> activeConnections = new LinkedHashMap<>();

    static void register(String server) {
        activeConnections.put(server, 0);
    }

    static String routeNextRequest() {
        return activeConnections.entrySet().stream()
            .min(Map.Entry.comparingByValue())
            .map(e -> {
                activeConnections.merge(e.getKey(), 1, Integer::sum); // connection starts
                return e.getKey();
            })
            .orElseThrow();
    }

    static void finishRequest(String server) {
        activeConnections.merge(server, -1, Integer::sum); // connection ends
    }

    public static void main(String[] args) {
        register("serverA");
        register("serverB");
        register("serverC");

        // Simulate serverA already handling 3 slow, still-in-progress requests.
        activeConnections.put("serverA", 3);

        String r1 = routeNextRequest();
        System.out.println("Request 1 routed to: " + r1 + " (counts now: " + activeConnections + ")");

        String r2 = routeNextRequest();
        System.out.println("Request 2 routed to: " + r2 + " (counts now: " + activeConnections + ")");

        finishRequest(r1);
        System.out.println(r1 + " finished (counts now: " + activeConnections + ")");

        String r3 = routeNextRequest();
        System.out.println("Request 3 routed to: " + r3 + " (counts now: " + activeConnections + ")");
    }
}
```

**How to run:** save as `LeastConnectionsSim.java`, run `java LeastConnectionsSim.java` (JDK 17+).

## 6. Walkthrough

1. `activeConnections` tracks each server's current in-flight request count, the state least-connections routing depends on.
2. `routeNextRequest` finds the server with the minimum current count, increments its count (since it is about to start handling one more request), and returns its name.
3. `finishRequest` decrements a server's count once one of its requests completes, making it more eligible for future requests.
4. `main` starts with `serverA` already at 3 active connections (simulating it being mid-way through slow work), then routes new requests and observes where they land.
5. Output:
```
Request 1 routed to: serverB (counts now: {serverA=3, serverB=1, serverC=0})
Request 2 routed to: serverC (counts now: {serverA=3, serverB=1, serverC=1})
serverB finished (counts now: {serverA=3, serverB=0, serverC=1})
Request 3 routed to: serverB (counts now: {serverA=3, serverB=1, serverC=1})
```
6. `serverA`, despite being "next" in a naive fixed order, never once receives a new request in this trace — every routing decision correctly avoids it because it consistently has the highest active connection count. This is exactly the adaptive behavior round-robin cannot provide.

## 7. Gotchas & takeaways

> **Gotcha:** using least connections without also accounting for request cost variability across *types* of requests, not just servers. A server handling one very heavy, long-running request can look "least busy" by connection count alone (just 1 connection) while actually being the worst choice for a new request right now — least response time addresses this by also weighing recent actual performance, not just the raw count.

- Round-robin assumes equal request cost; least connections adapts to real, current load per server.
- Least response time goes further, also considering how well each server has actually been performing recently.
- Both require the load balancer to track live per-server state, a bookkeeping cost round-robin avoids — worth it when request processing times vary significantly.
