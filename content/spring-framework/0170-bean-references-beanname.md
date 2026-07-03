---
card: spring-framework
gi: 170
slug: bean-references-beanname
title: "Bean references (@beanName)"
---

## 1. What it is

In a Spring `ApplicationContext`, SpEL expressions can reference beans by name using the `@beanName` syntax. This resolves the named bean from the `ApplicationContext` and makes it the subject of the following property or method chain. The bean resolver is wired automatically when Spring processes `@Value` annotations; for manual use, set it via `ctx.setBeanResolver(resolver)`.

```java
@Value("#{@myService.computeResult()}")       // calls a method on bean "myService"
@Value("#{@dataSourceConfig.maxPoolSize}")    // reads a property from bean "dataSourceConfig"
@Value("#{@featureFlags['betaEnabled']}")     // indexes a Map bean named "featureFlags"
```

## 2. Why & when

- **Cross-bean wiring without `@Autowired`** — derive a field value from another bean's method or property without full dependency injection overhead.
- **Feature flags** — `@Value("#{@featureFlags.isEnabled('betaFeature')}")` reads a runtime flag from a flag service.
- **Computed defaults** — `@Value("#{@appProperties.timeout ?: 5000}")` uses Elvis fallback when the bean's property may be zero.
- **Conditional logic** — `@Value("#{@env.isDev() ? 'debug' : 'info'}")` selects a log level based on a bean state.
- **Security** — Spring Security evaluates `@PreAuthorize("@authService.canAccess(#id)")` using the bean resolver.

## 3. Core concept

`@beanName` resolution:

1. SpEL recognizes `@` prefix → delegates to `ctx.getBeanResolver()`.
2. `BeanResolver.resolve(ctx, "beanName")` → calls `applicationContext.getBean("beanName")`.
3. The returned bean becomes the subject for subsequent property access or method calls.

| Syntax | Meaning |
|---|---|
| `@beanName` | get the bean itself |
| `@beanName.property` | read a property from the bean |
| `@beanName.method()` | call a method on the bean |
| `@beanName['key']` | index a Map or List bean by key |
| `@beanName.list[0]` | navigate into a collection property |

To enable `@beanName` outside Spring annotation processing:

```java
ctx.setBeanResolver((evalCtx, name) -> applicationContext.getBean(name));
```

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg">
  <!-- Expression -->
  <rect x="10" y="25" width="165" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="92" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SpEL: @myService</text>
  <text x="92" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">.computeResult()</text>

  <!-- BeanResolver -->
  <rect x="235" y="18" width="210" height="65" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="38" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">BeanResolver</text>
  <line x1="243" y1="45" x2="437" y2="45" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="340" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolve(ctx, "myService")</text>
  <text x="340" y="71" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ ctx.getBean("myService")</text>

  <!-- Spring ApplicationContext -->
  <rect x="505" y="18" width="185" height="65" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="597" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext</text>
  <line x1="513" y1="45" x2="682" y2="45" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="597" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">contains bean "myService"</text>
  <text x="597" y="71" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">returns MyService instance</text>

  <defs>
    <marker id="a170" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="177" y1="45" x2="232" y2="45" stroke="#6db33f" stroke-width="2" marker-end="url(#a170)"/>
  <line x1="447" y1="50" x2="502" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a170)"/>

  <!-- Result -->
  <rect x="10" y="100" width="680" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="350" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@myService.computeResult() → invokes computeResult() on the singleton MyService bean</text>
  <text x="350" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Automatic in @Value context  |  Manual: ctx.setBeanResolver(ac::getBean)</text>
  <text x="350" y="148" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Security: @PreAuthorize("@permService.canAccess(#id)") — same resolver mechanism</text>
</svg>

`@beanName` routes through `BeanResolver` to retrieve the named Spring bean; Spring auto-configures this in `@Value` context.

## 5. Runnable example

### Level 1 — Basic

`@Value` with bean references; read property and call method.

```java
// SpelBeanRefsBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

@Configuration
class BeanRefCfg {
    @Bean("appInfo")
    public AppInfo appInfo() { return new AppInfo("MyApp", "1.0.0", true); }
}

class AppInfo {
    private final String name;
    private final String version;
    private final boolean enabled;

    AppInfo(String name, String version, boolean enabled) {
        this.name = name; this.version = version; this.enabled = enabled;
    }
    public String getName()     { return name; }
    public String getVersion()  { return version; }
    public boolean isEnabled()  { return enabled; }
    public String getBanner()   { return name + " v" + version + (enabled ? " [ON]" : " [OFF]"); }
}

@org.springframework.stereotype.Component
class WelcomeBanner {
    @Value("#{@appInfo.name}")
    private String appName;

    @Value("#{@appInfo.version}")
    private String version;

    @Value("#{@appInfo.enabled}")
    private boolean enabled;

    @Value("#{@appInfo.banner}")
    private String banner;

    @Value("#{@appInfo.enabled ? 'ACTIVE' : 'DISABLED'}")
    private String status;

    public void print() {
        System.out.println("appName:  " + appName);
        System.out.println("version:  " + version);
        System.out.println("enabled:  " + enabled);
        System.out.println("banner:   " + banner);
        System.out.println("status:   " + status);
    }
}

public class SpelBeanRefsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BeanRefCfg.class, WelcomeBanner.class);
        ctx.getBean(WelcomeBanner.class).print();
        ctx.close();
    }
}
```

How to run: `java SpelBeanRefsBasic.java`

`@Value("#{@appInfo.name}")` resolves the bean named `"appInfo"` and reads its `name` property. Spring auto-configures the `BeanResolver` when processing `@Value` — no manual setup needed.

### Level 2 — Intermediate

Map bean as feature flag store; bean method call; conditional based on bean state.

```java
// SpelBeanRefsIntermediate.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.util.*;

@Configuration
class FlagCfg {
    @Bean("featureFlags")
    public Map<String, Boolean> featureFlags() {
        Map<String, Boolean> flags = new HashMap<>();
        flags.put("newUI",        true);
        flags.put("betaReports",  false);
        flags.put("aiAssistant",  true);
        return flags;
    }

    @Bean("limits")
    public Limits limits() { return new Limits(100, 5000, 10); }
}

class Limits {
    private int maxRetries;
    private int maxPayloadBytes;
    private int maxConnections;

    Limits(int maxRetries, int maxPayload, int maxConn) {
        this.maxRetries = maxRetries; this.maxPayloadBytes = maxPayload; this.maxConnections = maxConn;
    }
    public int getMaxRetries()      { return maxRetries; }
    public int getMaxPayloadBytes() { return maxPayloadBytes; }
    public int getMaxConnections()  { return maxConnections; }
    public int totalCapacity()      { return maxConnections * maxPayloadBytes; }
}

@org.springframework.stereotype.Component
class ServiceSettings {
    @Value("#{@featureFlags['newUI']}")
    private boolean newUiEnabled;

    @Value("#{@featureFlags['betaReports']}")
    private boolean betaReportsEnabled;

    @Value("#{@limits.maxRetries}")
    private int maxRetries;

    @Value("#{@limits.totalCapacity()}")
    private int totalCapacity;

    @Value("#{@featureFlags['aiAssistant'] ? 'gpt-4' : 'rule-based'}")
    private String modelName;

    public void print() {
        System.out.println("newUiEnabled:       " + newUiEnabled);
        System.out.println("betaReportsEnabled: " + betaReportsEnabled);
        System.out.println("maxRetries:         " + maxRetries);
        System.out.println("totalCapacity:      " + totalCapacity);
        System.out.println("modelName:          " + modelName);
    }
}

public class SpelBeanRefsIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FlagCfg.class, ServiceSettings.class);
        ctx.getBean(ServiceSettings.class).print();
        ctx.close();
    }
}
```

How to run: `java SpelBeanRefsIntermediate.java`

`@Value("#{@featureFlags['newUI']}")` resolves `featureFlags` as a `Map<String, Boolean>` bean and reads key `"newUI"`. `@Value("#{@limits.totalCapacity()}")` calls the method `totalCapacity()` on the `limits` bean. Bean method calls are fully supported.

### Level 3 — Advanced

Manual `BeanResolver` outside Spring annotations; security-style bean method in filter; nested bean navigation.

```java
// SpelBeanRefsAdvanced.java
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

interface PermissionService {
    boolean canAccess(String resourceId, String role);
    List<String> getAllowedResources(String role);
}

@org.springframework.stereotype.Service("permService")
class PermissionServiceImpl implements PermissionService {
    private static final Map<String, Set<String>> rolePerms = Map.of(
        "admin",  Set.of("res-A", "res-B", "res-C"),
        "viewer", Set.of("res-A"));

    @Override
    public boolean canAccess(String resourceId, String role) {
        return rolePerms.getOrDefault(role, Set.of()).contains(resourceId);
    }
    @Override
    public List<String> getAllowedResources(String role) {
        return new ArrayList<>(rolePerms.getOrDefault(role, Set.of()));
    }
}

@Configuration
class AdvBeanCfg {}

public class SpelBeanRefsAdvanced {
    public static void main(String[] args) {
        var appCtx = new AnnotationConfigApplicationContext(AdvBeanCfg.class, PermissionServiceImpl.class);

        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        // Set up BeanResolver manually
        ctx.setBeanResolver((evalCtx, name) -> appCtx.getBean(name));
        ctx.setVariable("resourceId", "res-B");
        ctx.setVariable("role", "admin");

        // Security-style access check
        System.out.println(parser.parseExpression(
            "@permService.canAccess(#resourceId, #role)").getValue(ctx, Boolean.class)); // true

        ctx.setVariable("role", "viewer");
        System.out.println(parser.parseExpression(
            "@permService.canAccess(#resourceId, #role)").getValue(ctx, Boolean.class)); // false

        // Get allowed resources via bean method
        System.out.println(parser.parseExpression(
            "@permService.getAllowedResources(#role)").getValue(ctx, List.class));

        // Conditional based on bean method
        System.out.println(parser.parseExpression(
            "@permService.canAccess('res-A', #role) ? 'ALLOWED' : 'DENIED'")
            .getValue(ctx, String.class)); // ALLOWED (viewer can access res-A)

        appCtx.close();
    }
}
```

How to run: `java SpelBeanRefsAdvanced.java`

`ctx.setBeanResolver((evalCtx, name) -> appCtx.getBean(name))` manually wires the `ApplicationContext` as the bean resolver. `@permService.canAccess(#resourceId, #role)` calls an instance method on the Spring-managed `PermissionServiceImpl` bean — exactly how Spring Security evaluates `@PreAuthorize` expressions.

## 6. Walkthrough

Execution for `"@permService.canAccess(#resourceId, #role)"` with `#resourceId="res-B"`, `#role="admin"`:

1. SpEL sees `@permService` — delegates to `BeanResolver.resolve(ctx, "permService")`.
2. `appCtx.getBean("permService")` → returns the `PermissionServiceImpl` singleton.
3. `.canAccess(#resourceId, #role)` → `MethodResolver` finds `canAccess(String, String)`.
4. `#resourceId` → `"res-B"`, `#role` → `"admin"`.
5. `PermissionServiceImpl.canAccess("res-B", "admin")` → checks `rolePerms.get("admin").contains("res-B")` → `true`.
6. Result: `Boolean.TRUE`.

## 7. Gotchas & takeaways

> **`@beanName` vs `#{beanName}`** — `@beanName` in SpEL uses the `BeanResolver`. `#{beanName}` without `@` resolves as a property or variable on the root object, NOT as a bean. The `@` prefix is required to trigger bean lookup.

> Bean names in `@beanName` are case-sensitive. `@MyService` and `@myService` are different lookups. Spring's default bean naming (lower-camel-case of class name) means `MyServiceImpl` becomes `myServiceImpl` — use the exact name you'd pass to `ctx.getBean(...)`.

- `@beanName` retrieves the full Spring bean, including all proxy wrapping. Calling a method on a `@Transactional` bean via `@beanName.method()` invokes the transactional proxy, so the transaction is active — same behavior as a direct `@Autowired` call.
- In Spring Security's `@PreAuthorize("@permService.check(#id)")`, `#id` refers to the method argument by name. This requires `-parameters` compiler flag (Spring Boot configures it by default) or `@Param` annotations on the method.
- `BeanResolver` is NOT available in `SimpleEvaluationContext`. Setting one manually on a `SimpleEvaluationContext` instance will throw — bean resolution requires full context capabilities.
