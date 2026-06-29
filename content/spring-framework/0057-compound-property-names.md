---
card: spring-framework
gi: 57
slug: compound-property-names
title: Compound property names
---

## 1. What it is

**Compound property names** (also called nested property paths) let you navigate through a chain of bean properties using dot notation in a single `<property name="...">` expression. Instead of injecting a whole intermediate object, you drill directly into one of its fields.

```xml
<!-- fred.sammy.bob.sammy is a compound path across three levels -->
<bean id="something" class="com.example.Something">
    <property name="fred.bob.sammy" value="123"/>
    <!--
        Equivalent Java:
          something.getFred().getBob().setSammy(123);
        fred and fred.bob must already be non-null at injection time.
    -->
</bean>
```

In annotation-driven code, Spring's `DataBinder` and `BeanWrapper` use the same dot-path notation when binding request parameters, configuration properties, and `@ConfigurationProperties` — for example, `server.port`, `spring.datasource.url`.

In one sentence: **Compound property names use dot-separated paths to navigate through nested beans and set a property on an intermediate object, provided every object in the path except the last is already non-null.**

## 2. Why & when

Compound property paths are used in:

- **XML configuration** — setting a deeply nested field on a collaborating object you don't own.
- **`@ConfigurationProperties`** — `spring.datasource.hikari.maximum-pool-size` maps to `datasource.hikari.maximumPoolSize` via nested POJOs.
- **Spring MVC data binding** — form field `address.city` binds to `customer.getAddress().setCity(...)`.
- **`BeanWrapper`** — the low-level API that powers all Spring property binding uses the same dot notation.

A compound path is useful when a sub-object is already set (via a separate bean or initialiser) and you only need to tweak a leaf property, rather than re-injecting the entire intermediate object.

## 3. Core concept

```
Path: "a.b.c.d" → injection chain
  1. target.getA()           ← navigate: must return non-null
  2. step1.getB()            ← navigate: must return non-null
  3. step2.getC()            ← navigate: must return non-null
  4. step3.setD(value)       ← set leaf property

If any intermediate step returns null:
  → NullValueInNestedPathException at container startup

Contrast with direct property:
  "a.b.c.d" (compound) navigates through a,b,c to set d
  "fullObject" (simple)  replaces the whole object in one step

BeanWrapper API (powers all compound path resolution):
  BeanWrapper bw = new BeanWrapperImpl(target);
  bw.setPropertyValue("address.city", "London");
  // → target.getAddress().setCity("London")
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Compound property path: Spring navigates from Something → Fred → Bob → sets sammy=123">
  <defs>
    <marker id="a57" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="185" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="340" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Compound path "fred.bob.sammy" resolved step by step</text>

  <!-- Something bean -->
  <rect x="15" y="35" width="140" height="100" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="85" y="54" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Something</text>
  <rect x="25" y="63" width="120" height="28" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="85" y="74" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Fred fred</text>
  <text x="85" y="86" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(pre-set, non-null)</text>
  <text x="85" y="124" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">① getFredd()</text>

  <!-- Fred bean -->
  <rect x="200" y="35" width="140" height="100" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="270" y="54" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Fred</text>
  <rect x="210" y="63" width="120" height="28" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="270" y="74" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Bob bob</text>
  <text x="270" y="86" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(pre-set, non-null)</text>
  <text x="270" y="124" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">② getBob()</text>

  <!-- Bob bean -->
  <rect x="385" y="35" width="140" height="100" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="455" y="54" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Bob</text>
  <rect x="395" y="63" width="120" height="28" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="455" y="74" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">int sammy</text>
  <text x="455" y="86" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">← SET HERE</text>
  <text x="455" y="124" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">③ setSammy(123)</text>

  <!-- Value -->
  <rect x="570" y="60" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="615" y="79" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">123</text>

  <!-- Arrows -->
  <line x1="155" y1="80" x2="198" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a57)"/>
  <line x1="340" y1="80" x2="383" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a57)"/>
  <line x1="568" y1="75" x2="516" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a57)"/>

  <text x="340" y="170" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">If fred or fred.bob returns null → NullValueInNestedPathException at startup.</text>
</svg>

Spring calls `getFred()` then `getBob()` then `setSammy(123)`. The path traversal happens left-to-right; the last segment is the write target.

## 5. Runnable example

Scenario: a `ServerConfig` bean that has nested `TlsConfig` and `TlsConfig` has a nested `KeyStoreConfig`. We use compound paths to set leaf properties on the nested objects.

### Level 1 — Basic

Set a leaf property on a nested object using a compound path.

```java
// CompoundPathDemo.java — run with: java CompoundPathDemo.java

public class CompoundPathDemo {

    static class KeyStoreConfig {
        String  path;
        String  password;
        String  type = "JKS";

        void setPath(String p)     { this.path = p; }
        void setPassword(String p) { this.password = p; }
        void setType(String t)     { this.type = t; }

        @Override public String toString() {
            return "KeyStore{path=" + path + " type=" + type + "}";
        }
    }

    static class TlsConfig {
        boolean        enabled    = false;
        int            port       = 443;
        KeyStoreConfig keyStore   = new KeyStoreConfig();  // pre-set (non-null!)

        void setEnabled(boolean e) { this.enabled = e; }
        void setPort(int p)        { this.port = p; }
        KeyStoreConfig getKeyStore() { return keyStore; }

        @Override public String toString() {
            return "TLS{enabled=" + enabled + " port=" + port + " keyStore=" + keyStore + "}";
        }
    }

    static class ServerConfig {
        String    host    = "localhost";
        int       httpPort = 8080;
        TlsConfig tls      = new TlsConfig();   // pre-set (non-null!)

        void setHost(String h)       { this.host = h; }
        void setHttpPort(int p)      { this.httpPort = p; }
        TlsConfig getTls()           { return tls; }

        @Override public String toString() {
            return "Server{host=" + host + " httpPort=" + httpPort + " tls=" + tls + "}";
        }
    }

    // ── simulate Spring BeanWrapper compound-path injection ───────────
    static ServerConfig buildBean() {
        ServerConfig cfg = new ServerConfig();

        // Simple property
        cfg.setHost("api.example.com");       // name="host"
        cfg.setHttpPort(80);                   // name="httpPort"

        // Compound path: name="tls.enabled"
        cfg.getTls().setEnabled(true);

        // Compound path: name="tls.port"
        cfg.getTls().setPort(443);

        // Deeper compound path: name="tls.keyStore.path"
        cfg.getTls().getKeyStore().setPath("/etc/ssl/server.jks");

        // Compound path: name="tls.keyStore.password"
        cfg.getTls().getKeyStore().setPassword("ch@ngem3");

        // Compound path: name="tls.keyStore.type"
        cfg.getTls().getKeyStore().setType("PKCS12");

        System.out.println("[BEAN] ServerConfig created via compound-path injection:");
        System.out.println("  " + cfg);
        return cfg;
    }

    public static void main(String[] args) {
        ServerConfig cfg = buildBean();
        System.out.println("\n[SUMMARY]");
        System.out.println("  host:     " + cfg.host);
        System.out.println("  httpPort: " + cfg.httpPort);
        System.out.println("  tls:      " + cfg.getTls());
    }
}
```

How to run: `java CompoundPathDemo.java`

`cfg.getTls().getKeyStore().setPath(...)` is exactly what Spring does when it sees `<property name="tls.keyStore.path" value="/etc/ssl/server.jks"/>`. Three levels of navigation: `ServerConfig` → `getTls()` → `getKeyStore()` → `setPath(...)`. All intermediate objects must be pre-initialised (non-null) before Spring traverses the path.

### Level 2 — Intermediate

Use Spring's `BeanWrapper` directly to see compound-path resolution, including type conversion and nested collection access.

```java
// CompoundPathDemo2.java — run with: java CompoundPathDemo2.java
import java.util.*;

public class CompoundPathDemo2 {

    // ── model ──────────────────────────────────────────────────────────
    static class PoolConfig {
        int    maxSize    = 10;
        int    minIdle    = 2;
        long   idleTimeoutMs = 30_000;
        boolean testOnBorrow = false;

        public int  getMaxSize()          { return maxSize; }
        public void setMaxSize(int v)     { maxSize = v; }
        public int  getMinIdle()          { return minIdle; }
        public void setMinIdle(int v)     { minIdle = v; }
        public long getIdleTimeoutMs()    { return idleTimeoutMs; }
        public void setIdleTimeoutMs(long v) { idleTimeoutMs = v; }
        public boolean isTestOnBorrow()   { return testOnBorrow; }
        public void setTestOnBorrow(boolean v) { testOnBorrow = v; }
        @Override public String toString() {
            return "Pool{maxSize=" + maxSize + " minIdle=" + minIdle
                + " idleMs=" + idleTimeoutMs + " testOnBorrow=" + testOnBorrow + "}";
        }
    }

    static class DataSourceConfig {
        String     url      = "jdbc:h2:mem:test";
        String     username = "sa";
        String     password = "";
        PoolConfig pool     = new PoolConfig();   // pre-set

        public String     getUrl()        { return url; }
        public void       setUrl(String v){ url = v; }
        public String     getUsername()   { return username; }
        public void       setUsername(String v) { username = v; }
        public String     getPassword()   { return password; }
        public void       setPassword(String v) { password = v; }
        public PoolConfig getPool()       { return pool; }
        @Override public String toString() {
            return "DS{url=" + url + " user=" + username + " " + pool + "}";
        }
    }

    // ── BeanWrapper simulation: compound path → getter/setter chain ────
    static class SimpleBeanWrapper {
        private final Object root;
        SimpleBeanWrapper(Object root) { this.root = root; }

        void setProperty(String path, Object value) throws Exception {
            String[] parts = path.split("\\.");
            Object current = root;
            // Navigate to the parent of the leaf
            for (int i = 0; i < parts.length - 1; i++) {
                String getter = "get" + Character.toUpperCase(parts[i].charAt(0)) + parts[i].substring(1);
                current = current.getClass().getMethod(getter).invoke(current);
                if (current == null) throw new RuntimeException(
                    "NullValueInNestedPathException at segment '" + parts[i] + "' in path '" + path + "'");
                System.out.println("  navigate: " + getter + "() → " + current.getClass().getSimpleName());
            }
            // Set the leaf
            String leaf   = parts[parts.length - 1];
            String setter = "set" + Character.toUpperCase(leaf.charAt(0)) + leaf.substring(1);
            // Find matching setter
            for (var m : current.getClass().getMethods()) {
                if (m.getName().equals(setter) && m.getParameterCount() == 1) {
                    // primitive type coercion
                    Object coerced = coerce(value, m.getParameterTypes()[0]);
                    m.invoke(current, coerced);
                    System.out.println("  set:      " + setter + "(" + coerced + ")");
                    return;
                }
            }
            throw new RuntimeException("No setter for: " + setter);
        }

        private Object coerce(Object val, Class<?> type) {
            if (val instanceof String s) {
                if (type == int.class  || type == Integer.class) return Integer.parseInt(s);
                if (type == long.class || type == Long.class)    return Long.parseLong(s);
                if (type == boolean.class || type == Boolean.class) return Boolean.parseBoolean(s);
            }
            return val;
        }
    }

    public static void main(String[] args) throws Exception {
        DataSourceConfig ds = new DataSourceConfig();
        SimpleBeanWrapper bw = new SimpleBeanWrapper(ds);

        System.out.println("[BEFORE] " + ds);
        System.out.println();

        System.out.println("[INJECT] path=url value=jdbc:postgresql://prod:5432/app");
        bw.setProperty("url", "jdbc:postgresql://prod:5432/app");
        System.out.println();

        System.out.println("[INJECT] path=pool.maxSize value=50");
        bw.setProperty("pool.maxSize", "50");
        System.out.println();

        System.out.println("[INJECT] path=pool.idleTimeoutMs value=60000");
        bw.setProperty("pool.idleTimeoutMs", "60000");
        System.out.println();

        System.out.println("[INJECT] path=pool.testOnBorrow value=true");
        bw.setProperty("pool.testOnBorrow", "true");
        System.out.println();

        System.out.println("[AFTER] " + ds);
    }
}
```

How to run: `java CompoundPathDemo2.java`

`SimpleBeanWrapper` replicates Spring's `BeanWrapperImpl` logic: split path on `.`, navigate with getters, then call the setter on the leaf. The output shows the exact navigation sequence: for `pool.maxSize`, it calls `getPool()` first, then `setMaxSize(50)`. Type coercion from `String "50"` to `int 50` mirrors Spring's `ConversionService`.

### Level 3 — Advanced

Deeply nested compound paths in a `@ConfigurationProperties`-style setup, including error handling when an intermediate path is null.

```java
// CompoundPathDemo3.java — run with: java CompoundPathDemo3.java
import java.util.*;

public class CompoundPathDemo3 {

    // ── deeply nested config hierarchy ────────────────────────────────
    static class RetryConfig {
        int    maxAttempts   = 3;
        long   backoffMs     = 500;
        double backoffMultiplier = 2.0;

        public int    getMaxAttempts()          { return maxAttempts; }
        public void   setMaxAttempts(int v)     { maxAttempts = v; }
        public long   getBackoffMs()            { return backoffMs; }
        public void   setBackoffMs(long v)      { backoffMs = v; }
        public double getBackoffMultiplier()    { return backoffMultiplier; }
        public void   setBackoffMultiplier(double v) { backoffMultiplier = v; }
        @Override public String toString() {
            return "Retry{maxAttempts=" + maxAttempts
                + " backoffMs=" + backoffMs + " mult=" + backoffMultiplier + "}";
        }
    }

    static class HttpClientConfig {
        int         connectTimeoutMs  = 3000;
        int         readTimeoutMs     = 10000;
        RetryConfig retry             = new RetryConfig();  // pre-set

        public int         getConnectTimeoutMs()       { return connectTimeoutMs; }
        public void        setConnectTimeoutMs(int v)  { connectTimeoutMs = v; }
        public int         getReadTimeoutMs()          { return readTimeoutMs; }
        public void        setReadTimeoutMs(int v)     { readTimeoutMs = v; }
        public RetryConfig getRetry()                  { return retry; }
        @Override public String toString() {
            return "Http{connect=" + connectTimeoutMs + "ms read=" + readTimeoutMs + "ms " + retry + "}";
        }
    }

    static class WeatherApiConfig {
        String           baseUrl     = "https://api.weather.io";
        String           apiKey      = "";
        HttpClientConfig http        = new HttpClientConfig();  // pre-set
        HttpClientConfig http2       = null;  // intentionally null — for NullPath demo

        public String           getBaseUrl()    { return baseUrl; }
        public void             setBaseUrl(String v) { baseUrl = v; }
        public String           getApiKey()     { return apiKey; }
        public void             setApiKey(String v)  { apiKey = v; }
        public HttpClientConfig getHttp()       { return http; }
        public HttpClientConfig getHttp2()      { return http2; }
        @Override public String toString() {
            return "WeatherApi{url=" + baseUrl + " http=" + http + "}";
        }
    }

    // ── compound path injector with null-path detection ───────────────
    static class PathInjector {
        static void set(Object root, String path, Object value) {
            try {
                String[] parts = path.split("\\.");
                Object cur = root;
                for (int i = 0; i < parts.length - 1; i++) {
                    String g = "get" + cap(parts[i]);
                    cur = cur.getClass().getMethod(g).invoke(cur);
                    if (cur == null)
                        throw new RuntimeException(
                            "NullValueInNestedPathException: path='" + path
                            + "' null at segment='" + parts[i] + "'");
                }
                String leaf = parts[parts.length-1];
                for (var m : cur.getClass().getMethods()) {
                    if (m.getName().equals("set" + cap(leaf)) && m.getParameterCount() == 1) {
                        m.invoke(cur, coerce(value, m.getParameterTypes()[0]));
                        System.out.printf("  [SET] %-40s = %s%n", path, value);
                        return;
                    }
                }
            } catch (RuntimeException e) { throw e; }
            catch (Exception e) { throw new RuntimeException(e); }
        }

        static String cap(String s) { return Character.toUpperCase(s.charAt(0)) + s.substring(1); }
        static Object coerce(Object v, Class<?> t) {
            if (!(v instanceof String s)) return v;
            if (t == int.class)    return Integer.parseInt(s);
            if (t == long.class)   return Long.parseLong(s);
            if (t == double.class) return Double.parseDouble(s);
            if (t == boolean.class)return Boolean.parseBoolean(s);
            return v;
        }
    }

    public static void main(String[] args) {
        WeatherApiConfig cfg = new WeatherApiConfig();
        System.out.println("[BEFORE] " + cfg);
        System.out.println();

        System.out.println("=== Injecting compound paths ===");
        PathInjector.set(cfg, "apiKey",                    "sk-weather-api-abc");
        PathInjector.set(cfg, "http.connectTimeoutMs",     "2000");
        PathInjector.set(cfg, "http.readTimeoutMs",        "8000");
        PathInjector.set(cfg, "http.retry.maxAttempts",    "5");
        PathInjector.set(cfg, "http.retry.backoffMs",      "1000");
        PathInjector.set(cfg, "http.retry.backoffMultiplier", "1.5");

        System.out.println("\n[AFTER]  " + cfg);
        System.out.println();

        System.out.println("=== NullValueInNestedPathException demo ===");
        try {
            // http2 is null — traversal will fail
            PathInjector.set(cfg, "http2.connectTimeoutMs", "5000");
        } catch (RuntimeException e) {
            System.out.println("  Caught: " + e.getMessage());
        }
    }
}
```

How to run: `java CompoundPathDemo3.java`

Four-segment path `http.retry.backoffMs` navigates `WeatherApiConfig → getHttp() → getRetry() → setBackoffMs(1000)`. The null path demo shows exactly what Spring throws when an intermediate getter returns null: `NullValueInNestedPathException` names the offending path segment. `http2` is null so any compound path starting with `http2.` fails immediately at the first navigation step.

## 6. Walkthrough

**`PathInjector.set(cfg, "http.retry.backoffMultiplier", "1.5")`:**

```
path = "http.retry.backoffMultiplier"
parts = ["http", "retry", "backoffMultiplier"]

Navigation loop (i=0 to 1):
  i=0: getter = "getHttp"
       cur = cfg.getHttp() → HttpClientConfig (non-null) ✓
  i=1: getter = "getRetry"
       cur = httpConfig.getRetry() → RetryConfig (non-null) ✓

Leaf: "backoffMultiplier" → setter = "setBackoffMultiplier"
  m.getParameterTypes()[0] = double.class
  coerce("1.5", double.class) → Double.parseDouble("1.5") = 1.5
  retryConfig.setBackoffMultiplier(1.5)

Output: [SET] http.retry.backoffMultiplier          = 1.5
```

**`PathInjector.set(cfg, "http2.connectTimeoutMs", "5000")` — null path:**

```
parts = ["http2", "connectTimeoutMs"]

Navigation loop (i=0):
  getter = "getHttp2"
  cur = cfg.getHttp2() → null
  → throw NullValueInNestedPathException:
      path='http2.connectTimeoutMs' null at segment='http2'
```

## 7. Gotchas & takeaways

> **Every intermediate object in the compound path must be non-null at injection time.** Spring does not auto-create intermediate objects. If `tls` is `null` and you try `name="tls.port"`, Spring throws `NullValueInNestedPathException` at startup. Pre-initialise nested objects with field initialisers or a separate `<property name="tls" ref="tlsBean"/>`.

> **Compound paths work in XML and `BeanWrapper` but NOT in `@Value`.** `@Value("${server.tls.port:443}")` is a configuration property key (a string with dots) — it does not navigate Java object graphs. Navigation only happens via `BeanWrapper`/`@ConfigurationProperties`.

- The `@ConfigurationProperties(prefix = "server")` annotation uses compound-path binding: `server.tls.keyStore.path` in `application.properties` binds to `TlsConfig.keyStore.setPath(...)` via nested POJOs.
- Spring MVC model binding uses the same mechanism: a form field `address.city` binds to `customer.getAddress().setCity(...)`.
- Array/list index notation is also supported: `items[0].name` sets `getItems().get(0).setName(...)` via `BeanWrapper`.
- Keep compound paths in XML shallow (1–2 levels). Very deep paths are hard to read and break easily if intermediate objects change.
