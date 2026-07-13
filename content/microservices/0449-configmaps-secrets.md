---
card: microservices
gi: 449
slug: configmaps-secrets
title: "ConfigMaps & Secrets"
---

## 1. What it is

A **ConfigMap** and a **Secret** are Kubernetes objects that hold configuration data outside of a container image, made available to Pods as environment variables or mounted files. A ConfigMap holds non-sensitive settings (log levels, feature flags, connection pool sizes); a Secret holds sensitive values (passwords, API keys, TLS certificates) that Kubernetes stores and handles with additional care — access control, base64 encoding at rest, and (in most clusters) encryption at rest. Both exist to answer the same question a container asks at startup: "what are my settings, right now, in this environment?" — without that answer being baked into the image itself.

## 2. Why & when

You need externalized configuration the moment the same image needs to behave differently across environments, or the moment any configuration value is sensitive enough that it can't live in source control:

- **Hardcoded configuration forces a rebuild for every change.** If a connection pool size or a feature flag is compiled into the image, changing it means rebuilding, re-tagging, and redeploying — even though nothing about the actual code changed. This is the exact problem [externalized config & stateless processes](0443-externalized-config-stateless-processes.md) and the twelve-factor "config" principle exist to solve; ConfigMaps and Secrets are the Kubernetes-native mechanism for it.
- **Secrets checked into source control are a standing liability.** A database password embedded in a Dockerfile or a properties file committed to git remains readable in that repository's history forever, even after it's "removed" in a later commit. Kubernetes Secrets keep sensitive values out of the image and out of source control entirely.
- **The same image needs to run in dev, staging, and production with different settings** — different database hosts, different feature-flag states, different log verbosity — without maintaining separate images per environment.
- **You configure this for every deployable service from the start**, not as an afterthought: any setting likely to differ by environment belongs in a ConfigMap, and any sensitive value belongs in a Secret, from the very first deployment manifest you write.

## 3. Core concept

Think of a shipping container versus its packing slip. The container (the image) holds the same goods no matter where it's shipped. The packing slip (ConfigMap/Secret) is attached at the destination and tells the recipient site-specific details — which warehouse door to use, which account to bill — without anyone having to repack the container itself. Kubernetes attaches configuration to a Pod the same way: the image stays identical across environments, and a ConfigMap or Secret supplies whatever varies.

Concretely, the mechanics are:

1. **ConfigMaps and Secrets are both key-value stores**, created independently of any Pod, then referenced by Pods that need them.
2. **They can be injected two ways**: as environment variables (read once, at container startup, and frozen for the container's lifetime) or as mounted files in a volume (which the kubelet can update on disk while the container keeps running, without a restart).
3. **Secrets get extra handling**: values are base64-encoded at rest (not itself encryption, but avoiding plaintext binary issues), access is typically restricted via role-based access control, and mature clusters encrypt Secret data at rest — none of which applies to ConfigMaps, which are meant to be freely readable.
4. **Rotation behavior depends entirely on injection method.** An environment variable captured at startup never changes until the container restarts, even if the underlying Secret is updated. A mounted volume is periodically synced by the kubelet, so a container that re-reads the file (rather than caching the value once) picks up rotation without a restart — a critical distinction for credentials that must be rotated regularly.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ConfigMap and a Secret are both injected into a Pod, either as environment variables captured once at startup or as mounted files that can update live without a restart">
  <rect x="20" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="95" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ConfigMap</text>

  <rect x="20" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="95" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Secret</text>

  <rect x="240" y="50" width="160" height="70" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="80" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Pod</text>
  <text x="320" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">env vars or mounted files</text>

  <line x1="170" y1="45" x2="240" y2="75" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="170" y1="115" x2="240" y2="90" stroke="#f0883e" marker-end="url(#a2)"/>

  <rect x="440" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="525" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">env var: frozen at startup</text>
  <text x="525" y="58" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">needs restart to see rotation</text>

  <rect x="440" y="90" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="525" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">mounted file: synced live</text>
  <text x="525" y="128" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">no restart needed for rotation</text>

  <line x1="400" y1="65" x2="440" y2="45" stroke="#8b949e" stroke-dasharray="3,2"/>
  <line x1="400" y1="90" x2="440" y2="115" stroke="#8b949e" stroke-dasharray="3,2"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#f0883e"/></marker>
  </defs>
</svg>

Both ConfigMaps and Secrets attach to a Pod the same way, but how they're injected — env var versus mounted file — determines whether the Pod sees a later change without needing a restart.

## 5. Runnable example

Scenario: an `order-service` reading its configuration at startup. We start by contrasting hardcoded values with an externally supplied config source, split that source into a ConfigMap-like and a Secret-like part (masking the sensitive one whenever it's logged), then handle the hard case: rotating a secret while the service is running, and observing that only the mounted-file-style source picks up the change without a restart.

### Level 1 — Basic

```java
// File: HardcodedVsExternalConfig.java -- contrasts hardcoded config
// (baked into the image, requires a rebuild to change) with config read
// from an EXTERNAL source at startup (a stand-in for a mounted ConfigMap).
import java.util.*;

public class HardcodedVsExternalConfig {
    // BAD: baked into the compiled artifact. Changing this means rebuilding
    // and redeploying the image, even though nothing about the CODE changed.
    static final String HARDCODED_MAX_CONNECTIONS = "10";

    public static void main(String[] args) {
        System.out.println("Hardcoded config: maxConnections=" + HARDCODED_MAX_CONNECTIONS + " (baked into the image)");

        // GOOD: a stand-in for a ConfigMap mounted as files/env vars, read
        // fresh at startup -- the SAME image works across environments.
        Map<String, String> externalConfig = new HashMap<>();
        externalConfig.put("max.connections", "50");
        externalConfig.put("feature.newCheckout", "true");

        String maxConnections = externalConfig.getOrDefault("max.connections", "5"); // fallback default
        String newCheckoutEnabled = externalConfig.getOrDefault("feature.newCheckout", "false");

        System.out.println("External config: maxConnections=" + maxConnections + " (read at startup, image unchanged)");
        System.out.println("External config: feature.newCheckout=" + newCheckoutEnabled);
    }
}
```

How to run: `java HardcodedVsExternalConfig.java`

`HARDCODED_MAX_CONNECTIONS` is a compile-time constant — changing it means editing code and rebuilding the image. `externalConfig` stands in for a ConfigMap: the same compiled program reads whatever values happen to be present in its environment, with sane fallback defaults (`getOrDefault`) for anything missing, so the image itself never needs to change to run differently in a different environment.

### Level 2 — Intermediate

```java
// File: ConfigMapAndSecretMerge.java -- the SAME startup-config idea, now
// split into TWO sources like Kubernetes does: a ConfigMap for non-secret
// settings (safe to log, safe to view in plain text) and a Secret for
// sensitive values (must be masked whenever it's logged or displayed).
import java.util.*;

public class ConfigMapAndSecretMerge {
    static class AppConfig {
        final Map<String, String> settings; // from a ConfigMap -- not sensitive
        final Map<String, String> secrets;   // from a Secret -- sensitive

        AppConfig(Map<String, String> settings, Map<String, String> secrets) {
            this.settings = settings; this.secrets = secrets;
        }

        String get(String key) {
            if (secrets.containsKey(key)) return secrets.get(key);
            return settings.get(key);
        }

        // Sensitive values are NEVER printed as-is, even for debugging.
        String describeForLogging() {
            StringBuilder sb = new StringBuilder("AppConfig{");
            settings.forEach((k, v) -> sb.append(k).append("=").append(v).append(", "));
            secrets.keySet().forEach(k -> sb.append(k).append("=****, "));
            sb.append("}");
            return sb.toString();
        }
    }

    public static void main(String[] args) {
        Map<String, String> configMap = Map.of(
                "max.connections", "50",
                "log.level", "INFO");
        Map<String, String> secret = Map.of(
                "db.password", "s3cr3t-value",
                "api.key", "abc123xyz");

        AppConfig config = new AppConfig(configMap, secret);

        System.out.println("Safe to log: " + config.describeForLogging());
        System.out.println("Actual db.password used internally (never logged): " + config.get("db.password"));
    }
}
```

How to run: `java ConfigMapAndSecretMerge.java`

`AppConfig` merges two sources with different trust levels: `settings` (ConfigMap-equivalent) is safe to print verbatim, while `secrets` (Secret-equivalent) is masked as `****` the moment it's formatted for logging, even though the real value is still used internally for actual database calls via `get()`. This mirrors the operational discipline Secrets require: the *value* flows through the application normally, but it must never appear in logs, error messages, or debug output.

### Level 3 — Advanced

```java
// File: SecretRotationAdvanced.java -- the SAME config model, now handling
// a PRODUCTION-FLAVORED hard case: a Secret is ROTATED while the app is
// still running. An env-var-style source was captured once at startup and
// never changes; a volume-mount-style source is re-read on each use and
// picks up the rotated value WITHOUT a restart.
import java.util.*;

public class SecretRotationAdvanced {
    // Stand-in for the underlying Secret store, which an operator rotates.
    static final Map<String, String> secretStore = new HashMap<>(Map.of("db.password", "old-password-v1"));

    // Stand-in for env-var injection: read ONCE, at container startup.
    static class EnvVarConfigSource {
        final String dbPasswordAtStartup;
        EnvVarConfigSource() { this.dbPasswordAtStartup = secretStore.get("db.password"); }
        String dbPassword() { return dbPasswordAtStartup; } // frozen forever, until the container restarts
    }

    // Stand-in for a mounted Secret volume: re-read from disk on every access.
    static class VolumeMountConfigSource {
        String dbPassword() { return secretStore.get("db.password"); } // reflects the current file contents
    }

    public static void main(String[] args) {
        EnvVarConfigSource envSource = new EnvVarConfigSource();
        VolumeMountConfigSource volumeSource = new VolumeMountConfigSource();

        System.out.println("At startup:");
        System.out.println("  env-var source:      " + envSource.dbPassword());
        System.out.println("  volume-mount source:  " + volumeSource.dbPassword());

        System.out.println("Operator rotates the secret (old-password-v1 -> new-password-v2), NO restart happens:");
        secretStore.put("db.password", "new-password-v2");

        System.out.println("  env-var source:      " + envSource.dbPassword() + "  <- STALE, will keep failing DB auth until restarted");
        System.out.println("  volume-mount source:  " + volumeSource.dbPassword() + "  <- picked up the rotation immediately");

        boolean envAuthWouldSucceed = envSource.dbPassword().equals(secretStore.get("db.password"));
        boolean volumeAuthWouldSucceed = volumeSource.dbPassword().equals(secretStore.get("db.password"));
        System.out.println();
        System.out.println("Would DB auth succeed right now? env-var source: " + envAuthWouldSucceed
                + ", volume-mount source: " + volumeAuthWouldSucceed);

        System.out.println("Restarting the container picking up env vars fresh...");
        EnvVarConfigSource envSourceAfterRestart = new EnvVarConfigSource();
        System.out.println("  env-var source after restart: " + envSourceAfterRestart.dbPassword() + "  <- now current");
    }
}
```

How to run: `java SecretRotationAdvanced.java`

`EnvVarConfigSource` captures `dbPasswordAtStartup` once, in its constructor, exactly like an environment variable is fixed for a container's entire lifetime. `VolumeMountConfigSource` instead re-reads `secretStore` on every call to `dbPassword()`, exactly like a container reading a mounted Secret file fresh each time it's needed. When the operator rotates the password mid-run, the env-var source keeps returning the stale value — silently failing future database authentication attempts — until the container is restarted, while the volume-mount source reflects the new value immediately.

## 6. Walkthrough

Trace `SecretRotationAdvanced.main` in order. **First**, `envSource` and `volumeSource` are both constructed while `secretStore` holds `"old-password-v1"`. `envSource`'s constructor runs `dbPasswordAtStartup = secretStore.get("db.password")`, capturing `"old-password-v1"` into a `final` field. `volumeSource` captures nothing at construction — it has no fields to freeze.

**Next**, both sources are queried and print identically: `"old-password-v1"` for both, since nothing has changed yet.

**Then**, the simulated rotation runs: `secretStore.put("db.password", "new-password-v2")` updates the underlying store, modeling an operator (or an automated rotation tool, per [secrets management & rotation](0394-secrets-management-rotation.md)) pushing a new credential.

**After that**, both sources are queried again. `envSource.dbPassword()` returns the `final` field `dbPasswordAtStartup`, which was fixed at construction time and is structurally incapable of reflecting the update — it still returns `"old-password-v1"`. `volumeSource.dbPassword()` re-reads `secretStore` directly on each call, so it returns `"new-password-v2"` immediately. The two boolean checks confirm the consequence: an auth attempt using the env-var source would fail (`false`, since it no longer matches the real, current secret), while the volume-mount source would succeed (`true`).

**Finally**, a brand-new `EnvVarConfigSource` is constructed, modeling a container restart. Its constructor now reads the current, rotated value, so it prints `"new-password-v2"` — confirming that the env-var source is not permanently broken, only stale until the next restart.

```
At startup:
  env-var source:      old-password-v1
  volume-mount source:  old-password-v1
Operator rotates the secret (old-password-v1 -> new-password-v2), NO restart happens:
  env-var source:      old-password-v1  <- STALE, will keep failing DB auth until restarted
  volume-mount source:  new-password-v2  <- picked up the rotation immediately

Would DB auth succeed right now? env-var source: false, volume-mount source: true
Restarting the container picking up env vars fresh...
  env-var source after restart: new-password-v2  <- now current
```

## 7. Gotchas & takeaways

> Choosing environment variables for a Secret that gets rotated regularly is a subtle, delayed-failure trap: everything works fine at deploy time, and the failure only surfaces later, at the next rotation, when every running Pod that hasn't restarted since starts failing authentication simultaneously — often long after whoever chose the injection method has moved on to other work.

- Prefer mounted-volume injection over environment variables for any Secret subject to rotation; env vars are simpler but are frozen for the life of the container, exactly as Level 3 demonstrates.
- Never log a Secret value directly, even for debugging — mask it structurally (as `describeForLogging` does in Level 2) so there's no code path that can accidentally print it.
- ConfigMaps and Secrets both decouple configuration from the image, which is exactly the discipline [externalized config & stateless processes](0443-externalized-config-stateless-processes.md) and the twelve-factor principles (see [twelve-factor app principles](0442-twelve-factor-app-principles.md)) call for — the Kubernetes objects are one concrete implementation of that broader idea.
- Base64 encoding, which Kubernetes applies to Secret values at rest, is an encoding, not encryption — treat cluster access control and at-rest encryption as the actual security boundary, not the encoding itself.
- A Pod's registration for traffic should generally wait until it has successfully loaded its configuration and secrets, tying into the readiness gating covered in [service instance registration on deploy](0455-service-instance-registration-on-deploy.md).
