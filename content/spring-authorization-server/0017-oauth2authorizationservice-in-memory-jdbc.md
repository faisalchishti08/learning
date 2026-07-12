---
card: spring-authorization-server
gi: 17
slug: oauth2authorizationservice-in-memory-jdbc
title: "OAuth2AuthorizationService (in-memory & JDBC)"
---

## 1. What it is

`OAuth2AuthorizationService` is the storage interface for `OAuth2Authorization` records (previous card) — it's the direct analogue of `RegisteredClientRepository`, but for grants-in-progress rather than client registrations. It exposes `save(OAuth2Authorization)`, `remove(OAuth2Authorization)`, and two flavors of lookup: `findById(String)` and `findByToken(String token, OAuth2TokenType tokenType)`. Spring Authorization Server ships `InMemoryOAuth2AuthorizationService` for demos and tests, and `JdbcOAuth2AuthorizationService` for real, persistent, multi-instance deployments.

## 2. Why & when

Authorization codes, access tokens, and refresh tokens all need to be looked up by their raw value at different points in the flow — the token endpoint needs to find "which authorization does this code belong to," the introspection endpoint needs "which authorization does this access token belong to," and the refresh flow needs "which authorization does this refresh token belong to." `OAuth2AuthorizationService` exists so all of that lookup logic is centralized behind one interface, regardless of where the data actually lives.

Reach for the in-memory implementation for demos, tests, and early prototypes — same tradeoffs as `InMemoryRegisteredClientRepository`. Reach for the JDBC implementation (or a custom one, e.g. backed by Redis) when:

- Tokens must survive an authorization server restart.
- You're running more than one authorization server instance behind a load balancer, and a token issued by instance A must be introspectable by instance B.
- You need to support token revocation lists, audit trails, or bulk cleanup of expired authorizations — all of which are far more practical against a real datastore than an in-memory map.

## 3. Core concept

If `OAuth2Authorization` is the case file, `OAuth2AuthorizationService` is the filing cabinet system and its index cards. The crucial detail is that this filing system supports **lookup by any of several different document numbers stapled inside the same file** — you can walk up and ask for "the file containing code ABC123," or "the file containing access token XYZ789," and get back the identical file either way, because internally the index tracks all of a file's document numbers, not just its own case number.

```java
public interface OAuth2AuthorizationService {
    void save(OAuth2Authorization authorization);
    void remove(OAuth2Authorization authorization);
    OAuth2Authorization findById(String id);
    OAuth2Authorization findByToken(String token, OAuth2TokenType tokenType);
}
```

`JdbcOAuth2AuthorizationService` implements this over an `oauth2_authorization` table, storing each token type's value in its own indexed column (`authorization_code_value`, `access_token_value`, `refresh_token_value`, ...) precisely so `findByToken` can do a direct, indexed lookup no matter which token type is being searched for.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OAuth2AuthorizationService supports lookup by id or by any token value">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizationService</text>

  <rect x="20" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">findByToken(code)</text>

  <rect x="185" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">findByToken(access)</text>

  <rect x="350" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="425" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">findByToken(refresh)</text>

  <rect x="490" y="120" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">findById(id)</text>

  <line x1="320" y1="70" x2="95" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="260" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="425" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="555" y2="118" stroke="#3fb950" stroke-width="2"/>

  <text x="320" y="200" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">All four lookups can return the SAME OAuth2Authorization record</text>
</svg>

Four different keys, one shared underlying record, whichever implementation is behind the interface.

## 5. Runnable example

The scenario: saving an authorization and retrieving it by its authorization code, then by its access token, growing from in-memory to a JDBC-backed store and finally handling the redemption-then-invalidate pattern safely.

### Level 1 — Basic

```java
// AuthServiceDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.InMemoryOAuth2AuthorizationService;
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationCode;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationService;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;

public class AuthServiceDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .build();

        Instant now = Instant.now();
        OAuth2AuthorizationCode code = new OAuth2AuthorizationCode("abc123code", now, now.plusSeconds(300));

        OAuth2Authorization authorization = OAuth2Authorization.withRegisteredClient(client)
                .principalName("alice")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizedScopes(Set.of("tasks.read"))
                .token(code)
                .build();

        OAuth2AuthorizationService service = new InMemoryOAuth2AuthorizationService();
        service.save(authorization);

        OAuth2Authorization found = service.findByToken("abc123code",
                new org.springframework.security.oauth2.core.OAuth2TokenType(
                        org.springframework.security.oauth2.core.endpoint.OAuth2ParameterNames.CODE));
        System.out.println("Found by code, principal: " + found.getPrincipalName());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java AuthServiceDemo.java`. Expected output:

```
Found by code, principal: alice
```

### Level 2 — Intermediate

A real deployment needs authorizations to survive a restart, so we swap in `JdbcOAuth2AuthorizationService`, backed by the library's own schema and a `RegisteredClientRepository` (it needs one, to reconstruct the `RegisteredClient` reference on each `OAuth2Authorization` it loads).

```java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.JdbcOAuth2AuthorizationService;
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationCode;
import org.springframework.security.oauth2.server.authorization.client.InMemoryRegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;

import javax.sql.DataSource;
import java.time.Instant;
import java.util.Set;
import java.util.UUID;

public class AuthServiceDemo {
    public static void main(String[] args) {
        DataSource dataSource = new EmbeddedDatabaseBuilder()
                .setType(EmbeddedDatabaseType.H2)
                .addScript("org/springframework/security/oauth2/server/authorization/client/oauth2-registered-client-schema.sql")
                .addScript("org/springframework/security/oauth2/server/authorization/oauth2-authorization-schema.sql")
                .build();

        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .build();

        RegisteredClientRepository clientRepository = new InMemoryRegisteredClientRepository(client);
        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);
        clientRepository = new org.springframework.security.oauth2.server.authorization.client.JdbcRegisteredClientRepository(jdbcTemplate);
        clientRepository.save(client);

        JdbcOAuth2AuthorizationService authorizationService =
                new JdbcOAuth2AuthorizationService(jdbcTemplate, clientRepository);

        Instant now = Instant.now();
        OAuth2AuthorizationCode code = new OAuth2AuthorizationCode("abc123code", now, now.plusSeconds(300));
        OAuth2Authorization authorization = OAuth2Authorization.withRegisteredClient(client)
                .principalName("alice")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizedScopes(Set.of("tasks.read"))
                .token(code)
                .build();

        authorizationService.save(authorization);

        OAuth2Authorization found = authorizationService.findById(authorization.getId());
        System.out.println("Persisted and reloaded, principal: " + found.getPrincipalName());
    }
}
```

**How to run:** add H2 and `spring-jdbc` to the classpath; run the same way. Expected output:

```
Persisted and reloaded, principal: alice
```

What changed: authorizations now live in a real `oauth2_authorization` table and survive restarts, and `JdbcOAuth2AuthorizationService` needs a `RegisteredClientRepository` because reconstructing a stored `OAuth2Authorization` requires re-attaching the actual `RegisteredClient` object, not just its ID.

### Level 3 — Advanced

Production correctly handles the redemption-then-invalidate pattern: looking up by code, checking it's still active, and atomically marking it consumed so a replayed code can never be redeemed twice — a real security requirement, not an edge case.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationCode;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationService;
import org.springframework.security.oauth2.core.OAuth2TokenType;
import org.springframework.security.oauth2.core.endpoint.OAuth2ParameterNames;

public class CodeRedemption {

    public static OAuth2Authorization redeemAuthorizationCode(
            OAuth2AuthorizationService authorizationService, String codeValue) {

        OAuth2Authorization authorization = authorizationService.findByToken(
                codeValue, new OAuth2TokenType(OAuth2ParameterNames.CODE));

        if (authorization == null) {
            throw new IllegalArgumentException("invalid_grant: no such authorization code");
        }

        OAuth2Authorization.Token<OAuth2AuthorizationCode> authorizationCode =
                authorization.getToken(OAuth2AuthorizationCode.class);

        if (!authorizationCode.isActive()) {
            // code was already used, or has expired -- per RFC 6749 this should
            // also trigger revocation of any tokens already issued from this authorization
            throw new IllegalStateException("invalid_grant: authorization code already used or expired");
        }

        // invalidate the code so it can never be redeemed again, then save
        OAuth2Authorization updated = OAuth2Authorization.from(authorization)
                .token(authorizationCode.getToken(), metadata ->
                        metadata.put(OAuth2Authorization.Token.INVALIDATED_METADATA_NAME, true))
                .build();

        authorizationService.save(updated);
        return updated;
    }
}
```

**How to run:** call `redeemAuthorizationCode(authorizationService, "abc123code")` against the service built in Level 2; a second call with the same code value throws `IllegalStateException`, matching the RFC 6749 requirement that a reused code must be rejected. Expected output on second call:

```
Exception in thread "main" java.lang.IllegalStateException: invalid_grant: authorization code already used or expired
```

What changed and why it's production-flavored: this is the exact check-then-invalidate sequence Spring Authorization Server's own token endpoint performs internally — treating a found-but-inactive code as an error rather than silently succeeding is what prevents a captured, already-redeemed code from being replayed by an attacker to obtain a second, independent set of tokens.

## 6. Walkthrough

Tracing a code redemption through `OAuth2AuthorizationService`, in execution order:

1. `POST /oauth2/token` arrives with `grant_type=authorization_code&code=abc123code`.
2. The token endpoint calls `authorizationService.findByToken("abc123code", CODE_TOKEN_TYPE)`.
3. `JdbcOAuth2AuthorizationService` runs a `SELECT ... WHERE authorization_code_value = ?` against the indexed column, deserializes the row's JSON-encoded `OAuth2Authorization`, and reattaches the `RegisteredClient` via the injected repository.
4. The endpoint checks `authorizationCode.isActive()` — true the first time — then proceeds to generate an access token and (if the client supports it) a refresh token.
5. It builds an **updated** `OAuth2Authorization` (Level 3's pattern): the code marked invalidated, the new access and refresh tokens attached, and calls `save` — which for the JDBC implementation is an `UPDATE` against the same row (matched by `id`), not an insert of a new one.
6. The response `{"access_token": "...", "refresh_token": "...", "token_type": "Bearer", "expires_in": 600}` goes back to the client.
7. If the same code is replayed — an attacker who intercepted it, or a buggy client retrying — step 4's `isActive()` check now returns false, and the endpoint responds `400 Bad Request` with `{"error": "invalid_grant"}` instead of minting a second set of tokens.

```
findByToken(code) --SELECT WHERE authorization_code_value=?--> row found
        |
   isActive()? --true (first time)--> issue tokens, mark code invalidated, UPDATE row
        |
   isActive()? --false (replay)-----> 400 invalid_grant, no tokens issued
```

## 7. Gotchas & takeaways

> Marking a code invalidated and issuing new tokens must happen together, saved as one update — if a crash or bug invalidates the code but fails to save the new tokens (or vice versa), the client is left with a permanently unusable code and no tokens, which is a hard-to-diagnose failure mode worth testing for explicitly.

- `findByToken` needs the correct `OAuth2TokenType` to know which column (or map key, for in-memory) to search — passing the wrong type for a given token value simply returns null, which can look like "the token doesn't exist" when it actually does.
- `JdbcOAuth2AuthorizationService` requires a `RegisteredClientRepository` in its constructor specifically to reconstruct the `RegisteredClient` reference on load — a common setup mistake is wiring it with a repository that doesn't actually contain the client the stored authorization references.
- In-memory authorizations vanish on restart — fine for demos, but any client mid-flow during a restart (e.g. holding an unredeemed code) will get `invalid_grant` afterward.
- For multi-instance deployments, `JdbcOAuth2AuthorizationService` (or an equivalent shared store) is not optional — an in-memory service means a token issued by instance A is invisible to instance B, breaking introspection and revocation behind a load balancer.
- Expired authorizations accumulate in the JDBC table over time — a real deployment needs a periodic cleanup job (there's no automatic pruning built in) to avoid unbounded table growth.
