---
card: spring-framework
gi: 51
slug: straight-values-primitives-strings
title: Straight values — primitives & strings
---

## 1. What it is

**Straight values** (also called "simple value injection") refers to injecting primitive types, their wrappers, and `String` values into beans — as opposed to injecting bean references. In XML this uses the `value` attribute; in annotation-driven code it uses `@Value`.

```java
// @Value: inject a scalar from properties or literal
@Component
public class ConnectionPool {

    @Value("${db.url}")
    private String url;

    @Value("${db.maxConnections:10}")     // default 10 if property missing
    private int maxConnections;

    @Value("${db.readOnly:false}")
    private boolean readOnly;

    @Value("jdbc:h2:mem:test")            // literal string
    private String fallbackUrl;
}

// XML equivalent
// <bean class="ConnectionPool">
//   <property name="url" value="${db.url}"/>
//   <property name="maxConnections" value="10"/>
// </bean>
```

Spring's `ConversionService` converts the string value (all property values are strings) to the target Java type (`int`, `boolean`, `long`, `Duration`, `List<String>`, etc.).

In one sentence: **Straight value injection wires primitive and string configuration data into beans using `@Value("${property.key}")`, with automatic type coercion from string to any Java type supported by Spring's `ConversionService`.**

## 2. Why & when

Straight value injection is used whenever a bean needs:

- **Configuration parameters** — database URL, port number, feature flags, timeouts.
- **Environment-specific values** — different SMTP host in dev vs prod.
- **Default values** — `@Value("${cache.ttl:300}")` uses 300 if the property is not set.
- **SpEL expressions** — `@Value("#{systemProperties['os.name']}")` evaluates a Spring Expression Language expression at injection time.

Use `@Value` for individual values. For related groups of values, `@ConfigurationProperties` (Spring Boot) is cleaner — it binds a whole prefix to a typed POJO.

## 3. Core concept

```
Property resolution chain (Spring):

  @Value("${db.url}")
    → PropertySourcesPropertyResolver
    → searches: System properties → JVM args → application.properties → ...
    → finds "db.url" = "jdbc:postgresql://db:5432/app"
    → returns String "jdbc:postgresql://db:5432/app"
    → ConversionService: String → String (no conversion needed)
    → injects into field

  @Value("${db.maxConnections:10}")
    → property "db.maxConnections" not found
    → uses default "10"
    → ConversionService: "10" → int 10
    → injects into int field

  Type coercion examples:
    "10"    → int, long, Integer, Long
    "true"  → boolean, Boolean
    "PT5M"  → java.time.Duration (ISO-8601)
    "1,2,3" → List<Integer> (with comma separator)
    "ADMIN" → MyEnum.ADMIN
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@Value resolution: property sources searched, string found, ConversionService converts to target type, field injected">
  <defs>
    <marker id="a51" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Property sources -->
  <rect x="10" y="20" width="160" height="145" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="40" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Property Sources</text>
  <rect x="20" y="50" width="140" height="24" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">System properties</text>
  <rect x="20" y="82" width="140" height="24" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JVM -D args</text>
  <rect x="20" y="114" width="140" height="24" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="130" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">application.properties ✓</text>
  <rect x="20" y="146" width="140" height="14" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="90" y="157" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">environment variables</text>

  <!-- Arrow to ConversionService -->
  <line x1="170" y1="100" x2="260" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a51)"/>
  <text x="215" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">"10"</text>

  <!-- ConversionService -->
  <rect x="262" y="65" width="170" height="70" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="347" y="86" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ConversionService</text>
  <text x="347" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">String "10" → int 10</text>
  <text x="347" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">"true" → boolean true</text>

  <!-- Arrow to bean field -->
  <line x1="432" y1="100" x2="520" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a51)"/>
  <text x="476" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">int 10</text>

  <!-- Bean field -->
  <rect x="520" y="50" width="150" height="100" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="595" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ConnectionPool</text>
  <text x="595" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">String url = "jdbc:..."</text>
  <text x="595" y="108" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">int maxConn = 10 ✓</text>
  <text x="595" y="124" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">boolean readOnly = false</text>

  <text x="340" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">All property values are strings. ConversionService converts to the declared field type.</text>
</svg>

Properties are strings. `ConversionService` converts each value to the target Java type before injection. The field receives the typed value.

## 5. Runnable example

Scenario: a `DatabaseConfig` bean that reads connection settings from properties, including primitives, strings, defaults, and type-coerced values.

### Level 1 — Basic

Inject string and primitive properties with defaults.

```java
// StraightValuesDemo.java — run with: java StraightValuesDemo.java
import java.util.*;

public class StraightValuesDemo {

    // Simulated @Value injection: reads from a property map
    static class PropertySource {
        private final Map<String, String> props;
        PropertySource(Map<String, String> props) { this.props = props; }

        String get(String key, String defaultValue) {
            return props.getOrDefault(key, defaultValue);
        }

        int    getInt   (String key, int    def) { return Integer.parseInt(get(key, String.valueOf(def))); }
        long   getLong  (String key, long   def) { return Long.parseLong(get(key, String.valueOf(def))); }
        boolean getBool (String key, boolean def) { return Boolean.parseBoolean(get(key, String.valueOf(def))); }
    }

    static class DatabaseConfig {
        final String  url;
        final String  username;
        final int     maxConnections;
        final long    connectionTimeoutMs;
        final boolean readOnly;
        final String  schema;

        // @Value-style injection via constructor (mirrors Spring constructor @Value)
        DatabaseConfig(PropertySource props) {
            this.url                = props.get    ("db.url",                "jdbc:h2:mem:test");
            this.username           = props.get    ("db.username",           "sa");
            this.maxConnections     = props.getInt ("db.maxConnections",     10);
            this.connectionTimeoutMs= props.getLong("db.connectionTimeout",  5000L);
            this.readOnly           = props.getBool("db.readOnly",           false);
            this.schema             = props.get    ("db.schema",             "public");
            System.out.println("  [BEAN] DatabaseConfig created:");
            System.out.println("    url=" + url + " maxConns=" + maxConnections
                + " timeout=" + connectionTimeoutMs + "ms readOnly=" + readOnly);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Scenario 1: application.properties present ===");
        PropertySource props1 = new PropertySource(Map.of(
            "db.url",              "jdbc:postgresql://prod-db:5432/app",
            "db.username",         "app_user",
            "db.maxConnections",   "20",
            "db.connectionTimeout","3000",
            "db.readOnly",         "false"
            // db.schema not set → uses default "public"
        ));
        DatabaseConfig cfg1 = new DatabaseConfig(props1);
        System.out.println("    schema=" + cfg1.schema + " (default)");

        System.out.println("\n=== Scenario 2: minimal config (all defaults) ===");
        PropertySource props2 = new PropertySource(Map.of());
        DatabaseConfig cfg2 = new DatabaseConfig(props2);
        System.out.println("    url=" + cfg2.url + " (default h2)");
    }
}
```

How to run: `java StraightValuesDemo.java`

All property values are strings in the source. `getInt()` and `getLong()` parse the string to the target type — equivalent to Spring's `ConversionService`. `db.schema` is absent in scenario 1 — the default `"public"` is used. Scenario 2 uses all defaults.

### Level 2 — Intermediate

Type coercion for more types: `List<String>`, `Duration`-style, and enums.

```java
// StraightValuesDemo2.java — run with: java StraightValuesDemo2.java
import java.util.*;
import java.util.stream.Collectors;

public class StraightValuesDemo2 {

    enum CacheStrategy { NONE, LOCAL, DISTRIBUTED }

    static class PropertySource {
        private final Map<String, String> props;
        PropertySource(Map<String, String> props) { this.props = props; }

        String  get    (String k, String  d) { return props.getOrDefault(k, d); }
        int     getInt (String k, int    d)  { return Integer.parseInt(get(k, String.valueOf(d))); }
        boolean getBool(String k, boolean d) { return Boolean.parseBoolean(get(k, String.valueOf(d))); }

        // Comma-separated list → List<String>
        List<String> getList(String k, String d) {
            String raw = get(k, d);
            return Arrays.stream(raw.split(",")).map(String::trim)
                .filter(s -> !s.isEmpty()).collect(Collectors.toList());
        }

        // "PT5M" or "300s" style → seconds
        long getDurationSeconds(String k, long d) {
            String raw = props.get(k);
            if (raw == null) return d;
            raw = raw.trim();
            if (raw.endsWith("s"))  return Long.parseLong(raw.substring(0, raw.length()-1));
            if (raw.endsWith("m"))  return Long.parseLong(raw.substring(0, raw.length()-1)) * 60;
            if (raw.endsWith("h"))  return Long.parseLong(raw.substring(0, raw.length()-1)) * 3600;
            return Long.parseLong(raw);
        }

        // String → enum
        <E extends Enum<E>> E getEnum(String k, Class<E> type, E d) {
            String raw = props.get(k);
            return raw == null ? d : Enum.valueOf(type, raw.toUpperCase());
        }
    }

    static class CacheConfig {
        final List<String>  nodes;
        final long          ttlSeconds;
        final int           maxEntries;
        final boolean       compression;
        final CacheStrategy strategy;

        CacheConfig(PropertySource props) {
            this.nodes       = props.getList("cache.nodes",       "localhost:6379");
            this.ttlSeconds  = props.getDurationSeconds("cache.ttl",  300L);
            this.maxEntries  = props.getInt ("cache.maxEntries",   10_000);
            this.compression = props.getBool("cache.compression",  false);
            this.strategy    = props.getEnum("cache.strategy",     CacheStrategy.class, CacheStrategy.LOCAL);

            System.out.println("  [BEAN] CacheConfig:");
            System.out.println("    nodes="       + nodes);
            System.out.println("    ttl="         + ttlSeconds + "s");
            System.out.println("    maxEntries="  + maxEntries);
            System.out.println("    compression=" + compression);
            System.out.println("    strategy="    + strategy);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Production config ===");
        PropertySource prod = new PropertySource(Map.of(
            "cache.nodes",       "redis-1:6379, redis-2:6379, redis-3:6379",
            "cache.ttl",         "10m",    // 10 minutes
            "cache.maxEntries",  "50000",
            "cache.compression", "true",
            "cache.strategy",    "distributed"
        ));
        new CacheConfig(prod);

        System.out.println("\n=== Dev config (minimal) ===");
        PropertySource dev = new PropertySource(Map.of(
            "cache.ttl", "30s"
            // all others use defaults
        ));
        new CacheConfig(dev);
    }
}
```

How to run: `java StraightValuesDemo2.java`

`getList("cache.nodes", ...)` parses `"redis-1:6379, redis-2:6379, redis-3:6379"` into a `List<String>`. `getDurationSeconds("cache.ttl", ...)` parses `"10m"` to `600` and `"30s"` to `30`. `getEnum("cache.strategy", ...)` converts `"distributed"` to `CacheStrategy.DISTRIBUTED`. All from plain property strings.

### Level 3 — Advanced

SpEL-style expression injection, nested property objects, and validation at injection time.

```java
// StraightValuesDemo3.java — run with: java StraightValuesDemo3.java
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class StraightValuesDemo3 {

    static class PropertySource {
        private final Map<String, String> store;

        PropertySource(Map<String, String> store) { this.store = store; }

        // ${key:default} resolution
        String resolve(String expr) {
            Matcher m = Pattern.compile("\\$\\{([^}:]+)(?::([^}]*))?}").matcher(expr);
            if (!m.matches()) return expr;  // literal value
            String key = m.group(1), def = m.group(2);
            String val = store.get(key);
            if (val == null) {
                if (def != null) return def;
                throw new RuntimeException("Missing required property: " + key);
            }
            return val;
        }

        // #{expr} — simple SpEL-style evaluator (subset)
        String eval(String expr) {
            if (expr.startsWith("#{") && expr.endsWith("}")) {
                String body = expr.substring(2, expr.length()-1).trim();
                // Support: ${key} * N, ${key} + N, ${key} / N
                Matcher m = Pattern.compile("\\$\\{([^}]+)}\\s*([*+/\\-])\\s*(\\d+)").matcher(body);
                if (m.find()) {
                    int base = Integer.parseInt(resolve("${" + m.group(1) + "}"));
                    int op2  = Integer.parseInt(m.group(3));
                    return String.valueOf(switch (m.group(2)) {
                        case "*" -> base * op2;
                        case "+" -> base + op2;
                        case "-" -> base - op2;
                        case "/" -> base / op2;
                        default  -> base;
                    });
                }
                return body;
            }
            return resolve(expr);
        }

        int    evalInt   (String e, int    d) { try { return Integer.parseInt(eval(e)); } catch(Exception ex) { return d; } }
        String evalString(String e)           { return eval(e); }
        List<String> evalList(String e) {
            return Arrays.stream(eval(e).split(",")).map(String::trim).filter(s -> !s.isEmpty()).toList();
        }
    }

    // Validated config bean
    static class SmtpConfig {
        final String       host;
        final int          port;
        final String       username;
        final String       password;
        final boolean      tls;
        final int          connectTimeoutMs;
        final List<String> allowedDomains;

        SmtpConfig(PropertySource props) {
            this.host             = props.evalString("${smtp.host}");
            this.port             = props.evalInt   ("${smtp.port:587}", 587);
            this.username         = props.evalString("${smtp.username}");
            this.password         = props.evalString("${smtp.password}");
            this.tls              = Boolean.parseBoolean(props.evalString("${smtp.tls:true}"));
            // SpEL: connectTimeout = port * 10 (contrived demo of expression)
            this.connectTimeoutMs = props.evalInt("#{${smtp.port:587} * 10}", 5870);
            this.allowedDomains   = props.evalList("${smtp.allowedDomains:example.com}");

            validate();
            System.out.println("  [BEAN] SmtpConfig validated:");
            System.out.printf("    host=%s port=%d tls=%s timeout=%dms%n",
                host, port, tls, connectTimeoutMs);
            System.out.println("    allowedDomains=" + allowedDomains);
        }

        private void validate() {
            if (host == null || host.isBlank())
                throw new IllegalArgumentException("smtp.host is required");
            if (port < 1 || port > 65535)
                throw new IllegalArgumentException("smtp.port must be 1-65535, got: " + port);
            if (username == null || username.isBlank())
                throw new IllegalArgumentException("smtp.username is required");
            System.out.println("  [VALIDATE] SmtpConfig passed validation");
        }

        boolean canSendTo(String domain) {
            return allowedDomains.contains("*") || allowedDomains.contains(domain);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Production SMTP config ===");
        PropertySource prod = new PropertySource(Map.of(
            "smtp.host",           "smtp.sendgrid.net",
            "smtp.port",           "465",
            "smtp.username",       "apikey",
            "smtp.password",       "SG.xxxx",
            "smtp.tls",            "true",
            "smtp.allowedDomains", "example.com, partner.io, internal.net"
        ));
        SmtpConfig cfg = new SmtpConfig(prod);
        System.out.println("    can send to example.com: " + cfg.canSendTo("example.com"));
        System.out.println("    can send to gmail.com:   " + cfg.canSendTo("gmail.com"));

        System.out.println("\n=== Validation failure (missing required property) ===");
        PropertySource badProps = new PropertySource(Map.of(
            "smtp.host", "smtp.example.com"
            // username missing → validation fails
        ));
        try { new SmtpConfig(badProps); }
        catch (IllegalArgumentException e) {
            System.out.println("  Caught: " + e.getMessage());
        }
    }
}
```

How to run: `java StraightValuesDemo3.java`

`${smtp.port:587}` uses `465` from properties. `#{${smtp.port:587} * 10}` is a SpEL-style expression that reads `port` (465) and multiplies by 10 to get `4650ms` as the connect timeout. `${smtp.allowedDomains:example.com}` parses the comma-separated string into `List<String>`. The `validate()` method runs inside the constructor — equivalent to `@PostConstruct` validation in real Spring.

## 6. Walkthrough

**Level 3 — resolution of each field:**

```
SmtpConfig(props):
  host:
    evalString("${smtp.host}")
    → resolve("${smtp.host}") → store["smtp.host"] = "smtp.sendgrid.net"
    → "smtp.sendgrid.net"

  port:
    evalInt("${smtp.port:587}", 587)
    → resolve("${smtp.port:587}") → store["smtp.port"] = "465"
    → Integer.parseInt("465") = 465

  connectTimeoutMs:
    evalInt("#{${smtp.port:587} * 10}", 5870)
    → eval("#{${smtp.port:587} * 10}")
        → body = "${smtp.port:587} * 10"
        → regex match: key="smtp.port", op="*", op2=10
        → resolve("${smtp.port:587}") = "465"
        → 465 * 10 = 4650
    → 4650

  allowedDomains:
    evalList("${smtp.allowedDomains:example.com}")
    → "example.com, partner.io, internal.net"
    → split(",") → trim → ["example.com","partner.io","internal.net"]

validate():
  host = "smtp.sendgrid.net" → not blank ✓
  port = 465 → 1..65535 ✓
  username = "apikey" → not blank ✓
  → passed
```

## 7. Gotchas & takeaways

> **`@Value("${key}")` throws `IllegalArgumentException` at startup if the property is missing and no default is provided.** Always specify a default with `@Value("${key:defaultValue}")` for optional properties, or use `@ConfigurationProperties` with `required=false` for groups of optional settings.

> **SpEL expressions in `@Value("#{...}")` are evaluated at injection time, not at config parse time.** If the expression references a bean (`@Value("#{someBean.method()}")`), that bean must already be instantiated — avoid depending on beans that are themselves lazily initialized.

- `@Value` can inject into constructor parameters, setter parameters, and fields. Constructor parameter injection (`@Value("${key}") String host` in constructor signature) is the most testable form.
- String-to-type coercion is handled by `ConversionService`. Register a custom `Converter<String, MyType>` bean to support custom types.
- `Environment.getProperty("key", Integer.class)` is the programmatic equivalent of `@Value` — useful when the key name is computed at runtime.
- In Spring Boot, `@ConfigurationProperties` is preferred over many `@Value` annotations: it binds a whole prefix (`db.*`) to a typed record/class, supports validation annotations (`@NotNull`, `@Min`), and generates IDE auto-completion metadata.
- `@Value` does not work on `static` fields — Spring injects instance fields only. Use a `@PostConstruct` method or a `@Bean` factory method for static configuration.
