---
card: spring-cloud
gi: 24
slug: config-client-importing-config-via-spring-config-import
title: "Config Client (importing config via spring.config.import)"
---

## 1. What it is

The Config Client is the consuming side of everything this section has covered: a Spring Boot application declares `spring.config.import=configserver:http://config-server:8888` in its `application.yml`, and Spring Boot's own configuration loading machinery fetches, merges, and applies the Config Server's response as if it were just another local property source — closing the loop from server to client with a single line of configuration.

```yaml
# application.yml -- in the CONSUMING application (e.g. payment-service)
spring:
  application:
    name: payment-service
  config:
    import: "configserver:http://config-server:8888"
  profiles:
    active: production
```

## 2. Why & when

Every earlier card in this section covered the server side: how configuration is stored, resolved, layered, encrypted, secured. This final card closes the loop with the actual client-side integration point — how an ordinary Spring Boot application (a `payment-service`, say) actually pulls all of that in. `spring.config.import` is the modern mechanism for this, replacing the legacy bootstrap-context approach from earlier in this Spring Cloud module — it fits directly into Spring Boot's own standard configuration import mechanism, alongside things like importing another local YAML file.

Reach for `spring.config.import=configserver:...` when:

- Any Spring Boot application needs to fetch its configuration from a centralized Config Server, rather than relying solely on locally bundled `application.yml`.
- You want Config Server-sourced properties merged seamlessly with local configuration, using Spring Boot's normal precedence rules — no special bootstrap-phase handling required.
- Combined with `@RefreshScope` and the `/actuator/refresh` endpoint (earlier Spring Cloud Context cards), for configuration that can update live without a restart.

## 3. Core concept

```
 application.yml:
   spring.application.name: payment-service
   spring.config.import: "configserver:http://config-server:8888"
   spring.profiles.active: production

 On startup, Spring Boot's config-loading machinery:
   1. reads spring.application.name and spring.profiles.active from local application.yml
   2. sees spring.config.import -- fetches from:
        GET http://config-server:8888/payment-service/production
   3. merges the fetched propertySources INTO the application's own Environment,
      following the SAME most-specific-first precedence covered throughout this section
   4. application startup continues, with EVERY @Value/@ConfigurationProperties
      seeing the FULLY merged configuration -- local AND remote, combined
```

`spring.config.import` slots the Config Server fetch directly into Spring Boot's own configuration-loading sequence — from the rest of the application's perspective, there's no distinction between a locally defined property and one that arrived from the Config Server.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application's local config and a fetched remote config both merge into one Environment during normal Spring Boot startup">
  <rect x="20" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">local application.yml</text>

  <rect x="20" y="90" width="200" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="120" y="115" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Config Server (fetched)</text>

  <line x1="220" y1="40" x2="290" y2="70" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a44)"/>
  <line x1="220" y1="110" x2="290" y2="80" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a44)"/>

  <rect x="300" y="55" width="220" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="410" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">merged Environment</text>

  <defs><marker id="a44" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Local and Config Server-fetched configuration merge into one `Environment` during standard Spring Boot startup — indistinguishable to the rest of the application afterward.

## 5. Runnable example

The scenario: a payment service starting up and consuming Config Server configuration, evolving from local-only configuration with no Config Server involved, to a full `spring.config.import`-style fetch merged with local properties, to a full startup simulation showing exactly what a `@Value`-injected field would resolve to once local and remote sources are properly merged.

### Level 1 — Basic

Show local-only configuration — the baseline before any Config Client integration.

```java
import java.util.*;

public class ConfigClientLevel1 {
    public static void main(String[] args) {
        Map<String, String> localApplicationYml = Map.of(
            "spring.application.name", "payment-service",
            "spring.profiles.active", "production",
            "server.port", "8081"
        );
        // No remote config fetched at all -- db.pool.size, feature flags, etc. are simply UNAVAILABLE here.
        System.out.println("Local-only config: " + localApplicationYml);
        System.out.println("db.pool.size: " + localApplicationYml.getOrDefault("db.pool.size", "NOT SET"));
    }
}
```

How to run: `java ConfigClientLevel1.java`

`db.pool.size` (and every other centrally-managed value from earlier cards in this section) is simply unavailable — this application only knows what's bundled in its own local `application.yml`.

### Level 2 — Intermediate

Add a simulated Config Server fetch, triggered by a `spring.config.import`-style declaration, and merge its result into the local configuration.

```java
import java.util.*;

public class ConfigClientLevel2 {
    public static void main(String[] args) {
        Map<String, String> localApplicationYml = new HashMap<>(Map.of(
            "spring.application.name", "payment-service",
            "spring.profiles.active", "production",
            "server.port", "8081"
        ));

        // spring.config.import: "configserver:http://config-server:8888"
        String applicationName = localApplicationYml.get("spring.application.name");
        String activeProfile = localApplicationYml.get("spring.profiles.active");
        Map<String, String> fetchedFromConfigServer = fetchFromConfigServer(applicationName, activeProfile);

        Map<String, String> merged = new HashMap<>(fetchedFromConfigServer); // remote FIRST (lower precedence)
        merged.putAll(localApplicationYml);                                    // local OVERRIDES remote, same as bootstrap card

        System.out.println("Merged Environment: " + merged);
    }

    static Map<String, String> fetchFromConfigServer(String application, String profile) {
        System.out.println("GET http://config-server:8888/" + application + "/" + profile);
        return Map.of("db.pool.size", "50", "payment.gateway", "stripe-live");
    }
}
```

How to run: `java ConfigClientLevel2.java`

`fetchFromConfigServer` simulates exactly what `spring.config.import=configserver:...` triggers during real Spring Boot startup — an HTTP call to the server, using `spring.application.name`/`spring.profiles.active` to build the request path — and the result is merged with local properties taking precedence, consistent with the precedence rules established in the earlier bootstrap-context card.

### Level 3 — Advanced

Simulate a full startup sequence, including a `@Value`-style property injection resolving against the fully merged configuration — showing that, from application code's perspective, there's no visible distinction between a local and a remote-sourced property.

```java
import java.util.*;

public class ConfigClientLevel3 {
    public static void main(String[] args) {
        Map<String, String> localApplicationYml = new HashMap<>(Map.of(
            "spring.application.name", "payment-service",
            "spring.profiles.active", "production",
            "server.port", "8081",
            "db.pool.size", "5" // ALSO defined locally -- will this or the remote value win?
        ));

        Map<String, String> fetchedFromConfigServer = fetchFromConfigServer(
            localApplicationYml.get("spring.application.name"), localApplicationYml.get("spring.profiles.active"));

        Environment environment = buildEnvironment(fetchedFromConfigServer, localApplicationYml);

        // Application code -- e.g. a @Value("${db.pool.size}") field -- resolves through the SAME merged Environment.
        DatabaseConfig databaseConfig = new DatabaseConfig(environment);
        System.out.println("Application startup complete.");
        System.out.println("Resolved db.pool.size for connection pool: " + databaseConfig.poolSize);
        System.out.println("Resolved payment.gateway: " + environment.get("payment.gateway"));
    }

    static Map<String, String> fetchFromConfigServer(String application, String profile) {
        return Map.of("db.pool.size", "50", "payment.gateway", "stripe-live");
    }

    static Environment buildEnvironment(Map<String, String> remote, Map<String, String> local) {
        Map<String, String> merged = new HashMap<>(remote);
        merged.putAll(local); // local wins on any overlapping key -- matches real Spring Boot precedence
        return new Environment(merged);
    }
}

class Environment {
    private final Map<String, String> properties;
    Environment(Map<String, String> properties) { this.properties = properties; }
    String get(String key) { return properties.get(key); }
}

// Stands in for a @Component reading @Value("${db.pool.size}") -- application code, unaware of WHERE the value came from.
class DatabaseConfig {
    final int poolSize;
    DatabaseConfig(Environment environment) { this.poolSize = Integer.parseInt(environment.get("db.pool.size")); }
}
```

How to run: `java ConfigClientLevel3.java`

`db.pool.size` is defined in *both* the local `application.yml` (`"5"`) and the Config Server response (`"50"`) — `buildEnvironment` merges remote first, then local, so the local value wins, exactly matching the precedence established back in the bootstrap-context card. `DatabaseConfig`, standing in for any real `@Value`-injected component, reads `db.pool.size` through the merged `Environment` with no awareness of which source actually won — it just sees `5`.

## 6. Walkthrough

Execution starts in `main` for Level 3. `localApplicationYml` defines `db.pool.size = "5"`; `fetchFromConfigServer` returns `db.pool.size = "50"` from the (simulated) remote server.

`buildEnvironment` constructs `merged` by first copying every entry from `remote`, then calling `merged.putAll(local)` — since `local` also defines `db.pool.size`, this second `putAll` overwrites the remote value of `"50"` with the local value of `"5"`:

```
Application startup complete.
Resolved db.pool.size for connection pool: 5
Resolved payment.gateway: stripe-live
```

`DatabaseConfig`'s constructor reads `environment.get("db.pool.size")` and parses it — it has no idea, and no need to know, whether that value came from local configuration or the Config Server; it just resolved to `5` because local configuration took precedence in this particular case. `payment.gateway`, defined *only* remotely, passes through untouched to `"stripe-live"`.

This is exactly what `spring.config.import=configserver:...` achieves in a real Spring Boot application: a single declarative line triggers the fetch, Spring Boot's own configuration machinery handles the merge with standard precedence rules, and every `@Value`/`@ConfigurationProperties` in the application resolves against the final result — with the entire Config Server integration this whole section has covered reduced, from the consuming application's point of view, to one line in `application.yml`.

## 7. Gotchas & takeaways

> Gotcha: because local configuration generally takes precedence over remote Config Server values for the same key, a value someone intends to be centrally managed can be silently shadowed by a leftover local override that was never cleaned up — this is a common source of "I changed it in the config repo but nothing happened" confusion, and the fix is almost always finding and removing the stale local override.

> Gotcha: `spring.config.import=configserver:...` fails application startup by default if the Config Server is unreachable — appending `optional:` (`spring.config.import=optional:configserver:...`) makes the fetch non-fatal, letting the application start with just its local configuration if the server can't be reached; whether that's the right behavior depends entirely on whether the application can function correctly without its remote configuration.

- `spring.config.import=configserver:...` is the modern, standard mechanism for a Spring Boot application to fetch configuration from a Config Server, replacing the legacy bootstrap-context approach from earlier in this module.
- The fetch integrates directly into Spring Boot's own configuration-loading sequence — fetched properties merge with local ones using standard precedence, with local generally winning on conflicts.
- Application code (`@Value`, `@ConfigurationProperties`) has no visibility into whether a resolved property came from local configuration or the Config Server — the merge is completely transparent.
- Prefixing with `optional:` controls whether an unreachable Config Server is a fatal startup error or a gracefully degraded fallback to local-only configuration — the right choice depends on whether the application can run correctly without its remote configuration.
