---
card: spring-security
gi: 76
slug: csrf-with-spa-cookie-based-token
title: "CSRF with SPA / cookie-based token"
---

## 1. What it is

The previous card's `HttpSessionCsrfTokenRepository` needs somewhere to *render* the token — a hidden `<input>` inside a server-rendered HTML form. A single-page application built with React, Vue, or Angular doesn't render forms on the server at all; it talks to the backend purely through `fetch`/XHR calls that exchange JSON. `CookieCsrfTokenRepository` solves that mismatch: instead of stashing the `CsrfToken` in the `HttpSession`, it writes the token's value into a cookie named `XSRF-TOKEN`. Crucially, that cookie is created with `withHttpOnlyFalse()` — meaning, unlike almost every other security-sensitive cookie, JavaScript running on the page is *deliberately allowed* to read it via `document.cookie`. The SPA's own script reads that value and echoes it back on every mutating request as a custom header, `X-XSRF-TOKEN` by default. The server then checks that the cookie value and the header value match — this is the **double-submit cookie pattern**.

```java
http.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
);
```

## 2. Why & when

Session-based CSRF protection (the previous card) assumes the server controls the HTML the token gets embedded into. That assumption breaks for API-only backends: there's no server-rendered form for a hidden `_csrf` field to live in, and requiring the SPA to first fetch a page just to scrape a token out of the DOM is awkward. The double-submit cookie sidesteps this entirely — the browser already stores and auto-attaches cookies to every request for the domain, so the server just needs the *SPA's own JavaScript* to copy that cookie's value into a header. An attacker's page can still make the browser send a forged request (the cookie rides along automatically, just like with session-based CSRF), but the attacker's JavaScript, running on a different origin, is blocked by the browser's same-origin policy from ever reading `app.example.com`'s cookies — so it cannot manufacture the matching header.

Reach for `CookieCsrfTokenRepository` when:

- Building a SPA or mobile-web frontend that authenticates via cookies (session or otherwise) but exchanges JSON, not server-rendered forms.
- The frontend framework already automates this pattern — Angular's `HttpClientXsrfModule` and Axios both look for a cookie named `XSRF-TOKEN` and auto-attach it as `X-XSRF-TOKEN` with zero extra frontend code, matching Spring Security's defaults exactly.
- You need CSRF protection that survives page reloads and multiple tabs without server-side session lookups on every request.
- You must explicitly call `withHttpOnlyFalse()` — the default `CookieCsrfTokenRepository()` constructor leaves `HttpOnly` **true**, which silently breaks the whole scheme because the SPA's script can no longer read the cookie it needs to echo back.

## 3. Core concept

```
1. Any response (even a GET) -- server has no XSRF-TOKEN cookie for this browser yet
   -> CookieCsrfTokenRepository generates a token, writes:
      Set-Cookie: XSRF-TOKEN=<value>; HttpOnly=false; SameSite=Lax
2. SPA's own JavaScript reads document.cookie, extracts XSRF-TOKEN
3. SPA issues a mutating request (POST/PUT/DELETE), attaching the value as:
      X-XSRF-TOKEN: <value>
   the browser ALSO auto-attaches the Cookie header for this domain regardless
4. CsrfFilter (double-submit check): does Cookie's XSRF-TOKEN == X-XSRF-TOKEN header ?
   MATCH    -> request proceeds
   MISMATCH / HEADER MISSING -> 403 Forbidden
```

A forged request from `evil.com` still carries the browser's auto-attached cookie, but `evil.com`'s script can never read that cookie's value to build the matching header — the same-origin policy, not the cookie's secrecy, is what defends this pattern.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The SPA on app example dot com reads the XSRF token cookie via same origin javascript and attaches it as a header so the double submit check passes and returns 200 OK evil dot com can trigger a forged request whose cookie still rides along automatically but its script cannot read app example dot com's cookie jar across origins so no header is sent and the request is rejected with 403">
  <rect x="15" y="15" width="290" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="160" y="33" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SPA on app.example.com</text>
  <text x="30" y="55" fill="#e6edf3" font-size="9.5" font-family="sans-serif">1. reads XSRF-TOKEN cookie</text>
  <text x="30" y="72" fill="#e6edf3" font-size="9.5" font-family="sans-serif">   (same-origin JS, HttpOnly=false)</text>
  <text x="30" y="89" fill="#e6edf3" font-size="9.5" font-family="sans-serif">2. fetch POST with header:</text>
  <text x="30" y="106" fill="#79c0ff" font-size="9.5" font-family="sans-serif">   X-XSRF-TOKEN: &lt;value&gt;</text>
  <text x="30" y="126" fill="#3fb950" font-size="9.5" font-family="sans-serif">3. cookie == header -&gt; 200 OK</text>

  <rect x="335" y="15" width="290" height="130" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.4"/>
  <text x="480" y="33" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Forged flow (evil.com)</text>
  <text x="350" y="55" fill="#e6edf3" font-size="9.5" font-family="sans-serif">1. hidden fetch(credentials:</text>
  <text x="350" y="70" fill="#e6edf3" font-size="9.5" font-family="sans-serif">   'include') to app.example.com</text>
  <text x="350" y="90" fill="#e6edf3" font-size="9.5" font-family="sans-serif">2. cookie auto-attached anyway,</text>
  <text x="350" y="105" fill="#e6edf3" font-size="9.5" font-family="sans-serif">   but evil.com's JS CANNOT read it</text>
  <text x="350" y="126" fill="#f85149" font-size="9.5" font-family="sans-serif">3. no header -&gt; 403 Forbidden</text>

  <rect x="180" y="175" width="280" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="320" y="197" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">CsrfFilter: double-submit check</text>
  <text x="320" y="216" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Cookie value == X-XSRF-TOKEN header value?</text>
  <text x="320" y="233" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">same-origin policy blocks cross-origin cookie reads, not secrecy</text>
</svg>

The cookie's value is never a secret — the protection comes from the browser refusing to let another origin's script read it.

## 5. Runnable example

The scenario: a transfer endpoint fronted by a simulated `CookieCsrfTokenRepository`, growing from a bare double-submit check into a full model of `HttpOnly`/same-origin boundaries and `SameSite` cookie behaviour.

### Level 1 — Basic

Issue an `XSRF-TOKEN` cookie and validate a request by comparing it to a submitted header.

```java
import java.util.*;

public class CsrfSpaLevel1 {
    record Cookie(String name, String value, boolean httpOnly) {}
    record CsrfToken(String headerName, String value) {}

    static class CookieCsrfTokenRepository {
        static final String COOKIE_NAME = "XSRF-TOKEN";
        static final String HEADER_NAME = "X-XSRF-TOKEN";

        CsrfToken generateToken() {
            return new CsrfToken(HEADER_NAME, UUID.randomUUID().toString());
        }

        // withHttpOnlyFalse(): the SPA's own JS MUST be able to read this cookie
        Cookie saveToken(CsrfToken token) {
            return new Cookie(COOKIE_NAME, token.value(), false);
        }
    }

    // simulates CsrfFilter's double-submit check
    static boolean validate(String method, String cookieValue, String headerValue) {
        if (method.equals("GET")) return true;
        return cookieValue != null && cookieValue.equals(headerValue);
    }

    public static void main(String[] args) {
        CookieCsrfTokenRepository repo = new CookieCsrfTokenRepository();
        CsrfToken token = repo.generateToken();
        Cookie xsrfCookie = repo.saveToken(token);
        System.out.println("Set-Cookie: " + xsrfCookie.name() + "=" + xsrfCookie.value() + "; HttpOnly=" + xsrfCookie.httpOnly());

        // legit SPA request: JS read the cookie, copied it into the header
        boolean legit = validate("POST", xsrfCookie.value(), xsrfCookie.value());
        System.out.println("SPA POST with matching header: " + (legit ? "200 OK" : "403 Forbidden"));

        // forged request: cookie auto-attached by the browser, but no header set
        boolean forged = validate("POST", xsrfCookie.value(), null);
        System.out.println("Forged POST, cookie auto-attached but no header: " + (forged ? "200 OK" : "403 Forbidden"));
    }
}
```

**How to run:** save as `CsrfSpaLevel1.java`, run `java CsrfSpaLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Set-Cookie: XSRF-TOKEN=<some-uuid>; HttpOnly=false
SPA POST with matching header: 200 OK
Forged POST, cookie auto-attached but no header: 403 Forbidden
```

The repository writes a JS-readable cookie instead of session state; the filter's decision is purely "does the header match the cookie," never a lookup keyed by session ID.

### Level 2 — Intermediate

Model the crucial distinction the previous level glossed over: a `HttpOnly` `SESSION` cookie the SPA's own script can *never* read, alongside the JS-readable `XSRF-TOKEN` cookie, and the same-origin policy that blocks any other origin's script from reading either one.

```java
import java.util.*;

public class CsrfSpaLevel2 {
    record Cookie(String name, String value, boolean httpOnly, String origin) {}
    record CsrfToken(String headerName, String value) {}

    static class CookieCsrfTokenRepository {
        static final String COOKIE_NAME = "XSRF-TOKEN";
        static final String HEADER_NAME = "X-XSRF-TOKEN";

        CsrfToken generateToken() {
            return new CsrfToken(HEADER_NAME, UUID.randomUUID().toString());
        }

        // withHttpOnlyFalse() only affects the XSRF cookie -- SESSION stays HttpOnly=true
        List<Cookie> issueCookies(CsrfToken csrf, String sessionId, String origin) {
            return List.of(
                    new Cookie("SESSION", sessionId, true, origin),
                    new Cookie(COOKIE_NAME, csrf.value(), false, origin)
            );
        }
    }

    // the browser attaches every cookie matching an origin to a request sent there,
    // no matter which page triggered the request -- this is what makes CSRF possible at all
    static List<Cookie> cookiesSentTo(List<Cookie> jar, String targetOrigin) {
        return jar.stream().filter(c -> c.origin().equals(targetOrigin)).toList();
    }

    // page JavaScript can read a cookie via document.cookie only if it is NOT HttpOnly
    // AND the script's own origin matches the cookie's origin (same-origin policy)
    static Optional<String> readCookieFromJs(List<Cookie> jar, String cookieName, String scriptOrigin) {
        return jar.stream()
                .filter(c -> c.name().equals(cookieName) && c.origin().equals(scriptOrigin) && !c.httpOnly())
                .map(Cookie::value)
                .findFirst();
    }

    public static void main(String[] args) {
        CookieCsrfTokenRepository repo = new CookieCsrfTokenRepository();
        CsrfToken token = repo.generateToken();
        String appOrigin = "https://app.example.com";
        List<Cookie> jar = repo.issueCookies(token, "sess-abc123", appOrigin);

        System.out.println("SPA JS reads XSRF-TOKEN: " + readCookieFromJs(jar, "XSRF-TOKEN", appOrigin));
        System.out.println("SPA JS reads SESSION (HttpOnly, expect empty): " + readCookieFromJs(jar, "SESSION", appOrigin));
        System.out.println("evil.com JS reads XSRF-TOKEN cross-origin (expect empty): " + readCookieFromJs(jar, "XSRF-TOKEN", "https://evil.com"));
        System.out.println("Cookies auto-attached to a request to app.example.com regardless: " + cookiesSentTo(jar, appOrigin).size());
    }
}
```

**How to run:** `java CsrfSpaLevel2.java`. What changed: `SESSION` stays `HttpOnly` so no script anywhere can ever read the actual authentication credential — that's unrelated to CSRF and protects against token theft via XSS. `XSRF-TOKEN` is deliberately readable, but only by same-origin script; `evil.com`'s script gets nothing back even though the browser still happily attaches both cookies to any request aimed at `app.example.com`.

### Level 3 — Advanced

Add the two production-flavoured hard cases: the repository must not rotate the token on every single request (only mint one when none exists yet), and `SameSite=Lax` adds a second, independent layer of defense on top of the double-submit check.

```java
import java.util.*;

public class CsrfSpaLevel3 {
    enum SameSite { STRICT, LAX, NONE }
    record Cookie(String name, String value, boolean httpOnly, SameSite sameSite) {}
    record CsrfToken(String headerName, String cookieName, String value) {}
    enum CsrfResult { OK, MISSING, MISMATCH, SAFE_METHOD, BLOCKED_BY_SAMESITE }

    static class CookieCsrfTokenRepository {
        static final String COOKIE_NAME = "XSRF-TOKEN";
        static final String HEADER_NAME = "X-XSRF-TOKEN";

        // deferred/lazy: only mints a NEW value when the incoming request has no
        // existing XSRF-TOKEN cookie at all -- it does not rotate on every request
        CsrfToken loadOrGenerate(Optional<String> existingCookieValue) {
            String value = existingCookieValue.orElseGet(() -> UUID.randomUUID().toString());
            return new CsrfToken(HEADER_NAME, COOKIE_NAME, value);
        }

        Cookie asSetCookie(CsrfToken token) {
            return new Cookie(token.cookieName(), token.value(), false, SameSite.LAX);
        }
    }

    // simplified browser attach-rule: Strict never rides along cross-site; Lax rides along
    // only on a top-level GET-like navigation, never on a cross-site POST/fetch; None always rides along
    static boolean browserWouldAttach(Cookie cookie, boolean isCrossSite, boolean isTopLevelGetNavigation) {
        if (!isCrossSite) return true;
        return switch (cookie.sameSite()) {
            case STRICT -> false;
            case LAX -> isTopLevelGetNavigation;
            case NONE -> true;
        };
    }

    static CsrfResult validate(String method, boolean cookieWasIssued, String cookieValue,
                               String headerValue, boolean isCrossSite, boolean isTopLevelGetNavigation) {
        Set<String> safe = Set.of("GET", "HEAD", "OPTIONS", "TRACE");
        if (safe.contains(method)) return CsrfResult.SAFE_METHOD;

        Cookie probe = new Cookie(CookieCsrfTokenRepository.COOKIE_NAME, cookieValue, false, SameSite.LAX);
        boolean attached = cookieWasIssued && browserWouldAttach(probe, isCrossSite, isTopLevelGetNavigation);
        if (!attached) return CsrfResult.BLOCKED_BY_SAMESITE;

        if (cookieValue == null || headerValue == null) return CsrfResult.MISSING;
        return cookieValue.equals(headerValue) ? CsrfResult.OK : CsrfResult.MISMATCH;
    }

    public static void main(String[] args) {
        CookieCsrfTokenRepository repo = new CookieCsrfTokenRepository();

        CsrfToken first = repo.loadOrGenerate(Optional.empty());
        Cookie issued = repo.asSetCookie(first);
        System.out.println("First response Set-Cookie: " + issued.name() + "=" + issued.value());

        CsrfToken second = repo.loadOrGenerate(Optional.of(issued.value()));
        System.out.println("Token unchanged across requests (no unnecessary rotation): " + first.value().equals(second.value()));

        System.out.println("1) Same-site SPA POST, header correctly attached by JS: " +
                validate("POST", true, issued.value(), issued.value(), false, false));

        System.out.println("2) Cross-site forged fetch() POST, SameSite=Lax blocks the cookie from attaching: " +
                validate("POST", true, issued.value(), null, true, false));

        System.out.println("3) Cross-site <img> tag GET request -- safe method, no CSRF check runs at all: " +
                validate("GET", true, issued.value(), null, true, true));

        System.out.println("4) Same-site POST, header simply omitted by the caller: " +
                validate("POST", true, issued.value(), null, false, false));
    }
}
```

**How to run:** `java CsrfSpaLevel3.java`. This adds: (1) `loadOrGenerate` only mints a fresh token when the request truly has none, matching real `CookieCsrfTokenRepository` behaviour of not rotating on every request; (2) `SameSite=Lax` as an independent layer — a cross-site forged `fetch` never even gets the cookie attached, so the double-submit check never has a chance to fail *or* pass; (3) a `CsrfResult` enum distinguishing exactly why a request was rejected, mirroring the granularity Spring Security exposes to a custom `AccessDeniedHandler`.

## 6. Walkthrough

Trace a legitimate SPA transfer request against Level 3's model, end-to-end:

1. **First contact.** The browser has no `XSRF-TOKEN` cookie yet, so `loadOrGenerate(Optional.empty())` mints one and `asSetCookie` produces a cookie to send back:
   ```
   HTTP/1.1 200 OK
   Set-Cookie: XSRF-TOKEN=9f1c...; Path=/; SameSite=Lax
   ```
2. **SPA reads the cookie.** Same-origin JavaScript (Axios/Angular or hand-rolled) reads `document.cookie`, extracts the `XSRF-TOKEN` value, and stores it for the next mutating call.
3. **SPA issues the transfer.** The frontend sends:
   ```
   POST /api/transfer HTTP/1.1
   Host: app.example.com
   Cookie: SESSION=sess-abc123; XSRF-TOKEN=9f1c...
   X-XSRF-TOKEN: 9f1c...
   Content-Type: application/json

   {"amount":500,"to":"bob"}
   ```
   Note the header value was copied by the SPA's script; the `Cookie` header was attached automatically by the browser — two independent mechanisms converging on the same value.
4. **`CsrfFilter` (simulated by `validate`)** runs before the controller. `POST` is not a safe method, so the safe-method shortcut is skipped. `isCrossSite` is `false` (the request originates from the SPA's own page), so `browserWouldAttach` returns `true` immediately — the cookie is present. The filter then compares the `Cookie` value (`9f1c...`) to the `X-XSRF-TOKEN` header value (`9f1c...`): they match, so `CsrfResult.OK`.
5. **Request proceeds** to the controller, which debits the account and returns:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"status":"transferred","amount":500,"to":"bob"}
   ```
6. **Contrast with a forgery.** If `evil.com` had triggered this same `POST` via a hidden `fetch(..., { credentials: "include" })`, `isCrossSite` would be `true`. Under `SameSite=Lax`, `browserWouldAttach` returns `false` for a cross-site `POST` — the cookie never even rides along, so the filter short-circuits to `CsrfResult.BLOCKED_BY_SAMESITE` and the controller never runs. Even if `SameSite` were absent, `evil.com`'s script still could not have read the cookie to produce a matching `X-XSRF-TOKEN` header, so the plain double-submit comparison would fail regardless.

## 7. Gotchas & takeaways

> Forgetting `withHttpOnlyFalse()` — using plain `new CookieCsrfTokenRepository()` instead — leaves the `XSRF-TOKEN` cookie `HttpOnly`, which silently breaks the entire pattern: the SPA's own JavaScript can no longer read the value it's supposed to echo back, so every mutating request fails with `403` even though nothing looks obviously wrong in the network tab.

- The double-submit pattern's security comes from the browser's same-origin policy blocking cross-origin cookie reads, not from the cookie value being secret — anyone on the same origin, including the legitimate SPA, can read it freely.
- Default names matter: cookie `XSRF-TOKEN`, header `X-XSRF-TOKEN` — this exact pairing is what Angular's `HttpClientXsrfModule` and Axios auto-detect with zero extra frontend configuration.
- `SameSite=Lax`/`Strict` is a second, independent layer of defense — it can block the cookie from attaching to a cross-site request at all, before the double-submit comparison is even reached.
- Cookie-based CSRF protection is orthogonal to how you authenticate; a `HttpOnly` session cookie should still carry the actual credential so no script, same-origin or not, can exfiltrate it via casual `document.cookie` access.
- Keep CORS configuration strict (specific allowed origins, not `*`) when combined with credentialed requests — a loose CORS policy can undermine assumptions this pattern depends on.
