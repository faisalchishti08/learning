---
card: microservices
gi: 57
slug: anti-corruption-layer-acl
title: "Anti-corruption layer (ACL)"
---

## 1. What it is

This tutorial goes deeper on the **Anticorruption Layer (ACL)** pattern already introduced in [bounded context](0049-bounded-context.md)'s overview, with a fresh, more elaborate scenario: an ACL is a dedicated translation layer, sitting entirely on the downstream (consuming) side of a relationship with an upstream system, whose sole job is converting the upstream's model, vocabulary, and quirks into the downstream context's own clean, purpose-built model — protecting the downstream domain from being shaped or "corrupted" by decisions the upstream system made for its own, different reasons.

## 2. Why & when

Integrating directly with an upstream system's model — especially a legacy system, a third-party API, or any system you don't control — means inheriting that system's own historical decisions, quirks, and vocabulary directly into your own domain, whether or not they make sense there. An ACL exists specifically to draw a hard line: the upstream's messiness stays contained entirely within the translation layer, and everything on the downstream side works only with clean, purpose-built domain concepts.

Build a dedicated ACL when integrating with a system whose model is genuinely messy, legacy, foreign to your domain's own vocabulary, or likely to change in ways outside your control — a third-party shipping carrier's API with its own field-naming conventions and status codes is a common, concrete example. Skip the extra translation layer for a well-designed, stable upstream you have genuine influence over, where a [Conformist](0060-conformist-relationship.md) relationship is simpler and sufficient.

## 3. Core concept

The ACL sits as a distinct architectural layer between the upstream integration and the downstream domain:

```
Upstream (ShippingCarrierAPI)     Anticorruption Layer          Downstream domain
  raw response: { "trk_no": "...",   ShippingTranslator          Shipment (clean domain model)
                   "stat": "IT",            |
                   "est_dt": "..." }  ------+------------->     status: IN_TRANSIT (an enum, not a raw code)
```

Downstream domain code, including any domain services or aggregates that need shipping information, depends only on the clean `Shipment` model — never on the raw upstream response shape.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A raw upstream shipping API response passes through a dedicated anticorruption layer that translates it into a clean domain model before downstream code ever sees it">
  <rect x="30" y="55" width="170" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="115" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ShippingCarrierAPI</text>
  <text x="115" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">raw, messy fields</text>

  <rect x="250" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ShippingTranslator</text>
  <text x="325" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">the ONLY messy code</text>

  <rect x="450" y="55" width="160" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Shipment (clean)</text>
  <text x="530" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">downstream domain model</text>

  <line x1="200" y1="85" x2="250" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a57)"/>
  <line x1="400" y1="85" x2="450" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a57)"/>
  <defs><marker id="a57" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The translator is the sole boundary containing the upstream's messiness; everything past it is clean domain model.

## 5. Runnable example

Scenario: integrating with a third-party shipping carrier's messy API, first without any ACL (upstream messiness leaking into domain logic), then with a dedicated ACL, then extended to show the ACL absorbing a second, differently-shaped carrier without touching downstream code at all.

### Level 1 — Basic

```java
// File: NoAcl.java -- downstream domain logic works DIRECTLY with the
// upstream carrier's raw, messy response shape.
import java.util.*;

public class NoAcl {
    // the UPSTREAM carrier's raw response shape -- abbreviated field names, cryptic codes
    static Map<String, String> carrierApiResponse() {
        return Map.of("trk_no", "TRACK123", "stat", "IT", "est_dt", "2026-08-01");
    }

    // downstream domain logic, POLLUTED with upstream's raw field names and codes
    static String describeShipment() {
        Map<String, String> response = carrierApiResponse();
        String statusText = response.get("stat").equals("IT") ? "In Transit" : "Unknown"; // must know the carrier's OWN codes
        return "Tracking " + response.get("trk_no") + ": " + statusText + ", est. " + response.get("est_dt");
    }

    public static void main(String[] args) {
        System.out.println(describeShipment());
    }
}
```

**How to run:** `javac NoAcl.java && java NoAcl` (JDK 17+).

Expected output:
```
Tracking TRACK123: In Transit, est. 2026-08-01
```

`describeShipment`, meant to be downstream domain logic, is directly coupled to the carrier's specific field names (`"trk_no"`, `"stat"`, `"est_dt"`) and cryptic status codes (`"IT"`). Any downstream code needing shipment info would need to repeat this same translation knowledge.

### Level 2 — Intermediate

```java
// File: DedicatedAcl.java -- a SINGLE translator class isolates ALL
// upstream messiness; downstream works with a CLEAN model.
import java.util.*;

public class DedicatedAcl {
    static Map<String, String> carrierApiResponse() {
        return Map.of("trk_no", "TRACK123", "stat", "IT", "est_dt", "2026-08-01");
    }

    enum ShipmentStatus { IN_TRANSIT, DELIVERED, UNKNOWN } // downstream's OWN clean vocabulary
    record Shipment(String trackingNumber, ShipmentStatus status, String estimatedDate) { } // downstream's OWN clean model

    // the ANTICORRUPTION LAYER -- the ONLY code that knows the carrier's raw field names and codes
    static class ShippingTranslator {
        Shipment translate(Map<String, String> rawResponse) {
            ShipmentStatus status = switch (rawResponse.get("stat")) {
                case "IT" -> ShipmentStatus.IN_TRANSIT;
                case "DL" -> ShipmentStatus.DELIVERED;
                default -> ShipmentStatus.UNKNOWN;
            };
            return new Shipment(rawResponse.get("trk_no"), status, rawResponse.get("est_dt"));
        }
    }

    // downstream domain logic depends ONLY on the clean Shipment model
    static String describeShipment(Shipment shipment) {
        return "Tracking " + shipment.trackingNumber() + ": " + shipment.status() + ", est. " + shipment.estimatedDate();
    }

    public static void main(String[] args) {
        ShippingTranslator translator = new ShippingTranslator();
        Shipment shipment = translator.translate(carrierApiResponse());
        System.out.println(describeShipment(shipment));
    }
}
```

**How to run:** `javac DedicatedAcl.java && java DedicatedAcl` (JDK 17+).

Expected output:
```
Tracking TRACK123: IN_TRANSIT, est. 2026-08-01
```

`describeShipment` now depends only on the clean `Shipment` record and the `ShipmentStatus` enum — no raw field names, no carrier-specific codes. `ShippingTranslator` is the single, isolated place that knows about `"trk_no"`, `"stat"`, and what `"IT"` actually means.

### Level 3 — Advanced

```java
// File: SecondCarrierAbsorbed.java -- integrate a SECOND carrier with a
// COMPLETELY DIFFERENT raw shape; downstream domain logic NEVER changes.
import java.util.*;

public class SecondCarrierAbsorbed {
    enum ShipmentStatus { IN_TRANSIT, DELIVERED, UNKNOWN }
    record Shipment(String trackingNumber, ShipmentStatus status, String estimatedDate) { } // UNCHANGED clean model

    interface CarrierTranslator { Shipment translate(); }

    // Carrier A's translator (same as Level 2)
    static class CarrierATranslator implements CarrierTranslator {
        Map<String, String> rawResponse = Map.of("trk_no", "TRACK123", "stat", "IT", "est_dt", "2026-08-01");
        public Shipment translate() {
            ShipmentStatus status = switch (rawResponse.get("stat")) {
                case "IT" -> ShipmentStatus.IN_TRANSIT; case "DL" -> ShipmentStatus.DELIVERED; default -> ShipmentStatus.UNKNOWN;
            };
            return new Shipment(rawResponse.get("trk_no"), status, rawResponse.get("est_dt"));
        }
    }

    // Carrier B's translator -- a COMPLETELY DIFFERENT raw shape (nested XML-style structure, modeled here as nested maps)
    static class CarrierBTranslator implements CarrierTranslator {
        Map<String, Object> rawResponse = Map.of(
            "shipment", Map.of("id", "SHIP789", "currentState", "delivered", "arrivalEstimate", "2026-08-02")
        );
        @SuppressWarnings("unchecked")
        public Shipment translate() {
            Map<String, String> shipmentData = (Map<String, String>) rawResponse.get("shipment");
            ShipmentStatus status = switch (shipmentData.get("currentState")) {
                case "delivered" -> ShipmentStatus.DELIVERED; case "in_transit" -> ShipmentStatus.IN_TRANSIT; default -> ShipmentStatus.UNKNOWN;
            };
            return new Shipment(shipmentData.get("id"), status, shipmentData.get("arrivalEstimate"));
        }
    }

    // downstream domain logic, UNCHANGED from Level 2 -- works with EITHER carrier identically
    static String describeShipment(Shipment shipment) {
        return "Tracking " + shipment.trackingNumber() + ": " + shipment.status() + ", est. " + shipment.estimatedDate();
    }

    public static void main(String[] args) {
        System.out.println(describeShipment(new CarrierATranslator().translate()));
        System.out.println(describeShipment(new CarrierBTranslator().translate())); // COMPLETELY different upstream shape, SAME downstream code
    }
}
```

**How to run:** `javac SecondCarrierAbsorbed.java && java SecondCarrierAbsorbed` (JDK 17+).

Expected output:
```
Tracking TRACK123: IN_TRANSIT, est. 2026-08-01
Tracking SHIP789: DELIVERED, est. 2026-08-02
```

The production-flavored payoff: Carrier B's raw response is structurally nothing like Carrier A's — nested maps instead of flat fields, entirely different field names and status vocabulary (`"delivered"` instead of `"DL"`). Yet `describeShipment`, downstream domain logic, is called identically for both and produces correctly formatted output either way — because each carrier's own translator absorbs its own specific messiness, converging on the exact same clean `Shipment` model downstream code always relies on.

## 6. Walkthrough

1. `new CarrierATranslator().translate()` reads `rawResponse.get("stat")`, matches `"IT"` in its `switch`, and constructs `new Shipment("TRACK123", IN_TRANSIT, "2026-08-01")` — this translator's own knowledge of Carrier A's flat field structure and status codes is used exactly once, here.
2. `describeShipment` receives this `Shipment` and formats it, having no idea it originated from a flat, `"stat"`-coded response.
3. `new CarrierBTranslator().translate()` reads a completely different raw structure: `rawResponse.get("shipment")` first extracts a nested map, then reads `"currentState"` (not `"stat"`) and matches `"delivered"` (not `"DL"`) in its own separate `switch`, constructing `new Shipment("SHIP789", DELIVERED, "2026-08-02")`.
4. `describeShipment` is called again, with this second `Shipment` object — the exact same method, the exact same code path as step 2, producing correctly formatted output despite the wildly different upstream shape that ultimately fed into it.
5. Neither call to `describeShipment` required any change to its own source code to handle the second carrier — all of Carrier B's structural differences were fully absorbed inside `CarrierBTranslator`, exactly matching the anticorruption layer's promise: downstream domain logic stays completely insulated from however many differently-shaped upstream integrations a system ends up needing.

```
CarrierA raw: {trk_no, stat: "IT", est_dt}          -> CarrierATranslator -> Shipment(IN_TRANSIT)
CarrierB raw: {shipment: {id, currentState: "delivered", arrivalEstimate}} -> CarrierBTranslator -> Shipment(DELIVERED)
        |                                                       |
        +----------------------- BOTH converge on -------------+
                                    |
                        describeShipment(Shipment)  <- IDENTICAL code, both carriers
```

## 7. Gotchas & takeaways

> **Gotcha:** an anticorruption layer must fully own its translation responsibility — if downstream code ever reaches back through the ACL to peek at raw upstream fields "just this once, for a quick fix," the protective boundary is broken, and the upstream's messiness begins leaking into the downstream domain exactly the way the ACL was built to prevent. Treat any such shortcut as a signal the ACL's clean model is missing something it should properly expose instead.

- An anticorruption layer is a dedicated translation boundary that converts an upstream system's model into the downstream domain's own clean model, containing all of the upstream's messiness within the translator itself.
- Multiple, structurally different upstream integrations (like two carriers with entirely different response shapes) can each have their own translator, all converging on the same clean downstream model — downstream code never needs to know how many, or how differently-shaped, the upstream sources actually are.
- Build a dedicated ACL specifically for messy, legacy, foreign, or unstable upstream dependencies — the translation effort earns its cost by fully insulating your domain from another system's design decisions.
- Never let downstream code bypass the ACL to reach raw upstream data directly, even for a "quick fix" — that shortcut reintroduces exactly the coupling and corruption risk the pattern exists to eliminate.
