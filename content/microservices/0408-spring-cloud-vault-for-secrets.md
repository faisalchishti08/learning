---
card: microservices
gi: 408
slug: spring-cloud-vault-for-secrets
title: "Spring Cloud Vault for secrets"
---

## 1. What it is

**Spring Cloud Vault** is the Spring integration for HashiCorp Vault, a dedicated secrets-management system. Instead of database passwords, API keys, or signing keys sitting in `application.yml` or environment variables (where they're easy to leak into version control, logs, or container images), Spring Cloud Vault fetches them at startup — or dynamically, per request — from Vault, giving a Spring Boot application the concrete implementation of [secrets management & rotation](0394-secrets-management-rotation.md): secrets live in one hardened system, are fetched just-in-time, and can be rotated without redeploying every service that uses them.

## 2. Why & when

You reach for Spring Cloud Vault specifically once "put the password in an environment variable" stops being an acceptable answer for a growing microservices system:

- **Static secrets in config files or environment variables never expire and are easy to leak** — a checked-in `application.yml`, a container image layer, or a process listing can all expose them; Vault-backed secrets can be short-lived and centrally revocable instead.
- **Dynamic secrets eliminate long-lived shared credentials entirely.** Rather than every service sharing one static database password, Vault can mint a *unique*, *time-limited* database credential per service instance on demand — if one leaks, it expires soon and was never shared with anyone else.
- **Centralized rotation** means rotating a secret is a Vault-side operation, not a "redeploy every service that has this password hardcoded" operation — directly addressing the rotation half of [secrets management & rotation](0394-secrets-management-rotation.md).
- **Audit and access control** live in Vault itself: every secret read is logged, and access policies determine which service identity can read which secret path, adding a real authorization layer to secret access instead of "anyone with the environment variable has it forever."

You need this the moment a system has more than a couple of secrets to manage across more than a couple of services, or any time compliance requirements demand provable rotation and access auditing for credentials.

## 3. Core concept

Think of hardcoded secrets in config as leaving a spare house key taped under the doormat — convenient, but anyone who finds it has permanent access, and you'd never know if it had been copied. Vault is like a smart lockbox: it hands out a temporary access code to anyone who first proves who they are, logs every code issued, and can revoke or expire codes without you ever needing to change the lock itself.

The essential pieces:

1. **`bootstrap.yml` (or `spring.config.import`)** — Spring Cloud Vault fetches secrets *before* the rest of the application context is created, so they're available as regular Spring properties by the time your beans wire up.

```yaml
spring:
  config:
    import: "vault://"
  cloud:
    vault:
      uri: https://vault.internal.example.com:8200
      authentication: KUBERNETES        # or TOKEN, APPROLE, AWS_IAM, etc.
      kubernetes:
        role: order-service
        service-account-token-file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kv:
        enabled: true
        backend: secret
        default-context: order-service   # reads secret/order-service/*
```

2. **Static secrets (KV secrets engine)** — key-value pairs stored at a path (e.g., `secret/order-service`) and exposed as ordinary Spring `@Value` or `@ConfigurationProperties` bindings, just like any other externalized configuration, except sourced from Vault instead of a file.
3. **Dynamic secrets (database secrets engine)** — Vault generates a brand-new database username/password pair on demand, with a lease that expires automatically; Spring Cloud Vault can renew the lease in the background as long as the application is running, and the credential simply stops working once the lease isn't renewed.

```yaml
spring:
  cloud:
    vault:
      database:
        enabled: true
        role: order-service-role          # a Vault role mapping to specific DB privileges
        backend: database
```

4. **Authentication to Vault itself** — the application must first prove *its own* identity to Vault (via a Kubernetes service account token, an AppRole, cloud IAM credentials, etc.) before Vault will hand out any secret — Vault doesn't trust an anonymous caller any more than a resource server trusts an unsigned token.

## 4. Diagram

<svg viewBox="0 0 660 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At startup a Spring Boot application authenticates to Vault using its own identity, Vault checks that identity's policy and returns a secret with a time-limited lease, the application uses the secret and renews the lease periodically, and the secret automatically becomes invalid if the lease is not renewed" font-family="sans-serif">
  <rect x="10" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="102" fill="#e6edf3" font-size="9" text-anchor="middle">order-service</text>
  <text x="75" y="118" fill="#8b949e" font-size="8" text-anchor="middle">Spring Cloud Vault</text>

  <rect x="260" y="60" width="150" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="80" fill="#e6edf3" font-size="10" text-anchor="middle">Vault</text>
  <text x="335" y="100" fill="#8b949e" font-size="8" text-anchor="middle">authenticates identity</text>
  <text x="335" y="114" fill="#8b949e" font-size="8" text-anchor="middle">checks policy</text>
  <text x="335" y="128" fill="#8b949e" font-size="8" text-anchor="middle">issues leased secret</text>

  <rect x="500" y="60" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="570" y="80" fill="#e6edf3" font-size="9" text-anchor="middle">DB credential</text>
  <text x="570" y="96" fill="#8b949e" font-size="8" text-anchor="middle">TTL: 1 hour, renewable</text>

  <rect x="500" y="150" width="140" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="570" y="170" fill="#e6edf3" font-size="9" text-anchor="middle">lease expires</text>
  <text x="570" y="186" fill="#8b949e" font-size="8" text-anchor="middle">if not renewed</text>

  <line x1="140" y1="100" x2="260" y2="100" stroke="#8b949e" marker-end="url(#vt)"/>
  <text x="200" y="90" fill="#8b949e" font-size="8" text-anchor="middle">auth token</text>
  <line x1="410" y1="90" x2="500" y2="85" stroke="#6db33f" marker-end="url(#vt)"/>
  <line x1="410" y1="120" x2="500" y2="170" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#vt)"/>
  <line x1="75" y1="140" x2="75" y2="190" stroke="#79c0ff" stroke-dasharray="2,2"/>
  <text x="75" y="205" fill="#79c0ff" font-size="8" text-anchor="middle">renews lease periodically</text>
  <line x1="140" y1="195" x2="335" y2="160" stroke="#79c0ff" stroke-dasharray="2,2" marker-end="url(#vt)"/>

  <defs>
    <marker id="vt" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Vault issues secrets with a lease, not permanently; the application must keep proving it still needs the secret by renewing that lease, or the credential expires on its own.

## 5. Runnable example

Scenario: `order-service` retrieving a database credential from a Vault-like secrets store. We model static secret retrieval first, then a dynamic, leased credential with expiry, then lease renewal that keeps a long-running service's credential alive without ever hardcoding a permanent password.

### Level 1 — Basic

```java
// File: StaticSecretFromVault.java -- retrieves a STATIC key-value secret,
// mirroring Spring Cloud Vault's KV secrets engine integration: the app
// authenticates, then reads a value at a known path -- no lease, no expiry,
// but still centrally stored and rotatable without redeploying the app.
import java.util.*;

public class StaticSecretFromVault {
    // Stand-in for Vault's KV engine, keyed by path.
    static final Map<String, Map<String, String>> VAULT_KV_STORE = Map.of(
            "secret/order-service", Map.of("api.upstream-key", "sk-live-abc123")
    );

    static Map<String, String> readSecret(String vaultToken, String path) {
        if (!"valid-vault-token".equals(vaultToken)) {
            throw new SecurityException("403 Forbidden -- Vault rejected this token for path " + path);
        }
        Map<String, String> secret = VAULT_KV_STORE.get(path);
        if (secret == null) throw new NoSuchElementException("no secret at path " + path);
        System.out.println("[Vault] returned secret at " + path);
        return secret;
    }

    public static void main(String[] args) {
        Map<String, String> secret = readSecret("valid-vault-token", "secret/order-service");
        System.out.println("Bound as Spring property api.upstream-key = " + secret.get("api.upstream-key"));
    }
}
```

How to run: `java StaticSecretFromVault.java`

`readSecret` requires a valid Vault token before returning anything — the application must already be authenticated to Vault (via `spring.cloud.vault.authentication`) before this call ever succeeds. This mirrors Spring Cloud Vault's `bootstrap` phase: it happens before the rest of the Spring context wires up, so `api.upstream-key` is available as an ordinary bound property to any bean that needs it, with the actual secret value never appearing in `application.yml` at all.

### Level 2 — Intermediate

```java
// File: DynamicLeasedSecret.java -- retrieves a DYNAMIC secret with a
// LEASE: Vault generates a brand-new, time-limited database credential on
// demand rather than returning a static, shared password -- mirroring
// Spring Cloud Vault's database secrets engine integration.
import java.time.*;
import java.util.*;

public class DynamicLeasedSecret {
    record LeasedCredential(String username, String password, Instant leaseExpiresAt) {}

    static int credentialsIssued = 0;

    // Stand-in for Vault's database secrets engine minting a fresh credential per request.
    static LeasedCredential requestDynamicCredential(String vaultToken, String role, Instant now) {
        if (!"valid-vault-token".equals(vaultToken)) throw new SecurityException("403 Forbidden");
        credentialsIssued++;
        String username = "v-" + role + "-" + credentialsIssued;
        String password = "generated-pw-" + UUID.randomUUID().toString().substring(0, 8);
        Instant expiresAt = now.plusSeconds(3600); // 1-hour lease, mirrors a role's configured TTL
        System.out.println("[Vault] minted NEW credential '" + username + "' for role '" + role + "', lease expires " + expiresAt);
        return new LeasedCredential(username, password, expiresAt);
    }

    static boolean isCredentialValid(LeasedCredential cred, Instant now) {
        return now.isBefore(cred.leaseExpiresAt());
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-07-13T12:00:00Z");
        LeasedCredential cred = requestDynamicCredential("valid-vault-token", "order-service-role", t0);
        System.out.println("Credential valid at +30min: " + isCredentialValid(cred, t0.plusSeconds(1800)));
        System.out.println("Credential valid at +90min (past lease): " + isCredentialValid(cred, t0.plusSeconds(5400)));
    }
}
```

How to run: `java DynamicLeasedSecret.java`

`requestDynamicCredential` mints a brand-new username and password every time it's called, rather than returning a fixed, shared value — exactly what Vault's database secrets engine does: it actually creates a new database user with the specified role's privileges, live, on demand. `isCredentialValid` simply compares against the lease's expiry. At `+30min` the credential is still within its 1-hour lease and valid; at `+90min` it has outlived its lease and is no longer usable, whether or not the application remembers to stop using it — the credential itself stops working on the database side once its lease expires, unless renewed.

### Level 3 — Advanced

```java
// File: LeaseRenewalForLongRunningService.java -- a long-running service
// that PERIODICALLY RENEWS its dynamic credential's lease, mirroring Spring
// Cloud Vault's background lease-renewal behavior: as long as the app is
// alive and renewing, the credential stays valid indefinitely; if renewal
// stops (app crashes, network partition to Vault), the credential expires
// on its own -- a form of automatic revocation with no manual step needed.
import java.time.*;
import java.util.*;

public class LeaseRenewalForLongRunningService {
    record LeasedCredential(String username, String password, Instant leaseExpiresAt, int leaseCount) {}

    static int mintCount = 0;
    static int renewCount = 0;
    static final Duration LEASE_TTL = Duration.ofSeconds(3600);

    static LeasedCredential mint(String role, Instant now) {
        mintCount++;
        return new LeasedCredential("v-" + role + "-" + mintCount, "pw-" + mintCount, now.plus(LEASE_TTL), 1);
    }

    // Mirrors Vault's lease renewal API: extends the SAME credential's expiry without minting a new one.
    static LeasedCredential renew(LeasedCredential cred, Instant now) {
        if (now.isAfter(cred.leaseExpiresAt())) {
            System.out.println("[Vault] lease already expired for '" + cred.username() + "' -- cannot renew, must mint fresh");
            return mint("order-service-role", now);
        }
        renewCount++;
        System.out.println("[Vault] renewed lease for '" + cred.username() + "', new expiry " + now.plus(LEASE_TTL));
        return new LeasedCredential(cred.username(), cred.password(), now.plus(LEASE_TTL), cred.leaseCount() + 1);
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-07-13T12:00:00Z");
        LeasedCredential cred = mint("order-service-role", t0);
        System.out.println("Minted: " + cred);

        // Healthy renewal loop: renews well before expiry, every 30 minutes, keeping the SAME username.
        cred = renew(cred, t0.plusSeconds(1800));  // +30min, within TTL -- renewed
        cred = renew(cred, t0.plusSeconds(3300));  // +55min, within TTL -- renewed again

        System.out.println("Final credential still usable, username unchanged: " + cred.username()
                + ", renewals applied: " + cred.leaseCount());

        // A SEPARATE scenario: renewal was missed for too long (e.g. Vault was unreachable) -- lease lapsed.
        LeasedCredential lapsed = mint("order-service-role", t0);
        LeasedCredential afterLapse = renew(lapsed, t0.plusSeconds(7200)); // +2h, way past TTL
        System.out.println("After a missed renewal window, credential was RE-MINTED: " + afterLapse.username()
                + " (old credential is now permanently dead on the database side)");
    }
}
```

How to run: `java LeaseRenewalForLongRunningService.java`

`renew` extends an existing credential's `leaseExpiresAt` as long as it's called before the current lease runs out, keeping the *same* username and password alive indefinitely — mirroring Spring Cloud Vault's background lease-renewal thread, which periodically calls Vault's renew API well before a lease's TTL elapses. The healthy path renews twice, each time well within the 3600-second TTL, and the final credential still carries its original username. The separate lapsed scenario calls `renew` at `+2h`, well past the original 1-hour TTL — `renew` detects the lease already expired and, since Vault cannot resurrect an expired lease, mints a brand-new credential instead, with a different username. This is the concrete failure mode of relying on lease renewal: if a service can't reach Vault for long enough, its credential dies and a fresh one must be minted, which is why the renewal interval should be comfortably shorter than the lease TTL.

## 6. Walkthrough

Trace `LeaseRenewalForLongRunningService.main`'s healthy renewal path. **First**, `mint("order-service-role", t0)` runs. `mintCount` becomes `1`, and a `LeasedCredential` with `username = "v-order-service-role-1"`, `leaseExpiresAt = t0 + 3600s`, and `leaseCount = 1` is returned and printed.

**Next**, `renew(cred, t0.plusSeconds(1800))` runs. `now` (`t0+1800s`) is compared against `cred.leaseExpiresAt()` (`t0+3600s`) — `now.isAfter(expiresAt)` is `false`, so the lease is still alive, and the renewal branch executes: `renewCount` becomes `1`, and a new `LeasedCredential` is returned with the *same* `username` and `password`, but `leaseExpiresAt` pushed out to `now + 3600s` (i.e., `t0 + 5400s`), and `leaseCount` incremented to `2`.

**Then**, `renew(cred, t0.plusSeconds(3300))` runs against the updated `cred` from the previous step. `cred.leaseExpiresAt()` is now `t0+5400s`; `now` (`t0+3300s`) is well before that, so this too is a valid renewal. `renewCount` becomes `2`, `leaseExpiresAt` is pushed to `t0+3300s + 3600s = t0+6900s`, and `leaseCount` becomes `3` — the username and password are unchanged throughout both renewals.

**Finally**, `main` prints the final credential's username (unchanged since minting) and `leaseCount` (`3`), confirming the same database credential survived two renewal cycles without ever being replaced — exactly the property that lets a long-running service keep working indefinitely on one credential, as long as its Vault client keeps renewing on schedule.

```
Minted: LeasedCredential[username=v-order-service-role-1, password=pw-1, leaseExpiresAt=2026-07-13T13:00:00Z, leaseCount=1]
[Vault] renewed lease for 'v-order-service-role-1', new expiry 2026-07-13T13:30:00Z
[Vault] renewed lease for 'v-order-service-role-1', new expiry 2026-07-13T14:15:00Z
Final credential still usable, username unchanged: v-order-service-role-1, renewals applied: 3
[Vault] lease already expired for 'v-order-service-role-2' -- cannot renew, must mint fresh
After a missed renewal window, credential was RE-MINTED: v-order-service-role-3 (old credential is now permanently dead on the database side)
```

## 7. Gotchas & takeaways

> A common production incident pattern: a network partition between a service and Vault lasts longer than the lease TTL, the service's dynamic database credential silently expires, and every subsequent database call starts failing with an authentication error that looks like a database outage rather than what it actually is — a lapsed Vault lease. Monitor lease renewal failures explicitly, and alert well before a lease's TTL, not just on the eventual database connection errors.

- Spring Cloud Vault moves secrets out of `application.yml` and environment variables into a dedicated, auditable, access-controlled system — directly implementing [secrets management & rotation](0394-secrets-management-rotation.md).
- Static (KV) secrets are simple key-value reads with no expiry of their own; dynamic secrets (database, cloud credentials) are minted fresh per request and carry a time-limited lease that must be renewed to stay valid.
- Dynamic secrets are strictly stronger from a security standpoint: no long-lived shared credential exists at all, so a leaked credential is only useful until its lease naturally expires.
- The application must first authenticate to Vault itself (Kubernetes service account, AppRole, cloud IAM) before any secret is returned — Vault access is itself subject to policy-based authorization, not open to any caller who knows a path.
- Lease renewal must happen comfortably before the TTL elapses, and its failure should be monitored explicitly — a lapsed lease produces confusing downstream authentication failures that don't obviously point back to Vault.
