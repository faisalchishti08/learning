---
card: system-design
gi: 208
slug: versioning-strategies
title: Versioning strategies
---

## 1. What it is

**API versioning** is a way to change an API's contract (adding, removing, or changing fields and endpoints) without breaking clients that are still using the previous contract. The three common strategies are **URI versioning** (`/v1/orders`), **header versioning** (a custom request header like `Api-Version: 2`), and **content negotiation versioning** (the `Accept` header, e.g. `Accept: application/vnd.myapi.v2+json`).

## 2. Why & when

Once an API has real clients, you cannot simply change a field's meaning or remove an endpoint — every client that has not updated its code will break. Versioning lets you introduce a new, changed contract (`v2`) while the old one (`v1`) keeps working exactly as before, giving clients time to migrate on their own schedule instead of all at once.

You need a versioning strategy the moment your API has any external consumer you do not fully control the deploy schedule of — which is most real APIs. Internal APIs where you control both client and server, and can deploy both together, can sometimes skip formal versioning in favor of careful backward-compatible changes, but any public or third-party-facing API needs one from day one.

## 3. Core concept

- **URI versioning (`/v1/orders`, `/v2/orders`).** The version is part of the URL itself. Simple to understand, easy to route (different code paths per version), and visible in every log line — but it means the same resource has different URLs across versions, which breaks the idea that a URL identifies one resource.
- **Header versioning (`Api-Version: 2`).** The URL stays `/orders` for every version; the version lives in a request header. This keeps URLs stable (better for the "URL identifies a resource" principle) but is less visible — you cannot tell a request's version just by looking at the URL in a browser or a log line without also capturing headers.
- **Content negotiation versioning (`Accept: application/vnd.myapi.v2+json`).** The most "correct" REST approach, using HTTP's built-in negotiation mechanism, but the least ergonomic in practice — most HTTP clients and tools do not make custom media types convenient to set.
- **Breaking vs. non-breaking changes.** Adding a new optional field is non-breaking (old clients ignore fields they do not recognize). Removing a field, renaming a field, or changing a field's type or meaning is breaking. Only breaking changes require a new version — do not bump the version for every change.
- **Deprecation policy.** A version is not removed the moment a new one ships. A sunset date (e.g. "v1 will stop working on 2027-01-01") is communicated in advance, often via a response header (`Deprecation: true`, `Sunset: <date>`), giving clients time to migrate.

## 4. Diagram

```
  URI VERSIONING              HEADER VERSIONING            CONTENT NEGOTIATION

  GET /v1/orders/5            GET /orders/5                GET /orders/5
                               Api-Version: 1               Accept: application/vnd.myapi.v1+json

  GET /v2/orders/5            GET /orders/5                GET /orders/5
  (different URL,             Api-Version: 2                Accept: application/vnd.myapi.v2+json
   different response         (same URL, different          (same URL, version encoded in
   shape)                      response shape based           the media type)
                                on header)

  Router picks code path by:  Router picks code path by:   Router picks code path by:
    URL prefix                  header value                  Accept header's version token
```
*Caption: all three strategies solve the same problem — routing a request to the correct version's handler — but differ in where the version signal lives.*

## 5. Runnable example

**Level 1 — Basic.** URI versioning: the version is parsed from the path, and two versions of the same resource return different shapes.

**Level 2 — Intermediate.** Header versioning: the same URL, but the response shape depends on a version header, defaulting sensibly when absent.

**Level 3 — Advanced.** A non-breaking change (a new optional field) served without a version bump, alongside a genuinely breaking change that does require one — showing the distinction in code.

```java
// VersioningDemo.java
import java.util.*;

public class VersioningDemo {

    // ---------- Level 1: URI versioning ----------
    static String handleUriVersioned(String path) {
        if (path.startsWith("/v1/orders/")) {
            String id = path.substring("/v1/orders/".length());
            return "v1 response: {id: \"" + id + "\", total: 42.00}"; // v1 shape: flat "total"
        }
        if (path.startsWith("/v2/orders/")) {
            String id = path.substring("/v2/orders/".length());
            // v2 shape: "total" replaced by a structured "amount" object - a BREAKING change.
            return "v2 response: {id: \"" + id + "\", amount: {value: 42.00, currency: \"USD\"}}";
        }
        return "404 Not Found";
    }

    // ---------- Level 2: header versioning, same URL for every version ----------
    static String handleHeaderVersioned(String path, String versionHeader) {
        if (!path.equals("/orders/5")) return "404 Not Found";
        String version = (versionHeader == null) ? "1" : versionHeader; // default to v1 if absent
        if (version.equals("2")) {
            return "response (Api-Version: 2): {id: \"5\", amount: {value: 42.00, currency: \"USD\"}}";
        }
        return "response (Api-Version: 1, default): {id: \"5\", total: 42.00}";
    }

    // ---------- Level 3: distinguish non-breaking vs breaking changes ----------
    record OrderV1(String id, double total) {}
    record OrderV1WithOptionalField(String id, double total, String giftMessage) {} // NON-breaking: new optional field
    record OrderV2(String id, Map<String, Object> amount) {} // BREAKING: total replaced entirely

    static String nonBreakingChange() {
        // Old clients parsing this ignore "giftMessage" - nothing breaks, no version bump needed.
        OrderV1WithOptionalField order = new OrderV1WithOptionalField("5", 42.00, null);
        return "same /v1/orders/5 endpoint, new OPTIONAL field added: " +
            "{id: \"" + order.id() + "\", total: " + order.total() +
            ", giftMessage: " + (order.giftMessage() == null ? "null" : order.giftMessage()) + "}" +
            "  <- old clients still work, they just ignore giftMessage";
    }

    static String breakingChange() {
        OrderV2 order = new OrderV2("5", Map.of("value", 42.00, "currency", "USD"));
        return "NEW /v2/orders/5 endpoint required: {id: \"" + order.id() + "\", amount: " + order.amount() + "}" +
            "  <- old clients expecting a numeric \"total\" field would break, so this MUST be a new version";
    }

    public static void main(String[] args) {
        System.out.println("Level 1 - URI versioning:");
        System.out.println("  " + handleUriVersioned("/v1/orders/5"));
        System.out.println("  " + handleUriVersioned("/v2/orders/5"));

        System.out.println("\nLevel 2 - header versioning, same URL, version from a header:");
        System.out.println("  no header (defaults to v1): " + handleHeaderVersioned("/orders/5", null));
        System.out.println("  Api-Version: 2              " + handleHeaderVersioned("/orders/5", "2"));

        System.out.println("\nLevel 3 - non-breaking change (no version bump) vs breaking change (needs one):");
        System.out.println("  " + nonBreakingChange());
        System.out.println("  " + breakingChange());
    }
}
```

**How to run:** `java VersioningDemo.java` (JDK 17+, single file, no dependencies).

## 6. Walkthrough

1. **Level 1:** `handleUriVersioned("/v1/orders/5")` checks the path prefix, finds `"/v1/orders/"`, and returns the v1 shape with a flat `total` field. `handleUriVersioned("/v2/orders/5")` matches the `"/v2/orders/"` prefix instead and returns a completely different shape, with `amount` as a nested object — two distinct URLs, two distinct code paths, no ambiguity about which version a given request used.
2. **Level 2:** `handleHeaderVersioned("/orders/5", null)` is called with no version header at all. The code treats a missing header as `version = "1"`, so it returns the v1-shaped response by default — a deliberate choice to keep existing clients working even if they never adopt the new header.
3. `handleHeaderVersioned("/orders/5", "2")` passes the same URL but with the header set to `"2"`. The `if (version.equals("2"))` branch now returns the v2 shape instead — the URL never changed, only the header did, which is the core tradeoff of this strategy: URLs stay stable, but you cannot tell the version from the URL alone.
4. **Level 3:** `nonBreakingChange()` adds `giftMessage` as a new field to the *same* v1 shape. The comment printed alongside it makes the point explicit: any client still parsing the old `OrderV1` shape simply never reads this new field — nothing breaks, so this ships on the existing `/v1/orders/5` endpoint with no version bump.
5. `breakingChange()` replaces the numeric `total` field with a structured `amount` object entirely — a client written against `OrderV1` would fail to find `total` at all. The comment explains why this specific change is exactly the kind that forces a new version (`/v2/orders/5`): it changes what already-shipped client code expects to find.

## 7. Gotchas & takeaways

> **Gotcha:** bumping the version for every small change (including non-breaking ones) creates version sprawl — clients end up unsure which version to target, and you end up maintaining many nearly-identical versions. Reserve a new version for genuinely breaking changes only, as shown in Level 3.

- Pick one strategy (URI, header, or content negotiation) for the whole API and stick to it — mixing strategies across endpoints confuses every consumer.
- URI versioning is the most common choice in practice because it is the most visible and the easiest to route, even though header versioning is arguably more "correct" for the idea that a URL identifies one resource.
- Always pair a new version with a clear deprecation timeline for the old one, communicated well in advance — a version that never gets deprecated defeats the purpose of having versions at all.
- Versioning decisions interact directly with [resource modeling](0206-resource-modeling-naming.md) (URI versioning changes the resource's path) and with [error contracts](0211-error-contracts-problem-json.md) (error shapes can also change between versions and need the same discipline).
