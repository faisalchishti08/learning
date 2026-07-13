---
card: spring-ldap
gi: 19
slug: connection-pooling-commons-pool2
title: "Connection pooling (commons-pool2)"
---

## 1. What it is

Modern Spring LDAP's connection pooling (introduced as `spring-ldap-pool2`, superseding an older `spring-ldap-pool` module) is built directly on Apache Commons Pool 2 — the same general-purpose object-pooling library used throughout the Spring ecosystem for pooling other kinds of expensive-to-create objects. `PooledContextSource` and its `PoolConfig` (already seen briefly in card 0003) are Spring LDAP's thin adapter layer over a genuine `GenericKeyedObjectPool<Object, Object>` from commons-pool2, configuring it specifically for pooling `DirContext` instances.

## 2. Why & when

Card 0003 covered *why* pooling matters for LDAP performance; this card is about the specific mechanism underneath — understanding that Spring LDAP's pooling isn't a bespoke, LDAP-only pooling implementation, but a configuration of the well-established, independently-tested commons-pool2 library. That matters practically: commons-pool2's own configuration knobs, terminology, and behavior (eviction policies, exhaustion behavior, keyed pooling by principal) apply directly, and its documentation and community knowledge transfer directly to tuning Spring LDAP's pool.

Reach for direct `commons-pool2`-level configuration understanding when:

- Tuning pool behavior beyond the basics already shown in card 0003 — for instance, configuring what happens when the pool is exhausted (`blockWhenExhausted`), or how eviction runs (`timeBetweenEvictionRuns`).
- Debugging pool behavior in production, where commons-pool2's own metrics and exceptions (`NoSuchElementException` when exhausted and not configured to block, for instance) are what actually surface.
- Migrating from the older `spring-ldap-pool` module, which used different configuration classes than the current `spring-ldap-pool2`-based approach.

## 3. Core concept

Think of commons-pool2 as the general-purpose engine under the hood, and Spring LDAP's `PooledContextSource`/`PoolConfig` as the dashboard and steering wheel built specifically for driving that engine toward one particular purpose: pooling `DirContext` objects, keyed by the exact bind principal used to create them (so a connection authenticated as one user is never handed out for another). The engine (commons-pool2) doesn't know or care that it's pooling LDAP connections specifically — it just pools "objects," created and destroyed via a factory, with configurable size and eviction behavior — but the dashboard (`PoolConfig`) translates LDAP-relevant concerns into the engine's general-purpose settings.

```java
PoolConfig poolConfig = new PoolConfig();
poolConfig.setMaxTotal(20);                 // commons-pool2: GenericKeyedObjectPoolConfig.maxTotal
poolConfig.setMaxTotalPerKey(10);            // commons-pool2: cap per distinct principal/credential key
poolConfig.setMinIdlePerKey(2);              // commons-pool2: keep at least this many idle per key
poolConfig.setBlockWhenExhausted(true);      // commons-pool2: block (rather than fail fast) when the pool is full
poolConfig.setMaxWaitMillis(5000);           // commons-pool2: how long to block before giving up
poolConfig.setTestOnBorrow(true);            // commons-pool2: validate before handing out
poolConfig.setTimeBetweenEvictionRunsMillis(30_000); // commons-pool2: background eviction cadence
```

Because connections are keyed by principal, an application binding as several different service accounts (a read-only account and an admin account, as in card 0002) effectively gets several independent sub-pools, each with its own `maxTotalPerKey` cap.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PooledContextSource and PoolConfig are a thin LDAP-specific layer over a general-purpose commons-pool2 GenericKeyedObjectPool">
  <rect x="20" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PooledContextSource</text>
  <text x="120" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ PoolConfig</text>

  <rect x="270" y="30" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">commons-pool2</text>
  <text x="380" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GenericKeyedObjectPool</text>

  <rect x="20" y="120" width="200" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="147" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">key: readonly-service</text>

  <rect x="270" y="120" width="220" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="380" y="147" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">key: admin</text>

  <line x1="120" y1="90" x2="380" y2="55" stroke="#3fb950" stroke-width="1.5" marker-end="url(#o1)"/>

  <defs>
    <marker id="o1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Each distinct bind principal (key) gets its own independently-capped sub-pool within the same underlying commons-pool2 instance.

## 5. Runnable example

The scenario: pooling two distinct service accounts used by the same application (read-only and admin, as introduced in card 0002), starting with default pool behavior, then tuning per-key limits, and finally handling pool exhaustion gracefully instead of blocking indefinitely.

### Level 1 — Basic

```java
// TwoAccountPoolDemo.java
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.pool2.factory.PoolConfig;
import org.springframework.ldap.pool2.factory.PooledContextSource;
import org.springframework.ldap.core.LdapTemplate;

public class TwoAccountPoolDemo {
    public static void main(String[] args) {
        LdapContextSource readOnly = new LdapContextSource();
        readOnly.setUrl("ldap://localhost:389");
        readOnly.setBase("dc=example,dc=com");
        readOnly.setUserDn("cn=readonly-service,dc=example,dc=com");
        readOnly.setPassword("readonlypass");
        readOnly.afterPropertiesSet();

        PoolConfig poolConfig = new PoolConfig(); // default settings from commons-pool2
        PooledContextSource pooled = new PooledContextSource(poolConfig);
        pooled.setContextSource(readOnly);

        LdapTemplate template = new LdapTemplate(pooled);
        template.search("ou=people", "(uid=jsmith)", (Object obj) -> obj);
        System.out.println("Search completed via pooled read-only context.");
    }
}
```

**How to run:** run against a reachable directory. Expected output: `Search completed via pooled read-only context.` — the pool is created with commons-pool2's own sensible defaults, transparently underneath `PooledContextSource`.

### Level 2 — Intermediate

An application binding as both a high-traffic read-only account and a rarely-used admin account benefits from different per-key limits — capping the admin account's pool small (since it's used sparingly) while giving the read-only account more headroom for concurrent search traffic.

```java
// TunedPerKeyPoolConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.pool2.factory.PoolConfig;
import org.springframework.ldap.pool2.factory.PooledContextSource;
import org.springframework.ldap.core.LdapTemplate;

@Configuration
public class TunedPerKeyPoolConfig {

    @Bean
    public PooledContextSource pooledContextSource() {
        LdapContextSource readOnly = new LdapContextSource();
        readOnly.setUrl("ldap://ldap.example.com:389");
        readOnly.setBase("dc=example,dc=com");
        readOnly.setUserDn("cn=readonly-service,dc=example,dc=com");
        readOnly.setPassword(System.getenv("LDAP_READONLY_PASSWORD"));
        readOnly.afterPropertiesSet();

        PoolConfig poolConfig = new PoolConfig();
        poolConfig.setMaxTotal(30);          // overall pool cap across all keys
        poolConfig.setMaxTotalPerKey(25);     // read-heavy account: generous per-key cap
        poolConfig.setMinIdlePerKey(3);       // keep a few warm connections ready for bursts
        poolConfig.setTestOnBorrow(true);

        PooledContextSource pooled = new PooledContextSource(poolConfig);
        pooled.setContextSource(readOnly);
        return pooled;
    }

    @Bean
    public LdapTemplate ldapTemplate(PooledContextSource pooledContextSource) {
        return new LdapTemplate(pooledContextSource);
    }
}
```

**How to run:** deploy under realistic concurrent read traffic. Expected result: the pool maintains up to 25 concurrently-active connections for the `readonly-service` key, with at least 3 kept idle and ready even during quiet periods (avoiding a cold-start cost on the next burst) — behavior directly attributable to commons-pool2's `maxTotalPerKey` and `minIdlePerKey` settings, exposed here through Spring LDAP's `PoolConfig`.

### Level 3 — Advanced

Under a genuine traffic spike exceeding the pool's configured capacity, the default blocking behavior (`blockWhenExhausted=true` with no `maxWaitMillis` set) can leave request threads waiting indefinitely for a connection that may never free up — a real risk of cascading thread exhaustion in the calling application. This level configures a bounded wait and handles the resulting exhaustion explicitly.

```java
// BoundedWaitPoolConfig.java
import org.springframework.ldap.pool2.factory.PoolConfig;
import org.springframework.ldap.pool2.factory.PooledContextSource;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.CommunicationException;

public class BoundedWaitPoolConfig {

    public static LdapTemplate buildTemplate() {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://ldap.example.com:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=readonly-service,dc=example,dc=com");
        cs.setPassword(System.getenv("LDAP_READONLY_PASSWORD"));
        cs.afterPropertiesSet();

        PoolConfig poolConfig = new PoolConfig();
        poolConfig.setMaxTotalPerKey(25);
        poolConfig.setBlockWhenExhausted(true);
        poolConfig.setMaxWaitMillis(2000); // give up after 2 seconds rather than waiting forever

        PooledContextSource pooled = new PooledContextSource(poolConfig);
        pooled.setContextSource(cs);
        return new LdapTemplate(pooled);
    }

    public static java.util.Optional<Object> safeSearch(LdapTemplate template, String uid) {
        try {
            return template.search("ou=people", "(uid=" + uid + ")", (Object obj) -> obj)
                .stream().findFirst();
        } catch (CommunicationException | org.springframework.ldap.NamingException e) {
            // Includes the case where waiting for a pooled connection timed out under a traffic spike.
            System.err.println("LDAP search unavailable (pool exhausted or unreachable): " + e.getMessage());
            return java.util.Optional.empty();
        }
    }
}
```

**How to run:** under a load test driving concurrency well beyond `maxTotalPerKey` (25), sustained for longer than the 2-second `maxWaitMillis`, call `safeSearch` repeatedly. Expected behavior: once every pooled connection is in active use, subsequent callers wait up to 2 seconds for one to free up rather than indefinitely, and if none does within that window, a caught exception routes them to a graceful `Optional.empty()` response instead of an indefinitely blocked thread — protecting the calling application's own thread pool from being exhausted by LDAP contention.

## 6. Walkthrough

Tracing `safeSearch` when the pool is fully exhausted and no connection frees up within the wait window, in execution order:

1. `template.search(...)` is called; internally, `LdapTemplate` asks `PooledContextSource` for a `DirContext` under the `readonly-service` key.
2. The underlying commons-pool2 `GenericKeyedObjectPool` checks its `readonly-service` sub-pool: all 25 permitted connections are currently checked out to other concurrent requests, and none are idle.
3. Because `blockWhenExhausted` is `true`, the borrowing call blocks rather than failing immediately — but because `maxWaitMillis` is set to 2000, it only blocks for up to 2 seconds waiting for another thread to return a connection.
4. If no connection is returned within that window (the traffic spike is sustained enough that every connection stays busy), commons-pool2's borrow operation gives up and throws (surfaced through Spring LDAP's exception translation as a `NamingException`/`CommunicationException`-family exception).
5. This propagates out of `template.search(...)` and is caught by `safeSearch`'s `catch` block, which logs a diagnostic and returns `Optional.empty()` rather than letting the calling thread hang indefinitely or crash uninformatively.
6. Meanwhile, other concurrently-executing requests that *did* successfully borrow a connection continue processing and eventually return their connections to the pool, at which point subsequently-blocked borrow attempts (within their own wait windows) can succeed.

```
25 connections all checked out (readonly-service key), traffic spike sustained > 2s
  safeSearch() -> template.search() -> pool.borrow(key="readonly-service")
    blockWhenExhausted=true, maxWaitMillis=2000 -> waits up to 2s
    no connection freed in time -> pool throws
  -> caught in safeSearch -> log -> return Optional.empty()
```

## 7. Gotchas & takeaways

> Leaving `blockWhenExhausted=true` with no `maxWaitMillis` configured (an unbounded wait) means a sustained traffic spike against a saturated pool can leave calling threads blocked indefinitely, which in turn can exhaust the calling application's *own* thread pool (a web server's request-handling threads, for instance) — a pool exhaustion problem in one system cascading into a thread exhaustion problem in another. Always set a bounded `maxWaitMillis` for anything handling real production traffic.

- Spring LDAP's connection pooling is a configuration layer over Apache Commons Pool 2's `GenericKeyedObjectPool` — commons-pool2's own concepts (keyed pooling, eviction, exhaustion behavior) apply directly and are worth understanding on their own terms, not just through Spring LDAP's `PoolConfig` wrapper.
- Connections are pooled per distinct bind principal (key) — an application using multiple service accounts (card 0002) effectively gets multiple independently-sized sub-pools within one overall pool.
- `maxTotalPerKey` and `minIdlePerKey` let per-account traffic patterns (a high-volume read-only account versus a rarely-used admin account) be tuned independently rather than sharing one blanket pool-size setting.
- Always configure a bounded `maxWaitMillis` alongside `blockWhenExhausted=true` for production traffic, and handle the resulting exhaustion exception explicitly, rather than leaving borrow calls able to block indefinitely.
- If migrating from the older `spring-ldap-pool` module, note that the current `spring-ldap-pool2`-based `PooledContextSource`/`PoolConfig` classes are different types with a different configuration surface — this isn't a drop-in rename, and configuration needs to be rewritten against the new API, not merely renamed.
