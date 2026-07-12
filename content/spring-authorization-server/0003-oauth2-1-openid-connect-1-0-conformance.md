---
card: spring-authorization-server
gi: 3
slug: oauth2-1-openid-connect-1-0-conformance
title: "OAuth2.1 & OpenID Connect 1.0 conformance"
---

## 1. What it is

OAuth 2.1 is a consolidation effort — not a wholly new protocol, but a tightened, security-hardened draft that folds years of accumulated best-practice guidance (much of it from RFC 8252 and the OAuth Security Best Current Practice document) directly into the specification's normative requirements, rather than leaving them as easily-missed recommendations scattered across separate documents. Spring Authorization Server builds specifically to this stricter baseline: several behaviors card 0090's Authorization Code grant discussion treated as *good practice* — PKCE, exact redirect URI matching, dropping the Implicit and Resource Owner Password Credentials grants entirely — are, in Spring Authorization Server, simply the only options available, not opt-in hardening a developer might forget to enable.

```java
// PKCE is effectively REQUIRED for public clients in OAuth 2.1 -- Spring Authorization Server
// enforces this automatically when a client is registered without a client secret (a "public" client)
RegisteredClient publicClient = RegisteredClient.withId(UUID.randomUUID().toString())
        .clientId("mobile-app")
        .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)  // no secret -- a PUBLIC client
        .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
        .redirectUri("myapp://callback")  // EXACT match required, no wildcard/prefix matching
        .clientSettings(ClientSettings.builder().requireProofKey(true).build())  // PKCE mandatory
        .build();
```

## 2. Why & when

Card 0090 described `state` verification, single-use codes, and short code lifetimes as security properties every well-implemented Authorization Code grant client should observe — but the original OAuth 2.0 specification never *required* several of the strongest protections (PKCE was optional, added later by a separate RFC; redirect URI matching rules were historically looser, permitting subtle bypass techniques). OAuth 2.1 exists because "best practice, if you remember to implement it" repeatedly proved insufficient in practice — real vulnerabilities kept surfacing from omitted PKCE, loose redirect URI matching, and continued support for grant types (Implicit, Password) that leak tokens through browser-visible channels or require clients to handle raw user passwords. Building an authorization server *to* this consolidated, stricter baseline means these protections are structural, not optional configuration a developer could accidentally skip.

Reach for understanding OAuth 2.1/OIDC 1.0 conformance specifically when:

- Registering a public client (a mobile app, a single-page application with no confidential backend) — PKCE is required, and Spring Authorization Server enforces it rather than merely recommending it.
- Wondering why the Implicit grant or Resource Owner Password Credentials grant aren't supported at all — they're dropped entirely in OAuth 2.1, considered obsolete security anti-patterns rather than legacy options still worth preserving.
- Configuring redirect URIs — exact string matching is required (no partial/prefix matching), closing a class of open-redirect-adjacent vulnerabilities looser matching historically permitted.
- Auditing whether an integration built against this authorization server needs updating for stricter conformance — a client relying on loose matching or an unsupported legacy grant type will need adjustment, not the server relaxing its own conformance.

## 3. Core concept

```
OAuth 2.0 (looser, original spec)          OAuth 2.1 (consolidated, stricter baseline)
------------------------------------       ------------------------------------------
PKCE: optional, separate RFC 7636           PKCE: REQUIRED for public clients
Implicit grant: supported                   Implicit grant: REMOVED entirely
Resource Owner Password Credentials:        Resource Owner Password Credentials:
    supported                                   REMOVED entirely
redirect_uri matching: could be looser      redirect_uri matching: EXACT STRING match required
                                                 (no wildcards, no partial/prefix matching)
bearer tokens in query strings: permitted   bearer tokens in query strings: DISCOURAGED/removed
                                                 in several contexts

Spring Authorization Server implements against OAuth 2.1's STRICTER baseline --
these are not configuration TOGGLES an application can loosen back to the old
behavior; they are how the framework is built.

OpenID Connect 1.0 conformance means: standard claims (sub, iss, aud, exp, iat),
standard endpoints (/userinfo, /.well-known/openid-configuration), and standard
ID token structure -- all interoperable with ANY OIDC-compliant client library,
not just Spring's own.
```

The practical upshot: applications integrating with a Spring Authorization Server instance benefit from these protections automatically, without needing to remember to configure each one individually.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting OAuth 2.0s optional security protections which required a developer to remember to enable them against OAuth 2.1s consolidated stricter baseline where PKCE exact redirect matching and dropped legacy grants are structural not configurable">
  <rect x="20" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="165" y="42" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth 2.0 (original)</text>
  <text x="165" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PKCE: optional (separate RFC)</text>
  <text x="165" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Implicit grant: supported</text>
  <text x="165" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Password grant: supported</text>
  <text x="165" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">redirect_uri: looser matching</text>
  <text x="165" y="150" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">security = "remember to configure it"</text>

  <rect x="330" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth 2.1 (Spring Auth Server)</text>
  <text x="475" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PKCE: REQUIRED for public clients</text>
  <text x="475" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Implicit grant: REMOVED</text>
  <text x="475" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Password grant: REMOVED</text>
  <text x="475" y="125" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">redirect_uri: EXACT match required</text>
  <text x="475" y="150" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">security = "structural, not optional"</text>

  <defs></defs>
</svg>

The same protections card 0090 recommended as best practice are, here, simply how the protocol works — no toggle to disable them.

## 5. Runnable example

The scenario: model the exact-match redirect URI rule and mandatory PKCE for public clients, growing from a bare exact-match check into rejecting a legacy grant type entirely, then into a full PKCE-verified authorization code exchange demonstrating the mandatory protection in action.

### Level 1 — Basic

Exact redirect URI matching, rejecting anything looser.

```java
import java.util.*;

public class ConformanceLevel1 {
    record RegisteredClient(String clientId, String registeredRedirectUri) {}

    static class RedirectUriException extends RuntimeException { RedirectUriException(String m) { super(m); } }

    // mirrors OAuth 2.1's EXACT STRING MATCH requirement -- no prefix/wildcard matching
    static void validateRedirectUri(RegisteredClient client, String requestedRedirectUri) {
        if (!client.registeredRedirectUri().equals(requestedRedirectUri)) {
            throw new RedirectUriException("redirect_uri does not exactly match the registered value");
        }
    }

    public static void main(String[] args) {
        RegisteredClient client = new RegisteredClient("my-app", "https://app.example.com/callback");

        validateRedirectUri(client, "https://app.example.com/callback"); // exact match
        System.out.println("exact match: accepted");

        try {
            // a SUBTLY different URI -- would have been accepted under looser, older matching rules
            validateRedirectUri(client, "https://app.example.com/callback/../admin");
        } catch (RedirectUriException e) {
            System.out.println("subtly different uri: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ConformanceLevel1.java`, run `java ConformanceLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
exact match: accepted
subtly different uri: redirect_uri does not exactly match the registered value
```

`validateRedirectUri` mirrors OAuth 2.1's exact-string-match requirement — a redirect URI that isn't character-for-character identical to what was registered is rejected outright, closing off the class of path-traversal or subdomain-confusion tricks looser matching rules historically permitted.

### Level 2 — Intermediate

Reject a legacy grant type entirely, mirroring the Implicit and Password grants' removal.

```java
import java.util.*;

public class ConformanceLevel2 {
    enum GrantType { AUTHORIZATION_CODE, CLIENT_CREDENTIALS, REFRESH_TOKEN, IMPLICIT, PASSWORD }

    static class UnsupportedGrantTypeException extends RuntimeException {
        UnsupportedGrantTypeException(String message) { super(message); }
    }

    static final Set<GrantType> SUPPORTED_GRANTS = Set.of(
            GrantType.AUTHORIZATION_CODE, GrantType.CLIENT_CREDENTIALS, GrantType.REFRESH_TOKEN);

    static void processTokenRequest(GrantType grantType) {
        if (!SUPPORTED_GRANTS.contains(grantType)) {
            throw new UnsupportedGrantTypeException(
                    grantType + " is not supported -- OAuth 2.1 removed this grant type entirely");
        }
        System.out.println(grantType + ": processed successfully");
    }

    public static void main(String[] args) {
        processTokenRequest(GrantType.AUTHORIZATION_CODE);
        processTokenRequest(GrantType.CLIENT_CREDENTIALS);

        try {
            processTokenRequest(GrantType.IMPLICIT);
        } catch (UnsupportedGrantTypeException e) {
            System.out.println("rejected: " + e.getMessage());
        }

        try {
            processTokenRequest(GrantType.PASSWORD);
        } catch (UnsupportedGrantTypeException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ConformanceLevel2.java`, run `java ConformanceLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
AUTHORIZATION_CODE: processed successfully
CLIENT_CREDENTIALS: processed successfully
rejected: IMPLICIT is not supported -- OAuth 2.1 removed this grant type entirely
rejected: PASSWORD is not supported -- OAuth 2.1 removed this grant type entirely
```

What changed: `processTokenRequest` now explicitly allowlists only the three grant types OAuth 2.1 retains — both `IMPLICIT` and `PASSWORD` are rejected with a message identifying exactly which grant type was refused and why, mirroring how Spring Authorization Server simply has no code path implementing either legacy grant at all, rather than accepting and then discouraging them.

### Level 3 — Advanced

A full PKCE-protected authorization code exchange for a public client — the mandatory protection in action, demonstrating why it closes the specific vulnerability it targets: a stolen authorization code being unusable without the original code verifier.

```java
import java.security.*;
import java.util.*;
import java.util.Base64;

public class ConformanceLevel3 {
    record RegisteredClient(String clientId, boolean isPublicClient) {}
    record PendingAuthorization(String code, String clientId, String codeChallenge) {}

    static class PkceValidationException extends RuntimeException { PkceValidationException(String m) { super(m); } }

    static class AuthorizationServer {
        private final Map<String, PendingAuthorization> pending = new HashMap<>();

        // mirrors GET /oauth2/authorize?...&code_challenge=...&code_challenge_method=S256
        String authorize(RegisteredClient client, String codeChallenge) {
            if (client.isPublicClient() && codeChallenge == null) {
                throw new PkceValidationException("PKCE code_challenge is REQUIRED for public clients");
            }
            String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
            pending.put(code, new PendingAuthorization(code, client.clientId(), codeChallenge));
            return code;
        }

        // mirrors POST /oauth2/token with code_verifier
        String exchangeToken(String code, String codeVerifier) throws NoSuchAlgorithmException {
            PendingAuthorization auth = pending.remove(code);
            if (auth == null) throw new IllegalStateException("invalid_grant");

            if (auth.codeChallenge() != null) {
                // mirrors verifying: BASE64URL(SHA256(code_verifier)) == code_challenge
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                byte[] hash = digest.digest(codeVerifier.getBytes());
                String computedChallenge = Base64.getUrlEncoder().withoutPadding().encodeToString(hash);
                if (!computedChallenge.equals(auth.codeChallenge())) {
                    throw new PkceValidationException("code_verifier does not match the original code_challenge");
                }
            }
            return "access-token-for-" + auth.clientId();
        }
    }

    public static void main(String[] args) throws NoSuchAlgorithmException {
        AuthorizationServer server = new AuthorizationServer();
        RegisteredClient mobileApp = new RegisteredClient("mobile-app", true);

        String codeVerifier = "a-random-high-entropy-string-generated-by-the-client";
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        String codeChallenge = Base64.getUrlEncoder().withoutPadding().encodeToString(digest.digest(codeVerifier.getBytes()));

        String code = server.authorize(mobileApp, codeChallenge);
        System.out.println("authorization code issued (PKCE challenge attached): " + code);

        // LEGITIMATE exchange: the ORIGINAL client, presenting the matching verifier
        String token = server.exchangeToken(code, codeVerifier);
        System.out.println("legitimate exchange succeeds: " + token);

        // simulate a STOLEN code (e.g. intercepted from a malicious app on the same device) --
        // the attacker has the CODE but NOT the original verifier, since it was never transmitted anywhere
        String secondCode = server.authorize(mobileApp, codeChallenge);
        try {
            server.exchangeToken(secondCode, "attacker-guessed-verifier");
        } catch (PkceValidationException e) {
            System.out.println("stolen code, wrong verifier: REJECTED -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ConformanceLevel3.java`, run `java ConformanceLevel3.java` (JDK 17+ runs single files directly).

Expected output (code values vary):
```
authorization code issued (PKCE challenge attached): code-a1b2c3d4
legitimate exchange succeeds: access-token-for-mobile-app
stolen code, wrong verifier: REJECTED -- code_verifier does not match the original code_challenge
```

What changed: `exchangeToken` now verifies the PKCE `code_verifier` against the `code_challenge` established at authorization time — a stolen authorization code alone is insufficient to obtain a token, since the attacker would need the original, never-transmitted-in-the-clear `code_verifier` as well. This is precisely the vulnerability class mandatory PKCE closes for public clients: a code intercepted (e.g., via a malicious app registering the same custom URL scheme on a mobile device) is useless without the verifier only the legitimate client ever held.

## 6. Walkthrough

Trace the stolen-code rejection from Level 3, then the legitimate exchange for contrast.

**Step 1 — the legitimate client starts the flow, generating a code verifier locally.** `codeVerifier` is a high-entropy random string, generated and held *only* by the mobile app — never sent anywhere until the final token exchange.

**Step 2 — the authorization request includes only the *derived* challenge, not the verifier itself:**
```
GET /oauth2/authorize?client_id=mobile-app&code_challenge=<SHA256 hash, base64url>&code_challenge_method=S256 HTTP/1.1
```
This corresponds to `server.authorize(mobileApp, codeChallenge)` — the server stores this challenge alongside the issued code, but has no way to derive the original verifier from it (SHA-256 is one-way).

**Step 3 — the authorization code is issued and, hypothetically, intercepted by a malicious application on the same device** (a known attack vector against custom URL scheme redirects on mobile platforms) — corresponding to `secondCode` being available to an attacker in this simulation.

**Step 4 — the attacker attempts to exchange the stolen code**, but has no way to know the original `codeVerifier` (it was never transmitted, only its hash):
```
POST /oauth2/token HTTP/1.1

grant_type=authorization_code&code=code-xyz&code_verifier=attacker-guessed-verifier
```
Corresponding to `server.exchangeToken(secondCode, "attacker-guessed-verifier")`.

**Step 5 — the verification fails.** `exchangeToken` recomputes `SHA256("attacker-guessed-verifier")` and compares it against the stored `code_challenge` — they don't match (the attacker's guess is essentially certain to be wrong against a high-entropy original), so `PkceValidationException` is thrown, and no token is issued.

**Step 6 — contrast: the legitimate client's exchange**, using the *actual* `codeVerifier` it generated in step 1, recomputes to the *same* hash the server stored as `code_challenge` — the check passes, and a real token is issued.

```
legitimate client: generates codeVerifier -> derives codeChallenge -> authorize() stores challenge
        |
        v
        code issued, sent to legitimate client via redirect
        |
        v
        exchangeToken(code, codeVerifier) -> hash matches -> TOKEN ISSUED

attacker: intercepts the CODE (not the verifier, which was never transmitted)
        |
        v
        exchangeToken(stolenCode, guessedVerifier) -> hash does NOT match -> REJECTED
```

## 7. Gotchas & takeaways

> **Gotcha:** OAuth 2.1's stricter requirements are not configuration toggles Spring Authorization Server exposes a way to relax — they reflect the framework's design against the newer specification's baseline. An integration expecting the old, looser OAuth 2.0 behavior (partial redirect URI matching, the Implicit grant) will need to be updated to conform, rather than the server being configured to accommodate legacy expectations.

- OAuth 2.1 consolidates years of separately-documented best practices into the specification's normative requirements, rather than leaving them as optional guidance a developer might omit.
- PKCE is mandatory for public clients, exact redirect URI matching is required, and the Implicit and Resource Owner Password Credentials grants are removed entirely — Spring Authorization Server implements against this stricter baseline structurally.
- PKCE specifically closes the vulnerability of a stolen authorization code being usable on its own — the code alone is insufficient without the original, never-transmitted code verifier.
- OpenID Connect 1.0 conformance ensures interoperability with any standards-compliant OIDC client library, not just Spring's own tooling — standard claims, standard endpoints, standard token structure.
- Building on this stricter baseline means client applications integrating with a Spring Authorization Server instance inherit these protections automatically, rather than needing to configure or remember each one individually.
