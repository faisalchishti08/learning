---
card: spring-cloud
gi: 32
slug: eureka-peer-awareness-ha
title: "Eureka peer awareness / HA"
---

## 1. What it is

A single Eureka Server is a single point of failure — if it goes down, no service can register or discover anything until it comes back. Peer awareness fixes this: run two or more Eureka Server instances configured to know about each other (each one's `defaultZone` points at the others), and they continuously replicate their registries to one another, so every server holds effectively the same data and clients can keep working against whichever server is still reachable.

```properties
# eureka-server-1
eureka.client.service-url.defaultZone=http://eureka-server-2:8762/eureka/

# eureka-server-2
eureka.client.service-url.defaultZone=http://eureka-server-1:8761/eureka/
```

Each Eureka Server is itself also a Eureka Client of its peers — that's the whole mechanism: registration and replication reuse the same client-server protocol used by ordinary services.

## 2. Why & when

A registry that everything depends on is exactly the kind of component that must not itself become a single point of failure — if it did, a single server crash would take down service discovery fleet-wide, even though every actual service instance is perfectly healthy. Peer awareness spreads the registry across multiple servers so that no single server's failure breaks discovery.

Reach for peer-aware, multi-node Eureka in any environment beyond local development:

- Production deployments always run at least two Eureka Server nodes, typically one per availability zone, so a zone outage doesn't take discovery down with it.
- Environments where discovery downtime has a real cost — if Eureka Server is fully down, existing cached client registries still work for a while (clients keep their last-known list), but no new registrations, deregistrations, or registry changes propagate until a server comes back.
- Any setup that already runs multiple Eureka Clients across zones, since peer-aware servers pair naturally with the region/zone-aware client behavior covered in a later card.

## 3. Core concept

```
   Eureka Server 1  <--- replicate registry changes --->  Eureka Server 2
        ^                                                        ^
        |  register/query                     register/query    |
        |                                                        |
   client A (points at server 1)          client B (points at server 2)

  A registers with server 1 -> server 1 replicates to server 2
  -> client B, querying server 2, sees A too
```

Each server pushes its own registration changes to every peer it knows about, so all servers converge on the same view even though clients only talk to one server at a time.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two Eureka Server nodes replicate registry changes to each other while different clients register against different servers and still see a consistent combined view">
  <rect x="80" y="30" width="180" height="44" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="57" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka Server 1</text>

  <rect x="380" y="30" width="180" height="44" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="57" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Eureka Server 2</text>

  <line x1="260" y1="45" x2="378" y2="45" stroke="#79c0ff" stroke-width="1.4" marker-end="url(#a32)"/>
  <line x1="378" y1="60" x2="260" y2="60" stroke="#79c0ff" stroke-width="1.4" marker-end="url(#a32)"/>
  <text x="320" y="35" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">replicate</text>

  <rect x="30" y="140" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="161" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client A</text>
  <rect x="470" y="140" width="140" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="540" y="161" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client B</text>

  <line x1="100" y1="140" x2="150" y2="74" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a32)"/>
  <line x1="540" y1="140" x2="490" y2="74" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a32)"/>

  <defs><marker id="a32" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Clients register or query one server each, but replication keeps every server's view converged.

## 5. Runnable example

The scenario: two independent registries that need to converge. Start with isolated single-node registries, then add manual replication between them, then add automatic peer discovery so a change on either node reaches all others without hand-coding every pair.

### Level 1 — Basic

Two isolated registries — the single-point-of-failure problem.

```java
import java.util.*;

public class PeerAwarenessLevel1 {
    static class Server {
        String name;
        Map<String, List<String>> registry = new HashMap<>();
        Server(String name) { this.name = name; }
        void register(String service, String address) {
            registry.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
        }
    }

    public static void main(String[] args) {
        Server server1 = new Server("server-1");
        Server server2 = new Server("server-2");

        server1.register("orders-service", "10.0.1.5:8080"); // registered ONLY on server-1

        System.out.println("server-1 sees: " + server1.registry.get("orders-service"));
        System.out.println("server-2 sees: " + server2.registry.get("orders-service")); // null -- server-2 is blind to it
    }
}
```

How to run: `java PeerAwarenessLevel1.java`

`server-2` has no idea `orders-service` exists, because the two servers never talk to each other. If a client is unlucky enough to query `server-2`, it gets nothing — and if `server-1` crashes, `orders-service` becomes entirely undiscoverable.

### Level 2 — Intermediate

Add manual replication: when a server accepts a registration, it also pushes that change to its known peers.

```java
import java.util.*;

public class PeerAwarenessLevel2 {
    static class Server {
        String name;
        Map<String, List<String>> registry = new HashMap<>();
        List<Server> peers = new ArrayList<>();
        Server(String name) { this.name = name; }

        void register(String service, String address) {
            registerLocal(service, address);
            for (Server peer : peers) {
                peer.replicateFromPeer(service, address); // push the change outward
            }
        }

        void registerLocal(String service, String address) {
            registry.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
        }

        void replicateFromPeer(String service, String address) {
            registerLocal(service, address); // no re-broadcast -- avoids infinite replication loops
        }
    }

    public static void main(String[] args) {
        Server server1 = new Server("server-1");
        Server server2 = new Server("server-2");
        server1.peers.add(server2);
        server2.peers.add(server1);

        server1.register("orders-service", "10.0.1.5:8080");

        System.out.println("server-1 sees: " + server1.registry.get("orders-service"));
        System.out.println("server-2 sees: " + server2.registry.get("orders-service")); // now populated via replication
    }
}
```

How to run: `java PeerAwarenessLevel2.java`

`register` now does two things: apply the change locally, then push it to every known peer via `replicateFromPeer`, which applies it locally on the peer's side but deliberately does *not* re-broadcast — otherwise a two-node setup would ping-pong the same change back and forth forever. Both servers now agree on the registry after a single registration on either one.

### Level 3 — Advanced

Scale to three nodes and simulate one node going down mid-operation — clients pointed at the surviving nodes should keep working, demonstrating the actual HA payoff.

```java
import java.util.*;

public class PeerAwarenessLevel3 {
    static class Server {
        String name;
        boolean up = true;
        Map<String, List<String>> registry = new HashMap<>();
        List<Server> peers = new ArrayList<>();
        Server(String name) { this.name = name; }

        void register(String service, String address) {
            if (!up) throw new IllegalStateException(name + " is down");
            registerLocal(service, address);
            for (Server peer : peers) {
                if (peer.up) peer.replicateFromPeer(service, address);
                // if a peer is down, it simply misses this replication and
                // catches up later, once it's back, via a full registry sync
            }
        }

        void registerLocal(String service, String address) {
            registry.computeIfAbsent(service, k -> new ArrayList<>()).add(address);
        }

        void replicateFromPeer(String service, String address) {
            registerLocal(service, address);
        }

        List<String> query(String service) {
            if (!up) throw new IllegalStateException(name + " is down");
            return registry.getOrDefault(service, List.of());
        }
    }

    public static void main(String[] args) {
        Server s1 = new Server("server-1"), s2 = new Server("server-2"), s3 = new Server("server-3");
        s1.peers = List.of(s2, s3);
        s2.peers = List.of(s1, s3);
        s3.peers = List.of(s1, s2);

        s1.register("orders-service", "10.0.1.5:8080");
        System.out.println("all three agree: " + s1.query("orders-service") + " / "
                + s2.query("orders-service") + " / " + s3.query("orders-service"));

        s1.up = false; // server-1 crashes
        System.out.println("server-1 down; client repoints to server-2");

        s2.register("orders-service", "10.0.1.6:8080"); // new instance registers against a surviving node
        System.out.println("server-2 sees: " + s2.query("orders-service"));
        System.out.println("server-3 sees: " + s3.query("orders-service")); // still converged, without server-1
    }
}
```

How to run: `java PeerAwarenessLevel3.java`

With three nodes, losing `server-1` doesn't break discovery: `server-2` and `server-3` are still peers of each other, so a new registration against `server-2` still replicates to `server-3`, and any client that repoints itself at a surviving node (which real Eureka Clients do automatically, given a list of server URLs) keeps working. `server-1`, once it recovers, performs a full registry sync from a peer rather than replaying missed individual updates.

## 6. Walkthrough

Trace Level 3's sequence end to end.

1. Three `Server` objects are created, each configured with the other two as peers — this models three `eureka.client.service-url.defaultZone` configs, each listing the *other* nodes' URLs, never its own.
2. `s1.register("orders-service", "10.0.1.5:8080")` runs — this models a real instance's `POST /eureka/apps/ORDERS-SERVICE` landing on `server-1`. `registerLocal` applies it there, then the loop pushes `replicateFromPeer` calls to `s2` and `s3`, both currently `up`, so both apply it locally too.
3. The first `println` confirms all three servers independently answer the same query with the same result — this is the "all replicas converge" property peer awareness provides.
4. `s1.up = false` models `server-1` crashing (process killed, host lost, etc.). Its `register` and `query` methods now throw, standing in for the node being unreachable.
5. `s2.register(...)` runs for a *new* instance address — this models a real client whose configured server list includes multiple URLs; when `server-1` doesn't respond, the underlying HTTP client automatically retries against the next URL in the list, landing this registration on `server-2` instead, with no manual intervention required.
6. Inside that `register` call, the peer loop iterates `s2.peers = [s1, s3]`; the `if (peer.up)` guard skips replicating to `s1` (down, would throw) and successfully replicates to `s3`.
7. The final two `println` calls show `server-2` and `server-3` both hold the new registration — the registry stayed consistent and available across the two surviving nodes, even though a third of the cluster is down. When `server-1` eventually restarts, it performs a full peer-registry sync (not modeled here) to catch back up rather than trying to replay every missed individual change.

```
register on s1 -> replicate -> s1, s2, s3 all agree
        |
   s1 crashes
        |
register on s2 -> replicate to up peers only (s3) -> s2, s3 still agree
   s1 catches up later via a full sync on restart
```

## 7. Gotchas & takeaways

> **Gotcha:** peer replication is asynchronous and best-effort — during and immediately after a partition or restart, different Eureka Server nodes can briefly disagree about the exact registry contents. This is the same AP tradeoff as self-preservation: Eureka prioritizes staying available over guaranteeing every node is byte-for-byte identical at every instant.

- Peer-aware Eureka needs at least two nodes, each configured with the *other* nodes' URLs (never its own) in `defaultZone`, for replication to actually happen.
- Clients should be configured with multiple server URLs (a comma-separated `defaultZone` list) so they can fail over to a surviving node automatically if their primary server goes down.
- A recovering node performs a full registry sync from a peer rather than replaying an exact log of missed changes — Eureka's replication model favors eventual convergence over strict ordering.
- Running Eureka Server across availability zones (one node per zone) is the standard production pattern — it survives both individual node failures and whole-zone outages.
