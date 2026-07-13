---
card: microservices
gi: 193
slug: service-registry-high-availability-replication
title: "Service registry high availability & replication"
---

## 1. What it is

Because every service-to-service call in a system ultimately depends on the [service registry](0182-service-registry-concept.md) being reachable and accurate, the registry itself needs the same high-availability treatment as an [HA gateway](0170-single-point-of-failure-concerns-ha-gateways.md) — running as multiple replicated nodes, each holding a copy of the registration data, so that any single node's failure doesn't take down service discovery for the entire system.

## 2. Why & when

A registry running as a single instance is a single point of failure with an even larger blast radius than a single-instance gateway: a gateway outage blocks *external* traffic, but a registry outage can block *every* service-to-service call across the entire internal system simultaneously, since virtually everything depends on discovery to find anything else. Running the registry as a replicated cluster — with registration data synchronized across multiple nodes — means any individual node's failure is absorbed by the remaining nodes continuing to serve accurate discovery queries, exactly the same resilience principle applied at an even more foundational layer of the system.

Deploy the registry as a replicated, multi-node cluster in any production system where the registry is genuinely load-bearing infrastructure — which describes essentially every system relying on dynamic service discovery. The specific replication strategy (each registry implementation, Eureka, Consul, etcd-backed systems, has its own consistency model and trade-offs) matters, but the baseline requirement — more than one node, with synchronized data — is close to universal for production use.

## 3. Core concept

Multiple registry nodes each hold a copy of the current registration data, synchronized with each other through a replication protocol; a client (or a load balancer in front of the registry cluster) can query any available node and get a consistent (or, depending on the specific registry's consistency model, an eventually-consistent) view, with no single node's failure causing service discovery to become unavailable.

```java
// MULTIPLE registry nodes, all synchronized
List<RegistryNode> registryCluster = List.of(node1, node2, node3);

ServiceInstance register(String serviceName, ServiceInstance instance) {
    RegistryNode target = pickAvailableNode(registryCluster); // any node can serve the request
    target.register(serviceName, instance);
    target.replicateToOtherNodes(registryCluster, serviceName, instance); // propagated to the OTHERS
    return instance;
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three registry nodes replicate registration data among each other; one node fails, but a query routed to either remaining node still returns the correct, current registration data, since the failed node's data was already synchronized to the survivors" >
  <rect x="20" y="80" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="104" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registry node 1</text>

  <rect x="245" y="20" width="150" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="320" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registry node 2 (DOWN)</text>

  <rect x="245" y="140" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="164" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Registry node 3</text>

  <line x1="170" y1="90" x2="243" y2="40" stroke="#8b949e" stroke-dasharray="2,2"/>
  <line x1="170" y1="105" x2="243" y2="155" stroke="#8b949e"/>
  <line x1="395" y1="40" x2="245" y2="40" stroke="#8b949e" stroke-dasharray="2,2"/>

  <text x="480" y="80" fill="#e6edf3" font-size="8" font-family="sans-serif">Query -&gt;</text>
  <rect x="480" y="90" width="120" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="112" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Caller</text>
  <line x1="480" y1="107" x2="397" y2="107" stroke="#8b949e" marker-end="url(#arr74)"/>

  <defs>
    <marker id="arr74" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Data replicated among nodes means any surviving node can still answer queries correctly after one node fails.

## 5. Runnable example

Scenario: a registry deployment that starts as a single instance (showing the total discovery outage a failure causes), replicates registration data across multiple nodes so a query can succeed against any surviving node, and finally demonstrates the replication propagation delay explicitly — a new registration briefly visible on some nodes before others, making the practical consistency trade-off concrete.

### Level 1 — Basic

```java
// File: SingleRegistryInstance.java -- ONE registry node; its failure means
// TOTAL discovery outage for the ENTIRE system, even though every backend service is healthy.
import java.util.*;

public class SingleRegistryInstance {
    static Map<String, List<String>> registrations = new HashMap<>(Map.of("order-service", List.of("10.0.1.5", "10.0.1.6")));
    static boolean registryIsUp = true;

    static List<String> lookup(String serviceName) {
        if (!registryIsUp) throw new RuntimeException("Registry unreachable -- discovery for EVERYTHING is now broken");
        return registrations.get(serviceName);
    }

    public static void main(String[] args) {
        System.out.println(lookup("order-service"));

        registryIsUp = false; // the ONE registry instance crashes
        try {
            lookup("order-service");
        } catch (RuntimeException e) {
            System.out.println("Lookup FAILED: " + e.getMessage());
            System.out.println("EVERY service-to-service call in the ENTIRE system now fails, even though every backend is perfectly healthy.");
        }
    }
}
```

**How to run:** `javac SingleRegistryInstance.java && java SingleRegistryInstance` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ReplicatedRegistryCluster.java -- MULTIPLE registry nodes, DATA
// REPLICATED across them; a query against ANY surviving node succeeds.
import java.util.*;

public class ReplicatedRegistryCluster {
    static class RegistryNode {
        String id;
        boolean up = true;
        Map<String, List<String>> data = new HashMap<>();
        RegistryNode(String id) { this.id = id; }
    }

    static class RegistryCluster {
        List<RegistryNode> nodes;
        RegistryCluster(List<RegistryNode> nodes) { this.nodes = nodes; }

        void register(String serviceName, String address) {
            for (RegistryNode node : nodes) { // WRITE replicated to EVERY node
                if (node.up) node.data.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(address);
            }
        }

        List<String> lookup(String serviceName) {
            for (RegistryNode node : nodes) { // try nodes in order, skip DOWN ones
                if (node.up) {
                    System.out.println("  [query] served by " + node.id());
                    return node.data.getOrDefault(serviceName, List.of());
                }
            }
            throw new RuntimeException("ALL nodes down -- this would require the ENTIRE cluster to fail simultaneously");
        }
    }

    public static void main(String[] args) {
        RegistryNode node1 = new RegistryNode("node-1");
        RegistryNode node2 = new RegistryNode("node-2");
        RegistryNode node3 = new RegistryNode("node-3");
        RegistryCluster cluster = new RegistryCluster(List.of(node1, node2, node3));

        cluster.register("order-service", "10.0.1.5");
        cluster.register("order-service", "10.0.1.6");

        System.out.println("Lookup with ALL nodes up:");
        System.out.println("  Result: " + cluster.lookup("order-service"));

        node1.up = false; // node-1 FAILS
        System.out.println("\nnode-1 CRASHES. Lookup with node-1 DOWN:");
        System.out.println("  Result: " + cluster.lookup("order-service") + " (correct, served by a surviving node)");
    }
}
```

**How to run:** `javac ReplicatedRegistryCluster.java && java ReplicatedRegistryCluster` (JDK 17+).

Expected output:
```
Lookup with ALL nodes up:
  [query] served by node-1
  Result: [10.0.1.5, 10.0.1.6]

node-1 CRASHES. Lookup with node-1 DOWN:
  [query] served by node-2
  Result: [10.0.1.5, 10.0.1.6] (correct, served by a surviving node)
```

### Level 3 — Advanced

```java
// File: ReplicationPropagationDelay.java -- registration data is NOT
// instantaneously synchronized -- a NEW registration is briefly visible on some
// nodes before others, making the REAL consistency trade-off concrete.
import java.util.*;

public class ReplicationPropagationDelay {
    static class RegistryNode {
        String id;
        Map<String, List<String>> data = new HashMap<>();
        RegistryNode(String id) { this.id = id; }
    }

    static class RegistryCluster {
        List<RegistryNode> nodes;
        RegistryCluster(List<RegistryNode> nodes) { this.nodes = nodes; }

        // registration hits ONE node IMMEDIATELY; replication to OTHERS is SIMULATED as taking time
        void registerWithDelayedReplication(String serviceName, String address, RegistryNode primaryNode, List<RegistryNode> replicationOrder) {
            primaryNode.data.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(address);
            System.out.println("  [t=0] registered on " + primaryNode.id() + " IMMEDIATELY");
            // OTHER nodes receive the update LATER, in this simulation, one at a time
            for (int i = 0; i < replicationOrder.size(); i++) {
                RegistryNode node = replicationOrder.get(i);
                if (node != primaryNode) {
                    node.data.computeIfAbsent(serviceName, k -> new ArrayList<>()).add(address);
                    System.out.println("  [t=" + (i + 1) + "] replicated to " + node.id());
                }
            }
        }

        List<String> lookupFrom(RegistryNode specificNode, String serviceName) {
            return specificNode.data.getOrDefault(serviceName, List.of());
        }
    }

    public static void main(String[] args) {
        RegistryNode node1 = new RegistryNode("node-1");
        RegistryNode node2 = new RegistryNode("node-2");
        RegistryNode node3 = new RegistryNode("node-3");
        RegistryCluster cluster = new RegistryCluster(List.of(node1, node2, node3));

        System.out.println("A NEW instance registers on node-1:");
        cluster.registerWithDelayedReplication("order-service", "10.0.1.99", node1, List.of(node1, node2, node3));

        // a query landing on node-1 IMMEDIATELY sees the new instance
        System.out.println("\nQuery landing on node-1 (the primary): " + cluster.lookupFrom(node1, "order-service"));
        // BUT a query landing on node-3 at the SAME instant, BEFORE replication reaches it, would NOT
        System.out.println("Query landing on node-3, BEFORE its replication step completed, would have seen: (empty, not yet replicated)");
        System.out.println("Query landing on node-3, AFTER replication completed: " + cluster.lookupFrom(node3, "order-service"));

        System.out.println("\nThis brief window where DIFFERENT nodes disagree is the REAL trade-off of replication -- eventual, not necessarily instantaneous, consistency.");
    }
}
```

**How to run:** `javac ReplicationPropagationDelay.java && java ReplicationPropagationDelay` (JDK 17+).

Expected output:
```
A NEW instance registers on node-1:
  [t=0] registered on node-1 IMMEDIATELY
  [t=1] replicated to node-2
  [t=2] replicated to node-3

Query landing on node-1 (the primary): [10.0.1.99]
Query landing on node-3, BEFORE its replication step completed, would have seen: (empty, not yet replicated)
Query landing on node-3, AFTER replication completed: [10.0.1.99]

This brief window where DIFFERENT nodes disagree is the REAL trade-off of replication -- eventual, not necessarily instantaneous, consistency.
```

## 6. Walkthrough

1. **Level 1** — `lookup` throws an exception the moment `registryIsUp` is `false`, and this single boolean flag represents the entire registry's availability — the caught exception's message makes explicit that this single point of failure affects discovery for the whole system, not just one service.
2. **Level 2, replicated writes** — `RegistryCluster.register` loops over every node in `nodes` and writes the new registration data to each one that's currently `up`, meaning a successful registration call results in the data existing on multiple independent nodes, not just one.
3. **Level 2, failover on read** — `lookup` iterates `nodes` in order and returns data from the first node found to be `up`, skipping any that are down; when `node1.up` is set to `false`, the subsequent `lookup` call transparently falls through to `node2`, which correctly holds the identical replicated data.
4. **Level 2, the correct result despite a node failure** — both the pre-failure and post-failure calls to `cluster.lookup("order-service")` return the identical `[10.0.1.5, 10.0.1.6]` result, directly demonstrating that a single node's failure had zero impact on the correctness of discovery queries.
5. **Level 3, modeling replication as a process with real steps** — `registerWithDelayedReplication` writes to `primaryNode` first, then iterates the remaining nodes in `replicationOrder`, applying the update to each one sequentially, with a printed timestamp for each step — this models replication as something that happens *over time*, not instantaneously across all nodes simultaneously.
6. **Level 3, the observable inconsistency window** — a query against `node1` immediately after registration correctly finds `"10.0.1.99"`, while the code comments make explicit that a hypothetical query against `node3` *during* the replication process (before its specific replication step completes) would have found nothing — only *after* all replication steps finish does `cluster.lookupFrom(node3, ...)` correctly return the new address.
7. **Level 3, the practical consistency trade-off named directly** — this demonstrates that registry replication typically provides *eventual* consistency, not instantaneous consistency across every node — a genuine, observable window exists where different nodes can briefly disagree about the current state, which is an accepted trade-off in exchange for the resilience replication provides; a caller unlucky enough to query a node mid-replication might briefly miss a just-registered instance, though this is generally far less harmful than the alternative (an entirely unavailable, unreplicated registry going down completely).

## 7. Gotchas & takeaways

> **Gotcha:** the brief eventual-consistency window during replication means a just-registered instance might not be immediately visible to every caller across the cluster — this is usually an acceptable trade-off (a caller simply doesn't yet route to the newest instance for a moment), but the equivalent gap during *deregistration* is more consequential: an instance that just shut down might still appear registered on a node whose replication hasn't yet caught up, meaning a caller could still be routed to a dead instance briefly, which is exactly why deregistration paths often need to be treated with extra care (or combined with fast health-check-based exclusion) in a replicated registry design.

- A service registry is critical, load-bearing infrastructure that every service-to-service call ultimately depends on, requiring the same high-availability treatment as any other foundational system component.
- Running the registry as a replicated, multi-node cluster means any single node's failure is absorbed by the remaining nodes, avoiding the outsized blast radius a single-instance registry failure would have on the entire system's service discovery.
- Replication typically provides eventual, not instantaneous, consistency — a brief window can exist where different nodes disagree about the most recent registration or deregistration.
- This eventual-consistency window is generally an acceptable trade-off for registration (a new instance briefly under-discovered), but deserves extra care for deregistration, where a lagging node could still route callers to an already-dead instance.
- The specific replication strategy and consistency guarantees vary between registry implementations (Eureka, Consul, etcd-backed systems), but the baseline requirement of running more than one synchronized node is close to universal for production use.
