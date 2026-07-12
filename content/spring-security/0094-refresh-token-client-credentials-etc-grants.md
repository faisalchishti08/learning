---
card: spring-security
gi: 94
slug: refresh-token-client-credentials-etc-grants
title: "Refresh token / client credentials / etc. grants"
---

## 1. What it is

The Authorization Code grant (cards 0089–0090) is only one of several ways an OAuth2 client can obtain an access token. Two others matter for everyday Spring Security work: the **`refresh_token` grant**, which trades a long-lived refresh token for a brand-new access token *without* re-prompting the user — this is exactly what `OAuth2AuthorizedClientProvider`'s built-in `refreshToken()` provider does transparently whenever an `OAuth2AuthorizedClient`'s access token has expired — and the **`client_credentials` grant**, which has no end user at all: the client authenticates as *itself*, using its own `client-id`/`client-secret`, and receives a token that represents the client (a machine, a batch job, a backend service), not any delegated human. A handful of older or narrower grants round out the picture: the **`password` grant** (deprecated and actively discouraged by the OAuth 2.0 Security Best Current Practice) and the **JWT bearer grant** (exchanging a trusted third party's signed assertion for a token, common in service-federation setups).

```java
@Bean
public OAuth2AuthorizedClientProvider authorizedClientProvider() {
    return OAuth2AuthorizedClientProviderBuilder.builder()
            .authorizationCode()
            .refreshToken()          // handles expired user-delegated tokens automatically
            .clientCredentials()     // handles machine-to-machine registrations
            .build();
}
```

## 2. Why & when

Each grant solves a problem the Authorization Code grant alone cannot. Access tokens are deliberately short-lived (minutes, not days) to limit the damage of a leaked token — but re-running the full browser redirect dance every few minutes to get a new one would be unusable. The `refresh_token` grant closes that gap: the authorization server hands the client a separate, longer-lived refresh token during the *original* login, and from then on the client silently exchanges it for fresh access tokens as needed, with the user none the wiser. The `client_credentials` grant solves an entirely different problem: some callers *are not acting on behalf of any user* — a nightly reporting job pulling data from a partner API, or one microservice calling another — and forcing them through a user-facing login flow makes no sense when there is no user to log in.

Reach for each grant specifically when:

- An `OAuth2AuthorizedClient`'s access token has expired and the client holds a valid refresh token — `refreshToken()` in the provider chain (card 0093) handles this automatically on the next `WebClient` call (card 0092), so application code rarely calls it directly.
- A registration represents a machine identity rather than a delegated user — configure it with `authorization-grant-type: client_credentials` and no user ever sees a login screen for it.
- Legacy integration work surfaces a `password` grant still in use — recognize it as deprecated: it requires the client application to directly handle the resource owner's raw username and password, which defeats OAuth2's core purpose of never sharing credentials with third-party clients; migrate away from it when possible.
- A trusted upstream system (an internal identity broker, a partner's signing service) issues signed assertions your application should accept without a password or a redirect — the JWT bearer grant exists for exactly that federation scenario.

## 3. Core concept

```
refresh_token grant (a USER is involved, just not interactively):
  client -> POST /token  { grant_type=refresh_token, refresh_token=<stored> }
  authorization server -> { access_token=<new>, refresh_token=<new-or-same>, expires_in=... }
  subject of the new access token = the SAME end user who originally logged in

client_credentials grant (NO user at all):
  client -> POST /token  { grant_type=client_credentials, client_id=..., client_secret=... }
  authorization server -> { access_token=<new>, expires_in=... }         (no refresh_token issued)
  subject of the access token = the CLIENT ITSELF (a machine identity)

password grant (DEPRECATED -- avoid):
  client -> POST /token  { grant_type=password, username=..., password=... }
  the CLIENT sees the user's raw password directly -- defeats delegated authorization's purpose

jwt-bearer grant (federation):
  client -> POST /token  { grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer, assertion=<signed JWT> }
  authorization server verifies the assertion's issuer/signature, then issues its OWN access token
```

The dividing line that matters most: does a token represent a delegated human (`refresh_token`, `password`) or the client's own machine identity (`client_credentials`, typically `jwt-bearer`)?

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two lanes contrast the refresh token grant where a client exchanges a stored refresh token for a new access token still representing the original end user against the client credentials grant where a client authenticates with its own client id and secret directly and receives an access token that represents the client itself with no end user involved">
  <rect x="15" y="15" width="610" height="105" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="32" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">refresh_token grant -- subject is still the end user</text>

  <rect x="35" y="50" width="150" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="110" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="110" y="84" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">holds refresh_token</text>

  <line x1="185" y1="73" x2="415" y2="73" stroke="#6db33f" stroke-width="2" marker-end="url(#a94)"/>
  <text x="300" y="65" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">POST /token grant_type=refresh_token</text>

  <rect x="420" y="50" width="180" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="510" y="70" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Authorization Server</text>
  <text x="510" y="84" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">new access_token, same subject</text>

  <rect x="15" y="140" width="610" height="105" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="157" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">client_credentials grant -- no end user at all</text>

  <rect x="35" y="175" width="150" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="110" y="195" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="110" y="209" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">its own client_id/secret</text>

  <line x1="185" y1="198" x2="415" y2="198" stroke="#6db33f" stroke-width="2" marker-end="url(#a94b)"/>
  <text x="300" y="190" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">POST /token grant_type=client_credentials</text>

  <rect x="420" y="175" width="180" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="510" y="195" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Authorization Server</text>
  <text x="510" y="209" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">access_token, subject=client itself</text>

  <defs>
    <marker id="a94" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="a94b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The top lane still speaks for a human; the bottom lane speaks only for the machine that sent it.

## 5. Runnable example

The scenario: a small in-memory authorization server that grows across three levels — first honoring only `refresh_token`, then adding `client_credentials` alongside a provider-selection layer, then hardening both with refresh-token rotation, replay detection, response caching, and the legacy `password`/JWT-bearer grants for completeness.

### Level 1 — Basic

A fake authorization server that issues an initial access + refresh token pair, then honors the `refresh_token` grant using virtual (manually advanced) time instead of real clock ticks, so the example is deterministic and instant.

```java
import java.util.*;

public class GrantsLevel1 {

    // an access token: an opaque value plus when it expires, in "virtual" milliseconds
    record AccessToken(String value, long expiresAtMillis) {
        boolean isExpired(long now) {
            return now >= expiresAtMillis;
        }
    }

    // a minimal fake authorization server: issues token pairs and honors the refresh_token grant
    static class AuthorizationServer {
        private int counter = 0;
        private final Map<String, String> refreshTokenToSubject = new HashMap<>();

        // simulates the initial Authorization Code exchange: issues an access token AND a refresh token
        AccessToken issueInitialTokens(String subject, long now, Map<String, String> refreshTokenOut) {
            counter++;
            String refreshToken = "refresh-" + subject + "-" + counter;
            refreshTokenToSubject.put(refreshToken, subject);
            refreshTokenOut.put(subject, refreshToken);
            return new AccessToken("access-" + counter, now + 5_000);
        }

        // the refresh_token grant: trade a still-valid refresh token for a brand-new access token,
        // WITHOUT involving the resource owner (the user) at all -- no browser redirect, no login screen
        AccessToken refresh(String refreshToken, long now) {
            String subject = refreshTokenToSubject.get(refreshToken);
            if (subject == null) {
                throw new IllegalStateException("unknown or revoked refresh token");
            }
            counter++;
            return new AccessToken("access-" + counter, now + 5_000);
        }
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();
        Map<String, String> refreshTokens = new HashMap<>();
        long now = 0;

        AccessToken initial = server.issueInitialTokens("alice", now, refreshTokens);
        System.out.println("Initial access token: " + initial.value() + ", expires at " + initial.expiresAtMillis());

        now = 6_000; // 6 seconds of virtual time pass -- longer than the 5-second lifetime
        System.out.println("Token expired? " + initial.isExpired(now));

        AccessToken refreshed = server.refresh(refreshTokens.get("alice"), now);
        System.out.println("Refreshed access token: " + refreshed.value() + ", expires at " + refreshed.expiresAtMillis());
    }
}
```

**How to run:** save as `GrantsLevel1.java`, run `java GrantsLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Initial access token: access-1, expires at 5000
Token expired? true
Refreshed access token: access-2, expires at 11000
```

`issueInitialTokens` hands out both tokens at once, mirroring the original Authorization Code exchange; once virtual time passes the 5-second lifetime, `refresh` looks up the subject behind the refresh token and mints a new access token — the user never sees any of this happen.

### Level 2 — Intermediate

Add the `client_credentials` grant alongside a small provider-selection layer that picks the right grant per registration — mirroring how `OAuth2AuthorizedClientProviderBuilder` chains multiple providers and each one decides whether it applies.

```java
import java.util.*;

public class GrantsLevel2 {

    record AccessToken(String value, long expiresAtMillis, String subject) {
        boolean isExpired(long now) { return now >= expiresAtMillis; }
    }

    static class AuthorizationServer {
        private int counter = 0;
        private final Map<String, String> refreshTokenToSubject = new HashMap<>();
        // registered machine clients: clientId -> secret (known only to the client and this server)
        private final Map<String, String> registeredClients = new HashMap<>();

        void registerClient(String clientId, String secret) {
            registeredClients.put(clientId, secret);
        }

        AccessToken issueInitialTokens(String subject, long now, Map<String, String> refreshTokenOut) {
            counter++;
            String refreshToken = "refresh-" + subject + "-" + counter;
            refreshTokenToSubject.put(refreshToken, subject);
            refreshTokenOut.put(subject, refreshToken);
            return new AccessToken("access-" + counter, now + 5_000, subject);
        }

        AccessToken refresh(String refreshToken, long now) {
            String subject = refreshTokenToSubject.get(refreshToken);
            if (subject == null) throw new IllegalStateException("unknown or revoked refresh token");
            counter++;
            return new AccessToken("access-" + counter, now + 5_000, subject);
        }

        // the client_credentials grant: the CLIENT authenticates as ITSELF, with its own id/secret --
        // there is no end user, no browser redirect, no refresh token -- the client just asks again when needed
        AccessToken clientCredentials(String clientId, String clientSecret, long now) {
            String expected = registeredClients.get(clientId);
            if (expected == null || !expected.equals(clientSecret)) {
                throw new IllegalStateException("invalid client credentials");
            }
            counter++;
            // subject IS the client itself -- this token represents the machine, not a delegated human user
            return new AccessToken("access-" + counter, now + 5_000, clientId);
        }
    }

    // mirrors Spring Security's OAuth2AuthorizedClientProvider chain: pick the right grant per registration
    enum GrantType { AUTHORIZATION_CODE, CLIENT_CREDENTIALS }

    record ClientRegistration(String registrationId, GrantType grantType, String clientId, String clientSecret) {}

    static AccessToken authorize(AuthorizationServer server, ClientRegistration reg, long now,
                                  Map<String, String> userRefreshTokens) {
        return switch (reg.grantType()) {
            case CLIENT_CREDENTIALS -> server.clientCredentials(reg.clientId(), reg.clientSecret(), now);
            case AUTHORIZATION_CODE -> {
                String existingRefresh = userRefreshTokens.get(reg.registrationId());
                if (existingRefresh == null) {
                    yield server.issueInitialTokens(reg.registrationId(), now, userRefreshTokens);
                }
                yield server.refresh(existingRefresh, now);
            }
        };
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();
        server.registerClient("reporting-service", "s3cr3t");

        Map<String, String> userRefreshTokens = new HashMap<>();
        long now = 0;

        ClientRegistration userFacing = new ClientRegistration("github", GrantType.AUTHORIZATION_CODE, null, null);
        ClientRegistration machineToMachine = new ClientRegistration("reporting-service", GrantType.CLIENT_CREDENTIALS,
                "reporting-service", "s3cr3t");

        AccessToken userToken = authorize(server, userFacing, now, userRefreshTokens);
        System.out.println("User-facing token (subject=" + userToken.subject() + "): " + userToken.value());

        AccessToken machineToken = authorize(server, machineToMachine, now, userRefreshTokens);
        System.out.println("Machine-to-machine token (subject=" + machineToken.subject() + "): " + machineToken.value());

        now = 6_000;
        AccessToken refreshedUserToken = authorize(server, userFacing, now, userRefreshTokens);
        System.out.println("Refreshed user-facing token (subject=" + refreshedUserToken.subject() + "): " + refreshedUserToken.value());

        AccessToken newMachineToken = authorize(server, machineToMachine, now, userRefreshTokens);
        System.out.println("New machine-to-machine token (subject=" + newMachineToken.subject() + "): " + newMachineToken.value());
    }
}
```

**How to run:** save as `GrantsLevel2.java`, run `java GrantsLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
User-facing token (subject=github): access-1
Machine-to-machine token (subject=reporting-service): access-2
Refreshed user-facing token (subject=github): access-3
New machine-to-machine token (subject=reporting-service): access-4
```

`authorize` now dispatches on `GrantType`, exactly like a provider chain trying each `OAuth2AuthorizedClientProvider` in turn: the `github` registration always goes through `refresh_token` once it has a stored refresh token, while `reporting-service` always goes through `client_credentials` — notice its resulting tokens carry the client's own id as the subject, never a human's.

### Level 3 — Advanced

Production systems add three hardenings this level demonstrates together: **refresh-token rotation** (each use invalidates the old refresh token and issues a new one, so a stolen-then-reused old token is detectable), **response caching** (don't hit the token endpoint again if a cached token isn't expired yet), and the legacy **`password`** and **JWT bearer** grants, shown for completeness with the deprecation of the former clearly called out.

```java
import java.util.*;

public class GrantsLevel3 {

    record AccessToken(String value, long expiresAtMillis, String subject) {
        boolean isExpired(long now) { return now >= expiresAtMillis; }
    }
    record TokenPair(AccessToken accessToken, String refreshToken) {}

    static class AuthorizationServer {
        private int counter = 0;
        private final Map<String, String> refreshTokenToSubject = new HashMap<>(); // VALID refresh tokens only
        private final Map<String, String> registeredClients = new HashMap<>();
        private final Map<String, String> userPasswords = new HashMap<>();
        private final Set<String> trustedJwtIssuers = new HashSet<>();

        void registerClient(String clientId, String secret) { registeredClients.put(clientId, secret); }
        void registerUser(String username, String password) { userPasswords.put(username, password); }
        void trustIssuer(String issuer) { trustedJwtIssuers.add(issuer); }

        TokenPair issueInitialTokenPair(String subject, long now) {
            counter++;
            String refreshToken = "refresh-" + subject + "-" + counter;
            refreshTokenToSubject.put(refreshToken, subject);
            AccessToken at = new AccessToken("access-" + counter, now + 5_000, subject);
            return new TokenPair(at, refreshToken);
        }

        // refresh_token grant WITH ROTATION: the old refresh token is consumed (removed) on use,
        // and a brand-new one is issued -- reusing an already-consumed refresh token is now detectable
        TokenPair refresh(String refreshToken, long now) {
            String subject = refreshTokenToSubject.remove(refreshToken); // one-time use
            if (subject == null) {
                throw new IllegalStateException("refresh token invalid, expired, or already used (possible replay)");
            }
            counter++;
            String newRefreshToken = "refresh-" + subject + "-" + counter;
            refreshTokenToSubject.put(newRefreshToken, subject);
            AccessToken at = new AccessToken("access-" + counter, now + 5_000, subject);
            return new TokenPair(at, newRefreshToken);
        }

        AccessToken clientCredentials(String clientId, String secret, long now) {
            String expected = registeredClients.get(clientId);
            if (expected == null || !expected.equals(secret)) throw new IllegalStateException("invalid client credentials");
            counter++;
            return new AccessToken("access-" + counter, now + 5_000, clientId);
        }

        // legacy "password" grant -- DEPRECATED, the OAuth 2.0 Security BCP discourages it: the CLIENT
        // handles the user's raw password directly, defeating the purpose of delegated authorization
        AccessToken passwordGrant(String username, String password, long now) {
            String expected = userPasswords.get(username);
            if (expected == null || !expected.equals(password)) throw new IllegalStateException("invalid resource owner credentials");
            counter++;
            return new AccessToken("access-" + counter, now + 5_000, username);
        }

        // JWT bearer grant: exchange a JWT ASSERTION issued by a TRUSTED third party for an access token --
        // no password, no browser redirect, common in service-federation / trusted-broker scenarios
        AccessToken jwtBearer(String assertionIssuer, String assertionSubject, long now) {
            if (!trustedJwtIssuers.contains(assertionIssuer)) throw new IllegalStateException("untrusted assertion issuer");
            counter++;
            return new AccessToken("access-" + counter, now + 5_000, assertionSubject);
        }
    }

    // mirrors an OAuth2AuthorizedClientManager: caches tokens, only calls the server when actually needed
    static class AuthorizedClientManager {
        private final AuthorizationServer server;
        private final Map<String, AccessToken> tokenCache = new HashMap<>();
        private final Map<String, String> refreshTokenCache = new HashMap<>();

        AuthorizedClientManager(AuthorizationServer server) { this.server = server; }

        AccessToken authorizationCode(String registrationId, long now) {
            AccessToken cached = tokenCache.get(registrationId);
            if (cached != null && !cached.isExpired(now)) {
                System.out.println("  (cache hit for " + registrationId + ")");
                return cached;
            }
            String existingRefresh = refreshTokenCache.get(registrationId);
            TokenPair pair = existingRefresh == null
                    ? server.issueInitialTokenPair(registrationId, now)
                    : server.refresh(existingRefresh, now);
            tokenCache.put(registrationId, pair.accessToken());
            refreshTokenCache.put(registrationId, pair.refreshToken());
            return pair.accessToken();
        }

        AccessToken clientCredentials(String registrationId, String clientId, String secret, long now) {
            AccessToken cached = tokenCache.get(registrationId);
            if (cached != null && !cached.isExpired(now)) {
                System.out.println("  (cache hit for " + registrationId + ")");
                return cached;
            }
            AccessToken fresh = server.clientCredentials(clientId, secret, now);
            tokenCache.put(registrationId, fresh);
            return fresh;
        }
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();
        server.registerClient("reporting-service", "s3cr3t");
        server.registerUser("alice", "hunter2");
        server.trustIssuer("partner-idp");

        AuthorizedClientManager manager = new AuthorizedClientManager(server);
        long now = 0;

        System.out.println("-- Authorization Code grant, first call --");
        System.out.println("token: " + manager.authorizationCode("github", now).value());

        System.out.println("-- Authorization Code grant, immediate second call (same virtual time) --");
        System.out.println("token: " + manager.authorizationCode("github", now).value());

        now = 6_000;
        System.out.println("-- Authorization Code grant, after expiry (triggers refresh_token grant) --");
        System.out.println("token: " + manager.authorizationCode("github", now).value());

        // a REPLAY: something captured the very first refresh token and tries to reuse it after rotation
        try {
            server.refresh("refresh-github-1", now);
        } catch (IllegalStateException e) {
            System.out.println("Replay of rotated refresh token rejected: " + e.getMessage());
        }

        System.out.println("-- client_credentials grant, first call --");
        System.out.println("token: " + manager.clientCredentials("reporting-service", "reporting-service", "s3cr3t", now).value());

        System.out.println("-- client_credentials grant, immediate second call (cached, no server round trip) --");
        System.out.println("token: " + manager.clientCredentials("reporting-service", "reporting-service", "s3cr3t", now).value());

        System.out.println("-- legacy password grant (deprecated -- shown for completeness only) --");
        AccessToken p1 = server.passwordGrant("alice", "hunter2", now);
        System.out.println("token: " + p1.value() + " (subject=" + p1.subject() + ")");

        System.out.println("-- JWT bearer grant (trusted assertion, no password, no redirect) --");
        AccessToken j1 = server.jwtBearer("partner-idp", "service-account-42", now);
        System.out.println("token: " + j1.value() + " (subject=" + j1.subject() + ")");
    }
}
```

**How to run:** save as `GrantsLevel3.java`, run `java GrantsLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
-- Authorization Code grant, first call --
token: access-1
-- Authorization Code grant, immediate second call (same virtual time) --
  (cache hit for github)
token: access-1
-- Authorization Code grant, after expiry (triggers refresh_token grant) --
token: access-2
Replay of rotated refresh token rejected: refresh token invalid, expired, or already used (possible replay)
-- client_credentials grant, first call --
token: access-3
-- client_credentials grant, immediate second call (cached, no server round trip) --
  (cache hit for reporting-service)
token: access-3
-- legacy password grant (deprecated -- shown for completeness only) --
token: access-4 (subject=alice)
-- JWT bearer grant (trusted assertion, no password, no redirect) --
token: access-5 (subject=service-account-42)
```

The manager caches every token and only calls the server again once a token actually expires; rotation means the very first refresh token cannot be replayed after it's been consumed once; `client_credentials` tokens have no refresh token at all, so a fresh call simply repeats the same grant when the cache expires.

## 6. Walkthrough

Trace `GrantsLevel3.main()` end to end, focusing on the `github` registration's Authorization Code lifecycle and its concrete wire traffic.

1. `manager.authorizationCode("github", 0)` finds no cached token, no stored refresh token, so it calls `server.issueInitialTokenPair("github", 0)`. This stands in for the very first `POST /token` after the browser redirect completed:
   ```
   POST /token HTTP/1.1
   Host: as.example.com
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code&code=abc123&redirect_uri=https://app.example.com/callback
   ```
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   { "access_token": "access-1", "refresh_token": "refresh-github-1", "expires_in": 5 }
   ```
2. The manager caches `access-1` under `"github"` and stores `refresh-github-1` in `refreshTokenCache`. `access-1` is printed.
3. The immediate second call at the same virtual time (`now = 0`) finds `tokenCache.get("github")` non-null and `!cached.isExpired(0)` true (`0 >= 5000` is false) — a **cache hit**, no server call at all, `access-1` is returned again.
4. `now` advances to `6_000`. The third call finds the cached token *is* expired (`6000 >= 5000`), so it falls back to `refreshTokenCache.get("github")`, which holds `refresh-github-1`, and calls `server.refresh("refresh-github-1", 6000)` — the `refresh_token` grant:
   ```
   POST /token HTTP/1.1
   Host: as.example.com
   Content-Type: application/x-www-form-urlencoded

   grant_type=refresh_token&refresh_token=refresh-github-1
   ```
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   { "access_token": "access-2", "refresh_token": "refresh-github-2", "expires_in": 5 }
   ```
5. Inside `refresh`, `refreshTokenToSubject.remove("refresh-github-1")` both looks up **and deletes** the entry — this is rotation: `refresh-github-1` can never be presented again. A new pair (`access-2`, `refresh-github-2`) is minted and cached.
6. The next line deliberately replays the now-dead `refresh-github-1`. `refreshTokenToSubject.remove(...)` returns `null` (it was already removed in step 5), so `refresh` throws `IllegalStateException("refresh token invalid, expired, or already used (possible replay)")` — caught and printed. A real authorization server responds to this with an error body instead of an exception:
   ```
   HTTP/1.1 400 Bad Request
   Content-Type: application/json

   { "error": "invalid_grant", "error_description": "refresh token already used" }
   ```
7. `manager.clientCredentials("reporting-service", ...)` has no cached token, so it calls `server.clientCredentials("reporting-service", "s3cr3t", 6000)`, which checks the secret and returns `access-3` — subject is `"reporting-service"` itself, not any user. The equivalent wire request carries the client's own credentials, not a user's:
   ```
   POST /token HTTP/1.1
   Host: as.example.com
   Content-Type: application/x-www-form-urlencoded

   grant_type=client_credentials&client_id=reporting-service&client_secret=s3cr3t
   ```
8. The immediate second `client_credentials` call at the same `now` hits the cache (`access-3` not yet expired) and skips the server entirely — printed with `(cache hit ...)`.
9. `passwordGrant` and `jwtBearer` run last, each independently issuing `access-4` and `access-5`; neither depends on or interacts with the refresh-token or client-credentials state above, since each grant type is a self-contained way of reaching the same `/token` endpoint with different parameters.

## 7. Gotchas & takeaways

> **Gotcha:** a refresh token failing with `invalid_grant` doesn't always mean an attack — refresh token rotation means the *previous* refresh token is deliberately invalidated the moment a new one is issued, so if a client crashes after receiving a rotated pair but before persisting it, its next attempt to use the *old* (now-dead) refresh token looks identical to a replay attempt. Production systems typically need a short grace window or a "reuse detected — revoke the whole token family" policy rather than treating every failure as a live attack.

- `refresh_token` keeps a user logged in across short-lived access tokens without ever showing them a login screen again; it is what `OAuth2AuthorizedClientProvider.refreshToken()` does automatically inside `AuthorizedClientManager`.
- `client_credentials` has no user in the picture at all — the resulting access token's subject is the client itself, appropriate for service-to-service and batch-job calls, and typically comes with no refresh token since the client can simply re-authenticate itself at any time.
- The `password` grant is deprecated: it requires the client to see the user's raw credentials, which is precisely what OAuth2 exists to avoid; treat any code still using it as a migration target, not a pattern to copy.
- The JWT bearer grant lets a trusted third party vouch for an identity via a signed assertion instead of a password or browser redirect — useful for federation between systems that already trust each other.
- Refresh token rotation (a new refresh token on every use, with the old one invalidated) is a production hardening that turns "was this refresh token stolen and reused?" into a detectable event instead of a silent vulnerability.
