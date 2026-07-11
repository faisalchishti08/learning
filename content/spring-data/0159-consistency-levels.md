---
card: spring-data
gi: 159
slug: consistency-levels
title: "Consistency levels"
---

## 1. What it is

A **consistency level** controls how many replica nodes must acknowledge a read or write before Cassandra considers it successful — Cassandra always replicates data across multiple nodes (unlike everything covered so far in this course, which assumed a single authoritative copy or a primary-replica model), and the consistency level is what lets each individual operation trade off latency against durability and read accuracy.

```java
Statement<?> statement = QueryBuilder.selectFrom("orders").all()
    .whereColumn("customer_id").isEqualTo(literal("customer-A"))
    .build()
    .setConsistencyLevel(ConsistencyLevel.QUORUM);

cassandraTemplate.getCqlOperations().query(statement, (row, rowNum) -> row);
```

## 2. Why & when

Every table in a real Cassandra deployment has a **replication factor** — data isn't stored on one node, it's copied to several (commonly 3). A write doesn't have to wait for *every* replica to confirm before Cassandra calls it successful, and a read doesn't have to check *every* replica before returning an answer — the consistency level is the per-operation dial controlling exactly how many replicas must participate, trading off latency (fewer replicas = faster) against durability/accuracy guarantees (more replicas = safer against a node being down or lagging).

Reach for tuning the consistency level when:

- The default consistency level doesn't match an operation's actual requirements — a low-stakes analytics read might be fine with `ONE` (fast, might read slightly stale data), while a financial balance read needs `QUORUM` (slower, but guarantees seeing the latest acknowledged write).
- You need the mathematical guarantee that `write consistency + read consistency > replication factor` — this specific relationship is what guarantees a read will always see the most recent write, called "strong consistency" in Cassandra's tunable model.
- A node or datacenter outage is degrading availability, and you need to consciously choose whether to accept eventual (weaker) consistency to keep the system available, or fail requests that can't meet a stronger consistency requirement.

## 3. Core concept

```
 Replication factor = 3 (data copied to 3 nodes)

 ConsistencyLevel.ONE:     only 1 of 3 replicas must respond   -- FASTEST, weakest guarantee
 ConsistencyLevel.QUORUM:  a MAJORITY (2 of 3) must respond    -- balanced
 ConsistencyLevel.ALL:      all 3 replicas must respond         -- SLOWEST, strongest guarantee (fails if ANY replica is down)

 Strong consistency guarantee:  write_consistency + read_consistency > replication_factor
   e.g. QUORUM write (2) + QUORUM read (2) = 4 > 3 (replication factor)
        -> guaranteed to see the most recent write, because the read and write replica sets MUST overlap
```

Each operation independently chooses its consistency level — there's no single, fixed guarantee for the whole database, only per-operation trade-offs.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="With replication factor 3, a QUORUM write to 2 replicas and a QUORUM read from 2 replicas are mathematically guaranteed to overlap on at least one replica">
  <rect x="20" y="20" width="600" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="40" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">3 replicas: Node A, Node B, Node C</text>

  <rect x="60" y="70" width="140" height="40" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="130" y="94" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">Node A (write ACK)</text>
  <rect x="240" y="70" width="140" height="40" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="310" y="94" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">Node B (write ACK)</text>
  <rect x="420" y="70" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="490" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Node C (not written to)</text>

  <rect x="240" y="130" width="140" height="30" rx="6" fill="#79c0ff22" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="150" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">QUORUM read overlaps here</text>
  <line x1="310" y1="110" x2="310" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Because a `QUORUM` read also touches at least two of the three replicas, it's mathematically guaranteed to overlap with any `QUORUM` write's set of acknowledging replicas.

## 5. Runnable example

The scenario: writing and reading order data with different consistency levels, evolving from a basic ONE-vs-ALL trade-off demonstration, to a QUORUM read/write pair guaranteeing strong consistency, to simulating a node outage and observing how different consistency levels respond differently to it.

### Level 1 — Basic

Model the core trade-off: `ONE` succeeds even if replicas are unavailable; `ALL` requires every replica to be healthy.

```java
import java.util.*;

public class ConsistencyLevel1 {
    public static void main(String[] args) {
        CassandraCluster cluster = new CassandraCluster(List.of("node-A", "node-B", "node-C"));
        cluster.markNodeDown("node-C"); // one of three replicas is currently unreachable

        boolean writeWithOne = cluster.write("order:1", "PENDING", 1); // needs only 1 replica
        System.out.println("Write with consistency=ONE, 1 node down: succeeded=" + writeWithOne);

        boolean writeWithAll = cluster.write("order:2", "PENDING", 3); // needs ALL 3 replicas
        System.out.println("Write with consistency=ALL, 1 node down: succeeded=" + writeWithAll);
    }
}

class CassandraCluster {
    private final List<String> nodes;
    private final Set<String> downNodes = new HashSet<>();
    CassandraCluster(List<String> nodes) { this.nodes = nodes; }
    void markNodeDown(String node) { downNodes.add(node); }

    // Mirrors requiring `requiredAcks` replicas to acknowledge before the write is considered successful.
    boolean write(String key, String value, int requiredAcks) {
        int availableNodes = (int) nodes.stream().filter(n -> !downNodes.contains(n)).count();
        return availableNodes >= requiredAcks;
    }
}
```

How to run: `java ConsistencyLevel1.java`

With one of three replicas down, a write requiring only `1` acknowledgment (`ONE`) succeeds, since two nodes are still available — but a write requiring all `3` acknowledgments (`ALL`) fails outright, because it's structurally impossible to get an acknowledgment from a node that's down. This is the fundamental availability-vs-durability trade-off every consistency level choice makes.

### Level 2 — Intermediate

Model the `QUORUM` write + `QUORUM` read guarantee: with a replication factor of 3, `QUORUM` (2) for both read and write mathematically guarantees the two sets of replicas overlap.

```java
import java.util.*;

public class ConsistencyLevel2 {
    public static void main(String[] args) {
        CassandraCluster cluster = new CassandraCluster(List.of("node-A", "node-B", "node-C"));

        // A QUORUM write acknowledges from 2 of 3 replicas -- record WHICH ones, for the demonstration.
        Set<String> writeAckedBy = cluster.quorumWrite("order:1", "SHIPPED");
        System.out.println("QUORUM write acknowledged by: " + writeAckedBy);

        // A QUORUM read queries 2 of 3 replicas -- record WHICH ones.
        Set<String> readFrom = cluster.quorumRead("order:1");
        System.out.println("QUORUM read queried: " + readFrom);

        Set<String> overlap = new HashSet<>(writeAckedBy);
        overlap.retainAll(readFrom);
        System.out.println("Overlap (guaranteed non-empty with RF=3, QUORUM+QUORUM): " + overlap);
        System.out.println("Read is guaranteed to see the write: " + !overlap.isEmpty());
    }
}

class CassandraCluster {
    private final List<String> nodes;
    CassandraCluster(List<String> nodes) { this.nodes = nodes; }

    // Simplified: QUORUM picks the FIRST two nodes for a write, and the LAST two for a read --
    // deliberately different subsets, to demonstrate that ANY two-of-three sets from the SAME three nodes must overlap.
    Set<String> quorumWrite(String key, String value) { return new LinkedHashSet<>(nodes.subList(0, 2)); }
    Set<String> quorumRead(String key) { return new LinkedHashSet<>(nodes.subList(1, 3)); }
}
```

How to run: `java ConsistencyLevel2.java`

`quorumWrite` acknowledges from `node-A` and `node-B`; `quorumRead` (deliberately modeled as querying a *different* pair) queries `node-B` and `node-C`. Even though the two operations touch different specific replicas, their overlap is `{node-B}` — non-empty, guaranteed by the pigeonhole principle: with only 3 total replicas, any two distinct subsets of size 2 must share at least one member. This is exactly why `QUORUM` read after `QUORUM` write (with replication factor 3) is guaranteed to see the write, regardless of which specific replicas happen to respond to either operation.

### Level 3 — Advanced

Simulate a node outage and observe how `ONE`, `QUORUM`, and `ALL` respond differently — the practical availability consequence of each choice.

```java
import java.util.*;

public class ConsistencyLevel3 {
    public static void main(String[] args) {
        CassandraCluster cluster = new CassandraCluster(List.of("node-A", "node-B", "node-C"));

        System.out.println("--- all 3 nodes healthy ---");
        report(cluster);

        cluster.markNodeDown("node-C");
        System.out.println("--- node-C goes down (1 of 3 unavailable) ---");
        report(cluster);

        cluster.markNodeDown("node-B");
        System.out.println("--- node-B ALSO goes down (2 of 3 unavailable) ---");
        report(cluster);
    }

    static void report(CassandraCluster cluster) {
        System.out.println("  ONE:     " + (cluster.canSatisfy(1) ? "available" : "UNAVAILABLE"));
        System.out.println("  QUORUM:  " + (cluster.canSatisfy(2) ? "available" : "UNAVAILABLE"));
        System.out.println("  ALL:     " + (cluster.canSatisfy(3) ? "available" : "UNAVAILABLE"));
    }
}

class CassandraCluster {
    private final List<String> nodes;
    private final Set<String> downNodes = new HashSet<>();
    CassandraCluster(List<String> nodes) { this.nodes = nodes; }
    void markNodeDown(String node) { downNodes.add(node); }
    boolean canSatisfy(int requiredAcks) {
        int available = (int) nodes.stream().filter(n -> !downNodes.contains(n)).count();
        return available >= requiredAcks;
    }
}
```

How to run: `java ConsistencyLevel3.java`

With all three nodes healthy, every consistency level is satisfiable. Once `node-C` goes down, `ALL` becomes unavailable (only 2 of 3 nodes can respond, but `ALL` needs 3), while `ONE` and `QUORUM` remain available. Once `node-B` also goes down (only `node-A` remains), even `QUORUM` becomes unavailable — only `ONE` still works, since a single available node is enough to satisfy it.

## 6. Walkthrough

Execution starts in `main` for Level 3. `report(cluster)` is called three times, once at each stage of the simulated outage.

At the first call, `downNodes` is empty, so `cluster.canSatisfy(1)`, `canSatisfy(2)`, and `canSatisfy(3)` all compute `available = 3` and return `true` — every consistency level is available.

After `cluster.markNodeDown("node-C")`, `available` becomes `2` for every subsequent check. `canSatisfy(1)` (`2 >= 1`) and `canSatisfy(2)` (`2 >= 2`) both return `true`, but `canSatisfy(3)` (`2 >= 3`) returns `false` — `ALL` has become unavailable, while `ONE` and `QUORUM` remain usable.

After `cluster.markNodeDown("node-B")` as well, `available` drops to `1`. `canSatisfy(1)` (`1 >= 1`) still returns `true`, but both `canSatisfy(2)` (`1 >= 2`) and `canSatisfy(3)` (`1 >= 3`) now return `false` — only `ONE` remains available, with a single surviving replica.

```
--- all 3 nodes healthy ---
  ONE:     available
  QUORUM:  available
  ALL:     available
--- node-C goes down (1 of 3 unavailable) ---
  ONE:     available
  QUORUM:  available
  ALL:     UNAVAILABLE
--- node-B ALSO goes down (2 of 3 unavailable) ---
  ONE:     available
  QUORUM:  UNAVAILABLE
  ALL:     UNAVAILABLE
```

In a real Cassandra deployment, this exact progression is what "graceful degradation" looks like under partial cluster failure: an application using `ALL` for its writes loses write availability the moment a single replica goes down, while an application using `QUORUM` tolerates one node failure (out of three replicas) and only loses availability once a majority of replicas are unreachable — this is precisely why `QUORUM` is the most common production default, balancing strong consistency guarantees against reasonable fault tolerance.

## 7. Gotchas & takeaways

> Gotcha: consistency level is chosen *per operation*, not globally for the whole database — using `ONE` for writes but `QUORUM` for reads (or any other asymmetric combination) does not provide the strong consistency guarantee, since `1 + 2 = 3`, which is not strictly greater than the replication factor of `3`. The `write + read > replication factor` inequality must be checked with the *actual* consistency levels used for both, not assumed from using a "strong-sounding" level on just one side.

> Gotcha: a higher consistency level doesn't just add latency — it directly reduces the cluster's fault tolerance, since more replicas must be reachable and responsive for the operation to succeed at all. Choosing `ALL` "to be safe" for every operation can make an otherwise-healthy, partially-degraded cluster completely unavailable for writes, which is often a worse outcome than accepting `QUORUM`'s slightly weaker (but still strong, in the mathematical sense above) guarantee.

- Consistency level controls how many replicas must acknowledge a read or write before Cassandra considers the operation complete — a per-operation trade-off between latency/availability and durability/accuracy.
- `write consistency + read consistency > replication factor` is the specific mathematical condition guaranteeing a read always sees the most recent acknowledged write ("strong consistency" in Cassandra's tunable model).
- Higher consistency levels reduce fault tolerance: `ALL` requires every replica to be healthy, while `QUORUM` tolerates a minority of replicas being unavailable, and `ONE` tolerates the most failures at the cost of the weakest guarantee.
- `QUORUM` for both reads and writes is the common production default, balancing strong-consistency guarantees against reasonable resilience to individual node failures.
