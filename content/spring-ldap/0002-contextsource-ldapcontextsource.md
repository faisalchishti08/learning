---
card: spring-ldap
gi: 2
slug: contextsource-ldapcontextsource
title: "ContextSource & LdapContextSource"
---

## 1. What it is

`ContextSource` is Spring LDAP's abstraction for obtaining a `DirContext` — a live, authenticated connection to an LDAP directory. `LdapContextSource` is the standard, ready-to-use implementation: you configure it once with a server URL, a base DN, and credentials, and it becomes the factory that `LdapTemplate` (card 0001) draws connections from for every operation. It plays exactly the role `DataSource` plays for JDBC: a single configured object that knows how to produce a usable connection on demand.

## 2. Why & when

An LDAP operation needs an authenticated network connection to a specific server before it can do anything. Hardcoding connection details (URL, credentials, base DN) inside every piece of code that talks to LDAP would mean duplicating that configuration everywhere and making it impossible to swap servers (say, moving from a test directory to production) without touching business logic. `ContextSource` centralizes that configuration into one bean, and `LdapContextSource` is the concrete class that actually implements it for a standard LDAP/JNDI connection.

Configure a `ContextSource` whenever an application:

- Connects to any LDAP or Active Directory server for search, bind, or modify operations.
- Needs to point at different directories per environment (a local test server, a staging directory, a production directory) without changing application code.
- Wants connection pooling (card 0003) — pooling is configured on top of the `ContextSource`, not on `LdapTemplate` itself.

## 3. Core concept

Think of `ContextSource` as a hotel's front desk, and a `DirContext` as a room key. You don't carve your own key or negotiate directly with the building's security system — you go to the front desk (`ContextSource`), present your credentials once during setup, and the desk hands you a key (`DirContext`) whenever you need to enter a room (perform an operation). `LdapContextSource` is simply the front desk implementation configured for one particular hotel (one particular LDAP server), knowing its address, the manager's login, and which floor (base DN) guests start from.

The key configuration properties on `LdapContextSource` are:

- **`url`** — the LDAP server's address, e.g. `ldap://ldap.example.com:389` (or `ldaps://` for TLS).
- **`base`** — the base distinguished name (DN) that all relative operations are resolved against, e.g. `dc=example,dc=com`.
- **`userDn`** and **`password`** — the credentials used to bind (authenticate) to the directory for operations performed through this `ContextSource`.
- **`pooled`** — whether connections should be pooled rather than opened fresh each time (card 0003 covers this in depth).

Once configured, calling `afterPropertiesSet()` (or letting Spring's container do it automatically for a `@Bean`) validates the configuration and makes the `ContextSource` ready to hand out contexts.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LdapContextSource is configured once with URL, base DN, and credentials, then produces authenticated DirContext instances on demand">
  <rect x="20" y="70" width="200" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="98" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">LdapContextSource</text>
  <text x="120" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">url, base, userDn, password</text>
  <text x="120" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(configured once)</text>

  <rect x="440" y="30" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="525" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">DirContext #1</text>

  <rect x="440" y="130" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="525" y="160" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">DirContext #2</text>

  <line x1="220" y1="95" x2="435" y2="55" stroke="#3fb950" stroke-width="1.5" marker-end="url(#b1)"/>
  <line x1="220" y1="115" x2="435" y2="150" stroke="#3fb950" stroke-width="1.5" marker-end="url(#b2)"/>
  <text x="330" y="70" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">getReadOnlyContext()</text>

  <defs>
    <marker id="b1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="b2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

One configured `LdapContextSource` produces many `DirContext` instances over its lifetime, each an authenticated connection ready for one operation.

## 5. Runnable example

The scenario: configure a `ContextSource` for a directory holding employee records, starting with a bare-minimum setup and evolving it to support environment-specific configuration and anonymous read-only access alongside privileged writes.

### Level 1 — Basic

```java
// BasicContextSourceDemo.java
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.LdapTemplate;

public class BasicContextSourceDemo {
    public static void main(String[] args) throws Exception {
        LdapContextSource contextSource = new LdapContextSource();
        contextSource.setUrl("ldap://localhost:389");
        contextSource.setBase("dc=example,dc=com");
        contextSource.setUserDn("cn=admin,dc=example,dc=com");
        contextSource.setPassword("adminpass");
        contextSource.afterPropertiesSet(); // validates config, must be called manually outside Spring

        LdapTemplate template = new LdapTemplate(contextSource);
        System.out.println("Context source ready, root DN: " + contextSource.getBaseLdapPathAsString());
    }
}
```

**How to run:** with an LDAP server listening on `localhost:389` (e.g. `docker run -p 389:389 osixia/openldap`), run `java BasicContextSourceDemo.java`. Expected output: `Context source ready, root DN: dc=example,dc=com`.

### Level 2 — Intermediate

Hardcoding the URL and password directly in code means every environment change requires a code change and redeploy, and it puts a plaintext password in source control. Externalizing this as Spring configuration solves both.

```java
// LdapConfig.java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;

@Configuration
public class LdapConfig {

    @Value("${ldap.url}")
    private String url;

    @Value("${ldap.base}")
    private String base;

    @Value("${ldap.userDn}")
    private String userDn;

    @Value("${ldap.password}")
    private String password;

    @Bean
    public LdapContextSource contextSource() {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl(url);
        cs.setBase(base);
        cs.setUserDn(userDn);
        cs.setPassword(password);
        // afterPropertiesSet() is called automatically by Spring for InitializingBean beans
        return cs;
    }

    @Bean
    public LdapTemplate ldapTemplate(LdapContextSource contextSource) {
        return new LdapTemplate(contextSource);
    }
}
```

```properties
# application-dev.properties
ldap.url=ldap://localhost:389
ldap.base=dc=example,dc=com
ldap.userDn=cn=admin,dc=example,dc=com
ldap.password=${LDAP_ADMIN_PASSWORD}
```

**How to run:** run the Spring application with `spring.profiles.active=dev` and `LDAP_ADMIN_PASSWORD` set as an environment variable. Expected result: the same `dc=example,dc=com` directory is reachable, but switching to `application-prod.properties` with different values points the exact same code at a different server with no code change — and the password never appears in source control.

### Level 3 — Advanced

A single, privileged `ContextSource` bound as `cn=admin` for every operation is a real production risk: read-heavy operations (most searches) don't need write credentials, and a compromised or misused code path could modify the directory unintentionally. This level splits reads and writes across two `ContextSource` beans with different privilege levels.

```java
// SplitPrivilegeLdapConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;

@Configuration
public class SplitPrivilegeLdapConfig {

    @Bean
    public LdapContextSource readOnlyContextSource() {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://ldap.example.com:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=readonly-service,dc=example,dc=com"); // account with search-only ACLs
        cs.setPassword(System.getenv("LDAP_READONLY_PASSWORD"));
        cs.setPooled(true); // safe for the high-volume read path (card 0003)
        return cs;
    }

    @Bean
    public LdapContextSource adminContextSource() {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://ldap.example.com:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com"); // account with write ACLs, used sparingly
        cs.setPassword(System.getenv("LDAP_ADMIN_PASSWORD"));
        return cs;
    }

    @Bean
    public LdapTemplate searchTemplate(LdapContextSource readOnlyContextSource) {
        return new LdapTemplate(readOnlyContextSource);
    }

    @Bean
    public LdapTemplate adminTemplate(LdapContextSource adminContextSource) {
        return new LdapTemplate(adminContextSource);
    }
}
```

**How to run:** wire `searchTemplate` into every read-only service (employee lookups, group membership checks) and `adminTemplate` only into the small set of provisioning code that actually creates or modifies entries. Attempting a write through `searchTemplate` fails at the directory's ACL layer (an `InsufficientResourcesException` or similar, depending on server configuration) rather than through application logic — the blast radius of a coding mistake in a read path is now contained by the directory server itself, not just by code review.

## 6. Walkthrough

Tracing a search request through the split-privilege setup, in execution order:

1. A service method calls `searchTemplate.search(...)`, requesting an employee lookup.
2. `LdapTemplate` (wrapping `searchTemplate`) asks its configured `readOnlyContextSource` for a `DirContext` via `getReadOnlyContext()`.
3. `LdapContextSource` opens (or, if pooling is enabled per card 0003, reuses) a network connection to `ldap://ldap.example.com:389` and performs a JNDI bind using the `cn=readonly-service` credentials.
4. The directory server authenticates the bind and, because this account's ACLs only grant search rights, would reject any write attempted through this same context — but here only a search is requested, so it proceeds.
5. The search executes and results flow back up through `LdapTemplate` exactly as described in card 0001's walkthrough.
6. Separately, if a provisioning workflow calls `adminTemplate.bind(...)` to create a new user entry, the same sequence happens but against `adminContextSource`, which binds as `cn=admin` — an account with write ACLs — so the create succeeds.

```
searchTemplate.search(...)  -> readOnlyContextSource -> bind as cn=readonly-service -> SEARCH allowed, WRITE denied
adminTemplate.bind(...)     -> adminContextSource     -> bind as cn=admin           -> SEARCH allowed, WRITE allowed
```

## 7. Gotchas & takeaways

> Outside a Spring container, `afterPropertiesSet()` must be called manually after configuring an `LdapContextSource` — it's normally invoked automatically because `LdapContextSource` implements `InitializingBean`, but a plain `new LdapContextSource()` used standalone (Level 1) will throw confusing errors on first use if this step is skipped.

- One `ContextSource` per distinct set of credentials/privileges is a common and valuable pattern — don't default to a single admin-bound `ContextSource` used for every operation in the application.
- Never hardcode LDAP credentials directly in source code; externalize them via configuration properties and environment variables, as in Level 2.
- `LdapContextSource` is the standard `ContextSource` implementation for direct LDAP connections; it is not itself pooled by default — pooling is a separate, explicit setting (card 0003).
- The `base` DN configured on the `ContextSource` becomes the implicit root for every relative name passed to `LdapTemplate` — operations use names relative to this base, not full DNs, unless configured otherwise.
- Switching environments (dev/staging/prod) should only ever require configuration changes, never code changes — if it doesn't, the `ContextSource` configuration probably needs to be externalized further.
