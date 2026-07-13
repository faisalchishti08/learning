---
card: microservices
gi: 206
slug: weighted-load-balancing
title: "Weighted load balancing"
---

## 1. What it is

Weighted load balancing assigns each instance a numeric weight reflecting its relative capacity, and routes traffic proportionally to those weights instead of splitting it evenly — an instance with weight 2 receives roughly twice the traffic of an instance with weight 1, letting a fleet of instances with genuinely different capacities (different hardware, different instance sizes, a canary release meant to receive only a small fraction of traffic) share load fairly relative to what each can actually handle.

## 2. Why & when

Plain [round-robin or random balancing](0205-load-balancing-algorithms-round-robin-random-least-connectio.md) assumes every instance can handle an equal share of traffic, which breaks down the moment instances genuinely differ in capacity — a larger, more powerful instance sitting alongside smaller ones would be underutilized by even splitting, while the smaller instances would be overloaded relative to their actual capacity. Weighted balancing fixes this by making capacity an explicit input to the routing decision, so traffic distribution matches each instance's real ability to handle it, rather than assuming uniformity that doesn't exist.

Use weighted balancing whenever instances genuinely differ in capacity — mixed instance sizes during a gradual infrastructure migration, deliberately smaller canary instances that should receive only a fraction of traffic for controlled rollout validation, or heterogeneous hardware in an on-premises deployment. For a fleet of genuinely identical instances, plain round-robin or random remains simpler and equally effective.

## 3. Core concept

Each instance carries a weight value; the balancing algorithm selects instances with probability (or frequency, for a deterministic weighted round-robin) proportional to their weight relative to the total weight of all instances, so higher-weighted instances receive proportionally more traffic over time.

```java
record WeightedInstance(String id, int weight) {}
List<WeightedInstance> instances = List.of(
    new WeightedInstance("large-a", 3),   // handles 3x the traffic of...
    new WeightedInstance("small-b", 1));   // ...this smaller instance

// selection probability is PROPORTIONAL to weight
int totalWeight = instances.stream().mapToInt(WeightedInstance::weight).sum(); // 4
int r = random.nextInt(totalWeight); // 0..3
// r in [0,3) -> large-a (75% chance); r == 3 -> small-b (25% chance)
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instance large-a has weight 3 and receives roughly 75% of traffic; instance small-b has weight 1 and receives roughly 25% of traffic, proportional to their relative weights" >
  <rect x="30" y="60" width="280" height="40" rx="4" fill="#6db33f" opacity="0.4"/>
  <text x="170" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">large-a (weight 3) -- ~75% of traffic</text>

  <rect x="330" y="60" width="95" height="40" rx="4" fill="#79c0ff" opacity="0.4"/>
  <text x="377" y="85" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">small-b (weight 1) -- ~25%</text>
</svg>

Traffic share is proportional to weight, not split evenly regardless of capacity.

## 5. Runnable example

Scenario: two instances with genuinely different capacity that starts with plain round-robin splitting traffic evenly (mismatching actual capacity), adds weighted random selection to route traffic proportionally to weight, and finally implements a deterministic weighted round-robin that achieves the exact target ratio precisely, useful when exact proportional distribution matters more than random approximation.

### Level 1 — Basic

```java
// File: EvenSplitMismatchesCapacity.java -- plain round-robin splits traffic
// EVENLY, even though the two instances have GENUINELY different capacity.
import java.util.*;

public class EvenSplitMismatchesCapacity {
    record Instance(String id, int actualCapacity) {}

    public static void main(String[] args) {
        List<Instance> instances = List.of(new Instance("large-a", 300), new Instance("small-b", 100)); // large-a can handle 3x
        int index = 0;

        Map<String, Integer> received = new TreeMap<>();
        for (int i = 0; i < 100; i++) {
            String chosen = instances.get(index++ % instances.size()).id(); // PLAIN round-robin, EVEN split
            received.merge(chosen, 1, Integer::sum);
        }

        System.out.println("Requests received: " + received);
        System.out.println("EVEN split (50/50), but large-a can handle 3x small-b's capacity -- small-b is being OVERLOADED relative to what it can actually handle.");
    }
}
```

**How to run:** `javac EvenSplitMismatchesCapacity.java && java EvenSplitMismatchesCapacity` (JDK 17+).

### Level 2 — Intermediate

```java
// File: WeightedRandomSelection.java -- traffic distributed PROPORTIONALLY to
// each instance's WEIGHT -- large-a correctly receives roughly 3x small-b's share.
import java.util.*;

public class WeightedRandomSelection {
    record WeightedInstance(String id, int weight) {}

    static String chooseWeighted(List<WeightedInstance> instances, Random random) {
        int totalWeight = instances.stream().mapToInt(WeightedInstance::weight).sum();
        int r = random.nextInt(totalWeight);
        int cumulative = 0;
        for (WeightedInstance instance : instances) {
            cumulative += instance.weight();
            if (r < cumulative) return instance.id();
        }
        return instances.get(instances.size() - 1).id();
    }

    public static void main(String[] args) {
        List<WeightedInstance> instances = List.of(new WeightedInstance("large-a", 3), new WeightedInstance("small-b", 1));
        Random random = new Random(42);

        Map<String, Integer> received = new TreeMap<>();
        for (int i = 0; i < 1000; i++) {
            String chosen = chooseWeighted(instances, random);
            received.merge(chosen, 1, Integer::sum);
        }

        System.out.println("Requests received over 1000 calls: " + received);
        System.out.println("large-a (weight 3) received roughly 3x small-b's (weight 1) share -- traffic now matches ACTUAL relative capacity.");
    }
}
```

**How to run:** `javac WeightedRandomSelection.java && java WeightedRandomSelection` (JDK 17+).

Expected output (exact numbers depend on the fixed random seed, but the ratio is close to 3:1):
```
Requests received over 1000 calls: {large-a=767, small-b=233}
large-a (weight 3) received roughly 3x small-b's (weight 1) share -- traffic now matches ACTUAL relative capacity.
```

### Level 3 — Advanced

```java
// File: DeterministicWeightedRoundRobin.java -- achieves the EXACT target
// ratio PRECISELY, every cycle, instead of a random approximation that
// converges only over many calls.
import java.util.*;

public class DeterministicWeightedRoundRobin {
    record WeightedInstance(String id, int weight) {}

    // classic "smooth weighted round-robin" -- each instance accumulates weight each round;
    // the one with the HIGHEST current total is picked, then reduced by the TOTAL weight
    static class SmoothWeightedRoundRobin {
        List<WeightedInstance> instances;
        Map<String, Integer> currentWeights = new HashMap<>();
        int totalWeight;
        SmoothWeightedRoundRobin(List<WeightedInstance> instances) {
            this.instances = instances;
            for (WeightedInstance i : instances) currentWeights.put(i.id(), 0);
            totalWeight = instances.stream().mapToInt(WeightedInstance::weight).sum();
        }
        String choose() {
            WeightedInstance best = null;
            for (WeightedInstance instance : instances) {
                currentWeights.merge(instance.id(), instance.weight(), Integer::sum); // accumulate
                if (best == null || currentWeights.get(instance.id()) > currentWeights.get(best.id())) best = instance;
            }
            currentWeights.merge(best.id(), -totalWeight, Integer::sum); // reduce the winner
            return best.id();
        }
    }

    public static void main(String[] args) {
        List<WeightedInstance> instances = List.of(new WeightedInstance("large-a", 3), new WeightedInstance("small-b", 1));
        SmoothWeightedRoundRobin balancer = new SmoothWeightedRoundRobin(instances);

        List<String> sequence = new ArrayList<>();
        for (int i = 0; i < 8; i++) sequence.add(balancer.choose());

        System.out.println("Deterministic sequence over 8 calls: " + sequence);
        Map<String, Long> counts = new TreeMap<>();
        for (String s : sequence) counts.merge(s, 1L, Long::sum);
        System.out.println("Exact counts: " + counts + " -- PRECISELY the 3:1 ratio, every single cycle, no randomness or approximation needed.");
    }
}
```

**How to run:** `javac DeterministicWeightedRoundRobin.java && java DeterministicWeightedRoundRobin` (JDK 17+).

Expected output:
```
Deterministic sequence over 8 calls: [large-a, large-a, small-b, large-a, large-a, large-a, small-b, large-a]
Exact counts: {large-a=6, small-b=2} -- PRECISELY the 3:1 ratio, every single cycle, no randomness or approximation needed.
```

## 6. Walkthrough

1. **Level 1** — `index++ % instances.size()` alternates strictly evenly between `large-a` and `small-b`, producing an exact 50/50 split (50 requests each out of 100) despite `large-a`'s `actualCapacity` (300) being three times `small-b`'s (100) — a genuine mismatch between traffic share and real capacity.
2. **Level 2, weighted probability computed from relative weight** — `chooseWeighted` computes `totalWeight` (4, from weights 3 and 1) and draws a random integer in `[0, totalWeight)`; because `large-a`'s weight spans 3 of those 4 possible values (`r < 3`) and `small-b`'s spans only 1 (`r == 3`), `large-a` has a 75% chance of selection on any given call, `small-b` a 25% chance.
3. **Level 2, the statistical result confirming the ratio** — across 1000 calls, the observed counts (roughly 767 and 233) closely approximate the intended 3:1 (75%/25%) ratio, demonstrating that weighted random selection converges to the configured proportions over a sufficiently large number of calls.
4. **Level 3, why a deterministic algorithm might be preferred** — Level 2's approach only approximates the target ratio statistically; over a small number of calls, the actual distribution can deviate meaningfully from 3:1 purely due to randomness, which may be undesirable when precise, predictable distribution matters even at small scale.
5. **Level 3, the smooth weighted round-robin mechanism** — `SmoothWeightedRoundRobin.choose` increments every instance's `currentWeights` entry by its own configured weight on every call (`large-a` gains 3, `small-b` gains 1 each round), then selects whichever instance now has the highest accumulated value, and finally reduces that winner's accumulated value by `totalWeight` (4) — a classic algorithm that guarantees the exact target ratio emerges deterministically.
6. **Level 3, tracing the accumulation** — starting from `{large-a: 0, small-b: 0}`: round 1 becomes `{3, 1}`, `large-a` wins, reduced to `{-1, 1}`; round 2 becomes `{2, 2}`, tied, `large-a` wins first (iteration order), reduced to `{-2, 2}`; round 3 becomes `{1, 3}`, `small-b` wins, reduced to `{1, -1}` — this pattern continues, naturally spacing out `small-b`'s selections rather than clustering them, while still achieving the exact 3:1 ratio.
7. **Level 3, the precise, guaranteed outcome** — across exactly 8 calls (two full weight-total cycles of 4), the counts land at exactly `{large-a=6, small-b=2}`, precisely the 3:1 ratio with zero statistical variance — this deterministic guarantee is the concrete advantage smooth weighted round-robin offers over Level 2's random approximation, at the cost of the more involved bookkeeping (`currentWeights` state) the algorithm requires.

## 7. Gotchas & takeaways

> **Gotcha:** weights need periodic re-evaluation as actual instance capacity changes — a weight configured once at deployment time based on an instance's provisioned size doesn't automatically adjust if that instance's real-world performance degrades (a noisy neighbor on shared infrastructure, a hardware issue) or improves; combining weighted balancing with ongoing capacity or latency monitoring, rather than treating weight as a permanently fixed configuration value, keeps the distribution genuinely matched to real capacity over time.

- Weighted load balancing routes traffic proportionally to each instance's assigned weight, letting instances with genuinely different capacities share load fairly relative to what each can actually handle.
- Plain round-robin or random balancing assumes uniform capacity and mismatches actual load distribution when that assumption doesn't hold.
- Weighted random selection approximates the target ratio statistically, converging accurately only over a sufficiently large number of calls.
- A deterministic algorithm like smooth weighted round-robin achieves the exact target ratio precisely and predictably, at the cost of more involved state-tracking than a simple random draw.
- Weights should be periodically re-evaluated against actual, current instance capacity or performance, rather than treated as a permanently fixed value set once at deployment time.
