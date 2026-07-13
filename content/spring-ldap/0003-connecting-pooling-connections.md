---
card: spring-ldap
gi: 3
slug: connecting-pooling-connections
title: "Connecting & pooling connections"
---

## 1. What it is

Connection pooling for LDAP means reusing already-open, already-authenticated `DirContext` connections across multiple operations instead of opening a brand-new network connection and re-authenticating (a full TCP handshake plus an LDAP bind) for every single search or update. Spring LDAP integrates with the `commons-pool`-based pooling built into its own `spring-ldap-core` module (via `PooledContextSource`/`pooled` configuration on `LdapContextSource`), so pooling can be turned on with a handful of configuration properties rather than custom connection-management code.

## 2. Why & when

Opening an LDAP connection is not free: it involves a TCP connect, often a TLS handshake if using `ldaps://`, and then an LDAP `bind` operation to authenticate. For an application performing dozens or hundreds of directory operations per second (a login-heavy service checking credentials against LDAP on every request, for instance), paying that full cost on every single operation adds latency and load on both the client and the directory server that pure computation can't fix — the fix is architectural: keep a small set of already-authenticated connections open and hand them out for reuse.

Enable pooling when:

- The application performs LDAP operations frequently (many requests per second), such as an authentication filter checking every login against a directory.
- Connection setup latency (TLS handshake, bind round-trip) is measurable relative to the actual operation cost — which is nearly always true for LDAP, since the operation itself (a simple search) is often cheaper than establishing the connection.
- The directory server has a connection limit and unpooled connections would create and tear down connections faster than the server (or an intermediate load balancer) can comfortably handle.

Skip pooling for infrequent, one-off administrative scripts where the setup cost of a single connection is irrelevant relative to the human time already being spent.

## 3. Core concept

Think of an unpooled connection like calling a locksmith to cut a brand-new key every single time you want to open your own front door, then throwing the key away the moment you're back inside. It works, but it's wasteful — cutting a key (the network handshake plus authentication) takes real time and effort that's completely unnecessary if you're going to need to open the same door again five seconds later. Pooling is keeping a small ring of pre-cut keys near the door: when you need to go in, you grab an available key from the ring, use it, and put it back for the next person (or yourself) to use, only cutting a new key if every key on the ring happens to be in use already.

Spring LDAP's pooling operates at two related layers:

- **`LdapContextSource.setPooled(true)`** — a simple switch enabling connection pooling for contexts obtained from this source, using default pool settings.
- **`PoolingContextSource`** (or the pooling support configured via `spring-ldap-core`'s pool package) — gives finer control: maximum active connections, maximum idle connections, what to do when the pool is exhausted (block, fail, grow), and how to validate a pooled connection is still alive before handing it out.

Underneath, the pool tracks connections by the exact combination of principal (bind DN) and credentials used, since a connection authenticated as one user cannot be silently handed to code expecting to act as another.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A pool holds several already-authenticated DirContext connections; operations borrow one, use it, and return it instead of opening a new connection each time">
  <rect x="30" y="70" width="150" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Connection pool</text>
  <text x="105" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ctx1 ctx2 ctx3</text>
  <text x="105" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(idle, authenticated)</text>

  <rect x="260" y="30" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Request A: borrow</text>

  <rect x="260" y="140" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="170" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Request B: borrow</text>

  <rect x="480" y="85" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">LDAP server</text>

  <line x1="180" y1="90" x2="255" y2="55" stroke="#3fb950" stroke-width="1.5" marker-end="url(#c1)"/>
  <line x1="180" y1="120" x2="255" y2="165" stroke="#3fb950" stroke-width="1.5" marker-end="url(#c2)"/>
  <line x1="400" y1="55" x2="475" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#c3)"/>
  <line x1="400" y1="165" x2="475" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#c4)"/>

  <defs>
    <marker id="c1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="c2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="c3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Two concurrent requests borrow already-open connections from the pool instead of each paying the full connect-and-authenticate cost.

## 5. Runnable example

The scenario: an authentication service that validates user credentials against LDAP on every login attempt, starting unpooled and evolving to a tuned, monitored pool under concurrent load.

### Level 1 — Basic

```java
// UnpooledAuthCheck.java
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.AuthenticationException;

public class UnpooledAuthCheck {
    public static void main(String[] args) {
        LdapContextSource contextSource = new LdapContextSource();
        contextSource.setUrl("ldap://localhost:389");
        contextSource.setBase("dc=example,dc=com");
        contextSource.setUserDn("cn=admin,dc=example,dc=com");
        contextSource.setPassword("adminpass");
        contextSource.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(contextSource);

        // Every call to authenticate() opens a fresh connection under the hood by default.
        boolean ok = template.authenticate("ou=people", "(uid=jsmith)", "userSecret123");
        System.out.println("Authenticated: " + ok);
    }
}
```

**How to run:** run against a seeded LDAP server with `uid=jsmith` whose password is `userSecret123`. Expected output: `Authenticated: true`. Run it a hundred times in a loop and each call independently opens and closes a connection — measurable, if small, overhead per call.

### Level 2 — Intermediate

Enabling pooling with `setPooled(true)` lets connections be reused across calls, avoiding the repeated connect-and-bind cost under load.

```java
// PooledAuthCheck.java
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.LdapTemplate;

public class PooledAuthCheck {
    public static void main(String[] args) {
        LdapContextSource contextSource = new LdapContextSource();
        contextSource.setUrl("ldap://localhost:389");
        contextSource.setBase("dc=example,dc=com");
        contextSource.setUserDn("cn=admin,dc=example,dc=com");
        contextSource.setPassword("adminpass");
        contextSource.setPooled(true); // enables pooling with default pool settings
        contextSource.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(contextSource);

        long start = System.nanoTime();
        for (int i = 0; i < 100; i++) {
            template.authenticate("ou=people", "(uid=jsmith)", "userSecret123");
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("100 authenticate() calls took " + elapsedMs + " ms");
    }
}
```

**How to run:** run this alongside a copy of Level 1 modified to loop 100 times. Expected result: the pooled version noticeably outperforms the unpooled version under the same 100-call loop, because most calls reuse an already-open connection instead of paying full connect-and-bind cost each time — the exact improvement depends on network latency to the LDAP server.

### Level 3 — Advanced

Default pool sizing may not fit a specific traffic pattern, and a pool that silently hands out a connection that the server has since dropped (an idle timeout on the server side) causes confusing failures. This level tunes pool bounds and adds validation so stale connections are detected before being handed to a caller.

```java
// TunedPoolConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.pool2.factory.PoolConfig;
import org.springframework.ldap.pool2.factory.PooledContextSource;

@Configuration
public class TunedPoolConfig {

    @Bean
    public LdapContextSource contextSource() {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://ldap.example.com:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=readonly-service,dc=example,dc=com");
        cs.setPassword(System.getenv("LDAP_READONLY_PASSWORD"));
        return cs;
    }

    @Bean
    public PooledContextSource pooledContextSource(LdapContextSource contextSource) {
        PoolConfig poolConfig = new PoolConfig();
        poolConfig.setMaxTotal(20);        // hard cap: never more than 20 concurrent connections
        poolConfig.setMaxIdlePerPartition(5); // don't hoard idle connections beyond expected steady load
        poolConfig.setTestOnBorrow(true);  // validate a connection is alive before handing it out
        poolConfig.setMinEvictableIdleTimeMillis(60_000); // recycle long-idle connections

        PooledContextSource pooled = new PooledContextSource(poolConfig);
        pooled.setContextSource(contextSource);
        return pooled;
    }

    @Bean
    public LdapTemplate ldapTemplate(PooledContextSource pooledContextSource) {
        return new LdapTemplate(pooledContextSource);
    }
}
```

**How to run:** deploy behind a load test hitting the authentication endpoint at a realistic concurrency (say, 20 concurrent requests). Expected behavior: the pool caps outstanding connections at 20 rather than opening unbounded connections under a traffic spike, `testOnBorrow` catches and silently replaces any connection the LDAP server has already closed on its side (e.g. after its own idle timeout) before it's handed to a real request, and `minEvictableIdleTimeMillis` prevents connections from sitting open indefinitely during quiet periods.

## 6. Walkthrough

Tracing one `authenticate()` call under the tuned pool configuration, in execution order:

1. A login request arrives at the application and calls `ldapTemplate.authenticate(...)`.
2. `LdapTemplate` asks `PooledContextSource` for a `DirContext`, rather than asking `LdapContextSource` directly.
3. `PooledContextSource` checks its pool: if an idle, already-authenticated connection is available, `testOnBorrow` first validates it's still usable (a lightweight check against the server) before handing it out — this is the step that prevents a silently-dead connection from causing a failed request.
4. If validation fails (the server had already closed that connection), the pool discards it and either creates a new one or borrows another idle connection, transparently to the caller.
5. If no idle connection is available at all and the pool is below `maxTotal` (20), a new connection is created; if the pool is already at 20 active connections, the borrow blocks (or fails, depending on configured exhausted-pool behavior) until one is returned.
6. The borrowed `DirContext` performs the actual bind-based authentication check against `uid=jsmith`'s entry.
7. Once the operation completes, the connection is returned to the pool rather than closed — it becomes available for the next borrow instead of being torn down.
8. Periodically, a background eviction thread checks for connections that have been idle longer than `minEvictableIdleTimeMillis` (60 seconds) and closes them, keeping the pool from holding stale connections open indefinitely during quiet traffic.

```
login request -> authenticate() -> PooledContextSource.borrow()
   idle conn available? -> testOnBorrow validates -> valid: reuse | invalid: discard, get another
   no idle conn, pool < maxTotal -> create new connection
   pool == maxTotal -> block until one is returned
-> perform bind check -> return connection to pool (not closed)
```

## 7. Gotchas & takeaways

> A pooled connection is tied to the exact principal (bind DN) and credentials it was created with. Never assume a pooled `DirContext` obtained for one identity can be reused for another — the pool itself enforces this by keying pools per credential set, but designing application code around a single shared identity per `ContextSource` (card 0002) keeps this simple and avoids surprises.

- Enable pooling for any application performing frequent LDAP operations; the overhead of connection setup (TCP + TLS + bind) is usually the dominant cost, not the operation itself.
- `testOnBorrow` (or equivalent validation) is what prevents a silently-dropped server-side connection from causing a confusing failure on the client — without it, a connection the server already closed can be handed to a caller and fail unpredictably.
- Size `maxTotal` based on both expected concurrency and the LDAP server's own connection limits — an unbounded or oversized pool can overwhelm the directory server just as easily as unpooled connections can.
- Idle eviction (`minEvictableIdleTimeMillis`) matters for applications with bursty traffic — without it, a pool sized for peak load stays fully open even during quiet periods, needlessly holding server-side resources.
- Pooling configuration lives on the `ContextSource` layer, not on `LdapTemplate` — the template code calling `search()` or `authenticate()` doesn't change at all when pooling is introduced.
