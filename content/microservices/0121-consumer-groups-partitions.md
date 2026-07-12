---
card: microservices
gi: 121
slug: consumer-groups-partitions
title: "Consumer groups & partitions"
---

## 1. What it is

A consumer group is a named set of consumer instances that collectively act as one logical subscriber to a topic, splitting its [partitions](0119-message-ordering-guarantees.md) between the group's members so each partition is read by exactly one member of that group at a time — combining [publish/subscribe](0114-publish-subscribe-topic-messaging.md)'s fan-out to independent subscriber groups with [competing consumers](0120-competing-consumers-pattern.md)'s scaling of throughput within a single subscriber.

## 2. Why & when

Plain pub/sub gives every subscriber its own full copy of every message, which is exactly wrong for scaling a single logical consumer's throughput — running four instances of the "email service" as independent pub/sub subscribers would mean every customer gets four confirmation emails, not one email processed four times as fast. Consumer groups fix this by having the broker treat all instances that report the same group name as one logical subscriber, splitting the topic's partitions among them so the group as a whole still sees every message exactly once, while individual instances within the group each handle only a slice of the traffic.

Reach for consumer groups whenever a pub/sub-style event needs to be seen by several *different* kinds of downstream consumers (each its own group) while also letting any *individual* kind of consumer scale out horizontally (multiple instances sharing one group name). This is the standard scaling model in partition-based brokers like Kafka.

## 3. Core concept

A topic has a fixed number of partitions; a consumer group's instances are assigned a disjoint subset of those partitions (rebalanced automatically as instances join or leave), so within one group, each partition is read by exactly one instance, but the same topic can have any number of independent groups, each getting its own full view of every partition.

```java
// group "email-service" and group "analytics-service" EACH see every message once,
// independent of each other -- that's the pub/sub part
topic.subscribe(group = "email-service", instanceId = "email-1");
topic.subscribe(group = "analytics-service", instanceId = "analytics-1");

// but WITHIN "email-service", adding a second instance SPLITS the partitions,
// not duplicates them -- that's the competing-consumers-within-a-group part
topic.subscribe(group = "email-service", instanceId = "email-2");
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A topic with four partitions; group email-service splits the four partitions across two instances; group analytics-service, with one instance, reads all four partitions itself; both groups independently see every message">
  <rect x="20" y="90" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Topic: order-events</text>
  <text x="110" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">P0  P1  P2  P3</text>

  <rect x="260" y="20" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">group: email-service</text>
  <text x="335" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">email-1: P0,P1</text>
  <text x="335" y="70" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">email-2: P2,P3</text>

  <rect x="450" y="20" width="170" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">group: analytics-service</text>
  <text x="535" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">analytics-1: P0,P1,P2,P3</text>

  <line x1="200" y1="110" x2="258" y2="50" stroke="#8b949e" marker-end="url(#arr9)"/>
  <line x1="200" y1="120" x2="448" y2="50" stroke="#8b949e" marker-end="url(#arr9)"/>

  <text x="335" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">within a group: partitions SPLIT (scale out)</text>
  <text x="335" y="215" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">across groups: every group sees ALL partitions (fan out)</text>

  <defs>
    <marker id="arr9" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Partitions split within a group for scale; the same topic fans out fully to every independent group.

## 5. Runnable example

Scenario: a four-partition `order-events` topic that starts with one group having one instance (a full-view baseline), grows that group to two competing instances that split the four partitions between them, and finally adds a second, entirely independent group to show both groups get their own complete view regardless of how the first group's instances are split.

### Level 1 — Basic

```java
// File: SingleInstanceGroup.java -- one group, one instance: sees ALL partitions, baseline.
import java.util.*;

public class SingleInstanceGroup {
    public static void main(String[] args) {
        List<Integer> partitions = List.of(0, 1, 2, 3);
        Map<Integer, List<String>> events = Map.of(
            0, List.of("OrderCreated:1"), 1, List.of("OrderCreated:2"),
            2, List.of("OrderCreated:3"), 3, List.of("OrderCreated:4"));

        String instanceId = "email-1";
        System.out.println(instanceId + " assigned partitions: " + partitions); // ALL of them, only instance in its group
        for (int p : partitions) {
            for (String e : events.get(p)) System.out.println("  " + instanceId + " processing (partition " + p + "): " + e);
        }
    }
}
```

**How to run:** `javac SingleInstanceGroup.java && java SingleInstanceGroup` (JDK 17+).

With one instance in the group, it is assigned every partition and processes every event — indistinguishable so far from a plain topic subscriber.

### Level 2 — Intermediate

```java
// File: SplitPartitionsGroup.java -- two instances in the SAME group split the four partitions.
import java.util.*;

public class SplitPartitionsGroup {
    static Map<String, List<Integer>> assignPartitions(List<Integer> partitions, List<String> instanceIds) {
        Map<String, List<Integer>> assignment = new LinkedHashMap<>();
        for (String id : instanceIds) assignment.put(id, new ArrayList<>());
        for (int i = 0; i < partitions.size(); i++) {
            String owner = instanceIds.get(i % instanceIds.size()); // round-robin partition assignment
            assignment.get(owner).add(partitions.get(i));
        }
        return assignment;
    }

    public static void main(String[] args) {
        List<Integer> partitions = List.of(0, 1, 2, 3);
        Map<Integer, String> events = Map.of(0, "OrderCreated:1", 1, "OrderCreated:2", 2, "OrderCreated:3", 3, "OrderCreated:4");

        List<String> emailGroupInstances = List.of("email-1", "email-2"); // TWO instances, same group "email-service"
        Map<String, List<Integer>> assignment = assignPartitions(partitions, emailGroupInstances);

        for (var entry : assignment.entrySet()) {
            System.out.println(entry.getKey() + " assigned partitions: " + entry.getValue());
            for (int p : entry.getValue()) System.out.println("  " + entry.getKey() + " processing (partition " + p + "): " + events.get(p));
        }
    }
}
```

**How to run:** `javac SplitPartitionsGroup.java && java SplitPartitionsGroup` (JDK 17+).

Expected output:
```
email-1 assigned partitions: [0, 2]
email-2 assigned partitions: [1, 3]
  email-1 processing (partition 0): OrderCreated:1
  email-1 processing (partition 2): OrderCreated:3
  email-2 processing (partition 1): OrderCreated:2
  email-2 processing (partition 3): OrderCreated:4
```

Each of the four events is processed exactly once across the whole group, but by only one of the two instances — the group's *combined* throughput doubled without any single instance seeing duplicate work.

### Level 3 — Advanced

```java
// File: TwoIndependentGroups.java -- a second, unrelated group gets its OWN full view,
// independent of how the first group split its partitions among instances.
import java.util.*;

public class TwoIndependentGroups {
    static Map<String, List<Integer>> assignPartitions(List<Integer> partitions, List<String> instanceIds) {
        Map<String, List<Integer>> assignment = new LinkedHashMap<>();
        for (String id : instanceIds) assignment.put(id, new ArrayList<>());
        for (int i = 0; i < partitions.size(); i++) {
            assignment.get(instanceIds.get(i % instanceIds.size())).add(partitions.get(i));
        }
        return assignment;
    }

    public static void main(String[] args) {
        List<Integer> partitions = List.of(0, 1, 2, 3);
        Map<Integer, String> events = Map.of(0, "OrderCreated:1", 1, "OrderCreated:2", 2, "OrderCreated:3", 3, "OrderCreated:4");

        Map<String, List<String>> groupInstances = Map.of(
            "email-service", List.of("email-1", "email-2"),       // 2 instances -- work is SPLIT
            "analytics-service", List.of("analytics-1"));           // 1 instance -- sees EVERYTHING

        for (var group : groupInstances.entrySet()) {
            System.out.println("=== group: " + group.getKey() + " ===");
            Map<String, List<Integer>> assignment = assignPartitions(partitions, group.getValue());
            int totalSeenByGroup = 0;
            for (var entry : assignment.entrySet()) {
                System.out.println("  " + entry.getKey() + " assigned partitions: " + entry.getValue());
                totalSeenByGroup += entry.getValue().size();
            }
            System.out.println("  total events seen by group '" + group.getKey() + "': " + totalSeenByGroup + " (all 4, regardless of instance count)");
        }
    }
}
```

**How to run:** `javac TwoIndependentGroups.java && java TwoIndependentGroups` (JDK 17+).

Expected output:
```
=== group: email-service ===
  email-1 assigned partitions: [0, 2]
  email-2 assigned partitions: [1, 3]
  total events seen by group 'email-service': 4 (all 4, regardless of instance count)
=== group: analytics-service ===
  analytics-1 assigned partitions: [0, 1, 2, 3]
  total events seen by group 'analytics-service': 4 (all 4, regardless of instance count)
```

## 6. Walkthrough

1. **Level 1** — with only `email-1` in its group, `assignPartitions`-equivalent logic trivially gives it every partition; it processes all four events, establishing what "one group, full view" looks like before splitting is introduced.
2. **Level 2, computing the split** — `assignPartitions` round-robins the four partitions across the two instance ids in `emailGroupInstances`, giving `email-1` partitions `[0, 2]` and `email-2` partitions `[1, 3]` — a deterministic, disjoint split with no overlap.
3. **Level 2, each instance processes only its share** — the nested loop only prints events for the partitions each instance was assigned, so `email-1` never touches partition 1's or 3's events and vice versa — exactly the "split, don't duplicate" behavior that distinguishes a consumer group from plain pub/sub fan-out.
4. **Level 2, the group's combined coverage** — summing what `email-1` and `email-2` each processed accounts for all four original events exactly once, meaning the *group* still behaves like a single logical subscriber to an outside observer, even though the work was split across two processes.
5. **Level 3, two groups, one topic** — `groupInstances` defines `email-service` with two instances and `analytics-service` with a single instance, both reading from the identical four-partition `order-events` topic.
6. **Level 3, independent assignment per group** — `assignPartitions` is called separately for each group's instance list, so `email-service`'s two instances split the four partitions between them while `analytics-service`'s single instance is assigned all four — group membership, not global topic state, determines the split.
7. **Level 3, the printed totals** — both groups' `totalSeenByGroup` end at 4, proving that `analytics-service`, despite having only one instance versus `email-service`'s two, still receives every single event; the number of instances *within* a group only affects how that group's own workload is divided, never whether another, independent group receives the full stream.

## 7. Gotchas & takeaways

> **Gotcha:** adding more consumer instances to a group than the topic has partitions does nothing useful — a partition can only be assigned to one instance at a time within a group, so extra instances beyond the partition count simply sit idle; partition count sets the group's maximum useful parallelism, and increasing it later (in most brokers) requires care because it changes how existing keys map to partitions.

- A consumer group is a named set of instances that collectively behave as one logical subscriber, with the topic's partitions split, not duplicated, among the group's current members.
- Different groups reading the same topic are fully independent — each group gets its own complete view of every message, regardless of how many instances any other group has.
- This combines pub/sub's fan-out (across independent groups) with competing consumers' throughput scaling (within a single group's instances), giving both properties from one mechanism.
- The number of partitions on a topic caps a single group's maximum useful parallelism — instances beyond that count go idle.
- Rebalancing (reassigning partitions when instances join or leave a group) is handled by the broker automatically in real systems like Kafka, but briefly pauses processing for the affected partitions while it happens — a detail worth knowing before assuming instance scaling is entirely free.
