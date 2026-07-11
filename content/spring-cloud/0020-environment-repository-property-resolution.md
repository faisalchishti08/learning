---
card: spring-cloud
gi: 20
slug: environment-repository-property-resolution
title: "Environment repository & property resolution"
---

## 1. What it is

`EnvironmentRepository` is the Config Server's internal Java interface that every backend (Git, native, Vault, JDBC, and the rest) implements — the actual abstraction point behind everything the previous cards described conceptually. Its single core method, `findOne(application, profile, label)`, returns an `Environment` object: an ordered list of `PropertySource`s, which is what actually gets serialized into the JSON response a Config Client receives.

```java
public interface EnvironmentRepository {
    Environment findOne(String application, String profile, String label);
}
```

## 2. Why & when

Every previous card in this section described a specific backend's behavior at a conceptual level. This card looks at the actual seam in the code where all of them meet: `EnvironmentRepository` is the interface the Config Server's HTTP layer calls, and every backend — Git, native, Vault, JDBC, Redis, S3, composite — is simply a different implementation of this one interface. Understanding this clarifies why composite backends (previous card) work at all: a `CompositeEnvironmentRepository` is just another `EnvironmentRepository` implementation that internally delegates to several others and merges their results.

Reach for understanding `EnvironmentRepository` directly when:

- Debugging exactly how a Config Server resolves a request — the resolution logic described across the previous cards is entirely implemented behind this one method.
- Writing a custom backend for a configuration source none of the built-in backends support — implementing `EnvironmentRepository` yourself is the documented extension point.
- Understanding property source ordering in a returned response — `Environment.getPropertySources()` returns them most-specific-first, and that ordering is what every client-side merge (including the Config Client's own resolution) depends on.

## 3. Core concept

```
 interface EnvironmentRepository {
     Environment findOne(String application, String profile, String label);
 }

 class Environment {
     String name;                                 -- the requested application
     List<String> profiles;
     String label;
     List<PropertySource> propertySources;           -- ORDERED, most-specific FIRST
 }

 class PropertySource {
     String name;                                   -- e.g. "payment-service-production.yml"
     Map<Object, Object> source;                      -- the actual key-value pairs
 }

 GitEnvironmentRepository implements EnvironmentRepository { ... }
 VaultEnvironmentRepository implements EnvironmentRepository { ... }
 CompositeEnvironmentRepository implements EnvironmentRepository {
     // internally holds a List<EnvironmentRepository>, delegates to each, concatenates their propertySources
 }
```

`Environment` is the actual data structure serialized as the Config Server's JSON response — every backend's job is producing one correctly, in the right order.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An HTTP request calls findOne on whichever EnvironmentRepository implementation is configured, returning an ordered Environment object">
  <rect x="20" y="45" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">HTTP request</text>

  <line x1="170" y1="67" x2="230" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a40)"/>

  <rect x="240" y="45" width="200" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">EnvironmentRepository.findOne</text>

  <line x1="440" y1="67" x2="500" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a40)"/>

  <rect x="510" y="45" width="110" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Environment</text>

  <defs><marker id="a40" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every request ultimately calls `findOne` on some `EnvironmentRepository` implementation, returning the ordered `Environment` that becomes the HTTP response.

## 5. Runnable example

The scenario: implementing the `EnvironmentRepository` contract directly, evolving from a minimal single-backend implementation, to a composite implementation built by delegating to several inner repositories (making explicit what the previous card's composite backend does internally), to a custom repository for a configuration source not covered by any built-in backend — demonstrating the actual extension point.

### Level 1 — Basic

Implement `EnvironmentRepository` for a single, minimal in-memory backend.

```java
import java.util.*;

public class EnvironmentRepoLevel1 {
    public static void main(String[] args) {
        EnvironmentRepository repo = new InMemoryEnvironmentRepository(Map.of(
            "application", Map.of("db.pool.size", "10"),
            "payment-service-production", Map.of("db.pool.size", "50")
        ));

        Environment env = repo.findOne("payment-service", "production", "main");
        System.out.println("Environment for payment-service/production:");
        for (PropertySource ps : env.propertySources) System.out.println("  " + ps.name + ": " + ps.source);
    }
}

class PropertySource { String name; Map<String, String> source; PropertySource(String name, Map<String, String> source) { this.name = name; this.source = source; } }
class Environment { String name; List<PropertySource> propertySources; Environment(String name, List<PropertySource> propertySources) { this.name = name; this.propertySources = propertySources; } }

interface EnvironmentRepository { Environment findOne(String application, String profile, String label); }

class InMemoryEnvironmentRepository implements EnvironmentRepository {
    private final Map<String, Map<String, String>> files;
    InMemoryEnvironmentRepository(Map<String, Map<String, String>> files) { this.files = files; }

    public Environment findOne(String application, String profile, String label) {
        List<PropertySource> sources = new ArrayList<>();
        String specific = application + "-" + profile;
        if (files.containsKey(specific)) sources.add(new PropertySource(specific, files.get(specific)));
        if (files.containsKey("application")) sources.add(new PropertySource("application", files.get("application")));
        return new Environment(application, sources);
    }
}
```

How to run: `java EnvironmentRepoLevel1.java`

`InMemoryEnvironmentRepository.findOne` implements the exact same contract a real `GitEnvironmentRepository` implements — accept `application`/`profile`/`label`, return an `Environment` with ordered `PropertySource`s.

### Level 2 — Intermediate

Implement a `CompositeEnvironmentRepository`, making explicit what the previous card's composite backend does internally: delegate to several inner repositories and concatenate their results.

```java
import java.util.*;

public class EnvironmentRepoLevel2 {
    public static void main(String[] args) {
        EnvironmentRepository gitRepo = new InMemoryEnvironmentRepository(
            Map.of("payment-service-production", Map.of("db.pool.size", "50", "feature.newCheckout", "true")));
        EnvironmentRepository vaultRepo = new InMemoryEnvironmentRepository(
            Map.of("payment-service-production", Map.of("db.password", "s3cr3t")));

        EnvironmentRepository composite = new CompositeEnvironmentRepository(List.of(gitRepo, vaultRepo));
        Environment env = composite.findOne("payment-service", "production", "main");

        System.out.println("Composite Environment:");
        for (PropertySource ps : env.propertySources) System.out.println("  " + ps.name + ": " + ps.source);
    }
}

class PropertySource { String name; Map<String, String> source; PropertySource(String name, Map<String, String> source) { this.name = name; this.source = source; } }
class Environment { String name; List<PropertySource> propertySources; Environment(String name, List<PropertySource> propertySources) { this.name = name; this.propertySources = propertySources; } }

interface EnvironmentRepository { Environment findOne(String application, String profile, String label); }

class InMemoryEnvironmentRepository implements EnvironmentRepository {
    private final Map<String, Map<String, String>> files;
    InMemoryEnvironmentRepository(Map<String, Map<String, String>> files) { this.files = files; }
    public Environment findOne(String application, String profile, String label) {
        String specific = application + "-" + profile;
        List<PropertySource> sources = new ArrayList<>();
        if (files.containsKey(specific)) sources.add(new PropertySource(specific, files.get(specific)));
        return new Environment(application, sources);
    }
}

// Implements the SAME interface, but delegates to a list of inner EnvironmentRepositories.
class CompositeEnvironmentRepository implements EnvironmentRepository {
    private final List<EnvironmentRepository> delegates;
    CompositeEnvironmentRepository(List<EnvironmentRepository> delegates) { this.delegates = delegates; }

    public Environment findOne(String application, String profile, String label) {
        List<PropertySource> combined = new ArrayList<>();
        for (EnvironmentRepository delegate : delegates) {
            combined.addAll(delegate.findOne(application, profile, label).propertySources);
        }
        return new Environment(application, combined);
    }
}
```

How to run: `java EnvironmentRepoLevel2.java`

`CompositeEnvironmentRepository` implements `EnvironmentRepository` itself, so it's usable anywhere a single backend would be — its `findOne` calls `findOne` on each delegate in turn and concatenates their `propertySources` lists, exactly the mechanism behind the previous card's `composite:` YAML configuration.

### Level 3 — Advanced

Implement a genuinely custom `EnvironmentRepository` for a configuration source none of the built-in backends cover — an internal HTTP-based configuration service — demonstrating the actual documented extension point for organizations with a bespoke config source.

```java
import java.util.*;

public class EnvironmentRepoLevel3 {
    public static void main(String[] args) {
        InternalHttpConfigService internalService = new InternalHttpConfigService();
        internalService.publish("payment-service", "production", Map.of("feature.betaCheckout", "true"));

        // A CUSTOM EnvironmentRepository, wrapping a configuration source Spring Cloud Config never anticipated.
        EnvironmentRepository customRepo = new CustomHttpEnvironmentRepository(internalService);

        Environment env = customRepo.findOne("payment-service", "production", "main");
        System.out.println("Custom-backend Environment:");
        for (PropertySource ps : env.propertySources) System.out.println("  " + ps.name + ": " + ps.source);
    }
}

class PropertySource { String name; Map<String, String> source; PropertySource(String name, Map<String, String> source) { this.name = name; this.source = source; } }
class Environment { String name; List<PropertySource> propertySources; Environment(String name, List<PropertySource> propertySources) { this.name = name; this.propertySources = propertySources; } }
interface EnvironmentRepository { Environment findOne(String application, String profile, String label); }

// An entirely bespoke, pre-existing internal service -- NOT one of Spring Cloud Config's built-in backends.
class InternalHttpConfigService {
    private final Map<String, Map<String, String>> published = new HashMap<>();
    void publish(String application, String profile, Map<String, String> values) {
        published.put(application + ":" + profile, values);
    }
    Map<String, String> fetch(String application, String profile) {
        return published.getOrDefault(application + ":" + profile, Map.of());
    }
}

// The custom extension point: adapt a bespoke source into the standard EnvironmentRepository contract.
class CustomHttpEnvironmentRepository implements EnvironmentRepository {
    private final InternalHttpConfigService service;
    CustomHttpEnvironmentRepository(InternalHttpConfigService service) { this.service = service; }

    public Environment findOne(String application, String profile, String label) {
        Map<String, String> values = service.fetch(application, profile);
        PropertySource source = new PropertySource(application + "-" + profile + " (internal-http)", values);
        return new Environment(application, List.of(source));
    }
}
```

How to run: `java EnvironmentRepoLevel3.java`

`CustomHttpEnvironmentRepository` adapts `InternalHttpConfigService` — a configuration source with no relationship to Git, Vault, or any other built-in backend — into the standard `EnvironmentRepository` contract; registered as a Spring bean in a real application, this is exactly how an organization plugs a bespoke configuration source into Spring Cloud Config Server without needing the framework to natively understand that source at all.

## 6. Walkthrough

Execution starts in `main` for Level 3. `internalService.publish(...)` stores a single config entry under the composed key `"payment-service:production"`. `customRepo.findOne("payment-service", "production", "main")` is called.

Inside `findOne`, `service.fetch("payment-service", "production")` retrieves the published values, and they're wrapped into a single `PropertySource` named to indicate its origin (`"payment-service-production (internal-http)"`), then packaged into an `Environment`:

```
Custom-backend Environment:
  payment-service-production (internal-http): {feature.betaCheckout=true}
```

The `label` parameter (`"main"`) is accepted by `findOne` but not actually used in this simplified example — a real custom implementation might use it to select a specific version or snapshot from the internal service, the same way the Git backend uses it to select a branch or tag. In a real Spring Cloud Config Server, registering a bean of this custom `EnvironmentRepository` type (instead of, or alongside, the built-in ones) is genuinely sufficient — the Config Server's HTTP-handling layer calls whatever `EnvironmentRepository` bean(s) are configured, with no awareness of, or special-casing for, which specific implementation is doing the actual work.

## 7. Gotchas & takeaways

> Gotcha: `PropertySource` ordering within the returned `Environment` is significant and must be most-specific-first for the standard client-side merge (an earlier card's precedence rules) to behave correctly — a custom `EnvironmentRepository` that returns sources in the wrong order silently produces incorrect effective configuration for any overlapping keys, with no error surfaced anywhere.

> Gotcha: `findOne` is called on every incoming request by default (unless caching is layered on top, as the Git backend typically does) — a custom implementation that performs an expensive operation (a slow external API call, a large database query) inside `findOne` directly impacts the latency of every single Config Server request for that application, making caching an important consideration for any non-trivial custom backend.

- `EnvironmentRepository` is the actual interface every Config Server backend implements — `findOne(application, profile, label)` returning an `Environment` of ordered `PropertySource`s.
- `CompositeEnvironmentRepository` is just another implementation of the same interface, delegating to and merging results from several inner repositories — explaining how composite backends actually work.
- Implementing `EnvironmentRepository` directly is the documented extension point for integrating a bespoke configuration source with no built-in backend support.
- Property source ordering (most-specific-first) is a hard requirement for correct downstream merging — a custom implementation must preserve it, and performance (caching an expensive lookup) is a real consideration since `findOne` runs per request by default.
