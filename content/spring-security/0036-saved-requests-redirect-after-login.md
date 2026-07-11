---
card: spring-security
gi: 36
slug: saved-requests-redirect-after-login
title: "Saved requests & redirect after login"
---

## 1. What it is

`RequestCache` (with `HttpSessionRequestCache` as the default implementation) is what makes "redirected to login, then landed back where you were headed" possible: when an unauthenticated request hits a protected resource, `ExceptionTranslationFilter` saves the full details of that original request (URL, method, query parameters, even headers) into a `SavedRequest` object stored in the `RequestCache`, before redirecting to the login page — and on successful login, `formLogin`'s default success handler (`SavedRequestAwareAuthenticationSuccessHandler`) checks the cache and, if a saved request exists, redirects there instead of to any fixed default URL.

```java
// conceptually, what happens when an unauthenticated GET /account/settings?tab=security is denied:
requestCache.saveRequest(request, response); // stores method, URL, params, headers as a SavedRequest
authenticationEntryPoint.commence(request, response, exception); // redirect to /login

// on successful login:
SavedRequest saved = requestCache.getRequest(request, response);
String redirectUrl = (saved != null) ? saved.getRedirectUrl() : defaultSuccessUrl;
response.sendRedirect(redirectUrl); // back to /account/settings?tab=security, not just "/"
```

## 2. Why & when

Without a saved request, every successful login would have to redirect to some single fixed destination (typically `/`), regardless of what the user was actually trying to reach before being interrupted by the login requirement — a frustrating experience for a user who clicked a specific deep link (an email notification linking to one particular order, a bookmarked settings page) only to land on a generic homepage after logging in, and then have to navigate back manually. The saved-request mechanism closes this gap entirely automatically for standard form login, requiring no extra application code.

Reach for understanding or customizing `RequestCache` when:

- Debugging why a login redirect lands somewhere unexpected — checking whether a request was actually saved (and to what URL), and whether `defaultSuccessUrl(url, true)` (from the earlier form-login card) is configured to override it, are the first two things to check.
- Building a stateless API where saved-request behavior makes no sense at all (there's no "redirect back" concept for a JSON client) — `NullRequestCache` explicitly disables the mechanism, avoiding pointless session writes for requests that will never benefit from it.
- A non-GET request (a `POST` submitting a form) triggers a login requirement — the saved request can restore the URL, but generally cannot safely resubmit the original request body automatically; this is a well-known limitation worth understanding when a user's in-progress form submission is interrupted by an expired session.

## 3. Core concept

```
 unauthenticated GET /account/settings?tab=security
        |
        v
 ExceptionTranslationFilter catches the AuthenticationException
        |
        v
 requestCache.saveRequest(request, response)
     stores a SavedRequest: method=GET, url=/account/settings, queryString=tab=security, headers=[...]
        |
        v
 authenticationEntryPoint.commence(...) --> redirect to /login
        |
        v
 (user submits credentials, authentication succeeds)
        |
        v
 SavedRequestAwareAuthenticationSuccessHandler:
     savedRequest = requestCache.getRequest(request, response)
     IF present: redirect to savedRequest.getRedirectUrl()  ("/account/settings?tab=security")
     ELSE:       redirect to the configured defaultSuccessUrl
```

The entire round trip — save, redirect to login, restore on success — happens without the application needing to write any of this logic itself.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unauthenticated request to a deep link is saved by RequestCache before redirecting to the login page after successful authentication the success handler checks the cache and redirects back to the originally saved deep link rather than a generic default">
  <rect x="15" y="20" width="200" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="115" y="38" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">GET /account/settings?tab=security</text>
  <text x="115" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(unauthenticated)</text>

  <rect x="260" y="20" width="160" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="38" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">RequestCache</text>
  <text x="340" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.saveRequest(...)</text>

  <rect x="460" y="20" width="150" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="535" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">redirect -&gt; /login</text>

  <rect x="15" y="120" width="200" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="115" y="145" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">login succeeds</text>

  <rect x="260" y="120" width="160" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="138" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">RequestCache</text>
  <text x="340" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.getRequest(...)</text>

  <rect x="460" y="120" width="150" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="138" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">redirect -&gt; back to</text>
  <text x="535" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">/account/settings?tab=security</text>

  <defs><marker id="a36" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="215" y1="41" x2="260" y2="41" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a36)"/>
  <line x1="420" y1="41" x2="460" y2="41" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a36)"/>
  <line x1="215" y1="141" x2="260" y2="141" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a36)"/>
  <line x1="420" y1="141" x2="460" y2="141" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a36)"/>
</svg>

The same deep link that was interrupted by a login requirement is exactly where the user lands once authenticated.

## 5. Runnable example

The scenario: model `RequestCache`'s save/restore lifecycle end to end, then show the interaction with `defaultSuccessUrl(url, true)` overriding it, then handle the non-GET-request limitation explicitly, matching a genuinely production-relevant edge case.

### Level 1 — Basic

A minimal request cache: save a request before redirecting to login, restore it after successful login.

```java
import java.util.*;

public class SavedRequestLevel1 {
    record SavedRequest(String method, String url, String queryString) {
        String getRedirectUrl() { return queryString == null ? url : url + "?" + queryString; }
    }

    static Map<String, SavedRequest> requestCache = new HashMap<>(); // sessionId -> SavedRequest

    static String handleUnauthenticated(String sessionId, String method, String url, String queryString) {
        requestCache.put(sessionId, new SavedRequest(method, url, queryString));
        return "302 Found -> Location: /login";
    }

    static String handleLoginSuccess(String sessionId) {
        SavedRequest saved = requestCache.remove(sessionId);
        String target = (saved != null) ? saved.getRedirectUrl() : "/"; // fall back if nothing was saved
        return "302 Found -> Location: " + target;
    }

    public static void main(String[] args) {
        String sessionId = "JSESSIONID-abc";
        System.out.println(handleUnauthenticated(sessionId, "GET", "/account/settings", "tab=security"));
        System.out.println(handleLoginSuccess(sessionId));
    }
}
```

How to run: `java SavedRequestLevel1.java`

`handleUnauthenticated` stores the original method, URL, and query string keyed by session ID; `handleLoginSuccess` retrieves and removes that entry, reconstructing the full original URL (`"/account/settings?tab=security"`) as the redirect target instead of a generic default.

### Level 2 — Intermediate

Add `defaultSuccessUrl(url, alwaysUse=true)`-style override, showing it takes precedence over any saved request, matching the real interaction between these two configuration options from the form-login card.

```java
import java.util.*;

public class SavedRequestLevel2 {
    record SavedRequest(String method, String url, String queryString) {
        String getRedirectUrl() { return queryString == null ? url : url + "?" + queryString; }
    }

    static Map<String, SavedRequest> requestCache = new HashMap<>();
    static String defaultSuccessUrl = "/dashboard";
    static boolean alwaysUseDefaultSuccessUrl = false;

    static String handleUnauthenticated(String sessionId, String method, String url, String queryString) {
        requestCache.put(sessionId, new SavedRequest(method, url, queryString));
        return "302 Found -> Location: /login";
    }

    static String handleLoginSuccess(String sessionId) {
        SavedRequest saved = requestCache.remove(sessionId);
        String target;
        if (alwaysUseDefaultSuccessUrl) {
            target = defaultSuccessUrl; // saved request COMPUTED (and discarded via remove) but IGNORED
        } else {
            target = (saved != null) ? saved.getRedirectUrl() : defaultSuccessUrl;
        }
        return "302 Found -> Location: " + target;
    }

    public static void main(String[] args) {
        String sessionId = "JSESSIONID-abc";
        handleUnauthenticated(sessionId, "GET", "/orders/42", null);

        System.out.println("alwaysUseDefaultSuccessUrl=false (honors saved request): " + handleLoginSuccess(sessionId));

        handleUnauthenticated(sessionId, "GET", "/orders/42", null);
        alwaysUseDefaultSuccessUrl = true;
        System.out.println("alwaysUseDefaultSuccessUrl=true (ignores saved request): " + handleLoginSuccess(sessionId));
    }
}
```

How to run: `java SavedRequestLevel2.java`

With `alwaysUseDefaultSuccessUrl = false`, the saved `/orders/42` request is correctly honored; with it set to `true`, the exact same saved request is retrieved (and removed from the cache) but its `getRedirectUrl()` value is never actually used — `target` is unconditionally set to `defaultSuccessUrl` instead, exactly matching `defaultSuccessUrl(url, true)`'s documented behavior of always overriding any saved request.

### Level 3 — Advanced

Handle the non-GET-request limitation explicitly: a `POST` form submission interrupted by a login requirement can have its *URL* restored, but not safely its original body — model the realistic compromise Spring Security's default behavior makes.

```java
import java.util.*;

public class SavedRequestLevel3 {
    record SavedRequest(String method, String url, String queryString, Map<String, String> formBody) {
        String getRedirectUrl() { return queryString == null ? url : url + "?" + queryString; }
    }

    static Map<String, SavedRequest> requestCache = new HashMap<>();

    static String handleUnauthenticated(String sessionId, String method, String url, String queryString, Map<String, String> formBody) {
        requestCache.put(sessionId, new SavedRequest(method, url, queryString, formBody));
        return "302 Found -> Location: /login";
    }

    static String handleLoginSuccess(String sessionId) {
        SavedRequest saved = requestCache.remove(sessionId);
        if (saved == null) return "302 Found -> Location: / (nothing saved)";

        if (!saved.method().equals("GET")) {
            // the URL CAN be restored, but the ORIGINAL POST body is NOT automatically resubmitted --
            // redirecting simply issues a fresh GET to that URL, which is often NOT equivalent to replaying the POST
            return "302 Found -> Location: " + saved.getRedirectUrl()
                    + "  (NOTE: original " + saved.method() + " body " + saved.formBody()
                    + " was NOT resubmitted -- redirect always issues a GET)";
        }
        return "302 Found -> Location: " + saved.getRedirectUrl();
    }

    public static void main(String[] args) {
        String getSession = "session-get";
        handleUnauthenticated(getSession, "GET", "/account/settings", "tab=security", Map.of());
        System.out.println("GET request restored cleanly: " + handleLoginSuccess(getSession));

        String postSession = "session-post";
        handleUnauthenticated(postSession, "POST", "/orders/checkout", null, Map.of("couponCode", "SAVE10"));
        System.out.println("POST request restored (with caveat): " + handleLoginSuccess(postSession));
    }
}
```

How to run: `java SavedRequestLevel3.java`

The `GET` case restores cleanly, landing the user back on `/account/settings?tab=security` exactly as they left it; the `POST` case restores the *URL* (`/orders/checkout`) but explicitly notes that the original form data (`{couponCode=SAVE10}`) was never resubmitted, since the redirect itself is always a `GET` — a real, user-visible limitation where a login interruption mid-checkout would land the user back on the checkout page, but without their coupon code already filled in, requiring them to re-enter it.

## 6. Walkthrough

Trace the `POST` scenario from Level 3 end to end.

1. `handleUnauthenticated("session-post", "POST", "/orders/checkout", null, Map.of("couponCode", "SAVE10"))` runs first, storing a `SavedRequest` with `method = "POST"`, `url = "/orders/checkout"`, `queryString = null`, and `formBody = {couponCode: SAVE10}` under `"session-post"` in `requestCache`, then returns the redirect-to-login message.
2. This models the moment a user, mid-checkout, has their session expire (or was never logged in for a checkout requiring authentication) — their in-progress form submission, including the coupon code they'd just entered, is captured before they're sent to log in.
3. `handleLoginSuccess("session-post")` runs after a successful login: `requestCache.remove("session-post")` retrieves and deletes the saved entry, assigning it to `saved`.
4. `saved.method().equals("GET")` evaluates `"POST".equals("GET")`, which is `false`, so the method takes the non-GET branch: it computes `saved.getRedirectUrl()` (which is simply `"/orders/checkout"`, since `queryString` is `null`) and appends the explicit caveat noting the original form body was not resubmitted.
5. The final returned string documents both facts clearly: the redirect target is correct (the user does land back on the checkout page), but the note makes explicit that `{couponCode=SAVE10}` was never carried through — in a real application, this means the checkout page loads fresh, and the user must re-enter the coupon code, since there is no safe, general way to automatically resubmit an arbitrary `POST` body as part of an HTTP redirect.

```
POST /orders/checkout (couponCode=SAVE10) interrupted by login requirement
  -> SavedRequest{method=POST, url=/orders/checkout, formBody={couponCode=SAVE10}} cached
  -> after login: redirect to /orders/checkout (URL restored)
  -> but formBody is NEVER resubmitted -- user must re-enter couponCode manually
```

## 7. Gotchas & takeaways

> **Gotcha:** assuming saved-request restoration means an entire interrupted form submission (URL *and* body) will be transparently replayed after login is a common misunderstanding — only the URL (and, for `GET` requests, query parameters) is restored; any `POST` body is never automatically resubmitted, since the restoration mechanism works by issuing a fresh redirect, which is inherently a `GET`.

- `RequestCache` (`HttpSessionRequestCache` by default) is what makes "redirected to login, then landed back on the original deep link" work automatically for standard form login, requiring no custom application code.
- `defaultSuccessUrl(url, true)` (from the earlier form-login card) always takes precedence over any saved request — understanding this interaction is essential when debugging an unexpected post-login redirect destination.
- Non-`GET` requests (form `POST` submissions) can only have their *URL* restored, never their original body — a real, user-facing limitation worth accounting for in any checkout-like flow that might be interrupted by an authentication requirement.
- `NullRequestCache` disables the entire mechanism, appropriate for stateless APIs where a "redirect back to where you were" concept doesn't apply at all.
