---
card: microservices
gi: 236
slug: spring-cloud-vault-for-secrets
title: "Spring Cloud Vault for secrets"
---

## 1. What it is

Spring Cloud Vault is Spring's integration with HashiCorp Vault, letting a Spring Boot application fetch secrets (database credentials, API keys, encryption keys) directly from Vault at startup (and optionally on a refresh), through the same `@Value`/`@ConfigurationProperties` mechanisms used for ordinary configuration — implementing the [secrets management & encryption](0222-secrets-management-encryption.md) pattern as a first-class, minimal-code Spring integration.

## 2. Why & when

[General secrets management](0222-secrets-management-encryption.md) establishes that secrets need dedicated, encrypted, access-controlled storage rather than plaintext configuration files, but implementing that from scratch — authenticating to a secret store, handling token renewal, mapping secret paths to application configuration — is real, non-trivial work every service would otherwise duplicate. Spring Cloud Vault absorbs this: it authenticates to Vault using a configured method (token, AppRole, Kubernetes service account, among others), fetches secrets from configured paths, and merges them into the application's `Environment` exactly like [Spring Cloud Config Client](0232-spring-cloud-config-client.md) does for ordinary configuration — application code reads a database password via `@Value("${db.password}")` with no awareness that it specifically came from Vault rather than a config file.

Use Spring Cloud Vault for any Spring Boot service that needs genuine secrets (not just ordinary settings) and already has access to a Vault deployment. It's commonly paired with [Spring Cloud Config Server](0231-spring-cloud-config-server.md) — structural configuration from a Git-backed Config Server, secrets from Vault, both surfaced to the application through the identical configuration-reading API.

## 3. Core concept

Spring Cloud Vault authenticates to Vault during the same early configuration-loading phase [Config Client](0232-spring-cloud-config-client.md) operates in, retrieves secrets from configured Vault paths, and merges them into the local `Environment` — application beans created afterward see these secrets through ordinary `@Value` injection, with Vault's own token lease renewal handled transparently underneath.

```java
// application.yaml (of the CLIENT application)
// spring:
//   cloud:
//     vault:
//       uri: https://vault.internal:8200
//       authentication: APPROLE // one of several supported AUTHENTICATION methods
//       kv:
//         backend: secret
//         default-context: order-service // reads from "secret/order-service/*"

@Component
public class DataSourceConfig {
    @Value("${db.password}") // resolved from VAULT -- this class has NO Vault-specific code at all
    String dbPassword;
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During startup, a Spring Boot application authenticates to Vault, fetches secrets from its configured path, and merges them into the local Environment, alongside ordinary configuration fetched from a Config Server -- both surfaced identically to application beans" >
  <rect x="20" y="30" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Vault (secrets)</text>

  <rect x="20" y="110" width="150" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Config Server (structural)</text>

  <rect x="255" y="65" width="150" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="330" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">merged, unified</text>

  <rect x="470" y="65" width="150" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Value("${db.password}")</text>
  <text x="545" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no Vault-specific code</text>

  <line x1="170" y1="52" x2="253" y2="80" stroke="#8b949e" marker-end="url(#arr236)"/>
  <line x1="170" y1="132" x2="253" y2="105" stroke="#8b949e" marker-end="url(#arr236)"/>
  <line x1="405" y1="92" x2="468" y2="92" stroke="#8b949e" marker-end="url(#arr236)"/>

  <defs>
    <marker id="arr236" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Secrets from Vault and structural settings from a Config Server merge into one Environment before any bean is created.

## 5. Runnable example

Scenario: a database configuration bean modeled first with a hard-coded, plaintext password (the risk `secrets management` addresses generally), refactored to fetch the password from a simulated Vault client during startup, and finally adding lease-based token renewal so a long-running application keeps its Vault access valid without any manual re-authentication — mirroring how Spring Cloud Vault handles renewal transparently underneath application code.

### Level 1 — Basic

```java
// File: HardCodedDbPassword.java -- the password is PLAINTEXT, directly
// in code -- the exact risk secrets management is meant to eliminate.
public class HardCodedDbPassword {
    static final String DB_PASSWORD = "hunter2"; // PLAINTEXT, in source AND git history

    public static void main(String[] args) {
        System.out.println("Connecting with password: " + DB_PASSWORD);
    }
}
```

**How to run:** `javac HardCodedDbPassword.java && java HardCodedDbPassword` (JDK 17+).

### Level 2 — Intermediate

```java
// File: FetchFromSimulatedVault.java -- mirrors Spring Cloud Vault:
// authenticates FIRST, then fetches the secret from a Vault-style path --
// NO plaintext secret exists anywhere in this source file.
import java.util.*;

public class FetchFromSimulatedVault {
    static class VaultClient {
        Map<String, Map<String, String>> secretsByPath = Map.of(
            "secret/order-service", Map.of("db.password", "hunter2", "api.key", "sk_live_abc123")
        );
        String authToken;

        String authenticate(String roleId, String secretId) { // mirrors Vault's AppRole auth flow
            authToken = "vault-token-xyz"; // a REAL client would receive a genuine lease-bound token here
            return authToken;
        }

        String readSecret(String path, String key) {
            if (authToken == null) throw new IllegalStateException("must authenticate before reading secrets");
            return secretsByPath.get(path).get(key);
        }
    }

    public static void main(String[] args) {
        VaultClient vault = new VaultClient();
        vault.authenticate("order-service-role", "***approle-secret-id***"); // STEP 1: authenticate

        String dbPassword = vault.readSecret("secret/order-service", "db.password"); // STEP 2: fetch, AFTER auth
        System.out.println("Connecting with password fetched from Vault: " + dbPassword);
        System.out.println("No plaintext secret exists anywhere in THIS source file.");
    }
}
```

**How to run:** `javac FetchFromSimulatedVault.java && java FetchFromSimulatedVault` (JDK 17+).

Expected output:
```
Connecting with password fetched from Vault: hunter2
No plaintext secret exists anywhere in THIS source file.
```

### Level 3 — Advanced

```java
// File: LeaseRenewalKeepsAccessValid.java -- models Vault's LEASE-BASED
// tokens: a token EXPIRES after a TTL, and a background renewal loop
// keeps it valid, mirroring how Spring Cloud Vault handles this
// TRANSPARENTLY for a long-running application.
import java.util.*;
import java.util.concurrent.*;

public class LeaseRenewalKeepsAccessValid {
    static class VaultClient {
        Map<String, Map<String, String>> secretsByPath = Map.of("secret/order-service", Map.of("db.password", "hunter2"));
        volatile String authToken;
        volatile long tokenExpiresAtMillis;

        void authenticate() {
            authToken = "vault-token-xyz";
            tokenExpiresAtMillis = System.currentTimeMillis() + 200; // a SHORT TTL, for a fast demo
            System.out.println("  [vault] authenticated, token valid until +200ms");
        }

        void renewIfNeeded() {
            if (System.currentTimeMillis() > tokenExpiresAtMillis - 50) { // renew BEFORE actual expiry
                authenticate(); // re-authenticate, mirrors Vault's token renewal API
                System.out.println("  [vault] token renewed proactively");
            }
        }

        String readSecret(String path, String key) {
            renewIfNeeded(); // CALLED on every access -- transparent to the caller
            if (authToken == null) throw new IllegalStateException("not authenticated");
            return secretsByPath.get(path).get(key);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        VaultClient vault = new VaultClient();
        vault.authenticate();

        System.out.println("Read 1: " + vault.readSecret("secret/order-service", "db.password")); // token still fresh

        Thread.sleep(180); // simulate time passing -- token is APPROACHING expiry

        System.out.println("Read 2 (near expiry): " + vault.readSecret("secret/order-service", "db.password")); // triggers renewal automatically
        System.out.println("The application NEVER manually re-authenticated -- renewal happened transparently underneath.");
    }
}
```

**How to run:** `javac LeaseRenewalKeepsAccessValid.java && java LeaseRenewalKeepsAccessValid` (JDK 17+).

Expected output:
```
  [vault] authenticated, token valid until +200ms
Read 1: hunter2
  [vault] authenticated, token valid until +200ms
  [vault] token renewed proactively
Read 2 (near expiry): hunter2
The application NEVER manually re-authenticated -- renewal happened transparently underneath.
```

## 6. Walkthrough

1. **Level 1, the exposed baseline** — `DB_PASSWORD` is a plaintext constant, identical in risk to the plaintext example examined generally in [secrets management & encryption](0222-secrets-management-encryption.md), with no involvement of any secret store at all.
2. **Level 2, authenticate-then-fetch** — `vault.authenticate("order-service-role", ...)` mirrors Vault's AppRole authentication flow, producing an `authToken`; `readSecret` explicitly checks `authToken != null` before proceeding, modeling how a real Vault client refuses to serve secrets to an unauthenticated caller.
3. **Level 2, no plaintext in source** — the only place `"hunter2"` appears in this program is inside `VaultClient.secretsByPath`, standing in for Vault's own encrypted storage rather than anything committed as part of `FetchFromSimulatedVault`'s own logic; `dbPassword`'s value only exists transiently in memory after the authenticated fetch, exactly mirroring how Spring Cloud Vault populates a `@Value`-injected field without that value ever touching a config file.
4. **Level 3, modeling a lease's expiry** — `tokenExpiresAtMillis` is set relative to authentication time, standing in for Vault's real lease-duration mechanism, where every token is valid only for a bounded TTL and must be renewed to remain usable.
5. **Level 3, renewal happening on access, not on a fixed schedule** — `renewIfNeeded` is called at the start of every `readSecret` invocation, checking whether the current time is within 50ms of expiry and re-authenticating if so; this models how Spring Cloud Vault's lease renewal can be triggered around actual usage patterns rather than requiring the application to run its own separate renewal scheduler.
6. **Level 3, the observable renewal event** — the first `readSecret` call happens while the token is still fresh, so no renewal message is printed; after `Thread.sleep(180)` brings the program close to the 200ms TTL, the second `readSecret` call detects the approaching expiry, triggers `authenticate()` again (printing the renewal log line), and *then* returns the secret — from `main`'s perspective, both calls to `readSecret` look identical (a plain method call returning a string), even though the second one silently triggered a full re-authentication underneath, exactly mirroring how Spring Cloud Vault's lease renewal stays entirely invisible to application code reading `@Value`-injected secrets.

## 7. Gotchas & takeaways

> **Gotcha:** if Vault's lease renewal fails (a network partition, an expired root credential, a revoked AppRole), an application relying on a since-expired token will start failing to fetch or refresh secrets — for a long-running service, this can surface much later than the actual root cause, as a sudden secret-access failure with no code change nearby; monitoring Vault connectivity and lease health separately from application-level error logs is important for catching this class of failure early.

- Spring Cloud Vault fetches secrets from HashiCorp Vault and merges them into the application's `Environment`, exposed through the same `@Value`/`@ConfigurationProperties` mechanisms as ordinary configuration.
- It handles authentication (via a configured method like AppRole or Kubernetes service accounts) and lease-based token renewal transparently, so application code never contains Vault-specific logic.
- It's commonly paired with [Spring Cloud Config Server](0231-spring-cloud-config-server.md): structural settings from a Git-backed Config Server, genuine secrets from Vault, both surfaced identically to application beans.
- Renewal happens proactively, before a token actually expires, so ongoing secret access continues without application code noticing anything happened.
- A Vault outage or a failed renewal is a distinct operational failure mode from an ordinary configuration issue, and needs its own monitoring separate from general application error logs to be caught promptly.
