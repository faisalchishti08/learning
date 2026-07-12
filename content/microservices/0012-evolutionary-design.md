---
card: microservices
gi: 12
slug: evolutionary-design
title: Evolutionary design
---

## 1. What it is

**Evolutionary design** is the Lewis & Fowler characteristic that says a service's API and internal design should be able to change gradually, over time, without requiring a single coordinated "big bang" release across every service that depends on it. In a monolith, changing a shared internal data type is one recompile away from being consistent everywhere. In microservices, callers and the service they call are deployed independently and often at different times — so the service's contract has to tolerate being consumed by both old and new client versions simultaneously, during the (sometimes lengthy) window while consumers migrate.

## 2. Why & when

If every change to a service's API required every consumer to update in lockstep, independent deployability — the whole point of microservices — would be an illusion: you'd still need a coordinated, synchronized release across teams, just now with more network hops involved. Evolutionary design avoids that by treating API changes as something that rolls out gradually: add new capability without removing the old, let consumers migrate at their own pace, and only remove old capability once you can confirm nothing still depends on it.

Apply this from the moment a service has more than one external consumer — even if that consumer is just one other team's service. The core technique is the **tolerant reader**: a consumer that only reads the specific fields it actually needs and ignores anything unfamiliar, rather than strictly validating the entire shape of a response. That tolerance is what lets a producer add new fields freely without breaking anyone.

## 3. Core concept

Two ways an API can change, with very different consequences:

- **Breaking change:** renaming or removing a field a consumer already depends on. Any consumer not yet updated instantly breaks the moment the new version deploys — this forces a coordinated, synchronized release.
- **Backward-compatible change:** adding a new, optional field while keeping every existing field exactly as it was. A "tolerant" consumer, one that ignores fields it doesn't recognize, keeps working unmodified; a consumer that wants the new field can adopt it whenever it's ready, on its own schedule.

Evolutionary design is the discipline of preferring the second kind of change, and giving consumers a deliberate, gradual migration path (often via API versioning) for the rare cases where a genuinely breaking change is unavoidable.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A breaking change forces every consumer to update at once; a backward-compatible change lets old and new consumers coexist while migrating gradually">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Breaking change</text>
  <rect x="30" y="35" width="240" height="35" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Producer v2 (field renamed)</text>
  <rect x="30" y="90" width="110" height="35" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="85" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">old consumer: BROKEN</text>
  <rect x="160" y="90" width="110" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="215" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">new consumer: OK</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Evolutionary change</text>
  <rect x="380" y="35" width="240" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Producer v2 (field added, old kept)</text>
  <rect x="380" y="90" width="110" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="435" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">old consumer: still OK</text>
  <rect x="510" y="90" width="110" height="35" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="565" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">new consumer: OK, uses new field</text>
</svg>

A breaking change splits consumers into working and broken; a backward-compatible change lets both coexist while migration happens on each team's own schedule.

## 5. Runnable example

Scenario: a `ProductInfo` API evolving over time, first breaking a consumer with a rename, then fixed with a tolerant reader and additive change, then extended to full parallel API versioning for a genuinely unavoidable breaking change.

### Level 1 — Basic

```java
// File: BreakingChange.java -- renaming a field breaks an existing consumer immediately
import java.util.*;

public class BreakingChange {
    // v1 producer: uses key "name"
    static Map<String, String> productV1() { return Map.of("name", "Widget", "price", "9.99"); }

    // v2 producer: renamed "name" to "productName" -- a BREAKING change
    static Map<String, String> productV2() { return Map.of("productName", "Widget", "price", "9.99"); }

    // consumer, written against v1's shape, STRICTLY expects "name" to exist
    static String describe(Map<String, String> product) {
        return product.get("name") + ": $" + product.get("price"); // throws NPE if "name" is missing
    }

    public static void main(String[] args) {
        System.out.println(describe(productV1())); // works fine
        try {
            System.out.println(describe(productV2())); // BREAKS -- "name" no longer exists
        } catch (NullPointerException e) {
            System.out.println("consumer BROKE: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac BreakingChange.java && java BreakingChange` (JDK 17+).

Expected output:
```
Widget: $9.99
consumer BROKE: Cannot invoke "String.concat(String)" because the return value of "java.util.Map.get(String)" is null
```

`describe` was written to strictly expect a `"name"` key. The moment the producer renames that field, every consumer still on the old expectation breaks — this is exactly the kind of change that would force a coordinated, synchronized release across every consumer team.

### Level 2 — Intermediate

```java
// File: TolerantReader.java -- ADD a new field instead of renaming; consumer
// reads tolerantly, ignoring fields it doesn't recognize.
import java.util.*;

public class TolerantReader {
    // v1 producer: unchanged shape
    static Map<String, String> productV1() { return Map.of("name", "Widget", "price", "9.99"); }

    // v2 producer: ADDS "category", keeps "name" -- a backward-compatible, additive change
    static Map<String, String> productV2() { return Map.of("name", "Widget", "price", "9.99", "category", "hardware"); }

    // TOLERANT consumer: reads only the fields it needs, ignores anything unfamiliar
    static String describe(Map<String, String> product) {
        String name = product.get("name");
        String price = product.get("price");
        return name + ": $" + price; // never looks at "category" -- doesn't care that it's there
    }

    public static void main(String[] args) {
        System.out.println(describe(productV1())); // works
        System.out.println(describe(productV2())); // ALSO works -- extra field is simply ignored
    }
}
```

**How to run:** `javac TolerantReader.java && java TolerantReader` (JDK 17+).

Expected output:
```
Widget: $9.99
Widget: $9.99
```

`describe` reads only `"name"` and `"price"`, exactly as before. `productV2` adds a whole new field, `"category"`, but because the consumer only asks for what it needs and ignores the rest, it works unmodified against both the old and new producer shape — no coordinated release needed.

### Level 3 — Advanced

```java
// File: ParallelApiVersions.java -- a GENUINELY breaking change (price format
// changes from a string to cents-as-int), handled via parallel v1/v2 endpoints
// so consumers migrate on their own schedule instead of all at once.
import java.util.*;

public class ParallelApiVersions {
    // v1: price as a decimal STRING -- the old, still-supported shape
    static Map<String, Object> productV1() { return Map.of("name", "Widget", "price", "9.99"); }

    // v2: price as INTEGER CENTS -- more precise, but a genuinely incompatible type change
    static Map<String, Object> productV2() { return Map.of("name", "Widget", "priceCents", 999); }

    // OLD consumer: still calls the v1 shape, untouched, migrates whenever THEY are ready
    static String describeV1Consumer(Map<String, Object> product) {
        return product.get("name") + ": $" + product.get("price");
    }

    // NEW consumer: has migrated to the v2 shape, gets the new precision benefit
    static String describeV2Consumer(Map<String, Object> product) {
        int cents = (int) product.get("priceCents");
        return product.get("name") + ": $" + String.format("%d.%02d", cents / 100, cents % 100);
    }

    public static void main(String[] args) {
        // BOTH api versions are served SIMULTANEOUSLY -- neither consumer is forced to move on the other's schedule
        System.out.println("old consumer, v1 endpoint: " + describeV1Consumer(productV1()));
        System.out.println("new consumer, v2 endpoint: " + describeV2Consumer(productV2()));

        // months later, once telemetry confirms NO ONE calls v1 anymore, it can finally be retired
        boolean v1StillInUse = false;
        if (!v1StillInUse) {
            System.out.println("v1 endpoint retired -- migration complete, no coordinated big-bang release was ever needed");
        }
    }
}
```

**How to run:** `javac ParallelApiVersions.java && java ParallelApiVersions` (JDK 17+).

Expected output:
```
old consumer, v1 endpoint: Widget: $9.99
new consumer, v2 endpoint: Widget: $9.990
v1 endpoint retired -- migration complete, no coordinated big-bang release was ever needed
```

The production-flavored hard case: `price` genuinely changing from a decimal string to integer cents is not something a tolerant reader can absorb — the type itself changed, not just an added field. Rather than force every consumer to migrate at the same instant, `productV1` and `productV2` are served in parallel. `describeV1Consumer` keeps working against the old shape indefinitely, and `describeV2Consumer` adopts the new shape whenever that team is ready — the two can be deployed and migrated on completely independent timelines, and v1 is only removed once telemetry confirms nothing calls it anymore.

## 6. Walkthrough

1. `productV1()` and `productV2()` represent two API versions being served at the same time — not sequentially replacing one another, but genuinely coexisting.
2. `describeV1Consumer(productV1())` runs first: it reads `"name"` and `"price"` from the v1 shape exactly as it always has, producing `"Widget: $9.99"` — this consumer's code has not changed at all during this entire evolution.
3. `describeV2Consumer(productV2())` runs next, on a completely different code path: it reads `"priceCents"` (an `Integer`, `999`), then formats it back into a dollar string with `String.format("%d.%02d", cents / 100, cents % 100)`, producing `"Widget: $9.990"` — a new consumer, written specifically against the new shape, getting the benefit of the more precise integer representation.
4. Both of these calls succeed in the same program run, proving the two API versions and their two respective consumers are not in conflict — deploying `describeV2Consumer`'s team's code has zero effect on `describeV1Consumer`'s team, and vice versa.
5. `v1StillInUse = false` represents a fact only observable in a real system through monitoring: tracking whether any caller still hits the v1 endpoint. Once that's confirmed false — not assumed, *confirmed* — the `if` block prints that v1 can finally be retired.
6. The key structural point: retiring v1 happens as its own, separate, low-risk step, decoupled in time from when v2 was first introduced — exactly the gradual migration evolutionary design is meant to enable, in contrast to Level 1's `BreakingChange`, where the rename took effect for every consumer the instant the new version deployed.

```
t0: v1 live, no consumers on v2 yet
t1: v2 introduced, served ALONGSIDE v1 -- both live simultaneously
t2: consumers migrate to v2 gradually, each on their own schedule
t3: telemetry confirms v1 has zero traffic
t4: v1 retired -- a separate, low-risk step, long after v2 first appeared
```

## 7. Gotchas & takeaways

> **Gotcha:** "tolerant reader" only protects against *additive* changes — new fields, new optional data. It does not protect against a field's *type* or *meaning* changing while keeping the same name (like `price` silently switching from dollars to cents under the same key) — that's a silent, dangerous breaking change a tolerant reader will happily misinterpret rather than fail loudly on. Renaming the field, as `ParallelApiVersions` does (`price` to `priceCents`), makes a genuine semantic change visible and forces consumers to opt in deliberately.

- Evolutionary design means a service's API can change gradually — new consumers adopting new capability while old consumers keep working unmodified — rather than requiring a coordinated, synchronized release across every dependent team.
- A tolerant reader (reading only the specific fields you need, ignoring the rest) is what lets a producer add new fields freely without breaking existing consumers.
- A genuinely breaking change (a type or meaning change, not just an addition) should get a new, distinctly named field or a new API version served in parallel with the old — never a silent reinterpretation of an existing field.
- Retire an old API version only once you can confirm, through real observation, that nothing still depends on it — not once you merely believe migration should be finished by now.
