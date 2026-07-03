---
card: spring-framework
gi: 116
slug: bean-naming-aliasing-in-bean
title: "Bean naming & aliasing in @Bean"
---

## 1. What it is

Every Spring bean has a **primary name** and zero or more **aliases**. For `@Bean` methods the default primary name is the method name. The `name` attribute on `@Bean` lets you replace that name and provide additional aliases in a single step: `@Bean(name = {"primary", "alias1", "alias2"})`.

Aliases allow the same singleton to be looked up by multiple identifiers, which is critical when integrating Spring with legacy code that references beans by fixed string names.

## 2. Why & when

Situations where explicit naming and aliasing matter:

- **API contracts** — a library documents a bean by a specific string name (`"dataSource"`); your method must produce that exact name.
- **Migration** — renaming a `@Component` class changes its default bean name and can break injection sites that rely on `@Qualifier("oldName")`. Adding an alias preserves both.
- **Integration** — JNDI, JMX, or external configuration systems reference beans by fixed names.
- **Multiple lookup paths** — a `PasswordEncoder` bean registered as `"bcrypt"` and `"passwordEncoder"` can be looked up either way without duplicating the object.

## 3. Core concept

`@Bean` name options:

| Syntax | Effect |
|---|---|
| `@Bean` | Primary name = method name |
| `@Bean("customName")` | Primary name = `"customName"`, method name ignored |
| `@Bean(name = "customName")` | Same as above |
| `@Bean(name = {"n1", "n2", "n3"})` | Primary = `"n1"`, aliases `"n2"` and `"n3"` |

All aliases refer to the **same singleton instance** — retrieving by any name gives the exact same object. Aliases are registered in the `BeanDefinitionRegistry` via `registerAlias(name, alias)`.

Programmatic aliasing is also possible:
```java
ctx.getBeanFactory().registerAlias("existingBeanName", "additionalAlias");
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- @Bean method -->
  <rect x="10" y="65" width="195" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="107" y="87" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Bean({"bcrypt","encoder"})</text>
  <text x="107" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">PasswordEncoder passwordEncoder()</text>
  <text x="107" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">return new BCryptPasswordEncoder()</text>

  <!-- Arrow -->
  <line x1="207" y1="95" x2="290" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a116)"/>
  <defs>
    <marker id="a116" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b116" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Registry -->
  <rect x="292" y="50" width="175" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="379" y="73" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Registry</text>
  <text x="379" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">"bcrypt" → BCryptPE (primary)</text>
  <text x="379" y="108" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"encoder" → alias → same obj</text>
  <text x="379" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"passwordEncoder" → NOT registered</text>

  <!-- Arrow -->
  <line x1="469" y1="95" x2="555" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#b116)"/>

  <!-- Lookup -->
  <rect x="557" y="65" width="135" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="624" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">getBean("bcrypt")</text>
  <text x="624" y="107" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">getBean("encoder")</text>
  <text x="624" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">→ same instance</text>

  <text x="350" y="170" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">First name in array is primary; rest are aliases pointing to same singleton</text>
</svg>

All names and aliases point to the same singleton; the first name in the array is the primary.

## 5. Runnable example

### Level 1 — Basic

A notification service registered under multiple names — show all names resolve to the same object.

```java
// BeanNamingBasic.java
import org.springframework.context.annotation.*;

class AlertService {
    private static int instanceCount = 0;
    private final int id;

    AlertService() { this.id = ++instanceCount; }
    public String whoAmI() { return "AlertService#" + id; }
}

@Configuration
class NamingCfg {
    // Primary name = "alerts"; aliases: "alertService", "notifier"
    @Bean(name = {"alerts", "alertService", "notifier"})
    public AlertService alertService() {
        return new AlertService();
    }
}

public class BeanNamingBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(NamingCfg.class);

        var a1 = (AlertService) ctx.getBean("alerts");
        var a2 = (AlertService) ctx.getBean("alertService");
        var a3 = (AlertService) ctx.getBean("notifier");
        var a4 = ctx.getBean(AlertService.class);

        System.out.println(a1.whoAmI());
        System.out.println("All same? " + (a1 == a2 && a2 == a3 && a3 == a4));

        // Default method name "alertService" — is it still registered?
        // Yes — it's in the aliases list above
        System.out.println("aliases: " + java.util.Arrays.toString(ctx.getAliases("alerts")));
        ctx.close();
    }
}
```

How to run: `java BeanNamingBasic.java`

All four lookups return the same `AlertService#1` instance. `ctx.getAliases("alerts")` lists the registered aliases.

### Level 2 — Intermediate

Renaming a bean while preserving the old name as an alias for backward compatibility.

```java
// BeanNamingMigration.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

// Scenario: we renamed "userRepository" to "userStore" but legacy code
// still injects by the old qualifier name.

interface UserStore { String find(int id); }

class InMemoryUserStore implements UserStore {
    public String find(int id) { return "User#" + id; }
}

// Legacy service that references the OLD bean name via @Qualifier
class LegacyReportService {
    @Autowired
    @Qualifier("userRepository")     // OLD name — still works via alias
    private UserStore store;

    public String report(int id) { return "[LEGACY] " + store.find(id); }
}

// New service using the new name
class NewReportService {
    @Autowired
    @Qualifier("userStore")          // NEW name
    private UserStore store;

    public String report(int id) { return "[NEW] " + store.find(id); }
}

@Configuration
@ComponentScan(basePackageClasses = BeanNamingMigration.class)
class MigrationCfg {
    // Primary name = "userStore"; "userRepository" kept as alias for legacy code
    @Bean(name = {"userStore", "userRepository"})
    public UserStore userStore() {
        return new InMemoryUserStore();
    }
}

public class BeanNamingMigration {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MigrationCfg.class);

        System.out.println(ctx.getBean(LegacyReportService.class).report(1));
        System.out.println(ctx.getBean(NewReportService.class).report(2));

        // Confirm they got the same singleton
        var fromOld = (UserStore) ctx.getBean("userRepository");
        var fromNew = (UserStore) ctx.getBean("userStore");
        System.out.println("Same bean? " + (fromOld == fromNew));
        ctx.close();
    }
}
```

How to run: `java BeanNamingMigration.java`

`LegacyReportService` uses `@Qualifier("userRepository")` — the old name. `NewReportService` uses `@Qualifier("userStore")` — the new name. Both resolve to the same `InMemoryUserStore` singleton.

### Level 3 — Advanced

Programmatic alias registration plus showing how aliases interact with `@Primary` and `getAliases`.

```java
// BeanNamingAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;

interface Cache { String get(String key); void put(String key, String val); }

class LocalCache implements Cache {
    private final java.util.Map<String,String> map = new java.util.HashMap<>();
    public String get(String key) { return map.getOrDefault(key, null); }
    public void put(String key, String val) { map.put(key, val); }
    public String toString() { return "LocalCache@" + System.identityHashCode(this); }
}

class RemoteCache implements Cache {
    public String get(String key) { return "[remote:" + key + "]"; }
    public void put(String key, String val) { System.out.println("[remote] stored " + key); }
    public String toString() { return "RemoteCache@" + System.identityHashCode(this); }
}

@Configuration
class CacheCfg {
    @Bean({"localCache", "l1Cache", "nearCache"})
    @Primary
    public Cache localCache() { return new LocalCache(); }

    @Bean("remoteCache")
    public Cache remoteCache() { return new RemoteCache(); }
}

public class BeanNamingAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CacheCfg.class);

        // List all names for the local cache
        System.out.println("Primary name: localCache");
        System.out.println("Aliases: " + java.util.Arrays.toString(ctx.getAliases("localCache")));

        // All aliases refer to same singleton
        var c1 = (Cache) ctx.getBean("localCache");
        var c2 = (Cache) ctx.getBean("l1Cache");
        var c3 = (Cache) ctx.getBean("nearCache");
        System.out.println("l1Cache == nearCache? " + (c1 == c2 && c2 == c3));

        // Programmatic alias registration (post-context)
        var factory = (DefaultListableBeanFactory) ctx.getBeanFactory();
        factory.registerAlias("remoteCache", "l2Cache");
        System.out.println("l2Cache added: " + ctx.containsBean("l2Cache"));
        System.out.println("l2Cache == remoteCache? " + (ctx.getBean("l2Cache") == ctx.getBean("remoteCache")));

        // @Primary: unqualified injection resolves to localCache
        c1.put("user:1", "Alice");
        System.out.println("Get from primary: " + ctx.getBean(Cache.class).get("user:1"));

        ctx.close();
    }
}
```

How to run: `java BeanNamingAdvanced.java`

`ctx.getAliases("localCache")` returns `["l1Cache", "nearCache"]`. Programmatic `registerAlias` adds `"l2Cache"` at runtime pointing to `remoteCache`. Unqualified `ctx.getBean(Cache.class)` resolves to the `@Primary` local cache.

## 6. Walkthrough

Execution order for Level 3:

1. **`CacheCfg` processed** — `ConfigurationClassPostProcessor` finds two `@Bean` methods.
2. **`localCache()` registered** — primary name `"localCache"`, aliases `"l1Cache"`, `"nearCache"`. Marked `@Primary`.
3. **`remoteCache()` registered** — single name `"remoteCache"`.
4. **`ctx.getAliases("localCache")`** → `["l1Cache", "nearCache"]`.
5. **`getBean("localCache")`, `getBean("l1Cache")`, `getBean("nearCache")`** — all return the same `LocalCache` singleton. `c1 == c2 && c2 == c3` → `true`.
6. **`factory.registerAlias("remoteCache", "l2Cache")`** — adds a new alias in the registry at runtime.
7. **`ctx.getBean("l2Cache") == ctx.getBean("remoteCache")`** → `true` — same `RemoteCache` singleton.
8. **`ctx.getBean(Cache.class)`** — two beans of type `Cache`; `localCache` is `@Primary` → resolves to `LocalCache`. `get("user:1")` returns `"Alice"`.

Expected output:
```
Primary name: localCache
Aliases: [l1Cache, nearCache]
l1Cache == nearCache? true
l2Cache added: true
l2Cache == remoteCache? true
Get from primary: Alice
```

## 7. Gotchas & takeaways

> When you supply `name = {"n1", "n2"}`, the **method name is completely ignored** as a bean name. If your method is `public Cache localCache()` but `@Bean(name = {"myCache"})`, then `"localCache"` is NOT registered. Only `"myCache"` is.

> Aliases are **global** — once registered, any lookup by that alias anywhere in the context returns the aliased bean. Registering the same alias twice (pointing to different beans) throws `IllegalStateException`.

- `ctx.getAliases(primaryName)` returns all aliases but not the primary name itself.
- `ctx.getBeanNamesForType(Cache.class)` returns ALL names (primary + aliases) of matching beans.
- Aliases created via `@Bean(name = {...})` are set up by `ConfigurationClassPostProcessor` before beans are instantiated.
- Runtime alias registration via `factory.registerAlias(...)` is possible but unusual; prefer compile-time aliases in `@Bean`.
- `@AliasFor` on annotations (covered in meta-annotation tutorial) is a different mechanism — it bridges annotation attributes, not bean names.
