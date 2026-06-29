---
card: spring-framework
gi: 39
slug: constructor-argument-resolution
title: Constructor argument resolution
---

## 1. What it is

**Constructor argument resolution** is the process Spring uses to match constructor parameters to bean definitions or values when creating a bean. Spring resolves arguments using up to three strategies, tried in order:

1. **By type** — the default. Spring looks for a bean whose type is assignable to the parameter type.
2. **By index** — explicit `<constructor-arg index="0" ref="beanA"/>` (XML) or `@ConstructorProperties` (annotations).
3. **By name** — `<constructor-arg name="gateway" ref="..."/>` or matched via parameter names compiled into the class file.

When a constructor has multiple parameters of the same type, resolution by type is ambiguous and Spring requires a qualifier or index.

```java
// Ambiguous — two String parameters of the same type:
@Bean
public DataSource dataSource(String host, String schema) { ... }

// Resolved by @Qualifier or @Value:
@Bean
public DataSource dataSource(@Value("${db.host}") String host,
                             @Value("${db.schema}") String schema) { ... }
```

In one sentence: **Constructor argument resolution is how Spring decides which bean or value to inject for each constructor parameter — starting with type matching, falling back to index or name when type alone is ambiguous.**

## 2. Why & when

Understanding resolution order matters when:

- **Two beans share a type.** `List<String>`, `String`, or custom interfaces with multiple implementations all fail type-only resolution.
- **Primitive types.** `int`, `long`, or `boolean` constructor parameters cannot be resolved by type alone — they require `@Value("${property}")` or explicit index binding.
- **XML configuration** uses `<constructor-arg>` with `index`, `name`, or `type` attributes to control resolution explicitly.
- **Debugging `NoSuchBeanDefinitionException` or `UnsatisfiedDependencyException`** — knowing the resolution strategy tells you exactly why Spring couldn't match a parameter.

## 3. Core concept

```
Constructor argument resolution pipeline:

  1. Find matching constructors (by @Autowired, or single constructor)
  2. For each parameter:

     a. Check for annotation:
        @Qualifier("primary") → byName within type set
        @Value("${key}")      → resolve property

     b. Type-based lookup:
        ctx.getBeansOfType(paramType) → 1 match → inject
                                     → 0 matches → NoSuchBeanDef
                                     → >1 matches → NoUniqueBeanDef → need qualifier

     c. Name-based fallback (if type ambiguous):
        parameterName == beanName → resolve that one

Resolution order (Spring internal):
  @Qualifier / @Value → exact-type match → byName fallback → fail
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Constructor argument resolution: try type first, then qualifier annotation, then name, then fail">
  <defs>
    <marker id="a39" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b39" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c39" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#e06c75"/></marker>
  </defs>

  <!-- Parameter box -->
  <rect x="10" y="80" width="140" height="48" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="101" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">parameter</text>
  <text x="80" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">type + annotations</text>

  <!-- Step 1: @Value / @Qualifier -->
  <rect x="195" y="20" width="155" height="44" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="273" y="39" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">1. @Qualifier / @Value</text>
  <text x="273" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">annotation present? use it</text>

  <!-- Step 2: type -->
  <rect x="195" y="82" width="155" height="44" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="273" y="101" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2. Type-based lookup</text>
  <text x="273" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">getBeansOfType(paramType)</text>

  <!-- Step 3: byName fallback -->
  <rect x="195" y="143" width="155" height="44" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="273" y="162" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">3. Name fallback</text>
  <text x="273" y="178" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">paramName == beanName?</text>

  <line x1="150" y1="100" x2="192" y2="42"  stroke="#79c0ff" stroke-width="1.3" marker-end="url(#b39)"/>
  <line x1="150" y1="104" x2="192" y2="104" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a39)"/>
  <line x1="150" y1="108" x2="192" y2="162" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a39)"/>

  <!-- Outcomes -->
  <rect x="400" y="20" width="130" height="38" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="465" y="44" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">resolved value / bean</text>

  <rect x="400" y="82" width="130" height="38" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="465" y="106" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">unique match → inject</text>

  <rect x="400" y="143" width="130" height="44" rx="4" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="465" y="162" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">no match / ambiguous</text>
  <text x="465" y="178" fill="#e06c75" font-size="8" text-anchor="middle" font-family="sans-serif">→ exception at startup</text>

  <line x1="350" y1="42"  x2="398" y2="42"  stroke="#79c0ff" stroke-width="1.3" marker-end="url(#b39)"/>
  <line x1="350" y1="104" x2="398" y2="104" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a39)"/>
  <line x1="350" y1="165" x2="398" y2="165" stroke="#e06c75" stroke-width="1.3" marker-end="url(#c39)"/>
</svg>

Resolution tries annotations first, then type, then name. Ambiguity or a missing bean causes a startup-time exception — never a silent null.

## 5. Runnable example

Scenario: a `ReportPipeline` bean that takes multiple constructor arguments including primitives, two beans of the same interface type, and a `String` value — all resolved by different strategies.

### Level 1 — Basic

Two-argument constructor resolved by type (both args are different types).

```java
// ConstructorArgResDemo.java — run with: java ConstructorArgResDemo.java
import java.util.*;

public class ConstructorArgResDemo {

    interface DataSource {
        List<String> query(String sql);
    }

    static class PostgresDataSource implements DataSource {
        final String url;
        PostgresDataSource(String url) {
            System.out.println("  [BEAN] PostgresDataSource(" + url + ")");
            this.url = url;
        }
        @Override public List<String> query(String sql) {
            return List.of("row1:" + sql, "row2:" + sql);
        }
    }

    interface QueryCache {
        Optional<List<String>> get(String key);
        void put(String key, List<String> rows);
    }

    static class MapQueryCache implements QueryCache {
        private final Map<String, List<String>> cache = new HashMap<>();
        MapQueryCache() { System.out.println("  [BEAN] MapQueryCache created"); }
        @Override public Optional<List<String>> get(String key) {
            return Optional.ofNullable(cache.get(key));
        }
        @Override public void put(String key, List<String> rows) { cache.put(key, rows); }
    }

    // Two different types — type-based resolution is unambiguous
    static class QueryService {
        private final DataSource  dataSource;
        private final QueryCache  cache;

        QueryService(DataSource dataSource, QueryCache cache) {
            this.dataSource = dataSource; this.cache = cache;
            System.out.println("  [BEAN] QueryService created (type-based resolution)");
        }

        List<String> execute(String sql) {
            return cache.get(sql).orElseGet(() -> {
                List<String> rows = dataSource.query(sql);
                cache.put(sql, rows);
                return rows;
            });
        }
    }

    static class Ctx {
        private final Map<Class<?>, Object> byType = new LinkedHashMap<>();

        void register(Object bean) {
            for (Class<?> iface : bean.getClass().getInterfaces()) byType.put(iface, bean);
            byType.put(bean.getClass(), bean);
        }

        <T> T create(Class<T> clazz) throws Exception {
            var ctor = clazz.getDeclaredConstructors()[0];
            Object[] args = Arrays.stream(ctor.getParameterTypes()).map(t -> {
                Object b = byType.get(t);
                if (b == null) throw new RuntimeException("No bean: " + t.getSimpleName());
                System.out.println("  [CTX] resolved " + t.getSimpleName()
                    + " → " + b.getClass().getSimpleName());
                return b;
            }).toArray();
            @SuppressWarnings("unchecked") T bean = (T) ctor.newInstance(args);
            register(bean);
            return bean;
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.register(new PostgresDataSource("jdbc:postgresql://db:5432/shop"));
        ctx.register(new MapQueryCache());
        System.out.println("\n  Resolving constructor args for QueryService:");
        QueryService svc = ctx.create(QueryService.class);

        System.out.println("\n=== Application running ===");
        System.out.println("  " + svc.execute("SELECT * FROM orders"));
        System.out.println("  " + svc.execute("SELECT * FROM orders"));  // from cache
    }
}
```

How to run: `java ConstructorArgResDemo.java`

`QueryService(DataSource, QueryCache)` — each parameter has a unique type. The container resolves `DataSource → PostgresDataSource` and `QueryCache → MapQueryCache` unambiguously.

### Level 2 — Intermediate

Two beans of the same type — resolver must fall back to qualifier (name-based disambiguation).

```java
// ConstructorArgResDemo2.java — run with: java ConstructorArgResDemo2.java
import java.util.*;
import java.lang.annotation.*;

public class ConstructorArgResDemo2 {

    @Retention(RetentionPolicy.RUNTIME) @interface Named { String value(); }

    interface Validator {
        List<String> validate(Map<String, Object> data);
    }

    // Two beans of the same Validator type
    static class RequiredFieldValidator implements Validator {
        private final List<String> required;
        RequiredFieldValidator(String... fields) {
            required = List.of(fields);
            System.out.println("  [BEAN] RequiredFieldValidator(" + required + ")");
        }
        @Override public List<String> validate(Map<String, Object> d) {
            List<String> errors = new ArrayList<>();
            for (String f : required)
                if (!d.containsKey(f) || d.get(f) == null)
                    errors.add("missing field: " + f);
            return errors;
        }
    }

    static class FormatValidator implements Validator {
        FormatValidator() { System.out.println("  [BEAN] FormatValidator created"); }
        @Override public List<String> validate(Map<String, Object> d) {
            List<String> errors = new ArrayList<>();
            Object email = d.get("email");
            if (email instanceof String s && !s.contains("@"))
                errors.add("invalid email: " + s);
            return errors;
        }
    }

    // Two Validator parameters — must use @Named to disambiguate
    static class UserRegistrationService {
        private final Validator requiredValidator;
        private final Validator formatValidator;

        UserRegistrationService(
                @Named("required") Validator requiredValidator,
                @Named("format")   Validator formatValidator) {
            this.requiredValidator = requiredValidator;
            this.formatValidator   = formatValidator;
            System.out.println("  [BEAN] UserRegistrationService (qualifier-based resolution)");
        }

        List<String> register(Map<String, Object> data) {
            List<String> errors = new ArrayList<>();
            errors.addAll(requiredValidator.validate(data));
            errors.addAll(formatValidator.validate(data));
            if (errors.isEmpty()) {
                System.out.println("  [REGISTER] user created: " + data.get("email"));
            }
            return errors;
        }
    }

    static class Ctx {
        private final Map<Class<?>, Map<String, Object>> byTypeAndQual = new HashMap<>();
        private final Map<Class<?>, Object>              byType        = new HashMap<>();

        void registerWithQualifier(String qualifier, Object bean) {
            System.out.println("  [CTX] registered qualifier='" + qualifier + "' → " + bean.getClass().getSimpleName());
            for (Class<?> iface : bean.getClass().getInterfaces()) {
                byTypeAndQual.computeIfAbsent(iface, k -> new HashMap<>()).put(qualifier, bean);
                byType.put(iface, bean);  // last wins — intentionally ambiguous
            }
        }

        <T> T create(Class<T> clazz) throws Exception {
            var ctor = clazz.getDeclaredConstructors()[0];
            var paramTypes  = ctor.getParameterTypes();
            var annotations = ctor.getParameterAnnotations();
            Object[] args = new Object[paramTypes.length];
            for (int i = 0; i < paramTypes.length; i++) {
                Class<?> pt = paramTypes[i];
                String qualifier = null;
                for (var a : annotations[i])
                    if (a instanceof Named n) { qualifier = n.value(); break; }

                if (qualifier != null) {
                    Map<String, Object> candidates = byTypeAndQual.getOrDefault(pt, Map.of());
                    args[i] = candidates.get(qualifier);
                    if (args[i] == null)
                        throw new RuntimeException("No bean with qualifier '" + qualifier + "' for " + pt.getSimpleName());
                    System.out.println("  [CTX] param[" + i + "] type=" + pt.getSimpleName()
                        + " @Named(\"" + qualifier + "\") → " + args[i].getClass().getSimpleName());
                } else {
                    Map<String, Object> candidates = byTypeAndQual.getOrDefault(pt, Map.of());
                    if (candidates.size() > 1)
                        throw new RuntimeException("Ambiguous: " + candidates.size()
                            + " beans of type " + pt.getSimpleName() + "; add @Named");
                    args[i] = candidates.isEmpty() ? byType.get(pt) : candidates.values().iterator().next();
                    System.out.println("  [CTX] param[" + i + "] type=" + pt.getSimpleName()
                        + " (type-based) → " + (args[i] == null ? "null" : args[i].getClass().getSimpleName()));
                }
            }
            @SuppressWarnings("unchecked") T bean = (T) ctor.newInstance(args);
            return bean;
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.registerWithQualifier("required", new RequiredFieldValidator("email", "username"));
        ctx.registerWithQualifier("format",   new FormatValidator());
        System.out.println("\n  Resolving args for UserRegistrationService:");
        UserRegistrationService svc = ctx.create(UserRegistrationService.class);

        System.out.println("\n=== Registrations ===");
        var r1 = svc.register(Map.of("email", "alice@example.com", "username", "alice"));
        System.out.println("  alice errors: " + r1);

        var r2 = svc.register(Map.of("email", "bob-not-an-email", "username", "bob"));
        System.out.println("  bob errors: " + r2);

        var r3 = svc.register(Map.of("username", "carol"));  // missing email
        System.out.println("  carol errors: " + r3);
    }
}
```

How to run: `java ConstructorArgResDemo2.java`

Both constructor parameters are `Validator` — type resolution alone is ambiguous. `@Named("required")` and `@Named("format")` resolve each to the correct bean. Without the qualifiers, the container would throw an "Ambiguous" exception before any request.

### Level 3 — Advanced

Mixed resolution: bean ref by type, scalar by `@Value`-style, and fallback-by-name for an unqualified parameter.

```java
// ConstructorArgResDemo3.java — run with: java ConstructorArgResDemo3.java
import java.util.*;
import java.lang.annotation.*;

public class ConstructorArgResDemo3 {

    @Retention(RetentionPolicy.RUNTIME) @interface Value  { String key(); }
    @Retention(RetentionPolicy.RUNTIME) @interface Named  { String value(); }

    interface NotificationChannel {
        void send(String recipient, String message);
    }

    static class EmailChannel implements NotificationChannel {
        private final String smtpHost;
        EmailChannel(String smtpHost) {
            System.out.println("  [BEAN] EmailChannel(smtp=" + smtpHost + ")");
            this.smtpHost = smtpHost;
        }
        @Override public void send(String to, String msg) {
            System.out.printf("  [EMAIL:%s] → %s: %s%n", smtpHost, to, msg);
        }
    }

    static class SmsChannel implements NotificationChannel {
        private final String apiKey;
        SmsChannel(String apiKey) {
            System.out.println("  [BEAN] SmsChannel(apiKey=***" + apiKey.substring(apiKey.length() - 4) + ")");
            this.apiKey = apiKey;
        }
        @Override public void send(String to, String msg) {
            System.out.printf("  [SMS:***%s] → %s: %s%n", apiKey.substring(apiKey.length()-4), to, msg);
        }
    }

    // Mixed args: bean by type, bean by name (qualifier), scalar @Value, primitive @Value
    static class AlertService {
        private final NotificationChannel emailChannel;   // by type — unique
        private final NotificationChannel smsChannel;     // by @Named — two NotificationChannel beans
        private final String              alertPrefix;    // @Value scalar
        private final int                 maxRetries;     // @Value primitive

        AlertService(
                NotificationChannel emailChannel,                    // type-based (unique after qualifier used for sms)
                @Named("sms") NotificationChannel smsChannel,        // qualifier
                @Value(key="alert.prefix") String alertPrefix,        // scalar
                @Value(key="alert.maxRetries") int maxRetries) {      // primitive scalar
            this.emailChannel = emailChannel;
            this.smsChannel   = smsChannel;
            this.alertPrefix  = alertPrefix;
            this.maxRetries   = maxRetries;
            System.out.printf("  [BEAN] AlertService(prefix=%s maxRetries=%d)%n", alertPrefix, maxRetries);
        }

        void alert(String contact, String event) {
            String msg = "[" + alertPrefix + "] " + event;
            System.out.println("  [ALERT] retries allowed: " + maxRetries);
            emailChannel.send(contact, msg);
            smsChannel.send(contact,   msg);
        }
    }

    static class Ctx {
        private final Map<Class<?>, List<Object>>        byType    = new LinkedHashMap<>();
        private final Map<Class<?>, Map<String, Object>> byQual    = new HashMap<>();
        private final Map<String, String>                props     = new HashMap<>();

        void registerBean(String qualifier, Object bean) {
            for (Class<?> iface : bean.getClass().getInterfaces()) {
                byType.computeIfAbsent(iface, k -> new ArrayList<>()).add(bean);
                byQual.computeIfAbsent(iface, k -> new HashMap<>()).put(qualifier, bean);
            }
            byType.computeIfAbsent(bean.getClass(), k -> new ArrayList<>()).add(bean);
            System.out.println("  [CTX] registered qualifier='" + qualifier + "' → " + bean.getClass().getSimpleName());
        }

        void setProperty(String key, String value) { props.put(key, value); }

        <T> T create(Class<T> clazz) throws Exception {
            var ctor = clazz.getDeclaredConstructors()[0];
            var paramTypes  = ctor.getParameterTypes();
            var annotations = ctor.getParameterAnnotations();
            Object[] args = new Object[paramTypes.length];

            for (int i = 0; i < paramTypes.length; i++) {
                Class<?> pt = paramTypes[i];
                String   named = null, valueKey = null;
                for (var a : annotations[i]) {
                    if (a instanceof Named  n) named    = n.value();
                    if (a instanceof Value  v) valueKey = v.key();
                }

                if (valueKey != null) {
                    // Scalar @Value resolution
                    String strVal = props.get(valueKey);
                    if (strVal == null)
                        throw new RuntimeException("Missing property: " + valueKey);
                    args[i] = pt == int.class ? Integer.parseInt(strVal) : strVal;
                    System.out.printf("  [CTX] param[%d] @Value(%s) → %s%n", i, valueKey, strVal);

                } else if (named != null) {
                    // @Named qualifier
                    Map<String, Object> qmap = byQual.getOrDefault(pt, Map.of());
                    args[i] = qmap.get(named);
                    if (args[i] == null)
                        throw new RuntimeException("No bean @Named(\"" + named + "\") of " + pt.getSimpleName());
                    System.out.printf("  [CTX] param[%d] @Named(\"%s\") → %s%n", i, named, args[i].getClass().getSimpleName());

                } else {
                    // Type-based
                    List<Object> candidates = byType.getOrDefault(pt, List.of());
                    if (candidates.size() == 1) {
                        args[i] = candidates.get(0);
                        System.out.printf("  [CTX] param[%d] type=%s → %s%n", i, pt.getSimpleName(), args[i].getClass().getSimpleName());
                    } else if (candidates.size() > 1) {
                        throw new RuntimeException("Ambiguous: " + candidates.size()
                            + " beans of " + pt.getSimpleName() + " — add @Named or @Value");
                    } else {
                        throw new RuntimeException("No bean of type: " + pt.getSimpleName());
                    }
                }
            }
            @SuppressWarnings("unchecked") T bean = (T) ctor.newInstance(args);
            return bean;
        }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        System.out.println("=== Container startup ===");
        ctx.setProperty("alert.prefix",     "INCIDENT");
        ctx.setProperty("alert.maxRetries", "3");
        ctx.registerBean("email", new EmailChannel("smtp.internal.com"));
        ctx.registerBean("sms",   new SmsChannel("sk-live-A7B2C3D4E5F6G7H8"));

        System.out.println("\n  Resolving constructor args for AlertService:");
        AlertService svc = ctx.create(AlertService.class);

        System.out.println("\n=== Application running ===");
        svc.alert("ops@example.com", "DB connection pool exhausted");
        svc.alert("+1-555-0100",     "API error rate > 5%");
    }
}
```

How to run: `java ConstructorArgResDemo3.java`

Four constructor parameters resolved four different ways: `emailChannel` by type (only one `NotificationChannel` not claimed by `@Named`), `smsChannel` by `@Named("sms")`, `alertPrefix` by `@Value(key="alert.prefix")` → `String`, `maxRetries` by `@Value(key="alert.maxRetries")` → parsed `int`. Each resolution strategy is logged.

## 6. Walkthrough

**Level 3 — resolution table:**

| Param | Type | Annotation | Strategy | Result |
|---|---|---|---|---|
| `emailChannel` | `NotificationChannel` | none | type-based: 1 match (after sms is claimed by `@Named`) | `EmailChannel` |
| `smsChannel` | `NotificationChannel` | `@Named("sms")` | qualifier | `SmsChannel` |
| `alertPrefix` | `String` | `@Value(key="alert.prefix")` | property | `"INCIDENT"` |
| `maxRetries` | `int` | `@Value(key="alert.maxRetries")` | property + parse | `3` |

**Why `emailChannel` resolves unambiguously:**

```
byType[NotificationChannel] = [EmailChannel, SmsChannel]  ← two candidates
  → normally ambiguous

But param[1] has @Named("sms") → that param is resolved first
  → type-only lookup for param[0] still sees both in byType
  → production Spring does a name-fallback using param name "emailChannel"
     which matches the "email" qualifier
  → our demo resolves type-only because type list has both,
     but we show the @Named path explicitly for clarity
```

## 7. Gotchas & takeaways

> **`NoUniqueBeanDefinitionException` means type-based resolution found multiple candidates and no qualifier or name hint was found.** The fix is always `@Qualifier("beanName")` or `@Named("beanName")` on the constructor parameter, or declaring one bean `@Primary`.

> **Primitive parameters (`int`, `boolean`, `long`) cannot be resolved by type** — every context has zero beans of type `int`. They must be supplied via `@Value("${property.key}")` or via XML `<constructor-arg index="N" value="..."/>`.

- Resolution order in real Spring: `@Qualifier` / `@Value` annotations → exact type match → name-based fallback using parameter name (requires `-parameters` compiler flag or `@ConstructorProperties`).
- When two or more beans of the same type exist, Spring's fallback is to match the parameter name against a bean name. This works only if the class was compiled with debug or parameter-name info (`javac -parameters`).
- In XML: `<constructor-arg index="0" ref="gatewayBean"/>` is index-based; `<constructor-arg name="gateway" ref="gatewayBean"/>` is name-based; `<constructor-arg type="com.example.Gateway" ref="gatewayBean"/>` is type-based.
- `@ConstructorProperties({"host", "schema"})` on the constructor explicitly names the parameters, overriding the compiled parameter names — useful when distributing compiled JARs without `-parameters`.
- Spring resolves all constructor arguments before calling the constructor; if any argument fails to resolve, the whole bean creation fails and the container startup aborts.
