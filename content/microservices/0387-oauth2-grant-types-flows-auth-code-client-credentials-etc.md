---
card: microservices
gi: 387
slug: oauth2-grant-types-flows-auth-code-client-credentials-etc
title: "OAuth2 grant types / flows (auth code, client credentials, etc.)"
---

## 1. What it is

An OAuth2 **grant type** (also called a **flow**) is a specific, standardized sequence of steps a [client](0386-oauth2-roles-resource-owner-client-auth-server-resource-serv.md) follows to obtain an access token from the [authorization server](0386-oauth2-roles-resource-owner-client-auth-server-resource-serv.md). Different grant types exist because different kinds of clients have fundamentally different needs and trust levels: a server-side web app can safely hold a secret; a mobile app or single-page app cannot; a backend service acting as itself has no human user to redirect at all. Picking the wrong grant type for your client's situation is one of the most common OAuth2 mistakes.

## 2. Why & when

You need to choose a grant type deliberately, not by copying whatever example you found first, because each one makes different security assumptions:

- **Authorization code** is the flow to use whenever a human user needs to log in and delegate access, and your client can either securely hold a secret (a confidential server-side client) or use PKCE to stay secure without one (a public client like a mobile or single-page app).
- **Client credentials** is the flow to use for pure machine-to-machine calls — a backend job or one microservice calling another as *itself*, with no human resource owner involved at all.
- **Refresh token** isn't a way to *get* the first token, but a way to *renew* one without forcing the user to log in again — used alongside authorization code to keep short-lived access tokens practical.
- **Legacy grants** (resource owner password credentials, implicit) exist in the spec but are now discouraged — password credentials requires the client to handle the user's raw password (defeating OAuth2's whole purpose), and implicit exposes tokens directly in URLs where they can leak into browser history and referrer headers.

You pick the grant type based on one question: **who is present, and what can this client safely hold?** A human at a browser with a confidential backend behind it: authorization code. A backend service with no human present: client credentials. A user is present but there's no confidential backend (mobile/SPA): authorization code with PKCE.

## 3. Core concept

Think of grant types like different ways to check into a hotel. **Authorization code** is like the front desk calling your phone to confirm your identity before handing the concierge (the client) your room key — an indirect, verified handoff where the concierge never sees your ID directly, just receives an already-verified key. **Client credentials** is like a hotel's own cleaning-service company badging into service areas with its own company ID — no guest is involved at all; the company simply proves it is who it says it is. **Refresh token** is like a keycard that's about to expire being swapped for a fresh one at a kiosk, without needing to show ID again, because you already proved who you were recently enough.

The two grant types you'll use constantly in microservices:

1. **Authorization code flow**: (a) the client redirects the user's browser to the authorization server's login page; (b) the user authenticates and consents; (c) the authorization server redirects back to the client with a short-lived, single-use **authorization code** in the URL; (d) the client — server-side, out of the browser's view — exchanges that code plus its own client secret (or a PKCE code verifier) for an access token via a direct, back-channel call to the authorization server. The token itself never appears in the browser's address bar, which is what makes this flow secure.
2. **Client credentials flow**: (a) the client (a service) authenticates directly to the authorization server's token endpoint using its own client ID and secret; (b) the authorization server, with no user involved, issues an access token scoped to what that client is registered for. This is a single, direct request-response — no redirects, no browser, no user.
3. **PKCE (Proof Key for Code Exchange)** extends the authorization code flow for clients that can't safely hold a secret (mobile apps, SPAs): the client generates a random secret locally (the "code verifier"), sends a hashed version (the "code challenge") upfront, and later proves it holds the original by presenting the raw verifier when exchanging the code — so even if the authorization code is intercepted, it's useless without the verifier.
4. **Refresh tokens** are issued alongside access tokens in flows that support them, letting the client obtain a fresh access token without re-involving the user, until the refresh token itself expires or is revoked.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Authorization code flow involves a browser redirect through the user and a back-channel code exchange; client credentials flow is a direct machine-to-machine request with no user or browser involved" font-family="sans-serif">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">Authorization code (user present)</text>
  <rect x="20" y="35" width="80" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="56" fill="#e6edf3" font-size="9" text-anchor="middle">Browser</text>
  <rect x="130" y="35" width="80" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="170" y="56" fill="#e6edf3" font-size="9" text-anchor="middle">Auth server</text>
  <rect x="20" y="100" width="80" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="60" y="121" fill="#e6edf3" font-size="9" text-anchor="middle">Client (app)</text>
  <line x1="60" y1="69" x2="60" y2="100" stroke="#8b949e" marker-end="url(#a6)"/>
  <text x="15" y="88" fill="#8b949e" font-size="7">code (URL)</text>
  <line x1="100" y1="117" x2="170" y2="69" stroke="#6db33f" stroke-dasharray="3,2" marker-end="url(#a6)"/>
  <text x="150" y="95" fill="#6db33f" font-size="7">back-channel: code+secret -&gt; token</text>

  <text x="480" y="20" fill="#e6edf3" font-size="12" text-anchor="middle">Client credentials (no user)</text>
  <rect x="420" y="55" width="100" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="470" y="76" fill="#e6edf3" font-size="9" text-anchor="middle">Service (client)</text>
  <rect x="560" y="55" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="590" y="76" fill="#e6edf3" font-size="8" text-anchor="middle">Auth svr</text>
  <line x1="520" y1="72" x2="560" y2="72" stroke="#6db33f" marker-end="url(#a6)"/>
  <text x="540" y="62" fill="#6db33f" font-size="7" text-anchor="middle">id+secret</text>

  <line x1="60" y1="150" x2="60" y2="190" stroke="none"/>
  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle">Choice depends on: is a human present, and can this client hold a secret?</text>
  <defs>
    <marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Authorization code involves the user's browser and a separate back-channel exchange; client credentials is a single direct request with no user in the loop at all.

## 5. Runnable example

Scenario: a "reporting dashboard" web app needs to read a user's order history, and a separate nightly batch job needs to sync inventory data with no user involved. We model both grant types, starting with a naive single-step "login and get everything" approach, then a proper two-step authorization code exchange, then add PKCE to defend the code exchange against interception.

### Level 1 — Basic

```java
// File: NaiveSingleStepGrant.java -- collapses "user logs in" and "token issued"
// into ONE step with no separation between the browser-visible part and the
// back-channel part -- realistic tokens should NEVER be exposed this directly.
import java.util.*;

public class NaiveSingleStepGrant {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");

    // Anti-pattern: password handled directly by what should be a THIRD-PARTY client, and
    // the token is returned in the SAME response visible to the browser -- no separation at all.
    static String loginAndGetToken(String username, String password) {
        if (!password.equals(USER_PASSWORDS.get(username))) return null;
        return "token-for-" + username; // exposed directly, e.g. in a URL fragment (the deprecated "implicit" pattern)
    }

    public static void main(String[] args) {
        String token = loginAndGetToken("alice", "hunter2");
        System.out.println("Token exposed directly to the browser-visible response: " + token);
        System.out.println("Anything that can see the browser's URL/history can now steal this token.");
    }
}
```

How to run: `java NaiveSingleStepGrant.java`

This mirrors the deprecated "implicit" grant: the token comes back in a response the browser itself can see directly (historically, in a URL fragment). Anything with access to browser history, a referrer header, or a shared machine can potentially recover that token. It also requires the client to handle the raw password, which authorization code flow specifically avoids.

### Level 2 — Intermediate

```java
// File: AuthorizationCodeFlow.java -- the PROPER two-step exchange: the browser-visible
// step yields only a short-lived, single-use CODE (not a token), and a separate
// back-channel exchange -- using a confidential client secret -- turns that code into a token.
import java.util.*;

public class AuthorizationCodeFlow {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");
    static final Map<String, String> REGISTERED_CLIENTS = Map.of("reporting-dashboard", "dashboard-client-secret");
    static final Map<String, String> ISSUED_CODES = new HashMap<>(); // code -> username, SINGLE USE

    // Step 1 (browser-visible): user authenticates, auth server issues a short-lived CODE, not a token.
    static String authenticateAndIssueCode(String username, String password) {
        if (!password.equals(USER_PASSWORDS.get(username))) return null;
        String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
        ISSUED_CODES.put(code, username);
        return code; // this is what the browser redirect carries -- USELESS on its own
    }

    // Step 2 (back-channel, NOT visible to the browser): client exchanges code + its OWN secret for a token.
    static String exchangeCodeForToken(String clientId, String clientSecret, String code) {
        if (!clientSecret.equals(REGISTERED_CLIENTS.get(clientId))) return null; // client itself must authenticate
        String username = ISSUED_CODES.remove(code); // SINGLE USE: removed immediately
        if (username == null) return null; // code invalid, expired, or already used
        return "token-for-" + username;
    }

    public static void main(String[] args) {
        String code = authenticateAndIssueCode("alice", "hunter2");
        System.out.println("Browser redirect carries code: " + code + " (a token would be far more dangerous to expose here)");

        String token = exchangeCodeForToken("reporting-dashboard", "dashboard-client-secret", code);
        System.out.println("Back-channel exchange produced token: " + token);

        // Replay attempt: try to use the SAME code again.
        String replayAttempt = exchangeCodeForToken("reporting-dashboard", "dashboard-client-secret", code);
        System.out.println("Replaying the same code: " + replayAttempt);
    }
}
```

How to run: `java AuthorizationCodeFlow.java`

Two clearly separate steps now exist. `authenticateAndIssueCode` is the browser-visible part — its output is a short-lived *code*, not a token, so even if it leaks via browser history it's far less dangerous than a token. `exchangeCodeForToken` is the back-channel part, requiring the client's own secret *and* removing the code from `ISSUED_CODES` the moment it's used — making the code genuinely single-use. The replay attempt at the end returns `null`, because the code was already consumed on the first exchange.

### Level 3 — Advanced

```java
// File: AuthorizationCodeWithPkce.java -- adds PKCE: a client that CANNOT safely
// hold a secret (a mobile app or single-page app) proves it initiated the flow by
// presenting a verifier that must hash to the challenge it sent upfront -- protecting
// the code exchange even without a confidential client secret.
import java.util.*;
import java.security.MessageDigest;
import java.util.Base64;

public class AuthorizationCodeWithPkce {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");
    // code -> [username, codeChallenge] -- PKCE ties the code to a specific challenge from THIS client instance.
    static final Map<String, String[]> ISSUED_CODES = new HashMap<>();

    static String sha256Base64Url(String input) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(input.getBytes("UTF-8"));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(hash);
    }

    // Step 1: client generates a random verifier LOCALLY, sends only the hashed challenge.
    static String authenticateAndIssueCode(String username, String password, String codeChallenge) {
        if (!password.equals(USER_PASSWORDS.get(username))) return null;
        String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
        ISSUED_CODES.put(code, new String[]{username, codeChallenge});
        return code;
    }

    // Step 2: client must present the ORIGINAL verifier; server re-hashes it and compares to the stored challenge.
    static String exchangeCodeForToken(String code, String codeVerifier) throws Exception {
        String[] entry = ISSUED_CODES.remove(code); // single use, same as before
        if (entry == null) return "DENIED: unknown or already-used code";
        String username = entry[0], expectedChallenge = entry[1];
        String recomputedChallenge = sha256Base64Url(codeVerifier);
        if (!recomputedChallenge.equals(expectedChallenge)) {
            return "DENIED: PKCE verifier does not match the original challenge -- code interception suspected";
        }
        return "token-for-" + username;
    }

    public static void main(String[] args) throws Exception {
        String codeVerifier = "random-verifier-" + UUID.randomUUID(); // generated and held ONLY by the legitimate client
        String codeChallenge = sha256Base64Url(codeVerifier);

        String code = authenticateAndIssueCode("alice", "hunter2", codeChallenge);
        System.out.println("Issued code (challenge sent upfront, verifier stays local): " + code);

        // Legitimate exchange: the SAME client presents the matching verifier.
        System.out.println("Legitimate exchange: " + exchangeCodeForToken(code, codeVerifier));

        // Attacker intercepted the code (e.g. via a logged redirect) but does NOT know the verifier.
        String code2 = authenticateAndIssueCode("alice", "hunter2", codeChallenge);
        System.out.println("Attacker exchange attempt with guessed verifier: " + exchangeCodeForToken(code2, "attacker-guessed-verifier"));
    }
}
```

How to run: `java AuthorizationCodeWithPkce.java`

PKCE closes a real gap: authorization codes travel through the browser (in a redirect URL), where they can be intercepted by a malicious app on the same device or logged somewhere unintended. Even with the code alone, `exchangeCodeForToken` also requires `codeVerifier` — a value only the legitimate client instance generated and kept locally, never sent anywhere until this final exchange. The attacker's exchange attempt, using a guessed verifier, produces a completely different SHA-256 hash than the original `codeChallenge`, so it's rejected — the code alone was insufficient to obtain a token.

## 6. Walkthrough

Trace `AuthorizationCodeWithPkce.main` in order. **First**, `codeVerifier` is generated locally as a random string, and `codeChallenge` is computed as its base64url-encoded SHA-256 hash — this challenge is what gets sent to the authorization server upfront; the verifier itself never leaves the client at this point.

**Next**, `authenticateAndIssueCode("alice", "hunter2", codeChallenge)` runs. The password check passes, and a new code is generated and stored in `ISSUED_CODES` alongside `["alice", codeChallenge]` — the challenge is now permanently tied to this specific code.

**Then**, the legitimate exchange runs: `exchangeCodeForToken(code, codeVerifier)`. The code is found and removed (single use). `sha256Base64Url(codeVerifier)` is recomputed fresh — and because this is the *same* verifier that produced the original challenge, the recomputed hash matches `expectedChallenge` exactly. The exchange succeeds, returning `"token-for-alice"`.

**Finally**, a second code (`code2`) is issued the same way, but this time `exchangeCodeForToken(code2, "attacker-guessed-verifier")` is called with a wrong verifier — modeling an attacker who intercepted the *code* (from a leaked redirect) but has no way to know the *verifier*, since it was never transmitted anywhere. `sha256Base64Url("attacker-guessed-verifier")` produces a completely different hash than the stored `codeChallenge`, so the comparison fails and the exchange is denied — even though the attacker possesses a technically valid, unused authorization code.

```
legitimate exchange (verifier matches challenge)   -> token-for-alice
attacker exchange (wrong verifier, code intercepted) -> DENIED: PKCE verifier does not match
```

Sample real HTTP shapes this models — the authorization redirect and the back-channel token exchange:

```
GET /authorize?response_type=code&client_id=dashboard&code_challenge=Xk9f...&code_challenge_method=S256
  --> redirects to: https://client-app/callback?code=abc123

POST /token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=abc123&code_verifier=random-verifier-...
```

## 7. Gotchas & takeaways

> A common mistake is using the `client_credentials` grant for a flow that actually involves a human user, just to "simplify" the code. If a user's specific identity and permissions matter for what happens next (as they usually do), collapsing to client credentials throws away *who* the user is — the resulting token represents the service, not the person, which silently breaks any per-user authorization logic downstream.

- Choose authorization code (with PKCE for public clients) whenever a human user is present and needs to delegate access; choose client credentials for pure machine-to-machine calls with no user involved.
- The authorization code itself is short-lived and single-use by design — treat any attempt to reuse a code as a signal of a possible interception or replay attack.
- PKCE protects the code exchange even for clients that can't hold a confidential secret, and is now recommended for *all* authorization code flows, not just mobile/SPA clients.
- Avoid the deprecated implicit and resource-owner-password-credentials grants in new systems — they expose tokens or passwords in ways the newer flows were specifically designed to avoid.
- These grant types are the mechanics underneath [OpenID Connect](0388-openid-connect-oidc.md), which adds a standardized identity layer (the ID token) on top of the same authorization code and client credentials flows.
