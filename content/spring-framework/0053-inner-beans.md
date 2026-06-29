---
card: spring-framework
gi: 53
slug: inner-beans
title: Inner beans
---

## 1. What it is

An **inner bean** is a bean defined *inside* the property or constructor-arg element of another bean — it has no id, it is anonymous, it cannot be referenced by any other bean, and its lifecycle is tied entirely to the enclosing (outer) bean. The concept mirrors Java anonymous/local inner classes: local, unnamed, and inaccessible from outside.

```xml
<!-- XML inner bean — the DataSource is anonymous and belongs only to userRepository -->
<bean id="userRepository" class="com.example.UserRepository">
    <constructor-arg>
        <bean class="org.springframework.jdbc.datasource.DriverManagerDataSource">
            <property name="url"      value="jdbc:h2:mem:test"/>
            <property name="username" value="sa"/>
        </bean>
        <!-- No id on this DataSource — it cannot be referenced elsewhere -->
    </constructor-arg>
</bean>
```

Annotation-driven Spring rarely uses inner beans explicitly — the equivalent is declaring a `@Bean` method that returns a new instance and is only ever called from one place.

In one sentence: **An inner bean is an anonymous, locally-scoped bean definition that lives inside a parent bean's property, is invisible to the rest of the container, and is destroyed when the parent bean is destroyed.**

## 2. Why & when

Inner beans are useful when:

- A collaborator is used by **exactly one bean** and should never be shared or looked up by any other part of the application.
- You want to **prevent accidental reuse** — e.g., a `DataSource` or `ConnectionFactory` that is private to one repository.
- Configuration is simpler without inventing a top-level bean id that you will use once.
- Migrating legacy XML configs: inner beans keep the XML compact for small, private collaborators.

In modern annotation-driven Spring, an inner bean's role is often replaced by a `@Bean` private helper method, or simply by not exposing a bean via `@Component` (making it package-private).

## 3. Core concept

```
Outer bean:
  id="userRepository"  class=UserRepository
    ↓ constructor-arg
    Inner bean (anonymous):
      class=DriverManagerDataSource
      url="jdbc:h2:mem:test"
      username="sa"

Rules:
  • Inner bean has NO id (id is ignored if set).
  • Inner bean is NEVER registered in the container — you cannot getBean() it.
  • Inner bean scope is ALWAYS effectively singleton relative to the parent
    (scope attribute on inner bean is ignored by container).
  • Inner bean is created BEFORE the outer bean's constructor runs.
  • Inner bean is destroyed WHEN the outer bean is destroyed.
  • Inner bean CAN have its own <property> and <constructor-arg> elements.
```

## 4. Diagram

<svg viewBox="0 0 580 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inner bean contained within outer bean — not accessible from the container directly">
  <defs>
    <marker id="a53" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Container boundary -->
  <rect x="5" y="5" width="570" height="195" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="290" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring IoC Container</text>

  <!-- Outer bean -->
  <rect x="20" y="40" width="360" height="145" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="200" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">UserRepository  (id="userRepository")</text>

  <!-- Inner bean (nested) -->
  <rect x="40" y="75" width="320" height="95" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="200" y="94" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Inner Bean  (anonymous — no id)</text>
  <text x="200" y="110" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">class: DriverManagerDataSource</text>
  <text x="200" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">url="jdbc:h2:mem:test"</text>
  <text x="200" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">username="sa"</text>
  <text x="200" y="158" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">lifecycle tied to UserRepository</text>

  <!-- Cross access blocked -->
  <line x1="408" y1="120" x2="478" y2="120" stroke="#ff4444" stroke-width="1.5" stroke-dasharray="4,3"/>
  <text x="490" y="110" fill="#ff4444" font-size="9" font-family="sans-serif">ctx.getBean(</text>
  <text x="490" y="123" fill="#ff4444" font-size="9" font-family="sans-serif">DataSource)</text>
  <text x="490" y="137" fill="#ff4444" font-size="9" font-family="sans-serif">→ FAILS</text>
  <text x="444" y="114" fill="#ff4444" font-size="14" text-anchor="middle" font-family="sans-serif">✗</text>

  <text x="200" y="195" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Inner bean cannot be shared or looked up. It belongs exclusively to its parent.</text>
</svg>

The inner bean is enclosed inside the outer bean definition. No other bean can reference it and it does not appear in `ctx.getBeanDefinitionNames()`.

## 5. Runnable example

Scenario: a `ReportService` that uses a private `CsvFormatter` helper. The formatter is an inner-bean-style dependency — only `ReportService` uses it and it should not be available to any other service.

### Level 1 — Basic

The simplest inner-bean pattern: a helper object constructed privately inside the owner.

```java
// InnerBeanDemo.java — run with: java InnerBeanDemo.java
import java.util.List;

public class InnerBeanDemo {

    // ── "inner bean" helper — not exposed to the outside ──────────────
    static class CsvFormatter {
        private final String delimiter;
        private final boolean includeHeader;

        CsvFormatter(String delimiter, boolean includeHeader) {
            this.delimiter     = delimiter;
            this.includeHeader = includeHeader;
            System.out.println("  [INNER] CsvFormatter created: delim='"
                + delimiter + "' header=" + includeHeader);
        }

        String format(List<String> headers, List<List<String>> rows) {
            StringBuilder sb = new StringBuilder();
            if (includeHeader) sb.append(String.join(delimiter, headers)).append("\n");
            for (List<String> row : rows) sb.append(String.join(delimiter, row)).append("\n");
            return sb.toString().trim();
        }
    }

    // ── outer "bean" — creates inner bean privately ────────────────────
    static class ReportService {
        private final CsvFormatter formatter;  // inner bean: private, not shared

        ReportService() {
            // Spring XML inner bean equivalent: <bean class="CsvFormatter">
            this.formatter = new CsvFormatter(",", true);
            System.out.println("  [OUTER] ReportService created");
        }

        void printReport(List<String> headers, List<List<String>> rows) {
            System.out.println("[REPORT]\n" + formatter.format(headers, rows));
        }
    }

    public static void main(String[] args) {
        ReportService svc = new ReportService();
        svc.printReport(
            List.of("Name", "Score", "Grade"),
            List.of(
                List.of("Alice", "92", "A"),
                List.of("Bob",   "75", "B"),
                List.of("Carol", "88", "A")
            )
        );
    }
}
```

How to run: `java InnerBeanDemo.java`

`CsvFormatter` is created inside `ReportService`'s constructor — it is never exposed to any outer scope. No other class can obtain or share this `CsvFormatter`. This is exactly what Spring's inner bean achieves in XML: the nested `<bean>` is created as part of `ReportService` and is invisible to the rest of the container.

### Level 2 — Intermediate

Multiple properties on the inner bean, and demonstrating that the inner bean's lifecycle ends with the outer bean.

```java
// InnerBeanDemo2.java — run with: java InnerBeanDemo2.java
import java.util.*;

public class InnerBeanDemo2 {

    // ── inner bean: connection config — used only by DataFetcher ──────
    static class ConnectionConfig {
        final String  host;
        final int     port;
        final int     timeoutMs;
        final boolean ssl;

        ConnectionConfig(String host, int port, int timeoutMs, boolean ssl) {
            this.host      = host;
            this.port      = port;
            this.timeoutMs = timeoutMs;
            this.ssl       = ssl;
            System.out.println("  [INNER] ConnectionConfig created: "
                + host + ":" + port + " ssl=" + ssl + " timeout=" + timeoutMs + "ms");
        }

        String url() { return (ssl ? "https" : "http") + "://" + host + ":" + port; }

        void close() { System.out.println("  [INNER] ConnectionConfig closed (" + url() + ")"); }
    }

    // ── outer bean ────────────────────────────────────────────────────
    static class DataFetcher {
        private final ConnectionConfig config;  // private inner "bean"
        private boolean open = true;

        DataFetcher(ConnectionConfig config) {
            this.config = config;
            System.out.println("  [OUTER] DataFetcher created using " + config.url());
        }

        String fetch(String path) {
            if (!open) throw new IllegalStateException("DataFetcher closed");
            System.out.println("  [FETCH] GET " + config.url() + path);
            return "{ \"path\": \"" + path + "\", \"data\": \"...\" }";
        }

        void close() {
            System.out.println("  [OUTER] DataFetcher closing...");
            open = false;
            config.close();  // inner bean destroyed with outer bean
        }
    }

    static DataFetcher buildFetcher() {
        ConnectionConfig cfg = new ConnectionConfig("api.example.com", 443, 5000, true);
        return new DataFetcher(cfg);
    }

    public static void main(String[] args) {
        DataFetcher fetcher = buildFetcher();
        System.out.println("[RESULT] " + fetcher.fetch("/users/1"));
        System.out.println("[RESULT] " + fetcher.fetch("/products/42"));
        fetcher.close();     // outer bean closed → inner bean also closed
        System.out.println();
        try { fetcher.fetch("/after-close"); }
        catch (IllegalStateException e) { System.out.println("[ERROR] " + e.getMessage()); }
    }
}
```

How to run: `java InnerBeanDemo2.java`

`ConnectionConfig` has its own properties (`host`, `port`, `timeoutMs`, `ssl`) — equivalent to `<property>` elements inside an XML inner bean. When `DataFetcher.close()` is called (equivalent to Spring's `destroy-method`), it also calls `config.close()` — demonstrating that the inner bean's teardown is tied to the outer bean's teardown.

### Level 3 — Advanced

Nested inner-bean ownership: a service holds a private pipeline with its own private configuration — three layers deep. Each layer is invisible to all other beans.

```java
// InnerBeanDemo3.java — run with: java InnerBeanDemo3.java
import java.util.*;

public class InnerBeanDemo3 {

    // ── layer 3 (innermost): retry policy ─────────────────────────────
    static class RetryPolicy {
        final int    maxAttempts;
        final long   backoffMs;
        final boolean jitter;

        RetryPolicy(int maxAttempts, long backoffMs, boolean jitter) {
            this.maxAttempts = maxAttempts;
            this.backoffMs   = backoffMs;
            this.jitter      = jitter;
            System.out.println("    [INNER-3] RetryPolicy: attempts=" + maxAttempts
                + " backoff=" + backoffMs + "ms jitter=" + jitter);
        }

        <T> T execute(String label, java.util.function.Supplier<T> action) {
            for (int i = 1; i <= maxAttempts; i++) {
                try {
                    T result = action.get();
                    System.out.println("      [RETRY] " + label + " succeeded on attempt " + i);
                    return result;
                } catch (RuntimeException e) {
                    System.out.println("      [RETRY] " + label + " attempt " + i + " failed: " + e.getMessage());
                    if (i == maxAttempts) throw e;
                }
            }
            throw new RuntimeException("unreachable");
        }
    }

    // ── layer 2 (inner): HTTP pipeline — contains RetryPolicy ─────────
    static class HttpPipeline {
        final String     baseUrl;
        final RetryPolicy retry;   // innermost inner bean
        final Map<String,String> defaultHeaders;

        HttpPipeline(String baseUrl, RetryPolicy retry) {
            this.baseUrl        = baseUrl;
            this.retry          = retry;
            this.defaultHeaders = new LinkedHashMap<>(Map.of(
                "Accept", "application/json",
                "X-Client", "inner-bean-demo"
            ));
            System.out.println("  [INNER-2] HttpPipeline: baseUrl=" + baseUrl);
        }

        String get(String path) {
            return retry.execute("GET " + path, () -> {
                System.out.println("      [HTTP] GET " + baseUrl + path
                    + " headers=" + defaultHeaders);
                if (path.contains("fail")) throw new RuntimeException("503 Service Unavailable");
                return "{ \"path\": \"" + path + "\" }";
            });
        }
    }

    // ── layer 1 (outer): public service — contains HttpPipeline ───────
    static class WeatherService {
        private final HttpPipeline pipeline;   // private inner "bean"
        private final String       apiKey;

        WeatherService(String apiKey, HttpPipeline pipeline) {
            this.apiKey   = apiKey;
            this.pipeline = pipeline;
            pipeline.defaultHeaders.put("X-API-Key", apiKey);
            System.out.println("[OUTER] WeatherService ready");
        }

        String getWeather(String city) {
            System.out.println("[WEATHER] querying city=" + city);
            return pipeline.get("/weather?city=" + city + "&key=" + apiKey);
        }
    }

    // ── container builds the chain: inner-3 → inner-2 → outer ─────────
    static WeatherService buildContainer() {
        RetryPolicy retry    = new RetryPolicy(3, 200, true);
        HttpPipeline pipeline = new HttpPipeline("https://api.weather.io", retry);
        return new WeatherService("sk-abc123", pipeline);
    }

    public static void main(String[] args) {
        WeatherService svc = buildContainer();
        System.out.println();
        System.out.println("[RESULT] " + svc.getWeather("London"));
        System.out.println();
        System.out.println("[RESULT] " + svc.getWeather("fail-city"));
    }
}
```

How to run: `java InnerBeanDemo3.java`

Three levels of nesting: `RetryPolicy` (innermost) is private to `HttpPipeline`, which is private to `WeatherService`. Neither `RetryPolicy` nor `HttpPipeline` is accessible from outside `WeatherService`. When `getWeather("fail-city")` is called, the retry logic runs three attempts before propagating the exception — all orchestrated through private inner-bean collaborators.

## 6. Walkthrough

**`buildContainer()` — creation order (innermost first):**

```
1. new RetryPolicy(3, 200, true)
     → [INNER-3] RetryPolicy: attempts=3 backoff=200ms jitter=true

2. new HttpPipeline("https://api.weather.io", retry)
     → [INNER-2] HttpPipeline: baseUrl=https://api.weather.io
     → defaultHeaders = {Accept:application/json, X-Client:inner-bean-demo}

3. new WeatherService("sk-abc123", pipeline)
     → defaultHeaders gets X-API-Key added
     → [OUTER] WeatherService ready
```

**`getWeather("fail-city")` — execution order:**

```
WeatherService.getWeather("fail-city")
  → pipeline.get("/weather?city=fail-city&key=sk-abc123")
    → retry.execute("GET /weather?city=fail-city...", action):
        attempt 1: action.get() → "fail" in path → RuntimeException("503...")
          [RETRY] attempt 1 failed: 503 Service Unavailable
        attempt 2: action.get() → RuntimeException("503...")
          [RETRY] attempt 2 failed: 503 Service Unavailable
        attempt 3: action.get() → RuntimeException("503...")
          [RETRY] attempt 3 failed: 503 Service Unavailable
          i == maxAttempts → throw RuntimeException("503...")
  → Exception propagates to main → printed as [RESULT] RuntimeException
```

State at each layer:
- `RetryPolicy` tracks attempt count in local variable `i`.
- `HttpPipeline` passes the `baseUrl` + `defaultHeaders` to each attempt.
- `WeatherService` adds the API key once at construction — shared across all calls.

## 7. Gotchas & takeaways

> **Inner beans in XML are always treated as singletons relative to their parent, regardless of any `scope` attribute you set.** Spring silently ignores the `scope` of an inner bean because it is created once for the enclosing bean and cannot be shared.

> **You cannot inject an inner bean anywhere else.** If you find yourself wanting to share an inner bean, it needs to become a top-level named bean instead.

- Inner beans cannot be retrieved via `ApplicationContext.getBean()` — they are not registered in the container's bean registry.
- The inner bean is created **before** the outer bean's constructor or setter is invoked — its construction failure will prevent the outer bean from being created.
- Modern Spring annotation-driven applications rarely declare explicit inner beans; the role is usually filled by package-private `@Bean` methods or by not annotating a class with `@Component`.
- If an inner bean implements `DisposableBean` or declares a `destroy-method`, Spring calls it when the outer bean is destroyed at context close.
