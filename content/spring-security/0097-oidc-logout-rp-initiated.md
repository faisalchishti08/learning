---
card: spring-security
gi: 97
slug: oidc-logout-rp-initiated
title: "OIDC logout (RP-initiated)"
---

## 1. What it is

Logging a user out of your application's own session (clearing `SecurityContextHolder`, invalidating the `HttpSession`, deleting the session cookie) does **not** log them out of the identity provider itself — the user's browser may still hold a live session with Google or Okta, so visiting "Login with Google" again could silently re-authenticate them with zero interaction. RP-Initiated Logout (RP = "Relying Party," the OIDC term for your application) is the OIDC extension that closes this gap: it redirects the browser to the provider's own logout endpoint after your local logout completes, using the `id_token_hint` (the ID token from card 0095/0096, presented back to prove which session to end) so the provider can also terminate its session and, per its configured `post_logout_redirect_uri`, send the browser back to your application afterward. Spring Security wires this via `OidcClientInitiatedLogoutSuccessHandler`, configured as the `logoutSuccessHandler` for `logout()`.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http, ClientRegistrationRepository repo) throws Exception {
    OidcClientInitiatedLogoutSuccessHandler oidcLogoutHandler =
            new OidcClientInitiatedLogoutSuccessHandler(repo);
    oidcLogoutHandler.setPostLogoutRedirectUri("{baseUrl}/"); // where the PROVIDER sends the browser back to

    http.logout(logout -> logout.logoutSuccessHandler(oidcLogoutHandler));
    return http.build();
}
```

## 2. Why & when

A plain `logout()` (no OIDC awareness) only ever touches your own application's session state — from the identity provider's point of view, nothing happened at all. For applications where this matters little (a single consumer app, low-sensitivity data), that's an acceptable gap. But for shared or corporate machines, or any deployment where "click logout" is expected to mean "this device is no longer signed in as me anywhere," leaving the provider's session alive is a real security gap — anyone using the same browser next can reopen the identity provider's still-active session and be waved straight back in.

Reach for RP-Initiated Logout when:

- Deploying on shared or kiosk-style machines where a provider session surviving local logout is a genuine risk.
- Building an internal application against a corporate IdP (Okta, Azure AD) where "logout" is expected, by policy, to mean a full sign-out, not just clearing this one app's cookie.
- Implementing "logout everywhere" functionality across multiple applications that all trust the same OIDC provider — RP-initiated logout is one building block toward that (true cross-application single sign-out additionally requires the provider to notify *other* relying parties, which is a separate, provider-side mechanism, front-channel or back-channel logout).
- The provider doesn't support RP-initiated logout at all (not every OIDC provider implements the `end_session_endpoint` from its discovery document) — in that case, `OidcClientInitiatedLogoutSuccessHandler` has nothing to redirect to, and only local logout is possible; this is important to check before assuming the redirect will work.

## 3. Core concept

```
Plain logout() (no OIDC):
    1. clear SecurityContextHolder
    2. invalidate HttpSession, delete cookie
    3. redirect browser to logoutSuccessUrl (e.g. "/login?logout")
    -- provider's own session: UNTOUCHED

OidcClientInitiatedLogoutSuccessHandler (RP-Initiated Logout):
    1. clear SecurityContextHolder
    2. invalidate HttpSession, delete cookie
    3. look up the end_session_endpoint from the provider's ClientRegistration/discovery metadata
    4. redirect browser to:
         {end_session_endpoint}?id_token_hint={the id_token from this session}
                                &post_logout_redirect_uri={configured callback}
    5. PROVIDER terminates its own session, then redirects the browser to post_logout_redirect_uri
    -- provider's own session: TERMINATED (if it supports this endpoint)
```

`id_token_hint` is what lets the provider know *which* of potentially many active sessions to end — it identifies the specific authentication event this application's login corresponded to.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence diagram of RP initiated logout the browser posts a logout request to the application which clears its own session and then redirects the browser to the providers end session endpoint carrying an id token hint the provider ends its own session and redirects the browser back to the applications configured post logout redirect uri">
  <text x="90" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">App Server</text>
  <text x="330" y="24" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="580" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Provider</text>

  <line x1="90" y1="35" x2="90" y2="245" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="330" y1="35" x2="330" y2="245" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="580" y1="35" x2="580" y2="245" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <line x1="330" y1="55" x2="95" y2="55" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#l97)"/>
  <text x="330" y="48" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">1. POST /logout</text>

  <rect x="40" y="65" width="220" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="150" y="84" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">2. clear SecurityContext + session</text>

  <line x1="90" y1="120" x2="325" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#l97b)"/>
  <text x="95" y="113" fill="#e6edf3" font-size="8.5" font-family="sans-serif">3. 302 -> end_session_endpoint?id_token_hint=..</text>

  <line x1="330" y1="150" x2="575" y2="150" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#l97)"/>
  <text x="335" y="143" fill="#e6edf3" font-size="8.5" font-family="sans-serif">4. GET end_session_endpoint</text>

  <rect x="470" y="160" width="150" height="26" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="545" y="177" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">5. end provider session</text>

  <line x1="580" y1="196" x2="335" y2="196" stroke="#8b949e" stroke-width="1.5" marker-end="url(#l97c)"/>
  <text x="575" y="212" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">6. 302 -> post_logout_redirect_uri</text>

  <line x1="330" y1="226" x2="95" y2="226" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#l97b)"/>
  <text x="330" y="238" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">7. GET post_logout_redirect_uri</text>

  <defs>
    <marker id="l97" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="l97b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="l97c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The extra two hops (3–6) are what distinguish RP-Initiated Logout from a plain local-only logout.

## 5. Runnable example

The scenario: model local logout alone, then add the redirect to a provider's `end_session_endpoint` carrying `id_token_hint`, then handle a provider that doesn't support this endpoint at all — falling back gracefully rather than breaking logout entirely.

### Level 1 — Basic

Plain local logout: clear session state, nothing more.

```java
import java.util.*;

public class OidcLogoutLevel1 {
    static class Session {
        String principal;
        String idToken;
        boolean active = true;
    }

    static void localLogout(Session session) {
        session.principal = null;
        session.idToken = null;
        session.active = false;
    }

    public static void main(String[] args) {
        Session session = new Session();
        session.principal = "alice";
        session.idToken = "id-tok-signed-jwt";

        System.out.println("before logout: active=" + session.active + " principal=" + session.principal);
        localLogout(session);
        System.out.println("after logout: active=" + session.active + " principal=" + session.principal);
        System.out.println("NOTE: the identity provider's own session is untouched by this alone");
    }
}
```

**How to run:** save as `OidcLogoutLevel1.java`, run `java OidcLogoutLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
before logout: active=true principal=alice
after logout: active=false principal=null
NOTE: the identity provider's own session is untouched by this alone
```

`localLogout` is exactly what a plain (non-OIDC-aware) `logout()` configuration does — it clears every trace of the local session, but has no way to reach the provider at all, so a still-active provider session is entirely out of its scope.

### Level 2 — Intermediate

Add the redirect to the provider's `end_session_endpoint`, carrying `id_token_hint` and `post_logout_redirect_uri` — mirroring `OidcClientInitiatedLogoutSuccessHandler`.

```java
import java.util.*;

public class OidcLogoutLevel2 {
    static class Session {
        String principal;
        String idToken;
        boolean active = true;
    }

    record ProviderMetadata(String endSessionEndpoint) {}

    static String buildLogoutRedirect(ProviderMetadata provider, String idToken, String postLogoutRedirectUri) {
        return provider.endSessionEndpoint()
                + "?id_token_hint=" + idToken
                + "&post_logout_redirect_uri=" + postLogoutRedirectUri;
    }

    static String localLogoutThenBuildProviderRedirect(Session session, ProviderMetadata provider, String appBaseUrl) {
        String idTokenForHint = session.idToken; // captured BEFORE clearing -- the provider needs it to identify the session
        session.principal = null;
        session.idToken = null;
        session.active = false;
        return buildLogoutRedirect(provider, idTokenForHint, appBaseUrl + "/");
    }

    public static void main(String[] args) {
        Session session = new Session();
        session.principal = "alice";
        session.idToken = "id-tok-signed-jwt";

        ProviderMetadata google = new ProviderMetadata("https://accounts.google.com/logout");

        String redirectUrl = localLogoutThenBuildProviderRedirect(session, google, "https://app.example.com");

        System.out.println("session active after local logout: " + session.active);
        System.out.println("redirecting browser to: " + redirectUrl);
    }
}
```

**How to run:** save as `OidcLogoutLevel2.java`, run `java OidcLogoutLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
session active after local logout: false
redirecting browser to: https://accounts.google.com/logout?id_token_hint=id-tok-signed-jwt&post_logout_redirect_uri=https://app.example.com/
```

What changed: `idTokenForHint` is deliberately captured *before* `session.idToken` is cleared — the local session state is wiped exactly as in Level 1, but the ID token value it held is preserved just long enough to build the provider redirect, since the provider needs it to identify which of its own sessions corresponds to this logout.

### Level 3 — Advanced

Not every provider supports RP-Initiated Logout — its `end_session_endpoint` might be entirely absent from the provider's metadata. Level 3 detects that case and falls back to local-only logout instead of building a broken redirect.

```java
import java.util.*;

public class OidcLogoutLevel3 {
    static class Session {
        String principal;
        String idToken;
        boolean active = true;
    }

    record ProviderMetadata(String registrationId, String endSessionEndpoint) {} // endSessionEndpoint may be null

    enum LogoutOutcome { LOCAL_ONLY, LOCAL_AND_PROVIDER_REDIRECT }
    record LogoutResult(LogoutOutcome outcome, String redirectUrl) {}

    static LogoutResult performLogout(Session session, ProviderMetadata provider, String appBaseUrl) {
        String idTokenForHint = session.idToken;
        String registrationId = provider.registrationId();

        // ALWAYS do local logout first, regardless of what the provider supports
        session.principal = null;
        session.idToken = null;
        session.active = false;

        if (provider.endSessionEndpoint() == null) {
            System.out.println("provider \"" + registrationId + "\" has no end_session_endpoint -- local logout only");
            return new LogoutResult(LogoutOutcome.LOCAL_ONLY, appBaseUrl + "/login?logout");
        }

        String redirectUrl = provider.endSessionEndpoint()
                + "?id_token_hint=" + idTokenForHint
                + "&post_logout_redirect_uri=" + appBaseUrl + "/";
        return new LogoutResult(LogoutOutcome.LOCAL_AND_PROVIDER_REDIRECT, redirectUrl);
    }

    public static void main(String[] args) {
        ProviderMetadata google = new ProviderMetadata("google", "https://accounts.google.com/logout");
        ProviderMetadata legacyIdp = new ProviderMetadata("legacy-idp", null); // does NOT support RP-initiated logout

        Session aliceSession = new Session();
        aliceSession.principal = "alice";
        aliceSession.idToken = "id-tok-alice";

        Session bobSession = new Session();
        bobSession.principal = "bob";
        bobSession.idToken = "id-tok-bob";

        LogoutResult aliceResult = performLogout(aliceSession, google, "https://app.example.com");
        System.out.println("alice: " + aliceResult.outcome() + " -> " + aliceResult.redirectUrl());

        LogoutResult bobResult = performLogout(bobSession, legacyIdp, "https://app.example.com");
        System.out.println("bob: " + bobResult.outcome() + " -> " + bobResult.redirectUrl());

        System.out.println("alice session active: " + aliceSession.active + ", bob session active: " + bobSession.active);
    }
}
```

**How to run:** save as `OidcLogoutLevel3.java`, run `java OidcLogoutLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
provider "legacy-idp" has no end_session_endpoint -- local logout only
alice: LOCAL_AND_PROVIDER_REDIRECT -> https://accounts.google.com/logout?id_token_hint=id-tok-alice&post_logout_redirect_uri=https://app.example.com/
bob: LOCAL_ONLY -> https://app.example.com/login?logout
alice session active: false, bob session active: false
```

What changed: `performLogout` always clears the local session first — regardless of what happens next — and only *attempts* the provider redirect when `endSessionEndpoint` is actually present; bob's provider has none, so his logout silently degrades to exactly Level 1's behavior rather than throwing or building a URL that would 404. Both sessions end up equally logged-out locally; only the provider-side outcome differs.

## 6. Walkthrough

Trace alice's full logout from Level 3 as a concrete HTTP sequence.

**Step 1 — the browser submits the logout request:**
```
POST /logout HTTP/1.1
Host: app.example.com
Cookie: JSESSIONID=sess-alice
```

**Step 2 — local logout runs first, unconditionally.** This corresponds to the first three lines inside `performLogout`: `session.principal = null`, `session.idToken = null` (but only after `idTokenForHint` captured its value), `session.active = false`. `SecurityContextHolder` is cleared and the `HttpSession` is invalidated exactly the same way a plain `logout()` would do it.

**Step 3 — the provider check.** `provider.endSessionEndpoint()` for `google` is `"https://accounts.google.com/logout"`, non-null, so the method proceeds to build the redirect rather than returning `LOCAL_ONLY`.

**Step 4 — the redirect is built and sent to the browser:**
```
HTTP/1.1 302 Found
Location: https://accounts.google.com/logout?id_token_hint=id-tok-alice&post_logout_redirect_uri=https://app.example.com/
Set-Cookie: JSESSIONID=; Max-Age=0
```
The `Set-Cookie` header deleting the session cookie happens at the same point Level 3's `session.active = false` did — the application no longer considers this browser authenticated, independent of anything the provider does next.

**Step 5 — the browser follows the redirect to Google:**
```
GET /logout?id_token_hint=id-tok-alice&post_logout_redirect_uri=https%3A%2F%2Fapp.example.com%2F HTTP/1.1
Host: accounts.google.com
```
Google uses `id_token_hint` to identify which of potentially several active sessions in this browser corresponds to this application's login, and terminates that specific one.

**Step 6 — Google redirects back to the configured `post_logout_redirect_uri`:**
```
HTTP/1.1 302 Found
Location: https://app.example.com/
```

**Step 7 — the browser lands back on the application, now logged out both locally and at the provider.** A subsequent click on "Login with Google" would require the user to authenticate again — no silently-reused provider session remains, in contrast to bob's `legacy-idp` case, where step 3's check failed and only local logout (Level 1's behavior) ever ran.

```
performLogout(alice, google)
   local logout            -> ALWAYS runs, regardless of provider support
   endSessionEndpoint != null -> build provider redirect
       -> browser -> Google -> Google ends its session -> browser -> back to app
   RESULT: fully logged out, both locally AND at the provider

performLogout(bob, legacy-idp)
   local logout            -> ALWAYS runs
   endSessionEndpoint == null -> skip provider redirect entirely
   RESULT: logged out locally only; legacy-idp's own session (if any) survives
```

## 7. Gotchas & takeaways

> **Gotcha:** `id_token_hint` must be captured from the session *before* local logout clears it — if the ID token is wiped first and only then read for the redirect, the hint is empty or stale, and the provider either can't identify which session to end or silently no-ops the request. Order matters: read what you need from the session, then clear it, not the reverse.

- Local logout and provider (RP-Initiated) logout are two separate steps with two separate scopes — clearing your own `SecurityContext`/session never, by itself, touches the identity provider's session.
- `OidcClientInitiatedLogoutSuccessHandler` adds exactly one thing on top of plain `logout()`: a redirect to the provider's `end_session_endpoint`, carrying `id_token_hint` (to identify the session) and `post_logout_redirect_uri` (where to send the browser afterward).
- Not every provider implements RP-Initiated Logout — check its OIDC discovery metadata for an `end_session_endpoint` before assuming this redirect will work; when it's absent, only local logout is possible, and that's a legitimate, expected fallback rather than an error condition.
- `post_logout_redirect_uri` typically must be pre-registered with the provider (much like the login `redirect_uri`), or the provider will reject or ignore it rather than honoring an arbitrary redirect target.
- True cross-application single sign-out (ending sessions in *other* relying parties too, not just this application and the provider) requires additional provider-side mechanisms (front-channel or back-channel logout notifications) beyond what RP-Initiated Logout alone provides.
