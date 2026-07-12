---
card: spring-authorization-server
gi: 21
slug: jwtencoder-jwk-source
title: "JwtEncoder & JWK source"
---

## 1. What it is

`JwtEncoder` is the interface that actually signs a set of claims into a JWT string — it's what `JwtGenerator` (card 0019) calls under the hood to produce the final token bytes. Spring Authorization Server uses `NimbusJwtEncoder`, backed by a `JWKSource<SecurityContext>` — a functional interface that supplies the signing key(s). The `JWKSource` is where the actual private key material lives (or is fetched from), and it's also what gets exposed publicly, minus private key components, at the server's `/oauth2/jwks` endpoint so resource servers can fetch the matching public key to verify signatures.

## 2. Why & when

Signing is what makes a JWT trustworthy — without it, anyone could fabricate a token claiming any scopes or identity they like. `JwtEncoder` and its `JWKSource` exist as the seam between "what claims to put in a token" (decided by `JwtGenerator` and its customizers) and "how to cryptographically prove this token really came from this server" (decided by the signing key and algorithm). You interact with this layer directly whenever:

- Standing up a new authorization server and providing its first signing key — this is a required bean, not optional.
- Rotating signing keys — a security best practice, and something a real deployment needs a plan for, since old tokens signed with a retiring key must still verify until they naturally expire.
- Debugging "invalid signature" errors on the resource server side — the answer usually traces back to a mismatch between the key the server signed with and the key the resource server is trying to verify against.

## 3. Core concept

Think of the `JWKSource` as a notary's private stamp and public seal registry. The notary (authorization server) keeps the private stamp locked away and uses it to notarize documents (sign JWTs). Separately, anyone in town can look up the notary's public seal pattern at a public registry (the `/oauth2/jwks` endpoint) to verify that a document claiming to be notarized by this notary really was — without ever needing access to the stamp itself. When the notary eventually retires a stamp and cuts a new one, the registry keeps *both* seal patterns listed for a while, so documents notarized before the changeover still verify correctly.

```java
@Bean
public JWKSource<SecurityContext> jwkSource() {
    KeyPair keyPair = generateRsaKey();
    RSAKey rsaKey = new RSAKey.Builder((RSAPublicKey) keyPair.getPublic())
            .privateKey((RSAPrivateKey) keyPair.getPrivate())
            .keyID(UUID.randomUUID().toString())
            .build();
    JWKSet jwkSet = new JWKSet(rsaKey);
    return (jwkSelector, context) -> jwkSelector.select(jwkSet);
}

@Bean
public JwtEncoder jwtEncoder(JWKSource<SecurityContext> jwkSource) {
    return new NimbusJwtEncoder(jwkSource);
}
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JwtEncoder signs with a private key while the public key is exposed via the JWKS endpoint">
  <rect x="30" y="30" width="220" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">JwtEncoder</text>
  <text x="140" y="75" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">signs claims with private key</text>

  <rect x="390" y="30" width="220" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">GET /oauth2/jwks</text>
  <text x="500" y="75" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">exposes public key(s) only</text>

  <rect x="200" y="150" width="240" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="175" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Resource server</text>
  <text x="320" y="195" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">fetches public key, verifies signature</text>

  <line x1="140" y1="100" x2="140" y2="150" stroke="#3fb950" stroke-width="2"/>
  <text x="60" y="130" fill="#3fb950" font-size="10" font-family="sans-serif">signed JWT</text>
  <line x1="500" y1="100" x2="330" y2="150" stroke="#79c0ff" stroke-width="2"/>
  <text x="480" y="130" fill="#79c0ff" font-size="10" font-family="sans-serif">public key</text>
</svg>

The private key never leaves the authorization server; only its public counterpart is ever published.

## 5. Runnable example

The scenario: generating a signing key, encoding a JWT with it, and growing toward supporting key rotation with multiple keys published simultaneously.

### Level 1 — Basic

```java
// JwtEncoderDemo.java
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import org.springframework.security.oauth2.jwt.JwsHeader;
import org.springframework.security.oauth2.jwt.JwtClaimsSet;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtEncoderParameters;
import org.springframework.security.oauth2.jwt.NimbusJwtEncoder;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.time.Instant;
import java.util.UUID;

public class JwtEncoderDemo {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(2048);
        KeyPair keyPair = generator.generateKeyPair();

        RSAKey rsaKey = new RSAKey.Builder((RSAPublicKey) keyPair.getPublic())
                .privateKey((RSAPrivateKey) keyPair.getPrivate())
                .keyID(UUID.randomUUID().toString())
                .build();

        JwtEncoder jwtEncoder = new NimbusJwtEncoder(new ImmutableJWKSet<>(new JWKSet(rsaKey)));

        JwtClaimsSet claims = JwtClaimsSet.builder()
                .issuer("https://auth.example.com")
                .subject("alice")
                .issuedAt(Instant.now())
                .expiresAt(Instant.now().plusSeconds(600))
                .claim("scope", "tasks.read")
                .build();

        var jwt = jwtEncoder.encode(JwtEncoderParameters.from(claims));
        System.out.println("Signed JWT (first 40 chars): " + jwt.getTokenValue().substring(0, 40) + "...");
    }
}
```

**How to run:** requires `nimbus-jose-jwt` and `spring-security-oauth2-jose` on the classpath; run via `java JwtEncoderDemo.java` through a build tool. Expected output (value truncated, will differ per run):

```
Signed JWT (first 40 chars): eyJraWQiOiJmNDU2Nz...
```

### Level 2 — Intermediate

Real applications shouldn't generate a throwaway key on every restart — the key needs to come from somewhere durable (an environment variable, a secrets manager, a keystore file) so tokens signed before a restart remain verifiable, and so multiple server instances behind a load balancer sign with the *same* key.

```java
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.NimbusJwtEncoder;

import java.security.KeyFactory;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

public class JwtEncoderDemo {

    static JwtEncoder buildEncoderFromPem(String base64PrivateKey, String base64PublicKey, String keyId) throws Exception {
        KeyFactory keyFactory = KeyFactory.getInstance("RSA");

        RSAPrivateKey privateKey = (RSAPrivateKey) keyFactory.generatePrivate(
                new PKCS8EncodedKeySpec(Base64.getDecoder().decode(base64PrivateKey)));
        RSAPublicKey publicKey = (RSAPublicKey) keyFactory.generatePublic(
                new X509EncodedKeySpec(Base64.getDecoder().decode(base64PublicKey)));

        RSAKey rsaKey = new RSAKey.Builder(publicKey)
                .privateKey(privateKey)
                .keyID(keyId) // stable, persisted key ID -- not regenerated on every restart
                .build();

        return new NimbusJwtEncoder(new ImmutableJWKSet<>(new JWKSet(rsaKey)));
    }

    public static void main(String[] args) {
        // In production, base64PrivateKey/base64PublicKey come from a secrets manager
        // (e.g. Vault, AWS Secrets Manager) or a mounted keystore -- never hardcoded.
        System.out.println("buildEncoderFromPem(...) loads a durable key with a stable keyID,");
        System.out.println("so every server instance behind a load balancer signs identically.");
    }
}
```

**How to run:** same environment as Level 1, providing real base64-encoded PKCS8/X509 key material. Expected output:

```
buildEncoderFromPem(...) loads a durable key with a stable keyID,
so every server instance behind a load balancer signs identically.
```

What changed: the key now comes from external, durable, shared storage rather than being freshly generated in memory each run — this is what makes horizontally-scaled authorization server deployments and server restarts safe, since previously-issued tokens remain verifiable against the same key.

### Level 3 — Advanced

Production supports key rotation: a `JWKSource` that publishes **both** the current and the previous key simultaneously, selecting the current one for new signing operations while still allowing the resource server's `/oauth2/jwks` fetch to validate tokens signed just before the rotation, until they naturally expire.

```java
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.JWKSource;
import com.nimbusds.jose.proc.SecurityContext;
import com.nimbusds.jose.jwk.JWKSelector;

import java.util.List;

public class RotatingJwkSource implements JWKSource<SecurityContext> {

    private volatile RSAKey currentKey;
    private volatile RSAKey previousKey; // kept only until its last issued token would have expired

    public RotatingJwkSource(RSAKey initialKey) {
        this.currentKey = initialKey;
    }

    /** Called by an ops rotation job/schedule, not on every request. */
    public synchronized void rotate(RSAKey newKey) {
        this.previousKey = this.currentKey;
        this.currentKey = newKey;
    }

    @Override
    public List<com.nimbusds.jose.jwk.JWK> get(JWKSelector jwkSelector, SecurityContext context) {
        JWKSet.Builder builder = new JWKSet.Builder(currentKey);
        JWKSet published = previousKey != null
                ? new JWKSet(List.of(currentKey, previousKey)) // both published so old tokens still verify
                : new JWKSet(currentKey);
        return jwkSelector.select(published);
    }

    public RSAKey signingKey() {
        return currentKey; // JwtEncoder always signs with the CURRENT key only
    }
}
```

**How to run:** wire `RotatingJwkSource` as the `JWKSource<SecurityContext>` bean and call `.rotate(newKey)` from a scheduled admin task; tokens signed before rotation keep verifying (their `kid` header matches `previousKey`, still present in the published set) while all new tokens sign with `currentKey`. Expected behavior when tested: a token signed before `rotate()` is called still passes signature verification afterward, since `previousKey` remains in the published JWK Set.

What changed and why it's production-flavored: key rotation without this two-key overlap window would instantly invalidate every currently-outstanding, unexpired token the moment a new key takes over — a real outage, not a theoretical one. Publishing both keys during the transition, while signing only with the new one, is the standard way to rotate keys with zero downtime.

## 6. Walkthrough

Tracing a token's full signing-and-verification lifecycle across a key rotation, in execution order:

1. Before rotation: `JwtGenerator` calls `jwtEncoder.encode(...)`, which asks the `RotatingJwkSource` for the signing key, gets `currentKey` (`kid: "key-1"`), and produces a JWT with header `{"alg": "RS256", "kid": "key-1"}`.
2. An operator triggers `rotate(newKey)` — `previousKey` becomes `key-1`, `currentKey` becomes `key-2`.
3. A new token request comes in; `JwtEncoder` now signs with `key-2`, producing a JWT with `{"alg": "RS256", "kid": "key-2"}`.
4. A resource server receives the **older** token (still signed with `key-1`, issued in step 1, not yet expired) and calls `GET /oauth2/jwks` to fetch verification keys.
5. Because `RotatingJwkSource.get(...)` currently publishes *both* `key-1` and `key-2`, the resource server's cached JWK Set contains `key-1` — it matches the token's `kid` header, verifies the signature successfully, and accepts the token.
6. A second resource server request arrives bearing the **newer** token (signed with `key-2`); the same published JWK Set also contains `key-2`, so this verifies too.
7. Once enough time passes that every token signed with `key-1` has expired naturally, an operator (or a scheduled job) removes `previousKey` from the source entirely — from that point on, only `key-2` is published, and the rotation is complete with zero failed verifications along the way.

```
before rotation: sign with key-1 --publish [key-1]-->        resource server verifies with key-1
rotate() called: sign with key-2 --publish [key-1, key-2]--> resource server verifies EITHER key-1 or key-2
after old tokens expire: remove key-1 --publish [key-2]-->   resource server verifies only key-2
```

## 7. Gotchas & takeaways

> Rotating a signing key by immediately removing the old key from the published JWK Set is a self-inflicted outage — every unexpired token signed with the old key instantly fails verification everywhere. Always keep the outgoing key published until its longest-lived issued token would have expired anyway.

- `JWKSource<SecurityContext>` is a functional interface — a lambda is enough for a static, single key, but rotation logic (Level 3) needs a real class with mutable state, since the source is consulted on every signing operation and every JWKS fetch.
- The `keyID` (`kid`) in the JWT header is what lets a resource server pick the *right* public key out of a set containing several — losing or randomizing `kid` between restarts (as in Level 1's throwaway key) breaks this matching and is fine only for local demos.
- Never hardcode private key material in source code or commit it to version control — Level 2's pattern of loading from a secrets manager or mounted keystore is the minimum bar for anything beyond a local demo.
- The `/oauth2/jwks` endpoint is public and unauthenticated by design — it must never expose private key material, only the public components, which is exactly what `RSAKey` without `.privateKey(...)` provides when serialized for that endpoint.
- Plan key rotation *before* you need it under pressure (e.g. after a suspected key compromise) — having a tested `rotate()` path in place turns an incident response into a routine operation instead of an improvised, risky one.
