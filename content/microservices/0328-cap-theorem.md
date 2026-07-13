---
card: microservices
gi: 328
slug: cap-theorem
title: "CAP theorem"
---

## 1. What it is

The **CAP theorem** states that a distributed data system can provide at most two of three properties at the same time: **Consistency** (every read sees the most recent write, or an error), **Availability** (every request gets a non-error response), and **Partition tolerance** (the system keeps working even when network messages between nodes are delayed or dropped). Because real networks *will* eventually partition, partition tolerance is not really optional in a distributed system — so in practice CAP is a choice between **C** and **A** during a partition, not a free choice among all three.

## 2. Why & when

Microservices are, by definition, a distributed system: independent services, independent databases, connected over a network that can and will fail or slow down. CAP theorem explains, in a precise and unavoidable way, why the earlier decision to avoid [2PC/XA](0318-why-2pc-xa-is-avoided-in-microservices.md) in favor of [sagas](0320-saga-pattern.md) and [eventual consistency](0326-eventual-consistency.md) isn't a stylistic preference — it's a response to a mathematical limit. During a network partition (a service temporarily can't reach another), you must choose: refuse to respond until you can confirm you have the latest data (favoring **C**), or respond anyway using whatever data you currently have, possibly stale (favoring **A**).

Use CAP as a framing tool whenever you are choosing a datastore or a replication strategy for a distributed piece of data: ask explicitly which side of C-versus-A this component needs to fall on if its network connections degrade, and pick technology and design accordingly, rather than discovering the answer by accident during an incident.

## 3. Core concept

During normal operation, with no partition, a well-designed system can offer both consistency and availability simultaneously — CAP only forces a real choice once a partition actually occurs. **CP** systems (like most traditional relational databases used strictly, or ZooKeeper/etcd) refuse or block requests during a partition rather than risk returning stale or conflicting data. **AP** systems (like many NoSQL stores in their default configuration, or a saga-based microservices flow) keep responding during a partition, accepting that different nodes might temporarily disagree.

```java
enum CapChoice { CP, AP } // the choice you must make, ONLY during an actual network partition
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A triangle with Consistency, Availability, and Partition tolerance at each corner; partition tolerance is required, so the real choice during a partition is between the C and A corners">
  <polygon points="320,20 60,170 580,170" fill="none" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="15" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Consistency</text>
  <text x="60" y="188" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Availability</text>
  <text x="580" y="188" fill="#f0883e" font-size="12" text-anchor="middle" font-family="sans-serif">Partition tolerance</text>
  <text x="320" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Partitions WILL happen --</text>
  <text x="320" y="126" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">real choice is C vs A</text>
</svg>

Partition tolerance isn't optional in a real distributed system — the actual decision under a network partition is between consistency and availability.

## 5. Runnable example

Scenario: a key-value store replicated across two nodes, first shown naively assuming both are always reachable, then forced to choose CP (block during a partition) or AP (respond with possibly-stale data), and finally extended to make the choice configurable per operation, since not every read needs the same guarantee.

### Level 1 — Basic

```java
// File: NoPartitionAssumed.java -- a naive replicated store that assumes
// both nodes are ALWAYS reachable -- doesn't yet confront the CAP choice.
import java.util.*;

public class NoPartitionAssumed {
    static Map<String, String> nodeA = new HashMap<>();
    static Map<String, String> nodeB = new HashMap<>();

    static void write(String key, String value) {
        nodeA.put(key, value); nodeB.put(key, value); // assumes BOTH always succeed
        System.out.println("wrote to both nodes: " + key + "=" + value);
    }

    public static void main(String[] args) {
        write("balance", "100");
        System.out.println("nodeA: " + nodeA.get("balance") + ", nodeB: " + nodeB.get("balance") + " -- always agree, in this idealized world.");
    }
}
```

How to run: `java NoPartitionAssumed.java`

`write` assumes replicating to both nodes always succeeds — a fine assumption right up until the network between them actually fails, at which point this code has no defined behavior at all. This Level exists purely to show the naive starting point before the CAP tradeoff is confronted.

### Level 2 — Intermediate

```java
// File: CpVsApUnderPartition.java -- a partition occurs (nodeB is
// unreachable); this shows BOTH a CP response (refuse) and an AP response
// (serve stale data from nodeA) to the same read.
import java.util.*;

public class CpVsApUnderPartition {
    static Map<String, String> nodeA = new HashMap<>();
    static Map<String, String> nodeB = new HashMap<>();
    static boolean nodeBReachable = false; // simulated partition

    static void write(String key, String value) {
        nodeA.put(key, value);
        if (nodeBReachable) nodeB.put(key, value);
        else System.out.println("nodeB UNREACHABLE -- write only landed on nodeA so far");
    }

    static String readCP(String key) { // Consistency-favoring: refuse if we can't confirm agreement
        if (!nodeBReachable) { System.out.println("CP read: nodeB unreachable, CANNOT confirm consistency -- REFUSING"); return null; }
        return nodeA.get(key);
    }

    static String readAP(String key) { // Availability-favoring: answer anyway, even if possibly stale
        String value = nodeA.get(key);
        System.out.println("AP read: answering from nodeA regardless of nodeB's reachability (possibly stale elsewhere): " + value);
        return value;
    }

    public static void main(String[] args) {
        write("balance", "100");
        System.out.println("CP result: " + readCP("balance"));
        System.out.println("AP result: " + readAP("balance"));
    }
}
```

How to run: `java CpVsApUnderPartition.java`

With `nodeBReachable=false`, `write` only lands on `nodeA`. `readCP` checks reachability first and refuses outright, returning `null` and explicitly logging that consistency cannot be confirmed — no answer is better than a possibly-wrong one, in this design. `readAP` ignores reachability entirely and answers from whatever local data is available — a response is always given, at the cost of it possibly disagreeing with what `nodeB` would say if reachable.

### Level 3 — Advanced

```java
// File: PerOperationCapChoice.java -- different operations on the SAME
// store choose DIFFERENT sides of CAP: a balance check favors consistency
// (CP), while a "recent activity feed" favors availability (AP), because
// the cost of being wrong differs by use case.
import java.util.*;

public class PerOperationCapChoice {
    static Map<String, String> nodeA = new HashMap<>();
    static boolean nodeBReachable = false;

    static Optional<String> readBalanceCP(String key) { // money: WRONG answer is worse than NO answer
        if (!nodeBReachable) {
            System.out.println("readBalanceCP: partition detected -- REFUSING rather than risk showing a stale balance");
            return Optional.empty();
        }
        return Optional.of(nodeA.get(key));
    }

    static String readActivityFeedAP(String key) { // a feed: STALE answer is fine, no answer is worse
        String value = nodeA.getOrDefault(key, "(no recent activity)");
        System.out.println("readActivityFeedAP: answering regardless of partition state (staleness acceptable here): " + value);
        return value;
    }

    public static void main(String[] args) {
        nodeA.put("balance", "100");
        nodeA.put("activityFeed", "3 new posts");

        Optional<String> balance = readBalanceCP("balance");
        System.out.println("Balance check result: " + (balance.isPresent() ? balance.get() : "REFUSED -- try again later"));

        String feed = readActivityFeedAP("activityFeed");
        System.out.println("Activity feed result: " + feed + " (shown even though we can't confirm it's the latest)");
    }
}
```

How to run: `java PerOperationCapChoice.java`

Both reads hit the same underlying `nodeA` data and the same partitioned state (`nodeBReachable=false`), but `readBalanceCP` and `readActivityFeedAP` make opposite CAP choices deliberately: the balance check refuses under partition because showing a wrong balance could mean a user makes a decision based on incorrect money data, while the activity feed answers regardless, because a slightly stale "3 new posts" is a perfectly acceptable outcome, and refusing to show anything would be a worse user experience than the risk of staleness.

## 6. Walkthrough

Trace `PerOperationCapChoice.main` in order. **First**, `nodeA` is populated with a balance and an activity feed value; `nodeBReachable` stays `false` throughout, simulating an ongoing partition.

**Next**, `readBalanceCP("balance")` runs. Inside, `nodeBReachable` is `false`, so the `if` branch executes: it prints a message explaining the refusal and returns `Optional.empty()` — no balance value is ever read from `nodeA` in this path, by design, since the method has already decided a partition makes it unsafe to answer.

**Back in `main`**, `balance.isPresent()` is `false`, so the printed result is `"REFUSED -- try again later"` — a deliberate, informative failure rather than a possibly-wrong number.

**Then**, `readActivityFeedAP("activityFeed")` runs. It does not check `nodeBReachable` at all; it simply reads `nodeA.getOrDefault("activityFeed", ...)`, gets `"3 new posts"`, prints it, and returns it directly.

**Finally**, `main` prints the feed result — a value was returned even though the exact same partitioned condition was in effect as during the balance check, illustrating that the CAP choice is made *per operation*, based on what each operation's use case actually needs, not as one global setting for the whole system.

```
partition: nodeB unreachable, nodeA has local data
readBalanceCP()      -> checks reachability -> REFUSES (favors Consistency)
readActivityFeedAP() -> ignores reachability -> ANSWERS from local data (favors Availability)
```

## 7. Gotchas & takeaways

> CAP is often mistaken for "pick any two of three, always" — in reality, partition tolerance must be assumed for any real network, so the theorem is really about the C-versus-A choice specifically during the (hopefully rare, but inevitable) moments a partition is actually happening; outside of a partition, a well-built system can offer both.

- CAP forces a real choice only during an actual network partition: consistency (refuse if unsure) or availability (answer anyway, possibly stale).
- The right choice differs by operation and business impact — money-related reads often favor consistency, while low-stakes, high-traffic reads often favor availability.
- Microservices architectures that adopt [sagas](0320-saga-pattern.md) and [eventual consistency](0326-eventual-consistency.md) have implicitly chosen AP for cross-service data, in exchange for availability.
- [PACELC](0329-pacelc-theorem.md) extends this reasoning to cover the tradeoff a system faces even when there is *no* partition at all.
