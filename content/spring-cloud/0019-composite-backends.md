---
card: spring-cloud
gi: 19
slug: composite-backends
title: "Composite backends"
---

## 1. What it is

A composite backend configures the Config Server to consult *multiple* backends for a single request, merging their results — most commonly Git for ordinary configuration plus Vault for secrets (the combination the Vault card touched on), but generalized to any combination of the supported backend types, each contributing its own layer to the final response.

```yaml
spring:
  cloud:
    config:
      server:
        composite:
          - type: git
            uri: https://github.com/example-org/config-repo
          - type: vault
            host: vault.internal
            port: 8200
```

## 2. Why & when

The Vault card showed Git and Vault being combined conceptually. Composite backends formalize that: rather than picking exactly one backend for the entire Config Server, the `composite` configuration explicitly lists several, each queried for every request, with their results merged in the order listed. This is the actual mechanism behind "ordinary config from Git, secrets from Vault" — and it generalizes to other combinations too, like a shared native backend for defaults plus a per-team Git repository for overrides.

Reach for composite backends when:

- Different categories of configuration genuinely belong in different systems (Vault for secrets, Git for everything else) but clients should still receive one unified response, not need to query multiple Config Server endpoints themselves.
- Migrating from one backend to another gradually — running both the old and new backend simultaneously, with the new one's values taking precedence, until the migration is verified complete.
- Different teams or organizational units maintain their own configuration sources, and a composite setup merges them into a consistent view for consuming applications.

## 3. Core concept

```
 composite:
   - type: git    (listed FIRST -- lower precedence)
   - type: vault  (listed SECOND -- higher precedence, can override git values for the same key)

 GET /payment-service/production
   1. Query Git backend  -> { db.pool.size: 50, feature.newCheckout: true }
   2. Query Vault backend -> { db.password: "s3cr3t", db.pool.size: 999 }  (Vault ALSO happens to define this key)
   3. Merge in LISTED order, LATER entries take precedence for the SAME key:
        { db.pool.size: 999, feature.newCheckout: true, db.password: "s3cr3t" }
```

Each configured backend contributes a property source; when the same key appears in more than one, the backend listed later in the composite configuration wins.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two backends are queried in sequence and their results merged in listed order, with the later backend taking precedence on key conflicts">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">1. Git backend</text>

  <rect x="20" y="90" width="180" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">2. Vault backend</text>

  <line x1="200" y1="40" x2="280" y2="70" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a39)"/>
  <line x1="200" y1="110" x2="280" y2="80" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a39)"/>

  <rect x="290" y="55" width="200" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">merged (later wins)</text>

  <defs><marker id="a39" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Backends are queried in configured order and merged, with later-listed backends overriding earlier ones on key conflicts.

## 5. Runnable example

The scenario: a Config Server composing Git and Vault backends, evolving from querying each backend separately with no merge logic, to composite merging honoring listed-order precedence, to a gradual-migration scenario using composite ordering to prefer a new backend's values while still falling back to an old one for keys not yet migrated.

### Level 1 — Basic

Query two backends independently, with no merge logic connecting them yet.

```java
import java.util.*;

public class CompositeBackendLevel1 {
    public static void main(String[] args) {
        Backend git = new Backend(Map.of("db.pool.size", "50", "feature.newCheckout", "true"));
        Backend vault = new Backend(Map.of("db.password", "s3cr3t"));

        System.out.println("Git result: " + git.query());
        System.out.println("Vault result: " + vault.query());
        // Two SEPARATE results -- a client would need to query and merge these itself.
    }
}

class Backend {
    private final Map<String, String> data;
    Backend(Map<String, String> data) { this.data = data; }
    Map<String, String> query() { return data; }
}
```

How to run: `java CompositeBackendLevel1.java`

Each backend is queried in isolation — nothing here combines them into one unified response, leaving that work to whoever consumes both results, exactly the gap composite configuration closes.

### Level 2 — Intermediate

Add a `CompositeConfigServer` that queries a list of backends in order and merges their results.

```java
import java.util.*;

public class CompositeBackendLevel2 {
    public static void main(String[] args) {
        Backend git = new Backend(Map.of("db.pool.size", "50", "feature.newCheckout", "true"));
        Backend vault = new Backend(Map.of("db.password", "s3cr3t"));

        CompositeConfigServer server = new CompositeConfigServer(List.of(git, vault)); // Git FIRST, Vault SECOND
        Map<String, String> merged = server.resolve();
        System.out.println("Composite result: " + merged);
    }
}

class Backend {
    private final Map<String, String> data;
    Backend(Map<String, String> data) { this.data = data; }
    Map<String, String> query() { return data; }
}

// Stands in for spring.cloud.config.server.composite: a list of backends, queried and merged in order.
class CompositeConfigServer {
    private final List<Backend> backends;
    CompositeConfigServer(List<Backend> backends) { this.backends = backends; }

    Map<String, String> resolve() {
        Map<String, String> merged = new HashMap<>();
        for (Backend backend : backends) merged.putAll(backend.query()); // LATER backends override EARLIER ones
        return merged;
    }
}
```

How to run: `java CompositeBackendLevel2.java`

`resolve` iterates `backends` in list order, calling `putAll` for each one's results — since `putAll` overwrites existing keys, any backend listed later in `backends` wins on a conflicting key, exactly mirroring the `composite:` YAML list's ordering semantics.

### Level 3 — Advanced

Model a gradual backend migration: an "old" JDBC-style backend and a "new" Git-style backend, composited with the new backend listed last (highest precedence), so already-migrated keys resolve from the new source while not-yet-migrated keys still fall back to the old one.

```java
import java.util.*;

public class CompositeBackendLevel3 {
    public static void main(String[] args) {
        Backend oldJdbcBackend = new Backend(Map.of(
            "db.pool.size", "10",             // NOT yet migrated -- still comes from the old backend
            "payment.gateway", "stripe-test",  // NOT yet migrated
            "feature.newCheckout", "false"      // migrated value is STALE here, but will be overridden
        ));
        Backend newGitBackend = new Backend(Map.of(
            "feature.newCheckout", "true"        // ALREADY migrated -- new backend has the current value
        ));

        // Old backend FIRST (lower precedence), new backend LAST (higher precedence, wins on overlap).
        CompositeConfigServer server = new CompositeConfigServer(List.of(oldJdbcBackend, newGitBackend));
        Map<String, String> resolved = server.resolve();

        System.out.println("Resolved during migration: " + resolved);
        System.out.println("feature.newCheckout came from the NEW backend: " + resolved.get("feature.newCheckout").equals("true"));
        System.out.println("db.pool.size still falls back to the OLD backend: " + resolved.get("db.pool.size"));
    }
}

class Backend {
    private final Map<String, String> data;
    Backend(Map<String, String> data) { this.data = data; }
    Map<String, String> query() { return data; }
}

class CompositeConfigServer {
    private final List<Backend> backends;
    CompositeConfigServer(List<Backend> backends) { this.backends = backends; }
    Map<String, String> resolve() {
        Map<String, String> merged = new HashMap<>();
        for (Backend backend : backends) merged.putAll(backend.query());
        return merged;
    }
}
```

How to run: `java CompositeBackendLevel3.java`

`feature.newCheckout` exists in both backends with different values — `"false"` in the old, stale one, `"true"` in the new one — and since `newGitBackend` is listed *last*, its value wins in the merge. `db.pool.size` and `payment.gateway` exist only in the old backend, so they pass through unaffected, giving a working blend of "already migrated" and "not yet migrated" configuration during the transition period.

## 6. Walkthrough

Execution starts in `main` for Level 3. `oldJdbcBackend` carries three keys, one of which (`feature.newCheckout`) has a stale value that's since been migrated to `newGitBackend`, which carries only that one, now-current key.

`server.resolve()` iterates `[oldJdbcBackend, newGitBackend]` in order — first merging in all three of the old backend's keys, then merging in the new backend's single key, which overwrites the stale `feature.newCheckout` value already present:

```
Resolved during migration: {db.pool.size=10, payment.gateway=stripe-test, feature.newCheckout=true}
feature.newCheckout came from the NEW backend: true
db.pool.size still falls back to the OLD backend: 10
```

This exact pattern — old backend first, new backend last, both configured simultaneously — is a practical way to migrate a Config Server's backend gradually, key by key: as more configuration keys are moved to the new backend, the merged result automatically prefers the new values for whatever's been migrated, while everything not yet moved continues resolving correctly from the old source, with no client-visible disruption and no need to migrate every key in one atomic cutover.

## 7. Gotchas & takeaways

> Gotcha: composite backend ordering determines precedence silently — a backend accidentally listed in the wrong position (old backend last instead of first, say) inverts the intended precedence with no error or warning; the merge just quietly resolves the "wrong" value for any overlapping key, which can be subtle to diagnose without carefully checking the `composite:` list order.

> Gotcha: querying multiple backends for every single request multiplies the Config Server's per-request work and failure surface — if one backend in the composite list is slow or temporarily unreachable, that latency or failure affects every request, even for keys that would have resolved fine from a different, healthy backend in the list, unless the specific backend type's own resilience/caching behavior mitigates it.

- Composite backends let a Config Server query and merge multiple configuration sources for a single request, most commonly Git for ordinary configuration and Vault for secrets.
- Precedence follows listed order — backends listed later override earlier ones for any key present in more than one source.
- This mechanism supports gradual backend migrations: listing the new backend last lets already-migrated keys take effect immediately while unmigrated keys continue falling back to the old source.
- Backend list ordering is a silent precedence decision — getting it backwards produces no error, just quietly wrong resolved values for overlapping keys.
