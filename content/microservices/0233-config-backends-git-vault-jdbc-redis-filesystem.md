---
card: microservices
gi: 233
slug: config-backends-git-vault-jdbc-redis-filesystem
title: "Config backends: Git, Vault, JDBC, Redis, filesystem"
---

## 1. What it is

A config backend is the actual storage system a [Spring Cloud Config Server](0231-spring-cloud-config-server.md) reads configuration from — Git, HashiCorp Vault, a JDBC database, Redis, or the local filesystem are all supported, pluggable options, each with different tradeoffs, selected via the Config Server's own configuration rather than requiring different code to consume them.

## 2. Why & when

Different backends suit different needs: Git gives configuration the review-and-history guarantees of [configuration as code](0221-configuration-as-code.md), and is the default and most common choice for structural, non-secret settings; Vault is purpose-built for [secrets](0236-spring-cloud-vault-for-secrets.md), with encryption and fine-grained access control that Git-as-plaintext-files can't match; a JDBC or Redis backend suits configuration that needs to be queried or updated programmatically at a rate or in a way that a Git commit-per-change workflow would make impractical; and a local filesystem backend is useful mainly for local development or testing, where a full Git repository is unnecessary overhead. The key architectural point is that the Config Server abstracts over all of these — consuming services calling the Config Server's HTTP API never need to know or care which backend is actually storing the data they're fetching.

Choose Git as the default for most structural configuration; add Vault specifically for secrets; reach for JDBC or Redis when configuration needs programmatic, high-frequency updates outside a commit-based workflow; use the filesystem backend for local development convenience, not production.

## 3. Core concept

Every backend implements the same underlying contract — given an application name and profile, return the matching configuration properties — and the Config Server's HTTP-facing behavior is identical regardless of which backend implementation is plugged in underneath; only the storage and retrieval mechanism differs.

```java
interface ConfigBackend { Map<String, String> fetch(String application, String profile); }

class GitConfigBackend implements ConfigBackend {
    public Map<String, String> fetch(String application, String profile) { /* git pull, read file, parse */ return Map.of(); }
}
class VaultConfigBackend implements ConfigBackend {
    public Map<String, String> fetch(String application, String profile) { /* authenticate, read encrypted secret path */ return Map.of(); }
}
class JdbcConfigBackend implements ConfigBackend {
    public Map<String, String> fetch(String application, String profile) { /* SELECT key, value FROM config WHERE app=? AND profile=? */ return Map.of(); }
}
// the CONFIG SERVER's HTTP-facing behavior is IDENTICAL no matter which ConfigBackend implementation is active
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four different backend types -- Git, Vault, JDBC, filesystem -- each implement the same fetch contract, and the Config Server sits on top exposing an identical HTTP API regardless of which backend is plugged in" >
  <rect x="20" y="115" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="85" y="139" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Git</text>

  <rect x="170" y="115" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="235" y="139" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Vault</text>

  <rect x="320" y="115" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="385" y="139" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">JDBC / Redis</text>

  <rect x="470" y="115" width="130" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="535" y="139" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Filesystem</text>

  <rect x="170" y="30" width="300" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="57" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Config Server -- IDENTICAL HTTP API</text>

  <line x1="85" y1="113" x2="280" y2="77" stroke="#8b949e" marker-end="url(#arr233)"/>
  <line x1="235" y1="113" x2="300" y2="77" stroke="#8b949e" marker-end="url(#arr233)"/>
  <line x1="385" y1="113" x2="345" y2="77" stroke="#8b949e" marker-end="url(#arr233)"/>
  <line x1="535" y1="113" x2="380" y2="77" stroke="#8b949e" marker-end="url(#arr233)"/>

  <defs>
    <marker id="arr233" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every backend plugs into the same interface; consumers of the Config Server never see which one is active underneath.

## 5. Runnable example

Scenario: a `ConfigBackend` abstraction that starts with only one hard-coded backend implementation available (unable to swap storage strategy), extends to support two interchangeable backends (Git-style and JDBC-style) selected by configuration, and finally demonstrates swapping the active backend at construction time with zero change to the calling code that fetches configuration — mirroring how a real Config Server's backend choice is a deployment-time decision, invisible to consuming services.

### Level 1 — Basic

```java
// File: SingleHardCodedBackend.java -- ONE backend implementation,
// directly instantiated; swapping storage strategy means EDITING this code.
import java.util.*;

public class SingleHardCodedBackend {
    static class GitConfigBackend {
        Map<String, String> fetch(String application, String profile) {
            return Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders"); // simulates a git-pulled YAML file
        }
    }

    public static void main(String[] args) {
        GitConfigBackend backend = new GitConfigBackend(); // HARD-CODED to Git
        System.out.println("Fetched: " + backend.fetch("order-service", "production"));
        System.out.println("Switching to a different backend means rewriting THIS class.");
    }
}
```

**How to run:** `javac SingleHardCodedBackend.java && java SingleHardCodedBackend` (JDK 17+).

### Level 2 — Intermediate

```java
// File: PluggableBackendInterface.java -- TWO backends implement the
// SAME interface; the Config Server logic depends only on the
// INTERFACE, not on which concrete backend is active.
import java.util.*;

public class PluggableBackendInterface {
    interface ConfigBackend { Map<String, String> fetch(String application, String profile); }

    static class GitConfigBackend implements ConfigBackend {
        public Map<String, String> fetch(String application, String profile) {
            return Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders", "retry.count", "3");
        }
    }

    static class JdbcConfigBackend implements ConfigBackend {
        public Map<String, String> fetch(String application, String profile) {
            // simulates: SELECT key, value FROM config WHERE app = ? AND profile = ?
            return Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders", "feature.flag.new-checkout", "true");
        }
    }

    // the CONFIG SERVER'S own logic -- depends ONLY on the ConfigBackend interface
    static Map<String, String> serveRequest(ConfigBackend backend, String application, String profile) {
        return backend.fetch(application, profile);
    }

    public static void main(String[] args) {
        System.out.println("Serving via Git backend: " + serveRequest(new GitConfigBackend(), "order-service", "production"));
        System.out.println("Serving via JDBC backend: " + serveRequest(new JdbcConfigBackend(), "order-service", "production"));
        System.out.println("SAME serveRequest method, DIFFERENT backend -- neither backend's own code changed.");
    }
}
```

**How to run:** `javac PluggableBackendInterface.java && java PluggableBackendInterface` (JDK 17+).

Expected output:
```
Serving via Git backend: {db.url=jdbc:postgresql://prod-db:5432/orders, retry.count=3}
Serving via JDBC backend: {db.url=jdbc:postgresql://prod-db:5432/orders, feature.flag.new-checkout=true}
SAME serveRequest method, DIFFERENT backend -- neither backend's own code changed.
```

### Level 3 — Advanced

```java
// File: DeploymentTimeBackendSelection.java -- the ACTIVE backend is
// chosen ONCE, at "deployment time" (here, a config value read at
// startup), and CONSUMING code never sees or cares which one is active.
import java.util.*;

public class DeploymentTimeBackendSelection {
    interface ConfigBackend { Map<String, String> fetch(String application, String profile); }

    static class GitConfigBackend implements ConfigBackend {
        public Map<String, String> fetch(String application, String profile) {
            return Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders");
        }
    }
    static class VaultConfigBackend implements ConfigBackend {
        public Map<String, String> fetch(String application, String profile) {
            return Map.of("db.password", "***decrypted-from-vault***"); // secrets, NEVER stored in Git
        }
    }
    static class CompositeConfigBackend implements ConfigBackend { // a Config Server can COMBINE multiple backends
        List<ConfigBackend> backends;
        CompositeConfigBackend(List<ConfigBackend> backends) { this.backends = backends; }
        public Map<String, String> fetch(String application, String profile) {
            Map<String, String> merged = new HashMap<>();
            for (ConfigBackend b : backends) merged.putAll(b.fetch(application, profile)); // ALL backends contribute
            return merged;
        }
    }

    // deployment-time choice: "spring.cloud.config.server.git.uri" AND "spring.cloud.config.server.vault.*" BOTH configured
    static ConfigBackend selectBackendForDeployment(String deploymentMode) {
        return switch (deploymentMode) {
            case "production" -> new CompositeConfigBackend(List.of(new GitConfigBackend(), new VaultConfigBackend())); // BOTH combined
            case "local-dev" -> new GitConfigBackend(); // secrets not needed locally
            default -> throw new IllegalArgumentException("unknown deployment mode: " + deploymentMode);
        };
    }

    static Map<String, String> serveRequest(ConfigBackend backend, String application, String profile) {
        return backend.fetch(application, profile);
    }

    public static void main(String[] args) {
        ConfigBackend productionBackend = selectBackendForDeployment("production");
        System.out.println("production: " + serveRequest(productionBackend, "order-service", "production"));

        ConfigBackend devBackend = selectBackendForDeployment("local-dev");
        System.out.println("local-dev: " + serveRequest(devBackend, "order-service", "development"));

        System.out.println("serveRequest's code is IDENTICAL in both calls -- only the backend, chosen ONCE at deployment time, differs.");
    }
}
```

**How to run:** `javac DeploymentTimeBackendSelection.java && java DeploymentTimeBackendSelection` (JDK 17+).

Expected output:
```
production: {db.url=jdbc:postgresql://prod-db:5432/orders, db.password=***decrypted-from-vault***}
local-dev: {db.url=jdbc:postgresql://prod-db:5432/orders}
serveRequest's code is IDENTICAL in both calls -- only the backend, chosen ONCE at deployment time, differs.
```

## 6. Walkthrough

1. **Level 1, the tight coupling** — `GitConfigBackend` is instantiated directly by concrete type in `main`; there is no abstraction separating "fetch configuration" from "fetch configuration specifically from Git," so any change of storage strategy requires editing this exact class.
2. **Level 2, the shared contract** — `ConfigBackend` declares a single `fetch` method that both `GitConfigBackend` and `JdbcConfigBackend` implement independently, and `serveRequest` is written entirely against this interface, never referencing either concrete class by name.
3. **Level 2, interchangeability demonstrated** — calling `serveRequest` with a `GitConfigBackend` instance and then again with a `JdbcConfigBackend` instance runs the identical `serveRequest` method body both times, producing different results only because the underlying backend object differs — proving `serveRequest` genuinely doesn't depend on which backend is plugged in.
4. **Level 3, combining backends** — `CompositeConfigBackend` itself implements `ConfigBackend` while internally delegating to a list of other `ConfigBackend` instances and merging their results, modeling a real Config Server configured with both a Git backend (for structural settings) and a Vault backend (for secrets) simultaneously — a common production pattern rather than a purely either/or choice.
5. **Level 3, choosing once at deployment time** — `selectBackendForDeployment` is the *only* place in this program that decides which concrete backend(s) are active, based on a single `deploymentMode` string; this mirrors how a real Config Server's backend is chosen through its own configuration (`spring.cloud.config.server.git.*`, `.vault.*`, etc.), set once when the Config Server itself is deployed, not something individual consuming services have any visibility into.
6. **Level 3, consumers stay backend-agnostic** — both calls to `serveRequest` in `main` use the exact same method with no branching on which backend was selected; a consuming service (in the real system, a client hitting the Config Server's HTTP API) is even further removed from this decision than `serveRequest` is here — it only ever sees the final, merged JSON response, with no visibility into Git, Vault, JDBC, or any other backend having been involved in producing it.

## 7. Gotchas & takeaways

> **Gotcha:** combining multiple backends (as `CompositeConfigBackend` models) introduces its own precedence question — if two backends define the same key differently, which one wins depends on the order they're merged in, exactly the [configuration precedence](0226-configuration-precedence-overrides.md) concern generalized to backend combination; a real multi-backend Config Server setup needs this merge order documented and deliberate, not left to whatever order the backends happen to be configured in.

- Config backends (Git, Vault, JDBC, Redis, filesystem) are pluggable storage implementations behind a Config Server's fetch contract, each with different tradeoffs around review history, secret handling, and update frequency.
- The Config Server's HTTP-facing behavior stays identical regardless of which backend (or combination of backends) is actually storing the underlying data.
- Git suits structural, reviewable configuration; Vault suits secrets; JDBC/Redis suit programmatically or frequently updated configuration; filesystem suits local development.
- Multiple backends can be combined (structural settings from Git, secrets from Vault), which introduces its own merge-precedence question that needs to be deliberate and documented.
- Consuming services calling the Config Server's HTTP API never need to know which backend served their configuration — the abstraction is complete from the client's perspective.
