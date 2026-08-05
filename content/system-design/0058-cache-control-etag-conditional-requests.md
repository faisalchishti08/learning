---
card: system-design
gi: 58
slug: cache-control-etag-conditional-requests
title: "Cache-Control, ETag & conditional requests"
---

## 1. What it is

**`Cache-Control`** is an HTTP response header that tells clients and intermediate caches (browsers, CDNs) how long a response may be reused before it must be revalidated. An **ETag** (entity tag) is a short, opaque identifier the server generates for a specific version of a resource. A **conditional request** is a follow-up request that asks the server "has this changed since I last saw it?" using the ETag, letting the server reply with a tiny "not modified" response instead of resending the whole body when nothing changed.

## 2. Why & when

`Cache-Control` and ETags exist to avoid two wasteful extremes: serving stale data forever (no caching at all would mean re-downloading everything on every request, which is also wasteful) and blindly trusting a cache for too long. Use `Cache-Control` to state how long a response is safe to reuse without even asking the server. Use ETags together with conditional requests for resources that change unpredictably, where you want the client to check in periodically but avoid re-downloading the full body if nothing actually changed.

## 3. Core concept

**`Cache-Control` directives:** `max-age=3600` tells the cache the response is fresh for 3600 seconds, and it may be reused with no request to the server at all during that window. `no-cache` (a confusing name) means the opposite of what it sounds like — it means "you may cache this, but you must revalidate with the server before reusing it every time." `no-store` means do not cache this at all, used for sensitive data.

**ETag generation:** the server computes an ETag from the current content — often a hash of the response body, or a version identifier — and sends it as an `ETag` header alongside the response. Two responses with identical content should produce the same ETag; any change in content changes the ETag.

**Conditional request flow (`If-None-Match`):** once a client holds a cached response with its ETag, the next time it needs to check freshness, it sends `If-None-Match: <etag>` in the request. If the server's current ETag for that resource still matches, it replies with **`304 Not Modified`** and an empty body — the client keeps using its cached copy. If the content changed, the server replies normally with **`200 OK`**, the new body, and a new ETag.

**Why this saves bandwidth:** a `304` response has no body at all, only headers — for a large resource (an image, a big JSON payload), this turns a full re-download into a near-free round trip whenever the content has not actually changed.

## 4. Diagram

```
First request:
  Client --GET /data----------------------> Server
  Client <--200 OK, body, ETag:"abc123"---- Server
  (client stores the response AND the ETag)

Later, cache entry needs revalidation:
  Client --GET /data, If-None-Match:"abc123"--> Server
                                                    |
                            content unchanged?  ----+---- content changed?
                                 |                              |
                                 v                              v
                   Client <--304 Not Modified--   Client <--200 OK, new body, ETag:"xyz789"--
                   (no body sent; client reuses     (client replaces its cached copy
                    its own cached copy)             and stores the new ETag)
```
*Caption: a conditional request either confirms the cached copy is still good (304, no body) or delivers the fresh version (200, full body).*

## 5. Runnable example

**Level 1 — Basic.** Compute an ETag for content and check whether a client's cached ETag still matches.

**Level 2 — Conditional request handling.** A server-side handler that returns 304 or 200 based on `If-None-Match`.

**Level 3 — Content change.** Show the ETag changing when content changes, forcing a full 200 response on the next conditional request.

```java
// CacheControlEtag.java
import java.util.HashMap;
import java.util.Map;

public class CacheControlEtag {

    static final Map<String, String> resources = new HashMap<>();

    // Level 1: ETag is a hash of the current content.
    static String computeEtag(String content) {
        return "\"" + Integer.toHexString(content.hashCode()) + "\"";
    }

    // Level 2 & 3: simulate a server handling a conditional GET.
    static class Response {
        int status; String body; String etag;
        Response(int status, String body, String etag) { this.status = status; this.body = body; this.etag = etag; }
    }

    static Response handleGet(String resourceKey, String clientEtag) {
        String content = resources.get(resourceKey);
        String currentEtag = computeEtag(content);
        if (clientEtag != null && clientEtag.equals(currentEtag)) {
            return new Response(304, null, currentEtag); // Not Modified: no body sent
        }
        return new Response(200, content, currentEtag); // full response
    }

    public static void main(String[] args) {
        resources.put("/data", "{\"count\":42}");

        // First request: no ETag held yet, always a full 200.
        Response first = handleGet("/data", null);
        System.out.println("first request: status=" + first.status + " body=" + first.body + " etag=" + first.etag);

        // Second request: client sends the ETag it stored; content has not changed.
        Response second = handleGet("/data", first.etag);
        System.out.println("second request (unchanged): status=" + second.status + " body=" + second.body);

        // Content changes on the server.
        resources.put("/data", "{\"count\":43}");
        Response third = handleGet("/data", first.etag); // client still holds the OLD etag
        System.out.println("third request (after change): status=" + third.status + " body=" + third.body + " etag=" + third.etag);
    }
}
```

**How to run:** save as `CacheControlEtag.java`, then run `java CacheControlEtag.java`.

## 6. Walkthrough

1. The first `handleGet("/data", null)` call has no `clientEtag` to compare, so it always returns `200` with the full body and the freshly computed `etag` for `"{\"count\":42}"`.
2. The client stores that ETag; the second `handleGet("/data", first.etag)` call recomputes `currentEtag` from the (unchanged) content, finds it equal to `clientEtag`, and returns `304` with a `null` body — the server confirms freshness without resending any data.
3. `resources.put("/data", "{\"count\":43}")` changes the underlying content, which changes what `computeEtag` produces for it.
4. The third call still sends the client's *old* ETag (`first.etag`, computed from `"count":42`), which no longer matches the server's newly computed ETag for `"count":43`, so the server returns `200` with the new body and a new ETag — the client must update both its cached body and its stored ETag.

## 7. Gotchas & takeaways

> Gotcha: `Cache-Control: no-cache` does not mean "do not cache" — that is `no-store`. `no-cache` means "cache it, but always revalidate before reuse," a common source of confusion when configuring headers.

- `max-age` avoids a network round trip entirely for its duration; ETags plus conditional requests still make a round trip, but skip resending the body when nothing changed — the two techniques solve different parts of the same problem and are commonly combined.
- ETags are only useful if the server can cheaply recompute them and if clients reliably send `If-None-Match` on revalidation; both browsers and CDNs handle this automatically once the headers are set correctly.
- Related concepts: [How a CDN works (edge PoPs)](0056-how-a-cdn-works-edge-pops.md) (TTL, set via `Cache-Control`, is what governs edge cache freshness), [Cache consistency & staleness](0054-cache-consistency-staleness.md) (the general staleness problem these headers help bound).
