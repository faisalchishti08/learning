---
card: system-design
gi: 40
slug: sticky-sessions-session-affinity
title: Sticky sessions (session affinity)
---

## 1. What it is

**Sticky sessions**, also called **session affinity**, is a load balancer configuration that routes all of a *specific client's* requests to the *same specific backend server*, for as long as that client's session lasts, instead of spreading their requests across whichever server the routing algorithm would normally pick. The load balancer typically achieves this by setting a cookie that identifies which server a client was first assigned to, and reading that cookie on every subsequent request.

## 2. Why & when

Some applications store session state — like a shopping cart, or a user's login session — directly in a single server's memory, rather than in a shared, external store. If a client's requests bounce between different servers, and each server only knows about its own local session data, the client's session appears to randomly disappear or reset whenever they happen to hit a different server. Sticky sessions work around this by guaranteeing a client always reaches the server that holds their in-memory session data.

## 3. Core concept

**How sticky sessions work, in Spring or any typical web application:**
1. A client's first request arrives with no session-identifying cookie; the load balancer picks a server using its normal algorithm (round-robin, least connections, etc.).
2. The load balancer (or the chosen server) sets a cookie identifying that specific server.
3. Every subsequent request from that client includes the cookie; the load balancer reads it and routes directly to the same server, bypassing its normal routing algorithm entirely for that request.

**The real cost — sticky sessions fight against load balancing's own purpose:** if one server happens to accumulate many "stuck" clients with long sessions, that server can become overloaded while others remain underused, precisely because the load balancer is now deliberately *not* spreading that traffic evenly — it is honoring stickiness over balance.

**It also breaks the availability benefit of having multiple servers:** if the specific server a client is stuck to crashes, that client's entire session (stored only in that server's memory) is lost — the very server failure that a load balancer is supposed to seamlessly route around instead causes a real, visible disruption for every client stuck to it.

**The better alternative, used in most modern designs — externalize session state:** instead of relying on sticky sessions, store session data in a shared, external store (like Redis) that every backend server can read from, regardless of which one handles a given request. This removes the need for stickiness entirely: any server can serve any client's request correctly, restoring the load balancer's full freedom to route however it decides is best, and removing the single-server session loss risk.

## 4. Diagram

```
 STICKY SESSIONS (session data lives IN the server)
 Client -> [LB reads cookie] -> ALWAYS Server2   (if Server2 crashes, session is LOST)

 EXTERNALIZED SESSIONS (session data lives in shared store)
 Client -> [LB, any algorithm] -> any server (Server1, 2, or 3)
                                        |
                                        v
                              [Shared Session Store: Redis]
                     (any server can serve this client correctly)
```
*Caption: sticky sessions tie a client to one server's memory; externalizing session state removes that dependency entirely.*

## 5. Runnable example

### Artifact: a Java simulation contrasting sticky, in-memory sessions with externalized, shared sessions

```java
import java.util.*;

public class StickySessionSim {

    // Sticky approach: each server has its OWN private session map.
    static final Map<String, Map<String, String>> perServerSessions = new HashMap<>();

    // Externalized approach: ONE shared session store, reachable by every server.
    static final Map<String, String> sharedSessionStore = new HashMap<>();

    static void stickyLogin(String server, String sessionId, String username) {
        perServerSessions.computeIfAbsent(server, s -> new HashMap<>()).put(sessionId, username);
    }

    static String stickyReadSession(String server, String sessionId) {
        return perServerSessions.getOrDefault(server, Map.of()).getOrDefault(sessionId, "SESSION NOT FOUND");
    }

    static void externalizedLogin(String sessionId, String username) {
        sharedSessionStore.put(sessionId, username);
    }

    static String externalizedReadSession(String sessionId) {
        return sharedSessionStore.getOrDefault(sessionId, "SESSION NOT FOUND");
    }

    public static void main(String[] args) {
        String sessionId = "sess_abc123";

        // Sticky: client logs in on serverA, then a later request happens to land on serverB.
        stickyLogin("serverA", sessionId, "ada");
        System.out.println("Sticky, read on serverA: " + stickyReadSession("serverA", sessionId));
        System.out.println("Sticky, read on serverB (stickiness broke, or serverA crashed): " + stickyReadSession("serverB", sessionId));

        // Externalized: same scenario, but session lives in a shared store any server can reach.
        externalizedLogin(sessionId, "ada");
        System.out.println("Externalized, read via serverA's code path: " + externalizedReadSession(sessionId));
        System.out.println("Externalized, read via serverB's code path: " + externalizedReadSession(sessionId));
    }
}
```

**How to run:** save as `StickySessionSim.java`, run `java StickySessionSim.java` (JDK 17+).

## 6. Walkthrough

1. `perServerSessions` models each server keeping its own completely separate session data, which is what "session data stored in server memory" really means.
2. `stickyLogin`/`stickyReadSession` write to, and read from, one specific server's private map — mirroring the sticky-session approach.
3. `sharedSessionStore` models one external store (like Redis) that every server's code reads from and writes to, regardless of which server is running it.
4. `main` simulates a login on `serverA`, then a read attempt on `serverB` — representing what happens if stickiness ever breaks, or the original server crashes.
5. Output:
```
Sticky, read on serverA: ada
Sticky, read on serverB (stickiness broke, or serverA crashed): SESSION NOT FOUND
Externalized, read via serverA's code path: ada
Externalized, read via serverB's code path: ada
```
6. The sticky approach fails the moment the client's request lands on a different server than the one it originally logged into — "SESSION NOT FOUND" is exactly the bug users experience when sticky sessions break, or their assigned server goes down. The externalized approach succeeds regardless of which server's code path reads it, because the data was never tied to one specific server in the first place.

## 7. Gotchas & takeaways

> **Gotcha:** relying on sticky sessions as your primary session strategy in a design meant to be highly available. Since the client's session lives only in one server's memory, that server becoming unavailable directly causes session loss for every client stuck to it — the opposite of the resilience a multi-server, load-balanced design is supposed to provide.

- Sticky sessions route a client to the same server repeatedly, usually via a cookie, to match in-memory session state on that server.
- This undermines even load distribution and creates a real availability risk if that specific server fails.
- Prefer externalizing session state to a shared store (like Redis); it removes the need for stickiness and restores full load-balancing flexibility and resilience.
