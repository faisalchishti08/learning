---
card: spring-boot
gi: 183
slug: custom-endpoints-endpoint-readoperation-writeoperation-delet
title: "Custom endpoints (@Endpoint, @ReadOperation, @WriteOperation, @DeleteOperation)"
---

## 1. What it is

Beyond the built-in Actuator endpoints, you can create your own by annotating a bean with `@Endpoint` (or its specialisations) and annotating methods with `@ReadOperation` (HTTP GET / JMX getAttribute), `@WriteOperation` (HTTP POST / JMX operation), or `@DeleteOperation` (HTTP DELETE). Spring Boot auto-detects these beans and registers them under `/actuator/<endpoint-id>` — no controller, no URL mapping needed.

## 2. Why & when

Built-in endpoints cover generic JVM and Spring concerns. Custom endpoints are for **application-specific operational queries**:
- Expose feature-flag state: `GET /actuator/features` returns which features are enabled.
- Trigger a cache refresh: `POST /actuator/cache/refresh` invalidates and reloads a named cache.
- Query a connection pool: `GET /actuator/poolstats` returns custom pool metrics not in Micrometer.
- Expose tenant configuration: `GET /actuator/tenants/{id}` for multi-tenant SaaS platforms.

**When not to use custom endpoints:** if the information belongs in the application's API (e.g., `/api/status`), put it there. Actuator is for operational visibility, not business data.

## 3. Core concept

```java
@Component
@Endpoint(id = "features")  // exposes at /actuator/features
public class FeaturesEndpoint {

    @ReadOperation
    public Map<String, Boolean> features() { ... }  // GET /actuator/features

    @ReadOperation
    public Boolean feature(@Selector String name) { ... }  // GET /actuator/features/{name}

    @WriteOperation
    public void toggle(@Selector String name, boolean enabled) { ... }  // POST

    @DeleteOperation
    public void remove(@Selector String name) { ... }  // DELETE /actuator/features/{name}
}
```

Key rules:
- `@Endpoint(id)`: the `id` becomes the URL segment. Must be kebab-case, e.g., `feature-flags`.
- `@Selector` on a parameter: maps to a URL path variable (`{name}`).
- Return types: `Map<String, Object>`, a POJO, or `void` (204). Spring serialises to JSON.
- No `@RequestBody` needed on `@WriteOperation` — parameters are mapped from the JSON request body by name.
- `@Endpoint` works over both HTTP and JMX. `@WebEndpoint` is HTTP-only; `@JmxEndpoint` is JMX-only.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Endpoint bean with three annotated methods; Spring registers them as GET, POST, DELETE under /actuator/features">
  <!-- Endpoint bean -->
  <rect x="10" y="40" width="280" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="62" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Endpoint(id="features")</text>
  <text x="150" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Component  FeaturesEndpoint</text>

  <!-- Methods -->
  <rect x="22" y="86" width="256" height="24" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="150" y="103" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@ReadOperation  Map&lt;&gt; features()</text>

  <rect x="22" y="116" width="256" height="24" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="150" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@ReadOperation  Boolean feature(@Selector String name)</text>

  <rect x="22" y="146" width="256" height="24" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="150" y="163" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@WriteOperation  void toggle(@Selector String, boolean)</text>

  <rect x="22" y="176" width="256" height="14" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="150" y="187" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@DeleteOperation  void remove(@Selector String name)</text>

  <!-- Spring wires -->
  <line x1="293" y1="115" x2="360" y2="115" stroke="#6db33f" stroke-width="2" marker-end="url(#xa)"/>
  <text x="325" y="108" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">auto-detected</text>

  <!-- HTTP endpoints -->
  <rect x="365" y="50" width="310" height="150" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">/actuator/features</text>

  <text x="380" y="95" fill="#6db33f" font-size="9" font-family="sans-serif">GET  /actuator/features           → @ReadOperation</text>
  <text x="380" y="112" fill="#6db33f" font-size="9" font-family="sans-serif">GET  /actuator/features/{name}    → @ReadOperation @Selector</text>
  <text x="380" y="129" fill="#79c0ff" font-size="9" font-family="sans-serif">POST /actuator/features/{name}    → @WriteOperation @Selector</text>
  <text x="380" y="146" fill="#8b949e" font-size="9" font-family="sans-serif">DEL  /actuator/features/{name}    → @DeleteOperation</text>
  <text x="380" y="168" fill="#8b949e" font-size="9" font-family="sans-serif">Also exposed as JMX MBeans</text>

  <defs>
    <marker id="xa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

One `@Endpoint` bean, three annotated methods → four HTTP routes registered automatically by Spring Boot.

## 5. Runnable example

```java
// CustomEndpointDemo.java — demonstrates @Endpoint / @ReadOperation / @WriteOperation / @DeleteOperation
// How to run: java CustomEndpointDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: annotate a @Component with @Endpoint; Spring auto-registers under /actuator/<id>

import java.util.*;

public class CustomEndpointDemo {

    // Simulates the FeaturesEndpoint bean
    // In Spring Boot: @Component @Endpoint(id = "features")
    static class FeaturesEndpoint {
        private final Map<String, Boolean> features = new LinkedHashMap<>(Map.of(
            "new-checkout",   true,
            "dark-mode",      false,
            "ai-search",      true
        ));

        // @ReadOperation  → GET /actuator/features
        Map<String, Boolean> features() {
            return Collections.unmodifiableMap(features);
        }

        // @ReadOperation  → GET /actuator/features/{name}   (@Selector String name)
        Boolean feature(String name) {
            return features.get(name);
        }

        // @WriteOperation  → POST /actuator/features/{name}   body: {"enabled": true}
        Map<String, Object> toggle(String name, boolean enabled) {
            if (!features.containsKey(name)) {
                return Map.of("error", "unknown feature: " + name);
            }
            boolean previous = features.put(name, enabled);
            return Map.of("feature", name, "previous", previous, "current", enabled);
        }

        // @DeleteOperation  → DELETE /actuator/features/{name}
        void remove(String name) {
            features.remove(name);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Custom @Endpoint Demo ===\n");
        var endpoint = new FeaturesEndpoint();

        // GET /actuator/features
        System.out.println("GET /actuator/features");
        System.out.println("  " + endpoint.features());

        // GET /actuator/features/dark-mode
        System.out.println("\nGET /actuator/features/dark-mode");
        System.out.println("  enabled: " + endpoint.feature("dark-mode"));

        // POST /actuator/features/dark-mode  body: {"enabled": true}
        System.out.println("\nPOST /actuator/features/dark-mode  {\"enabled\": true}");
        System.out.println("  response: " + endpoint.toggle("dark-mode", true));

        // GET again to verify
        System.out.println("\nGET /actuator/features (after toggle)");
        System.out.println("  " + endpoint.features());

        // POST with unknown feature
        System.out.println("\nPOST /actuator/features/nonexistent  {\"enabled\": true}");
        System.out.println("  response: " + endpoint.toggle("nonexistent", true));

        // DELETE /actuator/features/ai-search
        System.out.println("\nDELETE /actuator/features/ai-search");
        endpoint.remove("ai-search");
        System.out.println("  after delete: " + endpoint.features());

        System.out.println("\n--- Spring Boot wiring (no code change needed) ---");
        System.out.println("@Component @Endpoint(id=\"features\") class FeaturesEndpoint { ... }");
        System.out.println("management.endpoints.web.exposure.include=features");
        System.out.println("=> /actuator/features registered automatically");
    }
}
```

**How to run:** `java CustomEndpointDemo.java`

## 6. Walkthrough

- **`features()`** annotated with `@ReadOperation` → Spring maps `GET /actuator/features`. Return type `Map` → serialised to JSON.
- **`feature(String name)`** also `@ReadOperation` but with a `@Selector` parameter → maps to `GET /actuator/features/{name}`. Spring extracts the path variable and passes it as the argument.
- **`toggle(String name, boolean enabled)`** `@WriteOperation` with `@Selector` → `POST /actuator/features/{name}`. Non-selector parameters come from the JSON request body — Spring maps `{"enabled": true}` to the `enabled` parameter automatically.
- **`remove(String name)`** `@DeleteOperation` → `DELETE /actuator/features/{name}`. Returns `void` → HTTP 204 No Content.
- The unknown-feature case returns an error map — Spring serialises it as a 200 with error body. For proper 404, throw `EndpointNotFoundException` or return `null` (Spring sends 404).

## 7. Gotchas & takeaways

> `@Endpoint` is exposed over **both HTTP and JMX** by default. If your operation has side effects not safe for JMX tooling, use `@WebEndpoint` (HTTP only) instead.

> `@WriteOperation` parameters come from the **JSON request body**, not query params. A POST to `/actuator/features/dark-mode` with `?enabled=true` does NOT work — the body must be `{"enabled": true}`.

- To expose the custom endpoint: add its `id` to `management.endpoints.web.exposure.include` or use `include=*`.
- `@Endpoint(id="my-endpoint")` — the id must be kebab-case; camelCase is not valid and causes startup failure.
- Return `null` from a `@ReadOperation` → 404 Not Found. Return a `void` `@ReadOperation` → not possible (compiler error); use a no-arg `@WriteOperation` instead.
- Test with `WebMvcTest` + `@Import(MyEndpoint.class)` and `MockMvc` requests to `/actuator/my-endpoint`.
- `@EndpointWebExtension(endpoint=FeaturesEndpoint.class)` can add HTTP-specific behaviour (e.g., returning `ResponseEntity`) without changing the endpoint's JMX interface.
