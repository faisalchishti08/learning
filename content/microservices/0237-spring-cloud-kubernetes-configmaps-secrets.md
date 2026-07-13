---
card: microservices
gi: 237
slug: spring-cloud-kubernetes-configmaps-secrets
title: "Spring Cloud Kubernetes ConfigMaps & Secrets"
---

## 1. What it is

Spring Cloud Kubernetes lets a Spring Boot application read its configuration and secrets directly from Kubernetes-native `ConfigMap` and `Secret` resources — the platform's own built-in configuration objects — rather than requiring a separate [Config Server](0231-spring-cloud-config-server.md) deployment, integrating Kubernetes' native configuration primitives with Spring's `@Value`/`@ConfigurationProperties` mechanisms.

## 2. Why & when

An application already running on Kubernetes has access to the platform's own configuration primitives — `ConfigMap` for non-sensitive settings, `Secret` for sensitive values (base64-encoded and, depending on cluster setup, encrypted at rest) — managed through the exact same `kubectl`/GitOps workflows already used to manage every other Kubernetes resource. Running a separate Spring Cloud Config Server on top of this duplicates infrastructure the platform already provides. Spring Cloud Kubernetes closes this gap by reading `ConfigMap`s and `Secret`s mounted into (or accessible from) the application's pod directly, merging them into the application's `Environment` the same way Config Client merges values fetched from a Config Server.

Use Spring Cloud Kubernetes when a service already runs on Kubernetes and its configuration management should live natively within the cluster's own resources and tooling, avoiding a separate Config Server deployment. A multi-platform system that also runs services outside Kubernetes may still prefer a platform-agnostic Config Server so all services share one configuration mechanism regardless of where they run.

## 3. Core concept

A `ConfigMap` or `Secret` can be projected into a pod either as environment variables or as mounted files, and Spring Cloud Kubernetes reads from whichever projection is configured, merging the resulting key-value pairs into the application's `Environment` — with optional support for detecting changes to a mounted `ConfigMap`/`Secret` and triggering a [`@RefreshScope`](0234-refreshscope-for-runtime-refresh.md)-style refresh automatically.

```yaml
# a Kubernetes ConfigMap resource
apiVersion: v1
kind: ConfigMap
metadata: { name: order-service-config }
data:
  application.yaml: |
    order:
      retry:
        max-attempts: 5
---
# a Kubernetes Secret resource
apiVersion: v1
kind: Secret
metadata: { name: order-service-secrets }
type: Opaque
data:
  db-password: aHVudGVyMg== # base64-encoded -- NOT plaintext-safe by itself, but decoded automatically for the application
```
```java
@Value("${order.retry.max-attempts}") // resolved from the ConfigMap above
int maxAttempts;

@Value("${db-password}") // resolved from the Secret above, ALREADY decoded
String dbPassword;
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ConfigMap and a Secret, both native Kubernetes resources managed via kubectl or GitOps, are read by Spring Cloud Kubernetes and merged into the application's Environment, without a separate Config Server deployment" >
  <rect x="20" y="20" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ConfigMap</text>

  <rect x="20" y="105" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="132" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Secret</text>

  <rect x="255" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Cloud Kubernetes</text>
  <text x="330" y="96" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">reads + merges</text>

  <rect x="470" y="55" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Environment</text>
  <text x="545" y="96" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no separate Config Server</text>

  <line x1="170" y1="42" x2="253" y2="70" stroke="#8b949e" marker-end="url(#arr237)"/>
  <line x1="170" y1="127" x2="253" y2="98" stroke="#8b949e" marker-end="url(#arr237)"/>
  <line x1="405" y1="85" x2="468" y2="85" stroke="#8b949e" marker-end="url(#arr237)"/>

  <defs>
    <marker id="arr237" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Native Kubernetes resources feed directly into the application's Environment, without a separate config-serving deployment.

## 5. Runnable example

Scenario: an application reading configuration first from a standalone, hand-maintained Config Server (extra infrastructure), refactors to read the same values from simulated Kubernetes `ConfigMap`/`Secret` resources directly, and finally demonstrates detecting a live `ConfigMap` update (as Kubernetes performs when a mounted `ConfigMap` changes) and triggering an automatic refresh, mirroring Spring Cloud Kubernetes' native change-watching support.

### Level 1 — Basic

```java
// File: SeparateConfigServerDependency.java -- configuration comes from
// a SEPARATE Config Server deployment -- extra infrastructure to run
// and operate, on top of the Kubernetes cluster already running everything else.
import java.util.*;

public class SeparateConfigServerDependency {
    static class ConfigServer { // a WHOLE separate deployment, distinct from Kubernetes' own resources
        Map<String, String> fetch(String application, String profile) {
            return Map.of("order.retry.max-attempts", "5");
        }
    }

    public static void main(String[] args) {
        ConfigServer configServer = new ConfigServer();
        Map<String, String> config = configServer.fetch("order-service", "production");
        System.out.println("Fetched from separate Config Server: " + config);
        System.out.println("This Config Server is EXTRA infrastructure alongside the Kubernetes cluster.");
    }
}
```

**How to run:** `javac SeparateConfigServerDependency.java && java SeparateConfigServerDependency` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ReadFromKubernetesNativeResources.java -- reads DIRECTLY from
// simulated ConfigMap and Secret resources, mirroring Spring Cloud
// Kubernetes -- NO separate Config Server deployment needed.
import java.util.*;
import java.util.Base64;

public class ReadFromKubernetesNativeResources {
    static class ConfigMap { Map<String, String> data; ConfigMap(Map<String, String> data) { this.data = data; } }
    static class Secret { Map<String, String> base64Data; Secret(Map<String, String> base64Data) { this.base64Data = base64Data; } }

    static Map<String, String> readEnvironment(ConfigMap configMap, Secret secret) {
        Map<String, String> merged = new HashMap<>(configMap.data);
        for (var entry : secret.base64Data.entrySet()) {
            String decoded = new String(Base64.getDecoder().decode(entry.getValue())); // Spring Cloud Kubernetes DECODES automatically
            merged.put(entry.getKey(), decoded);
        }
        return merged;
    }

    public static void main(String[] args) {
        ConfigMap orderServiceConfig = new ConfigMap(Map.of("order.retry.max-attempts", "5"));
        Secret orderServiceSecrets = new Secret(Map.of("db-password", Base64.getEncoder().encodeToString("hunter2".getBytes())));

        Map<String, String> environment = readEnvironment(orderServiceConfig, orderServiceSecrets);
        System.out.println("Merged Environment: " + environment);
        System.out.println("Read directly from Kubernetes-native resources -- no separate Config Server.");
    }
}
```

**How to run:** `javac ReadFromKubernetesNativeResources.java && java ReadFromKubernetesNativeResources` (JDK 17+).

Expected output:
```
Merged Environment: {order.retry.max-attempts=5, db-password=hunter2}
Read directly from Kubernetes-native resources -- no separate Config Server.
```

### Level 3 — Advanced

```java
// File: WatchConfigMapAndAutoRefresh.java -- WATCHES for a ConfigMap
// change and AUTOMATICALLY triggers a refresh, mirroring Spring Cloud
// Kubernetes' built-in ConfigMap change-detection support.
import java.util.*;
import java.util.function.*;

public class WatchConfigMapAndAutoRefresh {
    static class ConfigMap { Map<String, String> data; ConfigMap(Map<String, String> data) { this.data = data; } }

    static class ConfigMapWatcher {
        ConfigMap currentConfigMap;
        List<Consumer<ConfigMap>> refreshListeners = new ArrayList<>();

        ConfigMapWatcher(ConfigMap initial) { this.currentConfigMap = initial; }
        void onRefresh(Consumer<ConfigMap> listener) { refreshListeners.add(listener); }

        void simulateKubernetesConfigMapUpdate(ConfigMap updated) { // mirrors the Kubernetes API server notifying of a change
            System.out.println("  [watcher] detected ConfigMap change");
            currentConfigMap = updated;
            for (Consumer<ConfigMap> listener : refreshListeners) listener.accept(updated); // AUTOMATICALLY triggers refresh
        }
    }

    static class RetryConfigBean {
        int maxAttempts;
        void applyConfig(ConfigMap cm) { this.maxAttempts = Integer.parseInt(cm.data.get("order.retry.max-attempts")); }
    }

    public static void main(String[] args) {
        ConfigMap initial = new ConfigMap(Map.of("order.retry.max-attempts", "3"));
        ConfigMapWatcher watcher = new ConfigMapWatcher(initial);

        RetryConfigBean retryBean = new RetryConfigBean();
        retryBean.applyConfig(watcher.currentConfigMap); // initial application, at startup
        watcher.onRefresh(retryBean::applyConfig); // SUBSCRIBE to future changes -- mirrors @RefreshScope reacting automatically

        System.out.println("Initial maxAttempts: " + retryBean.maxAttempts);

        // an operator runs: kubectl apply -f updated-configmap.yaml
        watcher.simulateKubernetesConfigMapUpdate(new ConfigMap(Map.of("order.retry.max-attempts", "8")));

        System.out.println("After ConfigMap update (no restart, no manual code call): " + retryBean.maxAttempts);
    }
}
```

**How to run:** `javac WatchConfigMapAndAutoRefresh.java && java WatchConfigMapAndAutoRefresh` (JDK 17+).

Expected output:
```
Initial maxAttempts: 3
  [watcher] detected ConfigMap change
After ConfigMap update (no restart, no manual code call): 8
```

## 6. Walkthrough

1. **Level 1, the extra-infrastructure baseline** — `ConfigServer` is modeled as a wholly separate component the application must reach out to over the network, representing real additional infrastructure (a deployment, a service, its own scaling and availability concerns) beyond the Kubernetes cluster the application already runs on.
2. **Level 2, reading platform-native resources directly** — `ConfigMap` and `Secret` are modeled as plain data holders representing Kubernetes' own resource types, and `readEnvironment` merges both into a single map, decoding the `Secret`'s base64-encoded values along the way — mirroring exactly what Spring Cloud Kubernetes does when reading these resources as mounted volumes or environment variables into a pod.
3. **Level 2, no separate deployment needed** — nothing in `ReadFromKubernetesNativeResources` reaches out over a network to a separate service; `orderServiceConfig` and `orderServiceSecrets` stand in for resources the Kubernetes platform itself already manages and delivers directly into the pod, eliminating the extra deployment Level 1 required.
4. **Level 3, modeling the watch mechanism** — `ConfigMapWatcher` holds a `currentConfigMap` and a list of `refreshListeners`; `simulateKubernetesConfigMapUpdate` stands in for the real Kubernetes API server detecting that a mounted `ConfigMap`'s underlying resource has changed (which happens when `kubectl apply` updates it) and notifying subscribers.
5. **Level 3, wiring a bean to react automatically** — `retryBean.applyConfig` is registered via `watcher.onRefresh(retryBean::applyConfig)`, meaning it will be called automatically whenever `simulateKubernetesConfigMapUpdate` fires, without `main` needing to explicitly call `applyConfig` again itself after the update.
6. **Level 3, the automatic propagation observed** — after `watcher.simulateKubernetesConfigMapUpdate` is called with an updated `ConfigMap` (`max-attempts` now `8`), `retryBean.maxAttempts` reflects `8` immediately, purely because the watcher's change-detection triggered the registered listener — this mirrors Spring Cloud Kubernetes' real capability to watch mounted `ConfigMap`/`Secret` resources and automatically trigger a [`@RefreshScope`](0234-refreshscope-for-runtime-refresh.md)-style refresh when the cluster's underlying resource changes, achieving dynamic configuration refresh through Kubernetes' own native change notification rather than requiring a Config Server and [Spring Cloud Bus](0235-spring-cloud-bus-config-for-broadcast-refresh.md) broadcast mechanism.

## 7. Gotchas & takeaways

> **Gotcha:** `ConfigMap`s and `Secret`s mounted as files into a pod update on their own schedule (Kubernetes' kubelet sync period, typically up to a minute, not instantaneous), and environment-variable-projected `ConfigMap`/`Secret` values don't update at all without a pod restart — relying on live change-detection requires the file-mount projection style specifically, not the environment-variable style, which is an easy detail to get wrong when setting this up.

- Spring Cloud Kubernetes reads configuration and secrets directly from Kubernetes' own `ConfigMap` and `Secret` resources, avoiding the need for a separate Config Server deployment for services already running on Kubernetes.
- `Secret` values are base64-encoded at the Kubernetes API level and are decoded automatically as they're merged into the application's `Environment`.
- It supports watching mounted `ConfigMap`/`Secret` resources for changes and triggering an automatic refresh, achieving dynamic configuration without a separate broadcast mechanism like Spring Cloud Bus.
- Choosing between a Config Server and Spring Cloud Kubernetes is largely a platform-fit decision — services entirely within Kubernetes benefit from native integration, while a multi-platform system may prefer one shared, platform-agnostic mechanism.
- Live change-detection depends on the file-mount projection style for `ConfigMap`/`Secret`s; environment-variable-projected values require a pod restart to pick up changes, an important distinction when designing for dynamic refresh.
