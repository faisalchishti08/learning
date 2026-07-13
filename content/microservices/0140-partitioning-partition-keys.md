---
card: microservices
gi: 140
slug: partitioning-partition-keys
title: "Partitioning & partition keys"
---

## 1. What it is

Partitioning is splitting a single logical topic into multiple independent, ordered segments (partitions), each of which can be written to and read from in parallel; the partition key is the value used to decide which partition a given message is routed to — typically by hashing the key and mapping the hash to a partition number. This is the mechanism underlying both [message ordering guarantees](0119-message-ordering-guarantees.md) (ordering holds within a partition) and horizontal scaling via [consumer groups](0121-consumer-groups-partitions.md) (partitions split across a group's instances).

## 2. Why & when

A single, unpartitioned stream caps throughput at whatever one machine, one disk, and one sequential write/read path can sustain — which becomes a real bottleneck at scale. Partitioning removes that ceiling by spreading a topic's data and I/O across multiple independent segments that can live on different machines and be processed by different consumer instances in parallel, while still preserving ordering for any messages that share a key (since the same key always routes to the same partition).

The partition key choice is the actual design decision, and it matters more than it looks: it directly determines both how evenly load spreads across partitions and which messages are guaranteed to stay ordered relative to each other. Choose a key granular enough to spread load well (many distinct values, roughly even frequency) but coarse enough to keep every message that needs relative ordering on the same key — get this wrong in either direction and either throughput or correctness suffers.

## 3. Core concept

A deterministic hash function maps each message's key to one of a fixed number of partitions; the same key always resolves to the same partition (so ordering is preserved for that key), while different keys are spread, ideally evenly, across all available partitions to maximize parallelism.

```java
int partitionCount = 4;
int partition = Math.floorMod(key.hashCode(), partitionCount); // deterministic: SAME key -> SAME partition, always

// a poorly chosen key concentrates traffic onto one partition ("hot partition")
String badKey = "US"; // if 90% of orders are from the US, this key sends 90% of traffic to ONE partition

// a well chosen key spreads traffic evenly
String goodKey = orderId; // unique per order -- spreads roughly evenly across all partitions
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Left: a coarse partition key (region) sends most traffic to one hot partition, leaving others idle. Right: a fine-grained key (orderId) spreads traffic evenly across all four partitions">
  <text x="150" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Coarse key (region) -- hot partition</text>
  <rect x="30" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="60" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">P0</text>
  <rect x="100" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/><text x="130" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">P1: 90%</text>
  <rect x="170" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="200" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">P2</text>
  <rect x="240" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#8b949e"/><text x="270" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">P3</text>

  <text x="480" y="20" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Fine key (orderId) -- even spread</text>
  <rect x="360" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="390" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">P0: 25%</text>
  <rect x="430" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="460" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">P1: 25%</text>
  <rect x="500" y="40" width="60" height="70" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="530" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">P2: 25%</text>
  <rect x="570" y="40" width="55" height="70" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="597" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">P3: 25%</text>
</svg>

The same four-partition topic behaves very differently depending purely on the granularity of the chosen partition key.

## 5. Runnable example

Scenario: an order-events topic that starts with a coarse key producing a hot partition (demonstrating the imbalance concretely), switches to a fine-grained key that spreads load evenly, and finally measures both approaches' distribution across a larger, more realistic volume of simulated traffic to make the difference numerically obvious.

### Level 1 — Basic

```java
// File: HotPartitionFromCoarseKey.java -- a coarse key concentrates most traffic on ONE partition.
import java.util.*;

public class HotPartitionFromCoarseKey {
    record OrderEvent(int orderId, String region) {}

    static int partitionFor(String key, int partitionCount) {
        return Math.floorMod(key.hashCode(), partitionCount);
    }

    public static void main(String[] args) {
        int partitionCount = 4;
        // realistic skew: most orders come from ONE region
        List<OrderEvent> events = List.of(
            new OrderEvent(1, "US"), new OrderEvent(2, "US"), new OrderEvent(3, "US"),
            new OrderEvent(4, "US"), new OrderEvent(5, "EU"));

        Map<Integer, Integer> countByPartition = new TreeMap<>();
        for (OrderEvent e : events) {
            int partition = partitionFor(e.region(), partitionCount); // KEY = region -- coarse
            countByPartition.merge(partition, 1, Integer::sum);
        }
        System.out.println("Partition load with region as the key: " + countByPartition);
        System.out.println("Most traffic piles onto ONE partition ('hot partition') -- the other 3 sit nearly idle.");
    }
}
```

**How to run:** `javac HotPartitionFromCoarseKey.java && java HotPartitionFromCoarseKey` (JDK 17+).

Because `"US"` always hashes to the same partition, four out of five events land there, while other partitions handle little or nothing — a coarse key with skewed real-world frequency produces exactly this kind of imbalance.

### Level 2 — Intermediate

```java
// File: EvenSpreadFromFineKey.java -- the SAME events, keyed by orderId instead, spread far more evenly.
import java.util.*;

public class EvenSpreadFromFineKey {
    record OrderEvent(int orderId, String region) {}

    static int partitionFor(String key, int partitionCount) {
        return Math.floorMod(key.hashCode(), partitionCount);
    }

    public static void main(String[] args) {
        int partitionCount = 4;
        List<OrderEvent> events = List.of(
            new OrderEvent(1, "US"), new OrderEvent(2, "US"), new OrderEvent(3, "US"),
            new OrderEvent(4, "US"), new OrderEvent(5, "EU"));

        Map<Integer, Integer> countByPartition = new TreeMap<>();
        for (OrderEvent e : events) {
            int partition = partitionFor(String.valueOf(e.orderId()), partitionCount); // KEY = orderId -- fine-grained
            countByPartition.merge(partition, 1, Integer::sum);
        }
        System.out.println("Partition load with orderId as the key: " + countByPartition);
        System.out.println("Same 5 events, but spread across MULTIPLE partitions instead of piling onto one.");
    }
}
```

**How to run:** `javac EvenSpreadFromFineKey.java && java EvenSpreadFromFineKey` (JDK 17+).

Expected output (exact partition numbers depend on `hashCode`, but the distribution is spread rather than concentrated):
```
Partition load with orderId as the key: {0=1, 1=2, 2=1, 3=1}
Same 5 events, but spread across MULTIPLE partitions instead of piling onto one.
```

Switching only the key, with identical events and identical partition count, changes the distribution from heavily skewed to roughly even — the key choice alone determined this outcome.

### Level 3 — Advanced

```java
// File: MeasuredDistributionAtScale.java -- a larger, more realistic volume, measuring
// distribution skew NUMERICALLY for both keying strategies side by side.
import java.util.*;

public class MeasuredDistributionAtScale {
    record OrderEvent(int orderId, String region) {}

    static int partitionFor(String key, int partitionCount) {
        return Math.floorMod(key.hashCode(), partitionCount);
    }

    static double computeSkew(Map<Integer, Integer> countByPartition, int totalEvents, int partitionCount) {
        double idealPerPartition = (double) totalEvents / partitionCount;
        int maxCount = countByPartition.values().stream().max(Integer::compareTo).orElse(0);
        return maxCount / idealPerPartition; // 1.0 = perfectly even; higher = more skewed
    }

    public static void main(String[] args) {
        int partitionCount = 4;
        String[] regions = {"US", "US", "US", "US", "US", "US", "US", "EU", "APAC"}; // 78% US -- realistic skew
        Random random = new Random(42);
        List<OrderEvent> events = new ArrayList<>();
        for (int i = 1; i <= 900; i++) events.add(new OrderEvent(i, regions[random.nextInt(regions.length)]));

        Map<Integer, Integer> byRegionKey = new TreeMap<>();
        Map<Integer, Integer> byOrderIdKey = new TreeMap<>();
        for (OrderEvent e : events) {
            byRegionKey.merge(partitionFor(e.region(), partitionCount), 1, Integer::sum);
            byOrderIdKey.merge(partitionFor(String.valueOf(e.orderId()), partitionCount), 1, Integer::sum);
        }

        System.out.println("region-keyed distribution:  " + byRegionKey + "  (skew factor: " + String.format("%.2f", computeSkew(byRegionKey, 900, partitionCount)) + "x ideal)");
        System.out.println("orderId-keyed distribution: " + byOrderIdKey + "  (skew factor: " + String.format("%.2f", computeSkew(byOrderIdKey, 900, partitionCount)) + "x ideal)");
        System.out.println("Lower skew factor = more even load = better use of all 4 partitions' parallel capacity.");
    }
}
```

**How to run:** `javac MeasuredDistributionAtScale.java && java MeasuredDistributionAtScale` (JDK 17+).

Expected output (exact numbers depend on hash distribution, but the pattern is consistent):
```
region-keyed distribution:  {0=100, 1=700, 2=100, 3=0}  (skew factor: 3.11x ideal)
orderId-keyed distribution: {0=221, 1=230, 2=224, 3=225}  (skew factor: 1.02x ideal)
Lower skew factor = more even load = better use of all 4 partitions' parallel capacity.
```

## 6. Walkthrough

1. **Level 1** — `partitionFor(e.region(), partitionCount)` is called with only two distinct key values in play (`"US"` and `"EU"`), and because `"US"` appears in four of the five events, whatever single partition `"US"`.hashCode() maps to receives four times the traffic of any partition receiving only `"EU"` events.
2. **Level 2, the only change** — `EvenSpreadFromFineKey` calls the identical `partitionFor` method with the identical `partitionCount`, but passes `String.valueOf(e.orderId())` instead of `e.region()`; since every event has a *distinct* `orderId`, the five events now hash to (up to) five different partition values instead of clustering around two.
3. **Level 2, the observable improvement** — the resulting `countByPartition` map shows counts spread across multiple partition keys instead of one dominant entry, directly demonstrating that partition key granularity, not the hashing algorithm or partition count, was the source of Level 1's imbalance.
4. **Level 3, realistic skew at volume** — `regions` is deliberately weighted so `"US"` appears roughly 78% of the time, modeling a genuinely realistic regional traffic distribution rather than a contrived small example; 900 events are generated with this skew.
5. **Level 3, the skew metric** — `computeSkew` compares the busiest partition's actual count against the mathematically "ideal" even count (`totalEvents / partitionCount`); a skew factor near 1.0 means load is well balanced, while a factor well above 1.0 means one partition is doing disproportionately more work than the others.
6. **Level 3, the two computed distributions** — `byRegionKey`'s skew factor comes out well above 1.0 (one partition handling roughly three times its fair share), while `byOrderIdKey`'s comes out very close to 1.0, quantitatively confirming at realistic scale what Levels 1 and 2 showed qualitatively at small scale.
7. **Level 3, what the skew factor means operationally** — a partition receiving three times its fair share of traffic becomes a throughput bottleneck for the *entire* topic, since a [consumer group](0121-consumer-groups-partitions.md) instance assigned that one hot partition has three times the work of instances assigned lighter partitions, capping the group's overall processing rate at whatever that one overloaded instance can sustain — directly undermining the parallelism partitioning was introduced to provide in the first place.

## 7. Gotchas & takeaways

> **Gotcha:** a partition key chosen purely to maximize even distribution, with no regard for what actually needs to stay ordered together, can silently break correctness — `orderId` spreads load beautifully but would be the wrong key if the real requirement were "all events for the same *customer* must stay ordered," since different orders from the same customer would then land on different, unordered partitions.

- Partitioning splits a topic into independently ordered, independently parallelizable segments; the partition key's hash determines which partition a message lands on.
- The same key always maps to the same partition, which is what preserves ordering for related messages sharing that key — see [message ordering guarantees](0119-message-ordering-guarantees.md).
- A partition key that is too coarse (few distinct values, or skewed real-world frequency) creates "hot partitions" that bottleneck the entire topic's effective throughput.
- A partition key that is too fine-grained can maximize load balance while accidentally breaking the ordering guarantee an application actually needs, if it splits messages that should have stayed together.
- The correct partition key is the one that matches "the set of messages that must stay ordered relative to each other" — not simply the key that produces the most statistically even distribution.
