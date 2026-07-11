---
card: spring-cloud
gi: 17
slug: vault-backend
title: "Vault backend"
---

## 1. What it is

The Vault backend sources Config Server configuration from HashiCorp Vault — a secrets management system — instead of Git or the filesystem, specifically for values that shouldn't live in a source-controlled config repository at all: database passwords, API keys, TLS certificates.

```yaml
spring:
  cloud:
    config:
      server:
        vault:
          host: vault.internal
          port: 8200
          scheme: https
          backend: secret
```

## 2. Why & when

Git and native backends (the previous two cards) are well suited to *ordinary* configuration — pool sizes, feature flags, timeouts. Secrets are a fundamentally different category: even a private Git repository's commit history is a poor place for a database password, since anyone with read access to the repo can see it, forever, in every historical commit, even after it's "changed." Vault exists specifically to store and control access to that category of value, with features Git was never designed for — access policies, audit logging of every secret read, and automatic secret rotation.

Reach for the Vault backend when:

- Configuration includes genuine secrets — credentials, tokens, keys — that shouldn't be readable by everyone with access to the config repository.
- You need fine-grained access control over *who* (which service, which environment) can read *which* specific secrets, beyond what repository-level Git permissions provide.
- Secret rotation needs to happen without a corresponding Git commit — Vault can issue short-lived, automatically expiring credentials that Git-based configuration has no equivalent mechanism for.

## 3. Core concept

```
 Git-backed application.yml (NOT secrets):
   db.pool.size: 10
   feature.newCheckout: true

 Vault (secrets, NOT in Git):
   secret/payment-service:
     db.password: "s3cr3t-rotated-weekly"
     stripe.apiKey: "sk_live_..."

 Config Server merges BOTH sources for a single client request:
   GET /payment-service/production
   -> combines Git-backed application.yml/payment-service.yml
      WITH Vault-backed secret/payment-service
   -> client receives ONE unified configuration, from TWO different backends
```

Ordinary configuration and secrets can be served from entirely different backends simultaneously, merged into one response for the requesting client — this composition is covered more generally in the next card on composite backends.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Config Server merges non-secret configuration from Git with secrets from Vault into one unified client response">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Git (non-secret config)</text>

  <rect x="20" y="90" width="180" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Vault (secrets)</text>

  <line x1="200" y1="40" x2="280" y2="70" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a37)"/>
  <line x1="200" y1="110" x2="280" y2="80" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a37)"/>

  <rect x="290" y="55" width="150" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="365" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>

  <line x1="440" y1="77" x2="500" y2="77" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a37)"/>

  <rect x="510" y="55" width="110" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">client</text>

  <defs><marker id="a37" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Non-secret configuration and secrets flow from separate backends, merged by the Config Server into one response.

## 5. Runnable example

The scenario: a payment service needing both ordinary configuration and a secret database credential, evolving from mixing a secret directly into the same source as ordinary config (the anti-pattern), to separating them into two distinct backends, to a token-scoped access control demonstration showing why Vault's model is fundamentally different from Git's.

### Level 1 — Basic

Show the anti-pattern baseline: a secret stored alongside ordinary configuration in the same source, with no special access control.

```java
import java.util.*;

public class VaultBackendLevel1 {
    public static void main(String[] args) {
        Map<String, String> mixedConfig = new HashMap<>();
        mixedConfig.put("db.pool.size", "50");
        mixedConfig.put("db.password", "s3cr3t123"); // a real secret, sitting right next to ordinary config

        // ANYONE who can read this "config repo" can now see the database password, forever,
        // in every historical version, with no separate access control on JUST this one value.
        System.out.println("Full config (including secret, mixed in): " + mixedConfig);
    }
}
```

How to run: `java VaultBackendLevel1.java`

`db.password` sits in the exact same data structure as `db.pool.size` — no distinction, no separate access control, exactly the situation that makes rotating or restricting access to that one value awkward and risky.

### Level 2 — Intermediate

Separate ordinary configuration from secrets into two distinct sources, merged only at request time.

```java
import java.util.*;

public class VaultBackendLevel2 {
    public static void main(String[] args) {
        GitSource gitSource = new GitSource();
        gitSource.put("payment-service", Map.of("db.pool.size", "50", "feature.newCheckout", "true"));

        VaultSource vaultSource = new VaultSource();
        vaultSource.put("payment-service", Map.of("db.password", "s3cr3t123", "stripe.apiKey", "sk_live_abc"));

        Map<String, String> merged = mergeForClient(gitSource, vaultSource, "payment-service");
        System.out.println("Merged config for payment-service: " + merged);
    }

    static Map<String, String> mergeForClient(GitSource git, VaultSource vault, String serviceId) {
        Map<String, String> merged = new HashMap<>();
        merged.putAll(git.get(serviceId));
        merged.putAll(vault.get(serviceId)); // secrets merged in, from a COMPLETELY separate backend
        return merged;
    }
}

class GitSource {
    private final Map<String, Map<String, String>> data = new HashMap<>();
    void put(String serviceId, Map<String, String> content) { data.put(serviceId, content); }
    Map<String, String> get(String serviceId) { return data.getOrDefault(serviceId, Map.of()); }
}

class VaultSource {
    private final Map<String, Map<String, String>> data = new HashMap<>();
    void put(String serviceId, Map<String, String> content) { data.put(serviceId, content); }
    Map<String, String> get(String serviceId) { return data.getOrDefault(serviceId, Map.of()); }
}
```

How to run: `java VaultBackendLevel2.java`

`gitSource` and `vaultSource` are entirely independent data structures — `db.password` never appears anywhere near `gitSource`'s data, which means Git's commit history, if this were real, would never contain it; only `mergeForClient`, at request-serving time, combines both into the response a specific requesting client actually receives.

### Level 3 — Advanced

Add token-scoped access control on the Vault side: different requesting services can only read secrets scoped to their own path — a genuine access-control model Git-based configuration has no native equivalent for.

```java
import java.util.*;

public class VaultBackendLevel3 {
    public static void main(String[] args) {
        VaultSource vault = new VaultSource();
        vault.put("secret/payment-service", Map.of("db.password", "payment-db-pass"), "payment-service-token");
        vault.put("secret/inventory-service", Map.of("db.password", "inventory-db-pass"), "inventory-service-token");

        System.out.println("payment-service reading its OWN secret: "
            + tryRead(vault, "secret/payment-service", "payment-service-token"));

        System.out.println("payment-service trying to read inventory-service's secret: "
            + tryRead(vault, "secret/inventory-service", "payment-service-token")); // WRONG token for this path
    }

    static String tryRead(VaultSource vault, String path, String presentedToken) {
        try {
            return vault.read(path, presentedToken).toString();
        } catch (SecurityException e) {
            return "DENIED: " + e.getMessage();
        }
    }
}

// Stands in for Vault's path-scoped access control -- each secret path requires its OWN authorized token.
class VaultSource {
    private final Map<String, Map<String, String>> secrets = new HashMap<>();
    private final Map<String, String> authorizedTokenForPath = new HashMap<>();

    void put(String path, Map<String, String> content, String authorizedToken) {
        secrets.put(path, content);
        authorizedTokenForPath.put(path, authorizedToken);
    }

    Map<String, String> read(String path, String presentedToken) {
        String required = authorizedTokenForPath.get(path);
        if (!required.equals(presentedToken)) {
            throw new SecurityException("token not authorized for path " + path);
        }
        return secrets.get(path);
    }
}
```

How to run: `java VaultBackendLevel3.java`

`payment-service-token` successfully reads `secret/payment-service` (its own scoped path) but is rejected when used to try reading `secret/inventory-service` — Vault's real access-control model works this way, scoping tokens/policies to specific secret paths, so a compromised or misconfigured payment-service credential can't be used to read secrets belonging to a completely different service, a level of granular access control a shared Git repository's file-level or repo-level permissions typically can't express as precisely.

## 6. Walkthrough

Execution starts in `main` for Level 3. Two secrets are stored, each requiring its own specific authorized token to read. `tryRead(vault, "secret/payment-service", "payment-service-token")` calls `vault.read`, which compares the presented token against the path's required token — they match, so the secret is returned:

```
payment-service reading its OWN secret: {db.password=payment-db-pass}
```

`tryRead(vault, "secret/inventory-service", "payment-service-token")` presents the *wrong* token for that path — `authorizedTokenForPath.get("secret/inventory-service")` is `"inventory-service-token"`, which doesn't equal the presented `"payment-service-token"` — so `read` throws `SecurityException`, caught and reported by `tryRead`:

```
payment-service trying to read inventory-service's secret: DENIED: token not authorized for path secret/inventory-service
```

In a real deployment, each service authenticates to Vault with its own identity (often via a Kubernetes service account, an AppRole, or a similar mechanism) and Vault's policies determine exactly which secret paths that identity can read — the Config Server, acting on behalf of the requesting client, uses that same access-controlled channel, so even the Config Server itself only retrieves secrets it's been granted access to, and every read is logged in Vault's audit trail.

## 7. Gotchas & takeaways

> Gotcha: if the Config Server's own Vault access is overly broad (a single token with access to every service's secrets, for convenience), it becomes a single point of compromise for *all* secrets — the fine-grained access control Vault is capable of only provides real protection if it's actually configured per-service rather than granted wholesale to the Config Server.

> Gotcha: unlike Git-backed configuration, Vault secrets typically don't have the same kind of easily browsable "history" — Vault has its own versioning (for the KV v2 secrets engine) and audit logging, but it's a different mechanism from `git log`, and teams moving secrets out of Git need to learn Vault's own tooling for viewing what changed and when.

- The Vault backend serves secrets — credentials, keys, tokens — that shouldn't live in a source-controlled Git repository, where they'd be permanently visible in commit history to anyone with repo access.
- A Config Server can combine a Git backend (ordinary configuration) with a Vault backend (secrets) simultaneously, merging both into one unified response per client request.
- Vault's access control is scoped per secret path, letting different services be restricted to only the secrets that actually belong to them — a level of granularity Git repository permissions typically can't match.
- The security value of Vault's fine-grained access control depends on it actually being configured that way — an overly broad token granted to the Config Server undermines the whole model.
