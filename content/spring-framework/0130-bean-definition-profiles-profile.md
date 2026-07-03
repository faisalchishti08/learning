---
card: spring-framework
gi: 130
slug: bean-definition-profiles-profile
title: "Bean definition profiles (@Profile)"
---

## 1. What it is

`@Profile` gates a bean (or an entire `@Configuration` class) so that it is only registered when one or more specific profiles are active. Beans outside any `@Profile` are always registered. Beans with `@Profile("prod")` only exist when `"prod"` is in the active profile set.

```java
@Bean @Profile("dev")  DataSource h2DataSource()       { ... }
@Bean @Profile("prod") DataSource postgresDataSource()  { ... }
```

Only one of these registers depending on which profile is active — they can share the same bean name without conflict.

## 2. Why & when

- **Environment-specific beans** — different datasources, caches, or service endpoints per environment.
- **Mock vs real services** — `@Profile("test")` provides in-memory fakes; `@Profile("prod")` provides the real implementations.
- **Feature branches** — `@Profile("feature-x")` activates experimental code in a subset of environments.
- **Multi-tenant configs** — different tenants get different infrastructure beans via profiles.

`@Profile` is itself `@Conditional(ProfileCondition.class)` — understanding `@Conditional` (tutorial 122) fully explains the mechanism.

## 3. Core concept

`@Profile` accepts:

| Expression | Matches |
|---|---|
| `"prod"` | exactly when `"prod"` is active |
| `{"prod","eu"}` | when ANY of the listed profiles is active (OR) |
| `"!prod"` | when `"prod"` is NOT active |
| `"prod & eu"` | when BOTH `"prod"` AND `"eu"` are active (AND) |
| `"prod \| staging"` | when either `"prod"` OR `"staging"` is active |

Profile activation:
- JVM property: `-Dspring.profiles.active=prod,eu`
- Programmatic: `ctx.getEnvironment().setActiveProfiles("prod")` before `ctx.refresh()`.
- `application.properties`: `spring.profiles.active=prod` (Spring Boot).
- Test annotation: `@ActiveProfiles("test")`.

`@Profile` can be placed on:
- A `@Bean` method — individual method gating.
- A `@Configuration` class — gates ALL `@Bean` methods inside it.
- A `@Component` class — gates component scanning.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Profile set -->
  <rect x="10" y="55" width="155" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="87" y="78" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Active profiles</text>
  <text x="87" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">["prod", "eu"]</text>
  <text x="87" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">set before refresh()</text>
  <text x="87" y="135" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">or via -D flag</text>

  <!-- @Profile gates -->
  <rect x="250" y="30" width="200" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="55" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@Profile("prod") → ✓ registered</text>

  <rect x="250" y="85" width="200" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="110" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Profile("dev") → ✗ skipped</text>

  <rect x="250" y="140" width="200" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="165" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">no @Profile → ✓ always</text>

  <!-- Lines -->
  <line x1="167" y1="100" x2="247" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a130)"/>
  <line x1="167" y1="100" x2="247" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#b130)"/>
  <line x1="167" y1="100" x2="247" y2="160" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#c130)"/>
  <defs>
    <marker id="a130" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b130" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="c130" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <text x="350" y="187" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Active profile set evaluated against each @Profile expression at startup</text>
</svg>

Beans with matching `@Profile` expressions are registered; non-matching beans are silently skipped.

## 5. Runnable example

### Level 1 — Basic

`@Profile` on individual `@Bean` methods — same interface, different implementations per profile.

```java
// ProfileBasic.java
import org.springframework.context.annotation.*;

interface DataStore {
    String save(String item);
    String find(int id);
}

class InMemoryDataStore implements DataStore {
    private final java.util.Map<Integer, String> store = new java.util.HashMap<>();
    private int seq = 0;
    InMemoryDataStore() { System.out.println("[DataStore] in-memory (dev)"); }
    public String save(String item) { store.put(++seq, item); return "saved as #" + seq; }
    public String find(int id) { return store.getOrDefault(id, "not found"); }
}

class PostgresDataStore implements DataStore {
    PostgresDataStore() { System.out.println("[DataStore] PostgreSQL (prod)"); }
    public String save(String item) { return "[pg] inserted: " + item; }
    public String find(int id) { return "[pg] SELECT ... id=" + id; }
}

@Configuration
class StoreCfg {
    @Bean @Profile("dev")   public DataStore devStore()  { return new InMemoryDataStore(); }
    @Bean @Profile("prod")  public DataStore prodStore() { return new PostgresDataStore(); }
}

public class ProfileBasic {
    static void run(String profile) {
        System.out.println("=== Profile: " + profile + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().setActiveProfiles(profile);
        ctx.register(StoreCfg.class);
        ctx.refresh();
        var store = ctx.getBean(DataStore.class);
        System.out.println(store.save("Widget"));
        System.out.println(store.find(1));
        ctx.close();
        System.out.println();
    }

    public static void main(String[] args) {
        run("dev");
        run("prod");
    }
}
```

How to run: `java ProfileBasic.java`

With `"dev"` active: only `devStore()` registered → `InMemoryDataStore`. With `"prod"` active: only `prodStore()` registered → `PostgresDataStore`. Both implement `DataStore` so the calling code is unchanged.

### Level 2 — Intermediate

`@Profile` on `@Configuration` classes and using compound profile expressions (`!`, `&`, `|`).

```java
// ProfileClasses.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

interface CacheProvider { String get(String key); void put(String key, String val); }

class LocalCache implements CacheProvider {
    java.util.Map<String,String> map = new java.util.HashMap<>();
    LocalCache() { System.out.println("[Cache] local (dev)"); }
    public String get(String k) { return map.get(k); }
    public void put(String k, String v) { map.put(k, v); }
}

class RedisCache implements CacheProvider {
    RedisCache() { System.out.println("[Cache] Redis (prod)"); }
    public String get(String k) { return "[redis] " + k; }
    public void put(String k, String v) { System.out.println("[redis] SET " + k + "=" + v); }
}

class NoOpCache implements CacheProvider {
    NoOpCache() { System.out.println("[Cache] no-op (test)"); }
    public String get(String k) { return null; }
    public void put(String k, String v) {}
}

// Active for dev and staging (OR expression)
@Configuration @Profile({"dev","staging"})
class DevStagingConfig {
    @Bean public CacheProvider cacheProvider() { return new LocalCache(); }
}

// Active for prod only
@Configuration @Profile("prod")
class ProdConfig {
    @Bean public CacheProvider cacheProvider() { return new RedisCache(); }
}

// Active when "test" profile is active AND "prod" is NOT
@Configuration @Profile("test & !prod")
class TestConfig {
    @Bean public CacheProvider cacheProvider() { return new NoOpCache(); }
}

// Always active — uses whichever CacheProvider was registered
class AppService {
    @Autowired CacheProvider cache;
    public void run(String key, String value) {
        cache.put(key, value);
        System.out.println("get(" + key + "): " + cache.get(key));
    }
}

@Configuration @ComponentScan(basePackageClasses = ProfileClasses.class)
class AppCfg {}

public class ProfileClasses {
    static void run(String label, String... profiles) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().setActiveProfiles(profiles);
        ctx.register(AppCfg.class, DevStagingConfig.class, ProdConfig.class, TestConfig.class);
        ctx.refresh();
        ctx.getBean(AppService.class).run("color", "green");
        ctx.close();
        System.out.println();
    }

    public static void main(String[] args) {
        run("dev mode", "dev");
        run("prod mode", "prod");
        run("test mode", "test");
        run("staging mode", "staging");
    }
}
```

How to run: `java ProfileClasses.java`

`@Profile({"dev","staging"})` is an OR — `LocalCache` activates for both. `@Profile("test & !prod")` uses the AND-NOT expression — `NoOpCache` only when both conditions hold.

### Level 3 — Advanced

Profile-specific `@Configuration` classes that compose together — a production deployment that activates `"prod"` and `"eu"` simultaneously, routing to a region-specific service.

```java
// ProfileComposed.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

interface RegionService { String endpoint(); }
class UsService  implements RegionService { public String endpoint() { return "us.api.acme.com";  } }
class EuService  implements RegionService { public String endpoint() { return "eu.api.acme.com";  } }
class ApacService implements RegionService { public String endpoint() { return "apac.api.acme.com";} }

interface AuthProvider { String token(); }
class ProdAuth implements AuthProvider {
    ProdAuth() { System.out.println("[Auth] prod JWT provider"); }
    public String token() { return "jwt-prod-secret"; }
}
class MockAuth implements AuthProvider {
    MockAuth() { System.out.println("[Auth] mock provider"); }
    public String token() { return "mock-token"; }
}

// Region configs
@Configuration @Profile("us   ") class UsRegionCfg   { @Bean RegionService regionService() { return new UsService();   } }
@Configuration @Profile(" eu  ") class EuRegionCfg   { @Bean RegionService regionService() { return new EuService();   } }
@Configuration @Profile("apac") class ApacRegionCfg  { @Bean RegionService regionService() { return new ApacService(); } }

// Auth configs
@Configuration @Profile("prod") class ProdAuthCfg { @Bean AuthProvider authProvider() { return new ProdAuth(); } }
@Configuration @Profile("!prod") class DevAuthCfg  { @Bean AuthProvider authProvider() { return new MockAuth(); } }

class ApiGateway {
    @Autowired RegionService region;
    @Autowired AuthProvider  auth;
    public void call(String path) {
        System.out.println("https://" + region.endpoint() + path + " [token=" + auth.token() + "]");
    }
}

@Configuration
@Import({UsRegionCfg.class, EuRegionCfg.class, ApacRegionCfg.class,
         ProdAuthCfg.class, DevAuthCfg.class})
@ComponentScan(basePackageClasses = ProfileComposed.class)
class GatewayCfg {}

public class ProfileComposed {
    static void run(String label, String... profiles) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().setActiveProfiles(profiles);
        ctx.register(GatewayCfg.class);
        ctx.refresh();
        ctx.getBean(ApiGateway.class).call("/orders/42");
        ctx.close(); System.out.println();
    }

    public static void main(String[] args) {
        run("dev+eu",       "eu");
        run("prod+us",      "prod", "us");
        run("prod+apac",    "prod", "apac");
    }
}
```

How to run: `java ProfileComposed.java`

Multiple profiles compose orthogonally: `"eu"` selects the EU region endpoint; `"prod"` selects the production auth provider. Mixing `"prod"` + `"eu"` activates the EU endpoint with production authentication.

## 6. Walkthrough

Execution for Level 3 `"prod+eu"` run (not shown but analogous to `"prod+us"`):

1. **Active profiles: `["prod","eu"]`** — set before refresh.
2. **`EuRegionCfg` processed** — `@Profile("eu")` matches → `regionService()` → `EuService`. (US and APAC configs skipped.)
3. **`ProdAuthCfg` processed** — `@Profile("prod")` matches → `authProvider()` → `ProdAuth`. (`DevAuthCfg` skipped — `!prod` false.)
4. **`ApiGateway` component-scanned and injected** — `region = EuService`, `auth = ProdAuth`.
5. **`call("/orders/42")`** → `https://eu.api.acme.com/orders/42 [token=jwt-prod-secret]`.

## 7. Gotchas & takeaways

> Two `@Profile` beans with the same name in the same context will conflict if both profiles are active simultaneously. Always ensure profile expressions are mutually exclusive for the same bean name — or use different names and let `@Primary` disambiguate.

> `@Profile` on a `@Configuration` class gates the **entire** class — if the class has 10 `@Bean` methods, all 10 are skipped when the profile doesn't match. If you need per-method gating within one config class, use `@Profile` directly on individual `@Bean` methods.

- Profiles are case-sensitive: `"Prod"` and `"prod"` are different profiles.
- Multiple active profiles set via `-Dspring.profiles.active=prod,eu` (comma-separated list).
- `@Profile("!prod")` is `@Conditional(ProfileCondition.class)` with negation — equivalent to `@Conditional` checking `!env.acceptsProfiles("prod")`.
- In Spring Boot, `spring.profiles.active=prod` in `application.properties` or `SPRING_PROFILES_ACTIVE=prod` as an environment variable activate profiles without code changes.
