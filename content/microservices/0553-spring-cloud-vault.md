---
card: microservices
gi: 553
slug: spring-cloud-vault
title: "Spring Cloud Vault"
---

## 1. What it is

**Spring Cloud Vault** integrates HashiCorp Vault — a dedicated secrets-management system — into Spring's configuration model, so database credentials, API keys, and certificates are fetched from Vault at runtime rather than stored in plaintext configuration files or environment variables. Beyond simply storing secrets more securely, Vault supports **dynamic secrets**: instead of a long-lived, shared database password, Vault can generate a short-lived, unique credential per requesting application on demand, automatically revoked or rotated after a configured lease expires — a fundamentally different security posture than a static secret that, once leaked, remains valid indefinitely.

## 2. Why & when

You reach for Vault-backed secrets specifically because static secrets in configuration files or environment variables carry real, ongoing risk that dynamic, short-lived secrets are designed to eliminate:

- **A static secret in a config file or environment variable is a standing liability** — anyone with read access to that file, that environment, or a backup of either has the secret indefinitely, and rotating it (an important security practice) requires manually updating every place that secret is configured, a real coordination burden that often causes rotation to be skipped or delayed in practice.
- **Vault's dynamic secrets are generated on demand, per requesting application, with a bounded lease** — a database credential fetched from Vault might only be valid for an hour, automatically expiring (and Vault automatically revoking the corresponding database user) unless the application renews the lease; a leaked dynamic secret has a bounded, often short, window of usefulness to an attacker, rather than being valid forever.
- **Spring Cloud Vault integrates this fetching transparently into Spring's configuration model** — a `@Value`-bound property or a `DataSource` bean's credentials can be sourced from Vault exactly as they would from any other property source, with the application code having no awareness that a secret is short-lived, being automatically renewed, or rotated in the background.
- **You reach for Vault specifically once secret management (not just configuration management) becomes a real, deliberate concern** — for a small number of low-sensitivity values, a simpler secrets mechanism might suffice; Vault earns its operational complexity when you have genuinely sensitive credentials (database passwords, third-party API keys, TLS private keys) that benefit from dynamic generation, centralized auditing of who accessed what secret and when, and fine-grained access policies.

## 3. Core concept

Think of the difference between a shared master key to a building, copied and handed out to everyone who might ever need access (a static secret — once someone leaves or the key is lost, everyone's access is compromised until every lock is physically rekeyed), versus a smart-lock system that issues a unique, temporary access code to each person requesting entry, valid only for a limited window, automatically expiring and requiring a fresh request afterward (a dynamic secret). The temporary-code approach means a specific compromised code has bounded value to whoever obtained it improperly, and the system maintains a clear, centralized log of exactly who requested access and when — neither of which the shared master key can offer.

Concretely:

1. **Vault stores static secrets (an encrypted key-value store) and can also broker dynamic secrets** for supported backends (databases, cloud provider credentials, PKI certificates) — for a database, Vault can generate a fresh, unique username/password pair on demand, valid only for a configured lease duration.
2. **Spring Cloud Vault fetches these secrets at application startup** (and, for dynamic secrets, manages lease renewal in the background), populating the application's `Environment` exactly as any other property source would — a `DataSource` bean configured with `${spring.datasource.username}`/`${spring.datasource.password}` sourced from Vault has no idea those values came from a dynamically-generated, time-limited credential rather than a static config file entry.
3. **A lease is Vault's tracked commitment to a secret's validity window** — Spring Cloud Vault's `VaultTokenRenewalScheduler`-style background mechanism renews the lease periodically as long as the application is running, and Vault automatically revokes the underlying secret (for a dynamic database credential, actually dropping that database user) once the lease is allowed to expire, whether because the application stopped renewing it or because it shut down.
4. **Access to Vault itself requires authentication** (via a token, Kubernetes service account, AWS IAM role, or other supported auth method) — Vault's own access policies determine which secrets a given authenticated identity is permitted to read, giving centralized, auditable control over who (or what application) can access which secrets.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A static secret is fetched once and remains valid indefinitely; a Vault dynamic secret is generated on demand with a bounded lease, automatically revoked when the lease expires or isn't renewed">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Static secret</text>
  <rect x="20" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">password in config file: valid FOREVER</text>
  <text x="150" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">leaked once = compromised indefinitely, until manually rotated</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Vault dynamic secret</text>
  <rect x="380" y="35" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">unique credential, lease: 1 hour</text>
  <text x="510" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">leaked = bounded window; auto-revoked if not renewed</text>
</svg>

A static secret is a standing liability once leaked; a dynamic secret's bounded lease limits how long a leak remains useful.

## 5. Runnable example

Scenario: a database credential fetched securely. We start with a plain Java model contrasting static versus dynamic secret validity, extend it to lease renewal, then show the real Spring Cloud Vault configuration.

### Level 1 — Basic

```java
// File: StaticVsDynamicSecret.java -- models the CORE difference: a
// static secret is valid forever; a dynamic one has a BOUNDED lease.
import java.time.*;

public class StaticVsDynamicSecret {
    record StaticSecret(String value) {} // no expiration concept AT ALL
    record DynamicSecret(String value, Instant leaseExpiresAt) {
        boolean isValid(Instant now) { return now.isBefore(leaseExpiresAt); }
    }

    public static void main(String[] args) {
        StaticSecret staticPassword = new StaticSecret("hardcoded-forever-password");
        System.out.println("Static secret is ALWAYS considered valid: " + staticPassword.value());

        Instant now = Instant.parse("2026-01-01T00:00:00Z");
        DynamicSecret dynamicCredential = new DynamicSecret("temp-user-a1b2:temp-pass-c3d4", now.plus(Duration.ofHours(1)));
        System.out.println("Dynamic secret valid now? " + dynamicCredential.isValid(now));
        System.out.println("Dynamic secret valid in 2 hours? " + dynamicCredential.isValid(now.plus(Duration.ofHours(2))) + " -- correctly EXPIRED, bounded lease.");
    }
}
```

How to run: `java StaticVsDynamicSecret.java`

`StaticSecret` has no expiration concept at all — its `value` is considered valid indefinitely. `DynamicSecret.isValid` checks against `leaseExpiresAt`, correctly reporting the credential expired two hours later — modeling exactly why a leaked dynamic secret has bounded usefulness to an attacker, unlike a leaked static one.

### Level 2 — Intermediate

```java
// File: LeaseRenewalModel.java -- models an application PERIODICALLY
// RENEWING its lease to keep a dynamic secret valid while it's still
// actively running, and the secret expiring if renewal stops.
import java.time.*;
import java.util.*;

public class LeaseRenewalModel {
    static Instant leaseExpiresAt;
    static final Duration LEASE_DURATION = Duration.ofMinutes(30);

    static void issueSecret(Instant now) {
        leaseExpiresAt = now.plus(LEASE_DURATION);
        System.out.println("Secret issued at " + now + ", lease expires " + leaseExpiresAt);
    }
    static void renewLease(Instant now) {
        if (now.isBefore(leaseExpiresAt)) {
            leaseExpiresAt = now.plus(LEASE_DURATION); // renewed BEFORE expiry -- extends validity
            System.out.println("Lease renewed at " + now + ", new expiry " + leaseExpiresAt);
        } else {
            System.out.println("Lease ALREADY EXPIRED at " + now + " -- too late to renew, secret is now invalid");
        }
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");
        issueSecret(t0);
        renewLease(t0.plus(Duration.ofMinutes(20))); // renewed BEFORE the 30-min expiry -- application still running
        renewLease(t0.plus(Duration.ofMinutes(50))); // renewed AGAIN before ITS new expiry

        // now imagine the application crashed and STOPPED renewing after t0+50min
        System.out.println("If renewal stops, the lease from t0+50min expires at t0+80min -- secret becomes invalid, Vault revokes it.");
    }
}
```

How to run: `java LeaseRenewalModel.java`

As long as `renewLease` is called before the current `leaseExpiresAt`, the secret's validity keeps extending — modeling a healthy, running application periodically renewing its Vault-issued lease in the background. If renewal calls stop (the application crashes or is shut down), the last-known `leaseExpiresAt` eventually passes, and the credential becomes invalid — in real Vault, this triggers automatic revocation of the underlying dynamic secret (dropping the database user, for instance).

### Level 3 — Advanced

```java
// File: SpringCloudVaultRealShape.java -- the REAL Spring Cloud Vault
// shape: a DataSource whose credentials are sourced from Vault's dynamic
// database secrets engine, with lease renewal handled transparently.
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import javax.sql.DataSource;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

public class SpringCloudVaultRealShape {

    @Configuration
    static class DataSourceConfig {
        // these values are populated from VAULT's dynamically-generated database credentials,
        // NOT a static config file entry -- Spring Cloud Vault fetches and renews them transparently
        @Value("${spring.datasource.username}")
        private String dbUsername;

        @Value("${spring.datasource.password}")
        private String dbPassword;

        @Bean
        public DataSource dataSource() {
            DriverManagerDataSource dataSource = new DriverManagerDataSource();
            dataSource.setUrl("jdbc:postgresql://order-db:5432/orders");
            dataSource.setUsername(dbUsername); // e.g. "v-approle-order-svc-a1b2c3", generated by Vault, unique to this app instance
            dataSource.setPassword(dbPassword); // valid only for Vault's configured lease duration
            return dataSource;
        }
    }

    // application.yml / bootstrap configuration:
    //   spring.cloud.vault.host: vault-server
    //   spring.cloud.vault.database.enabled: true
    //   spring.cloud.vault.database.role: order-service-role
    //   spring.cloud.vault.database.backend: database
    // -- Spring Cloud Vault fetches a FRESH, unique credential from Vault's database
    //    secrets engine at startup, and renews its lease automatically in the background.
}
```

How to run: requires `spring-cloud-starter-vault-config`, a running Vault server with the database secrets engine configured and a role (`order-service-role`) granting time-limited database credentials, plus `spring.cloud.vault.*` connection properties; run via `mvn spring-boot:run` and inspect the actual generated username in Vault's audit log to confirm it's unique per application instance and tied to a bounded lease, rather than a shared, static credential.

`DataSourceConfig`'s `dbUsername`/`dbPassword` fields are populated exactly like any other `@Value`-bound property — nothing in this code reveals they came from Vault's dynamically-generated database secrets engine rather than a static `application.yml` entry. Spring Cloud Vault's background lease-renewal mechanism (configured via `spring.cloud.vault.database.*`) keeps this credential valid for as long as the application keeps running, transparently, without `DataSourceConfig` needing any lease-aware code of its own.

## 6. Walkthrough

Trace what happens across an `order-service` instance's lifetime, using Vault-issued dynamic database credentials as in Level 3:

1. **At startup, Spring Cloud Vault authenticates to the Vault server** (using whichever auth method is configured — a Kubernetes service account token, an AppRole, etc.) and requests a new database credential for the configured role `order-service-role`.
2. **Vault's database secrets engine creates a brand-new, unique database user** (say, `v-approle-order-svc-a1b2c3`) with a randomly-generated password, grants it whatever permissions the `order-service-role` policy specifies, and returns both the username and password to Spring Cloud Vault, along with a lease ID and duration (say, 1 hour).
3. **Spring Cloud Vault populates `spring.datasource.username`/`spring.datasource.password` in the application's `Environment`** with these freshly-generated values, and `DataSourceConfig`'s `@Value`-bound fields are set accordingly when the `dataSource()` bean is created.
4. **The `DataSource` bean connects to the database using this unique, time-limited credential**, and the application proceeds to use it normally for all its database operations — completely unaware the credential is anything other than an ordinary username/password.
5. **In the background, Spring Cloud Vault's lease-renewal scheduler periodically calls back to Vault** (before the 1-hour lease expires) to renew it, extending its validity as long as the application keeps running — this happens without any involvement from `DataSourceConfig` or any other application code.
6. **If the application is shut down (or the lease renewal fails for some reason and the lease is allowed to expire)**, Vault automatically revokes the credential — actually dropping the `v-approid-order-svc-a1b2c3` database user — so even if that specific username/password pair were somehow leaked afterward, it would no longer grant any access at all.

## 7. Gotchas & takeaways

> **Gotcha:** if an application crashes or is forcibly killed without a graceful shutdown, its lease-renewal background thread simply stops running — Vault doesn't immediately know the application is gone, so the dynamic credential remains valid until its current lease naturally expires (potentially up to the full lease duration later); a shorter lease duration reduces this residual-validity window at the cost of more frequent renewal traffic against Vault, a trade-off worth tuning deliberately for genuinely sensitive credentials.

- Dynamic secrets, generated on demand with a bounded lease, replace the standing liability of a static, long-lived secret with a credential whose usefulness to an attacker is bounded by the lease duration.
- Spring Cloud Vault integrates secret fetching (and, for dynamic secrets, background lease renewal) transparently into Spring's ordinary configuration model — application code never needs lease-aware logic of its own.
- Vault centralizes access policy enforcement and auditing for who (or what application identity) can read which secrets, a meaningful improvement over secrets scattered across config files with no centralized record of access.
- Weigh lease duration deliberately: shorter leases reduce the residual-validity window after an ungraceful application shutdown, at the cost of more frequent renewal traffic against the Vault server.
