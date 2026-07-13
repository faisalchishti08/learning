---
card: microservices
gi: 231
slug: spring-cloud-config-server
title: "Spring Cloud Config Server"
---

## 1. What it is

Spring Cloud Config Server is Spring's implementation of the [centralized configuration server](0219-centralized-configuration-server.md) pattern — a standalone Spring Boot application (enabled via `@EnableConfigServer`) that serves configuration to every other service in a system over a simple HTTP API, backed by a [pluggable storage backend](0233-config-backends-git-vault-jdbc-redis-filesystem.md) such as a Git repository.

## 2. Why & when

Building a custom configuration server from scratch — an HTTP API, a storage backend, environment/profile-aware resolution — duplicates a well-solved problem that Spring Cloud already provides a production-ready implementation of. Spring Cloud Config Server exposes configuration by service name and profile through a conventional URL structure, integrates natively with [Spring Cloud Config Client](0232-spring-cloud-config-client.md) so consuming services need almost no custom code to fetch from it, and defaults to a Git-backed store, giving centralized configuration the same review-and-history guarantees as [configuration as code](0221-configuration-as-code.md) out of the box.

Stand up a Config Server once a system has grown enough services with shared or environment-varying configuration that centralizing it, as motivated in [centralized configuration server](0219-centralized-configuration-server.md), is worth the operational cost of running an additional service. A small number of independent services with non-overlapping configuration usually doesn't need one yet.

## 3. Core concept

Spring Cloud Config Server resolves a request for `{application}/{profile}` (optionally with a `{label}` for a specific Git branch or tag) by locating the matching configuration file(s) in its backend and returning the merged result as JSON, following naming conventions that mirror how a service's own `application.yaml`/`application-{profile}.yaml` files would be structured locally.

```java
// the CONFIG SERVER application itself -- a whole standalone Spring Boot app
@SpringBootApplication
@EnableConfigServer // turns this app INTO a config server
public class ConfigServerApplication {
    public static void main(String[] args) { SpringApplication.run(ConfigServerApplication.class, args); }
}

// application.yaml (of the CONFIG SERVER):
// spring:
//   cloud:
//     config:
//       server:
//         git:
//           uri: https://github.com/example/config-repo # the BACKEND -- a Git repo of config files

// a client requests: GET http://config-server:8888/order-service/production
// -- resolves order-service.yaml + order-service-production.yaml from the Git repo, MERGED
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Git repository of configuration files backs a Spring Cloud Config Server, which exposes an HTTP API that order-service requests configuration from using its service name and active profile" >
  <rect x="20" y="70" width="140" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Git config repo</text>

  <rect x="240" y="55" width="170" height="75" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Cloud Config Server</text>
  <text x="325" y="96" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">GET /{app}/{profile}</text>
  <text x="325" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">merges + returns JSON</text>

  <rect x="480" y="70" width="140" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">order-service</text>

  <line x1="160" y1="92" x2="238" y2="92" stroke="#8b949e" marker-end="url(#arr231)"/>
  <line x1="480" y1="92" x2="412" y2="92" stroke="#8b949e" marker-end="url(#arr231)"/>
  <text x="446" y="86" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">GET /order-service/production</text>

  <defs>
    <marker id="arr231" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

order-service requests its configuration by name and profile; the Config Server resolves and merges it from the Git backend.

## 5. Runnable example

Scenario: a Config Server's core resolution logic modeled in plain Java — starting with a single flat lookup, extending to service-name-plus-profile resolution mirroring the real `{application}/{profile}` URL convention, and finally adding merge behavior where a base file's settings and a profile-specific file's settings combine, with the profile-specific values taking precedence — exactly what a real Config Server request returns.

### Level 1 — Basic

```java
// File: FlatConfigLookup.java -- a SINGLE flat map, no service-name or
// profile awareness -- everyone gets the SAME configuration.
import java.util.*;

public class FlatConfigLookup {
    static Map<String, String> allConfig = Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "timeout.ms", "3000");

    public static void main(String[] args) {
        System.out.println("Config: " + allConfig);
        System.out.println("No way to give order-service and payment-service DIFFERENT settings this way.");
    }
}
```

**How to run:** `javac FlatConfigLookup.java && java FlatConfigLookup` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ServiceAndProfileResolution.java -- mirrors the REAL Config
// Server URL convention: {application}/{profile} resolves a SPECIFIC
// file for that combination.
import java.util.*;

public class ServiceAndProfileResolution {
    // simulates files: order-service-production.yaml, order-service-development.yaml, payment-service-production.yaml
    static Map<String, Map<String, String>> gitBackedFiles = Map.of(
        "order-service-production", Map.of("db.url", "jdbc:postgresql://prod-db:5432/orders", "timeout.ms", "3000"),
        "order-service-development", Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "timeout.ms", "10000"),
        "payment-service-production", Map.of("api.key", "prod-key-abc")
    );

    static Map<String, String> resolve(String application, String profile) {
        String fileKey = application + "-" + profile; // mirrors "{application}-{profile}.yaml"
        return gitBackedFiles.getOrDefault(fileKey, Map.of());
    }

    public static void main(String[] args) {
        System.out.println("GET /order-service/production -> " + resolve("order-service", "production"));
        System.out.println("GET /order-service/development -> " + resolve("order-service", "development"));
        System.out.println("GET /payment-service/production -> " + resolve("payment-service", "production"));
    }
}
```

**How to run:** `javac ServiceAndProfileResolution.java && java ServiceAndProfileResolution` (JDK 17+).

Expected output:
```
GET /order-service/production -> {db.url=jdbc:postgresql://prod-db:5432/orders, timeout.ms=3000}
GET /order-service/development -> {db.url=jdbc:postgresql://localhost:5432/orders, timeout.ms=10000}
GET /payment-service/production -> {api.key=prod-key-abc}
```

### Level 3 — Advanced

```java
// File: BaseAndProfileSpecificMerge.java -- mirrors the REAL Config
// Server behavior: a BASE file (order-service.yaml) merges with a
// PROFILE-SPECIFIC file (order-service-production.yaml), with the
// profile-specific values taking PRECEDENCE over the base.
import java.util.*;

public class BaseAndProfileSpecificMerge {
    static Map<String, Map<String, String>> gitBackedFiles = Map.of(
        "order-service", Map.of("timeout.ms", "3000", "retry.count", "3", "log.level", "INFO"), // BASE, applies to ALL profiles
        "order-service-production", Map.of("timeout.ms", "5000", "db.url", "jdbc:postgresql://prod-db:5432/orders"), // OVERRIDES timeout, ADDS db.url
        "order-service-development", Map.of("db.url", "jdbc:postgresql://localhost:5432/orders", "log.level", "DEBUG") // OVERRIDES log.level, ADDS db.url
    );

    static Map<String, String> resolve(String application, String profile) {
        Map<String, String> merged = new HashMap<>(gitBackedFiles.getOrDefault(application, Map.of())); // start with BASE
        Map<String, String> profileSpecific = gitBackedFiles.getOrDefault(application + "-" + profile, Map.of());
        merged.putAll(profileSpecific); // PROFILE-SPECIFIC values OVERRIDE the base, key by key
        return merged;
    }

    public static void main(String[] args) {
        System.out.println("GET /order-service/production ->");
        resolve("order-service", "production").entrySet().stream().sorted(Map.Entry.comparingByKey())
            .forEach(e -> System.out.println("  " + e.getKey() + "=" + e.getValue()));

        System.out.println("GET /order-service/development ->");
        resolve("order-service", "development").entrySet().stream().sorted(Map.Entry.comparingByKey())
            .forEach(e -> System.out.println("  " + e.getKey() + "=" + e.getValue()));
    }
}
```

**How to run:** `javac BaseAndProfileSpecificMerge.java && java BaseAndProfileSpecificMerge` (JDK 17+).

Expected output:
```
GET /order-service/production ->
  db.url=jdbc:postgresql://prod-db:5432/orders
  log.level=INFO
  retry.count=3
  timeout.ms=5000
GET /order-service/development ->
  db.url=jdbc:postgresql://localhost:5432/orders
  log.level=DEBUG
  retry.count=3
  timeout.ms=3000
```

## 6. Walkthrough

1. **Level 1, the undifferentiated baseline** — `allConfig` is a single flat map with no notion of which service or environment is asking; every consumer, regardless of identity, would receive the identical configuration, which is exactly the limitation a real Config Server's `{application}/{profile}` addressing scheme is designed to remove.
2. **Level 2, addressing by service and profile** — `resolve` combines `application` and `profile` into a file key (`"order-service-production"`), mirroring the real convention of a file named `order-service-production.yaml`; each combination resolves to its own distinct, independently stored configuration map.
3. **Level 2, distinct results per combination** — the three calls in `main` (`order-service`/`production`, `order-service`/`development`, `payment-service`/`production`) each return a completely different map, demonstrating that both the service identity and the active profile determine what's returned — a capability the flat lookup in Level 1 had no way to provide.
4. **Level 3, introducing a base configuration** — `gitBackedFiles` now includes a `"order-service"` entry with no profile suffix, mirroring a real `order-service.yaml` file that applies regardless of which profile is active; `resolve` starts by copying this base map into `merged` before considering any profile-specific overrides.
5. **Level 3, layering the profile-specific file on top** — `merged.putAll(profileSpecific)` copies every key from the profile-specific map into `merged`, and because `HashMap.putAll` overwrites any existing key with the same name, a key present in both the base and the profile-specific file (like `timeout.ms`) ends up with the profile-specific file's value, while a key present only in the base (like `retry.count`) survives unchanged.
6. **Level 3, confirming the merge in the output** — the `production` result shows `timeout.ms=5000` (the profile-specific override winning over the base's `3000`) alongside `retry.count=3` and `log.level=INFO` (both inherited unchanged from the base, since neither is redefined in `order-service-production`); the `development` result shows the same base-inheritance pattern but with its own distinct overrides (`db.url` and a `DEBUG` `log.level`) — this base-plus-profile-specific merge, with profile-specific values winning, is exactly what a real Spring Cloud Config Server request for `/order-service/production` returns as its resolved JSON response.

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Config Server, by default, serves configuration files as-is from its backend, including any plaintext values they contain — it is not itself a secrets vault; storing genuine secrets directly in Git-backed config files (even via Config Server) risks the same permanent-exposure problem covered in [secrets management & encryption](0222-secrets-management-encryption.md), unless combined with [Config Server's own encryption support](0238-encryption-decryption-of-config-values.md) or delegated to [Spring Cloud Vault](0236-spring-cloud-vault-for-secrets.md) for genuinely sensitive values.

- Spring Cloud Config Server is Spring's ready-made [centralized configuration server](0219-centralized-configuration-server.md), exposing configuration over HTTP addressed by service name and profile, typically backed by Git.
- It resolves each request by merging a base, profile-agnostic configuration file with a profile-specific one, with the profile-specific file's values taking precedence over the base for any overlapping key.
- Standing one up trades an additional operational service for centralized configuration management and Git's review/history guarantees applied directly to that configuration.
- Config Server is not a secrets vault by default — genuinely sensitive values need either its own encryption support or a dedicated secret store like Spring Cloud Vault.
- Consuming services fetch from it via [Spring Cloud Config Client](0232-spring-cloud-config-client.md), covered next, which needs almost no custom integration code beyond pointing at the server's address.
