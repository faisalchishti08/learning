---
card: microservices
gi: 49
slug: bounded-context
title: Bounded context
---

## 1. What it is

While [bounded context as a service boundary](0018-bounded-context-as-a-service-boundary.md) covered *drawing* service lines around bounded contexts, this tutorial covers the DDD concept more fully: bounded contexts don't exist in isolation — they relate to each other through well-known **context mapping patterns**, each describing a different way two contexts can depend on one another. The most common: **Shared Kernel** (two contexts deliberately share a small, jointly-owned piece of model), **Customer-Supplier** (one context's team has influence over the other's roadmap, since it depends on it), **Conformist** (a downstream context simply accepts an upstream context's model as-is, with no translation), and **Anticorruption Layer** (a downstream context translates an upstream context's model into its own terms, protecting its own model from the upstream's influence).

## 2. Why & when

Choosing the right relationship pattern between two bounded contexts matters because each pattern trades off translation effort against model purity differently, and getting it wrong in either direction has real cost. Blindly conforming to every upstream context's model (Conformist, everywhere) saves translation effort but lets an external system's design decisions leak directly into your own domain model, potentially corrupting concepts that should be independent. Building an anticorruption layer for every single upstream dependency, even trivial ones, adds real, possibly unnecessary translation overhead.

Choose deliberately, per relationship: use an **anticorruption layer** when the upstream context's model is messy, legacy, or conceptually foreign to your own domain, and you want to protect your model's integrity from its influence. Accept a **conformist** relationship when the upstream model is already clean and well-aligned with your needs, and building a translation layer would add cost without real benefit. Use a **shared kernel** sparingly, only when two teams are close enough (organizationally and in trust) to jointly maintain a small, genuinely shared piece of model without it becoming a coordination bottleneck.

## 3. Core concept

Four relationship patterns, each answering "how does context B depend on context A?":

| Pattern | Relationship |
|---|---|
| Shared Kernel | A and B jointly own and maintain a small, shared piece of model |
| Customer-Supplier | B (customer) depends on A (supplier); A's team considers B's needs in its own roadmap |
| Conformist | B accepts A's model exactly as-is, no translation, no negotiation |
| Anticorruption Layer | B translates A's model into B's own terms at the boundary, protecting B's model from A's influence |

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four context mapping patterns: shared kernel overlapping two contexts, conformist accepting the upstream model directly, and anticorruption layer translating at the boundary">
  <text x="110" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Shared Kernel</text>
  <rect x="30" y="35" width="80" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="90" y="35" width="80" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" opacity="0.7"/>
  <text x="110" y="65" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">shared model</text>

  <text x="330" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Conformist</text>
  <rect x="230" y="35" width="90" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="275" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Upstream A</text>
  <rect x="340" y="35" width="90" height="50" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="385" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">B: same model</text>
  <line x1="320" y1="60" x2="340" y2="60" stroke="#8b949e"/>

  <text x="550" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Anticorruption Layer</text>
  <rect x="460" y="35" width="80" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Upstream A</text>
  <rect x="555" y="35" width="20" height="50" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="590" y="35" width="30" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="60" fill="#e6edf3" font-size="6" text-anchor="middle" font-family="sans-serif">B</text>
</svg>

Different patterns for how one bounded context depends on another — jointly shared, directly conformed to, or translated at a protective boundary.

## 5. Runnable example

Scenario: a service depending on an upstream system's model, first as a naive conformist relationship, then protected by an anticorruption layer, then extended to show the anticorruption layer absorbing an upstream model change without affecting downstream code.

### Level 1 — Basic

```java
// File: Conformist.java -- downstream accepts the upstream model DIRECTLY, no translation
import java.util.*;

public class Conformist {
    // an UPSTREAM legacy system's model -- messy field names, its OWN conventions
    static Map<String, String> upstreamCustomerRecord() {
        return Map.of("CUST_NM", "Alice", "CUST_STAT_CD", "A"); // legacy naming, a status CODE not a clear value
    }

    // downstream code reads the upstream model DIRECTLY -- CONFORMIST
    static String describeCustomer() {
        Map<String, String> record = upstreamCustomerRecord();
        String status = record.get("CUST_STAT_CD").equals("A") ? "Active" : "Inactive"; // downstream must know the legacy CODE meaning
        return record.get("CUST_NM") + ": " + status;
    }

    public static void main(String[] args) {
        System.out.println(describeCustomer());
    }
}
```

**How to run:** `javac Conformist.java && java Conformist` (JDK 17+).

Expected output:
```
Alice: Active
```

`describeCustomer` directly depends on `"CUST_NM"`, `"CUST_STAT_CD"`, and the specific meaning of code `"A"` — all upstream legacy details leaking directly into downstream code. Any change to the upstream system's field names or status codes breaks this code immediately.

### Level 2 — Intermediate

```java
// File: AnticorruptionLayer.java -- translate the upstream model into a
// CLEAN, downstream-owned model at the boundary, protecting downstream code.
import java.util.*;

public class AnticorruptionLayer {
    static Map<String, String> upstreamCustomerRecord() {
        return Map.of("CUST_NM", "Alice", "CUST_STAT_CD", "A");
    }

    // downstream's OWN clean model -- no legacy naming, no raw status codes
    record Customer(String name, boolean isActive) { }

    // the ANTICORRUPTION LAYER -- the ONLY place that knows about the upstream's messy details
    static Customer translateFromUpstream(Map<String, String> upstreamRecord) {
        String name = upstreamRecord.get("CUST_NM");
        boolean isActive = upstreamRecord.get("CUST_STAT_CD").equals("A");
        return new Customer(name, isActive);
    }

    // downstream business logic depends ONLY on the clean model -- ZERO upstream knowledge
    static String describeCustomer(Customer customer) {
        return customer.name() + ": " + (customer.isActive() ? "Active" : "Inactive");
    }

    public static void main(String[] args) {
        Customer customer = translateFromUpstream(upstreamCustomerRecord());
        System.out.println(describeCustomer(customer));
    }
}
```

**How to run:** `javac AnticorruptionLayer.java && java AnticorruptionLayer` (JDK 17+).

Expected output:
```
Alice: Active
```

Same result, but now `describeCustomer` depends only on the clean `Customer` record — `"CUST_NM"`, `"CUST_STAT_CD"`, and the meaning of code `"A"` are known only inside `translateFromUpstream`, the one, deliberate anticorruption layer.

### Level 3 — Advanced

```java
// File: LayerAbsorbsUpstreamChange.java -- the upstream system CHANGES its
// model; the anticorruption layer absorbs it, downstream code is UNTOUCHED.
import java.util.*;

public class LayerAbsorbsUpstreamChange {
    // upstream V2: the legacy system migrated to a NEW status scheme --
    // codes changed from "A"/"I" to numeric "1"/"0"
    static Map<String, String> upstreamCustomerRecordV2() {
        return Map.of("CUST_NM", "Alice", "CUST_STAT_CD", "1"); // DIFFERENT encoding than before
    }

    record Customer(String name, boolean isActive) { } // downstream's clean model -- UNCHANGED

    // ONLY the anticorruption layer needs to change, to handle the NEW upstream encoding
    static Customer translateFromUpstreamV2(Map<String, String> upstreamRecord) {
        String name = upstreamRecord.get("CUST_NM");
        boolean isActive = upstreamRecord.get("CUST_STAT_CD").equals("1"); // updated to match the NEW upstream scheme
        return new Customer(name, isActive);
    }

    // downstream business logic, UNCHANGED from Level 2 -- still depends ONLY on the clean model
    static String describeCustomer(Customer customer) {
        return customer.name() + ": " + (customer.isActive() ? "Active" : "Inactive");
    }

    public static void main(String[] args) {
        Customer customer = translateFromUpstreamV2(upstreamCustomerRecordV2());
        System.out.println(describeCustomer(customer));
        System.out.println("describeCustomer's source code did NOT change, despite the upstream model changing entirely");
    }
}
```

**How to run:** `javac LayerAbsorbsUpstreamChange.java && java LayerAbsorbsUpstreamChange` (JDK 17+).

Expected output:
```
Alice: Active
describeCustomer's source code did NOT change, despite the upstream model changing entirely
```

The production-flavored payoff: the upstream system changed its status-code encoding entirely (`"A"`/`"I"` to `"1"`/`"0"`), a genuinely breaking change to its model. Only `translateFromUpstreamV2`, the anticorruption layer, needed to change to accommodate it. `describeCustomer` — and the clean `Customer` record it depends on — are byte-for-byte identical to Level 2, completely insulated from the upstream change, exactly as an anticorruption layer is designed to guarantee.

## 6. Walkthrough

1. `upstreamCustomerRecordV2()` returns a map using the upstream system's *new* encoding — `"CUST_STAT_CD"` is now `"1"` instead of the old `"A"`, modeling a real upstream migration downstream code had no control over.
2. `translateFromUpstreamV2` reads this map and checks `upstreamRecord.get("CUST_STAT_CD").equals("1")` — the *only* place in this entire program that knows about the new encoding scheme — and constructs a `Customer(name, isActive)` exactly as before, using the same clean model shape.
3. `describeCustomer(customer)` receives this `Customer` object and reads only `customer.name()` and `customer.isActive()` — it has no idea whether the underlying upstream system used `"A"`/`"I"` or `"1"`/`"0"`, because that detail was fully absorbed and translated away by the anticorruption layer before `describeCustomer` ever saw the data.
4. The output is identical to Level 2's — `"Alice: Active"` — confirming the translation correctly preserved meaning across the upstream's breaking change, and the explicit final print underlines that `describeCustomer`'s source code required zero edits to keep working correctly against the new upstream version.

```
Upstream V1: CUST_STAT_CD = "A"   -> translateFromUpstream   -> Customer(isActive=true)
Upstream V2: CUST_STAT_CD = "1"   -> translateFromUpstreamV2 -> Customer(isActive=true)
        |
describeCustomer(Customer) -- IDENTICAL code in both cases, fully insulated from the upstream change
```

## 7. Gotchas & takeaways

> **Gotcha:** building an anticorruption layer has a real, ongoing cost — someone has to maintain the translation logic, and it must be updated whenever the upstream model changes (as shown above). For a trivial, stable, well-designed upstream dependency, a Conformist relationship can be the more pragmatic choice; reserve anticorruption layers for upstream contexts whose model is genuinely messy, legacy, foreign to your domain, or likely to change in ways you don't control.

- Bounded contexts relate to each other through distinct context mapping patterns — Shared Kernel, Customer-Supplier, Conformist, and Anticorruption Layer — each trading off translation effort against model purity differently.
- A Conformist relationship accepts an upstream model exactly as-is, saving translation effort but letting the upstream's design decisions leak directly into downstream code.
- An Anticorruption Layer translates the upstream model into the downstream context's own clean terms at one deliberate boundary point, insulating downstream business logic from upstream changes entirely.
- Choose the relationship pattern deliberately per dependency, based on the upstream model's quality and stability — not as a blanket default applied to every integration regardless of its actual characteristics.
