---
card: microservices
gi: 496
slug: tolerant-reader-pattern
title: "Tolerant reader pattern"
---

## 1. What it is

The **tolerant reader pattern** is a consumer-side design discipline: when parsing a response or message from another service, read only the specific fields you actually need, and explicitly ignore everything else — unrecognized fields, unexpected extra data, fields in a different order. A tolerant reader is deliberately loose about what it accepts, so the provider can evolve its contract additively without breaking every consumer that happens to be strict about exactly what shape it expects.

## 2. Why & when

You apply the tolerant reader pattern in every consumer of another service's API, because a strict, brittle reader turns any additive, backward-compatible provider change into an unplanned breaking change for that specific consumer:

- **A provider adding a new, optional field is meant to be a safe, non-breaking change** — but a consumer that deserializes strictly (failing on unknown fields, or asserting on the exact field count) turns that safe change into a breakage anyway, entirely due to the consumer's own fragility, not the provider's mistake.
- **Field order and exact structure shouldn't matter to a well-behaved consumer.** JSON objects, in particular, have no meaningful field order — a consumer that somehow depends on order (rare, but a real anti-pattern in some deserialization approaches) is unnecessarily fragile.
- **You want consumers resilient to providers evolving independently**, which is the entire premise of [independently deployable](0013-independent-deployability.md) microservices — a consumer shouldn't need to be redeployed just because a provider added a field the consumer was never going to use anyway.
- **You apply this discipline to every piece of code that parses an external response**, from the very first integration — retrofitting tolerant parsing after a consumer has shipped with strict parsing means finding and fixing every brittle assumption after the fact, which is far more work than building it in from the start.

## 3. Core concept

Think of reading a job posting for the specific details you care about (salary range, location) while ignoring the boilerplate legal disclaimers and unrelated company history paragraphs also present in the document — you don't refuse to apply just because the posting contains sections irrelevant to your interests; you extract what matters and disregard the rest. A tolerant reader treats a service response the same way: extract the fields it actually needs, and simply don't look at, assert on, or fail because of anything else present.

Concretely, tolerant reading means:

1. **Deserialize permissively** — using a JSON library configured to ignore unknown properties rather than fail on them, rather than requiring an exact 1:1 field match between the response and a strict schema class.
2. **Only read the specific fields the consumer's own logic actually needs**, leaving everything else in the response entirely untouched and unexamined.
3. **Treat optional or new fields defensively** — check for presence before use, rather than assuming a field that might not exist in every provider version is always there.
4. **Avoid asserting on structural details that aren't semantically meaningful** — the exact number of fields, their order, or the presence of fields the consumer doesn't care about should never be part of a tolerant reader's validation logic.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tolerant reader extracts only the fields it needs from a response, ignoring extra fields it doesn't recognize, rather than failing on their presence" >
  <rect x="20" y="30" width="280" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">provider's response</text>
  <text x="160" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">orderId (needed)</text>
  <text x="160" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">status (needed)</text>
  <text x="160" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">loyaltyPointsEarned (ignored)</text>
  <text x="160" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">internalTrackingId (ignored)</text>

  <rect x="360" y="60" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="500" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">tolerant reader extracts</text>
  <text x="500" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">only orderId and status</text>

  <line x1="300" y1="75" x2="360" y2="90" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="300" y1="95" x2="360" y2="95" stroke="#6db33f" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
  </defs>
</svg>

The tolerant reader extracts only what it needs, leaving unrecognized fields in the response entirely untouched.

## 5. Runnable example

Scenario: a consumer reading order data from a provider. We start with a strict, brittle reader that fails on unexpected fields, extend it to a tolerant reader that extracts only what it needs, then handle the hard case: the provider genuinely changing the response shape between calls (adding fields, reordering), which the tolerant reader must handle correctly across every call while a strict reader would break.

### Level 1 — Basic

```java
// File: StrictReaderBrittle.java -- models the PROBLEM: a STRICT reader
// that fails the moment a response contains ANY field it doesn't
// explicitly expect -- brittle, and easily broken by a safe provider change.
import java.util.*;

public class StrictReaderBrittle {
    static void strictParseOrder(Map<String, Object> response) {
        Set<String> expectedFields = Set.of("orderId", "status");
        if (!response.keySet().equals(expectedFields)) {
            throw new RuntimeException("STRICT PARSE FAILED: response fields " + response.keySet()
                    + " do not exactly match expected fields " + expectedFields);
        }
        System.out.println("[strict reader] orderId=" + response.get("orderId") + ", status=" + response.get("status"));
    }

    public static void main(String[] args) {
        System.out.println("--- original response shape ---");
        strictParseOrder(Map.of("orderId", "42", "status", "SHIPPED"));

        System.out.println();
        System.out.println("--- provider adds a new, harmless optional field ---");
        try {
            strictParseOrder(new LinkedHashMap<>(Map.of("orderId", "43", "status", "SHIPPED", "loyaltyPointsEarned", 15)));
        } catch (RuntimeException e) {
            System.out.println("[strict reader] " + e.getMessage());
        }
    }
}
```

How to run: `java StrictReaderBrittle.java`

`strictParseOrder`'s `response.keySet().equals(expectedFields)` check demands an *exact* match — when the provider adds `loyaltyPointsEarned`, a perfectly safe, additive change, `response.keySet()` no longer equals `expectedFields` exactly, and the strict reader throws, even though the two fields it actually needed (`orderId`, `status`) are both still present and unchanged.

### Level 2 — Intermediate

```java
// File: TolerantReaderBasic.java -- the SAME parsing need, now as a
// TOLERANT reader: extract ONLY what's needed, and never even LOOK at
// the full set of fields present -- the same "extra field" scenario that
// broke the strict reader causes NO problem here.
import java.util.*;

public class TolerantReaderBasic {
    static void tolerantParseOrder(Map<String, Object> response) {
        // Only reads the two fields it actually needs -- never inspects keySet() at all.
        Object orderId = response.get("orderId");
        Object status = response.get("status");
        System.out.println("[tolerant reader] orderId=" + orderId + ", status=" + status);
    }

    public static void main(String[] args) {
        System.out.println("--- original response shape ---");
        tolerantParseOrder(Map.of("orderId", "42", "status", "SHIPPED"));

        System.out.println();
        System.out.println("--- provider adds a new, harmless optional field ---");
        tolerantParseOrder(new LinkedHashMap<>(Map.of("orderId", "43", "status", "SHIPPED", "loyaltyPointsEarned", 15)));
    }
}
```

How to run: `java TolerantReaderBasic.java`

`tolerantParseOrder` calls `response.get(...)` directly for the two fields it needs, and never examines `response.keySet()` or the map's overall shape at all — the exact same "provider adds a new field" scenario that broke `StrictReaderBrittle` causes zero disruption here, since the tolerant reader was never checking for the field's *absence* from some exhaustive expected set in the first place.

### Level 3 — Advanced

```java
// File: TolerantReaderAcrossEvolvingShapes.java -- the SAME tolerant
// reading, now handling the PRODUCTION-FLAVORED hard case: the PROVIDER's
// response shape genuinely EVOLVES across THREE real calls -- fields
// added, an optional field sometimes present and sometimes not, field
// insertion order changing. A truly tolerant reader must handle ALL
// THREE variations correctly and uniformly, with NO special-casing per
// call.
import java.util.*;

public class TolerantReaderAcrossEvolvingShapes {
    static void tolerantParseOrder(Map<String, Object> response) {
        Object orderId = response.get("orderId");
        Object status = response.get("status");
        // Defensively checks presence for a field that's KNOWN to be optional --
        // still tolerant, since it doesn't assume the field is always there.
        Object couponCode = response.getOrDefault("couponCode", null);

        String couponInfo = couponCode != null ? ("coupon=" + couponCode) : "no coupon";
        System.out.println("[tolerant reader] orderId=" + orderId + ", status=" + status + ", " + couponInfo
                + " (response had " + response.size() + " total fields, only 2-3 actually read)");
    }

    public static void main(String[] args) {
        System.out.println("--- call 1: original shape, v1 provider ---");
        Map<String, Object> response1 = new LinkedHashMap<>();
        response1.put("orderId", "1");
        response1.put("status", "SHIPPED");
        tolerantParseOrder(response1);

        System.out.println();
        System.out.println("--- call 2: v2 provider adds loyaltyPointsEarned AND a coupon field, different field order ---");
        Map<String, Object> response2 = new LinkedHashMap<>();
        response2.put("status", "DELIVERED"); // note: different field ORDER than call 1
        response2.put("couponCode", "SAVE10");
        response2.put("orderId", "2");
        response2.put("loyaltyPointsEarned", 20);
        tolerantParseOrder(response2);

        System.out.println();
        System.out.println("--- call 3: v2 provider, but THIS order has no coupon applied ---");
        Map<String, Object> response3 = new LinkedHashMap<>();
        response3.put("orderId", "3");
        response3.put("status", "PENDING");
        response3.put("loyaltyPointsEarned", 0);
        // couponCode genuinely absent this time -- no coupon was used.
        tolerantParseOrder(response3);
    }
}
```

How to run: `java TolerantReaderAcrossEvolvingShapes.java`

`tolerantParseOrder`'s code is completely unchanged across all three calls — it reads `orderId` and `status` unconditionally, and uses `getOrDefault("couponCode", null)` to defensively handle a field it knows might or might not be present. Call 2's fields are inserted in a different order and include two fields the reader has never heard of (`loyaltyPointsEarned` is read nowhere in this method), and call 3 genuinely omits `couponCode` entirely — all three calls succeed identically, with the reader correctly extracting what it needs regardless of field order, extra fields, or a known-optional field's presence or absence.

## 6. Walkthrough

Trace `TolerantReaderAcrossEvolvingShapes.main` in order. **First**, call 1 constructs `response1` with exactly two fields, in the original v1 shape, and passes it to `tolerantParseOrder`. `orderId` and `status` are read directly via `get`, `couponCode` reads as `null` since the key is entirely absent from `response1`, and the reader correctly reports "no coupon."

**Next**, call 2 constructs `response2` with four fields — `status` inserted *first* this time, then `couponCode`, then `orderId`, then a brand-new `loyaltyPointsEarned` field the reader's code never references anywhere. `tolerantParseOrder` runs its identical logic: `response.get("orderId")` and `response.get("status")` work correctly regardless of insertion order, since `Map.get` looks up by key, not position — `couponCode` is present this time, so `couponInfo` reports `"coupon=SAVE10"`.

**Then**, call 3 constructs `response3` with three fields, including `loyaltyPointsEarned` again but genuinely omitting `couponCode` this time (representing an order where no coupon was actually used). `tolerantParseOrder` runs the same logic once more: `orderId` and `status` read correctly, and `getOrDefault("couponCode", null)` correctly returns `null` since the key is absent, so `couponInfo` reports `"no coupon"` — exactly matching call 1's behavior for the same underlying condition (no coupon), despite call 3's response having an entirely different overall shape than call 1's.

**After that**, all three calls succeed without any exception, any special-casing in `tolerantParseOrder` for a specific call's shape, or any assumption about field count or order — the same twenty-some lines of parsing code correctly handled three meaningfully different response shapes from what's meant to represent the same evolving provider contract over time.

**Finally**, each call's printed field count (`response.size()`) differs — 2, 4, and 3 respectively — while the actual fields read remains constant at 2 or 3, visibly demonstrating the core discipline: the reader's behavior depends only on the specific fields it chooses to look at, never on the full shape of what it received.

```
--- call 1: original shape, v1 provider ---
[tolerant reader] orderId=1, status=SHIPPED, no coupon (response had 2 total fields, only 2-3 actually read)

--- call 2: v2 provider adds loyaltyPointsEarned AND a coupon field, different field order ---
[tolerant reader] orderId=2, status=DELIVERED, coupon=SAVE10 (response had 4 total fields, only 2-3 actually read)

--- call 3: v2 provider, but THIS order has no coupon applied ---
[tolerant reader] orderId=3, status=PENDING, no coupon (response had 3 total fields, only 2-3 actually read)
```

## 7. Gotchas & takeaways

> Some JSON deserialization libraries fail on unknown properties *by default* — a team adopting a strict-by-default library without explicitly configuring it to ignore unrecognized fields can accidentally build a brittle, strict reader without ever intending to, purely because they didn't override the library's default setting.
- Tolerant reading applies to more than just field presence — avoid asserting on field order, exact field counts, or any other structural detail that isn't semantically meaningful to what the consumer actually needs.
- This pattern is the consumer-side half of [backward and forward compatibility](0495-backward-forward-compatibility.md) — a provider can make all the additive, careful changes it wants, but that discipline only pays off if consumers are actually tolerant enough to benefit from it.
- [Consumer-driven contracts](0497-consumer-driven-contracts.md) formalize what a tolerant reader actually needs from a provider — rather than the provider guessing at what's safe to change, the consumer explicitly states which fields it depends on, and the provider can freely change anything outside that stated dependency set.
- Defensive presence checks (`getOrDefault`, null checks) for fields known to be optional are still fully "tolerant" — the discipline isn't "never check anything," it's "only check for what you specifically need, and handle its potential absence gracefully rather than assuming it."
