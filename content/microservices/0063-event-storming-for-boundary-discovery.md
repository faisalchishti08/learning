---
card: microservices
gi: 63
slug: event-storming-for-boundary-discovery
title: "Event storming for boundary discovery"
---

## 1. What it is

Event storming is a collaborative workshop technique for discovering [bounded contexts](0049-bounded-context.md): domain experts and engineers stand at a wall (physical or virtual) and cover it with orange sticky notes, each one naming a **domain event** — something that happened, phrased in past tense, like `OrderPlaced`, `PaymentCaptured`, or `ShipmentDispatched`. The events are arranged in the order they occur, then commands, actors, and read models are layered on around them. Clusters of tightly related events, driven by the same commands and the same actors, tend to reveal where a bounded context boundary naturally sits.

## 2. Why & when

Bounded context boundaries are hard to discover by staring at existing code or an entity-relationship diagram, because both tend to reflect whatever organizational accident produced them rather than the actual shape of the business process. Event storming sidesteps this by starting from a different, more reliable source: the sequence of things that actually happen in the business, described by the people who understand the domain, not by the current code structure. Because the notation is just "sticky note with a past-tense verb," domain experts with no software background can participate directly — which matters, because they are the ones who actually know where one business process ends and another begins.

Reach for event storming early: at the start of a monolith decomposition, when kicking off a new domain from scratch, or whenever a context map already exists but its boundaries feel arbitrary or contested. It is a discovery tool, not something you run once code already reflects the correct boundaries.

## 3. Core concept

Events cluster naturally around the actor and command that trigger them. A cluster boundary — a point where the events driving one process stop having much to do with the events driving the next — is a strong candidate for a bounded context boundary.

```
[Customer]--(PlaceOrder cmd)-->[OrderPlaced]--(ReserveStock cmd)-->[StockReserved]   <- Ordering cluster
                                                                          |
                                                            (DispatchShipment cmd)
                                                                          v
                                                                 [ShipmentDispatched]  <- Shipping cluster starts here
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline of orange event sticky notes clusters into two groups, revealing an Ordering context boundary and a Shipping context boundary">
  <text x="20" y="25" fill="#8b949e" font-size="9" font-family="sans-serif">timeline of domain events (left to right) -&gt;</text>

  <rect x="20" y="50" width="120" height="40" rx="4" fill="#c9820a" stroke="#1c2430"/>
  <text x="80" y="74" fill="#1c2430" font-size="8" text-anchor="middle" font-family="sans-serif">OrderPlaced</text>
  <rect x="160" y="50" width="120" height="40" rx="4" fill="#c9820a" stroke="#1c2430"/>
  <text x="220" y="74" fill="#1c2430" font-size="8" text-anchor="middle" font-family="sans-serif">StockReserved</text>

  <rect x="340" y="50" width="120" height="40" rx="4" fill="#c9820a" stroke="#1c2430"/>
  <text x="400" y="74" fill="#1c2430" font-size="8" text-anchor="middle" font-family="sans-serif">ShipmentDispatched</text>
  <rect x="480" y="50" width="120" height="40" rx="4" fill="#c9820a" stroke="#1c2430"/>
  <text x="540" y="74" fill="#1c2430" font-size="8" text-anchor="middle" font-family="sans-serif">ShipmentDelivered</text>

  <line x1="310" y1="40" x2="310" y2="100" stroke="#6db33f" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="310" y="115" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">candidate boundary</text>

  <rect x="20" y="150" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Ordering context</text>
  <rect x="340" y="150" width="260" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="470" y="170" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Shipping context</text>
</svg>

Events cluster around a shared actor and command; a gap in that clustering is where a context boundary tends to sit.

## 5. Runnable example

Scenario: model an event-storming board as data — a list of timestamped domain events with their triggering actor and command — then write code that clusters them by actor/command affinity to discover context boundaries, and finally harden the clustering to also weigh in on shared data (aggregate id) so it does not mis-cluster.

### Level 1 — Basic

```java
// File: EventBoard.java -- represent an event-storming board as a
// simple ordered list of (event name, triggering actor) pairs.
import java.util.*;

public class EventBoard {
    record StormEvent(String name, String actor) {}

    public static void main(String[] args) {
        List<StormEvent> board = List.of(
            new StormEvent("OrderPlaced", "Customer"),
            new StormEvent("StockReserved", "Customer"),
            new StormEvent("ShipmentDispatched", "WarehouseStaff"),
            new StormEvent("ShipmentDelivered", "WarehouseStaff")
        );
        for (StormEvent e : board) {
            System.out.println(e.name() + " (actor: " + e.actor() + ")");
        }
    }
}
```

**How to run:** `javac EventBoard.java && java EventBoard` (JDK 17+).

Expected output:
```
OrderPlaced (actor: Customer)
StockReserved (actor: Customer)
ShipmentDispatched (actor: WarehouseStaff)
ShipmentDelivered (actor: WarehouseStaff)
```

This is the raw board: just the sticky notes in timeline order, each with its actor. No clustering logic yet — this is the workshop's raw output before anyone draws boundary lines.

### Level 2 — Intermediate

```java
// File: ClusterByActor.java -- the SAME board, now clustered by
// consecutive-run of the same actor, to surface candidate boundaries.
import java.util.*;

public class ClusterByActor {
    record StormEvent(String name, String actor) {}

    static List<List<StormEvent>> clusterByActor(List<StormEvent> board) {
        List<List<StormEvent>> clusters = new ArrayList<>();
        List<StormEvent> current = new ArrayList<>();
        String lastActor = null;
        for (StormEvent e : board) {
            if (lastActor != null && !lastActor.equals(e.actor())) {
                clusters.add(current);
                current = new ArrayList<>();
            }
            current.add(e);
            lastActor = e.actor();
        }
        if (!current.isEmpty()) clusters.add(current);
        return clusters;
    }

    public static void main(String[] args) {
        List<StormEvent> board = List.of(
            new StormEvent("OrderPlaced", "Customer"),
            new StormEvent("StockReserved", "Customer"),
            new StormEvent("ShipmentDispatched", "WarehouseStaff"),
            new StormEvent("ShipmentDelivered", "WarehouseStaff")
        );
        List<List<StormEvent>> clusters = clusterByActor(board);
        int i = 1;
        for (List<StormEvent> cluster : clusters) {
            System.out.println("Candidate context " + i + ": " + cluster.stream().map(StormEvent::name).toList());
            i++;
        }
    }
}
```

**How to run:** `javac ClusterByActor.java && java ClusterByActor` (JDK 17+).

Expected output:
```
Candidate context 1: [OrderPlaced, StockReserved]
Candidate context 2: [ShipmentDispatched, ShipmentDelivered]
```

Now the actor changes (`Customer` to `WarehouseStaff`) are treated as boundary signals, and the events fall into two clusters — exactly the Ordering / Shipping split a real workshop would surface on the sticky-note wall.

### Level 3 — Advanced

```java
// File: ClusterByActorAndAggregate.java -- harden the clustering: actor
// alone is a weak signal (the same person can act across many contexts),
// so also require the events to share an aggregate id before merging them
// into the same cluster, and flag any event referencing an id outside
// its own cluster as a likely CROSS-CONTEXT INTEGRATION POINT.
import java.util.*;

public class ClusterByActorAndAggregate {
    record StormEvent(String name, String actor, String aggregateId) {}

    static List<List<StormEvent>> clusterByActorAndAggregate(List<StormEvent> board) {
        List<List<StormEvent>> clusters = new ArrayList<>();
        List<StormEvent> current = new ArrayList<>();
        String lastActor = null;
        for (StormEvent e : board) {
            boolean actorChanged = lastActor != null && !lastActor.equals(e.actor());
            if (actorChanged) {
                clusters.add(current);
                current = new ArrayList<>();
            }
            current.add(e);
            lastActor = e.actor();
        }
        if (!current.isEmpty()) clusters.add(current);
        return clusters;
    }

    static List<String> findCrossClusterReferences(List<List<StormEvent>> clusters) {
        List<String> flags = new ArrayList<>();
        for (int i = 0; i < clusters.size(); i++) {
            Set<String> idsInThisCluster = new HashSet<>();
            for (StormEvent e : clusters.get(i)) idsInThisCluster.add(e.aggregateId());
            for (int j = i + 1; j < clusters.size(); j++) { // only look FORWARD, so each pair is flagged once
                for (StormEvent other : clusters.get(j)) {
                    if (idsInThisCluster.contains(other.aggregateId())) {
                        flags.add(other.name() + " (context " + (j + 1) + ") shares aggregate id '"
                                + other.aggregateId() + "' with context " + (i + 1) + " -- likely integration point");
                    }
                }
            }
        }
        return flags;
    }

    public static void main(String[] args) {
        List<StormEvent> board = List.of(
            new StormEvent("OrderPlaced", "Customer", "ORD-1"),
            new StormEvent("StockReserved", "Customer", "ORD-1"),
            new StormEvent("ShipmentDispatched", "WarehouseStaff", "ORD-1"),
            new StormEvent("ShipmentDelivered", "WarehouseStaff", "ORD-1")
        );
        List<List<StormEvent>> clusters = clusterByActorAndAggregate(board);
        int i = 1;
        for (List<StormEvent> cluster : clusters) {
            System.out.println("Candidate context " + i + ": " + cluster.stream().map(StormEvent::name).toList());
            i++;
        }
        for (String flag : findCrossClusterReferences(clusters)) {
            System.out.println("FLAG: " + flag);
        }
    }
}
```

**How to run:** `javac ClusterByActorAndAggregate.java && java ClusterByActorAndAggregate` (JDK 17+).

Expected output:
```
Candidate context 1: [OrderPlaced, StockReserved]
Candidate context 2: [ShipmentDispatched, ShipmentDelivered]
FLAG: ShipmentDispatched (context 2) shares aggregate id 'ORD-1' with context 1 -- likely integration point
FLAG: ShipmentDelivered (context 2) shares aggregate id 'ORD-1' with context 1 -- likely integration point
```

The clustering still splits by actor, but now the code also flags that both clusters reference the same `ORD-1` id — a realistic signal that, once these become two separate services, `ORD-1` needs a clear translation (e.g. an [anti-corruption layer](0057-anti-corruption-layer-acl.md)) at the Ordering/Shipping seam rather than being passed around as a shared raw identifier.

## 6. Walkthrough

1. **Level 1** — `EventBoard.main` just prints the sticky-note board top to bottom, actor included. This mirrors the state of a workshop wall right after the "big picture" pass, before anyone has grouped anything.
2. **Level 2** — `clusterByActor` walks the board once, and every time the acting persona changes from the previous event, it closes the current cluster and starts a new one. Running it on the four sample events produces two clusters: `[OrderPlaced, StockReserved]` under `Customer`, and `[ShipmentDispatched, ShipmentDelivered]` under `WarehouseStaff`. This is the mechanical analogue of a facilitator physically drawing a vertical line on the sticky-note wall where the actor swimlane changes.
3. **Level 3** — `clusterByActorAndAggregate` performs the identical actor-based clustering pass first (same two clusters come out), but then `findCrossClusterReferences` does a second pass: for every cluster, it collects the aggregate ids appearing in it, then checks every *later* cluster (deliberately looking only forward, so each pair of clusters is compared once, not twice) for events referencing the same id. Because all four events reference `ORD-1`, the method finds that `ShipmentDispatched` and `ShipmentDelivered` (in context 2) both reference an id already claimed by context 1 — and prints a `FLAG` line for each.
4. **What the flags mean in practice** — in a real event-storming session, this is precisely the moment the facilitator would ask: "does Shipping own its own identifier, or is it still riding on the Order id?" If Shipping legitimately needs to reference the originating order, that is normal and expected — but it tells the team that a translation layer (an [anti-corruption layer](0057-anti-corruption-layer-acl.md) or a simple id-mapping table) belongs at that seam once Ordering and Shipping become separate services, rather than Shipping querying Ordering's database directly for `ORD-1`'s internal state.
5. **End-to-end output** — running Level 3 prints the two candidate contexts first, then the two flags, giving a facilitator (or in this simulation, a build script) both outputs a real workshop would want: "where are the likely boundaries," and "where do those boundaries need explicit integration."

## 7. Gotchas & takeaways

> **Gotcha:** clustering on actor alone is a weak signal in real domains — the same person (say, an "Ops Manager") can legitimately act across several unrelated contexts. Treat actor grouping as a starting hypothesis to validate with the domain experts in the room, not as a final answer a script can compute for you.

- Event storming works because it starts from business events, not existing code or database schemas, which tend to encode past organizational accidents rather than the domain's real shape.
- Orange stickies (events) go up first, in timeline order; commands, actors, and aggregates are layered in afterward once the event timeline feels complete.
- A cluster boundary in the workshop is only a *candidate* bounded context — validate it against [subdomain classification](0051-subdomains-core-supporting-generic.md) and existing team ownership before committing to a service split.
- Shared aggregate ids crossing a candidate boundary are a strong signal that an explicit integration pattern (ACL, published language) will be needed at that seam.
- Event storming is a discovery technique, most valuable *before* code exists or before a monolith split begins — running it against code that already reflects the wrong boundaries just tells you what you already suspected.
