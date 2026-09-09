---
card: system-design
gi: 177
slug: jwt-structure-validation
title: JWT structure & validation
---

## 1. What it is

A **JSON Web Token (JWT)** is a compact, self-contained token format made of three base64url-encoded parts joined by dots: `header.payload.signature`. The **header** describes the signing algorithm; the **payload** holds the actual claims (user ID, roles, expiry time, and so on) as a JSON object; the **signature** is computed over the header and payload using a secret (or private key) known only to the issuer, letting anyone with the corresponding key verify the token was not tampered with.

## 2. Why & when

Because a JWT's payload is only base64url-*encoded*, not encrypted, anyone can decode and read its contents without any key at all — the signature is what actually matters, since it is the only thing that proves the payload has not been altered since the issuer created it. This is exactly what makes JWTs useful as [tokens](0175-sessions-vs-tokens.md): the payload's claims can be trusted precisely because verifying the signature is fast and needs no shared server-side lookup. Use a JWT whenever you need a compact, verifiable, self-contained way to carry identity or authorization claims between services — but always validate the signature and the standard claims (especially expiry) on every single use, never just decode and trust it.

## 3. Core concept

- **Header:** typically `{"alg": "HS256", "typ": "JWT"}`, naming the signing algorithm (HMAC-SHA256 here) so a verifier knows how to check the signature.
- **Payload (claims):** standard claims like `exp` (expiry time), `iat` (issued-at time), `sub` (subject, usually the user ID), plus any custom claims the issuer wants to include (roles, permissions).
- **Signature:** `HMAC-SHA256(base64url(header) + "." + base64url(payload), secretKey)` for a symmetric-key JWT; verifying it means recomputing this same value and comparing it to the signature in the token.
- **Encoded, not encrypted:** base64url encoding is reversible by anyone — it is not a security mechanism, only a way to make binary/JSON data URL-safe; never put secret data directly in a JWT payload expecting it to be hidden.
- **Expiry (`exp`) must always be checked:** a syntactically valid, correctly-signed token that has simply expired must still be rejected — signature validity and expiry validity are two separate checks, and both are required.

## 4. Diagram

```
   JWT: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTE3IiwiZXhwIjoxNzAwMDAwMDAwfQ.SFLKJH34...

        header (decoded)         payload (decoded)              signature
   {"alg":"HS256"}      {"sub":"user-17","exp":1700000000}    (binary, verified against secret)

   verification:
     recompute HMAC-SHA256(header + "." + payload, secretKey)
                    |
              matches signature in token?  --- no  --> REJECT (tampered or wrong key)
                    |
                   yes
                    |
              is exp in the future?  --- no  --> REJECT (expired)
                    |
                   yes
                    |
              TRUST the claims (sub, roles, etc.)
```
*Caption: the payload is readable by anyone without a key, but the signature (checked against the secret) is what proves it has not been altered, and expiry must be checked separately.*

## 5. Runnable example

**Level 1 — Basic.** Build a JWT-shaped token: encode header and payload, then sign them.

**Level 2 — Validate the signature.** Reject a token whose payload was tampered with after signing.

**Level 3 — Check the expiry claim separately from the signature.** A correctly-signed but expired token must still be rejected.

```java
// JwtDemo.java
import java.util.*;
import java.util.Base64;

public class JwtDemo {

    static final String SECRET_KEY = "server-secret-key";

    // Level 1: build the three parts and join them - this models the real base64url + HMAC structure.
    static String issueJwt(String subject, long expiryEpochSeconds) {
        String header = "{\"alg\":\"HS256\"}";
        String payload = "{\"sub\":\"" + subject + "\",\"exp\":" + expiryEpochSeconds + "}";
        String encodedHeader = Base64.getUrlEncoder().withoutPadding().encodeToString(header.getBytes());
        String encodedPayload = Base64.getUrlEncoder().withoutPadding().encodeToString(payload.getBytes());
        String signature = sign(encodedHeader + "." + encodedPayload, SECRET_KEY);
        return encodedHeader + "." + encodedPayload + "." + signature;
    }

    // A simplified stand-in for real HMAC-SHA256 signing.
    static String sign(String data, String secretKey) {
        return Integer.toHexString((data + secretKey).hashCode());
    }

    // Level 2: verify the signature by recomputing it and comparing.
    static boolean verifySignature(String jwt) {
        String[] parts = jwt.split("\\.");
        String expectedSignature = sign(parts[0] + "." + parts[1], SECRET_KEY);
        return expectedSignature.equals(parts[2]);
    }

    // Level 3: check the expiry claim - a SEPARATE check from the signature.
    static boolean isExpired(String jwt, long nowEpochSeconds) {
        String[] parts = jwt.split("\\.");
        String payload = new String(Base64.getUrlDecoder().decode(parts[1]));
        long exp = Long.parseLong(payload.replaceAll(".*\"exp\":(\\d+).*", "$1"));
        return nowEpochSeconds >= exp;
    }

    static void validateAndUse(String jwt, long nowEpochSeconds) {
        if (!verifySignature(jwt)) {
            System.out.println("REJECTED: invalid signature (tampered or wrong key)");
            return;
        }
        if (isExpired(jwt, nowEpochSeconds)) {
            System.out.println("REJECTED: token expired");
            return;
        }
        System.out.println("ACCEPTED: token is valid and not expired");
    }

    public static void main(String[] args) {
        long now = 1_700_000_000L;
        String jwt = issueJwt("user-17", now + 3600); // expires 1 hour from now
        System.out.println("issued JWT: " + jwt);

        System.out.println("validating immediately:");
        validateAndUse(jwt, now);

        // Level 2: tamper with the payload after signing (change "user-17" to "user-99").
        String[] parts = jwt.split("\\.");
        String tamperedPayload = Base64.getUrlEncoder().withoutPadding().encodeToString(
            "{\"sub\":\"user-99\",\"exp\":" + (now + 3600) + "}".getBytes());
        String tamperedJwt = parts[0] + "." + tamperedPayload + "." + parts[2]; // signature NOT recomputed
        System.out.println("validating a TAMPERED token:");
        validateAndUse(tamperedJwt, now);

        // Level 3: a correctly-signed token, checked long after its expiry.
        System.out.println("validating the ORIGINAL token, checked 2 hours later:");
        validateAndUse(jwt, now + 7200);
    }
}
```

**How to run:** save as `JwtDemo.java`, then run `java JwtDemo.java`.

## 6. Walkthrough

1. `issueJwt("user-17", now + 3600)` base64url-encodes the header and payload separately, then computes `signature = sign(encodedHeader + "." + encodedPayload, SECRET_KEY)` — the signature covers exactly the header and payload as they were at signing time, joined by a dot.
2. `validateAndUse(jwt, now)` calls `verifySignature`, which re-derives the expected signature from the token's own header and payload parts and compares it to the signature embedded in the token; since nothing has changed, they match, and the check passes — then `isExpired` finds `now < exp`, so the token is accepted.
3. The tampering step re-encodes a *different* payload (`"user-99"` instead of `"user-17"`) but reuses the *original* signature from `parts[2]`, exactly modeling what an attacker who only has the encoded token (not the secret key) would be able to do — they can freely re-encode a new payload, but cannot compute a matching signature without the secret.
4. `validateAndUse(tamperedJwt, now)` calls `verifySignature`, which recomputes the expected signature from the *tampered* payload — this does not match the old signature still present in the token, so the method returns `false`, and the token is correctly rejected as "REJECTED: invalid signature".
5. The final call reuses the original, correctly-signed `jwt`, but checks it at `now + 7200` (2 hours later, while it was only valid for 1 hour); `verifySignature` still passes (nothing was tampered with), but `isExpired` now finds `nowEpochSeconds (now+7200) >= exp (now+3600)`, so the token is rejected as "REJECTED: token expired" — demonstrating that a valid signature alone is not sufficient; the expiry claim must always be checked too.

## 7. Gotchas & takeaways

> Gotcha: some poorly-written JWT libraries historically had a vulnerability where an attacker could set the header's `alg` field to `"none"` and strip the signature entirely, and a careless verifier that trusted the client-supplied algorithm would accept the unsigned token outright — always configure JWT verification to use a fixed, expected algorithm decided by the server, never one read from the token itself.

- A JWT's payload is readable by anyone (it is encoded, not encrypted); only the signature protects its integrity, and only a server holding the correct key can verify it.
- Signature validity and expiry validity are two separate, both-required checks — a correctly-signed but expired token must still be rejected.
- Never derive the verification algorithm from the token's own header; always fix it on the server side to prevent algorithm-substitution attacks.
- Related concepts: [Sessions vs tokens](0175-sessions-vs-tokens.md) (the broader tradeoff a JWT sits within), [OAuth2 & OpenID Connect](0176-oauth2-openid-connect.md) (where JWTs are commonly used as access and ID tokens), [Spring Security resource server (JWT)](0183-spring-security-resource-server-jwt.md) (a real Spring implementation of this exact validation logic).
