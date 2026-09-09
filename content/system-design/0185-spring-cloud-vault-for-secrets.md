---
card: system-design
gi: 185
slug: spring-cloud-vault-for-secrets
title: Spring Cloud Vault for secrets
---

## 1. What it is

**Spring Cloud Vault** integrates a Spring Boot application with **HashiCorp Vault**, a dedicated [secrets management](0180-secrets-management-rotation.md) system, so the application fetches secrets (database credentials, API keys) from Vault at startup (or refreshes them at runtime) instead of reading them from a static `application.yml` or environment variable. Vault can also generate short-lived, dynamic database credentials on demand, unique to each running application instance, rather than handing out one shared, long-lived password.

## 2. Why & when

A database password sitting in a configuration file (even one excluded from version control) still exists as a long-lived, static secret that anyone with access to the running server, a backup, or a configuration management tool can read indefinitely. Spring Cloud Vault instead has the application authenticate to Vault at startup, fetch the current secret value dynamically, and — for supported backends — request Vault to generate a brand-new, uniquely-scoped credential just for this application instance, with its own expiry. Use it in any Spring Boot application where credentials should be centrally managed, audited, and rotated, rather than baked into static configuration.

## 3. Core concept

- **`bootstrap.yml` / `spring.cloud.vault` configuration:** the application authenticates to Vault (commonly via a token, or a more dynamic method like AppRole) during startup, before the rest of the Spring context loads.
- **Static secrets backend (KV):** the simplest case — Vault stores a key-value secret, and Spring Cloud Vault injects its values directly into the application's `Environment`, the same way `application.yml` properties normally are.
- **Dynamic secrets backend (e.g. database):** instead of a fixed, shared password, Vault generates a brand-new database username and password *specifically for this application instance*, valid only for a configured lease duration — a genuinely different credential per instance, automatically expiring.
- **Lease renewal:** Spring Cloud Vault automatically renews a dynamic secret's lease in the background before it expires, as long as the application is still running; if renewal fails or the application shuts down, the credential's lease naturally expires and Vault revokes it.
- **`@RefreshScope` for rotated secrets:** combined with Spring Cloud's refresh mechanism, a bean holding a Vault-sourced secret can pick up a rotated value without restarting the whole application.

## 4. Diagram

```
   application startup
        |
        v
   authenticate to Vault (token / AppRole)
        |
        v
   request database credentials from Vault's "database" secrets engine
        |
        v
   Vault generates a UNIQUE username/password, with a lease duration (e.g. 1 hour)
        |
        v
   Spring injects these into the app's DataSource - this instance uses ITS OWN credential
        |
   [ background: Spring Cloud Vault renews the lease before it expires, automatically ]
        |
   if the application shuts down or renewal fails -> lease expires -> Vault revokes the credential
```
*Caption: each application instance gets its own uniquely-generated, automatically-expiring database credential, instead of every instance sharing one static password.*

## 5. Runnable example

This models Vault's dynamic-secret issuance and lease renewal in-process; the "How to run" note shows the real Spring Cloud Vault configuration.

**Level 1 — Basic.** Fetch a static secret value from a Vault-like key-value store.

**Level 2 — Request a dynamic, uniquely-generated database credential per instance.** Model Vault's database secrets engine.

**Level 3 — Automatic lease renewal, and revocation if renewal stops happening.** Show a credential expiring once its lease is no longer renewed.

```java
// SpringCloudVaultDemo.java
import java.util.*;

public class SpringCloudVaultDemo {

    // Level 1: a static KV secret, as Vault's simplest secrets engine would return.
    static Map<String, String> staticSecrets = Map.of("api-key", "static-key-abc123");

    static String fetchStaticSecret(String path) {
        return staticSecrets.get(path);
    }

    // Level 2: dynamic secrets - Vault generates a UNIQUE credential per request (per application instance).
    static class DynamicCredential {
        final String username, password;
        long leaseExpiresAtMillis;
        boolean revoked = false;
        DynamicCredential(String username, String password, long leaseExpiresAtMillis) {
            this.username = username; this.password = password; this.leaseExpiresAtMillis = leaseExpiresAtMillis;
        }
    }

    static int credentialCounter = 0;
    static DynamicCredential requestDynamicDbCredential(long nowMillis, long leaseDurationMillis) {
        credentialCounter++;
        String username = "app-generated-" + credentialCounter;
        String password = "pw-" + UUID.randomUUID().toString().substring(0, 8);
        System.out.println("  Vault generated a NEW credential: " + username + " (lease " + leaseDurationMillis + "ms)");
        return new DynamicCredential(username, password, nowMillis + leaseDurationMillis);
    }

    // Level 3: automatic renewal - extends the lease, as Spring Cloud Vault does in the background.
    static void renewLease(DynamicCredential cred, long nowMillis, long leaseDurationMillis) {
        if (cred.revoked) { System.out.println("  cannot renew - credential already revoked"); return; }
        cred.leaseExpiresAtMillis = nowMillis + leaseDurationMillis;
        System.out.println("  lease renewed for " + cred.username + ", now expires at t=" + cred.leaseExpiresAtMillis);
    }

    static void checkAndRevokeIfExpired(DynamicCredential cred, long nowMillis) {
        if (!cred.revoked && nowMillis >= cred.leaseExpiresAtMillis) {
            cred.revoked = true;
            System.out.println("  lease EXPIRED for " + cred.username + " - Vault revoked the credential");
        }
    }

    public static void main(String[] args) {
        System.out.println("-- static secret --");
        System.out.println("app fetches API key from Vault at startup: " + fetchStaticSecret("api-key"));

        System.out.println("-- dynamic database credential --");
        long now = 0;
        long leaseDuration = 1000; // 1000ms lease, for demo purposes
        DynamicCredential instanceOneCred = requestDynamicDbCredential(now, leaseDuration);
        DynamicCredential instanceTwoCred = requestDynamicDbCredential(now, leaseDuration);
        System.out.println("instance-1 uses: " + instanceOneCred.username + " (unique to this instance)");
        System.out.println("instance-2 uses: " + instanceTwoCred.username + " (a DIFFERENT credential, not shared)");

        // Level 3: instance-1 keeps renewing (still running); instance-2 stops (crashed, or shut down).
        now += 500;
        renewLease(instanceOneCred, now, leaseDuration); // instance-1's Spring Cloud Vault background renewal
        System.out.println("(instance-2 does NOT renew - simulating it crashed)");

        now += 600; // total elapsed: 1100ms - past instance-2's original 1000ms lease, which was never renewed
        checkAndRevokeIfExpired(instanceOneCred, now);
        checkAndRevokeIfExpired(instanceTwoCred, now);
        System.out.println("instance-1 credential still valid: " + !instanceOneCred.revoked);
        System.out.println("instance-2 credential still valid: " + !instanceTwoCred.revoked);
    }
}
```

**How to run:** save as `SpringCloudVaultDemo.java`, then run `java SpringCloudVaultDemo.java`. (Real Spring Cloud Vault: add `spring-cloud-starter-vault-config`, configure `spring.cloud.vault.uri` and an authentication method in `bootstrap.yml`, and for a static KV secret Spring injects the value directly into the `Environment`; for a `database` secrets engine, `spring.cloud.vault.database.role` triggers Vault to generate a unique credential per instance, with Spring Cloud Vault automatically renewing its lease in the background.)

## 6. Walkthrough

1. `fetchStaticSecret("api-key")` looks up the value directly from `staticSecrets`, modeling how Spring Cloud Vault injects a static KV secret's value into the application's configuration at startup, with no per-instance uniqueness involved.
2. `requestDynamicDbCredential(now, leaseDuration)` is called twice, once per simulated application instance; each call increments `credentialCounter` and generates a distinct `username` and random `password`, so `instanceOneCred` and `instanceTwoCred` are genuinely different credentials, each with its own `leaseExpiresAtMillis` set to `now + leaseDuration` (both `1000` at this point, since both were requested at `now = 0`).
3. `renewLease(instanceOneCred, now, leaseDuration)` is called at `now = 500`, modeling Spring Cloud Vault's background renewal for the still-running instance-1; it updates `leaseExpiresAtMillis` to `500 + 1000 = 1500`, extending it well past the original expiry — instance-2's credential is deliberately left un-renewed, modeling a crashed or shut-down instance.
4. By `now = 1100`, `checkAndRevokeIfExpired(instanceOneCred, now)` finds `1100 >= 1500` is false, so instance-1's credential remains valid — the renewal in step 3 successfully kept it alive past its original lease.
5. `checkAndRevokeIfExpired(instanceTwoCred, now)` finds `1100 >= 1000` (its original, never-renewed expiry) is true, so it sets `revoked = true` and prints the revocation message — the final printed check confirms instance-1's credential is still valid while instance-2's has been automatically revoked, exactly the self-cleaning behavior a crashed instance's dynamic credential should have, with no manual intervention required.

## 7. Gotchas & takeaways

> Gotcha: configuring a very short lease duration for a dynamic secret without confirming the application's renewal mechanism is actually working (network connectivity to Vault, correct authentication) can cause credentials to expire and be revoked out from under a perfectly healthy, still-running application — always monitor lease renewal health, not just assume it "just works" once configured.

- Spring Cloud Vault removes static, long-lived secrets from application configuration by fetching them (or generating them dynamically) from a dedicated secrets manager at runtime.
- Dynamic secrets give each application instance its own uniquely-generated, independently-expiring credential, rather than one shared password everyone uses.
- Automatic lease renewal is what keeps a healthy instance's dynamic credential alive; a crashed or disconnected instance's credential naturally expires and is revoked without manual cleanup.
- Related concepts: [Secrets management & rotation](0180-secrets-management-rotation.md) (the general pattern this Spring integration implements), [Encryption in transit (TLS) & at rest](0179-encryption-in-transit-tls-at-rest.md) (Vault itself also manages encryption keys, a related secret type), [API keys & mutual TLS (mTLS)](0178-api-keys-mutual-tls-mtls.md) (another kind of credential that benefits from this same centralized management).
