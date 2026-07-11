---
card: spring-cloud
gi: 14
slug: config-server-enableconfigserver
title: "Config Server (@EnableConfigServer)"
---

## 1. What it is

`@EnableConfigServer` turns a Spring Boot application into a Spring Cloud Config Server — an HTTP service that reads configuration from a backend (Git, by default, covered in the next card) and serves it to requesting client applications via a predictable REST API: `/{application}/{profile}/{label}`.

```java
@SpringBootApplication
@EnableConfigServer
class ConfigServerApplication {
    public static void main(String[] args) { SpringApplication.run(ConfigServerApplication.class, args); }
}
// GET http://localhost:8888/payment-service/production
// -> resolved configuration for payment-service, production profile
```

## 2. Why & when

The previous card described centralized configuration conceptually — one shared source, many consuming services. This card introduces the actual server component that makes that concrete: a running Spring Boot application whose entire job is answering "what configuration does service X need, for environment Y" over HTTP, backed by whatever storage mechanism (Git, filesystem, Vault) the following cards cover.

Reach for `@EnableConfigServer` when:

- Building the central configuration service itself — this is a one-time setup per organization or per major deployment environment, not something every service builds.
- You want a uniform, versioned, auditable source every other service's Config Client (a later card) can fetch from via a consistent REST API, regardless of the actual backend storage.
- You need environment-specific configuration resolution (dev vs. staging vs. production) served correctly based on the requesting client's active profile.

## 3. Core concept

```
 @EnableConfigServer application, running on port 8888

 GET /{application}/{profile}                 -- e.g. /payment-service/production
 GET /{application}/{profile}/{label}           -- {label} = a Git branch/tag, defaults to "main"
 GET /{application}-{profile}.yml                -- same data, as raw YAML
 GET /{application}-{profile}.properties          -- same data, as raw .properties

 Request:  GET /payment-service/production
 Response: {
   "name": "payment-service",
   "profiles": ["production"],
   "propertySources": [
     { "name": "...payment-service-production.yml", "source": { "db.pool.size": 50 } },
     { "name": "...application.yml",                  "source": { "db.pool.size": 10, ... } }
   ]
 }
```

The response includes every applicable property source, most-specific first — the client (or the server itself) merges them in that order to compute the final effective configuration.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client requests configuration for a named application and profile, and the Config Server responds with layered property sources">
  <rect x="20" y="45" width="220" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">GET /payment-service/production</text>

  <line x1="240" y1="67" x2="300" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a34)"/>

  <rect x="310" y="45" width="150" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="385" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>

  <line x1="460" y1="67" x2="520" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a34)"/>

  <rect x="530" y="45" width="90" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Git repo</text>

  <defs><marker id="a34" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A client's request identifies the application and profile; the Config Server resolves it against the backend and responds with layered property sources.

## 5. Runnable example

The scenario: a minimal Config Server resolving requests for two services across two profiles, evolving from a bare in-memory config source with no server API around it, to an HTTP-endpoint-style resolver following the `{application}/{profile}` path structure, to full profile-and-application layering producing the same most-specific-first property source ordering a real Config Server returns.

### Level 1 — Basic

Model the underlying config storage, without any request-handling API around it yet.

```java
import java.util.*;

public class ConfigServerLevel1 {
    public static void main(String[] args) {
        Map<String, Map<String, String>> configFiles = new HashMap<>();
        configFiles.put("application", Map.of("db.pool.size", "10"));
        configFiles.put("payment-service-production", Map.of("db.pool.size", "50", "payment.gateway", "stripe-live"));

        // No API yet -- just raw storage, directly accessed.
        System.out.println("Raw file 'application': " + configFiles.get("application"));
        System.out.println("Raw file 'payment-service-production': " + configFiles.get("payment-service-production"));
    }
}
```

How to run: `java ConfigServerLevel1.java`

Configuration exists, but there's no request-handling structure yet — nothing resolves "give me `payment-service`'s config for the `production` profile" into the right combination of files.

### Level 2 — Intermediate

Add a `ConfigServer` that resolves an `{application}/{profile}` request into the correct layered property sources, mirroring the real endpoint's structure.

```java
import java.util.*;

public class ConfigServerLevel2 {
    public static void main(String[] args) {
        ConfigServer server = new ConfigServer();
        server.addFile("application", Map.of("db.pool.size", "10"));
        server.addFile("payment-service-production", Map.of("db.pool.size", "50", "payment.gateway", "stripe-live"));

        ConfigResponse response = server.resolve("payment-service", "production");
        System.out.println("GET /payment-service/production ->");
        for (PropertySource ps : response.propertySources) System.out.println("  " + ps.name + ": " + ps.source);
    }
}

class PropertySource { String name; Map<String, String> source; PropertySource(String name, Map<String, String> source) { this.name = name; this.source = source; } }
class ConfigResponse { String application; List<PropertySource> propertySources; ConfigResponse(String application, List<PropertySource> propertySources) { this.application = application; this.propertySources = propertySources; } }

// Stands in for the @EnableConfigServer HTTP endpoint's resolution logic.
class ConfigServer {
    private final Map<String, Map<String, String>> files = new HashMap<>();
    void addFile(String name, Map<String, String> contents) { files.put(name, contents); }

    ConfigResponse resolve(String application, String profile) {
        List<PropertySource> sources = new ArrayList<>();
        String specific = application + "-" + profile;
        if (files.containsKey(specific)) sources.add(new PropertySource(specific + ".yml", files.get(specific)));
        if (files.containsKey("application")) sources.add(new PropertySource("application.yml", files.get("application")));
        return new ConfigResponse(application, sources);
    }
}
```

How to run: `java ConfigServerLevel2.java`

`resolve("payment-service", "production")` looks for both a service-and-profile-specific file (`payment-service-production`) and the shared `application` file, returning both as ordered property sources — most-specific first — mirroring the real Config Server's response shape.

### Level 3 — Advanced

Add profile-independent per-service files too (`payment-service` alone, applying to every profile), completing the full four-tier precedence a real Config Server resolves: service+profile, service-only, shared+profile, shared-only.

```java
import java.util.*;

public class ConfigServerLevel3 {
    public static void main(String[] args) {
        ConfigServer server = new ConfigServer();
        server.addFile("application", Map.of("db.pool.size", "10", "logging.level", "INFO"));
        server.addFile("payment-service", Map.of("payment.gateway", "stripe-test")); // applies to ALL profiles
        server.addFile("payment-service-production", Map.of("db.pool.size", "50", "payment.gateway", "stripe-live"));

        printResolved(server, "payment-service", "production");
        printResolved(server, "payment-service", "staging"); // no staging-specific file -- falls back further
    }

    static void printResolved(ConfigServer server, String application, String profile) {
        ConfigResponse response = server.resolve(application, profile);
        System.out.println("GET /" + application + "/" + profile + " ->");
        for (PropertySource ps : response.propertySources) System.out.println("  " + ps.name + ": " + ps.source);
        System.out.println("  EFFECTIVE (most-specific wins): " + mergeEffective(response));
    }

    static Map<String, String> mergeEffective(ConfigResponse response) {
        Map<String, String> effective = new HashMap<>();
        for (int i = response.propertySources.size() - 1; i >= 0; i--) { // apply LEAST specific first, most-specific overwrites LAST
            effective.putAll(response.propertySources.get(i).source);
        }
        return effective;
    }
}

class PropertySource { String name; Map<String, String> source; PropertySource(String name, Map<String, String> source) { this.name = name; this.source = source; } }
class ConfigResponse { String application; List<PropertySource> propertySources; ConfigResponse(String application, List<PropertySource> propertySources) { this.application = application; this.propertySources = propertySources; } }

class ConfigServer {
    private final Map<String, Map<String, String>> files = new HashMap<>();
    void addFile(String name, Map<String, String> contents) { files.put(name, contents); }

    ConfigResponse resolve(String application, String profile) {
        List<PropertySource> sources = new ArrayList<>();
        String specific = application + "-" + profile;
        if (files.containsKey(specific)) sources.add(new PropertySource(specific + ".yml", files.get(specific)));
        if (files.containsKey(application)) sources.add(new PropertySource(application + ".yml", files.get(application)));
        if (files.containsKey("application")) sources.add(new PropertySource("application.yml", files.get("application")));
        return new ConfigResponse(application, sources);
    }
}
```

How to run: `java ConfigServerLevel3.java`

For `production`, all three files apply, most-specific first: `payment-service-production` overrides `payment-service`, which overrides `application`. For `staging` — with no `payment-service-staging` file — the resolution falls back to just `payment-service` and `application`, showing how a missing profile-specific file gracefully degrades to broader, less specific sources rather than failing.

## 6. Walkthrough

Execution starts in `main` for Level 3. `printResolved(server, "payment-service", "production")` calls `server.resolve`, which finds all three matching files and returns them ordered from most to least specific.

`mergeEffective` then applies them in *reverse* order — least specific first (`application`, then `payment-service`, then `payment-service-production`) — so each subsequent `putAll` call overwrites any key the earlier, less-specific source also defined:

```
GET /payment-service/production ->
  payment-service-production.yml: {db.pool.size=50, payment.gateway=stripe-live}
  payment-service.yml: {payment.gateway=stripe-test}
  application.yml: {db.pool.size=10, logging.level=INFO}
  EFFECTIVE (most-specific wins): {db.pool.size=50, payment.gateway=stripe-live, logging.level=INFO}
```

`db.pool.size` and `payment.gateway` both end up with the `payment-service-production` values, since that source is applied last (most specific), while `logging.level` — never overridden by either more-specific file — retains its `application.yml` value. For `staging`, with no matching profile-specific file, the resolution silently falls back to just `payment-service` and `application`:

```
GET /payment-service/staging ->
  payment-service.yml: {payment.gateway=stripe-test}
  application.yml: {db.pool.size=10, logging.level=INFO}
  EFFECTIVE (most-specific wins): {payment.gateway=stripe-test, db.pool.size=10, logging.level=INFO}
```

This exact precedence — service+profile beats service-only beats shared+profile beats shared-only — is what a real `@EnableConfigServer` application computes on every incoming request, before returning the full ordered list of property sources for the requesting Config Client (a later card) to merge, exactly as `mergeEffective` does here.

## 7. Gotchas & takeaways

> Gotcha: the Config Server's default backend is Git, and by default it clones/pulls the repository on *every* incoming request unless caching or a refresh interval is configured — for a Config Server handling frequent requests from many service instances, this can generate significant, avoidable load against the backing Git host; production setups typically configure a local clone with periodic (not per-request) refresh.

> Gotcha: `@EnableConfigServer` alone doesn't secure the exposed configuration endpoints — anyone who can reach the server's HTTP port can request any service's configuration, including potentially sensitive values, unless authentication is layered on top (a later card in this section covers Config Server security specifically).

- `@EnableConfigServer` turns a Spring Boot application into an HTTP service resolving `{application}/{profile}` requests against a configurable backend, returning layered, most-specific-first property sources.
- Precedence resolves from most to least specific: service+profile, service-only, shared+profile, shared-only — a missing more-specific file gracefully falls back to broader sources rather than failing.
- This card covers the server component conceptually; the following cards cover the actual backend storage options (Git, filesystem, Vault, and others) the server can be configured to read from.
- The Config Server exposes potentially sensitive configuration over HTTP by default — securing access to it is a separate, necessary concern covered later in this section.
