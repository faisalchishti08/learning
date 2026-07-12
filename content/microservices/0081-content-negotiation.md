---
card: microservices
gi: 81
slug: content-negotiation
title: "Content negotiation"
---

## 1. What it is

Content negotiation is the mechanism by which an HTTP client and server agree on the *representation* of a resource — its format (JSON, XML, Protobuf) and sometimes its language or version — without needing separate URIs for each variant. The client sends an `Accept` header listing the formats it can handle, in preference order (`Accept: application/json, application/xml;q=0.8`), and the server picks the best match it supports, returning that choice in the response's `Content-Type` header so the client knows exactly how to parse the body.

## 2. Why & when

Without content negotiation, supporting multiple response formats means either maintaining separate endpoints (`/orders/42.json`, `/orders/42.xml`) or forcing every client onto one fixed format, regardless of what's actually convenient for them. Content negotiation keeps the resource's identity — its URI — stable while letting the representation vary per request, which matters especially in a microservices ecosystem where different consumers (an internal service preferring compact Protobuf, an external partner needing JSON, a legacy client needing XML) can all hit the exact same endpoint and each receive the format they actually want.

Use content negotiation whenever an API needs to serve more than one representation format to different classes of client. For an internal microservices mesh with full control over every client, standardizing on a single format (usually JSON, or Protobuf for high-throughput internal calls) and skipping negotiation entirely is often simpler and perfectly reasonable — negotiation earns its complexity when real client diversity exists.

## 3. Core concept

The client states its preferences in the `Accept` header; the server picks the best supported match and confirms its choice in `Content-Type` — the same URI serves every format.

```
Request:  GET /orders/42
          Accept: application/xml, application/json;q=0.9

Server supports: [json, protobuf]  (no xml support)
                        |
                        v
Response: 200 OK
          Content-Type: application/json          <- best AVAILABLE match, not the client's top preference
          { "id": 42, "status": "PLACED" }
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client sends an Accept header listing preferred formats; the server matches against what it supports and responds with the best available format in Content-Type">
  <rect x="20" y="20" width="220" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="130" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Client requests</text>
  <text x="130" y="60" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">Accept: xml, json;q=0.9</text>

  <rect x="330" y="20" width="290" height="140" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Server supports: [json, protobuf]</text>
  <text x="475" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">xml preferred by client, NOT supported</text>
  <text x="475" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">json: 2nd preference, IS supported -&gt; chosen</text>
  <text x="475" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Response:</text>
  <text x="475" y="132" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">Content-Type: application/json</text>

  <line x1="240" y1="50" x2="330" y2="50" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The server negotiates down to the best mutually-acceptable format, not necessarily the client's first choice.

## 5. Runnable example

Scenario: a resource server that can produce two formats, first with no negotiation at all (always JSON, regardless of client preference), then negotiating based on a simple `Accept` header match, then extended to respect quality values (`q=`) so the server picks the client's *genuinely* most-preferred format among the ones it actually supports.

### Level 1 — Basic

```java
// File: NoNegotiation.java -- the server ALWAYS returns JSON, ignoring
// whatever the client's Accept header says it would prefer.
public class NoNegotiation {
    static String respond(String acceptHeader) {
        return "Content-Type: application/json\nBody: {\"id\":42,\"status\":\"PLACED\"}";
    }

    public static void main(String[] args) {
        System.out.println(respond("application/xml")); // client wanted XML, gets JSON regardless
    }
}
```

**How to run:** `javac NoNegotiation.java && java NoNegotiation` (JDK 17+).

Expected output:
```
Content-Type: application/json
Body: {"id":42,"status":"PLACED"}
```

### Level 2 — Intermediate

```java
// File: BasicNegotiation.java -- parse the Accept header's listed
// formats and pick the FIRST one the server actually supports.
import java.util.*;

public class BasicNegotiation {
    static List<String> serverSupports = List.of("application/json", "application/protobuf");

    static String respond(String acceptHeader) {
        String[] requested = acceptHeader.split(",\\s*");
        for (String type : requested) {
            String mediaType = type.split(";")[0].trim(); // strip any q= parameter for now
            if (serverSupports.contains(mediaType)) {
                return "Content-Type: " + mediaType + "\nBody: " + bodyFor(mediaType);
            }
        }
        return "406 Not Acceptable"; // no mutually supported format found
    }

    static String bodyFor(String mediaType) {
        return mediaType.equals("application/json") ? "{\"id\":42,\"status\":\"PLACED\"}" : "<protobuf bytes>";
    }

    public static void main(String[] args) {
        System.out.println("Request Accept: application/xml, application/json");
        System.out.println(respond("application/xml, application/json"));
    }
}
```

**How to run:** `javac BasicNegotiation.java && java BasicNegotiation` (JDK 17+).

Expected output:
```
Request Accept: application/xml, application/json
Content-Type: application/json
Body: {"id":42,"status":"PLACED"}
```

The client listed `xml` first, but the server doesn't support it, so negotiation falls through to `json`, the client's second choice and the best mutually-acceptable format.

### Level 3 — Advanced

```java
// File: QualityValueNegotiation.java -- respect q= quality values: the
// client's Accept header can express RELATIVE preference, not just
// listing order, and the server must honor the highest-q SUPPORTED type.
import java.util.*;

public class QualityValueNegotiation {
    record MediaTypePreference(String mediaType, double quality) {}
    static List<String> serverSupports = List.of("application/json", "application/protobuf");

    static List<MediaTypePreference> parseAccept(String acceptHeader) {
        List<MediaTypePreference> prefs = new ArrayList<>();
        for (String part : acceptHeader.split(",\\s*")) {
            String[] pieces = part.split(";");
            String mediaType = pieces[0].trim();
            double quality = 1.0; // default quality if no q= given
            for (int i = 1; i < pieces.length; i++) {
                if (pieces[i].trim().startsWith("q=")) {
                    quality = Double.parseDouble(pieces[i].trim().substring(2));
                }
            }
            prefs.add(new MediaTypePreference(mediaType, quality));
        }
        prefs.sort((a, b) -> Double.compare(b.quality(), a.quality())); // highest quality first
        return prefs;
    }

    static String respond(String acceptHeader) {
        List<MediaTypePreference> prefs = parseAccept(acceptHeader);
        for (MediaTypePreference p : prefs) {
            if (serverSupports.contains(p.mediaType())) {
                return "Content-Type: " + p.mediaType() + " (client q=" + p.quality() + ")";
            }
        }
        return "406 Not Acceptable";
    }

    public static void main(String[] args) {
        // client LISTS xml first, but explicitly ranks it lower via q= than json
        String accept = "application/xml;q=0.5, application/json;q=0.9, application/protobuf;q=0.7";
        System.out.println("Request Accept: " + accept);
        System.out.println(respond(accept));
    }
}
```

**How to run:** `javac QualityValueNegotiation.java && java QualityValueNegotiation` (JDK 17+).

Expected output:
```
Request Accept: application/xml;q=0.5, application/json;q=0.9, application/protobuf;q=0.7
Content-Type: application/json (client q=0.9)
```

Even though `protobuf` is also server-supported and `xml` appears first in the header, `json` wins because its `q=0.9` is the highest quality value among the client's stated preferences — not because of listing order.

## 6. Walkthrough

1. **Level 1** — `respond` ignores its `acceptHeader` parameter entirely and always returns the same JSON response. Calling it with `"application/xml"` still produces a JSON body — demonstrating the baseline problem content negotiation solves: a client's stated preference has no effect at all.
2. **Level 2 — matching against listing order** — `respond` splits the `Accept` header on commas, and for each requested type (in the order the client listed them), checks whether `serverSupports` contains it, returning the first match. `main` sends `"application/xml, application/json"` — `xml` is checked first but isn't in `serverSupports`, so the loop moves to `json`, which *is* supported, and that's what gets returned — matching the client's second choice since its first wasn't available.
3. **Level 3 — respecting quality values** — real `Accept` headers can attach a `q=` parameter to each type, expressing relative preference on a 0–1 scale, independent of listing order. `parseAccept` extracts each type's `quality` (defaulting to `1.0` if unspecified), then sorts the list *by quality, descending* — so listing order in the raw header string no longer determines processing order; the client's actual stated preference does.
4. **Tracing the sample header** — `"application/xml;q=0.5, application/json;q=0.9, application/protobuf;q=0.7"` parses into three preferences: `xml` at `0.5`, `json` at `0.9`, `protobuf` at `0.7`. After sorting by quality descending, the order becomes `json (0.9)`, `protobuf (0.7)`, `xml (0.5)` — note this is *not* the order the client wrote them in. `respond` then walks this sorted list and returns on the first server-supported match: `json` is checked first (now that it's sorted to the top) and *is* supported, so it's returned immediately — printed as `Content-Type: application/json (client q=0.9)`.
5. **Why this matters over Level 2's simpler approach** — if a client's header happened to list a lower-priority but still-acceptable type before a higher-priority one (exactly as this example does, with `xml` listed first but ranked lowest via `q=0.5`), Level 2's naive listing-order match would have incorrectly tried `xml` first. Level 3 correctly identifies that the client's *real* top preference among mutually acceptable options is `json`, honoring the semantic meaning of the `q=` parameter rather than just the raw text order it appears in.

## 7. Gotchas & takeaways

> **Gotcha:** if the server truly cannot produce any format the client accepts (no overlap between `Accept` and what's supported), the correct HTTP response is `406 Not Acceptable` — not a silent fallback to some default format the client never agreed to receive, which risks producing a body the client's own parser can't handle at all.

- The client states preferences via `Accept`; the server confirms its actual choice via `Content-Type` in the response — the resource's URI never needs to change per format.
- Quality values (`q=`) express genuine relative preference and must be honored over raw listing order — a naive first-match-in-header-order approach can pick the wrong format.
- Return `406 Not Acceptable` when no mutually supported format exists, rather than silently defaulting to something the client didn't ask for.
- For a fully internal microservices mesh where you control every client, standardizing on one format and skipping negotiation entirely is often simpler and avoids this complexity where it isn't earning its keep.
- See [JSON / Protobuf / Avro serialization](0085-json-protobuf-avro-serialization.md) for how the chosen format actually gets encoded once negotiation has settled on it.
