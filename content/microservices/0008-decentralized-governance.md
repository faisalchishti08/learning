---
card: microservices
gi: 8
slug: decentralized-governance
title: Decentralized governance
---

## 1. What it is

**Decentralized governance** is the Lewis & Fowler characteristic that says individual teams should be free to choose their own tools, languages, and internal implementation approaches for the services they own, rather than having a single, centrally mandated technology stack imposed across the whole organization. What *is* still shared, typically, is the external contract each service must honor — its API shape, its expected behavior — not the code inside it.

This mirrors how well-run open-source ecosystems work: many independent contributors and libraries, each free to make its own internal choices, held together not by a central authority dictating implementation, but by shared, agreed interfaces.

## 2. Why & when

Centralized governance — "every service must be written in the same language, use the same framework, follow the same internal patterns" — has a real benefit: consistency makes it easier for any engineer to jump into any service. But it has a real cost too: it forces every team to use one-size-fits-all tooling even when a different tool would genuinely suit their specific problem better, and it creates a central authority that becomes a bottleneck whenever a team wants to deviate for a good reason.

Decentralize governance once your teams are genuinely independent enough, and your service boundaries clean enough, that a team choosing a different internal implementation for their own service doesn't create cross-team friction — because the only thing other teams depend on is the contract, not the implementation. Keep some things centralized deliberately — a shared authentication scheme, a shared logging format — where genuine cross-cutting consistency outweighs the value of local choice; decentralized governance is about defaulting to local autonomy, not eliminating every shared standard.

## 3. Core concept

The dividing line is: what's fixed centrally, and what's left to each team?

- **Centralized governance:** one team mandates *both* the contract and the implementation. Every service literally reuses the same internal code, the same data structure, the same algorithm.
- **Decentralized governance:** only the contract is fixed. Each team implements against that contract however suits them best — different internal data structures, different algorithms, even different languages in a real polyglot system — as long as the observable behavior at the boundary matches.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Centralized governance mandates one shared implementation for every service; decentralized governance fixes only the contract, letting each team choose its own implementation">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Centralized</text>
  <rect x="60" y="35" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="59" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">One mandated implementation</text>
  <rect x="30" y="95" width="80" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="190" y="95" width="80" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="230" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Decentralized</text>
  <rect x="380" y="35" width="240" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Shared contract only</text>
  <rect x="370" y="90" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="420" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service A: own impl</text>
  <rect x="490" y="90" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Service B: own impl</text>
</svg>

Centralized governance fixes the code; decentralized governance fixes only the contract.

## 5. Runnable example

Scenario: two teams each build a "lookup" service against the same shared contract, first sharing one mandated implementation, then choosing genuinely different internal implementations, then proving one team can change their internals freely without affecting the other.

### Level 1 — Basic

```java
// File: CentralizedGovernance.java -- BOTH services forced to reuse the
// exact same centrally mandated implementation class.
import java.util.*;

public class CentralizedGovernance {
    // MANDATED implementation -- every team must use this exact class, no exceptions
    static class MandatedLookup {
        Map<String, String> data = new HashMap<>();
        void put(String key, String value) { data.put(key, value); }
        String get(String key) { return data.getOrDefault(key, "not found"); }
    }

    public static void main(String[] args) {
        MandatedLookup serviceA = new MandatedLookup(); // Team A, no choice in implementation
        serviceA.put("widget", "9.99");

        MandatedLookup serviceB = new MandatedLookup(); // Team B, no choice either
        serviceB.put("gadget", "19.99");

        System.out.println("Service A: " + serviceA.get("widget"));
        System.out.println("Service B: " + serviceB.get("gadget"));
    }
}
```

**How to run:** `javac CentralizedGovernance.java && java CentralizedGovernance` (JDK 17+).

Expected output:
```
Service A: 9.99
Service B: 19.99
```

Both teams are locked into `MandatedLookup`'s internals — a `HashMap`. If Team B needed a different data structure for their specific access pattern (say, ordered iteration), they'd have to convince a central authority to change the mandated class for everyone, or break the mandate.

### Level 2 — Intermediate

```java
// File: DecentralizedGovernance.java -- only a shared CONTRACT (interface)
// is fixed; each team implements it however suits them.
import java.util.*;

public class DecentralizedGovernance {
    interface Lookup { // the ONLY thing centrally agreed: this contract
        void put(String key, String value);
        String get(String key);
    }

    // Team A chooses a HashMap -- fast, unordered lookups, their use case
    static class HashMapLookup implements Lookup {
        Map<String, String> data = new HashMap<>();
        public void put(String key, String value) { data.put(key, value); }
        public String get(String key) { return data.getOrDefault(key, "not found"); }
    }

    // Team B chooses a TreeMap -- they need SORTED iteration for their reports, a different concern entirely
    static class TreeMapLookup implements Lookup {
        Map<String, String> data = new TreeMap<>();
        public void put(String key, String value) { data.put(key, value); }
        public String get(String key) { return data.getOrDefault(key, "not found"); }
        List<String> sortedKeys() { return new ArrayList<>(data.keySet()); }
    }

    public static void main(String[] args) {
        Lookup serviceA = new HashMapLookup();
        serviceA.put("widget", "9.99");

        TreeMapLookup serviceB = new TreeMapLookup();
        serviceB.put("gadget", "19.99");
        serviceB.put("apple", "1.99");

        System.out.println("Service A: " + serviceA.get("widget"));
        System.out.println("Service B sorted keys: " + serviceB.sortedKeys()); // capability HashMapLookup never needed
    }
}
```

**How to run:** `javac DecentralizedGovernance.java && java DecentralizedGovernance` (JDK 17+).

Expected output:
```
Service A: 9.99
Service B sorted keys: [apple, gadget]
```

Only the `Lookup` interface (`put`/`get`) is shared. Team A picked `HashMap`; Team B picked `TreeMap` specifically because they needed sorted iteration — a capability `HashMapLookup` doesn't even offer. Neither team's choice constrains the other's.

### Level 3 — Advanced

```java
// File: DecentralizedGovernanceEvolve.java -- Team A swaps their ENTIRE
// internal implementation, and Team B's code needs ZERO changes.
import java.util.*;

public class DecentralizedGovernanceEvolve {
    interface Lookup {
        void put(String key, String value);
        String get(String key);
    }

    // Team B's implementation, UNCHANGED throughout this example
    static class TreeMapLookup implements Lookup {
        Map<String, String> data = new TreeMap<>();
        public void put(String key, String value) { data.put(key, value); }
        public String get(String key) { return data.getOrDefault(key, "not found"); }
    }

    static void exerciseService(String label, Lookup service) {
        service.put("widget", "9.99");
        System.out.println(label + ": " + service.get("widget") + ", " + service.get("missing"));
    }

    public static void main(String[] args) {
        // Team A v1: a HashMap-backed implementation
        Lookup serviceA_v1 = new Lookup() {
            Map<String, String> data = new HashMap<>();
            public void put(String key, String value) { data.put(key, value); }
            public String get(String key) { return data.getOrDefault(key, "not found"); }
        };
        exerciseService("Service A (v1, HashMap)", serviceA_v1);

        // Team A v2: they migrate to a case-insensitive, concurrent implementation --
        // a totally different internal data structure and algorithm, decided ENTIRELY on their own.
        Lookup serviceA_v2 = new Lookup() {
            Map<String, String> data = new java.util.concurrent.ConcurrentSkipListMap<>(String.CASE_INSENSITIVE_ORDER);
            public void put(String key, String value) { data.put(key, value); }
            public String get(String key) { return data.getOrDefault(key, "not found"); }
        };
        exerciseService("Service A (v2, concurrent case-insensitive)", serviceA_v2);

        // Team B's code is EXERCISED EXACTLY THE SAME WAY, completely unaware Team A changed anything
        exerciseService("Service B (unchanged throughout)", new TreeMapLookup());
    }
}
```

**How to run:** `javac DecentralizedGovernanceEvolve.java && java DecentralizedGovernanceEvolve` (JDK 17+).

Expected output:
```
Service A (v1, HashMap): 9.99, not found
Service A (v2, concurrent case-insensitive): 9.99, not found
Service A (v1, HashMap): 9.99, not found
Service B (unchanged throughout): 9.99, not found
```

The production-flavored case: `exerciseService` is written entirely against the `Lookup` contract, never against a concrete class. Team A migrated from a plain `HashMap` to a `ConcurrentSkipListMap` with case-insensitive ordering — a real, substantial internal change — and `exerciseService` didn't need a single line changed to keep working with either version. Team B's `TreeMapLookup`, exercised the exact same way, was never touched at all.

## 6. Walkthrough

1. `exerciseService("Service A (v1, HashMap)", serviceA_v1)` runs first: it calls `service.put("widget", "9.99")` and `service.get(...)` purely through the `Lookup` interface — it has no idea `serviceA_v1` is backed by a `HashMap` internally.
2. `serviceA_v2` is constructed with a completely different backing structure, `ConcurrentSkipListMap`, wired for case-insensitive keys — representing Team A independently deciding to change their internals, with no approval needed from any other team.
3. `exerciseService("Service A (v2, ...)", serviceA_v2)` runs the exact same calling code as step 1, against the new implementation, and produces the same contractual behavior (`get("widget")` returns `"9.99"`, `get("missing")` returns `"not found"`) — proving the contract held even though the implementation changed entirely.
4. `exerciseService("Service B (unchanged throughout)", new TreeMapLookup())` runs last, using Team B's implementation, which was never edited during this whole example — Team A's internal migration had zero effect on it, because the two teams were never coupled through anything but the shared `Lookup` interface.

```
Lookup (shared contract): put(key, value), get(key)
   |
   +-- Team A v1: HashMap-backed          -- Team A's own choice
   +-- Team A v2: ConcurrentSkipListMap   -- Team A's own choice, changed independently
   +-- Team B:    TreeMap-backed          -- Team B's own choice, never touched by A's changes
```

## 7. Gotchas & takeaways

> **Gotcha:** decentralized governance applies to *implementation*, not to every shared concern. If Team A's `Lookup` implementation silently started throwing a different exception type on a missing key instead of returning `"not found"`, that would break the *contract*, not just the implementation — and no amount of "we're allowed to choose our own tech" justifies breaking the agreed external behavior other teams depend on.

- Decentralized governance means teams choose their own internal implementation freely; what stays fixed and centrally agreed is the contract other services depend on.
- The concrete proof: can one team completely swap their internal data structures and algorithms without any other team's code changing?
- This is not "no standards at all" — deliberately centralizing a few genuinely cross-cutting concerns (auth scheme, logging format) alongside decentralized implementation choice is a normal, healthy middle ground.
- Decentralized governance works only as well as the contract is well-specified and honestly honored — a loose or frequently-broken contract turns "independent teams" back into tightly coupled ones, just less visibly so.
