---
card: system-design
gi: 37
slug: round-robin-weighted-round-robin
title: Round-robin & weighted round-robin
---

## 1. What it is

**Round-robin** is a load-balancing algorithm that cycles through a list of backend servers in fixed order, sending each new request to the next server in the sequence, wrapping back to the start after reaching the end. **Weighted round-robin** is the same idea, but each server is assigned a **weight**, so a more powerful server receives proportionally more requests than a weaker one, instead of every server receiving exactly the same share.

## 2. Why & when

Round-robin is often a load balancer's default algorithm because it is simple and spreads load evenly with no bookkeeping about server performance. Weighted round-robin becomes necessary as soon as your backend servers are not identical — for example, some are newer, more powerful machines than others — and you want the stronger machines to handle proportionally more traffic instead of being artificially capped at the same rate as the weaker ones.

## 3. Core concept

**Plain round-robin, step by step:** given servers `[A, B, C]`, the first request goes to A, the second to B, the third to C, the fourth wraps back to A, and so on. Every server receives an equal share of requests over time, regardless of its actual capacity.

**Weighted round-robin, step by step:** each server gets a weight representing its relative capacity — say A=3, B=2, C=1 (A can handle 3x what C can). The algorithm distributes requests so that, over any full cycle, A receives 3 requests for every 1 that C receives, and B receives 2. One common way to implement this smoothly (rather than sending 3 requests to A in a row, then all of B's, then C's) is to interleave them, so traffic still feels evenly spread out over time, not bursty.

**When plain round-robin is the wrong choice:** if servers have different capacities, but you still send them equal shares of traffic, the weaker server becomes overloaded (its queue backs up, and its latency degrades) while the stronger one sits underused — plain round-robin implicitly assumes all servers are equally capable, and that assumption is often false in mixed-hardware or gradually-scaled-up environments.

## 4. Diagram

```
 PLAIN ROUND-ROBIN (A, B, C equal capacity)      WEIGHTED ROUND-ROBIN (A=3, B=2, C=1)
 req1 -> A                                        req1 -> A
 req2 -> B                                        req2 -> A
 req3 -> C                                        req3 -> B
 req4 -> A  (cycle repeats)                       req4 -> A
 req5 -> B                                        req5 -> B
 req6 -> C                                        req6 -> C  (cycle repeats, 3:2:1 ratio)
```
*Caption: plain round-robin gives every server an equal share; weighted round-robin gives shares proportional to each server's declared capacity.*

## 5. Runnable example

### Artifact: a Java implementation of both plain and weighted round-robin routing

```java
import java.util.*;

public class RoundRobinSim {

    static class PlainRoundRobin {
        List<String> servers;
        int nextIndex = 0;
        PlainRoundRobin(List<String> servers) { this.servers = servers; }

        String next() {
            String chosen = servers.get(nextIndex);
            nextIndex = (nextIndex + 1) % servers.size();
            return chosen;
        }
    }

    static class WeightedRoundRobin {
        List<String> expandedList = new ArrayList<>();
        int nextIndex = 0;

        WeightedRoundRobin(Map<String, Integer> weights) {
            // Build an interleaved list so requests spread out evenly, not in bursts.
            int maxWeight = Collections.max(weights.values());
            for (int round = 0; round < maxWeight; round++) {
                for (Map.Entry<String, Integer> e : weights.entrySet()) {
                    if (round < e.getValue()) {
                        expandedList.add(e.getKey());
                    }
                }
            }
        }

        String next() {
            String chosen = expandedList.get(nextIndex);
            nextIndex = (nextIndex + 1) % expandedList.size();
            return chosen;
        }
    }

    public static void main(String[] args) {
        PlainRoundRobin plain = new PlainRoundRobin(List.of("A", "B", "C"));
        System.out.print("Plain round-robin (6 requests): ");
        for (int i = 0; i < 6; i++) System.out.print(plain.next() + " ");
        System.out.println();

        WeightedRoundRobin weighted = new WeightedRoundRobin(
            new LinkedHashMap<>(Map.of("A", 3, "B", 2, "C", 1))
        );
        System.out.print("Weighted round-robin A=3,B=2,C=1 (6 requests): ");
        for (int i = 0; i < 6; i++) System.out.print(weighted.next() + " ");
        System.out.println();
    }
}
```

**How to run:** save as `RoundRobinSim.java`, run `java RoundRobinSim.java` (JDK 17+).

## 6. Walkthrough

1. `PlainRoundRobin.next()` returns the server at `nextIndex`, then advances the index, wrapping around with `%` once it passes the end of the list — a simple, equal-share cycle.
2. `WeightedRoundRobin`'s constructor builds an `expandedList` by looping `maxWeight` rounds and, in each round, adding every server whose weight is still greater than the current round number — this naturally interleaves higher-weight servers more often, rather than clustering all of one server's requests together.
3. `WeightedRoundRobin.next()` then cycles through that pre-built expanded list exactly like plain round-robin does over its simple list.
4. `main` runs both algorithms for 6 requests each and prints the resulting sequence.
5. Output (note: `Map.of` does not guarantee iteration order, so the weighted example uses a `LinkedHashMap` wrapper to keep A, B, C in a stable order for a predictable result):
```
Plain round-robin (6 requests): A B C A B C
Weighted round-robin A=3,B=2,C=1 (6 requests): A B C A B A
```
6. Counting the weighted output: A appears 3 times, B appears 2 times, C appears 1 time — exactly matching the 3:2:1 weight ratio, and notice they are interleaved (not "AAA BB C") so traffic still arrives at each server in a spread-out, non-bursty pattern.

## 7. Gotchas & takeaways

> **Gotcha:** using plain round-robin across servers with meaningfully different capacities. The weaker server receives the same request share as the strongest one, causing it to become a bottleneck under load even while stronger servers have spare capacity.

- Plain round-robin: simple, equal shares, correct only when all servers have equal capacity.
- Weighted round-robin: proportional shares based on declared server capacity, correct for mixed-capacity server pools.
- Interleave weighted assignments rather than grouping them, so traffic to each server stays evenly spread over time.
