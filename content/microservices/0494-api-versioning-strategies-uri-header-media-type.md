---
card: microservices
gi: 494
slug: api-versioning-strategies-uri-header-media-type
title: "API versioning strategies (URI, header, media type)"
---

## 1. What it is

**API versioning** is how a service signals which version of its contract a given request or response uses, when a breaking change means old and new behavior must coexist for a transition period. The three common strategies differ in *where* the version is signaled: **URI versioning** puts it in the path (`/v2/orders`), **header versioning** puts it in a custom request header (`X-API-Version: 2`), and **media type versioning** puts it in the `Accept`/`Content-Type` header's value itself (`application/vnd.myapi.v2+json`).

## 2. Why & when

You need an explicit versioning strategy the moment an API's contract needs a breaking change while existing consumers are still depending on the old behavior:

- **Breaking changes can't simply replace the old behavior in place** — a field rename, a required-field addition, or a changed status code meaning would silently break every consumer still expecting the old contract, unless old and new versions can coexist during a migration window.
- **URI versioning is the most visible and simplest to reason about**, at the cost of "polluting" the resource path with something that isn't really part of the resource's identity — `/v2/orders/42` and `/v1/orders/42` look like different resources even though they represent the same underlying order.
- **Header and media-type versioning keep the URI itself stable** (`/orders/42` regardless of version), which is philosophically cleaner from a REST-purist standpoint, at the cost of being less visible — you can't just look at a URL in a browser and know which version you're hitting.
- **You commit to one primary strategy per API**, chosen early, since retrofitting a different versioning strategy onto an API that's already shipped and being consumed is itself a breaking change to how versioning is signaled.

## 3. Core concept

Think of a restaurant with a menu that changes over the years: URI versioning is like having a completely separate "2024 Menu" and "2025 Menu" printed as different documents, unambiguous but requiring the restaurant to print and hand out an obviously distinct one for each year; header versioning is like one menu that changes based on a discreet note the customer hands the waiter privately; media-type versioning is like ordering "the 2025-style burger" — the item's name itself encodes which version of the recipe you want.

Concretely:

1. **URI versioning**: the version number is part of the path itself — `GET /v1/orders/42` versus `GET /v2/orders/42` — routed by the server as effectively separate endpoint sets, often literally separate controller classes internally.
2. **Header versioning**: the path stays constant (`GET /orders/42`), and a custom header like `X-API-Version: 2` tells the server which contract version to apply — routing logic inspects this header to decide which handler or response shape to use.
3. **Media-type versioning**: the path stays constant, and the version is embedded in the `Accept` header's media type — `Accept: application/vnd.myapi.v2+json` — which is the most "correct" REST approach (content negotiation is what the `Accept` header exists for) but the least commonly understood by API consumers unfamiliar with the convention.
4. **All three achieve the same goal**: giving the server enough information, per request, to know which contract version the client expects, so old and new behavior can be served side by side during a transition.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three versioning strategies signaling the same version choice through different parts of the request: the URI path, a custom header, or the media type" >
  <rect x="20" y="20" width="600" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">URI: GET /v2/orders/42</text>

  <rect x="20" y="80" width="600" height="45" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Header: GET /orders/42, X-API-Version: 2</text>

  <rect x="20" y="140" width="600" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Media type: GET /orders/42, Accept: application/vnd.myapi.v2+json</text>
</svg>

The same version signal, expressed through three different parts of the same underlying request.

## 5. Runnable example

Scenario: a router that must dispatch to the correct handler version based on each of the three strategies. We start with basic URI-based routing, extend it to header-based routing on a stable URI, then handle the hard case: media-type-based routing where an unparseable or missing version defaults sensibly rather than failing the request outright.

### Level 1 — Basic

```java
// File: UriVersioningBasic.java -- models URI-based versioning: the
// version is PART OF THE PATH, and routing simply matches the prefix.
public class UriVersioningBasic {
    static String handleV1GetOrder(String orderId) {
        return "{\"id\":\"" + orderId + "\",\"amount\":79.50}"; // v1 shape: "amount"
    }

    static String handleV2GetOrder(String orderId) {
        return "{\"orderId\":\"" + orderId + "\",\"totalAmount\":79.50}"; // v2 shape: renamed fields
    }

    static String route(String path) {
        if (path.startsWith("/v1/orders/")) {
            String orderId = path.substring("/v1/orders/".length());
            return handleV1GetOrder(orderId);
        }
        if (path.startsWith("/v2/orders/")) {
            String orderId = path.substring("/v2/orders/".length());
            return handleV2GetOrder(orderId);
        }
        throw new RuntimeException("unknown route: " + path);
    }

    public static void main(String[] args) {
        System.out.println("[router] " + route("/v1/orders/42"));
        System.out.println("[router] " + route("/v2/orders/42"));
    }
}
```

How to run: `java UriVersioningBasic.java`

`route` inspects the raw path prefix to decide which handler to call — `/v1/orders/42` and `/v2/orders/42` are treated as entirely distinct routes despite representing the same underlying resource, with each handler producing its own contract-appropriate response shape.

### Level 2 — Intermediate

```java
// File: HeaderVersioningBasic.java -- the SAME two contract versions, now
// routed via a HEADER instead of the URI -- the path stays CONSTANT.
import java.util.*;

public class HeaderVersioningBasic {
    static String handleV1GetOrder(String orderId) {
        return "{\"id\":\"" + orderId + "\",\"amount\":79.50}";
    }

    static String handleV2GetOrder(String orderId) {
        return "{\"orderId\":\"" + orderId + "\",\"totalAmount\":79.50}";
    }

    static String route(String path, Map<String, String> headers) {
        if (!path.equals("/orders/42")) {
            throw new RuntimeException("unknown route: " + path);
        }
        String orderId = "42";
        String version = headers.getOrDefault("X-API-Version", "1"); // default to v1 if absent
        return version.equals("2") ? handleV2GetOrder(orderId) : handleV1GetOrder(orderId);
    }

    public static void main(String[] args) {
        System.out.println("[router] v1 (no header): " + route("/orders/42", Map.of()));
        System.out.println("[router] v2 (X-API-Version: 2): " + route("/orders/42", Map.of("X-API-Version", "2")));
    }
}
```

How to run: `java HeaderVersioningBasic.java`

`path` is identical (`/orders/42`) across both calls — the only thing that differs is the `headers` map, and `route` reads `X-API-Version` from it to decide which handler to dispatch to, defaulting to `"1"` when the header is entirely absent, which is what makes existing, unmodified clients keep receiving v1 behavior automatically.

### Level 3 — Advanced

```java
// File: MediaTypeVersioningWithFallback.java -- the SAME dual-version
// routing, now via MEDIA TYPE versioning, handling the
// PRODUCTION-FLAVORED hard case: the Accept header is MALFORMED or
// missing the version suffix entirely (a client using a generic HTTP tool
// that doesn't know about custom media types). Rather than failing the
// request outright, the router must FALL BACK to a sensible default
// version, while still correctly parsing well-formed version requests.
import java.util.*;
import java.util.regex.*;

public class MediaTypeVersioningWithFallback {
    static Pattern versionPattern = Pattern.compile("application/vnd\\.myapi\\.v(\\d+)\\+json");

    static String handleV1GetOrder(String orderId) {
        return "{\"id\":\"" + orderId + "\",\"amount\":79.50}";
    }

    static String handleV2GetOrder(String orderId) {
        return "{\"orderId\":\"" + orderId + "\",\"totalAmount\":79.50}";
    }

    static String parseVersionFromAcceptHeader(String acceptHeader) {
        if (acceptHeader == null) {
            System.out.println("[router] no Accept header at all -- falling back to default version 1");
            return "1";
        }
        Matcher matcher = versionPattern.matcher(acceptHeader);
        if (matcher.matches()) {
            return matcher.group(1);
        }
        System.out.println("[router] Accept header '" + acceptHeader + "' doesn't match the versioned media type pattern -- falling back to default version 1");
        return "1";
    }

    static String route(String orderId, String acceptHeader) {
        String version = parseVersionFromAcceptHeader(acceptHeader);
        return version.equals("2") ? handleV2GetOrder(orderId) : handleV1GetOrder(orderId);
    }

    public static void main(String[] args) {
        System.out.println("--- well-formed v2 media type ---");
        System.out.println("[router] " + route("42", "application/vnd.myapi.v2+json"));

        System.out.println();
        System.out.println("--- generic client, plain 'application/json', no version info at all ---");
        System.out.println("[router] " + route("42", "application/json"));

        System.out.println();
        System.out.println("--- no Accept header sent at all ---");
        System.out.println("[router] " + route("42", null));
    }
}
```

How to run: `java MediaTypeVersioningWithFallback.java`

`parseVersionFromAcceptHeader` first checks for a completely absent header, then tries to match `versionPattern` against whatever's present. The well-formed case matches the pattern and extracts `"2"` via the regex capture group. The generic `"application/json"` case doesn't match the versioned pattern at all — `matcher.matches()` is `false` — so it falls through to the same default-version-1 fallback as the entirely-absent-header case, ensuring a plain, version-unaware client still gets a valid, sensible response rather than an outright failure.

## 6. Walkthrough

Trace `MediaTypeVersioningWithFallback.main` in order. **First**, the well-formed case calls `route("42", "application/vnd.myapi.v2+json")`. Inside `parseVersionFromAcceptHeader`, the header is non-null, so `versionPattern.matcher(acceptHeader).matches()` runs — the string exactly matches the pattern `application/vnd\.myapi\.v(\d+)\+json`, capturing `"2"` — and that value is returned directly, with no fallback message printed.

**Next**, back in `route`, `version.equals("2")` is `true`, so `handleV2GetOrder("42")` runs, returning the v2-shaped JSON, which `main` prints.

**Then**, the generic-client case calls `route("42", "application/json")`. `parseVersionFromAcceptHeader` finds the header non-null, but `versionPattern.matcher("application/json").matches()` is `false`, since this string doesn't follow the versioned media-type convention at all — the fallback branch runs, printing an explicit message and returning `"1"` as the default.

**After that**, back in `route`, `"1".equals("2")` is `false`, so `handleV1GetOrder("42")` runs instead, returning the v1-shaped JSON — a generic client with no knowledge of this API's custom versioning convention still gets a complete, valid response rather than an error.

**Finally**, the no-header case calls `route("42", null)`. `parseVersionFromAcceptHeader`'s very first check, `if (acceptHeader == null)`, is `true`, so it immediately prints its own distinct fallback message and returns `"1"` without ever reaching the regex matching logic at all — `route` again dispatches to `handleV1GetOrder`, producing the same safe, default v1 response.

```
--- well-formed v2 media type ---
[router] {"orderId":"42","totalAmount":79.50}

--- generic client, plain 'application/json', no version info at all ---
[router] Accept header 'application/json' doesn't match the versioned media type pattern -- falling back to default version 1
[router] {"id":"42","amount":79.50}

--- no Accept header sent at all ---
[router] no Accept header at all -- falling back to default version 1
[router] {"id":"42","amount":79.50}
```

## 7. Gotchas & takeaways

> A versioning strategy that fails the request outright when a client doesn't (or can't) specify a version is unnecessarily hostile to simple or generic clients — falling back to a sensible, documented default version, as shown here, keeps the API usable by tools that were never built with your specific versioning convention in mind.
- URI versioning is the easiest for consumers to understand and debug (the version is right there in every log line and every browser address bar), which is why it remains the most common choice despite being the least "pure" from a strict REST perspective.
- Whichever strategy you choose, document the default behavior explicitly for requests that don't specify a version — silently guessing, or worse, silently serving a breaking new version to an old, unversioned client, causes exactly the disruption versioning exists to prevent.
- Combine explicit versioning with [backward and forward compatibility](0495-backward-forward-compatibility.md) practices and a clear [deprecation and sunset policy](0498-deprecation-sunset-policies.md) — versioning alone doesn't tell consumers *when* an old version will stop being supported.
- Pick one primary strategy and apply it consistently across an entire API surface — mixing URI versioning for some endpoints and header versioning for others creates confusion with no corresponding benefit.
