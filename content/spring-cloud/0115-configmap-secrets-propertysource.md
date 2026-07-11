---
card: spring-cloud
gi: 115
slug: configmap-secrets-propertysource
title: "ConfigMap & Secrets PropertySource"
---

## 1. What it is

Spring Cloud Kubernetes reads Kubernetes ConfigMaps and Secrets mounted or associated with an application's pod and exposes their key-value data as ordinary Spring `PropertySource` entries in the application's `Environment` — a ConfigMap named `order-service` with a `rate-limit: "100/min"` entry becomes readable as `@Value("${rate-limit}")` exactly like a properties-file entry would be, with Secrets handled identically but automatically base64-decoded, since Kubernetes stores Secret values base64-encoded by convention.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: order-service
data:
  rate-limit: "100/min"
  feature.new-checkout: "true"
```

```java
@Value("${rate-limit}")
String rateLimit; // resolved from the ConfigMap named "order-service", matching spring.application.name
```

## 2. Why & when

Kubernetes already provides ConfigMaps and Secrets as its own native configuration mechanism, decoupled from container images and independently updatable — but without Spring Cloud Kubernetes, consuming them from a Spring Boot application would mean either mounting them as environment variables (limited to flat key-value pairs, awkward for anything more structured) or as files (requiring custom file-parsing code the application would need to write itself). The ConfigMap/Secrets `PropertySource` closes this gap by reading them directly through the Kubernetes API (or from mounted volumes) and integrating them into Spring's existing, already-familiar `Environment`/`@Value`/`@ConfigurationProperties` resolution mechanism, so a ConfigMap entry is consumed exactly like any other Spring property, with no custom parsing code needed.

Reach for the ConfigMap/Secrets `PropertySource` when:

- Deploying to Kubernetes and wanting configuration to live in Kubernetes-native ConfigMap/Secret objects rather than in a separately-deployed Config Server — this keeps configuration management consistent with how the rest of a Kubernetes-native deployment typically manages its settings.
- Storing sensitive values (database passwords, API keys) that should be Kubernetes Secrets rather than plain ConfigMaps — Spring Cloud Kubernetes handles the base64 decoding transparently, so `@Value` bindings work identically for both, with the security distinction (encryption at rest, access control) handled at the Kubernetes Secret level rather than in application code.
- An application needs configuration that can be updated without a redeploy — updating a ConfigMap's data and (with reload enabled, a later card) having the running application pick up the change automatically is a common Kubernetes-native pattern this `PropertySource` enables.

## 3. Core concept

```
 Kubernetes ConfigMap "order-service":
   data: { rate-limit: "100/min", feature.new-checkout: "true" }

 Kubernetes Secret "order-service-db":
   data: { password: "aHVudGVyMg==" }   <- base64-encoded, Kubernetes convention

        |
        v (Spring Cloud Kubernetes reads BOTH, via the Kubernetes API or mounted volumes)

 Spring Environment (merged PropertySource):
   rate-limit=100/min
   feature.new-checkout=true
   password=hunter2    <- AUTOMATICALLY base64-DECODED before landing in the Environment
```

Both ConfigMap and Secret data land in the same unified `Environment`, resolved by `@Value`/`@ConfigurationProperties` identically — the only functional difference application code needs to care about is which Kubernetes object type a given key's value should live in, based on sensitivity.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ConfigMap and a Secret are both read by Spring Cloud Kubernetes and merged into the Spring Environment with Secret values automatically base64 decoded so Value annotated fields consume both identically">
  <rect x="20" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">ConfigMap</text>
  <text x="110" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">rate-limit: "100/min"</text>

  <rect x="20" y="90" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="112" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Secret</text>
  <text x="110" y="126" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">password: (base64)</text>

  <rect x="280" y="55" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="77" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Spring Environment</text>
  <text x="370" y="91" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">merged, Secret auto-decoded</text>

  <rect x="510" y="55" width="110" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="565" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@Value field</text>

  <defs><marker id="a115" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="43" x2="280" y2="70" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a115)"/>
  <line x1="200" y1="113" x2="280" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a115)"/>
  <line x1="460" y1="78" x2="510" y2="78" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a115)"/>
</svg>

Two distinct Kubernetes object types, one merged and uniformly-consumable Spring `Environment` on the other side.

## 5. Runnable example

The scenario: model reading and merging ConfigMap and Secret data into a unified property environment, with Secret values automatically base64-decoded — proving `@Value`-equivalent consumption is identical regardless of source object type. Start with ConfigMap-only resolution, then add Secret resolution with decoding, then add a key collision case to show precedence between the two.

### Level 1 — Basic

Reading ConfigMap data as ordinary properties.

```java
import java.util.*;

public class ConfigMapSecretsLevel1 {
    static Map<String, String> readConfigMap(Map<String, String> configMapData) {
        return new HashMap<>(configMapData); // plain values, used AS-IS
    }

    public static void main(String[] args) {
        Map<String, String> configMap = Map.of("rate-limit", "100/min", "feature.new-checkout", "true");

        Map<String, String> environment = readConfigMap(configMap);
        System.out.println("rate-limit=" + environment.get("rate-limit"));
        System.out.println("feature.new-checkout=" + environment.get("feature.new-checkout"));
    }
}
```

How to run: `java ConfigMapSecretsLevel1.java`

ConfigMap values are consumed exactly as stored, with no transformation — this is the simpler of the two source types, since Kubernetes ConfigMaps store plain text values, unlike Secrets' base64 convention.

### Level 2 — Intermediate

Add Secret reading with base64 decoding, merged alongside ConfigMap data into one unified environment.

```java
import java.util.*;

public class ConfigMapSecretsLevel2 {
    static Map<String, String> readConfigMap(Map<String, String> configMapData) {
        return new HashMap<>(configMapData);
    }

    // Kubernetes Secrets store values base64-ENCODED by convention -- Spring Cloud Kubernetes decodes them automatically
    static Map<String, String> readSecret(Map<String, String> secretDataBase64) {
        Map<String, String> decoded = new HashMap<>();
        for (Map.Entry<String, String> entry : secretDataBase64.entrySet()) {
            byte[] decodedBytes = Base64.getDecoder().decode(entry.getValue());
            decoded.put(entry.getKey(), new String(decodedBytes));
        }
        return decoded;
    }

    public static void main(String[] args) {
        Map<String, String> configMap = Map.of("rate-limit", "100/min");
        Map<String, String> secret = Map.of("password", Base64.getEncoder().encodeToString("hunter2".getBytes()));

        Map<String, String> environment = new HashMap<>();
        environment.putAll(readConfigMap(configMap));
        environment.putAll(readSecret(secret)); // MERGED into the same environment

        System.out.println("rate-limit=" + environment.get("rate-limit"));
        System.out.println("password=" + environment.get("password") + " (automatically decoded, NOT the raw base64)");
    }
}
```

How to run: `java ConfigMapSecretsLevel2.java`

`environment.get("password")` prints the plain-text `"hunter2"`, not the base64-encoded string the Secret actually stores — `readSecret`'s decoding step happened transparently before the value ever landed in `environment`, exactly mirroring how a real `@Value("${password}")` field never sees base64-encoded data, only the already-decoded plain value.

### Level 3 — Advanced

Add a key collision between ConfigMap and Secret data, demonstrating precedence order, plus a case handling a malformed base64 Secret value without crashing the whole environment build.

```java
import java.util.*;

public class ConfigMapSecretsLevel3 {
    static Map<String, String> readConfigMap(Map<String, String> configMapData) {
        return new HashMap<>(configMapData);
    }

    static Map<String, String> readSecret(Map<String, String> secretDataBase64) {
        Map<String, String> decoded = new HashMap<>();
        for (Map.Entry<String, String> entry : secretDataBase64.entrySet()) {
            try {
                byte[] decodedBytes = Base64.getDecoder().decode(entry.getValue());
                decoded.put(entry.getKey(), new String(decodedBytes));
            } catch (IllegalArgumentException e) {
                // one malformed Secret entry shouldn't prevent the REST of the environment from resolving
                System.out.println("WARNING: could not decode Secret key '" + entry.getKey() + "' -- skipping: " + e.getMessage());
            }
        }
        return decoded;
    }

    // Secrets take precedence over ConfigMaps for the SAME key -- mirrors Spring Cloud Kubernetes's own ordering
    static Map<String, String> buildEnvironment(Map<String, String> configMap, Map<String, String> secretBase64) {
        Map<String, String> environment = new HashMap<>();
        environment.putAll(readConfigMap(configMap));   // lower precedence, applied FIRST
        environment.putAll(readSecret(secretBase64));   // higher precedence, applied SECOND -- overwrites on collision
        return environment;
    }

    public static void main(String[] args) {
        Map<String, String> configMap = Map.of(
                "rate-limit", "100/min",
                "shared-key", "from-configmap" // will COLLIDE with the Secret below
        );
        Map<String, String> secret = Map.of(
                "password", Base64.getEncoder().encodeToString("hunter2".getBytes()),
                "shared-key", Base64.getEncoder().encodeToString("from-secret".getBytes()),
                "corrupted-entry", "not-valid-base64!!!" // deliberately malformed
        );

        Map<String, String> environment = buildEnvironment(configMap, secret);

        System.out.println("shared-key=" + environment.get("shared-key") + " (Secret wins the collision)");
        System.out.println("password=" + environment.get("password"));
        System.out.println("corrupted-entry present? " + environment.containsKey("corrupted-entry"));
    }
}
```

How to run: `java ConfigMapSecretsLevel3.java`

`shared-key` resolves to `"from-secret"`, not `"from-configmap"`, because `readSecret`'s results are merged in *after* `readConfigMap`'s via `putAll`, and a later `putAll` call overwrites earlier entries for the same key; `corrupted-entry` never makes it into `environment` at all, since `readSecret`'s `catch` block skips it with a warning rather than letting the invalid base64 crash the entire environment-building process, so `rate-limit` and `password` (both entirely unrelated to the malformed entry) resolve correctly regardless.

## 6. Walkthrough

Trace `buildEnvironment` in Level 3.

1. `readConfigMap(configMap)` returns a map with two entries: `rate-limit=100/min` and `shared-key=from-configmap`.
2. `environment.putAll(...)` merges these two entries into the initially-empty `environment` map.
3. `readSecret(secret)` processes three entries. For `"password"`, the base64 value decodes successfully to `"hunter2"`. For `"shared-key"`, the base64 value decodes successfully to `"from-secret"`. For `"corrupted-entry"`, `Base64.getDecoder().decode("not-valid-base64!!!")` throws `IllegalArgumentException` (the string contains characters outside the base64 alphabet), which the `catch` block catches, printing a warning and simply not adding that key to the returned map at all.
4. `readSecret` returns a map with exactly two entries: `password=hunter2` and `shared-key=from-secret` — `corrupted-entry` is entirely absent, having been skipped.
5. `environment.putAll(...)` merges these two entries into `environment` — for `password`, this is a new key, simply added; for `shared-key`, this key already exists in `environment` (from step 2, with value `"from-configmap"`), so `putAll` overwrites it with the Secret's value, `"from-secret"`.
6. The final `environment` map contains `rate-limit=100/min` (untouched, ConfigMap-only), `shared-key=from-secret` (Secret's value won the collision), `password=hunter2` (Secret-only), and no `corrupted-entry` key at all — exactly matching the three printed lines' expectations.

```
readConfigMap -> {rate-limit: 100/min, shared-key: from-configmap}
readSecret    -> {password: hunter2, shared-key: from-secret}          (corrupted-entry SKIPPED, with a warning)

environment after BOTH putAll calls (Secret applied SECOND, so it wins on collision):
  rate-limit=100/min       (ConfigMap only)
  shared-key=from-secret   (Secret OVERWROTE ConfigMap's value)
  password=hunter2         (Secret only)
  corrupted-entry: ABSENT
```

## 7. Gotchas & takeaways

> **Gotcha:** relying on ConfigMap/Secret key collisions for intentional overriding behavior (deliberately duplicating a key across both, expecting the Secret to always win) is fragile and easy to misunderstand later — it's generally clearer and less error-prone to keep ConfigMap and Secret keys entirely distinct, using Secrets purely for genuinely sensitive values and ConfigMaps for everything else, rather than relying on precedence ordering as a design pattern.

- ConfigMap and Secret data both flow into the same unified Spring `Environment`, consumed identically by `@Value`/`@ConfigurationProperties` — the distinction between the two Kubernetes object types matters for security and storage (Secrets are base64-encoded and typically subject to tighter access control), not for how application code consumes the resolved values.
- Automatic base64 decoding of Secret values is essential and easy to take for granted — application code should never need to manually decode a Secret-sourced property, and if it does, that's a signal the `PropertySource` integration isn't working as expected.
- A malformed or partially-invalid Secret entry should not be allowed to prevent an entire application's configuration from resolving — isolating and skipping (with a clear warning) one bad entry, as Level 3 modeled, is far preferable to a startup failure that offers no clue which specific key caused it.
- Later cards in this section cover config reload on change (picking up ConfigMap/Secret updates without a redeploy) and leader election, both building further on this `PropertySource` foundation and the broader Spring Cloud Kubernetes integration this section covers.
