---
card: spring-security
gi: 77
slug: security-http-response-headers-hsts-x-frame-options-csp-etc
title: "Security HTTP response headers (HSTS, X-Frame-Options, CSP, etc.)"
---

## 1. What it is

Spring Security ships a servlet `HeadersFilter` that stamps every outgoing response with a set of security-relevant HTTP headers before it reaches the browser. These headers aren't application data — they're instructions to the browser itself: "never let another site frame this page," "never guess this response's content type," "only ever talk to me over HTTPS," and so on. The `headers(headers -> ...)` DSL is the single configuration surface for all of them; it ships sane defaults out of the box and lets you override, add, or remove any individual header. This card is the map of that territory — a broad tour of what each header defends against — while the next several cards go deep on HSTS, `X-Frame-Options`, and Content Security Policy individually.

```java
http.headers(headers -> headers
    .frameOptions(frame -> frame.sameOrigin())
    .httpStrictTransportSecurity(hsts -> hsts.includeSubDomains(true).maxAgeInSeconds(31536000))
    .contentSecurityPolicy(csp -> csp.policyDirectives("default-src 'self'"))
);
```

## 2. Why & when

Browsers are willing participants in their own defense — but only if the server tells them what to enforce. Without these headers, a browser will let any other site frame your page (enabling clickjacking), will "helpfully" guess a response's content type even when you declared it explicitly (enabling MIME-sniffing attacks against user-uploaded files), will happily downgrade an HTTPS connection to plain HTTP if an attacker on the network suggests it, and will leak your full URL — including query strings that might contain tokens — to whatever site a link is clicked through to. Each header in the table below closes one specific one of these gaps, and `HeadersFilter` applies the sensible subset by default so a fresh Spring Security application is reasonably hardened without any explicit configuration at all.

Reach for the `headers{}` DSL when:

- Auditing what a Spring Security app sends by default, versus what your organization's security policy or a penetration test requires.
- Relaxing a default that's too strict for a legitimate use case — e.g., allowing your own app to frame itself for an embedded dashboard widget.
- Adding headers Spring Security doesn't enable by default, like `Permissions-Policy` or the `Cross-Origin-*` isolation headers.
- Diagnosing why a browser is blocking something (a frame, an inline script, a cross-origin fetch) — the answer is almost always one of these headers doing exactly what it was configured to do.

## 3. Core concept

| Header | Defends against | DSL entry point |
|---|---|---|
| `X-Content-Type-Options: nosniff` | MIME-sniffing (browser guessing a file's type against the declared `Content-Type`) | `contentTypeOptions()` |
| `X-Frame-Options: DENY`/`SAMEORIGIN` | Clickjacking (embedding your page in a hidden/disguised `<iframe>`) | `frameOptions()` |
| `Strict-Transport-Security` (HSTS) | Protocol downgrade / SSL-stripping attacks after the first HTTPS visit | `httpStrictTransportSecurity()` |
| `Content-Security-Policy` | XSS and unauthorized resource loading, by allowlisting sources per resource type | `contentSecurityPolicy()` |
| `Referrer-Policy` | Leaking full URLs (including sensitive query strings) to third-party sites via the `Referer` header | `referrerPolicy()` |
| `Cache-Control` / `Pragma` | Sensitive pages being cached and later replayed from browser/proxy history | applied by default, tunable via `cacheControl()` |
| `Permissions-Policy` | Unwanted use of powerful browser features (camera, geolocation, microphone) by embedded or injected content | custom header via `headers.addHeaderWriter(...)` |
| `Cross-Origin-Opener-Policy` / `-Embedder-Policy` / `-Resource-Policy` | Cross-origin data leaks via shared browsing contexts (Spectre-style side channels) | `crossOriginOpenerPolicy()` / `crossOriginEmbedderPolicy()` / `crossOriginResourcePolicy()` |

`default-src 'self'` and friends inside `Content-Security-Policy` get their own deep dive next card; here it's just one row in the map.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An HttpResponse passes through Spring Security's HeadersFilter which stamps it with several security headers X-Content-Type-Options X-Frame-Options Strict-Transport-Security Content-Security-Policy and Referrer-Policy before it reaches the browser which then enforces each one">
  <rect x="15" y="105" width="130" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="80" y="135" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HttpResponse</text>

  <rect x="200" y="90" width="150" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="275" y="115" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">HeadersFilter</text>
  <text x="275" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">stamps N security</text>
  <text x="275" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">headers before send</text>

  <rect x="440" y="15" width="185" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="532" y="37" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">X-Content-Type-Options</text>

  <rect x="440" y="58" width="185" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="532" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">X-Frame-Options</text>

  <rect x="440" y="101" width="185" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="532" y="123" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Strict-Transport-Security</text>

  <rect x="440" y="144" width="185" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="532" y="166" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Content-Security-Policy</text>

  <rect x="440" y="187" width="185" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="532" y="209" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Referrer-Policy</text>

  <defs><marker id="a77" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
  <line x1="145" y1="130" x2="198" y2="130" stroke="#3fb950" stroke-width="2" marker-end="url(#a77)"/>
  <line x1="350" y1="120" x2="438" y2="35" stroke="#8b949e" stroke-width="1" marker-end="url(#a77)"/>
  <line x1="350" y1="126" x2="438" y2="78" stroke="#8b949e" stroke-width="1" marker-end="url(#a77)"/>
  <line x1="350" y1="132" x2="438" y2="120" stroke="#8b949e" stroke-width="1" marker-end="url(#a77)"/>
  <line x1="350" y1="138" x2="438" y2="163" stroke="#8b949e" stroke-width="1" marker-end="url(#a77)"/>
  <line x1="350" y1="144" x2="438" y2="205" stroke="#8b949e" stroke-width="1" marker-end="url(#a77)"/>
</svg>

One filter, many headers — each chip on the right gets its own dedicated card later in this deck.

## 5. Runnable example

The scenario: a simulated `HeadersFilter` that builds up a response's header map, starting from Spring Security's defaults and growing into a fully production-tuned, request-aware configuration.

### Level 1 — Basic

The defaults Spring Security applies to every response with no configuration at all.

```java
import java.util.*;

public class SecurityHeadersLevel1 {
    static Map<String, String> defaultHeaders() {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("X-Content-Type-Options", "nosniff");
        headers.put("X-Frame-Options", "DENY");
        headers.put("Cache-Control", "no-cache, no-store, max-age=0, must-revalidate");
        headers.put("Pragma", "no-cache");
        return headers;
    }

    public static void main(String[] args) {
        defaultHeaders().forEach((name, value) -> System.out.println(name + ": " + value));
    }
}
```

**How to run:** save as `SecurityHeadersLevel1.java`, run `java SecurityHeadersLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Pragma: no-cache
```

Nothing here needs to be understood beyond "the framework already protects you against MIME sniffing, clickjacking, and stale cached pages before you write any config."

### Level 2 — Intermediate

Add the `headers{}` DSL's fluent overrides — relaxing `X-Frame-Options` for a legitimate same-origin embed, and adding HSTS and a `Referrer-Policy` explicitly.

```java
import java.util.*;

public class SecurityHeadersLevel2 {
    static class HeadersConfigurer {
        private final Map<String, String> headers = new LinkedHashMap<>();

        HeadersConfigurer() {
            headers.put("X-Content-Type-Options", "nosniff");
            headers.put("X-Frame-Options", "DENY");
            headers.put("Cache-Control", "no-cache, no-store, max-age=0, must-revalidate");
        }

        HeadersConfigurer frameOptions(String value) {
            headers.put("X-Frame-Options", value);
            return this;
        }

        HeadersConfigurer hsts(long maxAgeSeconds, boolean includeSubDomains) {
            String value = "max-age=" + maxAgeSeconds + (includeSubDomains ? "; includeSubDomains" : "");
            headers.put("Strict-Transport-Security", value);
            return this;
        }

        HeadersConfigurer referrerPolicy(String policy) {
            headers.put("Referrer-Policy", policy);
            return this;
        }

        Map<String, String> build() {
            return headers;
        }
    }

    public static void main(String[] args) {
        // this app legitimately embeds itself in an iframe (an internal dashboard widget),
        // so the blanket DENY default is relaxed to SAMEORIGIN rather than disabled outright
        Map<String, String> headers = new HeadersConfigurer()
                .frameOptions("SAMEORIGIN")
                .hsts(31536000, true)
                .referrerPolicy("strict-origin-when-cross-origin")
                .build();

        headers.forEach((name, value) -> System.out.println(name + ": " + value));
    }
}
```

**How to run:** `java SecurityHeadersLevel2.java`. What changed: `frameOptions("SAMEORIGIN")` overwrites the default in place (the header keeps its original position in the map), while `hsts(...)` and `referrerPolicy(...)` append two headers absent from the bare defaults — exactly mirroring how the DSL layers on top of, rather than replaces, Spring Security's baseline.

Expected output:
```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
```

### Level 3 — Advanced

Handle the production-flavoured hard cases: HSTS must never be sent over a plain HTTP response (the browser ignores it there anyway, and sending it is misleading), modern isolation headers should be added alongside the classics, and legacy `X-Frame-Options` should be *kept* even when a CSP `frame-ancestors` directive covers the same threat, for older browsers that don't implement CSP framing controls.

```java
import java.util.*;

public class SecurityHeadersLevel3 {
    static Map<String, String> buildHeaders(boolean isSecureRequest, boolean hasCspFrameAncestors) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("X-Content-Type-Options", "nosniff");

        // kept even when CSP's frame-ancestors also applies -- older browsers/webviews
        // ignore frame-ancestors entirely and rely solely on this legacy header
        headers.put("X-Frame-Options", "DENY");

        headers.put("Cache-Control", "no-cache, no-store, max-age=0, must-revalidate");
        headers.put("Referrer-Policy", "strict-origin-when-cross-origin");
        headers.put("Permissions-Policy", "geolocation=(), camera=(), microphone=()");
        headers.put("Cross-Origin-Opener-Policy", "same-origin");
        headers.put("Cross-Origin-Resource-Policy", "same-origin");

        // HSTS is meaningless -- and actively misleading -- on a plain HTTP response;
        // browsers ignore it there anyway, so only add it once the connection is secure
        if (isSecureRequest) {
            headers.put("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload");
        }

        if (hasCspFrameAncestors) {
            headers.put("Content-Security-Policy", "frame-ancestors 'self'");
        }

        return headers;
    }

    public static void main(String[] args) {
        System.out.println("-- Plain HTTP request (no HSTS added) --");
        buildHeaders(false, false).forEach((k, v) -> System.out.println(k + ": " + v));

        System.out.println("-- HTTPS request, CSP frame-ancestors also configured --");
        buildHeaders(true, true).forEach((k, v) -> System.out.println(k + ": " + v));

        Map<String, String> httpsHeaders = buildHeaders(true, true);
        System.out.println("Both X-Frame-Options AND CSP frame-ancestors present (defense in depth): " +
                (httpsHeaders.containsKey("X-Frame-Options") && httpsHeaders.containsKey("Content-Security-Policy")));
    }
}
```

**How to run:** `java SecurityHeadersLevel3.java`. This adds: (1) conditional HSTS, only stamped when the request actually arrived over HTTPS; (2) three newer isolation headers (`Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`) alongside the classics; (3) proof that the legacy and modern framing defenses coexist rather than replace one another.

Expected output:
```
-- Plain HTTP request (no HSTS added) --
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
-- HTTPS request, CSP frame-ancestors also configured --
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: no-cache, no-store, max-age=0, must-revalidate
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: frame-ancestors 'self'
Both X-Frame-Options AND CSP frame-ancestors present (defense in depth): true
```

## 6. Walkthrough

Trace a single page load against Level 3's model, end-to-end:

1. **Request arrives.** A browser sends:
   ```
   GET /dashboard HTTP/1.1
   Host: app.example.com
   ```
   over a TLS connection, so the server considers this request secure.
2. **Controller produces a response body** — ordinary HTML — with no awareness of security headers at all; that's not the controller's job.
3. **`HeadersFilter` runs** (simulated by `buildHeaders(true, true)` — secure request, CSP `frame-ancestors` configured for this route) and stamps the header map in insertion order: `X-Content-Type-Options`, `X-Frame-Options`, `Cache-Control`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, then — because `isSecureRequest` is `true` — `Strict-Transport-Security`, then — because `hasCspFrameAncestors` is `true` — `Content-Security-Policy`.
4. **Response leaves the server:**
   ```
   HTTP/1.1 200 OK
   X-Content-Type-Options: nosniff
   X-Frame-Options: DENY
   Cache-Control: no-cache, no-store, max-age=0, must-revalidate
   Referrer-Policy: strict-origin-when-cross-origin
   Permissions-Policy: geolocation=(), camera=(), microphone=()
   Cross-Origin-Opener-Policy: same-origin
   Cross-Origin-Resource-Policy: same-origin
   Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
   Content-Security-Policy: frame-ancestors 'self'
   Content-Type: text/html

   <html>...dashboard markup...</html>
   ```
5. **Browser enforces each header independently.** If some other page tries `<iframe src="https://app.example.com/dashboard">`, both `X-Frame-Options: DENY` and `Content-Security-Policy: frame-ancestors 'self'` tell the browser to refuse to render the frame — a modern browser honors the CSP directive, an older one falls back to the legacy header, and either way the embed is blocked.
6. **Every subsequent request to this host** upgrades to HTTPS automatically without a round trip, because the browser cached the `Strict-Transport-Security` directive from step 4 — that's the entire point of HSTS: it removes the window for a network attacker to intercept an initial plain-HTTP request and strip the upgrade.

```
Request  -> Controller (produces body, no header awareness)
         -> HeadersFilter (stamps N security headers, order = insertion order)
         -> Response (headers + body) -> Browser (enforces each header as an instruction)
```

## 7. Gotchas & takeaways

> Sending `Strict-Transport-Security` on a response delivered over plain HTTP accomplishes nothing — browsers only honor HSTS on responses that arrive over an already-secure connection, so "adding HSTS" to an HTTP-only endpoint is a false sense of security, not real protection.

- `headers{}` is additive and overriding on top of sensible defaults, not an opt-in system starting from zero — a fresh Spring Security app already ships `X-Content-Type-Options`, `X-Frame-Options`, and cache-control headers with no configuration.
- Keep legacy headers (`X-Frame-Options`) alongside their modern CSP equivalents (`frame-ancestors`) rather than choosing one — older browsers and embedded webviews frequently support only the legacy header.
- Disabling a header outright (e.g., `.contentTypeOptions(options -> options.disable())`) removes a real, currently-active protection; only do it for a specific, well-understood reason, never as a blanket "reduce noise" move.
- This card is deliberately broad — HSTS internals, the full `X-Frame-Options` story, and Content Security Policy's directive syntax each get their own dedicated, deeper card next.
- `Permissions-Policy` and the `Cross-Origin-*` isolation headers aren't enabled by Spring Security's defaults; add them explicitly if your threat model calls for locking down powerful browser APIs or cross-origin memory isolation.
