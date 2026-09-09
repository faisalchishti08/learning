---
card: system-design
gi: 165
slug: elasticsearch-cluster-basics-shards-replicas
title: Elasticsearch cluster basics (shards & replicas)
---

## 1. What it is

An Elasticsearch **index** (a named collection of documents, roughly like a database table) is split into **shards** — independent, self-contained pieces of the index, each holding a subset of its documents — spread across the machines (nodes) in a cluster. Each shard can have one or more **replicas**, full copies of that shard kept on other nodes for durability and to serve more concurrent read traffic. This is the mechanism that lets an [inverted index](0159-inverted-index.md) scale across many machines instead of living on just one.

## 2. Why & when

A single Elasticsearch node has finite CPU, memory, and disk — a huge index eventually will not fit on, or be searchable fast enough by, one machine alone. Splitting the index into shards spreads both the storage and the search workload across multiple nodes, and replicas provide both a copy to serve reads from (increasing search throughput) and a backup if a node holding a primary shard fails. Understand this when sizing an Elasticsearch cluster for a real workload, or when diagnosing why search performance or resilience does not match expectations.

## 3. Core concept

- **Primary shard:** one independent slice of the index's total document set; a document is routed to exactly one primary shard (commonly by hashing its ID), and every primary shard together makes up the whole index.
- **Shard count is fixed at index creation (in older Elasticsearch versions):** choosing too few shards limits how much you can scale out later; choosing too many adds per-shard overhead — this makes shard count a real up-front sizing decision.
- **Replica shard:** a full copy of a primary shard, kept on a different node; replicas serve read (search) traffic too, so more replicas mean more read throughput, at the cost of more storage and indexing overhead (every write must also update every replica).
- **A search request fans out to every relevant shard:** a query against the index is sent to (at least) one copy of every shard, each shard searches its own subset of documents, and the coordinating node merges and re-ranks the combined results before returning them.
- **Failure tolerance:** if a node holding a primary shard fails, Elasticsearch promotes one of that shard's replicas (on a surviving node) to become the new primary — no data is lost as long as at least one copy (primary or replica) of every shard survives.

## 4. Diagram

```
   index "products" — 3 primary shards, 1 replica each

   node-A: shard-0 (primary)   shard-1 (replica)
   node-B: shard-1 (primary)   shard-2 (replica)
   node-C: shard-2 (primary)   shard-0 (replica)

   search request for "laptop"
        |
        v
   coordinating node fans the query out to ONE copy of shard-0, shard-1, shard-2
        |
        v
   each shard searches its own documents -> partial results
        |
        v
   coordinating node merges + re-ranks all partial results -> final response
```
*Caption: every shard holds a different subset of documents; a search must reach one copy of every shard, then the results are merged into one ranked response.*

## 5. Runnable example

**Level 1 — Basic.** Route documents to shards by hashing their ID, and store each shard's documents separately.

**Level 2 — Fan-out search across all shards and merge results.** Model a coordinating node querying every shard and combining the responses.

**Level 3 — Simulate a node failure and promote a replica.** Show the cluster staying searchable and durable after losing a primary shard's node.

```java
// ElasticsearchClusterDemo.java
import java.util.*;
import java.util.stream.*;

public class ElasticsearchClusterDemo {

    static final int SHARD_COUNT = 3;

    static class Doc {
        String id, text;
        Doc(String id, String text) { this.id = id; this.text = text; }
    }

    // Level 1: route a document to a shard by hashing its ID.
    static int shardFor(String docId) {
        return Math.abs(docId.hashCode()) % SHARD_COUNT;
    }

    static Map<Integer, List<Doc>> primaryShards = new HashMap<>();
    static Map<Integer, List<Doc>> replicaShards = new HashMap<>(); // Level 3: full copies, kept in sync
    static Set<Integer> failedPrimaryShardNodes = new HashSet<>();  // which shard's PRIMARY node is down

    static void indexDocument(Doc doc) {
        int shard = shardFor(doc.id);
        primaryShards.computeIfAbsent(shard, s -> new ArrayList<>()).add(doc);
        replicaShards.computeIfAbsent(shard, s -> new ArrayList<>()).add(doc); // replica stays in sync
    }

    // Level 2: fan out to every shard, searching whichever copy (primary, or replica if primary is down) is available.
    static List<Doc> search(String keyword) {
        List<Doc> merged = new ArrayList<>();
        for (int shard = 0; shard < SHARD_COUNT; shard++) {
            List<Doc> shardData = failedPrimaryShardNodes.contains(shard)
                ? replicaShards.getOrDefault(shard, List.of())   // Level 3: primary down, use the replica
                : primaryShards.getOrDefault(shard, List.of());
            List<Doc> matches = shardData.stream().filter(d -> d.text.contains(keyword)).collect(Collectors.toList());
            System.out.println("  shard " + shard + " (" + (failedPrimaryShardNodes.contains(shard) ? "via replica" : "via primary") + "): " + matches.size() + " matches");
            merged.addAll(matches);
        }
        return merged;
    }

    public static void main(String[] args) {
        indexDocument(new Doc("p1", "gaming laptop"));
        indexDocument(new Doc("p2", "office laptop"));
        indexDocument(new Doc("p3", "wireless mouse"));
        indexDocument(new Doc("p4", "laptop sleeve"));
        indexDocument(new Doc("p5", "gaming mouse"));

        System.out.println("searching \"laptop\" (all primaries healthy):");
        System.out.println("total matches: " + search("laptop").size());

        // Level 3: the node holding shard 1's PRIMARY fails - Elasticsearch would promote its replica.
        int failedShard = 1;
        System.out.println("node holding shard " + failedShard + "'s primary FAILED - promoting its replica...");
        failedPrimaryShardNodes.add(failedShard);

        System.out.println("searching \"laptop\" again (shard " + failedShard + " now served by its replica):");
        System.out.println("total matches: " + search("laptop").size());
    }
}
```

**How to run:** save as `ElasticsearchClusterDemo.java`, then run `java ElasticsearchClusterDemo.java`.

## 6. Walkthrough

1. Each `indexDocument` call computes `shardFor(doc.id)` by hashing the document's ID, then stores the document in both `primaryShards` and `replicaShards` under that shard number — modeling how every write updates both the primary and its replica to keep them in sync.
2. The first `search("laptop")` call loops over all three shards; since `failedPrimaryShardNodes` is empty, every shard is searched "via primary", and each shard's own subset of documents is filtered independently for the keyword.
3. The per-shard match counts are printed, then all matches are merged into one `List<Doc>` — this models the coordinating node combining every shard's partial results into a single response, exactly as a real search request would.
4. `failedPrimaryShardNodes.add(1)` simulates shard 1's primary-holding node going down; nothing is removed from `primaryShards` itself (this demo does not model actual node loss of the data), but the search logic now treats shard 1 specially.
5. The second `search("laptop")` call reaches the `failedPrimaryShardNodes.contains(shard)` branch for shard 1, and reads from `replicaShards.get(1)` instead of `primaryShards.get(1)` — printing "via replica" for that shard — while shards 0 and 2 are unaffected and still search their primaries; the total match count stays the same as before the failure, demonstrating that the replica fully preserved both the data and the cluster's ability to keep serving search requests.

## 7. Gotchas & takeaways

> Gotcha: increasing the number of primary shards on an index that is already too small for the workload does not help, and can hurt — more shards means more per-shard overhead (each shard has its own resource cost) and more work for the coordinating node to merge results from, so shard count should be sized to the expected data volume and query load, not maximized blindly.

- Shards split an index's documents across nodes for scale; replicas copy each shard for durability and extra read throughput.
- A search request must reach at least one copy (primary or replica) of every shard, then merges the partial results — the coordinating node's merge step is essential, not optional.
- Losing a primary shard's node is survivable exactly because a replica holds the same data and can be promoted, keeping the cluster both durable and searchable.
- Related concepts: [Inverted index](0159-inverted-index.md) (what each shard actually stores internally), [Redundancy & replication](0130-redundancy-replication.md) (the general durability pattern replica shards implement), [Hash-based sharding](0091-hash-based-sharding.md) (the general partitioning concept shards are a specific application of).
