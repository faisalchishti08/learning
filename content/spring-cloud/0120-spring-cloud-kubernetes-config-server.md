---
card: spring-cloud
gi: 120
slug: spring-cloud-kubernetes-config-server
title: "Spring Cloud Kubernetes Config Server"
---

## 1. What it is

Spring Cloud Kubernetes Config Server is a standard Spring Cloud Config Server deployment that additionally reads Kubernetes ConfigMaps and Secrets as configuration sources alongside (or instead of) a Git repository, letting teams combine the Config Server's proven client protocol, versioned config history where a Git backend is still used, and encryption support, with Kubernetes-native ConfigMap/Secret storage where that's preferred for a given piece of configuration — running as one centralized Config Server deployment inside the cluster, rather than requiring every individual application to embed its own Spring Cloud Kubernetes `PropertySource` client directly.

```yaml
spring:
  profiles:
    active: kubernetes
  cloud:
    config:
      server:
        kubernetes:
          config-map:
            enabled: true
          secrets:
            enabled: true
```

```properties
# client applications configure EXACTLY as they would for any other Config Server
spring.config.import=configserver:http://config-server:8888
```

## 2. Why & when

Two earlier cards in this section established two different paths to Kubernetes-aware configuration: Spring Cloud Kubernetes's own `PropertySource` reads ConfigMaps/Secrets directly, per-application, with no separate Config Server at all; the standalone Spring Cloud Config Server (much earlier cards) serves configuration from a Git repository to any number of client applications through one centralized service. Spring Cloud Kubernetes Config Server is a specific combination of both: a Config Server deployment that itself sources from Kubernetes ConfigMaps/Secrets (rather than, or in addition to, Git), letting client applications use the standard, well-understood Config Server client protocol (`spring.config.import=configserver:...`) while the actual configuration storage backend is Kubernetes-native.

Reach for this combination when:

- A centralized Config Server is already valued for reasons independent of Kubernetes specifically (a uniform client protocol across mixed Kubernetes and non-Kubernetes deployments, centralized encryption of sensitive values) but the underlying configuration storage should still live in Kubernetes-native ConfigMaps/Secrets rather than (or alongside) a separate Git repository.
- Migrating gradually from a Git-backed Config Server toward Kubernetes-native configuration, or vice versa — this combination allows both backends to coexist during a transition period, since a Config Server instance can be configured with multiple simultaneous sources.
- Client applications should remain fully decoupled from *how* Config Server actually resolves configuration underneath — exactly the same benefit the original Config Server abstraction (an early card) provided over hardcoded properties files, extended now to cover a Kubernetes-native backend as one more interchangeable source.

## 3. Core concept

```
 client application:
   spring.config.import=configserver:http://config-server:8888
   -- IDENTICAL client configuration regardless of what backs the Config Server

 Config Server itself, configured with EITHER (or both):
   Git backend:              reads a Git repository's properties/YAML files
   Kubernetes ConfigMap/Secret backend: reads ConfigMap/Secret objects in the cluster

 client's Environment ends up populated identically either way --
 the CLIENT never knows or cares which backend actually served its configuration
```

This mirrors the exact same "swap the implementation, keep the interface" pattern seen throughout this section (discovery, load balancing) — here applied to the Config Server's own choice of underlying configuration storage.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client application uses the standard Config Server client protocol unaware that the Config Server itself may be backed by either a Git repository or Kubernetes ConfigMaps and Secrets or both simultaneously">
  <rect x="20" y="70" width="160" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="98" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">client application</text>

  <rect x="250" y="70" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="92" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Config Server</text>
  <text x="340" y="106" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">standard client protocol</text>

  <rect x="490" y="20" width="130" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="555" y="41" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Git repository</text>
  <rect x="490" y="130" width="130" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="555" y="151" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">ConfigMap/Secret</text>

  <defs><marker id="a120" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="180" y1="93" x2="250" y2="93" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a120)"/>
  <line x1="430" y1="85" x2="490" y2="42" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a120)"/>
  <line x1="430" y1="100" x2="490" y2="140" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a120)"/>
</svg>

The client's own connection (left arrow) never changes; the Config Server's own backend choice (right arrows) is entirely its internal concern.

## 5. Runnable example

The scenario: model a Config Server aggregating configuration from both a Git-style source and a Kubernetes-ConfigMap-style source, serving one unified response to a client that has no idea which backend contributed which property. Start with Git-only serving, then add a Kubernetes-backed source merged alongside it, then add a case where the same property key exists in both sources, demonstrating and testing precedence.

### Level 1 — Basic

Config Server serving configuration from a Git-style source only — the traditional baseline.

```java
import java.util.*;

public class K8sConfigServerLevel1 {
    static class GitBackend {
        Map<String, String> readProperties(String application) {
            return Map.of("server.port", "8080", "app.name", application);
        }
    }

    static class ConfigServer {
        GitBackend git = new GitBackend();
        Map<String, String> serveConfig(String application) {
            return git.readProperties(application);
        }
    }

    public static void main(String[] args) {
        ConfigServer server = new ConfigServer();
        System.out.println("client receives: " + server.serveConfig("order-service"));
    }
}
```

How to run: `java K8sConfigServerLevel1.java`

`serveConfig` reads purely from `GitBackend` — this is a standard, Git-only Config Server, exactly as covered in the earlier Config Server cards, before any Kubernetes-specific backend is introduced.

### Level 2 — Intermediate

Add a Kubernetes ConfigMap-style backend, merged alongside the Git backend into one unified response — the client-facing `serveConfig` method is unaffected in shape.

```java
import java.util.*;

public class K8sConfigServerLevel2 {
    static class GitBackend {
        Map<String, String> readProperties(String application) {
            return Map.of("server.port", "8080", "app.name", application);
        }
    }

    // models Spring Cloud Kubernetes Config Server's ConfigMap-reading backend
    static class KubernetesConfigMapBackend {
        Map<String, String> readProperties(String application) {
            return Map.of("rate-limit", "100/min", "feature.new-checkout", "true");
        }
    }

    static class ConfigServer {
        GitBackend git = new GitBackend();
        KubernetesConfigMapBackend k8s = new KubernetesConfigMapBackend();

        Map<String, String> serveConfig(String application) {
            Map<String, String> merged = new HashMap<>();
            merged.putAll(git.readProperties(application));
            merged.putAll(k8s.readProperties(application)); // BOTH sources contribute to ONE response
            return merged;
        }
    }

    public static void main(String[] args) {
        ConfigServer server = new ConfigServer();
        Map<String, String> response = server.serveConfig("order-service");
        System.out.println("client receives (Git + Kubernetes merged): " + response);
    }
}
```

How to run: `java K8sConfigServerLevel2.java`

`response` contains keys from both `GitBackend` (`server.port`, `app.name`) and `KubernetesConfigMapBackend` (`rate-limit`, `feature.new-checkout`) — a client calling `serveConfig` receives one unified map with no indication of which backend contributed which entry, exactly mirroring how a real client application consuming this Config Server via `spring.config.import=configserver:...` sees a single, merged `Environment` regardless of how many underlying sources the server itself aggregated.

### Level 3 — Advanced

Add a key collision between the two backends and demonstrate configurable precedence, plus a source-attribution debug mode useful for diagnosing exactly which backend a given property actually came from.

```java
import java.util.*;

public class K8sConfigServerLevel3 {
    static class GitBackend {
        Map<String, String> readProperties(String application) {
            return Map.of("server.port", "8080", "rate-limit", "50/min"); // deliberately COLLIDES on rate-limit
        }
    }

    static class KubernetesConfigMapBackend {
        Map<String, String> readProperties(String application) {
            return Map.of("rate-limit", "100/min", "feature.new-checkout", "true");
        }
    }

    static class ConfigServer {
        GitBackend git = new GitBackend();
        KubernetesConfigMapBackend k8s = new KubernetesConfigMapBackend();
        boolean kubernetesTakesPrecedence; // configurable, mirrors real Config Server precedence ordering

        ConfigServer(boolean kubernetesTakesPrecedence) { this.kubernetesTakesPrecedence = kubernetesTakesPrecedence; }

        Map<String, String> serveConfig(String application) {
            Map<String, String> merged = new HashMap<>();
            if (kubernetesTakesPrecedence) {
                merged.putAll(git.readProperties(application));     // lower precedence, applied FIRST
                merged.putAll(k8s.readProperties(application));     // higher precedence, applied SECOND
            } else {
                merged.putAll(k8s.readProperties(application));
                merged.putAll(git.readProperties(application));
            }
            return merged;
        }

        // debug helper: reports which backend actually contributed a given key's FINAL value
        String attributeSource(String key, String finalValue) {
            boolean fromGit = finalValue.equals(git.readProperties("x").get(key));
            boolean fromK8s = finalValue.equals(k8s.readProperties("x").get(key));
            if (fromGit && fromK8s) return "ambiguous (both sources happen to agree)";
            if (fromK8s) return "Kubernetes ConfigMap";
            if (fromGit) return "Git";
            return "unknown";
        }
    }

    public static void main(String[] args) {
        ConfigServer k8sWins = new ConfigServer(true);
        Map<String, String> response1 = k8sWins.serveConfig("order-service");
        System.out.println("Kubernetes precedence: rate-limit=" + response1.get("rate-limit")
                + " (source: " + k8sWins.attributeSource("rate-limit", response1.get("rate-limit")) + ")");

        ConfigServer gitWins = new ConfigServer(false);
        Map<String, String> response2 = gitWins.serveConfig("order-service");
        System.out.println("Git precedence: rate-limit=" + response2.get("rate-limit")
                + " (source: " + gitWins.attributeSource("rate-limit", response2.get("rate-limit")) + ")");
    }
}
```

How to run: `java K8sConfigServerLevel3.java`

With `kubernetesTakesPrecedence=true`, `response1.get("rate-limit")` resolves to `"100/min"` (the Kubernetes ConfigMap's value, applied second and winning the collision), while with `kubernetesTakesPrecedence=false`, `response2.get("rate-limit")` resolves to `"50/min"` (Git's value) — `attributeSource` then confirms which backend's own data actually matches the final resolved value, a useful debugging technique for a real Config Server deployment where a client reports an unexpected property value and the operator needs to determine which of several configured sources is actually responsible for it.

## 6. Walkthrough

Trace `k8sWins.serveConfig("order-service")` in Level 3.

1. `kubernetesTakesPrecedence` is `true`, so the `if` branch runs.
2. `merged.putAll(git.readProperties("order-service"))` adds `server.port=8080` and `rate-limit=50/min` to the initially-empty `merged` map.
3. `merged.putAll(k8s.readProperties("order-service"))` adds `rate-limit=100/min` and `feature.new-checkout=true` — because `rate-limit` already exists in `merged` from step 2, this `putAll` call overwrites it, replacing `"50/min"` with `"100/min"`.
4. `serveConfig` returns `merged`, now containing `server.port=8080`, `rate-limit=100/min` (Kubernetes' value won), and `feature.new-checkout=true`.
5. `k8sWins.attributeSource("rate-limit", "100/min")` is called — `fromGit` checks whether `git.readProperties("x").get("rate-limit")` (which is `"50/min"`) equals `"100/min"`; it doesn't, so `fromGit` is `false`. `fromK8s` checks whether `k8s.readProperties("x").get("rate-limit")` (which is `"100/min"`) equals `"100/min"`; it does, so `fromK8s` is `true`.
6. Since `fromGit` is `false` and `fromK8s` is `true`, `attributeSource` returns `"Kubernetes ConfigMap"` — correctly identifying that the final, resolved `rate-limit` value genuinely came from the Kubernetes-backed source, not Git, consistent with the precedence configuration used for this particular `ConfigServer` instance.

```
kubernetesTakesPrecedence=true:
  merged after Git:        {server.port: 8080, rate-limit: 50/min}
  merged after Kubernetes: {server.port: 8080, rate-limit: 100/min, feature.new-checkout: true}   <- rate-limit OVERWRITTEN

attributeSource("rate-limit", "100/min"):
  matches Git's own value (50/min)?        NO
  matches Kubernetes' own value (100/min)?  YES
  -> "Kubernetes ConfigMap"
```

## 7. Gotchas & takeaways

> **Gotcha:** relying on implicit precedence ordering to resolve intentional key collisions between multiple Config Server backends (as opposed to precedence only ever mattering for genuinely accidental overlaps) is a fragile configuration-management pattern — it's generally much clearer, and far less prone to future confusion, to keep each backend responsible for a distinct, non-overlapping set of property keys, reserving precedence ordering purely as a safety net rather than as an intentional mechanism for one source to systematically "win" over another on shared keys.

- Spring Cloud Kubernetes Config Server combines the standard, well-understood Config Server client protocol with a Kubernetes-native (ConfigMap/Secret) configuration storage backend, letting client applications remain fully agnostic to which storage mechanism actually backs their configuration.
- Multiple backends (Git and Kubernetes-native, simultaneously) can be configured on one Config Server instance, with a defined precedence order resolving any key collisions — understanding and deliberately configuring that precedence matters whenever more than one backend is in play.
- A source-attribution debugging technique (comparing a resolved value against each individual backend's own contribution, as `attributeSource` modeled) is a practical tool for diagnosing unexpected configuration values in a real multi-backend Config Server deployment.
- This card closes out the Security, Vault & Kubernetes section by tying together Vault-based secret management (earlier cards) and Kubernetes-native configuration and coordination (this section's later cards) under the same overarching theme: externalizing configuration and secrets out of application code and into dedicated, purpose-built infrastructure, consumed through consistent, stable Spring Cloud abstractions regardless of which specific backend ultimately serves them.
