---
card: microservices
gi: 388
slug: openid-connect-oidc
title: "OpenID Connect (OIDC)"
---

## 1. What it is

**OpenID Connect (OIDC)** is a thin identity layer built directly on top of [OAuth2](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md). OAuth2 by itself only answers "what is this client allowed to access?" — it was never designed to answer "who is this user, exactly?" OIDC adds that missing piece: a standardized **ID token** (always a [JWT](0384-json-web-token-jwt-structure-validation.md)) that tells the client precisely who authenticated, plus a standard `/userinfo` endpoint for fetching profile details. If OAuth2 is the delegation protocol, OIDC is "OAuth2 plus a reliable way to know who just logged in."

## 2. Why & when

Before OIDC, plenty of applications tried to bolt identity onto plain OAuth2 by treating "I successfully got an access token" as a proxy for "the user is logged in" — but that's an unreliable, non-standard hack, because access tokens were never designed to carry verified identity information, and their format and content varies by authorization server. You need OIDC specifically when:

- **You need "log in with X"** (Google, GitHub, your company's SSO) — this is precisely what OIDC standardizes, and it's the mechanism behind essentially every "Sign in with..." button you've ever clicked.
- **You need to know exactly who authenticated**, not just that *some* token was issued. An access token might be opaque or scoped for a completely different purpose; an ID token's entire job is to assert identity.
- **You want a standard, verifiable identity claim set** — `sub` (a stable user identifier), `email`, `name`, `iss`, `aud`, `exp` — rather than inventing your own ad hoc "who is this" convention per authorization server.
- **You're building single sign-on (SSO) across multiple microservices or applications** that all need to trust the same central identity source.

You still need plain OAuth2's access tokens whenever a client calls an API on the user's behalf (reading their orders, writing their data) — OIDC doesn't replace that; it sits alongside it, answering a different question.

## 3. Core concept

Think of the difference between a valet ticket and a driver's license. The valet ticket ([OAuth2 access token](0383-token-based-security.md)) proves you're allowed to retrieve *a* car from the garage — it doesn't say who you are, just what you're permitted to do. A driver's license (the OIDC **ID token**) is a verified statement of identity: your name, a stable ID number, an issuing authority, an expiry date — checkable and meaningful on its own, regardless of whether you're currently trying to get a car.

Concretely, OIDC layers three things onto OAuth2:

1. **The `openid` scope** — a client requests it alongside any other scopes (like `orders:read`) in the same authorization request. Its presence tells the authorization server "this is an OIDC request; also issue an ID token, not just an access token."
2. **The ID token** — always a JWT, always containing standardized claims: `sub` (subject — a stable, unique identifier for this user at this issuer), `iss` (issuer), `aud` (the client this token was issued to), `exp`, `iat`, and typically `email`, `name`, and other profile claims depending on requested scopes (`profile`, `email`). Unlike an opaque access token, the ID token is *meant* to be decoded and read by the client directly — that's its whole purpose.
3. **The `/userinfo` endpoint** — an authenticated endpoint the client can call with the access token to fetch additional profile claims not embedded directly in the ID token, useful when the token itself is kept minimal.
4. **Discovery** — most OIDC providers expose a well-known `/.well-known/openid-configuration` document listing their endpoints and signing keys, so clients (and Spring Security's OIDC support) can auto-configure against any compliant provider without hardcoding URLs.

Crucially, **the ID token is for the client**, proving to the *client itself* who just logged in — it is not meant to be sent onward to resource servers as an access credential. The access token remains the credential resource servers check; conflating the two is a common and consequential mistake.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OpenID Connect adds an ID token to the standard OAuth2 authorization code flow: after login, the client receives both an access token for calling APIs and an ID token asserting who authenticated" font-family="sans-serif">
  <rect x="20" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="119" fill="#e6edf3" font-size="10" text-anchor="middle">Client app</text>

  <rect x="200" y="30" width="160" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="280" y="52" fill="#6db33f" font-size="10" text-anchor="middle">Authorization server</text>
  <text x="280" y="68" fill="#8b949e" font-size="9" text-anchor="middle">(OIDC provider)</text>
  <text x="280" y="88" fill="#8b949e" font-size="8" text-anchor="middle">authenticates user,</text>
  <text x="280" y="100" fill="#8b949e" font-size="8" text-anchor="middle">scope includes "openid"</text>
  <text x="280" y="120" fill="#8b949e" font-size="8" text-anchor="middle">issues 2 tokens back</text>

  <rect x="440" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="525" y="42" fill="#79c0ff" font-size="10" text-anchor="middle">Access token</text>
  <text x="525" y="58" fill="#8b949e" font-size="8" text-anchor="middle">for calling APIs</text>

  <rect x="440" y="90" width="170" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="525" y="112" fill="#f0883e" font-size="10" text-anchor="middle">ID token (JWT)</text>
  <text x="525" y="128" fill="#8b949e" font-size="8" text-anchor="middle">sub, email, name -- for the CLIENT to read</text>

  <line x1="110" y1="115" x2="200" y2="90" stroke="#8b949e" marker-end="url(#a7)"/>
  <line x1="360" y1="60" x2="440" y2="45" stroke="#79c0ff" marker-end="url(#a7)"/>
  <line x1="360" y1="100" x2="440" y2="115" stroke="#f0883e" marker-end="url(#a7)"/>
  <defs>
    <marker id="a7" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Requesting the `openid` scope makes the authorization server return an ID token alongside the access token — one for API calls, one asserting exactly who logged in.

## 5. Runnable example

Scenario: a client app implementing "Sign in with our identity provider." We start with an access-token-only flow that has no reliable way to know who logged in, add a proper OIDC ID token, then validate that ID token fully (signature, issuer, audience, and — the OIDC-specific addition — a nonce, to prevent replay of a stolen ID token into a different login session).

### Level 1 — Basic

```java
// File: AccessTokenOnlyNoIdentity.java -- plain OAuth2 with NO identity layer:
// the client gets an access token, but has no standardized, reliable way to know
// WHO just logged in -- it would have to guess or use non-standard conventions.
import java.util.*;

public class AccessTokenOnlyNoIdentity {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");

    static String issueAccessTokenOnly(String username, String password) {
        if (!password.equals(USER_PASSWORDS.get(username))) return null;
        return "access-token-opaque-string"; // says NOTHING about who this belongs to
    }

    public static void main(String[] args) {
        String token = issueAccessTokenOnly("alice", "hunter2");
        System.out.println("Access token: " + token);
        System.out.println("The CLIENT has no standardized way to know this belongs to 'alice' -- just a token good for API calls.");
    }
}
```

How to run: `java AccessTokenOnlyNoIdentity.java`

`issueAccessTokenOnly` returns a token that's useful for calling APIs but carries no verifiable, standardized identity information the *client itself* can read. Some systems hack around this by making non-standard assumptions about access-token content, but that's fragile and provider-specific — exactly the gap OIDC's ID token closes.

### Level 2 — Intermediate

```java
// File: OidcIdToken.java -- adds a proper ID token: a JWT-shaped structure with
// standardized OIDC claims (sub, iss, aud, email) that the CLIENT decodes directly
// to learn exactly who authenticated -- separate from the access token used for APIs.
import java.util.*;
import java.nio.charset.StandardCharsets;

public class OidcIdToken {
    static final Map<String, String> USER_PASSWORDS = Map.of("alice", "hunter2");
    static final Map<String, String> USER_EMAILS = Map.of("alice", "alice@example.com");

    static String base64UrlEncode(String s) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }

    static class OidcResponse {
        String accessToken, idToken;
        OidcResponse(String accessToken, String idToken) { this.accessToken = accessToken; this.idToken = idToken; }
    }

    // Requesting scope "openid" triggers issuance of an ID TOKEN alongside the access token.
    static OidcResponse authenticateWithOidc(String username, String password, String scope) {
        if (!password.equals(USER_PASSWORDS.get(username))) return null;
        String accessToken = "access-token-for-" + username;
        String idToken = null;
        if (scope.contains("openid")) {
            String header = base64UrlEncode("{\"alg\":\"RS256\",\"typ\":\"JWT\"}");
            String payload = base64UrlEncode(
                    "{\"sub\":\"" + username + "\",\"iss\":\"https://idp.example.com\",\"aud\":\"reporting-dashboard\","
                    + "\"email\":\"" + USER_EMAILS.get(username) + "\"}");
            idToken = header + "." + payload + ".SIGNATURE"; // signature verification covered in Level 3
        }
        return new OidcResponse(accessToken, idToken);
    }

    public static void main(String[] args) {
        OidcResponse response = authenticateWithOidc("alice", "hunter2", "openid profile email orders:read");
        System.out.println("Access token (for calling APIs): " + response.accessToken);
        System.out.println("ID token (for the CLIENT to read identity from): " + response.idToken);

        String payloadJson = new String(Base64.getUrlDecoder().decode(response.idToken.split("\\.")[1]), StandardCharsets.UTF_8);
        System.out.println("Client decodes ID token payload directly: " + payloadJson);
    }
}
```

How to run: `java OidcIdToken.java`

Requesting `"openid"` in the scope string is what triggers ID-token issuance — a plain `"orders:read"`-only request would get back only an access token, exactly like Level 1. The ID token's payload carries `sub` (a stable identifier for `"alice"`), `iss`, `aud`, and `email` — all claims the client decodes and reads *directly*, unlike the opaque `accessToken`, which the client just holds and forwards to APIs without needing to understand its contents.

### Level 3 — Advanced

```java
// File: OidcFullValidationWithNonce.java -- full ID token validation (signature,
// issuer, audience, expiry -- same discipline as JWT validation) PLUS the
// OIDC-specific nonce check, which prevents a stolen/replayed ID token from a
// PREVIOUS login being reused to impersonate a fresh login session.
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.*;
import java.nio.charset.StandardCharsets;

public class OidcFullValidationWithNonce {
    static final String SECRET = "idp-signing-secret";
    static final String TRUSTED_ISSUER = "https://idp.example.com";
    static final String THIS_CLIENT_ID = "reporting-dashboard";

    static String base64UrlEncode(String s) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }
    static String hmacSign(String data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(SECRET.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
    }

    // The client generates a random nonce PER login attempt and sends it in the auth request;
    // the IdP echoes it back inside the ID token, unaltered.
    static String issueIdToken(String username, String nonce, long expiresInSeconds) throws Exception {
        long exp = (System.currentTimeMillis() / 1000) + expiresInSeconds;
        String header = base64UrlEncode("{\"alg\":\"HS256\",\"typ\":\"JWT\"}");
        String payload = base64UrlEncode(
                "{\"sub\":\"" + username + "\",\"iss\":\"" + TRUSTED_ISSUER + "\",\"aud\":\"" + THIS_CLIENT_ID + "\","
                + "\"exp\":" + exp + ",\"nonce\":\"" + nonce + "\"}");
        String signingInput = header + "." + payload;
        return signingInput + "." + hmacSign(signingInput);
    }

    static String validateIdToken(String idToken, String expectedNonce) throws Exception {
        String[] parts = idToken.split("\\.");
        String signingInput = parts[0] + "." + parts[1];
        if (!hmacSign(signingInput).equals(parts[2])) return "REJECTED: signature invalid";

        String payloadJson = new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
        long exp = Long.parseLong(payloadJson.replaceAll(".*\"exp\":(\\d+).*", "$1"));
        String iss = payloadJson.replaceAll(".*\"iss\":\"([^\"]+)\".*", "$1");
        String aud = payloadJson.replaceAll(".*\"aud\":\"([^\"]+)\".*", "$1");
        String nonce = payloadJson.replaceAll(".*\"nonce\":\"([^\"]+)\".*", "$1");

        if (System.currentTimeMillis() / 1000 > exp) return "REJECTED: ID token expired";
        if (!TRUSTED_ISSUER.equals(iss)) return "REJECTED: untrusted issuer";
        if (!THIS_CLIENT_ID.equals(aud)) return "REJECTED: audience mismatch";
        if (!expectedNonce.equals(nonce)) return "REJECTED: nonce mismatch -- possible replay of an OLD ID token into a NEW session";
        return "ACCEPTED: identity confirmed for this specific login session";
    }

    public static void main(String[] args) throws Exception {
        String sessionANonce = "nonce-session-A-" + UUID.randomUUID();
        String idTokenA = issueIdToken("alice", sessionANonce, 60);
        System.out.println(validateIdToken(idTokenA, sessionANonce)); // legitimate: same session's nonce

        // A NEW login session starts, generating its OWN fresh nonce.
        String sessionBNonce = "nonce-session-B-" + UUID.randomUUID();
        // An attacker replays the OLD idTokenA (e.g. captured from a previous session/log) into session B.
        System.out.println(validateIdToken(idTokenA, sessionBNonce));
    }
}
```

How to run: `java OidcFullValidationWithNonce.java`

`validateIdToken` runs the same signature/expiry/issuer/audience gates as plain JWT validation, then adds an OIDC-specific check: does the `nonce` claim inside the token match the nonce *this specific login attempt* generated and expects back? The hard case Level 3 handles: an attacker who somehow captured a previously-issued, still-unexpired, correctly-signed ID token (`idTokenA`) tries to replay it into a brand-new login session (`sessionB`). Every other check passes — the token is genuinely valid and correctly signed — but the nonce embedded in `idTokenA` matches `sessionANonce`, not the fresh `sessionBNonce` the new session is expecting, so the replay is caught.

## 6. Walkthrough

Trace `OidcFullValidationWithNonce.main` in order. **First**, `sessionANonce` is generated fresh, and `issueIdToken("alice", sessionANonce, 60)` produces `idTokenA`, an ID token whose `nonce` claim is exactly `sessionANonce`.

**Next**, `validateIdToken(idTokenA, sessionANonce)` runs. Signature verification passes (nothing altered since issuance). Expiry hasn't passed (well within 60 seconds). Issuer matches `TRUSTED_ISSUER`. Audience matches `THIS_CLIENT_ID`. Finally, `expectedNonce.equals(nonce)` compares `sessionANonce` to the token's embedded nonce — since this is the *same* session that requested the token, they match exactly, and the method returns `"ACCEPTED"`.

**Then**, a *new* login session begins and generates its own `sessionBNonce` — a completely different random value. An attacker who intercepted `idTokenA` earlier (say, from a browser history entry or an insufficiently protected log) attempts to present it as proof of identity for this new session. `validateIdToken(idTokenA, sessionBNonce)` runs: signature, expiry, issuer, and audience checks all pass identically to before, because `idTokenA` itself hasn't changed and is still genuinely valid. But the final check compares `sessionBNonce` (what session B expects) against `idTokenA`'s embedded nonce, which is still `sessionANonce` — a mismatch. The replay is rejected at the very last gate, specifically the one OIDC added beyond ordinary JWT validation.

```
idTokenA validated with matching sessionANonce -> ACCEPTED: identity confirmed
idTokenA replayed with a DIFFERENT sessionBNonce -> REJECTED: nonce mismatch (replay caught)
```

Sample decoded ID token payload (what a client would actually see after decoding):

```json
{"sub":"alice","iss":"https://idp.example.com","aud":"reporting-dashboard","exp":1752400999,"nonce":"nonce-session-A-7f3c..."}
```

## 7. Gotchas & takeaways

> A frequent and dangerous mistake is sending the **ID token** to a resource server as if it were an access token. ID tokens are meant for the client to consume directly — they assert who logged in, addressed (via the `aud` claim) to that one specific client. Resource servers should validate *access* tokens, not ID tokens; accepting an ID token as an API credential means the audience check (which was scoped to the client app, not the API) provides no real protection, and it blurs a distinction OIDC deliberately built in.

- OIDC adds an identity layer on top of OAuth2 by introducing the `openid` scope and a standardized ID token — it doesn't replace OAuth2's access tokens, it complements them.
- The ID token is a JWT meant for the client to decode directly; the access token remains what resource servers validate — don't conflate the two, even though both are often JWTs.
- Validate ID tokens with the same rigor as any JWT (signature, expiry, issuer, audience — see [JWT structure & validation](0384-json-web-token-jwt-structure-validation.md)), plus the OIDC-specific nonce check to prevent replaying an old ID token into a new login session.
- The `/userinfo` endpoint and discovery document (`/.well-known/openid-configuration`) let clients (including Spring Security's OIDC support) fetch additional profile data and auto-configure against any standards-compliant identity provider.
- OIDC is the standard mechanism behind virtually every "Sign in with Google/Microsoft/GitHub" button, and the same protocol underlies enterprise SSO across a company's internal microservices.
