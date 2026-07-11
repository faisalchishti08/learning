---
card: spring-cloud
gi: 5
slug: bootstrap-context-spring-cloud-bootstrap
title: "Bootstrap context & spring.cloud.bootstrap"
---

## 1. What it is

The bootstrap context is a special parent Spring `ApplicationContext`, created (in the legacy Spring Cloud Config Client model) *before* the main application context, whose entire job is to load configuration from an external source — typically a Config Server — early enough that it can influence how the main context itself gets built. It's activated via `bootstrap.yml`/`bootstrap.properties` or, in newer Spring Cloud versions, `spring.cloud.bootstrap.enabled=true`.

```yaml
# bootstrap.yml -- loaded BEFORE application.yml, by the bootstrap context
spring:
  application:
    name: order-service
  cloud:
    config:
      uri: http://config-server:8888
```

## 2. Why & when

Most configuration in a Spring Boot application can simply live in `application.yml`, loaded as part of normal startup. But some configuration — most notably, *where the external Config Server itself is* — has a chicken-and-egg problem: the application needs to know the Config Server's location before it can fetch the rest of its configuration from that server. The bootstrap context exists specifically to resolve that: it's a lightweight, early phase whose only job is to establish enough context (like the Config Server's address) to then go fetch everything else.

Reach for understanding the bootstrap context when:

- Diagnosing why a property set in `application.yml` doesn't seem to affect where the app looks for its Config Server — that's a bootstrap-phase property, and belongs in `bootstrap.yml` instead.
- Working with an older Spring Cloud Config Client setup (bootstrap context is opt-in and largely legacy in current Spring Cloud versions, superseded by `spring.config.import` in most new projects).
- Understanding property source precedence in a Spring Cloud application, since bootstrap-context properties are established before, and separately from, the main context's own property sources.

## 3. Core concept

```
 Startup sequence (legacy bootstrap model):

 1. Bootstrap context created FIRST
      reads bootstrap.yml: spring.cloud.config.uri = http://config-server:8888
      fetches remote config from that Config Server
      becomes the PARENT of the main application context

 2. Main application context created SECOND
      reads application.yml
      ALSO inherits every property fetched by the bootstrap context (as if it were a property source)

 A property needed to LOCATE the config source must be in bootstrap.yml --
 it can't depend on the config the bootstrap phase hasn't fetched yet.
```

The bootstrap context solves a genuine ordering problem: config needed to locate more config must be resolved in an earlier phase than everything else.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bootstrap context loads first, fetches remote config, then becomes the parent of the main application context">
  <rect x="20" y="20" width="260" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">1. Bootstrap context</text>
  <text x="150" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reads bootstrap.yml, fetches config</text>

  <line x1="150" y1="70" x2="150" y2="100" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a26)"/>

  <rect x="20" y="105" width="260" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="127" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">2. Main application context</text>
  <text x="150" y="143" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reads application.yml + inherited config</text>

  <rect x="360" y="60" width="240" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="480" y="90" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Config Server (remote)</text>

  <line x1="280" y1="45" x2="350" y2="75" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a26)"/>
  <defs><marker id="a26" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The bootstrap context runs first, contacts the remote config source, then hands its results down to the main application context.

## 5. Runnable example

The scenario: an application that needs to fetch configuration from a remote Config Server, evolving from a naive single-phase startup that can't resolve the chicken-and-egg problem, to a two-phase bootstrap-then-main startup, to a full simulation showing exactly which properties the main context inherits from the bootstrap phase versus its own local file.

### Level 1 — Basic

Show the chicken-and-egg problem directly: how would an application in a single startup phase find the Config Server's address, given the Config Server's address is itself supposed to come from configuration?

```java
import java.util.*;

public class BootstrapContextLevel1 {
    public static void main(String[] args) {
        Map<String, String> applicationProperties = new HashMap<>();
        // If ALL config, including the config-server URI, waits until "normal" startup...
        // ...where would the URI to FETCH remote config from ever come from? Nowhere -- it's circular.
        String configServerUri = applicationProperties.get("spring.cloud.config.uri"); // never set -- null
        System.out.println("Config server URI (single-phase startup): " + configServerUri);
    }
}
```

How to run: `java BootstrapContextLevel1.java`

With everything resolved in one flat phase, there's no natural place for "where is the Config Server" to be established before the application tries to use it — this circularity is exactly what a separate, earlier bootstrap phase resolves.

### Level 2 — Intermediate

Add a two-phase startup: a bootstrap phase resolves the Config Server's location and fetches remote properties first, then the main phase builds on top of it.

```java
import java.util.*;

public class BootstrapContextLevel2 {
    public static void main(String[] args) {
        // Phase 1: bootstrap context -- reads ONLY bootstrap.yml-equivalent properties.
        Map<String, String> bootstrapProperties = Map.of(
            "spring.application.name", "order-service",
            "spring.cloud.config.uri", "http://config-server:8888"
        );
        String configServerUri = bootstrapProperties.get("spring.cloud.config.uri");
        System.out.println("Phase 1 (bootstrap): resolved config server at " + configServerUri);

        Map<String, String> remoteConfig = fetchFromConfigServer(configServerUri, bootstrapProperties.get("spring.application.name"));
        System.out.println("Phase 1 (bootstrap): fetched remote config " + remoteConfig);

        // Phase 2: main application context -- inherits everything the bootstrap phase fetched.
        Map<String, String> mainContextProperties = new HashMap<>(remoteConfig);
        mainContextProperties.putAll(Map.of("server.port", "8080")); // application.yml's own local properties
        System.out.println("Phase 2 (main): final resolved properties " + mainContextProperties);
    }

    static Map<String, String> fetchFromConfigServer(String uri, String applicationName) {
        return Map.of("database.url", "jdbc:postgresql://prod-db/" + applicationName, "feature.newCheckout", "true");
    }
}
```

How to run: `java BootstrapContextLevel2.java`

Phase 1 resolves `spring.cloud.config.uri` from a properties map that stands in for `bootstrap.yml`, uses it to fetch remote config, and phase 2's `mainContextProperties` starts from that fetched result before adding its own local properties — mirroring exactly how the main application context inherits the bootstrap context's property sources.

### Level 3 — Advanced

Show precedence explicitly: a property defined in both the bootstrap-fetched remote config *and* the local `application.yml`-equivalent, demonstrating which one actually wins, and why understanding this ordering matters for debugging.

```java
import java.util.*;

public class BootstrapContextLevel3 {
    public static void main(String[] args) {
        Map<String, String> bootstrapProperties = Map.of(
            "spring.application.name", "order-service",
            "spring.cloud.config.uri", "http://config-server:8888"
        );
        Map<String, String> remoteConfig = fetchFromConfigServer(
            bootstrapProperties.get("spring.cloud.config.uri"), bootstrapProperties.get("spring.application.name"));

        Map<String, String> localApplicationYml = Map.of(
            "server.port", "9090",
            "feature.newCheckout", "false" // ALSO defined remotely as "true" -- which wins?
        );

        Map<String, String> resolved = resolveFinalProperties(remoteConfig, localApplicationYml);
        System.out.println("Remote (bootstrap-fetched): " + remoteConfig);
        System.out.println("Local (application.yml):    " + localApplicationYml);
        System.out.println("Final resolved:              " + resolved);
    }

    static Map<String, String> fetchFromConfigServer(String uri, String applicationName) {
        return new LinkedHashMap<>(Map.of(
            "database.url", "jdbc:postgresql://prod-db/" + applicationName,
            "feature.newCheckout", "true"
        ));
    }

    // Local application.yml properties take precedence over remote config for the SAME key, by default.
    static Map<String, String> resolveFinalProperties(Map<String, String> remote, Map<String, String> local) {
        Map<String, String> result = new LinkedHashMap<>(remote); // start from remote
        result.putAll(local); // local OVERRIDES remote for any overlapping key
        return result;
    }
}
```

How to run: `java BootstrapContextLevel3.java`

`feature.newCheckout` is defined as `"true"` in the remote, bootstrap-fetched config, but `"false"` locally — `resolveFinalProperties` starts from the remote map and then overlays the local one, so the local value wins for that key, while `database.url` (only present remotely) and `server.port` (only present locally) both pass through untouched.

## 6. Walkthrough

Execution starts in `main` for Level 3. Bootstrap-phase properties resolve `spring.cloud.config.uri`, which is used to call `fetchFromConfigServer`, returning a map with `database.url` and `feature.newCheckout=true`.

`resolveFinalProperties` builds `result` starting as a copy of `remote`, then calls `result.putAll(local)` — this overwrites any key present in both maps with the local value, while keys unique to either map are preserved untouched:

```
Remote (bootstrap-fetched): {database.url=jdbc:postgresql://prod-db/order-service, feature.newCheckout=true}
Local (application.yml):    {server.port=9090, feature.newCheckout=false}
Final resolved:              {database.url=jdbc:postgresql://prod-db/order-service, feature.newCheckout=false, server.port=9090}
```

`feature.newCheckout` ends up `false` in the final result, because the local `application.yml`-equivalent value overrode the remote one — this is the actual, sometimes-surprising precedence behavior in a real Spring Cloud application: local configuration generally wins over remote Config Server values for the same property key, unless the Config Server is specifically configured with a higher-priority profile or the application explicitly opts into different precedence.

## 7. Gotchas & takeaways

> Gotcha: in current Spring Cloud versions, the classic bootstrap-context mechanism is disabled by default and largely superseded by `spring.config.import=configserver:` inside regular `application.yml` — projects following older tutorials that rely on `bootstrap.yml` may find it silently ignored unless `spring.cloud.bootstrap.enabled=true` (or the `spring-cloud-starter-bootstrap` dependency) is explicitly added back.

> Gotcha: because the bootstrap phase runs before the main context and uses its own, more limited property resolution, some Spring features that work fine in `application.yml` (certain profile-specific document splitting, for instance) don't behave identically inside `bootstrap.yml` — treat it as a minimal, early-phase file, not a full replacement for the main configuration file.

- The bootstrap context is an early, separate phase whose job is resolving properties needed to *locate* further configuration (a Config Server's URI) before the main application context is built.
- It solves a genuine ordering problem: config needed to find more config can't itself depend on config that hasn't been fetched yet.
- Local `application.yml` properties generally take precedence over remote Config Server values for the same key once both are resolved.
- The bootstrap-context mechanism is legacy in current Spring Cloud — most new projects use `spring.config.import=configserver:...` directly in `application.yml` instead, avoiding the separate bootstrap phase and file entirely.
