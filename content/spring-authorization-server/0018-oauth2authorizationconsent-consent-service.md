---
card: spring-authorization-server
gi: 18
slug: oauth2authorizationconsent-consent-service
title: "OAuth2AuthorizationConsent & consent service"
---

## 1. What it is

`OAuth2AuthorizationConsent` is a small, separate record of exactly which scopes a specific user has approved for a specific client — distinct from `OAuth2Authorization`, which represents one grant in progress. It's keyed by the pair (registered client ID, principal name), and it's what lets the server remember, across many separate logins over time, "this user already agreed that this client can read their tasks" — so it doesn't have to ask again every single time. `OAuth2AuthorizationConsentService` is the storage interface for it, with `InMemoryOAuth2AuthorizationConsentService` and `JdbcOAuth2AuthorizationConsentService` implementations, mirroring the pattern of the previous two cards.

## 2. Why & when

Without a persisted consent record, every single authorization code request — even from the same user, to the same client, for the same scopes they approved five minutes ago — would have to show a consent screen again, which is both a poor user experience and, done often enough, trains users to click "approve" without reading anything, defeating the point of consent entirely. `OAuth2AuthorizationConsent` exists so consent is asked once and remembered, while still being re-askable the moment the client requests a *new* scope the user hasn't seen before.

Reach for understanding and configuring this whenever:

- A `RegisteredClient` has `requireAuthorizationConsent(true)` (card 0013) and you need to know why users are, or aren't, being re-prompted.
- Building an account settings page where users can review and revoke consent they've previously granted to third-party applications — this is exactly the data such a page would read and delete from.
- Debugging a flow where a user approved `tasks.read` previously, the client later starts requesting `tasks.write` too, and you need to understand why the consent screen reappears (it should — new scope, new consent needed).

## 3. Core concept

Think of `OAuth2AuthorizationConsent` as a signed permission slip filed at the front desk, separate from any individual visit's paperwork. Each time this specific visitor (user) tries to bring in this specific guest (client) again, the desk checks the filed slip: if the guest is only asking to access rooms already listed on the slip, no new signature needed — just let them through directly. If the guest suddenly wants to enter a room not listed on the slip, the desk pulls out a fresh slip for the visitor to sign, adding the new room to what's now approved for next time.

```java
public class OAuth2AuthorizationConsent implements Serializable {
    String getRegisteredClientId();
    String getPrincipalName();
    Set<GrantedAuthority> getAuthorities(); // scopes, prefixed as SCOPE_xxx authorities
}

public interface OAuth2AuthorizationConsentService {
    void save(OAuth2AuthorizationConsent authorizationConsent);
    void remove(OAuth2AuthorizationConsent authorizationConsent);
    OAuth2AuthorizationConsent findById(String registeredClientId, String principalName);
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Consent lookup determines whether the consent screen is shown or skipped">
  <rect x="20" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Request: scope=tasks.read</text>

  <rect x="270" y="20" width="340" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">findById(clientId, "alice")</text>

  <rect x="20" y="120" width="270" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="155" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">requested scopes subset of</text>
  <text x="155" y="163" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">stored consent -&gt; skip screen</text>

  <rect x="330" y="120" width="280" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="470" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">new scope not previously</text>
  <text x="470" y="163" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">consented -&gt; show consent screen</text>

  <line x1="440" y1="70" x2="155" y2="118" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="440" y1="70" x2="470" y2="118" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The same lookup branches to two very different user experiences depending on what's already on file.

## 5. Runnable example

The scenario: alice approves `tasks.read` for task-tracker once; later requests reuse that consent, and finally the client starts asking for an additional scope, which forces a new consent screen.

### Level 1 — Basic

```java
// ConsentDemo.java
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.server.authorization.InMemoryOAuth2AuthorizationConsentService;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsent;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsentService;

public class ConsentDemo {
    public static void main(String[] args) {
        OAuth2AuthorizationConsentService consentService = new InMemoryOAuth2AuthorizationConsentService();

        OAuth2AuthorizationConsent consent = OAuth2AuthorizationConsent
                .withId("task-tracker-client-id", "alice")
                .authority(new SimpleGrantedAuthority("SCOPE_tasks.read"))
                .build();

        consentService.save(consent);

        OAuth2AuthorizationConsent found = consentService.findById("task-tracker-client-id", "alice");
        System.out.println("Consented scopes: " + found.getScopes());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java ConsentDemo.java`. Expected output:

```
Consented scopes: [tasks.read]
```

### Level 2 — Intermediate

A subsequent authorization request for the same, already-consented scope should skip the consent screen entirely — the server checks this by comparing requested scopes against the stored consent before deciding whether to render the page at all.

```java
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.server.authorization.InMemoryOAuth2AuthorizationConsentService;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsent;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsentService;

import java.util.Set;

public class ConsentDemo {

    static boolean needsConsentScreen(OAuth2AuthorizationConsentService service,
                                       String clientId, String principal, Set<String> requestedScopes) {
        OAuth2AuthorizationConsent existing = service.findById(clientId, principal);
        if (existing == null) {
            return true; // never consented before -> must ask
        }
        // needs a new screen only if requesting a scope not already on file
        return !existing.getScopes().containsAll(requestedScopes);
    }

    public static void main(String[] args) {
        OAuth2AuthorizationConsentService consentService = new InMemoryOAuth2AuthorizationConsentService();
        consentService.save(OAuth2AuthorizationConsent.withId("task-tracker-client-id", "alice")
                .authority(new SimpleGrantedAuthority("SCOPE_tasks.read"))
                .build());

        System.out.println("Needs consent for [tasks.read]: "
                + needsConsentScreen(consentService, "task-tracker-client-id", "alice", Set.of("tasks.read")));
        System.out.println("Needs consent for [tasks.read, tasks.write]: "
                + needsConsentScreen(consentService, "task-tracker-client-id", "alice", Set.of("tasks.read", "tasks.write")));
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Needs consent for [tasks.read]: false
Needs consent for [tasks.read, tasks.write]: true
```

What changed: the logic now distinguishes "same scopes as before" (skip the screen, proceed straight to issuing a code) from "a new scope appeared" (show the screen again) — this is exactly the check Spring Authorization Server's built-in consent page controller performs before rendering anything.

### Level 3 — Advanced

Production persists consent in a real database (surviving restarts and shared across instances) and supports revocation — a user-facing "connected apps" settings page needs to list and delete consent records, which requires a real, queryable store rather than an in-memory map.

```java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.server.authorization.JdbcOAuth2AuthorizationConsentService;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationConsent;
import org.springframework.security.oauth2.server.authorization.client.InMemoryRegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;

import javax.sql.DataSource;
import java.util.UUID;

public class ConsentDemo {
    public static void main(String[] args) {
        DataSource dataSource = new EmbeddedDatabaseBuilder()
                .setType(EmbeddedDatabaseType.H2)
                .addScript("org/springframework/security/oauth2/server/authorization/client/oauth2-registered-client-schema.sql")
                .addScript("org/springframework/security/oauth2/server/authorization/oauth2-authorization-consent-schema.sql")
                .build();

        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .build();
        var clientRepository = new InMemoryRegisteredClientRepository(client);

        JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);
        JdbcOAuth2AuthorizationConsentService consentService =
                new JdbcOAuth2AuthorizationConsentService(jdbcTemplate, clientRepository);

        OAuth2AuthorizationConsent consent = OAuth2AuthorizationConsent
                .withId(client.getId(), "alice")
                .authority(new SimpleGrantedAuthority("SCOPE_tasks.read"))
                .build();
        consentService.save(consent);

        // "connected apps" page: user revokes access
        OAuth2AuthorizationConsent found = consentService.findById(client.getId(), "alice");
        consentService.remove(found);

        System.out.println("Consent after revoke: " + consentService.findById(client.getId(), "alice"));
    }
}
```

**How to run:** add H2 and `spring-jdbc` to the classpath; run the same way. Expected output:

```
Consent after revoke: null
```

What changed and why it's production-flavored: revocation is a first-class, user-facing operation — real applications need it for account settings pages and compliance ("let me see and remove what I've authorized"), and `JdbcOAuth2AuthorizationConsentService`'s `remove` makes it a straightforward, queryable database delete rather than something requiring server restart or manual data surgery.

## 6. Walkthrough

Tracing the built-in consent page flow end to end, in execution order:

1. `GET /oauth2/authorize?client_id=task-tracker&scope=tasks.read tasks.write&...` arrives from a client whose `ClientSettings.isRequireAuthorizationConsent()` is true.
2. After the user authenticates, the server calls `consentService.findById(client.getId(), "alice")`.
3. Say alice previously consented only to `tasks.read` (Level 1's state) — the server compares the requested scopes `{tasks.read, tasks.write}` against the stored `{tasks.read}` and finds `tasks.write` is new (Level 2's `needsConsentScreen` logic), so it renders the built-in consent page listing both scopes, with `tasks.write` visibly new.
4. Alice reviews and clicks approve; the browser submits `POST /oauth2/authorize` with the approved scopes as form parameters.
5. The server saves an **updated** `OAuth2AuthorizationConsent` covering `{tasks.read, tasks.write}` — replacing, not appending to, the old record — so future requests for either scope skip the screen.
6. The server proceeds to generate the authorization code and redirect back to the client, exactly as in a request that never needed a consent screen at all — from this point on, the flow is identical to card 0016's walkthrough.
7. Months later, if alice visits a "connected apps" settings page and clicks "revoke access" for task-tracker, that page calls `consentService.remove(...)` (Level 3) — the *next* authorization request from task-tracker will find no consent record at all and show the full consent screen again, exactly as if alice were authorizing it for the first time.

```
authorize request (scope=read,write)
   |
findById(client, "alice") --found, only "read" on file--> "write" is new
   |
render consent page (read already-approved, write new)
   |
approve --> save updated consent {read, write} --> continue to issue code
```

## 7. Gotchas & takeaways

> Saving an updated consent must **replace** the scope set, not merge indefinitely without limit — if a user later un-checks a scope on the consent screen (many UIs allow selective approval), the new saved consent should reflect exactly what was approved *this time*, not the union of ever-approved scopes, or a user could never truly narrow what they've granted.

- `OAuth2AuthorizationConsent` is keyed by (client, principal) — it has nothing to do with any particular grant's tokens; don't confuse it with `OAuth2Authorization`, which is per-grant and holds the actual tokens.
- If `ClientSettings.isRequireAuthorizationConsent()` is false, this entire mechanism is bypassed — the server never checks or stores consent for that client at all, appropriate only for fully trusted first-party clients.
- A consent record with zero scopes after a revocation should be deleted outright (via `remove`), not saved as an empty consent — an empty-but-present record can confuse code that only checks "does a consent record exist" rather than "are there any approved scopes."
- Building a user-facing consent-management page is a real, common production need — it's a straightforward `findById` (or a custom `findAllByPrincipal`-style query against the JDBC table) plus `remove`, not something requiring custom protocol work.
- Test the "new scope added later" path explicitly — it's the easiest part of consent handling to get wrong, either by never re-prompting (over-trusting) or by always re-prompting even for previously-approved scopes (annoying users unnecessarily).
