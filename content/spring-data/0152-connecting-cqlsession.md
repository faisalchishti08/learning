---
card: spring-data
gi: 152
slug: connecting-cqlsession
title: "Connecting (CqlSession)"
---

## 1. What it is

`CqlSession` is the DataStax Java driver's connection object for Cassandra — but unlike a JDBC `Connection` or a MongoDB `MongoClient` pointing at one server, a `CqlSession` connects to an entire **cluster** of Cassandra nodes at once, discovers the cluster's topology automatically, and routes each query to whichever node(s) actually own the relevant data's partition.

```java
@Bean
CqlSessionFactoryBean session() {
    CqlSessionFactoryBean session = new CqlSessionFactoryBean();
    session.setContactPoints("cassandra-node-1,cassandra-node-2");
    session.setPort(9042);
    session.setKeyspaceName("orders_keyspace");
    session.setLocalDatacenter("datacenter1");
    return session;
}
```

## 2. Why & when

Every earlier card in this section assumed a working connection to Cassandra already existed. `CqlSession` is what actually establishes that connection — and because Cassandra is a distributed cluster with no single "the server," connecting to it is meaningfully different from connecting to a standalone database: you provide a handful of **contact points** (some initial nodes to reach), and the driver discovers the rest of the cluster's topology from there, maintaining awareness of which nodes are up, which datacenter is "local," and how to route each query efficiently.

Reach for explicit `CqlSession` configuration when:

- Setting up Cassandra connectivity for the first time — contact points, port, keyspace, and local datacenter are the minimum required configuration.
- Running a multi-datacenter Cassandra deployment, where `setLocalDatacenter(...)` determines which datacenter's nodes the driver prefers for read/write requests, keeping latency-sensitive traffic local rather than crossing datacenters unnecessarily.
- Tuning connection-level concerns — request timeouts, connection pool sizing per node, SSL — that don't have a simpler property-based path.

## 3. Core concept

```
 session.setContactPoints("node-1,node-2")   -- just a STARTING point, not the whole cluster
        |
        v
 driver connects to node-1 and/or node-2, asks: "what does the cluster actually look like?"
        |
        v
 driver learns: node-1, node-2, node-3, node-4, ... (however many nodes exist), which datacenter each is in
        |
        v
 EVERY subsequent query is routed by the driver to the node(s) that OWN the relevant partition --
 not necessarily the contact points at all
```

Contact points are only a bootstrap mechanism — once connected, the driver has full cluster awareness and routes intelligently, independent of which specific nodes were originally listed.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The driver connects via contact points, discovers the full cluster topology, and then routes each query directly to the node owning the relevant data">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">contact points (2 nodes)</text>

  <rect x="250" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">driver discovers topology</text>

  <line x1="200" y1="42" x2="245" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="60" y="100" width="110" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="115" y="122" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">node-1</text>
  <rect x="190" y="100" width="110" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="245" y="122" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">node-2</text>
  <rect x="320" y="100" width="110" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="375" y="122" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">node-3</text>
  <rect x="450" y="100" width="110" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="505" y="122" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">node-4</text>

  <line x1="340" y1="65" x2="340" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a1)"/>

  <text x="320" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the FULL cluster is now known, even though only 2 nodes were named as contact points</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Two contact points are enough for the driver to discover and connect to every node in the cluster.

## 5. Runnable example

The scenario: establishing and using a cluster-aware connection, evolving from a basic contact-point bootstrap discovering the full cluster, to routing a query to the correct partition-owning node, to selecting a local datacenter to keep query routing latency-conscious in a multi-datacenter deployment.

### Level 1 — Basic

Model the contact-point-to-full-topology discovery process.

```java
import java.util.*;

public class CqlSessionLevel1 {
    public static void main(String[] args) {
        CqlSession session = CqlSession.connect(List.of("node-1", "node-2"));
        System.out.println("Connected using " + 2 + " contact points.");
        System.out.println("Full cluster discovered: " + session.knownNodes());
    }
}

// Stands in for com.datastax.oss.driver.api.core.CqlSession.
class CqlSession {
    private final List<String> allClusterNodes;
    private CqlSession(List<String> allClusterNodes) { this.allClusterNodes = allClusterNodes; }

    static CqlSession connect(List<String> contactPoints) {
        // The driver contacts these nodes and asks them for the FULL cluster's topology --
        // this simulated cluster happens to have 2 MORE nodes than were listed as contact points.
        List<String> fullTopology = new ArrayList<>(contactPoints);
        fullTopology.add("node-3");
        fullTopology.add("node-4");
        return new CqlSession(fullTopology);
    }

    List<String> knownNodes() { return allClusterNodes; }
}
```

How to run: `java CqlSessionLevel1.java`

`connect` mirrors `CqlSession.builder().addContactPoint(...).build()`: only two nodes are provided as contact points, but the resulting session knows about all four nodes in the cluster — the driver discovered `node-3` and `node-4` on its own by asking the contact points for the cluster's actual topology, exactly like a real Cassandra driver does on connection.

### Level 2 — Intermediate

Route a query to the specific node that owns a given partition — the driver's core job on every subsequent request after the initial connection.

```java
import java.util.*;

public class CqlSessionLevel2 {
    public static void main(String[] args) {
        CqlSession session = CqlSession.connect(List.of("node-1", "node-2"));

        String partitionKey = "order-42";
        String owningNode = session.nodeForPartition(partitionKey);
        System.out.println("Partition '" + partitionKey + "' is owned by: " + owningNode);
        System.out.println("Query for this order is routed DIRECTLY to " + owningNode + ", regardless of which contact point was used to connect.");
    }
}

class CqlSession {
    private final List<String> allClusterNodes;
    private CqlSession(List<String> allClusterNodes) { this.allClusterNodes = allClusterNodes; }

    static CqlSession connect(List<String> contactPoints) {
        List<String> fullTopology = new ArrayList<>(contactPoints);
        fullTopology.add("node-3");
        fullTopology.add("node-4");
        return new CqlSession(fullTopology);
    }

    List<String> knownNodes() { return allClusterNodes; }

    // Mirrors the driver's token-ring-based routing: hash the partition key, find which node owns that token range.
    String nodeForPartition(String partitionKey) {
        int index = Math.floorMod(partitionKey.hashCode(), allClusterNodes.size());
        return allClusterNodes.get(index);
    }
}
```

How to run: `java CqlSessionLevel2.java`

`nodeForPartition` mirrors the driver's real token-ring routing: Cassandra hashes a partition key into a numeric "token," and each node in the cluster owns a specific range of that token space — the driver computes which node owns the token for a given partition key and sends the query straight there, rather than asking every node or relying on whichever node happened to be a contact point.

### Level 3 — Advanced

Select a local datacenter, matching multi-datacenter deployments where `setLocalDatacenter(...)` keeps latency-sensitive query routing confined to nearby nodes rather than crossing to a distant datacenter unnecessarily.

```java
import java.util.*;

public class CqlSessionLevel3 {
    public static void main(String[] args) {
        Map<String, String> nodeToDatacenter = Map.of(
            "node-1", "us-east", "node-2", "us-east",
            "node-3", "eu-west", "node-4", "eu-west"
        );

        CqlSession session = CqlSession.connect(List.of("node-1", "node-3"), nodeToDatacenter, "us-east");

        String partitionKey = "order-42";
        String owningNode = session.nodeForPartitionPreferringLocalDc(partitionKey);
        System.out.println("Local datacenter: us-east");
        System.out.println("Query for '" + partitionKey + "' preferentially routed to: " + owningNode
            + " (datacenter=" + nodeToDatacenter.get(owningNode) + ")");
    }
}

class CqlSession {
    private final List<String> allClusterNodes;
    private final Map<String, String> nodeToDatacenter;
    private final String localDatacenter;

    private CqlSession(List<String> allClusterNodes, Map<String, String> nodeToDatacenter, String localDatacenter) {
        this.allClusterNodes = allClusterNodes; this.nodeToDatacenter = nodeToDatacenter; this.localDatacenter = localDatacenter;
    }

    static CqlSession connect(List<String> contactPoints, Map<String, String> nodeToDatacenter, String localDatacenter) {
        List<String> fullTopology = new ArrayList<>(nodeToDatacenter.keySet()); // discovered ALL nodes, across all DCs
        return new CqlSession(fullTopology, nodeToDatacenter, localDatacenter);
    }

    // Mirrors setLocalDatacenter(...): prefer nodes in the LOCAL datacenter for routing, even if a replica exists elsewhere.
    String nodeForPartitionPreferringLocalDc(String partitionKey) {
        List<String> localDcNodes = allClusterNodes.stream()
            .filter(n -> localDatacenter.equals(nodeToDatacenter.get(n)))
            .sorted()
            .collect(java.util.stream.Collectors.toList());
        int index = Math.floorMod(partitionKey.hashCode(), localDcNodes.size());
        return localDcNodes.get(index); // ONLY considers local-datacenter nodes for this routing decision
    }
}
```

How to run: `java CqlSessionLevel3.java`

`nodeForPartitionPreferringLocalDc` first narrows the candidate nodes down to only those in `"us-east"` (the configured local datacenter) before routing, mirroring `setLocalDatacenter("us-east")`'s effect: even though replicas of the same data may exist in `"eu-west"` too, the driver prefers the local datacenter's replicas to avoid the latency (and often cost) of cross-datacenter network hops for routine reads and writes.

## 6. Walkthrough

Execution starts in `main` for Level 3. `nodeToDatacenter` maps four nodes across two datacenters: `node-1`/`node-2` in `"us-east"`, `node-3`/`node-4` in `"eu-west"`. `CqlSession.connect(...)` is called with contact points `node-1` and `node-3` (one from each datacenter, purely for the example) plus the datacenter map and `"us-east"` as the configured local datacenter.

Inside `connect`, `fullTopology` is built from *every* key in `nodeToDatacenter` — all four nodes, regardless of which two were contact points — modeling the driver's full cluster discovery from before.

`session.nodeForPartitionPreferringLocalDc("order-42")` first filters `allClusterNodes` down to only those where `nodeToDatacenter.get(n)` equals `"us-east"` — this keeps only `node-1` and `node-2`, discarding the `eu-west` nodes entirely from consideration for this routing decision. It then hashes `"order-42"` modulo the size of that *filtered* list (`2`, not `4`) to pick one of the two local nodes.

```
Local datacenter: us-east
Query for 'order-42' preferentially routed to: node-... (datacenter=us-east)
```

In a real multi-datacenter Cassandra deployment, `setLocalDatacenter("us-east")` configures the driver's default load-balancing policy to prefer `us-east` replicas for query routing — this matters enormously for latency (avoiding cross-ocean network round trips for routine operations) and is a required setting for any multi-datacenter cluster; omitting it, or configuring it incorrectly, is a common source of unexpectedly high query latency in production Cassandra deployments.

## 7. Gotchas & takeaways

> Gotcha: contact points are only a *bootstrap* mechanism — if every contact point happens to be down when the application starts, the driver cannot connect at all, even if the rest of the cluster is healthy. Production configurations typically list several contact points across different nodes (and ideally different racks/datacenters) specifically to avoid this single point of failure at startup.

> Gotcha: forgetting to set `localDatacenter` (or setting it incorrectly) in a multi-datacenter cluster can cause the driver to route queries to a distant datacenter by default, silently adding significant latency to every request without any error or obvious symptom other than "the application feels slow" — this is a frequent, hard-to-diagnose Cassandra misconfiguration.

- `CqlSession` connects to an entire Cassandra cluster, not a single server — contact points bootstrap the connection, after which the driver discovers and maintains awareness of the full cluster topology.
- Every subsequent query is routed by the driver directly to the node(s) owning the relevant partition, based on the partition key's hashed token — not necessarily to any of the original contact points.
- `localDatacenter` must be configured explicitly for any multi-datacenter deployment, keeping routine query routing confined to nearby, low-latency replicas.
- List multiple contact points across different nodes in production to avoid a single point of failure at application startup.
