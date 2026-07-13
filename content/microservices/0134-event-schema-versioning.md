---
card: microservices
gi: 134
slug: event-schema-versioning
title: "Event schema & versioning"
---

## 1. What it is

Event schema versioning is the discipline of evolving an event's structure over time without breaking consumers that were written against an earlier version of it — using techniques like additive-only changes, explicit version fields, and tolerant reader parsing, so producers and consumers can be deployed and upgraded independently rather than in lockstep.

## 2. Why & when

An [integration event](0131-domain-events-vs-integration-events.md)'s schema is a public contract, and unlike a synchronous API where a version mismatch fails loudly and immediately at call time, a schema-incompatible event can be silently mis-parsed, silently dropped, or crash a consumer hours or days after the producer's change was deployed — by which point the offending event may be long gone from the log, and reproducing the failure is much harder. Because producers and consumers of an event are, by definition, independently deployable services, there is no way to guarantee they upgrade to a new schema at the same moment — so the schema itself has to be designed to tolerate that gap.

Apply schema versioning discipline to any integration event from the moment it is first published, not after the first breaking change causes an incident — retrofitting tolerant parsing onto consumers already deployed against a rigid, unversioned schema is far more painful than designing for evolution from the start.

## 3. Core concept

Additive changes (new optional fields) are safe by default if consumers are written to ignore unknown fields rather than reject them; changes that would otherwise be breaking (removing a field, changing a type, renaming) are instead introduced as a *new* version, with an explicit version marker in the event, so old and new consumers can both correctly interpret whichever version they receive during the transition period.

```java
record OrderPlacedEventV1(int orderId, double total) {}
// adding a field is safe -- V2 is a SUPERSET; a V1-only consumer just never reads discountCode
record OrderPlacedEventV2(int orderId, double total, String discountCode) {}

// a tolerant reader ignores unknown fields rather than failing on them
JsonNode node = parse(rawEvent);
int orderId = node.get("orderId").asInt();       // always present, always read
String discount = node.has("discountCode") ? node.get("discountCode").asText() : null; // tolerant of absence
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During a migration window, both V1 events (orderId, total) and V2 events (orderId, total, discountCode) are published; an old consumer reads both fine, ignoring discountCode when present; a new consumer reads both fine, treating discountCode as optional when absent">
  <rect x="20" y="20" width="180" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Event V1: {orderId, total}</text>

  <rect x="20" y="80" width="220" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="102" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Event V2: {orderId, total,</text>
  <text x="130" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">discountCode}</text>

  <rect x="420" y="30" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="54" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Old consumer (V1-aware)</text>
  <rect x="420" y="100" width="180" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="510" y="124" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">New consumer (V2-aware)</text>

  <line x1="200" y1="42" x2="418" y2="48" stroke="#8b949e" marker-end="url(#arr19)"/>
  <line x1="240" y1="100" x2="418" y2="55" stroke="#8b949e" marker-end="url(#arr19)"/>
  <line x1="240" y1="105" x2="418" y2="115" stroke="#8b949e" marker-end="url(#arr19)"/>

  <text x="330" y="170" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">both consumers correctly handle both event versions during the migration window</text>

  <defs>
    <marker id="arr19" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Additive fields plus tolerant readers let old and new event versions coexist safely during a rollout.

## 5. Runnable example

Scenario: an order-placed event consumer that starts rigid (breaking the instant a new field appears), becomes a tolerant reader that safely ignores unknown fields, and finally handles a genuinely breaking change (a field type change) using an explicit version number and dual-format parsing during the migration window.

### Level 1 — Basic

```java
// File: RigidParsingBreaks.java -- a strict parser that CRASHES the moment an
// unexpected field appears, even though nothing it actually needs has changed.
import java.util.*;

public class RigidParsingBreaks {
    record OrderPlacedEventV1(int orderId, double total) {}

    static OrderPlacedEventV1 parseStrict(Map<String, Object> raw) {
        Set<String> allowedKeys = Set.of("orderId", "total");
        if (!allowedKeys.containsAll(raw.keySet())) {
            throw new RuntimeException("Unexpected field(s) in event: " + raw.keySet()); // FAILS on anything new
        }
        return new OrderPlacedEventV1((int) raw.get("orderId"), (double) raw.get("total"));
    }

    public static void main(String[] args) {
        Map<String, Object> v1Event = Map.of("orderId", 42, "total", 99.90);
        System.out.println("Parsed V1 event fine: " + parseStrict(v1Event));

        // the producer later adds a harmless NEW optional field, discountCode
        Map<String, Object> v2Event = new HashMap<>(v1Event);
        v2Event.put("discountCode", "SAVE10");
        try {
            parseStrict(v2Event);
        } catch (RuntimeException e) {
            System.out.println("CRASHED on a perfectly harmless new field: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac RigidParsingBreaks.java && java RigidParsingBreaks` (JDK 17+).

Expected output:
```
Parsed V1 event fine: OrderPlacedEventV1[orderId=42, total=99.9]
CRASHED on a perfectly harmless new field: Unexpected field(s) in event: [orderId, total, discountCode]
```

Adding `discountCode` was a purely additive, backward-compatible change from the producer's point of view, but this consumer's strict validation treats any unrecognized field as an error.

### Level 2 — Intermediate

```java
// File: TolerantReader.java -- ignores unknown fields entirely, only reads what it needs.
import java.util.*;

public class TolerantReader {
    record OrderPlacedEventV1(int orderId, double total) {}

    static OrderPlacedEventV1 parseTolerant(Map<String, Object> raw) {
        // reads ONLY the fields it cares about -- anything else present is simply ignored, not an error
        int orderId = (int) raw.get("orderId");
        double total = (double) raw.get("total");
        return new OrderPlacedEventV1(orderId, total);
    }

    public static void main(String[] args) {
        Map<String, Object> v1Event = Map.of("orderId", 42, "total", 99.90);
        System.out.println("Parsed V1 event: " + parseTolerant(v1Event));

        Map<String, Object> v2Event = new HashMap<>(v1Event);
        v2Event.put("discountCode", "SAVE10");
        v2Event.put("giftWrapped", true); // even MULTIPLE new fields are fine
        System.out.println("Parsed V2 event (unknown fields ignored): " + parseTolerant(v2Event));

        System.out.println("No crash, no code change needed in this consumer when the producer adds new fields.");
    }
}
```

**How to run:** `javac TolerantReader.java && java TolerantReader` (JDK 17+).

Expected output:
```
Parsed V1 event: OrderPlacedEventV1[orderId=42, total=99.9]
Parsed V2 event (unknown fields ignored): OrderPlacedEventV1[orderId=42, total=99.9]
No crash, no code change needed in this consumer when the producer adds new fields.
```

The exact same `v2Event` that crashed `RigidParsingBreaks` parses cleanly here, because `parseTolerant` was written to read only what it needs and simply never looks at anything else.

### Level 3 — Advanced

```java
// File: ExplicitVersionDualFormat.java -- a genuinely BREAKING change (total's type
// changes from a plain double to a structured amount+currency object) handled with
// an explicit version field and dual-format parsing during the migration window.
import java.util.*;

public class ExplicitVersionDualFormat {
    record Money(double amount, String currency) {}
    record OrderPlacedEvent(int orderId, Money total, int schemaVersion) {}

    @SuppressWarnings("unchecked")
    static OrderPlacedEvent parseVersioned(Map<String, Object> raw) {
        int version = (int) raw.getOrDefault("schemaVersion", 1); // absent version field == implicitly V1
        int orderId = (int) raw.get("orderId");

        Money total = switch (version) {
            case 1 -> new Money((double) raw.get("total"), "USD"); // V1: bare double, ASSUME USD
            case 2 -> {
                Map<String, Object> totalObj = (Map<String, Object>) raw.get("total"); // V2: structured object
                yield new Money((double) totalObj.get("amount"), (String) totalObj.get("currency"));
            }
            default -> throw new RuntimeException("Unknown schemaVersion: " + version);
        };
        return new OrderPlacedEvent(orderId, total, version);
    }

    public static void main(String[] args) {
        // an OLD event, published before the schema change, with no schemaVersion field at all
        Map<String, Object> v1Event = Map.of("orderId", 42, "total", 99.90);

        // a NEW event, published after the breaking change, with an explicit version and structured total
        Map<String, Object> v2Event = Map.of(
            "orderId", 43, "schemaVersion", 2,
            "total", Map.of("amount", 45.00, "currency", "EUR"));

        System.out.println("Parsed old-format event: " + parseVersioned(v1Event));
        System.out.println("Parsed new-format event: " + parseVersioned(v2Event));
        System.out.println("Both formats coexist safely during the migration window -- neither consumer nor producer needed to upgrade in lockstep.");
    }
}
```

**How to run:** `javac ExplicitVersionDualFormat.java && java ExplicitVersionDualFormat` (JDK 17+).

Expected output:
```
Parsed old-format event: OrderPlacedEvent[orderId=42, total=Money[amount=99.9, currency=USD], schemaVersion=1]
Parsed new-format event: OrderPlacedEvent[orderId=43, total=Money[amount=45.0, currency=EUR], schemaVersion=2]
Both formats coexist safely during the migration window -- neither consumer nor producer needed to upgrade in lockstep.
```

## 6. Walkthrough

1. **Level 1** — `parseStrict` explicitly checks `raw.keySet()` against a fixed `allowedKeys` set and throws the instant anything extra is present; adding `discountCode`, a change that added information without removing or altering anything the consumer already relied on, still crashes this consumer entirely.
2. **Level 2, reading only what's needed** — `parseTolerant` never inspects `raw.keySet()` at all; it directly reads `raw.get("orderId")` and `raw.get("total")` and constructs the record from exactly those two values, regardless of what else the map might contain.
3. **Level 2, the resulting tolerance** — passing `v2Event`, which has two extra keys beyond what `v1Event` had, produces the identical `OrderPlacedEventV1` result as parsing `v1Event` itself — the new fields are present in the input but simply never examined, achieving forward compatibility with future additive changes for free.
4. **Level 3, a genuinely breaking change** — `total` changes shape entirely, from a bare `double` to a structured `{amount, currency}` object; no amount of "ignore unknown fields" tolerance can bridge this, because the *existing* field's type itself changed, not just the presence of new fields.
5. **Level 3, the explicit version field as the signal** — `parseVersioned` reads `schemaVersion` from the raw map, defaulting to `1` if absent (since events published before this field existed have no way to carry it) — this version number, not any structural inspection, is what tells the parser which branch of the `switch` to use.
6. **Level 3, the dual-format branch** — the `version == 1` case reads `total` as a bare double and wraps it in a `Money` object with an assumed `"USD"` currency (a deliberate, documented assumption bridging old data into the new internal representation); the `version == 2` case reads `total` as the new structured object directly.
7. **Level 3, the coexistence proof** — `main` parses both `v1Event` (no `schemaVersion` key at all, representing an event published before the migration) and `v2Event` (`schemaVersion: 2`, the new structured format) through the *same* `parseVersioned` method, and both produce correct, fully-populated `OrderPlacedEvent` records — demonstrating that during a migration window, a consumer updated to understand both formats can correctly process events from producers still on the old version and producers already on the new one, with neither side forced to upgrade at the exact same moment.

## 7. Gotchas & takeaways

> **Gotcha:** dual-format parsing code (the `switch` on `schemaVersion` in Level 3) is deliberately temporary scaffolding for a migration window, not a permanent feature — leaving support for arbitrarily old schema versions in place forever accumulates unbounded parsing complexity; plan an explicit deprecation point once you're confident no producer is still emitting the old format, and remove the old branch then.

- Additive changes to an event schema (new optional fields) are safe by default, provided consumers are written as tolerant readers that ignore fields they don't recognize rather than rejecting them.
- Strict, allow-list-based parsing turns every additive, backward-compatible producer change into a breaking change for consumers — the opposite of the intended safety.
- Genuinely breaking changes (a field's type or meaning changing) need an explicit version marker in the event itself, so a consumer can correctly branch its parsing logic per version.
- During a migration window, both old and new event formats coexist in the wild simultaneously, since producers and consumers are independently deployed and cannot be guaranteed to upgrade in lockstep — dual-format parsing bridges that window.
- Dual-format support is temporary scaffolding, not a permanent architecture; plan to retire old-version branches once the migration window has genuinely closed.
