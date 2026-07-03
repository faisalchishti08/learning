---
card: spring-framework
gi: 132
slug: default-profile
title: "Default profile"
---

## 1. What it is

The **default profile** (`"default"`) is the profile that Spring activates automatically when no other profiles are explicitly set as active. Beans annotated `@Profile("default")` are registered only in this implicit fallback state. As soon as you activate any other profile, the `"default"` profile is no longer considered active — it is replaced, not extended.

```java
@Bean @Profile("default") DataSource embeddedDataSource() { ... }
@Bean @Profile("prod")    DataSource postgresDataSource()  { ... }
```

Running without any profile → `embeddedDataSource()` registered. Running with `"prod"` active → `postgresDataSource()` registered, `embeddedDataSource()` skipped.

## 2. Why & when

The default profile solves a specific problem: you want `@Profile`-aware beans to have a sensible out-of-box experience without forcing developers to remember to activate a `"dev"` profile to make the app start.

Use `@Profile("default")` for:
- Embedded/in-memory datasources that work without external services.
- Mock/stub external integrations for local development.
- Convenience defaults a new team member can run immediately after checkout.

Use `setDefaultProfiles("custom")` when you want to rename the implicit fallback from `"default"` to something more expressive like `"local"` or `"embedded"`.

## 3. Core concept

Two aspects of "default profile":

1. **The `"default"` profile name** — literally the string `"default"`. Beans with `@Profile("default")` activate when no profile is explicitly set.

2. **`setDefaultProfiles("name")`** — the configurable default profile name. By default it is `"default"`, but you can change it programmatically to any string. The profile set via `setDefaultProfiles` only takes effect when `getActiveProfiles()` returns an empty array.

```java
// Rename the default profile
ctx.getEnvironment().setDefaultProfiles("local");
// Now @Profile("local") beans activate when nothing is explicitly set
```

The interplay:
```
No active profiles set
  → environment.getDefaultProfiles()   = ["default"]  (or custom default)
  → env.getActiveProfiles()            = []
  → Spring activates the default profile

One active profile set ("prod")
  → env.getActiveProfiles()            = ["prod"]
  → default profile is NOT active
  → @Profile("default") beans skipped
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Left: no active profiles -->
  <rect x="10" y="30" width="175" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="53" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">No active profiles</text>
  <text x="97" y="73" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">getActiveProfiles() = []</text>
  <text x="97" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">default profile = "default"</text>
  <text x="97" y="117" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile("default") ✓</text>
  <text x="97" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile("prod")    ✗</text>
  <text x="97" y="149" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">no @Profile         ✓</text>

  <!-- Right: prod active -->
  <rect x="370" y="30" width="175" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="457" y="53" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Profile "prod" active</text>
  <text x="457" y="73" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">getActiveProfiles() = ["prod"]</text>
  <text x="457" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">default profile ignored</text>
  <text x="457" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile("default") ✗</text>
  <text x="457" y="133" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Profile("prod")    ✓</text>
  <text x="457" y="149" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">no @Profile         ✓</text>

  <line x1="187" y1="95" x2="367" y2="95" stroke="#8b949e" stroke-width="2" stroke-dasharray="6,4"/>
  <text x="277" y="88" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">activate "prod"</text>
  <defs>
    <marker id="a132" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <line x1="187" y1="95" x2="367" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a132)"/>

  <text x="350" y="182" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Activating any profile replaces the default — @Profile("default") beans no longer register</text>
</svg>

The default profile is active only when no other profile is active; activating any profile deactivates it.

## 5. Runnable example

### Level 1 — Basic

Show that `@Profile("default")` beans register when nothing is active and are replaced when another profile is active.

```java
// DefaultProfileBasic.java
import org.springframework.context.annotation.*;
import java.util.Arrays;

interface DataSource { String url(); }
class EmbeddedDs  implements DataSource { public String url() { return "jdbc:h2:mem:test"; } }
class ExternalDs  implements DataSource { public String url() { return "jdbc:postgresql://db/shop"; } }

@Configuration
class DsCfg {
    @Bean @Profile("default") public DataSource embeddedDs() {
        System.out.println("[DS] embedded (default profile)");
        return new EmbeddedDs();
    }

    @Bean @Profile("prod") public DataSource externalDs() {
        System.out.println("[DS] external (prod profile)");
        return new ExternalDs();
    }

    @Bean public String appName() { return "MyApp"; }  // no @Profile — always registered
}

public class DefaultProfileBasic {
    static void run(String label, String... profiles) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        if (profiles.length > 0) ctx.getEnvironment().setActiveProfiles(profiles);
        ctx.register(DsCfg.class);
        ctx.refresh();
        System.out.println("Active profiles:  " + Arrays.toString(ctx.getEnvironment().getActiveProfiles()));
        System.out.println("Default profiles: " + Arrays.toString(ctx.getEnvironment().getDefaultProfiles()));
        System.out.println("DataSource url:   " + ctx.getBean(DataSource.class).url());
        System.out.println("appName present:  " + ctx.containsBean("appName"));
        ctx.close(); System.out.println();
    }

    public static void main(String[] args) {
        run("no profile active");      // default profile fires
        run("prod active", "prod");    // default profile suppressed
    }
}
```

How to run: `java DefaultProfileBasic.java`

No profile active → `embeddedDs()` (`@Profile("default")`) registered. `prod` active → `externalDs()` registered, `embeddedDs()` not registered. `appName` is always present.

### Level 2 — Intermediate

Custom default profile name using `setDefaultProfiles()`.

```java
// DefaultProfileCustom.java
import org.springframework.context.annotation.*;
import java.util.Arrays;

interface CacheService { String get(String k); void put(String k, String v); }

class InMemCache implements CacheService {
    java.util.Map<String,String> store = new java.util.HashMap<>();
    InMemCache() { System.out.println("[Cache] in-memory (local profile)"); }
    public String get(String k)          { return store.get(k); }
    public void put(String k, String v)  { store.put(k, v); }
}

class RedisCache implements CacheService {
    RedisCache() { System.out.println("[Cache] Redis (prod profile)"); }
    public String get(String k)          { return "[redis]" + k; }
    public void put(String k, String v)  { System.out.println("[redis] SET " + k + "=" + v); }
}

class NoOpCache implements CacheService {
    NoOpCache() { System.out.println("[Cache] no-op (ci profile)"); }
    public String get(String k)          { return null; }
    public void put(String k, String v)  {}
}

@Configuration
class CacheCfg {
    @Bean @Profile("local") CacheService inMemCache() { return new InMemCache(); }
    @Bean @Profile("prod")  CacheService redisCache()  { return new RedisCache();  }
    @Bean @Profile("ci")    CacheService noOpCache()   { return new NoOpCache();   }
}

public class DefaultProfileCustom {
    static void run(String label, String defaultProfile, String... activeProfiles) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().setDefaultProfiles(defaultProfile);
        if (activeProfiles.length > 0) ctx.getEnvironment().setActiveProfiles(activeProfiles);
        ctx.register(CacheCfg.class);
        ctx.refresh();
        System.out.println("Default: " + Arrays.toString(ctx.getEnvironment().getDefaultProfiles()));
        System.out.println("Active:  " + Arrays.toString(ctx.getEnvironment().getActiveProfiles()));
        ctx.getBean(CacheService.class).put("key", "value");
        ctx.close(); System.out.println();
    }

    public static void main(String[] args) {
        // "local" is now the default — no explicit activation → local cache
        run("default=local, nothing active", "local");
        // "local" is default, but "prod" overrides it
        run("default=local, prod active", "local", "prod");
        // "ci" explicitly active
        run("ci explicitly", "local", "ci");
    }
}
```

How to run: `java DefaultProfileCustom.java`

`setDefaultProfiles("local")` makes `"local"` the fallback. When nothing is explicitly activated, `InMemCache` (gated on `"local"`) registers. When `"prod"` is activated, `"local"` default is suppressed.

### Level 3 — Advanced

A full service stack with default, override, and environment-variable-style activation — demonstrating the complete priority hierarchy.

```java
// DefaultProfilePriority.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

interface AuthService { String authenticate(String user, String pass); }
class DevAuth  implements AuthService { public String authenticate(String u, String p) { return "[DEV] " + u + " ok"; } }
class ProdAuth implements AuthService { public String authenticate(String u, String p) { return "[PROD] verified " + u; } }
class TestAuth implements AuthService { public String authenticate(String u, String p) { return "[TEST] mock:" + u; } }

interface MessagingService { void send(String topic, String msg); }
class InMemMessaging  implements MessagingService { public void send(String t, String m) { System.out.println("[MEM] " + t + ": " + m); } }
class KafkaMessaging  implements MessagingService { public void send(String t, String m) { System.out.println("[KAFKA] " + t + ": " + m); } }

@Configuration
class ServicesCfg {
    // default = "dev"
    @Bean @Profile("dev")   AuthService devAuth()   { return new DevAuth();  }
    @Bean @Profile("prod")  AuthService prodAuth()  { return new ProdAuth(); }
    @Bean @Profile("test")  AuthService testAuth()  { return new TestAuth(); }

    @Bean @Profile({"dev","test"})    MessagingService inMemMsg()   { return new InMemMessaging(); }
    @Bean @Profile("prod")            MessagingService kafkaMsg()   { return new KafkaMessaging(); }
}

public class DefaultProfilePriority {
    static void run(String label, String defaultProf, String... active) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        ctx.getEnvironment().setDefaultProfiles(defaultProf);
        if (active.length > 0) ctx.getEnvironment().setActiveProfiles(active);
        ctx.register(ServicesCfg.class);
        ctx.refresh();

        System.out.println("Default: " + Arrays.toString(ctx.getEnvironment().getDefaultProfiles()));
        System.out.println("Active:  " + Arrays.toString(ctx.getEnvironment().getActiveProfiles()));

        var auth = ctx.getBean(AuthService.class);
        System.out.println(auth.authenticate("alice", "secret"));
        ctx.getBean(MessagingService.class).send("orders", "order-42");
        ctx.close(); System.out.println();
    }

    public static void main(String[] args) {
        // Developer checkout — no activation needed, dev mode via default
        run("developer mode (default=dev)", "dev");

        // CI environment — override to test
        run("CI (default=dev, active=test)", "dev", "test");

        // Production — override to prod
        run("Production (active=prod)", "dev", "prod");
    }
}
```

How to run: `java DefaultProfilePriority.java`

`setDefaultProfiles("dev")` makes local development work out of the box. CI and production explicitly activate their profiles, which suppress the `"dev"` default.

## 6. Walkthrough

Execution for Level 3 "CI" run:

1. **`setDefaultProfiles("dev")`** — `"dev"` is the fallback if nothing explicit is activated.
2. **`setActiveProfiles("test")`** — explicitly activates `"test"`.
3. **`ctx.refresh()`** — active profiles = `["test"]`. Default profile `"dev"` is NOT active (active set is non-empty).
4. **`ServicesCfg` processed** — `@Profile("dev")` → `false` (not active). `@Profile("prod")` → `false`. `@Profile("test")` → `true` → `testAuth` registered. `@Profile({"dev","test"})` → `true` (test is active) → `inMemMsg` registered.
5. **`authenticate("alice","secret")`** → `[TEST] mock:alice`.
6. **`send("orders","order-42")`** → `[MEM] orders: order-42`.

Expected output:
```
=== CI (default=dev, active=test) ===
Default: [dev]
Active:  [test]
[TEST] mock:alice
[MEM] orders: order-42
```

## 7. Gotchas & takeaways

> `@Profile("default")` (the string literal `"default"`) is active ONLY when nothing else is. The moment you call `setActiveProfiles("anything")`, the default profile deactivates — even if you don't activate a bean that provides the same dependency. This can cause `NoSuchBeanDefinitionException` if you activate a custom profile but forget to provide an alternative for every `@Profile("default")` bean.

> `setDefaultProfiles(...)` changes the name of the fallback profile — it does NOT add to the active set. Calling both `setDefaultProfiles("local")` and `setActiveProfiles("prod")` gives you `active=["prod"]`, `default=["local"]`. The `"local"` name is never used because active profiles suppress the default.

- The built-in default profile name is `"default"`. Spring uses it unless you call `setDefaultProfiles()`.
- An ungated `@Bean` (no `@Profile`) always registers — it's not subject to the default/active interplay.
- In Spring Boot: `spring.profiles.default` property sets the default profile name.
- Common pattern: name all environment-specific beans with their profile name (`@Profile("local")`, `@Profile("ci")`, `@Profile("prod")`) and set `setDefaultProfiles("local")` so `"local"` activates by default for developers.
