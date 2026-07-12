---
card: spring-authorization-server
gi: 11
slug: registeredclientrepository-in-memory-jdbc
title: "RegisteredClientRepository (in-memory & JDBC)"
---

## 1. What it is

`RegisteredClientRepository` is the interface the authorization server uses to look up `RegisteredClient` objects by client ID (or internal ID). It has exactly two read methods — `findByClientId(String)` and `findById(String)` — plus a `save(RegisteredClient)` method, and it's the single seam between "the server knows about clients" and "where those clients actually live." Spring Authorization Server ships two ready-made implementations: `InMemoryRegisteredClientRepository`, which holds clients in a `Map` for demos and tests, and `JdbcRegisteredClientRepository`, which persists them in a relational database table.

## 2. Why & when

Every request that arrives at the authorization or token endpoint needs to answer "is this a real, registered client, and what is it allowed to do?" — and that answer has to come from *somewhere*. The repository abstraction exists so the rest of the server never cares whether that somewhere is a hardcoded list, a SQL table, or (in a custom implementation) a call to another microservice; it only ever calls `findByClientId`.

Reach for the in-memory implementation when:

- Writing a demo, a tutorial, or a test where clients are fixed and few.
- Prototyping a new authorization server before deciding on a persistence strategy.

Reach for the JDBC implementation (or a custom one) when:

- Clients are created and edited by administrators through a UI or API at runtime, without redeploying the server.
- The number of clients is large, changes over time, or must survive a server restart.
- You're running multiple authorization server instances behind a load balancer — they all need to see the same client data.

## 3. Core concept

Picture a hotel's guest registry. `RegisteredClientRepository` is the front desk's lookup system — it doesn't matter to the receptionist whether guest records are on index cards in a box (in-memory) or in a computer database (JDBC); the receptionist always asks the same question ("do we have a reservation for this name?") and gets back the same kind of answer. The authorization server is the receptionist: it always calls `repository.findByClientId(clientId)`, and the implementation behind that call decides where the lookup actually happens.

```java
public interface RegisteredClientRepository {
    void save(RegisteredClient registeredClient);
    RegisteredClient findById(String id);
    RegisteredClient findByClientId(String clientId);
}
```

`JdbcRegisteredClientRepository` implements this by serializing the non-primitive fields of `RegisteredClient` (its settings maps) to JSON and storing them in an `oauth2_registered_client` table, using a `JdbcTemplate` under the hood — the same pattern Spring Security uses elsewhere for JDBC-backed persistence.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Authorization server calls RegisteredClientRepository which is backed by memory or a database">
  <rect x="20" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="106" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Authorization</text>
  <text x="105" y="122" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Server</text>

  <rect x="240" y="80" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="106" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">RegisteredClientRepository</text>
  <text x="350" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">findByClientId(id)</text>

  <rect x="510" y="20" width="110" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">In-memory Map</text>

  <rect x="510" y="150" width="110" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="178" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JDBC table</text>

  <line x1="190" y1="105" x2="235" y2="105" stroke="#3fb950" stroke-width="2"/>
  <line x1="460" y1="95" x2="505" y2="55" stroke="#3fb950" stroke-width="2"/>
  <line x1="460" y1="115" x2="505" y2="165" stroke="#3fb950" stroke-width="2"/>
</svg>

Same interface call, two interchangeable storage backends behind it.

## 5. Runnable example

The scenario: registering a client and looking it up by ID, growing from a hardcoded in-memory list to a JDBC-backed store initialized from `schema.sql`.

### Level 1 — Basic

```java
// RepoDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.InMemoryRegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;

import java.util.UUID;

public class RepoDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("http://127.0.0.1:8080/login/oauth2/code/task-tracker")
                .scope("read")
                .build();

        RegisteredClientRepository repository = new InMemoryRegisteredClientRepository(client);

        RegisteredClient found = repository.findByClientId("task-tracker");
        System.out.println("Found: " + found.getClientId());
    }
}
```

**How to run:** run inside a Spring Boot project with `spring-security-oauth2-authorization-server` on the classpath, `java RepoDemo.java`-style via a build tool. Expected output:

```
Found: task-tracker
```

### Level 2 — Intermediate

A real server needs more than one client, and needs to add clients without restarting — so we swap the fixed in-memory repository for `JdbcRegisteredClientRepository`, backed by the library's ready-made schema.

```java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.JdbcRegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import javax.sql.DataSource;
import java.util.UUID;

public class RepoDemo {
    public static void main(String[] args) {
        // spring-security-oauth2-authorization-server ships oauth2-registered-client-schema.sql
        DataSource dataSource = new EmbeddedDatabaseBuilder()
                .setType(EmbeddedDatabaseType.H2)
                .addScript("org/springframework/security/oauth2/server/authorization/client/oauth2-registered-client-schema.sql")
                .build();

        JdbcRegisteredClientRepository repository =
                new JdbcRegisteredClientRepository(new JdbcTemplate(dataSource));

        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("http://127.0.0.1:8080/login/oauth2/code/task-tracker")
                .scope("read")
                .scope("write")
                .build();

        repository.save(client);

        RegisteredClient found = repository.findByClientId("task-tracker");
        System.out.println("Persisted and reloaded: " + found.getClientId() + ", scopes=" + found.getScopes());
    }
}
```

**How to run:** add `com.h2database:h2` and `org.springframework:spring-jdbc` to the classpath; run the same way as Level 1. Expected output:

```
Persisted and reloaded: task-tracker, scopes=[read, write]
```

What changed: clients now live in a real SQL table (`oauth2_registered_client`), so `save` persists across a server restart, and an admin API could call `save` at runtime to add a new client without redeploying anything.

### Level 3 — Advanced

Production wraps the raw `JdbcRegisteredClientRepository` with caching (lookups happen on nearly every request) and a custom `RegisteredClientRepository` decorator that adds read-through caching and cache invalidation on save — handling the hard case of high-traffic lookups without hammering the database.

```java
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class CachingRegisteredClientRepository implements RegisteredClientRepository {

    private final RegisteredClientRepository delegate; // e.g. JdbcRegisteredClientRepository
    private final Map<String, RegisteredClient> byClientId = new ConcurrentHashMap<>();

    public CachingRegisteredClientRepository(RegisteredClientRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public void save(RegisteredClient registeredClient) {
        delegate.save(registeredClient);
        // invalidate rather than update, to avoid caching a stale write
        byClientId.remove(registeredClient.getClientId());
    }

    @Override
    public RegisteredClient findById(String id) {
        return delegate.findById(id); // rarely on the hot path; skip caching
    }

    @Override
    public RegisteredClient findByClientId(String clientId) {
        return byClientId.computeIfAbsent(clientId, delegate::findByClientId);
    }
}
```

**How to run:** wire this bean around a `JdbcRegisteredClientRepository` in a Spring Boot application context; every call to `findByClientId` for a given client hits the database only once, then serves from memory. Expected behavior when tested with a JUnit assertion calling `findByClientId` twice: the second call returns the cached instance without a new SQL query (verifiable by logging JDBC queries or asserting reference equality).

What changed and why it's production-flavored: the token endpoint calls `findByClientId` on essentially every request, so an uncached JDBC round trip per request is real, avoidable latency. Caching reads while invalidating on write (rather than updating the cache in place) keeps the cache correct even if `save` is called concurrently from an admin console.

## 6. Walkthrough

Tracing a real token request through the Level 3 repository, in execution order:

1. A client sends `POST /oauth2/token` with `Authorization: Basic base64(task-tracker:secret)` and `grant_type=authorization_code&code=...&redirect_uri=...`.
2. Spring Authorization Server's client authentication filter extracts `task-tracker` from the Basic auth header and calls `registeredClientRepository.findByClientId("task-tracker")`.
3. In `CachingRegisteredClientRepository`, `computeIfAbsent` checks the `ConcurrentHashMap` first — on a cache hit, the `RegisteredClient` object is returned immediately with zero database access.
4. On a cache miss (first request for this client, or after the cache was invalidated), `delegate.findByClientId` runs, which is `JdbcRegisteredClientRepository` issuing a `SELECT` against `oauth2_registered_client`, deserializing the stored JSON settings back into a `RegisteredClient`, and the result is cached for next time.
5. The filter now has the real `RegisteredClient` and checks the supplied secret against `client.getClientSecret()` using the configured password encoder.
6. If authentication succeeds, downstream processing (grant validation, token generation) proceeds using the same `RegisteredClient` object — every check from here on reads from the object this repository handed back.

```
POST /oauth2/token (Basic auth: task-tracker)
        |
        v
findByClientId("task-tracker") --cache hit--> RegisteredClient (fast path)
        |
     cache miss
        v
JdbcRegisteredClientRepository --SQL SELECT--> oauth2_registered_client table
        |
        v
   deserialize JSON settings --> RegisteredClient --> cache it --> return
```

## 7. Gotchas & takeaways

> `JdbcRegisteredClientRepository` requires the client secret to already be encoded (e.g. via `PasswordEncoderFactories.createDelegatingPasswordEncoder()`) before calling `save` — it does not hash it for you. Saving a plaintext secret to the database is a real, silent security hole.

- `InMemoryRegisteredClientRepository` is not thread-safe for mutation after construction in older versions — treat it as read-mostly and built once at startup for anything beyond a demo.
- The JDBC schema (`oauth2-registered-client-schema.sql`) ships inside the `spring-security-oauth2-authorization-server` jar; you run it once against your database, you don't hand-write the table.
- A custom `RegisteredClientRepository` is the standard extension point for backing clients with a different store (a document database, an admin microservice) — implement the three methods and register it as a `@Bean`.
- Caching client lookups is a real optimization worth making once traffic is non-trivial, since every token request performs at least one lookup — but always invalidate (don't just overwrite) the cache entry on `save` to avoid serving stale settings.
