---
card: spring-authorization-server
gi: 9
slug: sample-bootiful-setup
title: "Sample/Bootiful setup"
---

## 1. What it is

A "Bootiful" setup — Spring's own informal term for a minimal, idiomatic Spring Boot application — brings every concept from this section's earlier cards together into one working, runnable authorization server: a Spring Boot main class, the `SecurityFilterChain` bean from cards 0006–0007, an in-memory `RegisteredClientRepository` with one registered test client, a generated RSA signing key exposed as a `JWKSource<SecurityContext>` bean, and a minimal `UserDetailsService` for the resource owner login — the complete, minimum-viable set of beans an authorization server genuinely needs to issue its first real token.

```java
@Bean
public RegisteredClientRepository registeredClientRepository() {
    RegisteredClient registeredClient = RegisteredClient.withId(UUID.randomUUID().toString())
            .clientId("demo-client")
            .clientSecret("{noop}secret")  // {noop} = plaintext, for LOCAL DEMO ONLY, never production
            .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
            .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
            .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
            .redirectUri("http://127.0.0.1:8080/login/oauth2/code/demo-client")
            .scope(OidcScopes.OPENID)
            .scope("read")
            .clientSettings(ClientSettings.builder().requireAuthorizationConsent(true).build())
            .build();
    return new InMemoryRegisteredClientRepository(registeredClient);
}

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
```

## 2. Why & when

Every earlier card in this section explained a piece in isolation — this card is where those pieces need to actually cohere into something that starts, serves requests, and issues a real, verifiable token, which is the only way to genuinely confirm understanding of the preceding material rather than just reading about it. A "Bootiful" reference setup is deliberately minimal and explicitly marked as demo-only (the `{noop}` plaintext password prefix, an in-memory client repository, a freshly-generated-on-every-restart signing key) precisely so it's clear which pieces need hardening before any real deployment, without obscuring the essential shape of a working configuration under production concerns that would otherwise dominate a first example.

Reach for building (or studying) a sample setup like this when:

- Learning Spring Authorization Server hands-on for the first time — running a genuinely working instance locally, then completing a real Authorization Code grant flow against it end to end, cements the concepts far more effectively than reading configuration in isolation.
- Prototyping quickly, before investing in production-grade concerns (a real `RegisteredClientRepository` backed by a database, a properly-managed signing key with rotation, hashed client secrets) — the in-memory, demo-oriented setup gets something running in minutes.
- Debugging a real deployment by first confirming the *minimal* setup works — if a from-scratch, minimal reference configuration functions correctly locally, but a more complex, production configuration doesn't, the difference between the two narrows down where the actual problem lies.

Every piece marked "demo only" here (`{noop}` passwords, in-memory storage, ephemeral keys) is explicitly *not* appropriate for production — recognizing which pieces are demo shortcuts versus genuinely reusable configuration is as important as getting the sample running at all.

## 3. Core concept

```
Minimum viable Bootiful authorization server, the FULL bean list:

    @Bean SecurityFilterChain authorizationServerSecurityFilterChain(...)   -- card 0007
    @Bean SecurityFilterChain defaultSecurityFilterChain(...)               -- card 0002's ordinary chain
                                                                                (formLogin(), for resource owner login)
    @Bean UserDetailsService userDetailsService(...)                        -- resource owner accounts
    @Bean RegisteredClientRepository registeredClientRepository(...)         -- THIS card's client registration
    @Bean JWKSource<SecurityContext> jwkSource(...)                         -- THIS card's signing key
    @Bean JwtDecoder jwtDecoder(JWKSource<SecurityContext> jwkSource)        -- derived FROM the jwkSource bean
    @Bean AuthorizationServerSettings authorizationServerSettings()          -- the issuer URL, endpoint paths

DEMO-ONLY markers to recognize and NEVER carry into production:
    "{noop}secret"                    -- PLAINTEXT client secret -- production needs a real PasswordEncoder
    InMemoryRegisteredClientRepository -- lost on restart -- production needs a persistent (JDBC) repository
    a freshly-generated RSA key EVERY startup -- production needs a STABLE, managed key (or rotation, card 0101's story)

The FULL flow this setup makes possible, end to end:
    1. start the application
    2. a browser (or a REAL registered oauth2Login()-configured client app) hits /oauth2/authorize
    3. redirected to THIS server's OWN /login (card 0002's ordinary chain) -- log in as a seeded user
    4. consent screen (requireAuthorizationConsent(true)) -- approve the requested scopes
    5. redirected back with a code -- exchanged at /oauth2/token -- a REAL, verifiable JWT is issued
```

Every piece maps directly back to a concept an earlier card in this section already introduced — this card is the assembly, not new material.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing the complete minimum bean list for a bootiful authorization server two security filter chains a user details service a registered client repository and a jwk source with demo only markers flagged on the parts that need hardening before production">
  <rect x="20" y="20" width="600" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="320" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Two SecurityFilterChain beans (cards 0002, 0007)</text>
  <text x="320" y="65" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">OAuth2 endpoints (HIGHEST precedence) + ordinary formLogin() (lower precedence)</text>

  <rect x="40" y="95" width="170" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="125" y="115" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">UserDetailsService</text>
  <text x="125" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">resource owner accounts</text>

  <rect x="245" y="95" width="170" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="330" y="115" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">RegisteredClientRepository</text>
  <text x="330" y="132" fill="#f0883e" font-size="7.5" text-anchor="middle" font-family="sans-serif">DEMO: in-memory, lost on restart</text>

  <rect x="450" y="95" width="170" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="535" y="115" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">JWKSource (signing key)</text>
  <text x="535" y="132" fill="#f0883e" font-size="7.5" text-anchor="middle" font-family="sans-serif">DEMO: regenerated every restart</text>

  <text x="320" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">every DEMO-marked piece needs hardening (real password encoding, persistent storage, managed keys) before production</text>

  <defs></defs>
</svg>

The complete minimal bean list, with demo-only shortcuts explicitly flagged for what production would need instead.

## 5. Runnable example

The scenario: assemble the full sample setup's logic in one place — a registered client, a signing key, the two-chain login-then-authorize sequence — growing from a single registered client into the full end-to-end Authorization Code grant flow, then into flagging exactly which pieces of this working demo would need to change before any real deployment.

### Level 1 — Basic

Register the demo client and generate a signing key, mirroring the two core sample-setup beans.

```java
import java.util.*;

public class BootifulSetupLevel1 {
    record RegisteredClient(String clientId, String clientSecret, Set<String> scopes, String redirectUri) {}
    record SigningKey(String keyId, String material) {}

    static RegisteredClient buildDemoClient() {
        // mirrors the sample RegisteredClient bean -- {noop} prefix means PLAINTEXT, demo-only
        return new RegisteredClient("demo-client", "{noop}secret",
                Set.of("openid", "read"), "http://127.0.0.1:8080/login/oauth2/code/demo-client");
    }

    static SigningKey generateDemoSigningKey() {
        // mirrors generating a FRESH RSA key pair every application startup
        return new SigningKey(UUID.randomUUID().toString(), "generated-rsa-key-material-" + System.nanoTime());
    }

    public static void main(String[] args) {
        RegisteredClient client = buildDemoClient();
        SigningKey key = generateDemoSigningKey();

        System.out.println("registered client: " + client.clientId() + ", scopes=" + client.scopes());
        System.out.println("signing key generated, keyId=" + key.keyId());
    }
}
```

**How to run:** save as `BootifulSetupLevel1.java`, run `java BootifulSetupLevel1.java` (JDK 17+ runs single files directly).

Expected output (key id/material vary):
```
registered client: demo-client, scopes=[openid, read]
signing key generated, keyId=a1b2c3d4-...
```

`buildDemoClient` and `generateDemoSigningKey` mirror exactly the two core beans this card's sample setup provides — a registered client with a demo (plaintext) secret, and a freshly-generated signing key, both explicitly marked as appropriate for local demonstration only.

### Level 2 — Intermediate

The full two-chain login-then-authorize sequence, mirroring card 0002's pattern applied concretely with this sample's specific registered client.

```java
import java.util.*;

public class BootifulSetupLevel2 {
    record RegisteredClient(String clientId, String clientSecret, Set<String> scopes, String redirectUri) {}
    static class Session {
        String authenticatedUsername;
        boolean isAuthenticated() { return authenticatedUsername != null; }
    }

    static RegisteredClient buildDemoClient() {
        return new RegisteredClient("demo-client", "secret", Set.of("openid", "read"),
                "http://127.0.0.1:8080/login/oauth2/code/demo-client");
    }

    // mirrors the ORDINARY second SecurityFilterChain's formLogin() -- card 0002
    static void login(Session session, String username, String password, Map<String, String> seededUsers) {
        if (!password.equals(seededUsers.get(username))) throw new IllegalStateException("Bad credentials");
        session.authenticatedUsername = username;
    }

    // mirrors the OAuth2-SPECIFIC chain's authorization endpoint -- card 0007
    static String authorize(Session session, RegisteredClient client) {
        if (!session.isAuthenticated()) throw new IllegalStateException("redirect to /login first");
        return client.redirectUri() + "?code=demo-code-" + session.authenticatedUsername;
    }

    public static void main(String[] args) {
        RegisteredClient client = buildDemoClient();
        Map<String, String> seededUsers = Map.of("alice", "password123"); // a seeded UserDetailsService user

        Session session = new Session();

        try {
            authorize(session, client);
        } catch (IllegalStateException e) {
            System.out.println("before login: " + e.getMessage());
        }

        login(session, "alice", "password123", seededUsers);
        System.out.println("logged in as: " + session.authenticatedUsername);

        String redirect = authorize(session, client);
        System.out.println("authorization redirect: " + redirect);
    }
}
```

**How to run:** save as `BootifulSetupLevel2.java`, run `java BootifulSetupLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
before login: redirect to /login first
logged in as: alice
authorization redirect: http://127.0.0.1:8080/login/oauth2/code/demo-client?code=demo-code-alice
```

What changed: this now models the complete sequence a browser genuinely experiences against this sample setup — an unauthenticated hit on the authorization endpoint requires logging in first (via the ordinary chain's `formLogin()`), and only after that succeeds does the OAuth2-specific chain's authorization endpoint produce a redirect carrying an authorization code, exactly card 0002's two-chain relationship demonstrated against this specific sample's registered client and seeded user.

### Level 3 — Advanced

Complete the flow with a real token exchange and signing, then explicitly enumerate which pieces of this working demo are flagged as unsuitable for production, alongside what each would need to become production-ready.

```java
import java.util.*;

public class BootifulSetupLevel3 {
    record RegisteredClient(String clientId, String clientSecret, Set<String> scopes) {}
    record IssuedToken(String value, String subject, String signedByKeyId, Set<String> scopes) {}
    record ProductionConcern(String demoPiece, String productionRequirement) {}

    static class AuthorizationServer {
        private final Map<String, RegisteredClient> clients = new HashMap<>();
        private final Map<String, String> pendingCodes = new HashMap<>(); // code -> subject
        private final String signingKeyId;

        AuthorizationServer(String signingKeyId) { this.signingKeyId = signingKeyId; }

        void registerClient(RegisteredClient client) { clients.put(client.clientId(), client); }

        String authorize(String clientId, String subject) {
            String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
            pendingCodes.put(code, subject);
            return code;
        }

        IssuedToken exchangeToken(String code, String clientId, String clientSecret) {
            RegisteredClient client = clients.get(clientId);
            if (client == null || !client.clientSecret().equals(clientSecret)) throw new IllegalStateException("invalid_client");
            String subject = pendingCodes.remove(code);
            if (subject == null) throw new IllegalStateException("invalid_grant");
            return new IssuedToken("jwt-" + UUID.randomUUID().toString().substring(0, 8), subject, signingKeyId, client.scopes());
        }
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer("demo-key-1");
        server.registerClient(new RegisteredClient("demo-client", "secret", Set.of("openid", "read")));

        String code = server.authorize("demo-client", "alice");
        IssuedToken token = server.exchangeToken(code, "demo-client", "secret");
        System.out.println("issued token for " + token.subject() + ", scopes=" + token.scopes()
                + ", signed by key=" + token.signedByKeyId());

        System.out.println();
        System.out.println("=== production readiness checklist for THIS demo setup ===");
        List<ProductionConcern> concerns = List.of(
                new ProductionConcern("{noop} plaintext client secret", "a real PasswordEncoder (e.g. BCrypt) hashing client secrets"),
                new ProductionConcern("InMemoryRegisteredClientRepository", "a JDBC-backed (or otherwise persistent) RegisteredClientRepository"),
                new ProductionConcern("RSA key generated fresh every startup", "a stable, securely-managed signing key with a real rotation strategy"));

        for (ProductionConcern concern : concerns) {
            System.out.println("DEMO: " + concern.demoPiece() + " -> PRODUCTION NEEDS: " + concern.productionRequirement());
        }
    }
}
```

**How to run:** save as `BootifulSetupLevel3.java`, run `java BootifulSetupLevel3.java` (JDK 17+ runs single files directly).

Expected output (specific token/code values vary):
```
issued token for alice, scopes=[openid, read], signed by key=demo-key-1

=== production readiness checklist for THIS demo setup ===
DEMO: {noop} plaintext client secret -> PRODUCTION NEEDS: a real PasswordEncoder (e.g. BCrypt) hashing client secrets
DEMO: InMemoryRegisteredClientRepository -> PRODUCTION NEEDS: a JDBC-backed (or otherwise persistent) RegisteredClientRepository
DEMO: RSA key generated fresh every startup -> PRODUCTION NEEDS: a stable, securely-managed signing key with a real rotation strategy
```

The checklist loop walks all three `ProductionConcern` entries in order, printing each demo shortcut alongside exactly what production would need instead — a concrete, actionable list to work through before this sample setup could ever be deployed for real.

## 6. Walkthrough

Trace alice's complete journey through this sample setup, from a cold application start to a signed, issued token.

**Step 1 — the Spring Boot application starts.** Every bean from this card's core concept section is constructed: two `SecurityFilterChain`s, a `UserDetailsService` (seeded with alice), a `RegisteredClientRepository` (holding `demo-client`), and a `JWKSource` (a freshly-generated RSA key pair) — corresponding to `AuthorizationServer("demo-key-1")` being constructed with `demo-client` registered in Level 3's code.

**Step 2 — a browser hits the authorization endpoint, unauthenticated:**
```
GET /oauth2/authorize?client_id=demo-client&response_type=code&scope=openid+read&... HTTP/1.1
```
Card 0007's chain requires authentication; since none exists yet, the browser is redirected to `/login` — corresponding to Level 2's `authorize` throwing before `login` has been called.

**Step 3 — alice logs in via the ordinary chain's `formLogin()`:**
```
POST /login HTTP/1.1

username=alice&password=password123
```
Validated against the seeded `UserDetailsService` — corresponding to `login(session, "alice", "password123", seededUsers)`.

**Step 4 — redirected back to the authorization endpoint, now authenticated, a consent screen appears** (since `requireAuthorizationConsent(true)` was set on the registered client) — alice approves the requested `openid`/`read` scopes.

**Step 5 — the authorization code is issued and the browser is redirected back to `demo-client`'s registered redirect URI:**
```
HTTP/1.1 302 Found
Location: http://127.0.0.1:8080/login/oauth2/code/demo-client?code=code-a1b2c3d4
```
Corresponding to `server.authorize("demo-client", "alice")` in Level 3.

**Step 6 — the client exchanges the code for a token, server-to-server:**
```
POST /oauth2/token HTTP/1.1
Authorization: Basic ZGVtby1jbGllbnQ6c2VjcmV0

grant_type=authorization_code&code=code-a1b2c3d4&redirect_uri=...
```
Corresponding to `server.exchangeToken(code, "demo-client", "secret")` — the client's `clientId`/`clientSecret` are verified, the code is consumed, and a token is constructed, signed using the server's generated key (`demo-key-1`).

**Step 7 — the resulting token is a genuine, verifiable JWT** — any resource server configured to trust this authorization server's JWKS endpoint (card 0101's territory) could validate it exactly as any other JWT this course has covered, closing the loop from "assembled a sample configuration" to "produced a real, standards-conformant, verifiable artifact."

```
cold start -> beans constructed (2 chains, UserDetailsService, RegisteredClientRepository, JWKSource)
        |
        v
GET /oauth2/authorize (unauthenticated) -> redirect to /login
        |
        v
POST /login (alice/password123) -> authenticated session
        |
        v
GET /oauth2/authorize (NOW authenticated) -> consent -> code issued -> redirect to demo-client
        |
        v
POST /oauth2/token (client credentials + code) -> REAL, SIGNED JWT issued
```

## 7. Gotchas & takeaways

> **Gotcha:** every demo-marked shortcut in this sample setup (`{noop}` plaintext secrets, in-memory storage, an ephemeral signing key regenerated on every restart) is explicitly unsuitable for production, and it's easy to copy a working sample directly into a real deployment without recognizing which specific pieces need to change first. Treat a sample setup like this as a learning and prototyping tool whose demo-only markers are a checklist for what to replace before going live, not a template to deploy as-is.

- A complete, minimal Bootiful authorization server needs, at minimum: two `SecurityFilterChain` beans (OAuth2-specific and ordinary), a `UserDetailsService`, a `RegisteredClientRepository`, and a `JWKSource` — every piece this section's earlier cards already introduced individually.
- `{noop}` client secrets, in-memory client repositories, and freshly-generated-per-restart signing keys are explicit demo-only shortcuts — production deployments need real password encoding, persistent client storage, and a properly managed (and rotatable) signing key.
- Running through the complete flow end to end — login, consent, code issuance, token exchange, a genuinely signed and verifiable JWT — is the most effective way to confirm understanding of every concept this section introduced, rather than treating each card's material as independent, disconnected facts.
- A working minimal sample setup is also a valuable debugging baseline: if it works but a more complex, production-oriented configuration doesn't, the delta between the two narrows down where the actual configuration problem lies.
- Recognizing which parts of any sample configuration are demo-only shortcuts, versus genuinely reusable patterns, is a skill worth deliberately practicing — it's the difference between learning from an example and accidentally deploying one.
