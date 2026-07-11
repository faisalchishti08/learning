---
card: spring-cloud
gi: 22
slug: serving-plain-text-binary-files
title: "Serving plain text & binary files"
---

## 1. What it is

Beyond structured `{application}/{profile}` configuration responses, Config Server can also serve arbitrary files from its backend repository directly — plain text files via `/{application}/{profile}/{label}/{path}` and generic (including binary) files via `/{application}/{profile}/{label}/{path}` with content-type-aware handling, useful for things like a `nginx.conf` template, a log4j2 XML config, or a small binary asset that needs to be environment-specific but doesn't fit the key-value property model.

```
GET /payment-service/production/main/nginx-template.conf
-> raw file content, with {{ }}-style substitution tokens resolved against the environment's properties,
   returned as plain text -- not wrapped in the usual propertySources JSON structure
```

## 2. Why & when

Every backend and resolution mechanism covered so far assumes configuration is fundamentally key-value shaped. Some configuration genuinely isn't — an entire Nginx config file, a Logback XML file, a certificate — and forcing that content into individual property keys would be awkward or simply impossible. Plain text and generic file serving is the escape hatch: the Config Server can serve *any* file from its backend, optionally resolving substitution tokens against the resolved property values first.

Reach for plain/binary file serving when:

- A configuration artifact is a whole file, not a set of key-value pairs — an Nginx template, a log configuration, a properties-format legacy config file consumed by a non-Spring component.
- The file needs its substitution tokens resolved against environment-specific values — the same `{application}/{profile}` layering used for ordinary config, applied to text inside a template file.
- A binary asset (a small icon, a certificate) needs to vary by environment and should be centrally managed the same way ordinary configuration is.

## 3. Core concept

```
 config-repo:
   nginx-template.conf:
     upstream backend {
         server {{payment.upstream.host}}:{{payment.upstream.port}};
     }
   payment-service-production.yml:
     payment.upstream.host: prod-payment.internal
     payment.upstream.port: 8081

 GET /payment-service/production/main/nginx-template.conf
 -> Config Server resolves payment-service/production's properties FIRST
 -> substitutes {{ }} substitution tokens in nginx-template.conf against those resolved properties
 -> returns:
      upstream backend {
          server prod-payment.internal:8081;
      }
```

The file's substitution tokens are resolved against the *same* layered property resolution every other card in this section covers — plain text serving reuses that resolution, just applies it to template substitution instead of a JSON property list.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A template file with substitution tokens is combined with resolved environment properties to produce a fully substituted output file">
  <rect x="20" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="130" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">nginx-template.conf ({{...}})</text>

  <rect x="20" y="80" width="220" height="45" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="107" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">resolved environment properties</text>

  <line x1="240" y1="42" x2="330" y2="72" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a42)"/>
  <line x1="240" y1="102" x2="330" y2="82" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a42)"/>

  <rect x="340" y="55" width="260" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">fully substituted output</text>

  <defs><marker id="a42" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A template file and resolved environment properties combine to produce the final, environment-specific output.

## 5. Runnable example

The scenario: serving an environment-specific Nginx configuration template, evolving from a bare template with no substitution, to a substitution engine resolving substitution tokens against a specific environment's properties, to serving that same mechanism across two different profiles — showing the same template producing genuinely different output per environment.

### Level 1 — Basic

Show a raw template file with unresolved substitution tokens — the starting point before any substitution.

```java
public class FileServingLevel1 {
    public static void main(String[] args) {
        String template =
            "upstream backend {\n" +
            "    server {{payment.upstream.host}}:{{payment.upstream.port}};\n" +
            "}\n";

        System.out.println("Raw template, unresolved:");
        System.out.println(template);
        // {{ }} substitution tokens are useless to Nginx as-is -- something needs to substitute real values in.
    }
}
```

How to run: `java FileServingLevel1.java`

The template has `{{payment.upstream.host}}`/`{{payment.upstream.port}}` substitution tokens that Nginx itself has no idea how to interpret — something needs to substitute concrete values before this file is usable.

### Level 2 — Intermediate

Add a substitution engine that resolves `{{ }}` substitution tokens against a resolved property map for one specific environment.

```java
import java.util.*;
import java.util.regex.*;

public class FileServingLevel2 {
    public static void main(String[] args) {
        String template =
            "upstream backend {\n" +
            "    server {{payment.upstream.host}}:{{payment.upstream.port}};\n" +
            "}\n";

        Map<String, String> productionProperties = Map.of(
            "payment.upstream.host", "prod-payment.internal",
            "payment.upstream.port", "8081"
        );

        String resolved = substitute(template, productionProperties);
        System.out.println("GET /payment-service/production/main/nginx-template.conf ->");
        System.out.println(resolved);
    }

    // Mirrors Config Server's token resolution: {{key}} -> resolved property value.
    static String substitute(String template, Map<String, String> properties) {
        Matcher matcher = Pattern.compile("\\{\\{([\\w.]+)\\}\\}").matcher(template);
        StringBuilder result = new StringBuilder();
        int lastEnd = 0;
        while (matcher.find()) {
            result.append(template, lastEnd, matcher.start());
            String key = matcher.group(1);
            result.append(properties.getOrDefault(key, "{{" + key + "}}")); // leave unresolved keys visible
            lastEnd = matcher.end();
        }
        result.append(template.substring(lastEnd));
        return result.toString();
    }
}
```

How to run: `java FileServingLevel2.java`

`substitute` scans for `{{key}}` patterns and replaces each with the corresponding value from `productionProperties`, exactly mirroring the token-resolution mechanism the Config Server's plain-text-serving endpoint applies before returning a requested template file.

### Level 3 — Advanced

Serve the *same* template against two different profiles' properties, demonstrating that plain-text serving reuses the exact same layered environment resolution the rest of this section covers — the file's content genuinely differs per environment, driven by the same profile-based mechanism.

```java
import java.util.*;
import java.util.regex.*;

public class FileServingLevel3 {
    public static void main(String[] args) {
        String template =
            "upstream backend {\n" +
            "    server {{payment.upstream.host}}:{{payment.upstream.port}};\n" +
            "}\n" +
            "# pool size hint: {{db.pool.size}}\n";

        EnvironmentResolver resolver = new EnvironmentResolver();
        resolver.setSharedDefaults(Map.of("db.pool.size", "10"));
        resolver.setProfileOverrides("production", Map.of(
            "payment.upstream.host", "prod-payment.internal", "payment.upstream.port", "8081", "db.pool.size", "50"));
        resolver.setProfileOverrides("staging", Map.of(
            "payment.upstream.host", "staging-payment.internal", "payment.upstream.port", "8082"));

        System.out.println("--- production ---");
        System.out.println(substitute(template, resolver.resolve("production")));

        System.out.println("--- staging ---");
        System.out.println(substitute(template, resolver.resolve("staging")));
    }

    static String substitute(String template, Map<String, String> properties) {
        Matcher matcher = Pattern.compile("\\{\\{([\\w.]+)\\}\\}").matcher(template);
        StringBuilder result = new StringBuilder();
        int lastEnd = 0;
        while (matcher.find()) {
            result.append(template, lastEnd, matcher.start());
            result.append(properties.getOrDefault(matcher.group(1), "{{" + matcher.group(1) + "}}"));
            lastEnd = matcher.end();
        }
        result.append(template.substring(lastEnd));
        return result.toString();
    }
}

// Reuses the SAME shared-defaults-plus-profile-overrides layering from earlier cards in this section.
class EnvironmentResolver {
    private Map<String, String> sharedDefaults = Map.of();
    private final Map<String, Map<String, String>> profileOverrides = new HashMap<>();
    void setSharedDefaults(Map<String, String> defaults) { this.sharedDefaults = defaults; }
    void setProfileOverrides(String profile, Map<String, String> overrides) { profileOverrides.put(profile, overrides); }
    Map<String, String> resolve(String profile) {
        Map<String, String> resolved = new HashMap<>(sharedDefaults);
        resolved.putAll(profileOverrides.getOrDefault(profile, Map.of()));
        return resolved;
    }
}
```

How to run: `java FileServingLevel3.java`

The *same* `template` string is substituted twice, against `resolver.resolve("production")` and `resolver.resolve("staging")` — `staging` doesn't override `db.pool.size`, so it falls back to the shared default of `10`, while `production` overrides it to `50`, demonstrating that file-template substitution isn't a separate, parallel mechanism from ordinary configuration resolution — it's the exact same layered resolution, just applied to substitution tokens inside a file instead of returned as a JSON property list.

## 6. Walkthrough

Execution starts in `main` for Level 3. `resolver` is configured with shared defaults and per-profile overrides, matching the layering pattern from the Config Server card earlier in this section. The `production` call resolves `payment.upstream.host`, `payment.upstream.port`, and `db.pool.size` all from the `production`-specific overrides, since all three are defined there.

`substitute` walks the template, replacing each `{{key}}` with its resolved value:

```
--- production ---
upstream backend {
    server prod-payment.internal:8081;
}
# pool size hint: 50
```

The `staging` call resolves `payment.upstream.host`/`payment.upstream.port` from its own overrides, but `db.pool.size` isn't defined there, so `resolve` falls back to the shared default of `10`:

```
--- staging ---
upstream backend {
    server staging-payment.internal:8082;
}
# pool size hint: 10
```

In a real deployment, a service or infrastructure component requesting `GET /payment-service/{profile}/main/nginx-template.conf` gets back a fully-substituted, ready-to-use configuration file — commonly fetched during container startup by an init script that writes the response directly to `/etc/nginx/nginx.conf` before the actual Nginx process starts, letting one template in the config repository serve every environment correctly.

## 7. Gotchas & takeaways

> Gotcha: unresolved substitution tokens (a typo in the template, or a property that was never actually defined for that profile) are typically left as literal `{{key}}` text in the output rather than causing a request failure — this can silently ship a broken configuration file (a template with visible, unsubstituted substitution token syntax) unless something downstream specifically validates the final output.

> Gotcha: serving binary files through this same mechanism requires being careful about content-type handling and any accidental text-based token substitution being applied to binary content — a genuinely binary file (an image, a certificate) shouldn't have its byte content scanned for `{{ }}` patterns, since a coincidental byte sequence could be corrupted by an unintended "substitution."

- Config Server can serve whole files — plain text templates or binary assets — directly from its backend, not just structured key-value configuration.
- Text file serving reuses the exact same layered `{application}/{profile}` property resolution as the rest of the Config Server, applying it as token substitution inside the file rather than as a JSON response.
- The same template file can produce genuinely different output per environment, driven entirely by which profile's properties get resolved and substituted in.
- Unresolved substitution tokens typically fail silently (left as literal text) rather than causing a request error — validating the final substituted output is worth doing for anything critical.
