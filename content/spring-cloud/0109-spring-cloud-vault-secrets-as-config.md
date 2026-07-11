---
card: spring-cloud
gi: 109
slug: spring-cloud-vault-secrets-as-config
title: "Spring Cloud Vault (secrets as config)"
---

## 1. What it is

Spring Cloud Vault integrates HashiCorp Vault into Spring's externalized configuration mechanism the same way Spring Cloud Config integrates a Git repository — secrets stored in Vault (database credentials, API keys, certificates) are fetched at application startup (or refreshed later) and bound directly onto `@Value`/`@ConfigurationProperties` fields, exactly like any other property source, so application code never constructs a Vault client or calls its API directly.

```properties
spring.cloud.vault.uri=https://vault.example.com:8200
spring.cloud.vault.token=${VAULT_TOKEN}
spring.cloud.vault.kv.enabled=true
spring.cloud.vault.kv.backend=secret
spring.cloud.vault.kv.default-context=order-service
```

```java
@Value("${database.password}")
String databasePassword; // pulled from Vault at startup, looks identical to any other externalized property
```

## 2. Why & when

Hardcoding secrets (database passwords, third-party API keys) into a properties file — even one pulled from Config Server — puts sensitive material in a Git repository's history indefinitely, readable by anyone with repository access, and impossible to fully purge once committed. Vault exists specifically to store secrets outside of any version-controlled configuration, with fine-grained access policies, an audit log of every secret access, and (for dynamic secrets, covered in a later card) credentials that don't even exist until requested and expire automatically. Spring Cloud Vault's contribution is making all of this invisible to application code: a bean that would otherwise read `${database.password}` from a properties file reads the exact same property key, and Spring Cloud Vault transparently resolves it from Vault instead — the property source changes, the application code consuming it does not.

Reach for Spring Cloud Vault when:

- Secrets need to live outside of Git-tracked configuration entirely — database credentials, encryption keys, third-party API tokens — while still being consumable through the same `@Value`/`@ConfigurationProperties` mechanism the rest of an application's configuration already uses.
- Centralized secret management, access auditing, or fine-grained per-application access policies matter — Vault provides all of these at the secret-storage layer, which a plain properties file (even an encrypted one) does not.
- Combining static configuration (Config Server, covered in earlier cards) with secret configuration (Vault) in one unified property resolution — both can be layered together, with Vault-sourced secrets and Config-Server-sourced properties both simply appearing as ordinary Spring `Environment` properties to application code.

## 3. Core concept

```
 traditional (INSECURE) approach:
   application.properties (in Git):  database.password=hunter2   <- committed to version control, forever

 Spring Cloud Vault approach:
   application.properties (in Git):  (no password here at all)
   Vault (NOT in Git):               secret/order-service -> {database.password: "hunter2"}
        |
        v (at startup, Spring Cloud Vault fetches from Vault)
   Spring Environment:               database.password=hunter2   <- resolved from Vault, bound to @Value normally
```

From the perspective of a `@Value("${database.password}")` field, the property's origin (a properties file, Config Server, or Vault) is completely invisible — all three are just different `PropertySource` implementations feeding the same unified `Environment`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At startup the application fetches secrets from a Vault server which are merged into the Spring Environment alongside ordinary properties so a Value annotated field cannot tell whether its value came from Vault or a plain properties file">
  <rect x="20" y="20" width="170" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Vault server</text>
  <text x="105" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">secret/order-service</text>

  <rect x="250" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="340" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Environment</text>
  <text x="340" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">merged property sources</text>

  <rect x="480" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="550" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Value field</text>
  <text x="550" y="56" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">unaware of origin</text>

  <defs><marker id="a109" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="43" x2="250" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a109)"/>
  <line x1="430" y1="43" x2="480" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a109)"/>
</svg>

Vault-sourced secrets flow into the exact same unified property resolution mechanism every other configuration source already uses.

## 5. Runnable example

The scenario: a small property-resolution system where secrets fetched from a simulated Vault are merged with plain properties into one unified environment, consumed by application code with no awareness of which source any given property came from. Start with plain property resolution, then add a Vault-backed source merged in, then add a case where a secret is deliberately excluded from a plain properties fallback, proving the merge, not the individual source, is what a `@Value`-equivalent lookup actually sees.

### Level 1 — Basic

Plain property resolution — the baseline before Vault is introduced.

```java
import java.util.*;

public class VaultConfigLevel1 {
    static Map<String, String> plainProperties = Map.of(
            "server.port", "8080",
            "app.name", "order-service"
    );

    static String resolve(String key) { return plainProperties.get(key); }

    public static void main(String[] args) {
        System.out.println("server.port=" + resolve("server.port"));
        System.out.println("app.name=" + resolve("app.name"));
    }
}
```

How to run: `java VaultConfigLevel1.java`

`resolve` looks up a key from one flat source — this is the pre-Vault baseline: no secrets are involved yet, only ordinary, non-sensitive configuration.

### Level 2 — Intermediate

Add a simulated Vault source and merge it with plain properties into one unified lookup — `resolve` becomes source-agnostic.

```java
import java.util.*;

public class VaultConfigLevel2 {
    static Map<String, String> plainProperties = Map.of(
            "server.port", "8080",
            "app.name", "order-service"
    );

    // stands in for a fetch against Vault's KV secrets engine at path secret/order-service
    static Map<String, String> fetchFromVault(String path) {
        System.out.println("fetching secrets from Vault path: " + path);
        return Map.of("database.password", "vault-managed-secret-xyz", "api.key", "sk-abc123");
    }

    static Map<String, String> buildUnifiedEnvironment() {
        Map<String, String> merged = new HashMap<>(plainProperties);
        merged.putAll(fetchFromVault("secret/order-service")); // Vault-sourced entries merged in ALONGSIDE plain ones
        return merged;
    }

    public static void main(String[] args) {
        Map<String, String> environment = buildUnifiedEnvironment();

        // resolve() has NO idea which properties came from Vault and which came from the plain source
        for (String key : List.of("server.port", "database.password", "api.key")) {
            System.out.println(key + "=" + environment.get(key));
        }
    }
}
```

How to run: `java VaultConfigLevel2.java`

`environment` is a single merged map — `database.password` and `api.key` came from `fetchFromVault`, while `server.port` came from `plainProperties`, but the final lookup loop treats all three identically, exactly mirroring how a `@Value("${database.password}")` field in a real Spring application has no code-level distinction between a Vault-sourced and a properties-file-sourced value.

### Level 3 — Advanced

Add a case where a required secret is deliberately absent from Vault (simulating a misconfigured Vault path or missing secret), and fail fast with a clear error rather than silently proceeding with a `null` credential — a realistic and important production concern.

```java
import java.util.*;

public class VaultConfigLevel3 {
    static Map<String, String> plainProperties = Map.of(
            "server.port", "8080",
            "app.name", "order-service"
    );

    static Map<String, String> fetchFromVault(String path, boolean simulateMissingSecret) {
        System.out.println("fetching secrets from Vault path: " + path);
        if (simulateMissingSecret) {
            return Map.of("api.key", "sk-abc123"); // database.password is MISSING this time
        }
        return Map.of("database.password", "vault-managed-secret-xyz", "api.key", "sk-abc123");
    }

    static Map<String, String> buildUnifiedEnvironment(boolean simulateMissingSecret) {
        Map<String, String> merged = new HashMap<>(plainProperties);
        merged.putAll(fetchFromVault("secret/order-service", simulateMissingSecret));
        return merged;
    }

    // models a required-property check a real application performs at startup (fail fast, don't run with null secrets)
    static String requireProperty(Map<String, String> environment, String key) {
        String value = environment.get(key);
        if (value == null) {
            throw new IllegalStateException("required property '" + key + "' not found -- check Vault path and secret name");
        }
        return value;
    }

    public static void main(String[] args) {
        Map<String, String> healthyEnvironment = buildUnifiedEnvironment(false);
        System.out.println("healthy startup: database.password=" + requireProperty(healthyEnvironment, "database.password"));

        try {
            Map<String, String> brokenEnvironment = buildUnifiedEnvironment(true);
            requireProperty(brokenEnvironment, "database.password"); // this Vault fetch was missing the secret
        } catch (IllegalStateException e) {
            System.out.println("startup would FAIL here: " + e.getMessage());
        }
    }
}
```

How to run: `java VaultConfigLevel3.java`

The first `buildUnifiedEnvironment(false)` call produces a complete environment, and `requireProperty` succeeds; the second call, with `simulateMissingSecret=true`, produces an environment missing `database.password` entirely, so `requireProperty` throws `IllegalStateException` with a message pointing directly at the likely cause (the Vault path or secret name) — mirroring how a real Spring Boot application should fail fast at startup with a clear diagnostic when a required secret can't be resolved from Vault, rather than starting up successfully and failing later, more confusingly, the first time that credential is actually used.

## 6. Walkthrough

Trace the failure path in Level 3.

1. `buildUnifiedEnvironment(true)` calls `fetchFromVault("secret/order-service", true)`, which, because `simulateMissingSecret` is `true`, returns a map containing only `"api.key"` — `"database.password"` is deliberately absent, modeling a real scenario where a secret was never written to that Vault path, or the application's Vault policy doesn't grant read access to it.
2. `merged.putAll(...)` merges this incomplete map into `merged`, which already contains `plainProperties`' two entries — the resulting `brokenEnvironment` has three keys total (`server.port`, `app.name`, `api.key`), and `database.password` is simply not one of them.
3. `requireProperty(brokenEnvironment, "database.password")` is called — `environment.get("database.password")` returns `null` (`Map.get` on a missing key returns `null`, it doesn't throw), so `value` is `null`.
4. The `if (value == null)` check is `true`, so `requireProperty` throws `IllegalStateException` with the message `"required property 'database.password' not found -- check Vault path and secret name"` — this exception propagates out of the `try` block in `main`.
5. The `catch (IllegalStateException e)` block catches it and prints the diagnostic — in a real application, an equivalent failure during Spring's own context startup would prevent the application from starting at all, which is the correct behavior for a genuinely required secret: better a clear, immediate startup failure than a running application silently missing a critical credential.

```
buildUnifiedEnvironment(true) -> Vault fetch returns {api.key: ...}  (database.password MISSING)
merged = {server.port, app.name, api.key}                            (3 keys, NOT 4)
requireProperty(merged, "database.password")
   environment.get("database.password") -> null
   throw IllegalStateException("required property 'database.password' not found...")
caught in main -> clear diagnostic printed instead of a confusing later NullPointerException
```

## 7. Gotchas & takeaways

> **Gotcha:** Vault-sourced properties are typically fetched once at application startup by default — a secret rotated in Vault after the application has already started won't automatically be picked up without either an explicit refresh mechanism (Spring Cloud Bus's `/actuator/busrefresh`, covered in earlier cards, or Vault-specific lease renewal, covered in a later card) or a restart. Assuming Vault-backed configuration is always perfectly current, the moment it changes in Vault, is a common and incorrect assumption without one of those refresh mechanisms explicitly wired up.

- Spring Cloud Vault's core value is making secret resolution invisible to application code — a `@Value`/`@ConfigurationProperties` field bound to a Vault-sourced property looks and behaves identically to one bound to any other property source.
- Keeping secrets out of version control entirely (rather than encrypting them within a Git-tracked properties file) is the fundamental security improvement Vault provides over even an encrypted-properties-in-Git approach, since Vault also adds access policies and audit logging that a Git repository alone cannot.
- Failing fast and clearly when a required secret can't be resolved (as Level 3 modeled) is essential — a missing secret should prevent a misconfigured application from starting at all, not allow it to run with a `null` or default credential that fails, confusingly, only when that credential is first actually used.
- Later cards in this section cover the different kinds of Vault backends beyond simple key-value secrets (dynamic database credentials, PKI certificates), authentication methods for the application-to-Vault connection itself, and lease renewal for credentials that expire automatically.
