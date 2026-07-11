---
card: spring-security
gi: 75
slug: csrf-protection-csrftoken-csrftokenrepository
title: "CSRF protection (CsrfToken, CsrfTokenRepository)"
---

## 1. What it is

**Cross-Site Request Forgery (CSRF)** protection stops a malicious site from tricking a logged-in user's browser into submitting a state-changing request (like "transfer money" or "change email") to your app without the user's consent. Spring Security's defence is a `CsrfToken`: a random, unguessable value the server hands the browser, which the browser must echo back on every unsafe request (`POST`/`PUT`/`DELETE`/`PATCH`). A `CsrfTokenRepository` is the strategy interface that decides *where* that token is stored between requests — the default (`HttpSessionCsrfTokenRepository`) keeps it in the HTTP session; `CookieCsrfTokenRepository` keeps it in a cookie instead (used for SPAs, covered next card).

```java
http.csrf(csrf -> csrf
    .csrfTokenRepository(new HttpSessionCsrfTokenRepository())
);
```

## 2. Why & when

A forged cross-site request carries the victim's session cookie automatically (browsers attach cookies to every request to a domain, regardless of which page initiated it) — so a hidden auto-submitting form on `evil.com` pointed at `yourbank.com/transfer` would succeed *without* CSRF protection, because the browser happily attaches the real session cookie. The fix relies on something the attacker's page *cannot* read or guess: a per-session (or per-request) random token that must be present in the request body or a header, not just the cookie jar. Since `evil.com` can trigger the request but cannot read `yourbank.com`'s page to extract the token, it cannot include a valid one.

Reach for this understanding when:

- Building any traditional server-rendered form (login, settings, checkout) — Spring Security enables CSRF protection **by default** for all state-changing HTTP methods.
- Debugging a `403 Forbidden` on a `POST` that otherwise looks correct — a missing or stale CSRF token is the single most common cause.
- Deciding *where* to store the token — session-backed (stateful apps with server-rendered forms) versus cookie-backed (stateless APIs / SPAs, next card).
- Explicitly disabling CSRF — appropriate **only** for genuinely stateless APIs authenticated via a bearer token (no cookies involved at all), never for cookie-authenticated browser apps.

## 3. Core concept

```
1. Browser GETs a form page
2. Server generates CsrfToken (random value), stores it via CsrfTokenRepository,
   embeds it in a hidden <input> in the rendered form
3. Browser POSTs the form -- the hidden input carries the token back
4. CsrfFilter compares: token submitted == token in CsrfTokenRepository ?
   MATCH    -> request proceeds
   NO MATCH / MISSING -> 403 Forbidden, request rejected BEFORE reaching the controller
```

The token never leaves the origin server's own rendered pages, so a third-party site cannot forge it, even though it can force the browser to send the request.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Legitimate flow the server issues a csrf token embedded in a form and the browser echoes it back so the request is accepted an attacker page cannot read that token so its forged request is rejected with 403">
  <rect x="15" y="15" width="290" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="160" y="33" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Legitimate flow</text>
  <text x="30" y="55" fill="#e6edf3" font-size="9.5" font-family="sans-serif">1. GET /transfer-form</text>
  <text x="30" y="72" fill="#e6edf3" font-size="9.5" font-family="sans-serif">2. server embeds CsrfToken</text>
  <text x="30" y="89" fill="#e6edf3" font-size="9.5" font-family="sans-serif">3. POST includes token</text>
  <text x="30" y="106" fill="#3fb950" font-size="9.5" font-family="sans-serif">4. token matches -&gt; 200 OK</text>

  <rect x="335" y="15" width="290" height="110" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.4"/>
  <text x="480" y="33" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Forged flow (evil.com)</text>
  <text x="350" y="55" fill="#e6edf3" font-size="9.5" font-family="sans-serif">1. hidden auto-submit form</text>
  <text x="350" y="72" fill="#e6edf3" font-size="9.5" font-family="sans-serif">2. cannot read your session's</text>
  <text x="350" y="87" fill="#e6edf3" font-size="9.5" font-family="sans-serif">   CsrfToken (same-origin only)</text>
  <text x="350" y="106" fill="#f85149" font-size="9.5" font-family="sans-serif">3. token missing -&gt; 403</text>

  <rect x="180" y="160" width="280" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="320" y="182" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">CsrfFilter</text>
  <text x="320" y="202" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">compares submitted token</text>
  <text x="320" y="217" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">to CsrfTokenRepository value</text>
</svg>

The browser's cookie jar alone is not enough to authorize a request — the token must be echoed from a page the attacker could never have read.

## 5. Runnable example

The scenario: a tiny in-memory transfer endpoint protected by a simulated `CsrfFilter`, evolving from "always accept" to full token issue/validate/rotate behaviour.

### Level 1 — Basic

A repository holding one token, and a filter that rejects requests missing it.

```java
import java.util.*;

public class CsrfLevel1 {
    record CsrfToken(String value) {}

    static class CsrfTokenRepository {
        private CsrfToken current;
        CsrfToken generateToken() { return new CsrfToken(UUID.randomUUID().toString()); }
        void saveToken(CsrfToken t) { this.current = t; }
        CsrfToken loadToken() { return current; }
    }

    static boolean handleRequest(CsrfTokenRepository repo, String method, String submittedToken) {
        if (method.equals("GET")) return true; // safe method, no check needed
        CsrfToken expected = repo.loadToken();
        return expected != null && expected.value().equals(submittedToken);
    }

    public static void main(String[] args) {
        CsrfTokenRepository repo = new CsrfTokenRepository();

        // GET renders the form: server generates + saves a token, would embed it as hidden input
        CsrfToken issued = repo.generateToken();
        repo.saveToken(issued);
        System.out.println("GET /transfer-form -> issued token " + issued.value());

        // legitimate POST echoes the token back
        boolean legit = handleRequest(repo, "POST", issued.value());
        System.out.println("Legit POST with correct token: " + (legit ? "200 OK" : "403 Forbidden"));

        // forged POST from evil.com has no way to know the token
        boolean forged = handleRequest(repo, "POST", null);
        System.out.println("Forged POST with no token: " + (forged ? "200 OK" : "403 Forbidden"));
    }
}
```

**How to run:** save as `CsrfLevel1.java`, run `java CsrfLevel1.java` (JDK 17+ runs single files directly, no compile step needed).

Expected output:
```
GET /transfer-form -> issued token <some-uuid>
Legit POST with correct token: 200 OK
Forged POST with no token: 403 Forbidden
```

### Level 2 — Intermediate

Real Spring Security stores the token per-session and regenerates a *new* token after each successful login (to prevent session-fixation-style reuse). We add that behaviour and a case-sensitive comparison.

```java
import java.util.*;

public class CsrfLevel2 {
    record CsrfToken(String value) {}

    static class SessionCsrfRepository {
        private final Map<String, CsrfToken> bySession = new HashMap<>();

        CsrfToken generateToken() { return new CsrfToken(UUID.randomUUID().toString()); }

        void saveToken(String sessionId, CsrfToken t) { bySession.put(sessionId, t); }

        CsrfToken loadToken(String sessionId) { return bySession.get(sessionId); }

        // regenerate on login -- an old token (possibly leaked before authentication) stops working
        CsrfToken rotateOnLogin(String sessionId) {
            CsrfToken fresh = generateToken();
            saveToken(sessionId, fresh);
            return fresh;
        }
    }

    static boolean checkRequest(SessionCsrfRepository repo, String sessionId, String method, String submitted) {
        if (method.equals("GET") || method.equals("HEAD") || method.equals("OPTIONS")) return true;
        CsrfToken expected = repo.loadToken(sessionId);
        return expected != null && submitted != null && expected.value().equals(submitted);
    }

    public static void main(String[] args) {
        SessionCsrfRepository repo = new SessionCsrfRepository();
        String sessionId = "JSESSIONID-abc123";

        CsrfToken beforeLogin = repo.generateToken();
        repo.saveToken(sessionId, beforeLogin);
        System.out.println("Anonymous GET -> token " + beforeLogin.value());

        CsrfToken afterLogin = repo.rotateOnLogin(sessionId);
        System.out.println("After login -> ROTATED token " + afterLogin.value());

        boolean staleTokenReplay = checkRequest(repo, sessionId, "POST", beforeLogin.value());
        System.out.println("POST replaying pre-login token: " + (staleTokenReplay ? "200 OK" : "403 Forbidden"));

        boolean freshTokenUsed = checkRequest(repo, sessionId, "POST", afterLogin.value());
        System.out.println("POST with current token: " + (freshTokenUsed ? "200 OK" : "403 Forbidden"));
    }
}
```

**How to run:** `java CsrfLevel2.java`. What changed: the token is now keyed per session, and `rotateOnLogin` shows why Spring Security refreshes the CSRF token after authentication — a token issued to an anonymous visitor should not silently carry over into their authenticated session.

### Level 3 — Advanced

Real deployments must also handle: multiple concurrent tabs (the token must not change on every page load, only on rotation events), the `CsrfToken` being deferred/lazily-loaded (Spring's `XorCsrfTokenRequestAttributeHandler` masks the token per-request via a lightweight XOR to defeat BREACH-style compression attacks), and rejecting requests whose method is unsafe but whose token header is entirely absent versus present-but-wrong (both must fail, but we track the distinct reasons for diagnostics).

```java
import java.util.*;

public class CsrfLevel3 {
    record CsrfToken(String token, String headerName, String parameterName) {}

    enum CsrfResult { OK, MISSING, MISMATCH, SAFE_METHOD }

    static class RobustCsrfRepository {
        private final Map<String, CsrfToken> bySession = new HashMap<>();
        private final Random random = new Random();

        CsrfToken generateToken() {
            String raw = Long.toHexString(random.nextLong()) + Long.toHexString(random.nextLong());
            return new CsrfToken(raw, "X-CSRF-TOKEN", "_csrf");
        }

        void saveToken(String sessionId, CsrfToken t) { bySession.put(sessionId, t); }
        CsrfToken loadToken(String sessionId) { return bySession.get(sessionId); }

        // BREACH mitigation: mask the real token with a random per-request pad via XOR,
        // so the token bytes sent over the wire differ every time even though they decode
        // back to the same underlying secret.
        String maskForTransmission(CsrfToken t) {
            byte[] secret = t.token().getBytes();
            byte[] pad = new byte[secret.length];
            random.nextBytes(pad);
            byte[] masked = new byte[secret.length * 2];
            for (int i = 0; i < secret.length; i++) {
                masked[i] = pad[i];
                masked[secret.length + i] = (byte) (secret[i] ^ pad[i]);
            }
            return Base64.getEncoder().encodeToString(masked);
        }

        String unmask(String maskedBase64) {
            byte[] masked = Base64.getDecoder().decode(maskedBase64);
            int half = masked.length / 2;
            byte[] secret = new byte[half];
            for (int i = 0; i < half; i++) secret[i] = (byte) (masked[i] ^ masked[half + i]);
            return new String(secret);
        }
    }

    static Set<String> SAFE_METHODS = Set.of("GET", "HEAD", "OPTIONS", "TRACE");

    static CsrfResult validate(RobustCsrfRepository repo, String sessionId, String method, String submittedMasked) {
        if (SAFE_METHODS.contains(method)) return CsrfResult.SAFE_METHOD;
        CsrfToken expected = repo.loadToken(sessionId);
        if (expected == null || submittedMasked == null) return CsrfResult.MISSING;
        String unmasked = repo.unmask(submittedMasked);
        return expected.token().equals(unmasked) ? CsrfResult.OK : CsrfResult.MISMATCH;
    }

    public static void main(String[] args) {
        RobustCsrfRepository repo = new RobustCsrfRepository();
        String sessionId = "JSESSIONID-xyz789";

        CsrfToken token = repo.generateToken();
        repo.saveToken(sessionId, token);

        // simulate two page loads -- each masks the SAME underlying token differently
        String maskedForPageA = repo.maskForTransmission(token);
        String maskedForPageB = repo.maskForTransmission(token);
        System.out.println("Same token, two different masked encodings: " + !maskedForPageA.equals(maskedForPageB));

        System.out.println("GET request: " + validate(repo, sessionId, "GET", null));
        System.out.println("POST with valid masked token from page A: " + validate(repo, sessionId, "POST", maskedForPageA));
        System.out.println("POST with valid masked token from page B: " + validate(repo, sessionId, "POST", maskedForPageB));
        System.out.println("POST with no token at all: " + validate(repo, sessionId, "POST", null));
        String tampered = Base64.getEncoder().encodeToString(new byte[]{1, 2, 3, 4});
        System.out.println("POST with tampered token: " + validate(repo, sessionId, "POST", tampered));
    }
}
```

**How to run:** `java CsrfLevel3.java`. This adds the two production-flavoured hard cases: (1) BREACH mitigation via per-request XOR masking, so the wire-visible token differs across requests even though it always unmasks to the same secret compared server-side; (2) a `CsrfResult` enum that distinguishes *why* a request failed (`MISSING` vs `MISMATCH` vs correctly bypassed via `SAFE_METHOD`), which is exactly the granularity Spring Security's `AccessDeniedException` handling exposes to a custom `AccessDeniedHandler`.

## 6. Walkthrough

Trace Level 3 end-to-end for a real form submission:

1. **`GET /transfer-form`** arrives. Method is safe, so no CSRF check runs. The server calls `generateToken()`, producing a random `CsrfToken`, and `saveToken(sessionId, token)` stores it against the session.
2. **Rendering.** The server calls `maskForTransmission(token)` and embeds the *masked* value as a hidden `<input name="_csrf" value="...">` — the raw secret token itself never appears in the rendered HTML.
   ```html
   <form method="post" action="/transfer">
     <input type="hidden" name="_csrf" value="qk3F...base64...">
     ...
   </form>
   ```
3. **`POST /transfer`** — the browser submits the form body including that hidden field. Request:
   ```
   POST /transfer HTTP/1.1
   Cookie: JSESSIONID=xyz789
   Content-Type: application/x-www-form-urlencoded

   amount=500&to=bob&_csrf=qk3F...base64...
   ```
4. **`CsrfFilter` (simulated by `validate`)** runs *before* the controller. It loads the expected `CsrfToken` from the session-keyed repository, unmasks the submitted value via XOR, and compares it to the stored secret.
5. **Match → request proceeds** to the controller/service/repository layers exactly as normal; **mismatch or missing → `403 Forbidden`** is returned immediately, and the controller method body never executes at all.
6. **Response** on success: `200 OK` with the transfer confirmation; on failure: `403 Forbidden` with an `AccessDeniedException`-derived body, no state changed.

The forged-request path from part 4's diagram never reaches step 4 with a valid token, because `evil.com` never received the masked value from step 2 — it can only guess.

## 7. Gotchas & takeaways

> Disabling CSRF (`.csrf(csrf -> csrf.disable())`) is sometimes copy-pasted from tutorials to "fix" a confusing `403`. Only do this for genuinely stateless, cookie-free, bearer-token-authenticated APIs — for anything using session cookies, disabling CSRF reopens the exact hole this card defends against.

- CSRF protection only guards *unsafe* methods (`POST`, `PUT`, `PATCH`, `DELETE`); `GET`/`HEAD`/`OPTIONS` are assumed side-effect-free and are never checked.
- The token must travel through a channel the attacker's origin cannot read — a hidden form field or a custom header, never a cookie alone (cookies are sent automatically regardless of origin).
- `CsrfTokenRepository` is pluggable: session-backed for classic server-rendered apps, cookie-backed (`CookieCsrfTokenRepository`, next card) for SPAs that can't easily thread a hidden form field.
- Real Spring Security masks the token per-request (XOR against a random pad) specifically to defeat BREACH, a compression-oracle attack — don't be surprised the wire value changes every time even though validation always succeeds for the same session.
- Rotate the token after login/privilege changes so a token an attacker might have observed pre-authentication becomes useless afterward.
