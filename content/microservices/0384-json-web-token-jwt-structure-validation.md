---
card: microservices
gi: 384
slug: json-web-token-jwt-structure-validation
title: "JSON Web Token (JWT) structure & validation"
---

## 1. What it is

A **JSON Web Token (JWT)** is the most common concrete implementation of a self-contained [token](0383-token-based-security.md): a compact, URL-safe string made of three parts — a **header**, a **payload**, and a **signature** — separated by dots, like `xxxxx.yyyyy.zzzzz`. The header and payload are just base64url-encoded JSON, readable by anyone who has the token (a JWT is *not* encrypted by default, only signed), while the signature cryptographically proves the header and payload haven't been altered since a trusted party issued them.

## 2. Why & when

JWTs became the default choice for token-based security because they solve a specific problem cleanly: how does a service verify a caller's identity and claims *without* calling back to a central authority on every request? You reach for a JWT specifically when:

- **You want stateless verification.** Any service holding the issuer's public key (or shared secret) can verify a JWT's signature locally — no database lookup, no network call to an auth server.
- **You want structured, inspectable claims.** A JWT payload can carry a username, roles, scopes, an expiry, and custom claims, all as plain JSON any service can read directly (though, again, not confidentially — see the gotcha below).
- **You're working within [OAuth2](0386-oauth2-roles-resource-owner-client-auth-server-resource-serv.md)/[OIDC](0388-openid-connect-oidc.md) ecosystems**, where JWTs are the standard format for access tokens and ID tokens, with broad library and framework support (including Spring Security's OAuth2 resource server support).

You'd reach instead for an [opaque token](0385-opaque-tokens-token-introspection.md) when you need instant revocation or don't want claims visible to anyone holding the token — JWTs trade that away for the convenience of stateless, local verification.

## 3. Core concept

Think of a JWT like a sealed wax-stamped letter with the contents printed in clear, readable text on the outside of the envelope. Anyone who picks up the envelope can read what it says — that's the header and payload, base64url-encoded but *not* encrypted, just encoded for safe transport. But nobody can alter what it says without breaking the wax seal in a way that's instantly obvious — that's the signature. The seal doesn't hide the message; it proves the message hasn't been tampered with since whoever holds the matching stamp sealed it.

Concretely, the three parts are:

1. **Header** — a small JSON object naming the signing algorithm (e.g. `"alg": "HS256"` or `"alg": "RS256"`) and token type (`"typ": "JWT"`). This part is base64url-encoded, not encrypted.
2. **Payload (claims)** — a JSON object of claims. Standard claims include `sub` (subject/identity), `iss` (issuer), `exp` (expiry, as a Unix timestamp), `iat` (issued-at), and `aud` (audience — who the token is intended for). Applications add custom claims like `scope` or `roles`. Also base64url-encoded, also not encrypted.
3. **Signature** — computed by the issuer over the header and payload using a secret key (symmetric, e.g. HMAC-SHA256) or a private key (asymmetric, e.g. RSA or ECDSA). A verifier recomputes the expected signature using the corresponding public key (or shared secret) and compares.

**Validation** — the step every receiving service must perform on every token it accepts — means checking, in order: (a) the signature is valid for the given header+payload, using a key the verifier actually trusts; (b) `exp` hasn't passed; (c) `iss` matches an expected, trusted issuer; (d) `aud` includes this service (or the audience it's operating as), so a token minted for a different service can't be replayed here; and only then (e) reading and acting on the remaining claims (scopes, roles). Skipping any of steps (a)–(d) and jumping straight to (e) is the classic JWT validation bug.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A JWT has three dot-separated parts: a base64url-encoded header, a base64url-encoded payload of claims, and a signature computed over both; the payload is readable by anyone but the signature proves it was not tampered with" font-family="sans-serif">
  <rect x="20" y="30" width="180" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="110" y="50" fill="#79c0ff" font-size="11" text-anchor="middle">Header</text>
  <text x="110" y="68" fill="#8b949e" font-size="8" text-anchor="middle">{"alg":"RS256",</text>
  <text x="110" y="80" fill="#8b949e" font-size="8" text-anchor="middle">"typ":"JWT"}</text>
  <text x="110" y="95" fill="#8b949e" font-size="8" text-anchor="middle">base64url -- readable</text>

  <rect x="230" y="30" width="200" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="48" fill="#6db33f" font-size="11" text-anchor="middle">Payload (claims)</text>
  <text x="330" y="66" fill="#8b949e" font-size="8" text-anchor="middle">sub, iss, aud, exp,</text>
  <text x="330" y="78" fill="#8b949e" font-size="8" text-anchor="middle">scope, roles ...</text>
  <text x="330" y="95" fill="#8b949e" font-size="8" text-anchor="middle">base64url -- readable,</text>
  <text x="330" y="107" fill="#8b949e" font-size="8" text-anchor="middle">NOT encrypted</text>

  <rect x="460" y="30" width="160" height="70" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="540" y="50" fill="#f0883e" font-size="11" text-anchor="middle">Signature</text>
  <text x="540" y="68" fill="#8b949e" font-size="8" text-anchor="middle">sign(header+payload,</text>
  <text x="540" y="80" fill="#8b949e" font-size="8" text-anchor="middle">private/secret key)</text>
  <text x="540" y="95" fill="#8b949e" font-size="8" text-anchor="middle">proves integrity</text>

  <text x="110" y="140" fill="#8b949e" font-size="14" text-anchor="middle">.</text>
  <text x="330" y="140" fill="#8b949e" font-size="10" text-anchor="middle">xxxxx.yyyyy.zzzzz</text>

  <rect x="150" y="170" width="340" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="320" y="192" fill="#f85149" font-size="10" text-anchor="middle">Verifier: recompute expected signature</text>
  <text x="320" y="208" fill="#f85149" font-size="10" text-anchor="middle">from header+payload using trusted key,</text>
  <text x="320" y="224" fill="#f85149" font-size="10" text-anchor="middle">then check exp, iss, aud before trusting claims</text>
</svg>

Header and payload are freely readable once decoded; the signature is what a verifier checks to trust that the claims are genuine and unaltered.

## 5. Runnable example

Scenario: an internal identity service issuing and verifying JWT-like tokens for an "orders" API. We build a minimal JWT encode/decode by hand (no external library, to make every step explicit) at Level 1, add real signature verification at Level 2, then add full validation (expiry, issuer, audience) at Level 3 to model what a real resource server checks.

### Level 1 — Basic

```java
// File: JwtStructureBasics.java -- builds a JWT-shaped string by hand: base64url-encoded
// header and payload joined by dots, with a stand-in signature value, to show the raw structure.
import java.util.*;
import java.nio.charset.StandardCharsets;

public class JwtStructureBasics {
    static String base64UrlEncode(String json) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(json.getBytes(StandardCharsets.UTF_8));
    }

    public static void main(String[] args) {
        String header = "{\"alg\":\"HS256\",\"typ\":\"JWT\"}";
        String payload = "{\"sub\":\"alice\",\"iss\":\"auth-server\",\"exp\":9999999999,\"scope\":\"orders:read\"}";

        String encodedHeader = base64UrlEncode(header);
        String encodedPayload = base64UrlEncode(payload);
        String fakeSignature = "STANDIN_SIGNATURE_VALUE"; // Level 2 replaces this with a real one

        String jwt = encodedHeader + "." + encodedPayload + "." + fakeSignature;
        System.out.println("Header JSON:  " + header);
        System.out.println("Payload JSON: " + payload);
        System.out.println("Resulting JWT-shaped string:\n" + jwt);
        System.out.println("Anyone can base64url-DECODE the header and payload -- they are readable, not secret.");
    }
}
```

How to run: `java JwtStructureBasics.java`

This builds the three-part, dot-separated structure by hand, using only base64url encoding (no encryption) for the header and payload — exactly matching what a real JWT looks like structurally. It deliberately uses a stand-in value for the signature to isolate and show the *encoding* half of a JWT before introducing the *signing* half, which is what actually makes the token trustworthy.

### Level 2 — Intermediate

```java
// File: JwtWithRealSignature.java -- adds an ACTUAL HMAC-SHA256 signature over the
// header and payload, and verifies it -- so tampering is now genuinely detectable.
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.*;
import java.nio.charset.StandardCharsets;

public class JwtWithRealSignature {
    static final String SECRET = "super-secret-signing-key-shared-only-by-trusted-issuers";

    static String base64UrlEncode(String s) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }

    static String hmacSign(String data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(SECRET.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        byte[] rawSig = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(rawSig);
    }

    static String issueJwt(String subject, String scope) throws Exception {
        String header = base64UrlEncode("{\"alg\":\"HS256\",\"typ\":\"JWT\"}");
        String payload = base64UrlEncode("{\"sub\":\"" + subject + "\",\"scope\":\"" + scope + "\"}");
        String signingInput = header + "." + payload;
        String signature = hmacSign(signingInput);
        return signingInput + "." + signature;
    }

    static boolean verifyJwt(String jwt) throws Exception {
        String[] parts = jwt.split("\\.");
        String signingInput = parts[0] + "." + parts[1];
        String expectedSignature = hmacSign(signingInput);
        return expectedSignature.equals(parts[2]); // must match EXACTLY
    }

    public static void main(String[] args) throws Exception {
        String jwt = issueJwt("alice", "orders:read");
        System.out.println("Issued JWT: " + jwt);
        System.out.println("Signature valid? " + verifyJwt(jwt));

        // Tamper: change the payload without re-signing (attacker doesn't have SECRET).
        String[] parts = jwt.split("\\.");
        String tamperedPayload = base64UrlEncode("{\"sub\":\"alice\",\"scope\":\"admin:all\"}");
        String tamperedJwt = parts[0] + "." + tamperedPayload + "." + parts[2]; // old signature, new payload
        System.out.println("Tampered JWT signature valid? " + verifyJwt(tamperedJwt));
    }
}
```

How to run: `java JwtWithRealSignature.java`

`hmacSign` computes a real HMAC-SHA256 signature over the exact bytes of `header + "." + payload`. `verifyJwt` recomputes that same signature independently and does an exact comparison. The legitimate token verifies. The tampered token — payload changed to claim `"admin:all"` scope, but signed with the *old* signature because the attacker never had `SECRET` — fails verification, because HMAC-SHA256 output changes completely when even one byte of input changes. This is the real mechanism behind the stand-in signature shown conceptually in Level 1.

### Level 3 — Advanced

```java
// File: JwtFullValidation.java -- adds the FULL validation sequence a real resource
// server performs: signature, THEN expiry, THEN issuer, THEN audience -- each an
// independent gate, in the correct order, before any claim is trusted.
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.util.*;
import java.nio.charset.StandardCharsets;

public class JwtFullValidation {
    static final String SECRET = "super-secret-signing-key-shared-only-by-trusted-issuers";
    static final String TRUSTED_ISSUER = "https://auth.example.com";
    static final String THIS_SERVICE_AUDIENCE = "orders-api";

    static String base64UrlEncode(String s) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(s.getBytes(StandardCharsets.UTF_8));
    }
    static String hmacSign(String data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(SECRET.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
    }

    static String issueJwt(String subject, String issuer, String audience, long expiresInSeconds) throws Exception {
        long exp = (System.currentTimeMillis() / 1000) + expiresInSeconds;
        String header = base64UrlEncode("{\"alg\":\"HS256\",\"typ\":\"JWT\"}");
        String payload = base64UrlEncode(
                "{\"sub\":\"" + subject + "\",\"iss\":\"" + issuer + "\",\"aud\":\"" + audience + "\",\"exp\":" + exp + "}");
        String signingInput = header + "." + payload;
        return signingInput + "." + hmacSign(signingInput);
    }

    // Full validation pipeline: EACH gate independently capable of rejecting the token.
    static String validate(String jwt) throws Exception {
        String[] parts = jwt.split("\\.");
        String signingInput = parts[0] + "." + parts[1];

        if (!hmacSign(signingInput).equals(parts[2])) {
            return "REJECTED: signature invalid";
        }
        String payloadJson = new String(Base64.getUrlDecoder().decode(parts[1]), StandardCharsets.UTF_8);
        long exp = Long.parseLong(payloadJson.replaceAll(".*\"exp\":(\\d+).*", "$1"));
        String iss = payloadJson.replaceAll(".*\"iss\":\"([^\"]+)\".*", "$1");
        String aud = payloadJson.replaceAll(".*\"aud\":\"([^\"]+)\".*", "$1");

        if (System.currentTimeMillis() / 1000 > exp) {
            return "REJECTED: token expired";
        }
        if (!TRUSTED_ISSUER.equals(iss)) {
            return "REJECTED: untrusted issuer '" + iss + "'";
        }
        if (!THIS_SERVICE_AUDIENCE.equals(aud)) {
            return "REJECTED: token audience '" + aud + "' is not this service ('" + THIS_SERVICE_AUDIENCE + "')";
        }
        return "ACCEPTED: valid token for subject in payload, all gates passed";
    }

    public static void main(String[] args) throws Exception {
        String goodToken = issueJwt("alice", TRUSTED_ISSUER, THIS_SERVICE_AUDIENCE, 60);
        String wrongAudienceToken = issueJwt("alice", TRUSTED_ISSUER, "payments-api", 60); // minted for a DIFFERENT service
        String expiredToken = issueJwt("alice", TRUSTED_ISSUER, THIS_SERVICE_AUDIENCE, -10); // already expired

        System.out.println(validate(goodToken));
        System.out.println(validate(wrongAudienceToken));
        System.out.println(validate(expiredToken));
    }
}
```

How to run: `java JwtFullValidation.java`

`validate` runs four gates in strict order: signature, expiry, issuer, audience. The "hard case" this level handles is the **audience-confusion attack**: `wrongAudienceToken` has a perfectly valid signature and hasn't expired — it was legitimately issued by the trusted issuer — but it was minted for `"payments-api"`, not `"orders-api"`. If this service skipped the audience check (a very common real-world oversight), a token a user obtained for one API could be replayed against a completely different API. Checking `aud` closes that gap.

## 6. Walkthrough

Trace `JwtFullValidation.main` in order. **First**, three tokens are issued: `goodToken` (correct issuer, correct audience, 60-second expiry), `wrongAudienceToken` (correct issuer, but audience `"payments-api"`), and `expiredToken` (correct issuer and audience, but a *negative* 10-second expiry, meaning `exp` is already 10 seconds in the past at issuance).

**Next**, `validate(goodToken)` runs. The recomputed HMAC signature matches — gate 1 passes. The payload is decoded and `exp` is parsed out; `System.currentTimeMillis() / 1000` is still well before `exp` — gate 2 passes. `iss` equals `"https://auth.example.com"`, matching `TRUSTED_ISSUER` — gate 3 passes. `aud` equals `"orders-api"`, matching `THIS_SERVICE_AUDIENCE` — gate 4 passes. All four gates clear, returning `"ACCEPTED"`.

**Then**, `validate(wrongAudienceToken)` runs. Signature and expiry checks pass identically (the token is genuinely valid and unexpired) — but when `aud` is extracted, it reads `"payments-api"`, which does not equal `"orders-api"`. Gate 4 rejects it: `"REJECTED: token audience 'payments-api' is not this service"`. Crucially, this token would have sailed through a validator that only checked signature and expiry.

**Finally**, `validate(expiredToken)` runs. Its signature is valid (gate 1 passes, nothing was tampered with). But its `exp` claim was set to `(issue time) - 10` seconds — already in the past the instant it was issued — so `System.currentTimeMillis() / 1000 > exp` is `true`, and gate 2 rejects it before issuer or audience are even inspected.

```
goodToken            -> ACCEPTED: all gates passed
wrongAudienceToken   -> REJECTED: token audience 'payments-api' is not this service (orders-api)
expiredToken         -> REJECTED: token expired
```

Sample decoded payload for `goodToken` (what `validate` sees after base64url-decoding `parts[1]`):

```json
{"sub":"alice","iss":"https://auth.example.com","aud":"orders-api","exp":1752400123}
```

## 7. Gotchas & takeaways

> A JWT's payload is **encoded, not encrypted**. `Base64.getUrlDecoder().decode(...)` on the payload segment of *any* JWT you can get your hands on — including ones you're not supposed to be able to read — reveals every claim in plain JSON. Never put secrets (passwords, credit card numbers, private personal data beyond a user ID) directly in a JWT payload; anyone who intercepts the token, or a client that merely stores it, can read every claim without needing the signing key at all.

- Structure: `base64url(header).base64url(payload).signature`, joined by dots — header and payload are always human-readable once decoded.
- Validation must check signature, expiry (`exp`), issuer (`iss`), and audience (`aud`) — in that order, all four, every time; skipping audience checking allows tokens minted for one service to be replayed against another.
- JWTs are naturally revocation-resistant: because verification is local and stateless, a compromised JWT stays valid until it expires, unless you add extra infrastructure (a blocklist, short expiries with refresh tokens) — this is the core trade-off against [opaque tokens](0385-opaque-tokens-token-introspection.md).
- Prefer asymmetric signing (RS256/ES256) over symmetric (HS256) when multiple services need to *verify* tokens but shouldn't be able to *issue* them — with HMAC, anyone who can verify also holds the secret needed to forge.
- JWTs are the standard access-token and ID-token format in [OAuth2](0386-oauth2-roles-resource-owner-client-auth-server-resource-serv.md) and [OpenID Connect](0388-openid-connect-oidc.md), and Spring Security's OAuth2 resource server support performs exactly this validation sequence out of the box when configured with a trusted issuer.
