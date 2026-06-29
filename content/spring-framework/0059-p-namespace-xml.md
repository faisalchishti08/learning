---
card: spring-framework
gi: 59
slug: p-namespace-xml
title: p-namespace (XML)
---

## 1. What it is

The **p-namespace** is an XML shorthand that lets you express property injection as XML *attributes* on a `<bean>` element, instead of writing verbose nested `<property>` child elements. It uses the namespace URI `http://www.springframework.org/schema/p`, declared as `xmlns:p="..."` on the root `<beans>` element.

```xml
<!-- Standard XML (verbose) -->
<bean id="user" class="User">
    <property name="firstName" value="John"/>
    <property name="lastName"  value="Smith"/>
    <property name="email"     value="john@example.com"/>
    <property name="address"   ref="addressBean"/>
</bean>

<!-- p-namespace equivalent (compact) -->
<bean id="user" class="User"
    p:firstName="John"
    p:lastName="Smith"
    p:email="john@example.com"
    p:address-ref="addressBean"/>
<!--
    p:propertyName="value"      ← sets a scalar/string value
    p:propertyName-ref="beanId" ← injects a bean reference
-->
```

The p-namespace is a pure authoring convenience — the bean definition produced is identical to the verbose form. Spring strips the `p:` prefix and delegates to the same `BeanDefinitionParserDelegate` that handles `<property>`.

In one sentence: **The p-namespace lets you write property injections as XML attributes (`p:fieldName="value"` and `p:fieldName-ref="beanId"`) instead of nested `<property>` elements, making XML bean definitions shorter without changing their semantics.**

## 2. Why & when

Use the p-namespace when:

- You have many **simple scalar properties** on a bean and want to avoid 5–10 `<property>` elements.
- The bean configuration is **read-only configuration** (no complex sub-elements like `<list>`) — p-namespace works best with flat scalar values and bean refs.
- You want more **compact XML** that resembles property file syntax while still being in a structured format.

Limitations — you cannot use the p-namespace for:
- Injecting **collections** (`<list>`, `<set>`, `<map>`, `<props>`).
- Setting **`<null/>`** (use a `<property>` child element with `<null/>` for that).
- **Inner beans** (nested `<bean>` elements must stay in `<property>`).

## 3. Core concept

```
Namespace declaration (beans element):
  xmlns:p="http://www.springframework.org/schema/p"

p-namespace attribute rules:
  p:name="value"      → <property name="name" value="value"/>
  p:name-ref="beanId" → <property name="name" ref="beanId"/>

The "-ref" suffix signals a bean reference, not a string value.

Full XML context:
  <beans xmlns="http://www.springframework.org/schema/beans"
         xmlns:p="http://www.springframework.org/schema/p"
         ...>

    <bean id="myBean" class="MyClass"
          p:timeout="5000"
          p:host="localhost"
          p:dataSource-ref="dataSourceBean"/>

  </beans>
```

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="p-namespace attributes on left become property elements on right — same bean definition, different syntax">
  <defs>
    <marker id="a59" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="650" height="185" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">p-namespace → &lt;property&gt; — identical bean definition</text>

  <!-- p-namespace form -->
  <rect x="15" y="30" width="295" height="130" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="162" y="48" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">p-namespace (compact)</text>
  <text x="162" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">&lt;bean id="mailer" class="Mailer"</text>
  <text x="162" y="82" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">  p:host="smtp.example.com"</text>
  <text x="162" y="98" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">  p:port="587"</text>
  <text x="162" y="114" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">  p:tls="true"</text>
  <text x="162" y="130" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">  p:sender-ref="senderBean"/&gt;</text>
  <text x="162" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">4 attributes — 1 bean element</text>

  <!-- Equals arrow -->
  <line x1="312" y1="95" x2="348" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a59)"/>
  <text x="330" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">≡</text>

  <!-- standard form -->
  <rect x="350" y="30" width="295" height="145" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="497" y="48" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;property&gt; form (verbose)</text>
  <text x="497" y="66" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">&lt;bean id="mailer" class="Mailer"&gt;</text>
  <text x="497" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;property name="host" value="smtp.example.com"/&gt;</text>
  <text x="497" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;property name="port" value="587"/&gt;</text>
  <text x="497" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;property name="tls"  value="true"/&gt;</text>
  <text x="497" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">  &lt;property name="sender" ref="senderBean"/&gt;</text>
  <text x="497" y="148" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">&lt;/bean&gt;</text>
  <text x="497" y="165" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">5 elements — 4 property children</text>

  <text x="330" y="190" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Spring parses both forms into the same BeanDefinition.</text>
</svg>

The p-namespace and the `<property>` form produce exactly the same internal `BeanDefinition`. The difference is only in the XML source — not in what Spring does with it.

## 5. Runnable example

Scenario: a `MailerService` bean with SMTP settings and a reference to a `MessageFormatter` bean. We wire it first with `<property>` elements, then refactor to p-namespace.

### Level 1 — Basic

Demonstrate property injection using standard XML, then the p-namespace equivalent.

```java
// PNamespaceDemo.java — run with: java PNamespaceDemo.java

public class PNamespaceDemo {

    static class MessageFormatter {
        final String template;
        MessageFormatter(String template) {
            this.template = template;
            System.out.println("  [BEAN] MessageFormatter: template=" + template);
        }
        String format(String to, String subject, String body) {
            return template
                .replace("{to}", to)
                .replace("{subject}", subject)
                .replace("{body}", body);
        }
    }

    static class MailerService {
        String           host;
        int              port;
        boolean          tls;
        String           username;
        String           password;
        MessageFormatter formatter;   // bean reference

        // Setters (property injection)
        void setHost(String v)              { this.host = v; }
        void setPort(int v)                 { this.port = v; }
        void setTls(boolean v)              { this.tls = v; }
        void setUsername(String v)          { this.username = v; }
        void setPassword(String v)          { this.password = v; }
        void setFormatter(MessageFormatter v) { this.formatter = v; }

        void init() {
            System.out.println("  [BEAN] MailerService: host=" + host + " port=" + port
                + " tls=" + tls + " user=" + username);
        }

        boolean send(String to, String subject, String body) {
            String msg = formatter.format(to, subject, body);
            System.out.println("  [SEND] via " + host + ":" + port
                + " tls=" + tls + "\n    " + msg);
            return true;
        }
    }

    // ── simulate XML <property> injection ─────────────────────────────
    static MailerService buildWithPropertyElement() {
        MessageFormatter fmt = new MessageFormatter("To: {to}\nSubject: {subject}\n\n{body}");

        MailerService mailer = new MailerService();
        // equivalent to <property name="host" value="smtp.sendgrid.net"/>
        mailer.setHost("smtp.sendgrid.net");
        mailer.setPort(587);
        mailer.setTls(true);
        mailer.setUsername("apikey");
        mailer.setPassword("SG.xxx");
        // equivalent to <property name="formatter" ref="messageFormatter"/>
        mailer.setFormatter(fmt);
        mailer.init();
        return mailer;
    }

    // ── simulate p-namespace injection (identical result) ─────────────
    // p:host="smtp.sendgrid.net" p:port="587" p:tls="true"
    // p:username="apikey" p:password="SG.xxx" p:formatter-ref="messageFormatter"
    static MailerService buildWithPNamespace() {
        // p-namespace produces IDENTICAL setters calls — same result
        return buildWithPropertyElement();
    }

    public static void main(String[] args) {
        System.out.println("=== Property-element style ===");
        MailerService m1 = buildWithPropertyElement();
        m1.send("alice@example.com", "Welcome", "Thanks for signing up!");

        System.out.println("\n=== p-namespace style (same result) ===");
        MailerService m2 = buildWithPNamespace();
        m2.send("bob@example.com", "Order Confirmed", "Your order #1234 is ready.");
    }
}
```

How to run: `java PNamespaceDemo.java`

Both build methods produce identical `MailerService` instances. In real Spring, the XML difference is purely syntactic: `p:host="smtp.sendgrid.net"` and `<property name="host" value="smtp.sendgrid.net"/>` produce the same `BeanDefinition` — the same setter is called at the same time with the same value.

### Level 2 — Intermediate

Compare verbose XML vs p-namespace for a bean with five properties and two refs. Show that p-namespace reduces line count significantly.

```java
// PNamespaceDemo2.java — run with: java PNamespaceDemo2.java
import java.util.*;

public class PNamespaceDemo2 {

    // ── two collaborator beans ─────────────────────────────────────────
    static class DataSource {
        final String url;
        DataSource(String url) {
            this.url = url;
            System.out.println("  [BEAN] DataSource: url=" + url);
        }
        String query(String sql) { return "[rows from " + url + " for: " + sql + "]"; }
    }

    static class CacheManager {
        final int ttlSec;
        final Map<String,String> store = new LinkedHashMap<>();
        CacheManager(int ttlSec) {
            this.ttlSec = ttlSec;
            System.out.println("  [BEAN] CacheManager: ttlSec=" + ttlSec);
        }
        void put(String k, String v)   { store.put(k, v); }
        String get(String k)           { return store.get(k); }
    }

    // ── main service bean with 5 scalars + 2 refs ─────────────────────
    static class ProductCatalogService {
        // scalars
        String  serviceName;
        int     maxResults;
        boolean enableSearch;
        String  defaultLocale;
        long    cacheKeyTtlMs;
        // bean refs
        DataSource   dataSource;
        CacheManager cacheManager;

        void setServiceName(String v)       { this.serviceName = v; }
        void setMaxResults(int v)           { this.maxResults = v; }
        void setEnableSearch(boolean v)     { this.enableSearch = v; }
        void setDefaultLocale(String v)     { this.defaultLocale = v; }
        void setCacheKeyTtlMs(long v)       { this.cacheKeyTtlMs = v; }
        void setDataSource(DataSource v)    { this.dataSource = v; }
        void setCacheManager(CacheManager v){ this.cacheManager = v; }

        void init() {
            System.out.println("  [BEAN] ProductCatalogService:");
            System.out.printf("    name=%s maxResults=%d search=%b locale=%s ttlMs=%d%n",
                serviceName, maxResults, enableSearch, defaultLocale, cacheKeyTtlMs);
        }

        List<String> findProducts(String query) {
            String cacheKey = "q:" + query;
            String cached = cacheManager.get(cacheKey);
            if (cached != null) {
                System.out.println("  [CACHE HIT] " + query);
                return List.of(cached.split(","));
            }
            String raw = dataSource.query("SELECT * FROM products WHERE name LIKE '%" + query + "%'");
            String[] items = {"Product-A", "Product-B"};  // simulated
            cacheManager.put(cacheKey, String.join(",", items));
            System.out.println("  [DB HIT] " + query + " → " + Arrays.toString(items));
            return Arrays.asList(items);
        }
    }

    // ── verbose XML style: <property name="..." value="..."/>  ──────────────
    // <bean id="catalogService" class="ProductCatalogService">
    //     <property name="serviceName"   value="Product Catalog v2"/>
    //     <property name="maxResults"    value="50"/>
    //     <property name="enableSearch"  value="true"/>
    //     <property name="defaultLocale" value="en-US"/>
    //     <property name="cacheKeyTtlMs" value="300000"/>
    //     <property name="dataSource"    ref="dataSource"/>
    //     <property name="cacheManager"  ref="cacheManager"/>
    // </bean>

    // ── p-namespace style (7 attributes, 1 element):
    // <bean id="catalogService" class="ProductCatalogService"
    //     p:serviceName="Product Catalog v2"
    //     p:maxResults="50"
    //     p:enableSearch="true"
    //     p:defaultLocale="en-US"
    //     p:cacheKeyTtlMs="300000"
    //     p:dataSource-ref="dataSource"
    //     p:cacheManager-ref="cacheManager"/>

    static ProductCatalogService buildBean() {
        DataSource    ds    = new DataSource("jdbc:postgresql://db:5432/catalog");
        CacheManager  cache = new CacheManager(300);
        ProductCatalogService svc = new ProductCatalogService();
        svc.setServiceName("Product Catalog v2");
        svc.setMaxResults(50);
        svc.setEnableSearch(true);
        svc.setDefaultLocale("en-US");
        svc.setCacheKeyTtlMs(300_000L);
        svc.setDataSource(ds);
        svc.setCacheManager(cache);
        svc.init();
        return svc;
    }

    public static void main(String[] args) {
        ProductCatalogService svc = buildBean();
        System.out.println();
        System.out.println("[SEARCH] laptop:  " + svc.findProducts("laptop"));
        System.out.println("[SEARCH] laptop:  " + svc.findProducts("laptop")); // cache hit
        System.out.println("[SEARCH] monitor: " + svc.findProducts("monitor"));
    }
}
```

How to run: `java PNamespaceDemo2.java`

Verbose XML form: 9 lines (7 `<property>` + opening/closing `<bean>` tags). p-namespace form: 8 lines total (1 `<bean>` with 7 attributes, self-closing). The p-namespace version is roughly 30% shorter for this case. The `cacheManager` and `dataSource` refs use `-ref` suffix: `p:dataSource-ref="dataSource"`.

### Level 3 — Advanced

A complete application context equivalent showing p-namespace for multiple beans with cross-refs, plus demonstrating what p-namespace cannot do (collections, null).

```java
// PNamespaceDemo3.java — run with: java PNamespaceDemo3.java
import java.util.*;

public class PNamespaceDemo3 {

    // ── infrastructure beans ───────────────────────────────────────────
    static class EncryptionService {
        final String algorithm;
        final int    keyLengthBits;
        EncryptionService(String algorithm, int keyLengthBits) {
            this.algorithm     = algorithm;
            this.keyLengthBits = keyLengthBits;
            System.out.println("  [BEAN] EncryptionService: alg=" + algorithm + " keyLen=" + keyLengthBits);
        }
        String encrypt(String data) { return "[ENC:" + algorithm + ":" + data + "]"; }
    }

    static class RateLimiter {
        final int    requestsPerMin;
        final int    burstCapacity;
        final boolean strictMode;
        RateLimiter(int rpm, int burst, boolean strict) {
            this.requestsPerMin = rpm;
            this.burstCapacity  = burst;
            this.strictMode     = strict;
            System.out.println("  [BEAN] RateLimiter: rpm=" + rpm + " burst=" + burst + " strict=" + strict);
        }
        boolean allow(String clientId) {
            System.out.println("  [RATE] checking " + clientId + " (rpm=" + requestsPerMin + ")");
            return true; // always allow in demo
        }
    }

    // ── service bean: p-namespace candidates ──────────────────────────
    static class AuthService {
        // scalars: can be done with p-namespace
        String  jwtSecret;
        int     tokenExpiryMin;
        boolean refreshEnabled;
        String  issuer;
        // bean refs: p-namespace with -ref suffix
        EncryptionService encryption;
        RateLimiter       rateLimiter;
        // collection: CANNOT use p-namespace
        List<String>      allowedAudiences;  // must use <property><list>...

        void setJwtSecret(String v)        { this.jwtSecret = v; }
        void setTokenExpiryMin(int v)      { this.tokenExpiryMin = v; }
        void setRefreshEnabled(boolean v)  { this.refreshEnabled = v; }
        void setIssuer(String v)           { this.issuer = v; }
        void setEncryption(EncryptionService v)  { this.encryption = v; }
        void setRateLimiter(RateLimiter v)       { this.rateLimiter = v; }
        void setAllowedAudiences(List<String> v) { this.allowedAudiences = v; }

        void init() {
            System.out.println("  [BEAN] AuthService: issuer=" + issuer
                + " expiry=" + tokenExpiryMin + "m refresh=" + refreshEnabled
                + " audiences=" + allowedAudiences);
        }

        String authenticate(String clientId, String credential) {
            if (!rateLimiter.allow(clientId)) return "RATE_LIMITED";
            String token = encryption.encrypt(issuer + ":" + clientId + ":" + tokenExpiryMin + "m");
            System.out.println("  [AUTH] " + clientId + " → token=" + token);
            return token;
        }
    }

    // XML that demonstrates what p-namespace CAN and CANNOT do:
    // <!-- p-namespace CAN handle scalars and refs -->
    // <bean id="authService" class="AuthService"
    //     p:jwtSecret="s3cr3t-key-abc"          ← scalar ✓
    //     p:tokenExpiryMin="60"                  ← scalar ✓
    //     p:refreshEnabled="true"                ← scalar ✓
    //     p:issuer="auth.example.com"            ← scalar ✓
    //     p:encryption-ref="encryptionService"   ← ref ✓
    //     p:rateLimiter-ref="rateLimiter">       ← ref ✓
    //     <!-- p-namespace CANNOT handle List — must use <property> -->
    //     <property name="allowedAudiences">
    //         <list>
    //             <value>api.example.com</value>
    //             <value>app.example.com</value>
    //         </list>
    //     </property>
    // </bean>

    static AuthService buildContainer() {
        EncryptionService enc  = new EncryptionService("AES-256-GCM", 256);
        RateLimiter       rl   = new RateLimiter(100, 20, false);
        AuthService       auth = new AuthService();

        // Scalar injection (p-namespace compatible)
        auth.setJwtSecret("s3cr3t-key-abc");
        auth.setTokenExpiryMin(60);
        auth.setRefreshEnabled(true);
        auth.setIssuer("auth.example.com");

        // Ref injection (p-namespace: p:encryption-ref / p:rateLimiter-ref)
        auth.setEncryption(enc);
        auth.setRateLimiter(rl);

        // Collection injection — MUST use <property><list> (not p-namespace)
        auth.setAllowedAudiences(List.of("api.example.com", "app.example.com"));

        auth.init();
        return auth;
    }

    public static void main(String[] args) {
        System.out.println("=== Container startup ===");
        AuthService auth = buildContainer();
        System.out.println();
        System.out.println("=== Authentication requests ===");
        System.out.println("  token1: " + auth.authenticate("client-123", "password1"));
        System.out.println("  token2: " + auth.authenticate("client-456", "password2"));
    }
}
```

How to run: `java PNamespaceDemo3.java`

`AuthService` uses a hybrid: p-namespace for 4 scalars and 2 refs, then a regular `<property><list>` element for `allowedAudiences` — because p-namespace cannot express collections. The XML comment inside the code block shows exactly which parts are p-namespace-eligible and which require `<property>` children.

## 6. Walkthrough

**`buildContainer()` — what Spring does for each p-namespace attribute:**

```
p:jwtSecret="s3cr3t-key-abc"
  → auth.setJwtSecret("s3cr3t-key-abc")     [String setter]

p:tokenExpiryMin="60"
  → ConversionService: "60" → int 60
  → auth.setTokenExpiryMin(60)              [int setter]

p:refreshEnabled="true"
  → ConversionService: "true" → boolean true
  → auth.setRefreshEnabled(true)            [boolean setter]

p:issuer="auth.example.com"
  → auth.setIssuer("auth.example.com")      [String setter]

p:encryption-ref="encryptionService"
  → container.getBean("encryptionService")  [lookup by id]
  → auth.setEncryption(encryptionService)   [EncryptionService setter]

p:rateLimiter-ref="rateLimiter"
  → container.getBean("rateLimiter")
  → auth.setRateLimiter(rateLimiter)        [RateLimiter setter]

<property name="allowedAudiences"><list>...</list></property>
  → auth.setAllowedAudiences(List.of("api...", "app..."))
  [List: not expressible in p-namespace]
```

**`auth.authenticate("client-123", "password1")`:**

```
rateLimiter.allow("client-123")
  → [RATE] checking client-123 (rpm=100) → true
encryption.encrypt("auth.example.com:client-123:60m")
  → "[ENC:AES-256-GCM:auth.example.com:client-123:60m]"
  → [AUTH] client-123 → token=[ENC:AES-256-GCM:...]
return token
```

## 7. Gotchas & takeaways

> **A property name that ends with `-ref` is ambiguous.** If your bean has a property literally named `something-ref`, the p-namespace parser will interpret `p:something-ref="beanId"` as a bean reference for property `something`, not as a string value for property `something-ref`. Avoid hyphens at the end of property names.

> **p-namespace cannot inject collections, inner beans, or `<null/>`.** For those, fall back to `<property>` child elements. Mixing both in the same `<bean>` element is allowed and is the common pattern.

- The namespace URI `http://www.springframework.org/schema/p` requires no XSD schema location — it is handled internally by Spring's `DefaultBeanDefinitionDocumentReader`.
- In modern Spring applications using annotation-driven config (`@Configuration`, `@Bean`, component scanning), you would never write p-namespace XML at all — it is only relevant for legacy XML-heavy codebases.
- p-namespace attributes go on the `<bean>` element, NOT on child elements — `<property p:name="val"/>` is not valid.
- IDE support (IntelliJ IDEA, Eclipse STS) auto-completes p-namespace attributes based on the class's setters, so typos are caught early.
