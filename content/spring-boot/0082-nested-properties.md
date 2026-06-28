---
card: spring-boot
gi: 82
slug: nested-properties
title: Nested properties
---

## 1. What it is

`@ConfigurationProperties` is not limited to a flat list of simple key-value pairs. Any field whose type is a POJO, a Java record, a `List`, or a `Map` is also bound — recursively. Spring Boot walks the object graph and matches property keys to nested field paths using the same relaxed-binding rules that apply at the top level.

In a `.properties` file, nesting is expressed with **dotted paths**: `myapp.database.host`, `myapp.database.pool.min-size`. In YAML, the same structure is expressed with **indentation**. Both notations resolve to the same bound object.

This means you can model your configuration as a domain object — with inner classes, records, lists of objects, and maps of objects — instead of a flat bag of strings.

## 2. Why & when

Flat properties become unmanageable once you have more than a handful of keys. Consider a hypothetical set of twelve properties for database, connection pool, and TLS: without nesting they are all siblings named `db-host`, `db-port`, `pool-min`, `pool-max`, `tls-cert-path`, etc. With nesting they become `database.host`, `database.port`, `database.pool.min-size`, `database.pool.max-size`, `database.tls.cert-path` — clearly grouped, self-documenting, and impossible to confuse.

Use nested properties when:

- Related sub-settings belong together and have their own internal structure (connection pools, TLS config, OAuth client settings).
- You want a **list of objects** — for example, multiple data-source configurations or a list of webhook endpoints.
- You want a **map of objects** keyed by name — for example, per-tenant settings or named caches.
- You want nested validation — `@Valid` on an inner field activates JSR-303 recursively.

## 3. Core concept

Spring Boot's `ConfigurationPropertiesBinder` builds the target object by treating each dotted segment of a key as a nesting level. Given prefix `myapp` and the key `myapp.database.pool.min-size`, it:

1. Finds or creates the `database` field on the top-level object.
2. Finds or creates the `pool` field on the `database` object.
3. Sets the `minSize` field on the `pool` object to the converted value.

This works for:

- **Simple nested POJO** — a field whose type is another class with its own fields.
- **Java record** — immutable; Spring Boot 2.6+ binds records via constructor binding (no setters needed).
- **`List<T>` where T is a complex type** — elements are addressed by index: `myapp.endpoints[0].url`, `myapp.endpoints[1].url`.
- **`Map<String, T>` where T is a complex type** — elements are addressed by key: `myapp.caches.users.ttl`, `myapp.caches.products.ttl`.

In `.properties` files, list indices are written as `[0]`, `[1]`, … In YAML they are written with `- ` list notation. Map keys are just additional path segments.

## 4. Diagram

<svg viewBox="0 0 700 360" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Property key dotted path mapped to nested Java object graph">
  <rect x="10" y="10" width="680" height="340" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="350" y="38" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Dotted Key Path → Nested Object Graph</text>

  <!-- Left: property keys -->
  <rect x="25" y="55" width="290" height="260" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="170" y="78" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">application.properties</text>
  <text x="42" y="100" fill="#e6edf3" font-size="11" font-family="monospace">myapp.database.host=db.local</text>
  <text x="42" y="118" fill="#e6edf3" font-size="11" font-family="monospace">myapp.database.port=5432</text>
  <text x="42" y="136" fill="#e6edf3" font-size="11" font-family="monospace">myapp.database.pool.min-size=2</text>
  <text x="42" y="154" fill="#e6edf3" font-size="11" font-family="monospace">myapp.database.pool.max-size=20</text>
  <text x="42" y="180" fill="#8b949e" font-size="10" font-family="monospace">— list of objects —</text>
  <text x="42" y="198" fill="#e6edf3" font-size="11" font-family="monospace">myapp.endpoints[0].url=/api</text>
  <text x="42" y="216" fill="#e6edf3" font-size="11" font-family="monospace">myapp.endpoints[1].url=/admin</text>
  <text x="42" y="240" fill="#8b949e" font-size="10" font-family="monospace">— map of objects —</text>
  <text x="42" y="258" fill="#e6edf3" font-size="11" font-family="monospace">myapp.caches.users.ttl=5m</text>
  <text x="42" y="276" fill="#e6edf3" font-size="11" font-family="monospace">myapp.caches.orders.ttl=1m</text>

  <!-- Arrow -->
  <line x1="318" y1="185" x2="368" y2="185" stroke="#6db33f" stroke-width="2.5" marker-end="url(#na1)"/>
  <defs>
    <marker id="na1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <text x="342" y="178" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">bind</text>

  <!-- Right: Java object graph -->
  <rect x="372" y="55" width="295" height="260" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="520" y="78" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">MyAppProperties</text>
  <!-- database box -->
  <rect x="390" y="90" width="258" height="100" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="400" y="107" fill="#79c0ff" font-size="10" font-family="monospace">database: Database</text>
  <text x="412" y="124" fill="#e6edf3" font-size="10" font-family="monospace">host = "db.local"</text>
  <text x="412" y="140" fill="#e6edf3" font-size="10" font-family="monospace">port = 5432</text>
  <!-- pool box inside database -->
  <rect x="412" y="148" width="220" height="34" rx="4" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="422" y="162" fill="#8b949e" font-size="10" font-family="monospace">pool: Pool  { min=2, max=20 }</text>
  <!-- endpoints list -->
  <rect x="390" y="200" width="258" height="46" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="400" y="217" fill="#8b949e" font-size="10" font-family="monospace">endpoints: List&lt;Endpoint&gt;</text>
  <text x="412" y="233" fill="#e6edf3" font-size="10" font-family="monospace">[0].url="/api"  [1].url="/admin"</text>
  <!-- caches map -->
  <rect x="390" y="254" width="258" height="46" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="400" y="271" fill="#8b949e" font-size="10" font-family="monospace">caches: Map&lt;String, Cache&gt;</text>
  <text x="412" y="287" fill="#e6edf3" font-size="10" font-family="monospace">"users".ttl=PT5M  "orders".ttl=PT1M</text>

  <text x="350" y="330" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same graph; YAML uses indentation instead of dots</text>
</svg>

Each dotted segment in the property key corresponds to one level of nesting in the Java object graph. Lists use indexed segments; maps use arbitrary string keys as segments.

## 5. Runnable example

```java
// src/main/java/com/example/demo/MyAppProperties.java
package com.example.demo;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
@ConfigurationProperties(prefix = "myapp")
@Validated
public class MyAppProperties {

    /** Simple nested POJO. */
    @Valid
    private Database database = new Database();

    /** List of nested objects. */
    @Valid
    private List<Endpoint> endpoints = new ArrayList<>();

    /** Map of nested objects, keyed by cache name. */
    private Map<String, Cache> caches = new HashMap<>();

    // --- getters / setters ---
    public Database getDatabase()               { return database; }
    public void setDatabase(Database db)        { this.database = db; }
    public List<Endpoint> getEndpoints()        { return endpoints; }
    public void setEndpoints(List<Endpoint> e)  { this.endpoints = e; }
    public Map<String, Cache> getCaches()       { return caches; }
    public void setCaches(Map<String, Cache> c) { this.caches = c; }

    // ---- nested: database ----
    public static class Database {
        @NotBlank
        private String host;
        @Positive
        private int port = 5432;

        /** Further nesting: pool config lives inside database config. */
        @Valid
        private Pool pool = new Pool();

        public String getHost()                 { return host; }
        public void setHost(String h)           { this.host = h; }
        public int getPort()                    { return port; }
        public void setPort(int p)              { this.port = p; }
        public Pool getPool()                   { return pool; }
        public void setPool(Pool pool)          { this.pool = pool; }
    }

    // ---- nested inside Database: pool ----
    public static class Pool {
        @Positive
        private int minSize = 2;
        @Positive
        private int maxSize = 10;

        public int getMinSize()                 { return minSize; }
        public void setMinSize(int m)           { this.minSize = m; }
        public int getMaxSize()                 { return maxSize; }
        public void setMaxSize(int m)           { this.maxSize = m; }
    }

    // ---- element type for endpoints list ----
    public static class Endpoint {
        @NotBlank
        private String url;
        private boolean secure = true;

        public String getUrl()                  { return url; }
        public void setUrl(String u)            { this.url = u; }
        public boolean isSecure()               { return secure; }
        public void setSecure(boolean s)        { this.secure = s; }
    }

    // ---- value type for caches map ----
    public static class Cache {
        private Duration ttl = Duration.ofMinutes(5);
        private int maxEntries = 1000;

        public Duration getTtl()                { return ttl; }
        public void setTtl(Duration t)          { this.ttl = t; }
        public int getMaxEntries()              { return maxEntries; }
        public void setMaxEntries(int m)        { this.maxEntries = m; }
    }
}

// -----------------------------------------------------------------------
// src/main/java/com/example/demo/DemoApplication.java
package com.example.demo;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class DemoApplication implements CommandLineRunner {

    @Autowired MyAppProperties props;

    public static void main(String[] args) {
        SpringApplication.run(DemoApplication.class, args);
    }

    @Override
    public void run(String... args) {
        MyAppProperties.Database db = props.getDatabase();
        System.out.println("DB host      : " + db.getHost());
        System.out.println("DB port      : " + db.getPort());
        System.out.println("Pool min/max : " + db.getPool().getMinSize() + " / " + db.getPool().getMaxSize());

        props.getEndpoints().forEach(ep ->
            System.out.println("Endpoint     : " + ep.getUrl() + " (secure=" + ep.isSecure() + ")"));

        props.getCaches().forEach((name, cache) ->
            System.out.println("Cache " + name + ": ttl=" + cache.getTtl() + ", max=" + cache.getMaxEntries()));
    }
}
```

`application.properties` (flat dotted notation):

```properties
myapp.database.host=db.local
myapp.database.port=5432
myapp.database.pool.min-size=5
myapp.database.pool.max-size=30

myapp.endpoints[0].url=/api
myapp.endpoints[0].secure=true
myapp.endpoints[1].url=/admin
myapp.endpoints[1].secure=false

myapp.caches.users.ttl=5m
myapp.caches.users.max-entries=500
myapp.caches.orders.ttl=1m
myapp.caches.orders.max-entries=200
```

Equivalent `application.yml` (indented notation):

```yaml
myapp:
  database:
    host: db.local
    port: 5432
    pool:
      min-size: 5
      max-size: 30
  endpoints:
    - url: /api
      secure: true
    - url: /admin
      secure: false
  caches:
    users:
      ttl: 5m
      max-entries: 500
    orders:
      ttl: 1m
      max-entries: 200
```

**How to run:** `./mvnw spring-boot:run`. Both property files produce identical bound objects.

## 6. Walkthrough

- **`MyAppProperties` with prefix `myapp`** — top-level class. It has three fields: `database` (a single nested POJO), `endpoints` (a `List`), and `caches` (a `Map`).
- **`myapp.database.host`** — the binder splits on `.`. `myapp` matches the prefix, `database` selects the `database` field, `host` selects the field on the `Database` inner class. The string `"db.local"` is set directly.
- **`myapp.database.pool.min-size=5`** — three segments beneath the prefix. `database` → `pool` → `minSize` (relaxed: `min-size` → `minSize`). This is three levels of nesting handled transparently.
- **`myapp.endpoints[0].url=/api`** — the `[0]` index tells the binder that `endpoints` is a list and this is its first element. The binder creates an `Endpoint` instance, sets `url`, and adds it to the list. `[1]` adds a second element.
- **`myapp.caches.users.ttl=5m`** — `caches` is a `Map<String, Cache>`. The segment `users` becomes the map key; `ttl` is a field on the `Cache` value type. The string `"5m"` is auto-converted to `Duration.ofMinutes(5)`.
- **`@Valid` on the nested fields** — without `@Valid` on `database`, the `@NotBlank` on `host` and `@Positive` on `port` are not checked at startup. Adding `@Valid` enables recursive validation.
- **YAML vs `.properties`** — both files bind to the identical Java object graph. The binder normalises both notations to the same canonical dotted path before resolving field names.

## 7. Gotchas & takeaways

> **List elements in `.properties` files must use index notation `[0]`, `[1]`, …** Spring Boot does not support the comma-separated list syntax (`myapp.endpoints=/api,/admin`) for lists of complex objects — that only works for `List<String>`. For lists of POJOs you must use indexed keys.

> **Nested POJOs must have a no-argument constructor and public setters** (or use a Java record with constructor binding). If the inner class lacks setters, the binder creates the object but cannot set any of its fields — fields silently stay at their defaults with no error.

- In YAML, map keys that contain dots must be quoted: `"my.cache":` — otherwise YAML interprets the dots as nesting.
- For deep nesting, consider extracting inner classes into top-level classes to make the code easier to navigate and test in isolation.
- Java records work as nested types: `record Pool(int minSize, int maxSize) {}`. Spring Boot 2.6+ binds them via their canonical constructor — no setters needed.
- A `Map<String, String>` can be bound from YAML block mappings or from `.properties` dotted keys, which is useful for dynamic key sets you can't enumerate at compile time.
- `@Valid` on a `List<T>` field triggers validation on every element in the list, not just the list itself.
