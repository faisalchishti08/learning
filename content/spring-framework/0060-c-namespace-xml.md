---
card: spring-framework
gi: 60
slug: c-namespace-xml
title: c-namespace (XML)
---

## 1. What it is

The **c-namespace** is an XML shorthand for **constructor-argument injection** — the constructor counterpart to the p-namespace's setter injection. It uses the namespace URI `http://www.springframework.org/schema/c` and lets you express constructor arguments as XML attributes on the `<bean>` element, instead of nested `<constructor-arg>` elements.

```xml
<!-- Standard constructor-arg (verbose) -->
<bean id="encryptionService" class="EncryptionService">
    <constructor-arg name="algorithm"    value="AES-256-GCM"/>
    <constructor-arg name="keyLengthBits" value="256"/>
    <constructor-arg name="provider"     ref="jcaProviderBean"/>
</bean>

<!-- c-namespace equivalent (compact) -->
<bean id="encryptionService" class="EncryptionService"
    c:algorithm="AES-256-GCM"
    c:keyLengthBits="256"
    c:provider-ref="jcaProviderBean"/>
<!--
    c:paramName="value"      ← constructor param by name (requires debug info or @ConstructorProperties)
    c:paramName-ref="beanId" ← constructor param reference by name
    c:_0="value"             ← constructor param by index (0-based)
    c:_0-ref="beanId"        ← constructor param reference by index
-->
```

In one sentence: **The c-namespace lets you express constructor-argument injection as XML attributes (`c:paramName="value"` or `c:_0="value"`) instead of `<constructor-arg>` child elements, making XML constructor-injection config more compact.**

## 2. Why & when

Use the c-namespace when:

- You have **constructor injection** (preferred over setter injection for mandatory deps) and want compact XML.
- Your constructors have **few parameters** (3–5) — for longer constructor lists the verbose form is clearer.
- Your class has **debug symbol information** (compiled with `-parameters` or `@ConstructorProperties`) so Spring can resolve parameters by name; otherwise use index notation (`c:_0`, `c:_1`).
- You want consistency: if you use p-namespace for setters, use c-namespace for constructors to keep the XML style uniform.

Limitations identical to p-namespace:
- Cannot inject **collections** (`<list>`, `<set>`, `<map>`).
- Cannot inject **`<null/>`** or inner beans.
- Names work only when the class was compiled with `-parameters` flag or annotated with `@ConstructorProperties`.

## 3. Core concept

```
Namespace declaration:
  xmlns:c="http://www.springframework.org/schema/c"

Attribute forms:
  c:name="value"      → <constructor-arg name="name" value="value"/>
  c:name-ref="beanId" → <constructor-arg name="name" ref="beanId"/>
  c:_0="value"        → <constructor-arg index="0" value="value"/>
  c:_0-ref="beanId"   → <constructor-arg index="0" ref="beanId"/>

Name-based vs index-based:
  Name-based (c:host="..."):
    requires -parameters compile flag OR @ConstructorProperties annotation
  Index-based (c:_0="..."):
    always works, no compile-flag requirement
    underscore + zero-based number

Mixed is possible:
  <bean ... c:_0="AES" c:keyLengthBits="256"/>  ← index for first, name for second
```

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="c-namespace attributes map to constructor-arg elements — name-based and index-based forms">
  <defs>
    <marker id="a60" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="185" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">c-namespace → &lt;constructor-arg&gt; — same bean definition, different syntax</text>

  <!-- c-namespace -->
  <rect x="15" y="30" width="290" height="140" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="48" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">c-namespace (compact)</text>
  <text x="160" y="64" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">— name-based —</text>
  <text x="160" y="80" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">&lt;bean class="Svc"</text>
  <text x="160" y="94" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">  c:host="localhost"</text>
  <text x="160" y="108" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">  c:port="8080"</text>
  <text x="160" y="122" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">  c:ds-ref="dataSource"/&gt;</text>
  <line x1="15" y1="135" x2="305" y2="135" stroke="#8b949e" stroke-width="0.5"/>
  <text x="160" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">— index-based (always works) —</text>
  <text x="160" y="162" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">c:_0="localhost" c:_1="8080"</text>

  <!-- equals -->
  <line x1="307" y1="95" x2="345" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a60)"/>
  <text x="326" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">≡</text>

  <!-- verbose form -->
  <rect x="347" y="30" width="295" height="140" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="494" y="48" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;constructor-arg&gt; form (verbose)</text>
  <text x="494" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">&lt;bean class="Svc"&gt;</text>
  <text x="494" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;constructor-arg name="host"</text>
  <text x="494" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">                  value="localhost"/&gt;</text>
  <text x="494" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;constructor-arg name="port"</text>
  <text x="494" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">                  value="8080"/&gt;</text>
  <text x="494" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;constructor-arg name="ds"</text>
  <text x="494" y="146" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">                  ref="dataSource"/&gt;</text>
  <text x="494" y="162" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">&lt;/bean&gt;</text>

  <text x="330" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Spring treats both forms as identical BeanDefinitions at parse time.</text>
</svg>

Name-based c-namespace (`c:host="..."`) requires the `-parameters` compiler flag. Index-based (`c:_0="..."`) always works. Both produce the same `BeanDefinition` as verbose `<constructor-arg>` elements.

## 5. Runnable example

Scenario: a `ConnectionPool` with a mandatory constructor that takes host, port, max-connections, and a `CredentialStore` reference. We wire it with full `<constructor-arg>` elements, then with c-namespace, showing how both work and what c-namespace cannot do.

### Level 1 — Basic

Constructor injection with three params — show name-based and index-based c-namespace.

```java
// CNamespaceDemo.java — run with: java CNamespaceDemo.java

public class CNamespaceDemo {

    static class CredentialStore {
        final String vaultUrl;
        CredentialStore(String vaultUrl) {
            this.vaultUrl = vaultUrl;
            System.out.println("  [BEAN] CredentialStore: vault=" + vaultUrl);
        }
        String getPassword(String service) { return "pass-for-" + service; }
    }

    static class ConnectionPool {
        final String          host;
        final int             port;
        final int             maxConnections;
        final CredentialStore credentials;

        // Constructor — params need @ConstructorProperties or -parameters flag
        // for c:name="..." to work; c:_0, c:_1 always work
        ConnectionPool(String host, int port, int maxConnections, CredentialStore credentials) {
            this.host           = host;
            this.port           = port;
            this.maxConnections = maxConnections;
            this.credentials    = credentials;
            System.out.printf("  [BEAN] ConnectionPool: %s:%d maxConn=%d%n",
                host, port, maxConnections);
        }

        String connect() {
            String pwd = credentials.getPassword("db");
            return "connected to " + host + ":" + port + " (max=" + maxConnections
                + " pwd=" + pwd + ")";
        }
    }

    // ── verbose constructor-arg form ───────────────────────────────────
    // <bean id="pool" class="ConnectionPool">
    //   <constructor-arg name="host"           value="db.example.com"/>
    //   <constructor-arg name="port"           value="5432"/>
    //   <constructor-arg name="maxConnections" value="20"/>
    //   <constructor-arg name="credentials"    ref="credentialStore"/>
    // </bean>

    // ── c-namespace name-based form ────────────────────────────────────
    // <bean id="pool" class="ConnectionPool"
    //     c:host="db.example.com"
    //     c:port="5432"
    //     c:maxConnections="20"
    //     c:credentials-ref="credentialStore"/>

    // ── c-namespace index-based form ───────────────────────────────────
    // <bean id="pool" class="ConnectionPool"
    //     c:_0="db.example.com"
    //     c:_1="5432"
    //     c:_2="20"
    //     c:_3-ref="credentialStore"/>

    static ConnectionPool build() {
        CredentialStore creds = new CredentialStore("https://vault.example.com");
        return new ConnectionPool("db.example.com", 5432, 20, creds);
    }

    public static void main(String[] args) {
        ConnectionPool pool = build();
        System.out.println("[CONNECT] " + pool.connect());

        System.out.println("\n[C-NAMESPACE EQUIVALENTS]");
        System.out.println("  Name-based:  c:host=\"db.example.com\" c:port=\"5432\" ...");
        System.out.println("  Index-based: c:_0=\"db.example.com\" c:_1=\"5432\" ...");
        System.out.println("  (Both resolve to the same ConnectionPool constructor call)");
    }
}
```

How to run: `java CNamespaceDemo.java`

Three c-namespace forms are shown in comments: verbose `<constructor-arg>`, name-based `c:host=`, and index-based `c:_0=`. In real Spring XML, all three produce the same `ConnectionPool(host, port, maxConnections, credentials)` call. The `-ref` suffix (`c:credentials-ref`) signals a bean reference; without it, the value is treated as a string.

### Level 2 — Intermediate

Show c-namespace + p-namespace mixed on the same `<bean>`, and demonstrate that index-based always works even without compile flags.

```java
// CNamespaceDemo2.java — run with: java CNamespaceDemo2.java

public class CNamespaceDemo2 {

    // ── two-param constructor → use c-namespace ─────────────────────────
    static class JwtConfig {
        final String secret;
        final int    expiryMinutes;

        JwtConfig(String secret, int expiryMinutes) {
            this.secret        = secret;
            this.expiryMinutes = expiryMinutes;
            System.out.println("  [BEAN] JwtConfig: expiry=" + expiryMinutes + "m");
        }
    }

    // ── three setter properties → use p-namespace ──────────────────────
    static class AuthService {
        final JwtConfig jwt;   // constructor-injected (c-namespace)
        String  issuer;        // setter-injected (p-namespace)
        boolean mfaEnabled;    // setter-injected
        int     maxSessions;   // setter-injected

        // Mixed: constructor for mandatory deps, setters for optional config
        AuthService(JwtConfig jwt) {
            this.jwt = jwt;
            System.out.println("  [BEAN] AuthService: jwt.expiry=" + jwt.expiryMinutes + "m");
        }

        void setIssuer(String v)      { this.issuer = v; }
        void setMfaEnabled(boolean v) { this.mfaEnabled = v; }
        void setMaxSessions(int v)    { this.maxSessions = v; }

        // XML: <bean id="authService" class="AuthService"
        //           c:jwt-ref="jwtConfig"     ← constructor ref (c-namespace)
        //           p:issuer="auth.example.com"  ← setter (p-namespace)
        //           p:mfaEnabled="true"
        //           p:maxSessions="5"/>

        String generateToken(String userId) {
            return "[JWT:" + jwt.secret.substring(0,4) + "... iss=" + issuer
                + " user=" + userId + " exp=" + jwt.expiryMinutes + "m]";
        }

        void printConfig() {
            System.out.printf("  AuthService: issuer=%s mfa=%b maxSessions=%d%n",
                issuer, mfaEnabled, maxSessions);
        }
    }

    static AuthService buildContainer() {
        // c-namespace: c:_0="s3cr3t-key" c:_1="60"  (index-based — no compile flag needed)
        JwtConfig  jwt  = new JwtConfig("s3cr3t-key-ABC123-256bit", 60);

        // c-namespace on AuthService: c:jwt-ref="jwtConfig" (name) or c:_0-ref="jwtConfig" (index)
        AuthService svc = new AuthService(jwt);

        // p-namespace: p:issuer="..." p:mfaEnabled="true" p:maxSessions="5"
        svc.setIssuer("auth.example.com");
        svc.setMfaEnabled(true);
        svc.setMaxSessions(5);
        svc.printConfig();
        return svc;
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        AuthService auth = buildContainer();
        System.out.println();
        System.out.println("=== Token generation ===");
        System.out.println("  user-123: " + auth.generateToken("user-123"));
        System.out.println("  admin:    " + auth.generateToken("admin"));
    }
}
```

How to run: `java CNamespaceDemo2.java`

`JwtConfig` uses c-namespace for its 2-param constructor. `AuthService` uses c-namespace for the constructor ref (`c:jwt-ref`) and p-namespace for the three setter properties. Mixing both namespaces on the same bean is legal and common — each handles a different injection mode (constructor vs setter).

### Level 3 — Advanced

Four-param constructor, index-based c-namespace (works without compile flags), type-coercion, and demonstrating c-namespace limits vs `<constructor-arg>`.

```java
// CNamespaceDemo3.java — run with: java CNamespaceDemo3.java
import java.util.*;

public class CNamespaceDemo3 {

    static class MetricsExporter {
        final String  endpoint;
        final int     pushIntervalSec;
        final boolean tlsEnabled;
        final int     batchSize;

        // @ConstructorProperties simulates -parameters flag for c:name="..." to work
        MetricsExporter(String endpoint, int pushIntervalSec, boolean tlsEnabled, int batchSize) {
            this.endpoint        = endpoint;
            this.pushIntervalSec = pushIntervalSec;
            this.tlsEnabled      = tlsEnabled;
            this.batchSize       = batchSize;
            System.out.printf("  [BEAN] MetricsExporter: %s interval=%ds tls=%b batch=%d%n",
                endpoint, pushIntervalSec, tlsEnabled, batchSize);
        }

        // Verbose XML:
        // <bean class="MetricsExporter">
        //   <constructor-arg name="endpoint"       value="https://metrics.example.com/v1/push"/>
        //   <constructor-arg name="pushIntervalSec" value="15"/>
        //   <constructor-arg name="tlsEnabled"     value="true"/>
        //   <constructor-arg name="batchSize"      value="500"/>
        // </bean>

        // c-namespace name-based (requires -parameters):
        // <bean class="MetricsExporter"
        //     c:endpoint="https://metrics.example.com/v1/push"
        //     c:pushIntervalSec="15"
        //     c:tlsEnabled="true"
        //     c:batchSize="500"/>

        // c-namespace index-based (ALWAYS works, no -parameters needed):
        // <bean class="MetricsExporter"
        //     c:_0="https://metrics.example.com/v1/push"
        //     c:_1="15"
        //     c:_2="true"
        //     c:_3="500"/>

        void exportMetrics(Map<String, Double> metrics) {
            System.out.printf("  [EXPORT] → %s batch=%d tls=%b%n", endpoint, batchSize, tlsEnabled);
            int count = 0;
            for (Map.Entry<String, Double> e : metrics.entrySet()) {
                System.out.printf("    metric: %s = %.2f%n", e.getKey(), e.getValue());
                if (++count >= batchSize) { System.out.println("    ... (batch limit reached)"); break; }
            }
        }
    }

    // What c-namespace CANNOT do — must use <constructor-arg> child with nested element:
    static class MetricsAggregator {
        final List<String>   sourceNames;    // collection — no c-namespace
        final MetricsExporter exporter;      // ref — c-namespace OK with -ref suffix
        final String          jobName;       // scalar — c-namespace OK

        MetricsAggregator(List<String> sourceNames, MetricsExporter exporter, String jobName) {
            this.sourceNames = sourceNames;
            this.exporter    = exporter;
            this.jobName     = jobName;
            System.out.println("  [BEAN] MetricsAggregator: job=" + jobName
                + " sources=" + sourceNames + " exporter=" + exporter.endpoint);
        }

        // Hybrid XML:
        // <bean class="MetricsAggregator"
        //     c:exporter-ref="metricsExporter"   ← c-namespace: ref ✓
        //     c:jobName="hourly-aggregation">     ← c-namespace: scalar ✓
        //     <constructor-arg name="sourceNames">  ← regular: collection (c-namespace cannot)
        //         <list>
        //             <value>prometheus</value>
        //             <value>statsd</value>
        //             <value>cloudwatch</value>
        //         </list>
        //     </constructor-arg>
        // </bean>

        void run() {
            System.out.println("[AGG] Running job=" + jobName + " sources=" + sourceNames);
            Map<String, Double> metrics = new LinkedHashMap<>();
            for (String src : sourceNames) {
                metrics.put(src + ".requests_total", Math.random() * 1000);
                metrics.put(src + ".error_rate",     Math.random() * 0.05);
            }
            exporter.exportMetrics(metrics);
        }
    }

    static MetricsAggregator buildContainer() {
        System.out.println("=== Container startup ===");
        // c-namespace on MetricsExporter (index-based: c:_0..c:_3)
        MetricsExporter exporter = new MetricsExporter(
            "https://metrics.example.com/v1/push", 15, true, 100
        );
        // MetricsAggregator: hybrid — collection must be passed directly
        return new MetricsAggregator(
            List.of("prometheus", "statsd", "cloudwatch"), // not c-namespace eligible
            exporter,         // c:exporter-ref eligible
            "hourly-aggregation"  // c:jobName eligible
        );
    }

    public static void main(String[] args) {
        MetricsAggregator agg = buildContainer();
        System.out.println();
        agg.run();
    }
}
```

How to run: `java CNamespaceDemo3.java`

`MetricsExporter` demonstrates both XML forms in comments: verbose `<constructor-arg>`, name-based `c:endpoint=`, and index-based `c:_0=`. `MetricsAggregator` shows the hybrid: `c:exporter-ref` and `c:jobName` are c-namespace-eligible, but `sourceNames` (a `List`) must use a regular `<constructor-arg><list>` — c-namespace cannot express collection values.

## 6. Walkthrough

**`buildContainer()` — how c-namespace resolves for `MetricsExporter`:**

```
XML (index-based, always safe):
  c:_0="https://metrics.example.com/v1/push"
  c:_1="15"
  c:_2="true"
  c:_3="100"

Spring resolution:
  _0 → index 0 → param type: String
       value "https://..." → no coercion needed → "https://metrics.example.com/v1/push"
  _1 → index 1 → param type: int
       ConversionService: "15" → int 15
  _2 → index 2 → param type: boolean
       ConversionService: "true" → boolean true
  _3 → index 3 → param type: int
       ConversionService: "100" → int 100

Constructor call:
  new MetricsExporter(
    "https://metrics.example.com/v1/push",  // _0
    15,                                      // _1
    true,                                    // _2
    100                                      // _3
  )
Output:
  [BEAN] MetricsExporter: https://... interval=15s tls=true batch=100
```

**`MetricsAggregator` hybrid:**

```
c:exporter-ref="metricsExporter"
  → container.getBean("metricsExporter") → MetricsExporter instance
  → arg index 1 (matching param type MetricsExporter)

c:jobName="hourly-aggregation"
  → String literal → arg index 2

<constructor-arg name="sourceNames"><list>...
  → List.of("prometheus","statsd","cloudwatch") → arg index 0

Constructor call:
  new MetricsAggregator(
    List.of("prometheus","statsd","cloudwatch"),
    exporter,
    "hourly-aggregation"
  )
```

**`agg.run()` — execution:**

```
job=hourly-aggregation sources=[prometheus, statsd, cloudwatch]
For each source:
  prometheus.requests_total → random ~[0,1000]
  prometheus.error_rate     → random ~[0,0.05]
  statsd.requests_total, statsd.error_rate
  cloudwatch.requests_total, cloudwatch.error_rate
→ exporter.exportMetrics(metrics)
  → [EXPORT] → https://metrics.example.com/v1/push batch=100 tls=true
  → prints all 6 metric lines
```

## 7. Gotchas & takeaways

> **c-namespace name-based attributes require the `-parameters` compiler flag** (added in Java 8, but not the default). Without it, Spring cannot resolve parameter names from bytecode and throws `IllegalStateException: Ambiguous argument values for parameter...`. Fall back to index-based `c:_0=`, `c:_1=` — these always work without any compile flag.

> **c-namespace cannot handle `null`, inner beans, or collection types.** For those, keep the `<constructor-arg>` child element and mix it with c-namespace attributes on the same `<bean>` — this is explicitly supported.

- The `@ConstructorProperties({"host","port",...})` annotation on a constructor tells Spring the parameter names without needing the `-parameters` flag — useful for library jars where you do not control the compilation.
- The underscore prefix in `c:_0` is required because XML attribute names cannot start with a digit (`c:0` is not valid XML).
- c-namespace and p-namespace may appear on the same `<bean>` element: c-namespace handles constructor args, p-namespace handles setter properties.
- In modern Spring Boot applications with `@Configuration` classes, c-namespace XML is rarely needed — constructor injection via `@Autowired` or implicit single-constructor autowiring is the standard approach.
