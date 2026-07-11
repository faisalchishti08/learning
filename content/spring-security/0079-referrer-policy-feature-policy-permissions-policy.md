---
card: spring-security
gi: 79
slug: referrer-policy-feature-policy-permissions-policy
title: "Referrer Policy / Feature Policy / Permissions Policy"
---

## 1. What it is

`Referrer-Policy` and `Permissions-Policy` are two response headers, both configurable through Spring Security's headers DSL, that limit what a page is allowed to leak or do once it's loaded in a browser. `Referrer-Policy` controls how much of the current page's URL is sent in the `Referer` header when the browser follows a link or loads a subresource on another origin — the default Spring Security value, `strict-origin-when-cross-origin`, sends the full URL to same-origin destinations but trims it down to just the scheme and host for cross-origin ones. `Permissions-Policy` (the successor to the older, now-deprecated `Feature-Policy`) lets a page declare which browser features — camera, microphone, geolocation, autoplay, and dozens more — it and any embedded iframes are allowed to use, denying everything not explicitly listed.

```java
http.headers(headers -> headers
    .referrerPolicy(referrer -> referrer
        .policy(ReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN))
    .permissionsPolicy(permissions -> permissions
        .policy("geolocation=(), camera=(), microphone=()"))
);
```

## 2. Why & when

Both headers exist to shrink the amount of ambient trust a browser extends to a page by default. Before `Referrer-Policy` existed, browsers sent the entire current URL — including query strings, which frequently carry session tokens, search terms, or internal document IDs — to every link clicked and every third-party script or image loaded, silently leaking that data to whoever operated the destination. Before `Permissions-Policy`, any script running anywhere on the page (including a compromised third-party ad or analytics snippet) could request access to the camera, microphone, or location with no way for the page owner to opt out in advance.

Reach for these headers when:

- Your URLs contain anything sensitive in the path or query string (password reset tokens, search terms, internal record IDs) and you don't want that data handed to third-party sites your users click through to.
- You embed third-party scripts (ads, analytics, widgets) and want to guarantee they cannot invoke sensitive browser APIs even if compromised, without auditing every script's source.
- You embed iframes from other origins and want to restrict which powerful features those frames can request, regardless of what the frame's own page would otherwise be allowed to do.
- You're hardening a public-facing application against data-leakage and privacy audits, where an overly permissive `Referrer-Policy` (or none at all) is a common, easily-fixed finding.

The previous card in this series covered Content-Security-Policy, which restricts *where a page's content can load from*; these two headers instead restrict *what the browser leaks about the page* (`Referrer-Policy`) and *what capabilities a page or its frames may exercise* (`Permissions-Policy`) — complementary defenses, not overlapping ones.

## 3. Core concept

```
Referrer-Policy: strict-origin-when-cross-origin
  same-origin link/request  -> full URL sent as Referer      (https://shop.com/cart?id=42)
  cross-origin link/request -> origin only sent as Referer   (https://shop.com/)
  HTTPS -> HTTP downgrade   -> NO Referer sent at all

Permissions-Policy: geolocation=(), camera=(), microphone=()
  empty parens () -- feature denied to EVERYONE, including the top-level page itself
  self             -- feature allowed only for this origin
  (self "https://trusted.example") -- allowed for this origin and one named origin

Feature-Policy (deprecated predecessor, same idea, different header name/syntax)
  -- still sent by Spring Security alongside Permissions-Policy for older browsers, if configured
```

`Referrer-Policy` is evaluated by the browser every time it's about to send a `Referer` header, whether for a navigation, an image fetch, or an XHR/fetch call — the policy decides how much of the current URL survives into that header. `Permissions-Policy` is evaluated once per feature request — every time a script (or an embedded iframe) calls an API like `navigator.geolocation.getCurrentPosition()`, the browser checks whether that origin is allowed by the active policy before letting the call proceed; if not, the call fails as though the feature didn't exist.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A page at shop dot com with a sensitive query string navigates to two destinations under strict origin when cross origin referrer policy a same origin destination receives the full url including the query string a cross origin destination receives only the origin with no path or query below that a permissions policy of geolocation empty parens blocks a script on the page from calling navigator geolocation get current position">
  <rect x="20" y="15" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Current page: https://shop.com/cart?id=42&amp;token=abc123</text>

  <rect x="20" y="90" width="270" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="112" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">same-origin link</text>
  <text x="155" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Referer: full URL sent</text>
  <text x="155" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">/cart?id=42&amp;token=abc123</text>

  <rect x="350" y="90" width="270" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="485" y="112" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">cross-origin link</text>
  <text x="485" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Referer: origin only</text>
  <text x="485" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">https://shop.com/</text>

  <line x1="155" y1="55" x2="155" y2="88" stroke="#79c0ff" stroke-width="2" marker-end="url(#a79)"/>
  <line x1="485" y1="55" x2="485" y2="88" stroke="#f85149" stroke-width="2" marker-end="url(#a79r)"/>

  <rect x="120" y="185" width="400" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="207" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Permissions-Policy: geolocation=()</text>
  <text x="320" y="225" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">navigator.geolocation.getCurrentPosition() -&gt; blocked</text>
  <text x="320" y="240" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">denied for every origin, including the top-level page</text>

  <defs>
    <marker id="a79" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a79r" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

The same query string survives to a same-origin destination but is stripped to bare origin for a cross-origin one, while an empty-parens permissions policy blocks a browser feature outright regardless of origin.

## 5. Runnable example

The scenario: a small in-memory model of a browser's outgoing-request pipeline that applies a configurable `Referrer-Policy` when computing the `Referer` header for a link click, then grows to also enforce a `Permissions-Policy` before allowing a simulated feature call, and finally handles the trickier real-world cases — HTTPS-to-HTTP downgrades, per-feature allow-lists, and header value parsing.

### Level 1 — Basic

Compute the `Referer` header a browser would send for a link click, under a fixed `strict-origin-when-cross-origin` policy.

```java
import java.net.URI;

public class ReferrerPolicyLevel1 {

    // returns the ORIGIN of a URL: scheme + host + port, no path or query
    static String originOf(URI uri) {
        int port = uri.getPort();
        String portPart = (port == -1) ? "" : (":" + port);
        return uri.getScheme() + "://" + uri.getHost() + portPart;
    }

    // simulates strict-origin-when-cross-origin: full URL for same-origin, origin only for cross-origin
    static String computeReferer(URI currentPage, URI destination) {
        boolean sameOrigin = originOf(currentPage).equals(originOf(destination));
        return sameOrigin ? currentPage.toString() : originOf(currentPage);
    }

    public static void main(String[] args) {
        URI currentPage = URI.create("https://shop.com/cart?id=42&token=abc123");

        URI sameOriginDest = URI.create("https://shop.com/checkout");
        URI crossOriginDest = URI.create("https://ads.example/click");

        System.out.println("Referer to same-origin dest: " + computeReferer(currentPage, sameOriginDest));
        System.out.println("Referer to cross-origin dest: " + computeReferer(currentPage, crossOriginDest));
    }
}
```

**How to run:** save as `ReferrerPolicyLevel1.java`, run `java ReferrerPolicyLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Referer to same-origin dest: https://shop.com/cart?id=42&token=abc123
Referer to cross-origin dest: https://shop.com
```

`computeReferer` mirrors the `strict-origin-when-cross-origin` policy Spring Security sets by default: a same-origin destination gets the full current URL (including the sensitive `token` query parameter), while a cross-origin destination gets only the origin, with no path or query string at all — the actual sensitive part of the URL never leaves `shop.com`.

### Level 2 — Intermediate

Add a `Permissions-Policy` check that blocks a simulated feature call unless the calling origin is on the feature's allow-list.

```java
import java.net.URI;
import java.util.*;

public class ReferrerPolicyLevel2 {

    static String originOf(URI uri) {
        int port = uri.getPort();
        String portPart = (port == -1) ? "" : (":" + port);
        return uri.getScheme() + "://" + uri.getHost() + portPart;
    }

    static String computeReferer(URI currentPage, URI destination) {
        boolean sameOrigin = originOf(currentPage).equals(originOf(destination));
        return sameOrigin ? currentPage.toString() : originOf(currentPage);
    }

    // a Permissions-Policy: feature name -> set of ALLOWED origins ("*" means every origin, empty set means none)
    record PermissionsPolicy(Map<String, Set<String>> allowedOrigins) {
        boolean isAllowed(String feature, String requestingOrigin) {
            Set<String> allowed = allowedOrigins.getOrDefault(feature, Set.of());
            return allowed.contains("*") || allowed.contains(requestingOrigin);
        }
    }

    // simulates a script on some origin trying to invoke a browser feature (e.g. navigator.geolocation)
    static String tryUseFeature(PermissionsPolicy policy, String feature, String callingOrigin) {
        if (!policy.isAllowed(feature, callingOrigin)) {
            return "BLOCKED: '" + feature + "' denied for origin " + callingOrigin;
        }
        return "ALLOWED: '" + feature + "' invoked by " + callingOrigin;
    }

    public static void main(String[] args) {
        URI currentPage = URI.create("https://shop.com/cart?id=42&token=abc123");
        URI crossOriginDest = URI.create("https://ads.example/click");
        System.out.println("Referer to cross-origin dest: " + computeReferer(currentPage, crossOriginDest));

        // geolocation=() -- denied for everyone; camera=(self) -- allowed only for shop.com itself
        PermissionsPolicy policy = new PermissionsPolicy(Map.of(
                "geolocation", Set.of(),
                "camera", Set.of("https://shop.com")
        ));

        System.out.println(tryUseFeature(policy, "geolocation", "https://shop.com"));
        System.out.println(tryUseFeature(policy, "camera", "https://shop.com"));
        System.out.println(tryUseFeature(policy, "camera", "https://ads.example"));
    }
}
```

**How to run:** save as `ReferrerPolicyLevel2.java`, run `java ReferrerPolicyLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
Referer to cross-origin dest: https://shop.com
BLOCKED: 'geolocation' denied for origin https://shop.com
ALLOWED: 'camera' invoked by https://shop.com
BLOCKED: 'camera' denied for origin https://ads.example
```

What changed from Level 1: a `PermissionsPolicy` record now models the header's real per-feature allow-list syntax — an empty set denies a feature to every origin including the top-level page itself, while a named-origin set (like `camera` allowed only for `shop.com`) lets the top-level page use a feature while still denying it to any embedded third-party frame from a different origin. This is exactly the failure mode `Permissions-Policy` closes: without it, a compromised or malicious ad script embedded on the page could call `navigator.geolocation.getCurrentPosition()` directly, with no way for `shop.com` to have preemptively denied it.

### Level 3 — Advanced

Handle the harder real-world cases: an HTTPS-to-HTTP downgrade suppressing the `Referer` entirely, and parsing a raw `Permissions-Policy` header string (as Spring Security would emit it) into the allow-list model.

```java
import java.net.URI;
import java.util.*;

public class ReferrerPolicyLevel3 {

    static String originOf(URI uri) {
        int port = uri.getPort();
        String portPart = (port == -1) ? "" : (":" + port);
        return uri.getScheme() + "://" + uri.getHost() + portPart;
    }

    // full strict-origin-when-cross-origin behavior, INCLUDING the HTTPS -> HTTP downgrade rule:
    // a secure page navigating to an insecure destination sends NO Referer at all, to avoid
    // leaking any part of a URL that was protected by TLS onto an unencrypted connection.
    static Optional<String> computeReferer(URI currentPage, URI destination) {
        boolean downgrade = "https".equals(currentPage.getScheme()) && "http".equals(destination.getScheme());
        if (downgrade) {
            return Optional.empty();
        }
        boolean sameOrigin = originOf(currentPage).equals(originOf(destination));
        return Optional.of(sameOrigin ? currentPage.toString() : originOf(currentPage));
    }

    record PermissionsPolicy(Map<String, Set<String>> allowedOrigins) {

        boolean isAllowed(String feature, String requestingOrigin) {
            Set<String> allowed = allowedOrigins.getOrDefault(feature, Set.of());
            return allowed.contains("*") || allowed.contains(requestingOrigin);
        }

        // parses a raw header value like: "geolocation=(), camera=(self \"https://trusted.example\")"
        static PermissionsPolicy parse(String headerValue) {
            Map<String, Set<String>> directives = new LinkedHashMap<>();
            for (String directive : headerValue.split(",")) {
                directive = directive.trim();
                int eq = directive.indexOf('=');
                String feature = directive.substring(0, eq).trim();
                String allowList = directive.substring(eq + 1).trim();
                allowList = allowList.replaceAll("[()\"]", ""); // strip parens and quotes
                Set<String> origins = new LinkedHashSet<>();
                for (String token : allowList.split("\\s+")) {
                    if (token.equals("self")) {
                        origins.add("SELF"); // caller resolves "self" against the serving origin
                    } else if (!token.isBlank()) {
                        origins.add(token);
                    }
                }
                directives.put(feature, origins);
            }
            return new PermissionsPolicy(directives);
        }

        // resolves the special "self" token against the page's own serving origin before checking
        boolean isAllowedResolved(String feature, String requestingOrigin, String servingOrigin) {
            Set<String> allowed = allowedOrigins.getOrDefault(feature, Set.of());
            if (allowed.contains("*")) return true;
            if (allowed.contains(requestingOrigin)) return true;
            return allowed.contains("SELF") && requestingOrigin.equals(servingOrigin);
        }
    }

    static String tryUseFeature(PermissionsPolicy policy, String feature, String callingOrigin, String servingOrigin) {
        boolean allowed = policy.isAllowedResolved(feature, callingOrigin, servingOrigin);
        return (allowed ? "ALLOWED: '" : "BLOCKED: '") + feature + "' for " + callingOrigin
                + (allowed ? "" : " (serving origin: " + servingOrigin + ")");
    }

    public static void main(String[] args) {
        URI securePage = URI.create("https://shop.com/cart?id=42&token=abc123");
        URI insecureDest = URI.create("http://legacy-partner.com/redirect");
        URI secureCrossOrigin = URI.create("https://ads.example/click");

        System.out.println("HTTPS -> HTTP downgrade Referer: " + computeReferer(securePage, insecureDest));
        System.out.println("HTTPS -> HTTPS cross-origin Referer: " + computeReferer(securePage, secureCrossOrigin));

        // exactly the header value Spring Security's permissionsPolicy() DSL would write out
        String rawHeader = "geolocation=(), camera=(self \"https://trusted.example\")";
        PermissionsPolicy policy = PermissionsPolicy.parse(rawHeader);

        String servingOrigin = "https://shop.com";
        System.out.println(tryUseFeature(policy, "geolocation", "https://shop.com", servingOrigin));
        System.out.println(tryUseFeature(policy, "camera", "https://shop.com", servingOrigin));
        System.out.println(tryUseFeature(policy, "camera", "https://trusted.example", servingOrigin));
        System.out.println(tryUseFeature(policy, "camera", "https://ads.example", servingOrigin));
    }
}
```

**How to run:** save as `ReferrerPolicyLevel3.java`, run `java ReferrerPolicyLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
HTTPS -> HTTP downgrade Referer: Optional.empty
HTTPS -> HTTPS cross-origin Referer: Optional[https://shop.com]
BLOCKED: 'geolocation' for https://shop.com (serving origin: https://shop.com)
ALLOWED: 'camera' for https://shop.com
ALLOWED: 'camera' for https://trusted.example
BLOCKED: 'camera' for https://ads.example (serving origin: https://shop.com)
```

`computeReferer` now checks for a secure-to-insecure downgrade before anything else, returning `Optional.empty()` (no header sent at all) — this protects a URL that was only ever transmitted over TLS from leaking, even in stripped-down form, onto a plaintext HTTP connection. `PermissionsPolicy.parse` reproduces the real header's syntax: comma-separated `feature=(allow-list)` directives, where the allow-list can be empty (deny all, as with `geolocation`), or contain the literal token `self` plus optional quoted origins (as with `camera`). `isAllowedResolved` treats the parsed `"SELF"` marker specially, resolving it against whatever origin is actually serving the policy — `shop.com` itself and the explicitly named `trusted.example` both get `camera` access, while `ads.example`, present in neither the origin list nor matching `self`, is blocked.

## 6. Walkthrough

Trace the Level 3 program end-to-end, starting from a concrete HTTP exchange and following it through to the two header checks.

Example request (a browser loading a page on `shop.com` that then tries to use the camera from an embedded ad frame):

```
GET /cart?id=42&token=abc123 HTTP/1.1
Host: shop.com
```

Example response, carrying both headers this card covers:

```
HTTP/1.1 200 OK
Content-Type: text/html
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(self "https://trusted.example")
```

1. The server (configured via `http.headers(headers -> headers.referrerPolicy(...).permissionsPolicy(...))`) writes both headers onto every response, before the browser renders anything — these are declarative policies the browser must obey for the lifetime of that page load.
2. The browser parses `Referrer-Policy: strict-origin-when-cross-origin` and stores it as the active policy for this page; it does the same for `Permissions-Policy`, building an internal per-feature allow-list.
3. The user clicks a link to `http://legacy-partner.com/redirect`. Before sending that navigation request, the browser calls the equivalent of `computeReferer(securePage, insecureDest)`; because the current page's scheme is `https` and the destination's is `http`, the downgrade check at the top of the method fires first and short-circuits to `Optional.empty()` — no `Referer` header is attached to that outgoing request at all.
4. Separately, an ad script running in an embedded frame from `https://ads.example` attempts `navigator.geolocation.getCurrentPosition()`. The browser looks up `geolocation` in the parsed policy map built by `PermissionsPolicy.parse`; the raw header's `geolocation=()` produced an empty set for that feature, so `isAllowedResolved` returns `false` for every origin, including `shop.com` itself — the call fails immediately, before it ever reaches the operating system's actual location API.
5. The same ad script then attempts to access the camera. `PermissionsPolicy.parse` recorded `camera`'s allow-list as `{"SELF", "https://trusted.example"}` (the quoted origin string, with its surrounding quotes stripped during parsing). `isAllowedResolved("camera", "https://ads.example", "https://shop.com")` checks membership directly (`ads.example` isn't in the set), then checks the `self` case (`ads.example` doesn't equal the serving origin `shop.com`) — both checks fail, so the call is blocked.
6. A first-party script on `shop.com` itself makes the identical camera call. This time `requestingOrigin` ("https://shop.com") equals `servingOrigin`, so the `self`-resolution branch succeeds — the call is allowed, exactly matching what the raw header's `self` token was meant to permit.

```
response headers -> browser policy store -> per-navigation Referer check
                                          -> per-feature-call Permissions-Policy check
```

Every check in this trace happens entirely inside the browser, against policies the server declared once in its response headers — the server never re-validates anything per click or per feature call; it simply states the rule and trusts browser enforcement.

## 7. Gotchas & takeaways

> **Gotcha:** `Permissions-Policy` denies by omission — any feature not listed in the header at all is left to the browser's own default (often permissive), while a feature explicitly listed with an empty allow-list, `feature=()`, is denied to absolutely everyone, including same-origin scripts on the page that set the header. If you actually need a feature yourself, you must list your own origin (`self`) explicitly rather than assuming omitting the feature protects you.

- `Referrer-Policy: strict-origin-when-cross-origin` is Spring Security's default and a reasonable one: full URL same-origin, origin-only cross-origin, nothing at all on an HTTPS-to-HTTP downgrade.
- `Feature-Policy` is deprecated in favor of `Permissions-Policy`; Spring Security's `featurePolicy()` DSL method still exists for legacy browser support but new configuration should use `permissionsPolicy()`.
- Sensitive data belongs in the request body or in headers, not in the URL path or query string — `Referrer-Policy` reduces *how far* a leaked URL travels, but it cannot un-leak a token that a same-origin page or an internal link already forwards in full.
- Empty-parens (`()`) in a `Permissions-Policy` directive denies a feature to every context, including the top level page itself — use `(self)` if the page needs the feature for itself while still denying it to embedded third-party frames.
- Both headers are enforced entirely client-side by the browser; a malicious or outdated client can simply ignore them, so they are a defense-in-depth layer alongside, not a replacement for, server-side authorization checks.
