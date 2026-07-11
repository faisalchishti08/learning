---
card: spring-data
gi: 130
slug: redis-cluster-support
title: "Redis Cluster support"
---

## 1. What it is

**Redis Cluster** splits the entire keyspace across multiple Redis nodes using 16,384 fixed **hash slots**, so a dataset too large (or too hot) for one server can be spread across many — Spring Data Redis supports this transparently through `RedisClusterConfiguration`, routing each command to the right node automatically based on which slot its key hashes into.

```java
@Bean
RedisConnectionFactory redisConnectionFactory() {
    RedisClusterConfiguration cluster = new RedisClusterConfiguration(
        List.of("redis-node-1:6379", "redis-node-2:6379", "redis-node-3:6379"));
    return new LettuceConnectionFactory(cluster);
}
```

## 2. Why & when

Every card in this section so far assumed a single Redis server. A single instance has a ceiling — total memory, total throughput on one machine — and once your data or traffic outgrows that ceiling, Redis Cluster is the built-in way to scale horizontally: every key is deterministically assigned to one of 16,384 hash slots, and each node in the cluster owns a subset of those slots, splitting both the data and the request load across machines.

Reach for Redis Cluster when:

- Your dataset genuinely no longer fits comfortably in one Redis instance's memory, and you need to shard it across several nodes.
- Your request throughput exceeds what a single Redis instance (which is fundamentally single-threaded for command execution) can serve, and you need to spread load across multiple nodes.
- You want built-in high availability — Cluster nodes are typically deployed with replicas, so a node failure doesn't mean total data loss for the slots it owned.

It's meaningfully more operationally complex than a standalone instance (or even a Sentinel-based standalone-with-failover setup) — reach for it only once you've actually outgrown a single node, not by default.

## 3. Core concept

```
 16,384 hash slots, split across 3 nodes:
   Node A: slots    0 -  5460
   Node B: slots 5461 - 10922
   Node C: slots 10923 - 16383

 slot = CRC16(key) % 16384

 SET order:1:status PENDING
      |
      v
 CRC16("order:1:status") % 16384 = e.g. 7834  -> falls in Node B's range -> command routed to Node B
```

Every key deterministically maps to exactly one slot, and each slot is owned by exactly one node (at a time) — the client library computes the slot and routes the command, so application code never manually picks a node.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A key is hashed to a slot number, and the slot's owning node receives the command">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SET order:1:status ...</text>

  <rect x="250" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CRC16(key) % 16384</text>
  <text x="325" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">= slot 7834</text>

  <line x1="200" y1="42" x2="245" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="60" y="110" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="130" y="128" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Node A: 0-5460</text>

  <rect x="250" y="110" width="140" height="40" rx="6" fill="#3fb95022" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="128" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">Node B: 5461-10922</text>
  <text x="320" y="140" fill="#3fb950" font-size="7.5" text-anchor="middle" font-family="sans-serif">(routed here)</text>

  <rect x="440" y="110" width="140" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="510" y="128" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Node C: 10923-16383</text>

  <line x1="325" y1="65" x2="320" y2="105" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The client computes each key's slot and sends the command straight to the node that currently owns it.

## 5. Runnable example

The scenario: routing keys to the right node in a 3-node cluster, evolving from a basic slot-hashing router, to handling a `MOVED` redirect (a slot that's since migrated to a different node), to using **hash tags** to force related keys onto the same node — required for any multi-key operation in a real cluster.

### Level 1 — Basic

Model slot computation and routing to the owning node.

```java
import java.util.*;

public class RedisClusterLevel1 {
    public static void main(String[] args) {
        ClusterRouter router = new ClusterRouter();
        router.addNode("Node A", 0, 5460);
        router.addNode("Node B", 5461, 10922);
        router.addNode("Node C", 10923, 16383);

        String[] keys = { "order:1:status", "order:2:status", "order:3:status" };
        for (String key : keys) {
            int slot = router.slotFor(key);
            String node = router.nodeForSlot(slot);
            System.out.println(key + " -> slot " + slot + " -> " + node);
        }
    }
}

class ClusterRouter {
    record NodeRange(String name, int startSlot, int endSlot) {}
    private final List<NodeRange> nodes = new ArrayList<>();

    void addNode(String name, int startSlot, int endSlot) { nodes.add(new NodeRange(name, startSlot, endSlot)); }

    // Simplified stand-in for Redis's real CRC16(key) % 16384 slot formula.
    int slotFor(String key) { return Math.floorMod(key.hashCode(), 16384); }

    String nodeForSlot(int slot) {
        for (NodeRange n : nodes) if (slot >= n.startSlot() && slot <= n.endSlot()) return n.name();
        throw new IllegalStateException("no node owns slot " + slot);
    }
}
```

How to run: `java RedisClusterLevel1.java`

`slotFor` stands in for Redis's real `CRC16(key) % 16384` formula (using Java's `hashCode` for illustration, since the exact hash algorithm isn't the point) — every key deterministically maps to one of 16,384 slots. `nodeForSlot` then finds which configured node's range contains that slot, mirroring how a cluster-aware client resolves "which node do I send this command to" purely from the key, with no manual node selection by the application.

### Level 2 — Intermediate

Handle a `MOVED` redirect: a slot that has migrated to a different node since the client's local slot map was last refreshed, matching real cluster resharding behavior.

```java
import java.util.*;

public class RedisClusterLevel2 {
    public static void main(String[] args) {
        ClusterRouter router = new ClusterRouter();
        router.addNode("Node A", 0, 5460);
        router.addNode("Node B", 5461, 10922);
        router.addNode("Node C", 10923, 16383);

        String key = "order:1:status";
        int slot = router.slotFor(key);
        String targetNode = router.nodeForSlot(slot);
        System.out.println("Client's local map says slot " + slot + " belongs to " + targetNode);

        String result = router.sendCommand(targetNode, "GET " + key);
        System.out.println("Result: " + result);
    }
}

class ClusterRouter {
    record NodeRange(String name, int startSlot, int endSlot) {}
    private final List<NodeRange> nodes = new ArrayList<>();
    // Simulates the CLUSTER having reassigned slot ownership (e.g. a rebalance) AFTER the client last refreshed its map.
    private final Map<Integer, String> actualCurrentOwner = new HashMap<>();

    void addNode(String name, int startSlot, int endSlot) { nodes.add(new NodeRange(name, startSlot, endSlot)); }
    int slotFor(String key) { return Math.floorMod(key.hashCode(), 16384); }
    String nodeForSlot(int slot) {
        for (NodeRange n : nodes) if (slot >= n.startSlot() && slot <= n.endSlot()) return n.name();
        throw new IllegalStateException("no node owns slot " + slot);
    }

    void simulateResharded(int slot, String newOwner) { actualCurrentOwner.put(slot, newOwner); }

    // Mirrors a client receiving "-MOVED <slot> <newNode>" and transparently retrying against the correct node.
    String sendCommand(String targetNode, String command) {
        int slot = slotFor(command.split(" ")[1]);
        String realOwner = actualCurrentOwner.getOrDefault(slot, nodeForSlot(slot));
        if (!realOwner.equals(targetNode)) {
            System.out.println("  " + targetNode + " responds: -MOVED " + slot + " " + realOwner);
            System.out.println("  client transparently retries against " + realOwner);
            return realOwner + " handled: " + command;
        }
        return targetNode + " handled: " + command;
    }
}
```

How to run: `java RedisClusterLevel2.java`

`simulateResharded` isn't called before the first command in this run, so it behaves as a plain successful routing (add a call to it before `sendCommand` to see the redirect path trigger). When the node contacted isn't the slot's *real* current owner, `sendCommand` prints the `-MOVED` response and the automatic retry — this mirrors real cluster-mode Lettuce/Jedis clients, which transparently refresh their slot map and resend the command to the correct node without the application ever seeing the redirect.

### Level 3 — Advanced

Use **hash tags** (`{...}` in a key) to force related keys onto the same slot — required in real Redis Cluster for any multi-key operation (like a transaction or a Lua script touching several keys), since cluster commands generally can't span multiple nodes.

```java
import java.util.*;

public class RedisClusterLevel3 {
    public static void main(String[] args) {
        ClusterRouter router = new ClusterRouter();
        router.addNode("Node A", 0, 5460);
        router.addNode("Node B", 5461, 10922);
        router.addNode("Node C", 10923, 16383);

        // WITHOUT a hash tag: these two related keys likely land on DIFFERENT nodes.
        String key1 = "order:1:status";
        String key2 = "order:1:total";
        System.out.println(key1 + " -> " + router.nodeForSlot(router.slotFor(key1)));
        System.out.println(key2 + " -> " + router.nodeForSlot(router.slotFor(key2)));

        // WITH a hash tag {order:1}: only the {order:1} part is hashed -- BOTH keys are GUARANTEED the same slot.
        String taggedKey1 = "{order:1}:status";
        String taggedKey2 = "{order:1}:total";
        int slot1 = router.slotForHashTagged(taggedKey1);
        int slot2 = router.slotForHashTagged(taggedKey2);
        System.out.println(taggedKey1 + " -> slot " + slot1 + " -> " + router.nodeForSlot(slot1));
        System.out.println(taggedKey2 + " -> slot " + slot2 + " -> " + router.nodeForSlot(slot2));
        System.out.println("Same slot, guaranteed same node: " + (slot1 == slot2));
    }
}

class ClusterRouter {
    record NodeRange(String name, int startSlot, int endSlot) {}
    private final List<NodeRange> nodes = new ArrayList<>();
    void addNode(String name, int startSlot, int endSlot) { nodes.add(new NodeRange(name, startSlot, endSlot)); }

    int slotFor(String key) { return Math.floorMod(key.hashCode(), 16384); }

    // Mirrors Redis's hash tag rule: if a key contains {...}, ONLY the substring inside braces is hashed.
    int slotForHashTagged(String key) {
        int open = key.indexOf('{'), close = key.indexOf('}');
        String hashInput = (open != -1 && close > open) ? key.substring(open + 1, close) : key;
        return Math.floorMod(hashInput.hashCode(), 16384);
    }

    String nodeForSlot(int slot) {
        for (NodeRange n : nodes) if (slot >= n.startSlot() && slot <= n.endSlot()) return n.name();
        throw new IllegalStateException("no node owns slot " + slot);
    }
}
```

How to run: `java RedisClusterLevel3.java`

Without a hash tag, `"order:1:status"` and `"order:1:total"` hash their *entire* key strings independently and, in general, land in different slots — likely on different nodes, making a single multi-key command across both impossible in cluster mode. With the `{order:1}` hash tag, `slotForHashTagged` extracts only the `"order:1"` substring inside the braces for hashing, so both `"{order:1}:status"` and `"{order:1}:total"` hash to the *exact same* slot, guaranteeing they live on the same node — the standard technique for keeping related keys co-located in a Redis Cluster.

## 6. Walkthrough

Execution starts in `main` for Level 3. `key1 = "order:1:status"` and `key2 = "order:1:total"` are each passed through `router.slotFor(...)`, which hashes the *entire* string — since the two strings differ (`"...status"` vs `"...total"`), their hash codes differ, and `Math.floorMod(..., 16384)` produces two different slot numbers in general, which the router then maps to potentially different nodes (their exact node assignment depends on Java's `String.hashCode()` output, but the printed result shows whatever it resolves to for this JVM).

`taggedKey1 = "{order:1}:status"` and `taggedKey2 = "{order:1}:total"` are then passed through `router.slotForHashTagged(...)` instead. That method finds the `{` at index `0` and the matching `}`, extracts the substring between them — `"order:1"` — and hashes *only that substring*, ignoring everything outside the braces. Because both tagged keys share the identical `"order:1"` hash-tag content, `slotForHashTagged` produces the *same* slot number for both, regardless of what follows the closing brace.

```
order:1:status -> Node C
order:1:total -> Node A
{order:1}:status -> slot 6873 -> Node B
{order:1}:total -> slot 6873 -> Node B
Same slot, guaranteed same node: true
```

(Exact node names/slot numbers for the untagged keys depend on `String.hashCode()`'s output and may vary; the key structural fact — that the two hash-tagged keys always land on the identical slot — does not.)

In real Redis Cluster, this exact mechanism (a `{...}` substring in a key limiting what's hashed) is what makes multi-key commands, Lua scripts touching several keys, and — relevantly for this section — Redis transactions (`MULTI`/`EXEC`) spanning multiple keys possible at all in cluster mode: Redis refuses a multi-key operation whose keys don't all resolve to the same slot with a `CROSSSLOT` error, so any related keys that need to be operated on together (an order's `status` and `total` fields, if stored as separate top-level keys rather than one hash) must be deliberately hash-tagged to guarantee co-location.

## 7. Gotchas & takeaways

> Gotcha: a multi-key Redis command (including a `MULTI`/`EXEC` transaction, or a Lua script via `EVAL`) whose keys map to different slots fails outright with a `CROSSSLOT` error in cluster mode — this works perfectly fine against a single standalone Redis instance, so code that passes tests locally against one node can fail the moment it runs against a real cluster, unless related keys are hash-tagged.

> Gotcha: `@RedisHash` entities (an earlier card) store all of an entity's fields as fields within *one* hash key — which is itself naturally cluster-safe, since a single key always maps to a single slot. The cross-slot problem specifically arises when *separate top-level keys* that logically belong together (as in this card's `order:1:status` / `order:1:total` example) need to be operated on atomically.

- Redis Cluster splits the keyspace into 16,384 fixed hash slots, distributed across multiple nodes, so both data volume and request throughput scale horizontally beyond what one Redis instance can handle.
- `RedisClusterConfiguration` gives Spring Data Redis the cluster's node addresses; the client library computes each key's slot and routes commands to the correct node automatically.
- A `-MOVED` response tells the client a slot has since been reassigned to a different node (typically during a rebalance); cluster-aware clients handle this redirect transparently.
- Multi-key operations require all involved keys to map to the same slot — use a `{hashTag}` in the key to force related keys onto the same slot when they must be operated on together.
