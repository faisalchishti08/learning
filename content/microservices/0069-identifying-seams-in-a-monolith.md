---
card: microservices
gi: 69
slug: identifying-seams-in-a-monolith
title: "Identifying seams in a monolith"
---

## 1. What it is

A "seam," a term popularized in the context of legacy code, is a place in existing code where you can alter behavior without editing the code at that exact spot — a natural joint. In the context of monolith decomposition, identifying seams means finding the places in the codebase where coupling is already lowest: modules with few incoming calls from the rest of the system, classes that don't share a database transaction with anything else, or packages with a clean, narrow public interface. These low-coupling spots are where extraction into a separate service is cheapest and safest.

## 2. Why & when

Not every part of a monolith is equally easy to extract. Some code is deeply entangled — shared mutable state, direct method calls in and out from a dozen other modules, transactions spanning multiple concerns — while other code is naturally more isolated, perhaps already called through a narrow interface, or already only reachable from one place. Attempting extraction on the most entangled code first, before the team has practice with the mechanics of decomposition, tends to produce the most painful, highest-risk migrations. Finding seams first turns "where should we start decomposing?" from a guess into something you can actually measure: count incoming dependencies, look at deployment history, check for shared transactions.

Do this analysis before starting [incremental monolith decomposition](0066-decomposing-a-monolith-incrementally.md) — ideally alongside [event storming](0063-event-storming-for-boundary-discovery.md) or bounded context analysis, since a good extraction candidate needs to be both a coherent bounded context *and* a low-coupling seam. The two lenses often agree, but not always, and when they disagree, that disagreement itself is useful information.

## 3. Core concept

Coupling can often be approximated mechanically, before any manual analysis: count how many other modules call into a given module, and how many modules that module calls out to. Low counts on both sides mark a strong seam candidate.

```
Module        incoming calls     outgoing calls     verdict
------        --------------     --------------     -------
Notifications        2                  0            strong seam (few dependents, isolated)
Shipping              4                  3            moderate seam
Orders                9                  6            weak seam (deeply entangled, extract LAST)
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A dependency graph of a monolith shows Notifications with few connections as a strong seam, and Orders densely connected to everything as a weak seam to extract last">
  <rect x="270" y="90" width="110" height="45" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="325" y="117" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Orders</text>

  <rect x="60" y="20" width="110" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="115" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Customers</text>
  <rect x="470" y="20" width="110" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="525" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Inventory</text>
  <rect x="60" y="170" width="110" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="115" y="195" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Billing</text>
  <rect x="470" y="170" width="110" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="525" y="195" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Shipping</text>

  <line x1="170" y1="45" x2="270" y2="100" stroke="#8b949e"/>
  <line x1="470" y1="45" x2="380" y2="100" stroke="#8b949e"/>
  <line x1="170" y1="190" x2="270" y2="125" stroke="#8b949e"/>
  <line x1="470" y1="190" x2="380" y2="125" stroke="#8b949e"/>

  <rect x="270" y="150" width="0" height="0"/>
  <circle cx="325" cy="60" r="0"/>
  <rect x="20" y="90" width="110" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Notifications</text>
  <line x1="130" y1="110" x2="270" y2="110" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="140" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">1 incoming edge -- strong seam</text>
  <text x="325" y="150" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">4 edges -- weak seam, extract last</text>
</svg>

Fewer edges touching a module means a cheaper, safer extraction; Orders, densely connected, is extracted last.

## 5. Runnable example

Scenario: model a monolith's modules and their call dependencies, then write code that scores each module's "seam strength" by counting incoming and outgoing edges, first with a simple count, then refined to also weigh whether calls cross a shared database transaction (a stronger form of coupling than a plain method call).

### Level 1 — Basic

```java
// File: DependencyGraph.java -- represent the monolith's module call
// graph as a simple adjacency list: caller -> list of callees.
import java.util.*;

public class DependencyGraph {
    public static void main(String[] args) {
        Map<String, List<String>> callsOutTo = new LinkedHashMap<>();
        callsOutTo.put("Orders", List.of("Customers", "Inventory", "Billing", "Shipping"));
        callsOutTo.put("Billing", List.of("Customers"));
        callsOutTo.put("Shipping", List.of("Inventory"));
        callsOutTo.put("Notifications", List.of()); // calls out to nothing

        for (var entry : callsOutTo.entrySet()) {
            System.out.println(entry.getKey() + " calls out to: " + entry.getValue());
        }
    }
}
```

**How to run:** `javac DependencyGraph.java && java DependencyGraph` (JDK 17+).

Expected output:
```
Orders calls out to: [Customers, Inventory, Billing, Shipping]
Billing calls out to: [Customers]
Shipping calls out to: [Inventory]
Notifications calls out to: []
```

This is the raw call graph — the starting data any seam analysis needs before it can score anything.

### Level 2 — Intermediate

```java
// File: SeamScore.java -- SAME call graph, now scored: count incoming
// AND outgoing edges per module, and rank modules from strongest seam
// (fewest total edges) to weakest (most).
import java.util.*;

public class SeamScore {
    public static void main(String[] args) {
        Map<String, List<String>> callsOutTo = new LinkedHashMap<>();
        callsOutTo.put("Orders", List.of("Customers", "Inventory", "Billing", "Shipping"));
        callsOutTo.put("Billing", List.of("Customers"));
        callsOutTo.put("Shipping", List.of("Inventory"));
        callsOutTo.put("Notifications", List.of());

        Set<String> allModules = new LinkedHashSet<>(callsOutTo.keySet());
        allModules.addAll(List.of("Customers", "Inventory"));

        Map<String, Integer> outgoing = new HashMap<>();
        Map<String, Integer> incoming = new HashMap<>();
        for (String m : allModules) { outgoing.put(m, 0); incoming.put(m, 0); }

        for (var entry : callsOutTo.entrySet()) {
            outgoing.put(entry.getKey(), entry.getValue().size());
            for (String callee : entry.getValue()) {
                incoming.merge(callee, 1, Integer::sum);
            }
        }

        List<String> ranked = new ArrayList<>(allModules);
        ranked.sort(Comparator.comparingInt(m -> outgoing.get(m) + incoming.get(m)));

        for (String m : ranked) {
            int total = outgoing.get(m) + incoming.get(m);
            System.out.println(m + ": incoming=" + incoming.get(m) + " outgoing=" + outgoing.get(m) + " total=" + total);
        }
    }
}
```

**How to run:** `javac SeamScore.java && java SeamScore` (JDK 17+).

Expected output:
```
Notifications: incoming=0 outgoing=0 total=0
Billing: incoming=1 outgoing=1 total=2
Shipping: incoming=1 outgoing=1 total=2
Customers: incoming=2 outgoing=0 total=2
Inventory: incoming=2 outgoing=0 total=2
Orders: incoming=0 outgoing=4 total=4
```

`Notifications` ranks first — zero edges in either direction, the strongest seam candidate. `Orders`, with four outgoing calls, ranks last — the most entangled, extract-last candidate.

### Level 3 — Advanced

```java
// File: SeamScoreWithTransactions.java -- refine the score: a call that
// shares a DATABASE TRANSACTION with the caller is a much stronger form
// of coupling than a plain method call, and should weigh more heavily
// in the score -- a seam that LOOKS clean at the method-call level can
// still be a trap if it shares a transaction.
import java.util.*;

public class SeamScoreWithTransactions {
    record Call(String from, String to, boolean sharesTransaction) {}

    public static void main(String[] args) {
        List<Call> calls = List.of(
            new Call("Orders", "Customers", false),
            new Call("Orders", "Inventory", true),   // SAME transaction -- strong coupling
            new Call("Orders", "Billing", false),
            new Call("Orders", "Shipping", false),
            new Call("Billing", "Customers", false),
            new Call("Shipping", "Inventory", true)  // SAME transaction -- strong coupling
        );

        Set<String> allModules = new LinkedHashSet<>(List.of("Orders", "Billing", "Shipping", "Customers", "Inventory", "Notifications"));
        Map<String, Integer> weightedScore = new HashMap<>();
        for (String m : allModules) weightedScore.put(m, 0);

        for (Call c : calls) {
            int weight = c.sharesTransaction() ? 3 : 1; // shared transaction counts 3x a plain call
            weightedScore.merge(c.from(), weight, Integer::sum);
            weightedScore.merge(c.to(), weight, Integer::sum);
        }

        List<String> ranked = new ArrayList<>(allModules);
        ranked.sort(Comparator.comparingInt(weightedScore::get));

        for (String m : ranked) {
            System.out.println(m + ": weighted coupling score=" + weightedScore.get(m));
        }
    }
}
```

**How to run:** `javac SeamScoreWithTransactions.java && java SeamScoreWithTransactions` (JDK 17+).

Expected output:
```
Notifications: weighted coupling score=0
Billing: weighted coupling score=2
Customers: weighted coupling score=2
Shipping: weighted coupling score=4
Orders: weighted coupling score=6
Inventory: weighted coupling score=6
```

`Inventory` jumps up the risk ranking compared to a plain edge-count: it looked no worse than `Customers` in Level 2 (2 edges each), but two of its calls share a database transaction, which the weighted score now reflects — `Inventory` is a riskier extraction candidate than a naive count would have suggested.

## 6. Walkthrough

1. **Level 1** — `DependencyGraph.main` builds a `Map<String, List<String>>` recording, for each module, which other modules it calls into. Printing it shows `Orders` calling four other modules, while `Notifications` calls nothing — this is just the raw data collection step, typically done by reading code or, in a real system, by static analysis tooling.
2. **Level 2 — scoring** — `SeamScore.main` walks the same graph twice: once to fill `outgoing` (the size of each module's own call list), and once more, for every call, to increment `incoming` on the *callee*. Sorting all modules by `outgoing + incoming` produces the ranked list. `Notifications` scores `0` (nothing calls it, it calls nothing) and lands at the top — the strongest seam. `Orders` scores `4` from its four outgoing calls alone and lands at the bottom — the weakest seam, confirming intuition: a module that reaches into four others is expensive and risky to extract first.
3. **Level 3 — accounting for shared transactions** — real coupling isn't just "does a method call exist," it's also "do these modules commit inside the same database transaction," which is far harder to safely split (see [database decomposition](0068-database-decomposition-splitting-a-shared-schema.md)). `SeamScoreWithTransactions` models each `Call` with a `sharesTransaction` flag and weighs those calls 3x as heavily when summing into `weightedScore`.
4. **Tracing the score changes** — `Inventory` receives weight from two calls: `Orders -> Inventory` (`sharesTransaction=true`, weight 3) and `Shipping -> Inventory` (also `sharesTransaction=true`, weight 3), for a total of 6. In Level 2's plain edge count, `Inventory` tied with `Customers` at a score of 2 each; here, `Customers` (whose two incoming calls are both plain, non-transactional) stays at 2, while `Inventory`'s score triples to 6 — correctly surfacing that `Inventory` is a much riskier extraction target than `Customers`, even though a naive method-call count made them look identical.
5. **Reading the final ranking** — `Notifications` (0) and then `Billing`/`Customers` (2 each) remain the safest seams; `Shipping` (4) is moderate risk, driven up specifically by its one transactional call; `Orders` and `Inventory` tie at 6, both dragged up by the same shared transactional edge between them — `Orders` remains a weak seam and a late candidate for extraction, consistent with it being the system's dense, central hub in both versions of the analysis.

## 7. Gotchas & takeaways

> **Gotcha:** a plain method-call count, as in Level 2, can seriously understate risk when two modules share a database transaction. Two modules with the same edge count are not equally safe to split if one pair's calls are wrapped in the same `@Transactional` boundary — always fold transaction sharing into the analysis, as Level 3 does, before ranking candidates.

- A seam is a place of naturally low coupling — few incoming calls, few outgoing calls, and no shared database transaction with the rest of the system.
- Mechanical seam-scoring (counting call-graph edges, weighting shared transactions more heavily) turns "where should we start?" into something measurable rather than a guess.
- Seam analysis and bounded-context analysis (via [event storming](0063-event-storming-for-boundary-discovery.md) or DDD) should be done together — a good extraction candidate needs to be both a coherent business concept and a low-coupling seam.
- Extract the strongest seams first to build team confidence and reusable migration tooling, as covered in [decomposing a monolith incrementally](0066-decomposing-a-monolith-incrementally.md); save the most entangled modules for last, once the team has practice.
- Static call-graph counts are a useful starting heuristic, not a complete picture — deployment coupling, shared caches, and implicit contracts (like relying on a specific execution order) can all add coupling that a pure code-dependency count misses.
