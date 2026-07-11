---
card: spring-data
gi: 178
slug: repositoryrestresource
title: "@RepositoryRestResource"
---

## 1. What it is

`@RepositoryRestResource` customizes how Spring Data REST exposes a specific repository — its resource path, the name used in HAL relation links, and (via `exported = false`) whether it's exposed at all. It's the annotation-level control over the auto-generation the previous card introduced.

```java
@RepositoryRestResource(path = "clients", collectionResourceRel = "clients")
interface CustomerRepository extends JpaRepository<Customer, String> { }
// Now exposed at /clients instead of the default /customers
```

## 2. Why & when

Left entirely on defaults, Spring Data REST derives a repository's exposed path from the entity's class name — `CustomerRepository` becomes `/customers`. That default is usually fine, but sometimes the desired public API path doesn't match the Java class name, or a repository shouldn't be exposed publicly at all. `@RepositoryRestResource` is the annotation for both cases.

Reach for `@RepositoryRestResource` when:

- The public REST path should differ from the entity's default pluralized class name (`/clients` instead of `/customers`, for API versioning or naming consistency reasons).
- A repository exists purely for internal use and should never be reachable as a REST endpoint — `exported = false`.
- The HAL relation name used in `_links` (e.g. `_links.clients` instead of `_links.customers`) needs to match a client's expectations.

## 3. Core concept

```
 Default (no annotation):
   interface CustomerRepository extends JpaRepository<Customer, String> { }
   -> exposed at /customers, relation name "customers"

 @RepositoryRestResource(path = "clients", collectionResourceRel = "clients")
   -> exposed at /clients, relation name "clients"

 @RepositoryRestResource(exported = false)
   -> NOT exposed as REST at all -- repository still works internally, just has no HTTP endpoint
```

The annotation overrides individual pieces of the default naming derivation, or opts a repository out of exposure entirely, without touching the entity or the repository's actual query methods.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same repository can be exposed under a default path, a custom path, or not exposed at all">
  <rect x="20" y="20" width="180" height="100" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="42" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">No annotation</text>
  <text x="110" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">/customers</text>

  <rect x="230" y="20" width="180" height="100" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">path="clients"</text>
  <text x="320" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">/clients</text>

  <rect x="440" y="20" width="180" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="42" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">exported=false</text>
  <text x="530" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">no endpoint at all</text>
</svg>

The same underlying repository can be exposed under its default path, a customized path, or not exposed as REST at all.

## 5. Runnable example

The scenario: controlling how a `CustomerRepository` is exposed, evolving from the default path derivation, to a custom path and relation name, to a second, internal-only repository (`AuditLogRepository`) that's excluded from REST exposure entirely while remaining fully usable inside the application.

### Level 1 — Basic

Model default path derivation — the class-name-based convention Spring Data REST falls back to without any annotation.

```java
public class RepositoryRestResourceLevel1 {
    public static void main(String[] args) {
        String path = derivePath("CustomerRepository", null); // no @RepositoryRestResource
        System.out.println("Exposed at: /" + path);
    }

    // Stands in for Spring Data REST's default resource-path derivation from a repository's entity name.
    static String derivePath(String repositoryClassName, String explicitPath) {
        if (explicitPath != null) return explicitPath;
        String entityName = repositoryClassName.replace("Repository", ""); // "Customer"
        return entityName.substring(0, 1).toLowerCase() + entityName.substring(1) + "s"; // "customers"
    }
}
```

How to run: `java RepositoryRestResourceLevel1.java`

`derivePath` mirrors Spring Data REST's default naming: strip `Repository` from the class name, lowercase the first letter, pluralize — `CustomerRepository` becomes `/customers` automatically, with no configuration needed.

### Level 2 — Intermediate

Add `@RepositoryRestResource`-style overrides for the path and HAL relation name.

```java
import java.util.*;

public class RepositoryRestResourceLevel2 {
    public static void main(String[] args) {
        RepositoryRestConfig defaultConfig = new RepositoryRestConfig("CustomerRepository", null, null);
        RepositoryRestConfig customConfig = new RepositoryRestConfig("CustomerRepository", "clients", "clients");

        System.out.println("Default: " + defaultConfig.describe());
        System.out.println("Customized: " + customConfig.describe());
    }
}

// Stands in for @RepositoryRestResource(path = ..., collectionResourceRel = ...).
class RepositoryRestConfig {
    private final String repositoryClassName, path, collectionResourceRel;
    RepositoryRestConfig(String repositoryClassName, String path, String collectionResourceRel) {
        this.repositoryClassName = repositoryClassName; this.path = path; this.collectionResourceRel = collectionResourceRel;
    }
    String describe() {
        String entityName = repositoryClassName.replace("Repository", "");
        String defaultName = entityName.substring(0, 1).toLowerCase() + entityName.substring(1) + "s";
        String effectivePath = (path != null) ? path : defaultName;
        String effectiveRel = (collectionResourceRel != null) ? collectionResourceRel : defaultName;
        return "path=/" + effectivePath + ", relation=\"" + effectiveRel + "\"";
    }
}
```

How to run: `java RepositoryRestResourceLevel2.java`

`customConfig` overrides both `path` and `collectionResourceRel` to `"clients"`, while `defaultConfig` falls back to the derived `"customers"` for both — the annotation's attributes each independently override one piece of the default naming, falling back to the convention wherever left unset.

### Level 3 — Advanced

Add `exported = false` for an internal-only repository, and show it alongside an exposed one in a combined registry — modeling how Spring Data REST decides, per repository, whether to generate an endpoint at all.

```java
import java.util.*;

public class RepositoryRestResourceLevel3 {
    public static void main(String[] args) {
        List<RepositoryRestConfig> repositories = List.of(
            new RepositoryRestConfig("CustomerRepository", "clients", "clients", true),
            new RepositoryRestConfig("OrderRepository", null, null, true),
            new RepositoryRestConfig("AuditLogRepository", null, null, false) // exported = false -- internal only
        );

        System.out.println("Generated REST endpoints:");
        for (RepositoryRestConfig repo : repositories) {
            if (repo.exported) System.out.println("  " + repo.describe());
            else System.out.println("  (skipped: " + repo.repositoryClassName + " is exported=false)");
        }
    }
}

class RepositoryRestConfig {
    final String repositoryClassName, path, collectionResourceRel; final boolean exported;
    RepositoryRestConfig(String repositoryClassName, String path, String collectionResourceRel, boolean exported) {
        this.repositoryClassName = repositoryClassName; this.path = path;
        this.collectionResourceRel = collectionResourceRel; this.exported = exported;
    }
    String describe() {
        String entityName = repositoryClassName.replace("Repository", "");
        String defaultName = entityName.substring(0, 1).toLowerCase() + entityName.substring(1) + "s";
        String effectivePath = (path != null) ? path : defaultName;
        return "/" + effectivePath;
    }
}
```

How to run: `java RepositoryRestResourceLevel3.java`

`AuditLogRepository` is skipped entirely from the generated endpoint list because `exported = false` — it remains a perfectly usable Spring Data repository internally (autowired into services, queried normally), it simply never gets an HTTP surface, which is exactly the tool for repositories that should stay implementation detail.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three repository configs are built: `CustomerRepository` with an explicit path/relation override, `OrderRepository` with defaults, and `AuditLogRepository` explicitly marked `exported = false`.

The loop checks each repository's `exported` flag before deciding whether to print an endpoint line:

```
Generated REST endpoints:
  /clients
  /orders
  (skipped: AuditLogRepository is exported=false)
```

In a real Spring Boot application, this decision happens once at startup, when Spring Data REST scans the application context for repository beans: each one either gets a `RepositoryRestController`-equivalent mapping registered for it, or is skipped, based on its `@RepositoryRestResource(exported = ...)` value (defaulting to `true` if the annotation is absent entirely). A request to `GET /audit-logs` in this configuration would return a plain 404 — Spring Data REST never registered a handler for it, not because access was denied.

## 7. Gotchas & takeaways

> Gotcha: `exported = false` on the *repository* stops the collection/item endpoints, but doesn't automatically hide the entity if it's still reachable as a *linked association* from another exposed repository — a `Customer`'s `@OneToMany` to `AuditLogEntry`, if not separately configured, can still leak audit log data through `/customers/{id}/auditLogEntries` even with the repository itself unexported.

> Gotcha: changing a repository's exposed `path` is a breaking change for any existing client relying on the old URL — treat `@RepositoryRestResource(path = ...)` changes with the same care as any other public API contract change, since HAL's hypermedia navigation doesn't retroactively fix clients that bookmarked the old URL directly.

- `@RepositoryRestResource` overrides individual pieces of Spring Data REST's default naming convention — `path` for the URL, `collectionResourceRel` for the HAL relation name — falling back to convention for anything left unset.
- `exported = false` opts a repository out of REST exposure entirely, while leaving it fully functional for internal use within the application.
- The decision to expose or hide a repository is made once, at startup, based on this annotation (or its absence, which defaults to exported).
- Unexported repositories can still leak through associations from other exposed repositories — exposure control needs to consider the whole entity graph, not just the top-level repository.
