---
card: spring-security
gi: 82
slug: cache-control-headers
title: Cache control headers
---

## 1. What it is

**Cache-Control** is an HTTP header that tells caches — the browser's own disk cache, its back/forward cache, and any shared proxy or CDN sitting between the browser and your server — how, and whether, a response may be stored and reused for a later request. Spring Security's header-writing support sets a deliberately restrictive `Cache-Control` value on every response by default: `no-cache, no-store, max-age=0, must-revalidate`, accompanied by the older `Pragma: no-cache` and `Expires: 0` headers for HTTP/1.0-era caches that don't understand `Cache-Control` at all.

That default is not an accident or leftover boilerplate — it exists specifically so that a page rendered for one authenticated user (an account balance, an admin dashboard, a private message thread) is never stored by an intermediate cache or the browser's own disk cache and later handed to a *different* person who happens to share that proxy or that machine. The `headers().cacheControl()` DSL is the escape hatch: it lets an application override this blanket restrictive policy for responses that genuinely are safe to cache, such as versioned, content-hashed static assets.

## 2. Why & when

Shared machines and shared network paths are everywhere: a library computer, an office workstation used across shifts, a corporate proxy sitting between hundreds of employees and the internet, a CDN edge node serving thousands of unrelated users. If a server response carried no caching directives at all, browsers and intermediate caches would be free to guess — and historically, many guessed "yes, cache this," including responses containing another user's private data. The browser's **back/forward cache (bfcache)** compounds the problem: press *back* after logging out, and without `no-store` the browser may resurrect the exact rendered page — balance, messages and all — straight from memory, with no request to the server at all.

Reach for the restrictive default (i.e., leave it alone) for essentially every dynamic, authenticated response your application produces: account pages, API responses carrying personal data, anything rendered per-session. Reach for `headers().cacheControl()` to override it when:

- Serving genuinely public, cacheable static assets — a logo, a hashed/fingerprinted JS or CSS bundle (`app.a1b2c3.js`) — where being cached aggressively by a CDN or the browser is exactly what you want, and there's no per-user data to leak.
- Serving public API responses that are identical for every caller (a public product catalog, a status page), where recomputing the same response on every request wastes server resources for no security benefit.
- Building a hybrid application where some paths are private (leave the default) and others are public (add a per-path override) — normally done with a path-scoped `RequestMatcher` so the restrictive default stays in force everywhere it isn't explicitly relaxed.

## 3. Core concept

```
 Default (Spring Security's HeaderWriter, applied to EVERY response unless overridden):
   Cache-Control: no-cache, no-store, max-age=0, must-revalidate
   Pragma: no-cache      -- for very old HTTP/1.0 caches
   Expires: 0            -- for caches that only understand Expires

 "no-store" is the strongest directive: a cache (browser disk cache, shared proxy, CDN)
 must not persist ANY part of this response, full stop -- not "revalidate before reuse,"
 just never store it in the first place.

 headers().cacheControl() DSL: lets an app REPLACE the default for matched paths, e.g.:
   Cache-Control: public, max-age=31536000, immutable
   -- appropriate ONLY for content that never changes for a given URL (hashed filenames)
      or that carries no per-user/per-session data at all.
```

The rule of thumb: restrictive by default, because the cost of under-caching is a few wasted milliseconds, while the cost of over-caching a sensitive page is another person's data on someone else's screen.

## 4. Diagram

<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A browser sends two kinds of requests through a shared proxy to an origin server the account page response carries Cache-Control no-store so the proxy forwards it without storing anything shown with a red crossed out cache icon while the static asset response carries Cache-Control public max-age so the proxy stores it and serves the second request directly from its own cache without ever reaching the origin server again shown with a green checkmark">
  <rect x="20" y="30" width="130" height="260" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="55" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Browser</text>

  <rect x="280" y="30" width="150" height="260" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="355" y="55" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Shared proxy</text>

  <rect x="550" y="30" width="130" height="260" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="615" y="55" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Origin server</text>

  <text x="215" y="95" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET /account</text>
  <line x1="150" y1="105" x2="280" y2="105" stroke="#f85149" stroke-width="2" marker-end="url(#arrowRed)"/>
  <line x1="430" y1="105" x2="550" y2="105" stroke="#f85149" stroke-width="2" marker-end="url(#arrowRed)"/>
  <text x="500" y="95" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">forwarded, NOT stored</text>
  <text x="355" y="130" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Cache-Control: no-store -&gt; cache SKIPPED</text>
  <text x="355" y="150" fill="#f85149" font-size="16" text-anchor="middle" font-family="sans-serif">X</text>

  <text x="215" y="205" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET /static/logo.png</text>
  <line x1="150" y1="215" x2="280" y2="215" stroke="#3fb950" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <line x1="430" y1="215" x2="550" y2="215" stroke="#3fb950" stroke-width="2" marker-end="url(#arrowGreen)" stroke-dasharray="4,3"/>
  <text x="500" y="205" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">only on first request</text>
  <text x="355" y="240" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">Cache-Control: public, max-age -&gt; STORED</text>
  <text x="355" y="260" fill="#3fb950" font-size="16" text-anchor="middle" font-family="sans-serif">OK</text>
  <line x1="280" y1="272" x2="150" y2="272" stroke="#3fb950" stroke-width="2" marker-end="url(#arrowGreen)"/>
  <text x="215" y="288" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">2nd request: served from proxy cache</text>

  <defs>
    <marker id="arrowRed" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="arrowGreen" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The restrictive `no-store` response always travels all the way to the origin server; the `public, max-age` response is cached at the proxy after its first trip and served locally on every request after that.

## 5. Runnable example

The scenario: a single `CacheControlPolicy` decides what `Cache-Control` value a response gets, and a `SharedProxyCache` models a proxy sitting between multiple users and the origin. Level 1 applies Spring Security's restrictive default to a single response. Level 2 shows what a shared proxy does with that default versus with no header at all — including one user's sensitive data leaking to another user when the header is missing. Level 3 adds a path-based override so a genuinely public static asset can be cached, while the sensitive route keeps the restrictive default.

### Level 1 — Basic

```java
import java.util.*;

public class CacheControlLevel1 {

    record HttpResponse(int status, Map<String, String> headers, String body) {}

    // Mirrors Spring Security's default HeaderWriter behavior: every response gets
    // restrictive Cache-Control headers, whether the resource is sensitive or not.
    static HttpResponse applyDefaultSecurityHeaders(String body) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Cache-Control", "no-cache, no-store, max-age=0, must-revalidate");
        headers.put("Pragma", "no-cache");
        headers.put("Expires", "0");
        return new HttpResponse(200, headers, body);
    }

    public static void main(String[] args) {
        HttpResponse accountPage = applyDefaultSecurityHeaders("Balance: $12,345.67");
        System.out.println("Status: " + accountPage.status());
        accountPage.headers().forEach((k, v) -> System.out.println(k + ": " + v));
        System.out.println("Body: " + accountPage.body());
    }
}
```

**How to run:** save as `CacheControlLevel1.java`, run `java CacheControlLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Status: 200
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Pragma: no-cache
Expires: 0
Body: Balance: $12,345.67
```

Every response, sensitive or not, gets the same restrictive headers here — that's exactly Spring Security's out-of-the-box behavior, and on its own it's already the safe choice for a page like this.

### Level 2 — Intermediate

```java
import java.util.*;

public class CacheControlLevel2 {

    record HttpResponse(int status, Map<String, String> headers, String body) {}

    static HttpResponse applyDefaultSecurityHeaders(String body) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Cache-Control", "no-cache, no-store, max-age=0, must-revalidate");
        headers.put("Pragma", "no-cache");
        headers.put("Expires", "0");
        return new HttpResponse(200, headers, body);
    }

    // A response with NO Cache-Control header at all -- what a naive endpoint would produce
    // if Spring Security's header writer were disabled.
    static HttpResponse rawResponseNoHeaders(String body) {
        return new HttpResponse(200, new LinkedHashMap<>(), body);
    }

    // Simulates a shared proxy (a corporate proxy, or a CDN edge) sitting between many
    // users and the origin server -- exactly the "shared machine" scenario Cache-Control
    // is designed to protect against.
    static class SharedProxyCache {
        private final Map<String, String> store = new HashMap<>();

        String fetch(String url, java.util.function.Supplier<HttpResponse> origin) {
            if (store.containsKey(url)) {
                return "[CACHE HIT] " + store.get(url);
            }
            HttpResponse response = origin.get();
            String cacheControl = response.headers().getOrDefault("Cache-Control", "");
            if (!cacheControl.contains("no-store")) {
                store.put(url, response.body()); // proxy is ALLOWED to cache this response
            }
            return "[ORIGIN] " + response.body();
        }
    }

    public static void main(String[] args) {
        SharedProxyCache proxy = new SharedProxyCache();
        System.out.println("-- With Spring Security's default headers (no-store present) --");
        System.out.println("Alice requests /account: "
                + proxy.fetch("/account", () -> applyDefaultSecurityHeaders("Alice's balance: $12,345.67")));
        System.out.println("Bob requests /account:   "
                + proxy.fetch("/account", () -> applyDefaultSecurityHeaders("Bob's balance: $500.00")));

        SharedProxyCache insecureProxy = new SharedProxyCache();
        System.out.println();
        System.out.println("-- Without any Cache-Control header (headers disabled) --");
        System.out.println("Alice requests /account: "
                + insecureProxy.fetch("/account", () -> rawResponseNoHeaders("Alice's balance: $12,345.67")));
        System.out.println("Bob requests /account:   "
                + insecureProxy.fetch("/account", () -> rawResponseNoHeaders("Bob's balance: $500.00")));
    }
}
```

**How to run:** save as `CacheControlLevel2.java`, run `java CacheControlLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
-- With Spring Security's default headers (no-store present) --
Alice requests /account: [ORIGIN] Alice's balance: $12,345.67
Bob requests /account:   [ORIGIN] Bob's balance: $500.00

-- Without any Cache-Control header (headers disabled) --
Alice requests /account: [ORIGIN] Alice's balance: $12,345.67
Bob requests /account:   [CACHE HIT] Alice's balance: $12,345.67
```

With `no-store` present, every request for `/account` reaches the origin fresh — Bob correctly sees his own balance. Without any header at all, the proxy is free to store Alice's response, and Bob's later request for the same URL is served her cached body instead of his own: exactly the cross-user data leak the restrictive default exists to prevent.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.Supplier;

public class CacheControlLevel3 {

    record HttpResponse(int status, Map<String, String> headers, String body) {}

    // Mirrors overriding headers().cacheControl(): a ROUTE-AWARE policy decides the
    // Cache-Control value per request path, instead of one blanket value for every response.
    static class CacheControlPolicy {
        private final Map<String, String> overridesByPathPrefix = new LinkedHashMap<>();
        private final String defaultPolicy = "no-cache, no-store, max-age=0, must-revalidate";

        void allowPublicCaching(String pathPrefix, int maxAgeSeconds) {
            overridesByPathPrefix.put(pathPrefix, "public, max-age=" + maxAgeSeconds + ", immutable");
        }

        String resolve(String path) {
            for (var entry : overridesByPathPrefix.entrySet()) {
                if (path.startsWith(entry.getKey())) return entry.getValue();
            }
            return defaultPolicy; // restrictive by default -- matches Spring Security's out-of-the-box behavior
        }
    }

    static HttpResponse applyHeaders(CacheControlPolicy policy, String path, String body) {
        Map<String, String> headers = new LinkedHashMap<>();
        String cacheControl = policy.resolve(path);
        headers.put("Cache-Control", cacheControl);
        if (cacheControl.contains("no-store")) {
            headers.put("Pragma", "no-cache");
            headers.put("Expires", "0");
        }
        return new HttpResponse(200, headers, body);
    }

    static class SharedProxyCache {
        private final Map<String, String> store = new HashMap<>();

        String fetch(String url, Supplier<HttpResponse> origin) {
            if (store.containsKey(url)) return "[CACHE HIT] " + store.get(url);
            HttpResponse response = origin.get();
            String cc = response.headers().getOrDefault("Cache-Control", "");
            if (cc.contains("public") && cc.contains("max-age")) {
                store.put(url, response.body());
            }
            return "[ORIGIN] " + response.body();
        }
    }

    public static void main(String[] args) {
        CacheControlPolicy policy = new CacheControlPolicy();
        policy.allowPublicCaching("/static/", 31536000); // override: 1 year, safe for hashed asset filenames

        HttpResponse account = applyHeaders(policy, "/account", "Alice's balance: $12,345.67");
        System.out.println("/account Cache-Control: " + account.headers().get("Cache-Control"));

        HttpResponse logo = applyHeaders(policy, "/static/logo-8f3a1c.png", "<png bytes>");
        System.out.println("/static/logo-8f3a1c.png Cache-Control: " + logo.headers().get("Cache-Control"));

        SharedProxyCache proxy = new SharedProxyCache();
        System.out.println();
        System.out.println("First user fetches /account:  "
                + proxy.fetch("/account", () -> applyHeaders(policy, "/account", "Alice's balance: $12,345.67")));
        System.out.println("Second user fetches /account: "
                + proxy.fetch("/account", () -> applyHeaders(policy, "/account", "Bob's balance: $500.00")));

        System.out.println("First user fetches /static/logo-8f3a1c.png:  "
                + proxy.fetch("/static/logo-8f3a1c.png", () -> applyHeaders(policy, "/static/logo-8f3a1c.png", "<png bytes>")));
        System.out.println("Second user fetches /static/logo-8f3a1c.png: "
                + proxy.fetch("/static/logo-8f3a1c.png", () -> applyHeaders(policy, "/static/logo-8f3a1c.png", "<png bytes>")));
    }
}
```

**How to run:** save as `CacheControlLevel3.java`, run `java CacheControlLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
/account Cache-Control: no-cache, no-store, max-age=0, must-revalidate
/static/logo-8f3a1c.png Cache-Control: public, max-age=31536000, immutable

First user fetches /account:  [ORIGIN] Alice's balance: $12,345.67
Second user fetches /account: [ORIGIN] Bob's balance: $500.00
First user fetches /static/logo-8f3a1c.png:  [ORIGIN] <png bytes>
Second user fetches /static/logo-8f3a1c.png: [CACHE HIT] <png bytes>
```

`/account` keeps the restrictive default because its path never matches the `/static/` prefix registered with `allowPublicCaching`, so every request for it reaches the origin. `/static/logo-8f3a1c.png` gets the overridden public policy: the first request is stored by the proxy, and the second is served straight from the cache without touching the origin at all — the override is scoped to exactly the paths that are safe to relax.

## 6. Walkthrough

Trace two requests through the Level 3 `CacheControlPolicy` and `SharedProxyCache`, showing the concrete HTTP exchange each produces.

**Request 1 — the sensitive page:**
```
GET /account HTTP/1.1
Host: api.example.com
Cookie: SESSION=abc123
```

**Response:**
```
HTTP/1.1 200 OK
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Pragma: no-cache
Expires: 0

Alice's balance: $12,345.67
```

1. `applyHeaders(policy, "/account", ...)` calls `policy.resolve("/account")`. The loop over `overridesByPathPrefix` checks whether `/account` starts with `/static/` — it doesn't — so no override applies and `resolve` falls through to `defaultPolicy`, the restrictive string.
2. Because that string contains `"no-store"`, `applyHeaders` also adds `Pragma: no-cache` and `Expires: 0` for older caches.
3. `proxy.fetch("/account", ...)` checks `store.containsKey("/account")` — empty on the first call — so it invokes the `origin` supplier, gets this response, and inspects its `Cache-Control` value. The storage rule requires **both** `"public"` and `"max-age"` to be present; `"public"` is absent here, so the proxy does not store the body. The response is handed straight back to the caller marked `[ORIGIN]`.
4. A second, different user hitting the same URL repeats step 3 from scratch — `store` still has no entry for `/account`, so their own request goes to the origin again, and they get *their own* data, never a cached copy of someone else's.

**Request 2 — the static asset:**
```
GET /static/logo-8f3a1c.png HTTP/1.1
Host: api.example.com
```

**Response:**
```
HTTP/1.1 200 OK
Cache-Control: public, max-age=31536000, immutable

<png bytes>
```

5. `policy.resolve("/static/logo-8f3a1c.png")` finds that the path starts with the registered prefix `"/static/"`, so it returns the overridden value from `allowPublicCaching`, `"public, max-age=31536000, immutable"`.
6. Because this value doesn't contain `"no-store"`, `applyHeaders` skips adding `Pragma`/`Expires` — those legacy headers are only relevant to the restrictive, no-store case.
7. On the first fetch, `proxy.fetch` again finds no cache entry, calls the origin, and this time the `Cache-Control` value contains both `"public"` and `"max-age"`, so the proxy stores the body under the key `/static/logo-8f3a1c.png`.
8. On the second fetch for the same URL, `store.containsKey(...)` is now `true`, so the proxy returns the stored bytes directly, marked `[CACHE HIT]`, without ever calling the origin supplier again — exactly the behavior you want for a fingerprinted asset that will never change under that URL.

## 7. Gotchas & takeaways

> **Gotcha:** `no-store` is not the same as `no-cache` despite the confusingly similar names — `no-cache` still permits storage but forces revalidation with the server before reuse, while `no-store` forbids storing the response at all. Spring Security's default sends *both*, along with `max-age=0`, precisely so that no cache implementation can find a loophole through one directive it might interpret loosely.

- The restrictive default (`no-cache, no-store, max-age=0, must-revalidate`) applies to every response unless explicitly overridden — treat that as correct behavior for anything carrying per-user or per-session data.
- `Pragma: no-cache` and `Expires: 0` exist purely for ancient HTTP/1.0 caches that don't understand `Cache-Control` — modern caches only need the `Cache-Control` header, but the older headers are cheap insurance.
- Only override the default via `headers().cacheControl()` for responses that are genuinely public and either identical for every caller or uniquely identified by a content hash in the URL, so a new version gets a new URL rather than reusing a stale cached one.
- The browser's back/forward cache (bfcache) is exactly why `no-store` matters even for a single user on a single device — without it, pressing "back" after logout can resurrect an authenticated page from memory with no network request at all.
- A path-based override that's scoped too broadly is a real risk: a `RequestMatcher` covering more than the intended static-asset paths can accidentally relax caching restrictions for an endpoint that actually carries sensitive, per-user data.
