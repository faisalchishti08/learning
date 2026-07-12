---
card: spring-security
gi: 91
slug: oauth2authorizedclient-repository-service
title: "OAuth2AuthorizedClient & repository/service"
---

## 1. What it is

`OAuth2AuthorizedClient` is the object Spring Security produces once a user has successfully completed an OAuth2/OIDC login (or any other supported grant): it pairs a `ClientRegistration` (the static configuration for one provider — Google, GitHub, an internal auth server) with the actual **access token** issued for one specific end-user `principal`, plus an optional **refresh token** if the provider issued one. It is the runtime answer to "does this user currently have a usable token for this provider, and what is it?" Two collaborating abstractions manage that object's lifecycle: `OAuth2AuthorizedClientRepository`, an HTTP-session-scoped interface tied to the current `HttpServletRequest`/`HttpServletResponse` that the OAuth2 login filter calls on every request to load or save the authorized client; and `OAuth2AuthorizedClientService`, a more general storage-backed abstraction — `InMemoryOAuth2AuthorizedClientService` by default, or a `JdbcOAuth2AuthorizedClientService` backed by a real table — that the default repository implementation (`AuthenticatedPrincipalOAuth2AuthorizedClientRepository`) delegates to underneath for the actual persistence.

```java
@Bean
public OAuth2AuthorizedClientService authorizedClientService(ClientRegistrationRepository clientRegistrationRepository) {
    // swap in a JdbcOAuth2AuthorizedClientService here for persistence across restarts / multiple instances
    return new InMemoryOAuth2AuthorizedClientService(clientRegistrationRepository);
}

@Bean
public OAuth2AuthorizedClientRepository authorizedClientRepository(OAuth2AuthorizedClientService service) {
    // the repository is what request-handling code talks to; it DELEGATES to the service for real storage
    return new AuthenticatedPrincipalOAuth2AuthorizedClientRepository(service);
}
```

## 2. Why & when

The split exists because "loading a token for this request" and "persisting a token somewhere" are genuinely different concerns with different natural lifetimes. The **repository** is the interface the OAuth2 login filter and resource-fetching code actually call per-request — its contract (`loadAuthorizedClient`, `saveAuthorizedClient`, `removeAuthorizedClient`) is deliberately shaped around the current `HttpServletRequest`/`HttpServletResponse`, because in the most common setup the client is really being looked up "for the currently logged-in user of this session." The **service**, by contrast, has no notion of a servlet request at all — it is a plain key-value store keyed by `(registrationId, principalName)`, which makes it swappable independently of how a request arrives: in-memory for a single instance during development, JDBC-backed for a real deployment where tokens must survive a restart or be visible across multiple application instances.

Reach for understanding this split when:

- Explaining why a user's OAuth2 access token "disappears" after a server restart — the default `InMemoryOAuth2AuthorizedClientService` is exactly that, in-memory, and is wiped on restart; a `JdbcOAuth2AuthorizedClientService` (or a custom implementation backed by Redis or your own table) is what production deployments with multiple instances or restart resilience actually need.
- Writing a custom `OAuth2AuthorizedClientRepository` — for example, one that stores the authorized client in a signed cookie instead of the `HttpSession`, useful for stateless deployments that avoid server-side sessions entirely.
- Deciding where to plug in custom persistence: implement `OAuth2AuthorizedClientService` (the storage abstraction) for a new backing store, not `OAuth2AuthorizedClientRepository` (the request-scoped contract), unless you also need to change *how* the client is correlated to the current request itself.
- Manually loading a previously authorized client inside a controller or service method — via `@RegisteredOAuth2AuthorizedClient` (backed by the repository) for request-handling code, or by injecting the `OAuth2AuthorizedClientService` directly for background/non-request code (a scheduled job refreshing tokens, for instance).

## 3. Core concept

```
OAuth2AuthorizedClient (one instance, PER user PER provider):
    ClientRegistration registration   -- WHICH provider (static config, from ClientRegistrationRepository)
    String principalName              -- WHICH end-user this token belongs to
    OAuth2AccessToken accessToken      -- the actual bearer token, with an expiresAt instant
    OAuth2RefreshToken refreshToken    -- optional; present if the provider issued one

OAuth2AuthorizedClientRepository (HTTP-session-scoped, tied to the CURRENT request):
    loadAuthorizedClient(registrationId, principal, request)               -- called on EVERY request needing a token
    saveAuthorizedClient(authorizedClient, principal, request, response)   -- called once login / refresh completes
    removeAuthorizedClient(registrationId, principal, request, response)   -- called on logout / revocation

    DEFAULT implementation: AuthenticatedPrincipalOAuth2AuthorizedClientRepository
        -- has NO storage of its own -- DELEGATES every call straight through to a Service

OAuth2AuthorizedClientService (general, storage-backed, NO request/response parameters at all):
    loadAuthorizedClient(registrationId, principalName)     -- keyed by (provider id, username) ONLY
    saveAuthorizedClient(authorizedClient, principal)
    removeAuthorizedClient(registrationId, principalName)

    InMemoryOAuth2AuthorizedClientService   -- default; a Map, wiped on restart
    JdbcOAuth2AuthorizedClientService       -- real table; survives restarts, shared across instances
```

The repository is the per-request front door; the service is the actual filing cabinet behind it.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request carrying a session cookie reaches the OAuth2 authorized client repository which has no storage of its own and delegates to the authorized client service the service looks up the authorized client by registration id and principal name in its backing store either an in memory map or a jdbc table and returns it to the repository which returns it to the calling code">
  <rect x="15" y="15" width="610" height="230" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="34" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Per-request token lookup</text>

  <rect x="35" y="60" width="150" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">HttpServletRequest</text>
  <text x="110" y="96" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">session cookie present</text>

  <rect x="240" y="60" width="180" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="330" y="80" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizedClient-</text>
  <text x="330" y="94" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">Repository</text>

  <line x1="185" y1="85" x2="235" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#a91)"/>

  <text x="330" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">delegates -- NO storage of its own</text>
  <line x1="330" y1="110" x2="330" y2="150" stroke="#8b949e" stroke-width="1.6" marker-end="url(#a91)"/>

  <rect x="240" y="152" width="180" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="330" y="172" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizedClient-</text>
  <text x="330" y="186" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">Service</text>

  <rect x="460" y="152" width="150" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="535" y="172" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">backing store</text>
  <text x="535" y="186" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Map or JDBC table</text>

  <line x1="425" y1="177" x2="455" y2="177" stroke="#79c0ff" stroke-width="2" marker-end="url(#a91)"/>

  <text x="330" y="230" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">keyed by (registrationId, principalName)</text>

  <defs><marker id="a91" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

The repository is the request-facing contract; it has no storage of its own and hands every call straight to the service, which is the actual keyed store.

## 5. Runnable example

The scenario: model `OAuth2AuthorizedClient` faithfully, build an in-memory `OAuth2AuthorizedClientService`, then a request-scoped `OAuth2AuthorizedClientRepository` that delegates to it, and finally handle token expiry so a stale-but-present authorized client is distinguished from a genuinely missing one.

### Level 1 — Basic

Model the token and a minimal service keyed by `(registrationId, principalName)`.

```java
import java.time.Instant;
import java.util.*;

public class AuthorizedClientLevel1 {
    record AccessToken(String value, Instant expiresAt) {}
    record AuthorizedClient(String registrationId, String principalName, AccessToken accessToken) {}

    // mirrors InMemoryOAuth2AuthorizedClientService -- a Map keyed by (registrationId, principalName)
    static class InMemoryAuthorizedClientService {
        private final Map<String, AuthorizedClient> store = new HashMap<>();

        private String key(String registrationId, String principalName) {
            return registrationId + "::" + principalName;
        }

        void save(AuthorizedClient client) {
            store.put(key(client.registrationId(), client.principalName()), client);
        }

        AuthorizedClient load(String registrationId, String principalName) {
            return store.get(key(registrationId, principalName)); // null if never authorized
        }
    }

    public static void main(String[] args) {
        InMemoryAuthorizedClientService service = new InMemoryAuthorizedClientService();

        AuthorizedClient alice = new AuthorizedClient("github", "alice",
                new AccessToken("tok-abc123", Instant.now().plusSeconds(3600)));
        service.save(alice);

        AuthorizedClient loaded = service.load("github", "alice");
        AuthorizedClient missing = service.load("github", "bob");

        System.out.println("alice's token: " + (loaded != null ? loaded.accessToken().value() : "none"));
        System.out.println("bob's token: " + (missing != null ? missing.accessToken().value() : "none"));
    }
}
```

**How to run:** save as `AuthorizedClientLevel1.java`, run `java AuthorizedClientLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's token: tok-abc123
bob's token: none
```

`InMemoryAuthorizedClientService` is a plain map keyed by a composite of provider id and username, exactly like the real `InMemoryOAuth2AuthorizedClientService` — alice, who was saved, is found; bob, who never authorized, correctly yields `null`.

### Level 2 — Intermediate

Add the request-scoped `OAuth2AuthorizedClientRepository`, which has no storage of its own and delegates every call to the service — mirroring `AuthenticatedPrincipalOAuth2AuthorizedClientRepository`.

```java
import java.time.Instant;
import java.util.*;

public class AuthorizedClientLevel2 {
    record AccessToken(String value, Instant expiresAt) {}
    record AuthorizedClient(String registrationId, String principalName, AccessToken accessToken) {}
    record FakeSession(String sessionId, String loggedInPrincipal) {} // stands in for HttpServletRequest's session

    static class InMemoryAuthorizedClientService {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient client) { store.put(key(client.registrationId(), client.principalName()), client); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    // mirrors AuthenticatedPrincipalOAuth2AuthorizedClientRepository -- NO storage of its own
    static class AuthorizedClientRepository {
        private final InMemoryAuthorizedClientService service;
        AuthorizedClientRepository(InMemoryAuthorizedClientService service) { this.service = service; }

        AuthorizedClient loadAuthorizedClient(String registrationId, FakeSession request) {
            if (request.loggedInPrincipal() == null) return null; // no one logged in on this request at all
            return service.load(registrationId, request.loggedInPrincipal());
        }

        void saveAuthorizedClient(AuthorizedClient client, FakeSession request) {
            service.save(client); // delegates straight through -- the repository itself stores nothing
        }
    }

    public static void main(String[] args) {
        InMemoryAuthorizedClientService service = new InMemoryAuthorizedClientService();
        AuthorizedClientRepository repository = new AuthorizedClientRepository(service);

        FakeSession aliceRequest = new FakeSession("sess-1", "alice");
        FakeSession anonymousRequest = new FakeSession("sess-2", null);

        // login completes -- the filter calls saveAuthorizedClient on the REPOSITORY, which delegates to the service
        repository.saveAuthorizedClient(
                new AuthorizedClient("github", "alice", new AccessToken("tok-abc123", Instant.now().plusSeconds(3600))),
                aliceRequest);

        AuthorizedClient forAlice = repository.loadAuthorizedClient("github", aliceRequest);
        AuthorizedClient forAnonymous = repository.loadAuthorizedClient("github", anonymousRequest);

        System.out.println("alice's request -> token: " + (forAlice != null ? forAlice.accessToken().value() : "none"));
        System.out.println("anonymous request -> token: " + (forAnonymous != null ? forAnonymous.accessToken().value() : "none"));
    }
}
```

**How to run:** save as `AuthorizedClientLevel2.java`, run `java AuthorizedClientLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's request -> token: tok-abc123
anonymous request -> token: none
```

What changed: a `AuthorizedClientRepository` now sits in front of the service, taking the current request (here, `FakeSession`) as a parameter on every call — it checks who is logged in on *this* request and looks up that principal's client via the service, but stores nothing itself. An anonymous request (no logged-in principal) correctly yields no authorized client, without the service ever being consulted.

### Level 3 — Advanced

Handle token expiry: an authorized client can be *present* in the service yet hold an expired access token, which callers must detect distinctly from "no authorized client at all," since the two cases require different handling (refresh versus re-login).

```java
import java.time.Instant;
import java.util.*;

public class AuthorizedClientLevel3 {
    record AccessToken(String value, Instant expiresAt) {
        boolean isExpired() { return Instant.now().isAfter(expiresAt); }
    }
    record RefreshToken(String value) {}
    record AuthorizedClient(String registrationId, String principalName, AccessToken accessToken, RefreshToken refreshToken) {}
    record FakeSession(String sessionId, String loggedInPrincipal) {}

    enum LookupResult { NO_PRINCIPAL, NEVER_AUTHORIZED, EXPIRED_NO_REFRESH, EXPIRED_HAS_REFRESH, VALID }

    static class InMemoryAuthorizedClientService {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient client) { store.put(key(client.registrationId(), client.principalName()), client); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    static class AuthorizedClientRepository {
        private final InMemoryAuthorizedClientService service;
        AuthorizedClientRepository(InMemoryAuthorizedClientService service) { this.service = service; }

        AuthorizedClient loadAuthorizedClient(String registrationId, FakeSession request) {
            if (request.loggedInPrincipal() == null) return null;
            return service.load(registrationId, request.loggedInPrincipal());
        }

        void saveAuthorizedClient(AuthorizedClient client, FakeSession request) { service.save(client); }
    }

    // classifies exactly what state the caller is in -- distinguishing "never authorized" from "expired"
    static LookupResult classify(AuthorizedClientRepository repository, String registrationId, FakeSession request) {
        if (request.loggedInPrincipal() == null) return LookupResult.NO_PRINCIPAL;
        AuthorizedClient client = repository.loadAuthorizedClient(registrationId, request);
        if (client == null) return LookupResult.NEVER_AUTHORIZED;
        if (!client.accessToken().isExpired()) return LookupResult.VALID;
        return client.refreshToken() != null ? LookupResult.EXPIRED_HAS_REFRESH : LookupResult.EXPIRED_NO_REFRESH;
    }

    public static void main(String[] args) {
        InMemoryAuthorizedClientService service = new InMemoryAuthorizedClientService();
        AuthorizedClientRepository repository = new AuthorizedClientRepository(service);

        FakeSession aliceRequest = new FakeSession("sess-1", "alice");
        FakeSession bobRequest = new FakeSession("sess-2", "bob");
        FakeSession carolRequest = new FakeSession("sess-3", "carol");

        // alice: valid, unexpired token
        repository.saveAuthorizedClient(
                new AuthorizedClient("github", "alice", new AccessToken("tok-alice", Instant.now().plusSeconds(3600)), null),
                aliceRequest);

        // bob: token already expired, but a refresh token IS present -- refreshable, not a re-login
        repository.saveAuthorizedClient(
                new AuthorizedClient("github", "bob", new AccessToken("tok-bob-old", Instant.now().minusSeconds(60)),
                        new RefreshToken("refresh-bob")),
                bobRequest);

        // carol: token expired, NO refresh token at all -- must re-login, no way to silently refresh
        repository.saveAuthorizedClient(
                new AuthorizedClient("github", "carol", new AccessToken("tok-carol-old", Instant.now().minusSeconds(60)), null),
                carolRequest);

        FakeSession daveRequest = new FakeSession("sess-4", "dave"); // never authorized at all

        System.out.println("alice: " + classify(repository, "github", aliceRequest));
        System.out.println("bob: " + classify(repository, "github", bobRequest));
        System.out.println("carol: " + classify(repository, "github", carolRequest));
        System.out.println("dave: " + classify(repository, "github", daveRequest));
    }
}
```

**How to run:** save as `AuthorizedClientLevel3.java`, run `java AuthorizedClientLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice: VALID
bob: EXPIRED_HAS_REFRESH
carol: EXPIRED_NO_REFRESH
dave: NEVER_AUTHORIZED
```

`classify` layers the expiry check on top of the repository lookup from Level 2: it first rules out the "no principal at all" and "never authorized" cases exactly as before, then, for a present client, checks `accessToken().isExpired()` and — if expired — whether a `refreshToken` exists to decide between `EXPIRED_HAS_REFRESH` (recoverable via a silent refresh, the subject of the next card) and `EXPIRED_NO_REFRESH` (nothing to do but send the user through the login flow again).

## 6. Walkthrough

Trace `classify(repository, "github", bobRequest)` from Level 3, where bob's saved authorized client has an access token that expired sixty seconds ago but does carry a refresh token.

**Example inbound request a controller might be handling at this moment:**
```
GET /api/repos HTTP/1.1
Host: myapp.example.com
Cookie: JSESSIONID=sess-2
```

1. The servlet container resolves the session cookie `JSESSIONID=sess-2` to bob's authenticated session — represented here by `bobRequest`, whose `loggedInPrincipal()` is `"bob"`.
2. `classify` first checks `request.loggedInPrincipal() == null` — it is `"bob"`, not `null`, so this returns `false` and execution continues past the `NO_PRINCIPAL` case.
3. `repository.loadAuthorizedClient("github", request)` is called. Inside, it re-checks `loggedInPrincipal() == null` (still false), then calls `service.load("github", "bob")`.
4. Inside `InMemoryAuthorizedClientService.load`, the composite key `"github::bob"` is computed and looked up in the backing `Map` — bob's `AuthorizedClient` (saved earlier in `main`) is found and returned up through the repository to `classify`.
5. Back in `classify`, `client == null` is `false` (a client was found), so the `NEVER_AUTHORIZED` branch is skipped.
6. `client.accessToken().isExpired()` is evaluated: inside `AccessToken.isExpired()`, `Instant.now().isAfter(expiresAt)` compares the current instant against bob's `expiresAt`, which was set to sixty seconds in the past — `isAfter` returns `true`, so `isExpired()` is `true`.
7. Since the token is expired, the `if (!client.accessToken().isExpired())` branch (which would return `VALID`) is skipped, and `classify` falls to the final line: `client.refreshToken() != null ? EXPIRED_HAS_REFRESH : EXPIRED_NO_REFRESH`.
8. Bob's client was saved with `new RefreshToken("refresh-bob")`, a non-null value, so the ternary evaluates to `EXPIRED_HAS_REFRESH`, and `classify` returns that.
9. In a real Spring Security application, this is precisely the state that triggers a silent, automatic refresh (card 0093's `OAuth2AuthorizedClientProvider` for the `refresh_token` grant) rather than redirecting bob to re-authenticate — once refreshed, the *new* access token would be saved back through the same repository/service pair, replacing bob's stored `AuthorizedClient` with one carrying a fresh `expiresAt`.

**What the eventual outbound call looks like once a valid token is in hand (whether bob's original token or a freshly refreshed one):**
```
GET /user/repos HTTP/1.1
Host: api.github.com
Authorization: Bearer tok-bob-old
Accept: application/vnd.github+json
```
```
HTTP/1.1 200 OK
Content-Type: application/json

[{"name":"my-repo","private":false}, ...]
```

10. If bob's token had instead had no refresh token (carol's case), the same trace up through step 6 would be identical, but step 8's ternary would yield `EXPIRED_NO_REFRESH` — the application's only correct move there is to discard the stale authorized client and send the user back through the authorization code flow from scratch (card 0090).

```
service.load("github","bob") -> AuthorizedClient(expiresAt = now-60s, refreshToken = "refresh-bob")
   isExpired() -> true
   refreshToken != null -> true
   -> EXPIRED_HAS_REFRESH  (refresh silently; do NOT force re-login)
```

## 7. Gotchas & takeaways

> **Gotcha:** `OAuth2AuthorizedClientRepository` is tied to the current `HttpServletRequest`/`HttpServletResponse` and, in the default implementation, ultimately backed by the `HttpSession` — code running outside a request (a `@Scheduled` job refreshing tokens overnight, a message-queue consumer) has no request to hand the repository, so it must talk to the `OAuth2AuthorizedClientService` directly instead; reaching for `@RegisteredOAuth2AuthorizedClient` or the repository interface from background code will not compile or will have nothing meaningful to operate on.

- `OAuth2AuthorizedClient` bundles a `ClientRegistration`, a `principalName`, an access token, and an optional refresh token — it is the per-user, per-provider runtime record, distinct from the static `ClientRegistration` config it references.
- `OAuth2AuthorizedClientRepository` is the per-request contract the login filter and `@RegisteredOAuth2AuthorizedClient` resolvers actually call; its default implementation holds no storage of its own and delegates every call to an `OAuth2AuthorizedClientService`.
- `OAuth2AuthorizedClientService` is the actual storage abstraction, keyed by `(registrationId, principalName)` with no notion of the current request at all — `InMemoryOAuth2AuthorizedClientService` (default, wiped on restart) or `JdbcOAuth2AuthorizedClientService` (persistent) are the two built-in choices.
- Custom persistence (Redis, a different table shape, encryption at rest) belongs in a custom `OAuth2AuthorizedClientService` implementation; a custom `OAuth2AuthorizedClientRepository` is for changing *how* the client is correlated to a request (a cookie instead of the session, for instance), not where it is ultimately stored.
- A present-but-expired `OAuth2AuthorizedClient` is a distinct state from no authorized client at all, and the presence of a refresh token determines whether that expiry is silently recoverable or requires sending the user through the login flow again — the next two cards build directly on this distinction.
