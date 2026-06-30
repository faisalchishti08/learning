---
card: spring-framework
gi: 81
slug: aware-interfaces-overview
title: Aware interfaces overview
---

## 1. What it is

**`Aware` interfaces** are marker interfaces in Spring that allow a bean to signal it needs access to a piece of the container's infrastructure. Each `Aware` sub-interface has one setter method; Spring detects the interface during bean creation and calls the setter to inject the requested resource. There are a dozen built-in `Aware` interfaces — the most common are `BeanNameAware`, `BeanFactoryAware`, and `ApplicationContextAware`.

```java
import org.springframework.beans.factory.BeanNameAware;
import org.springframework.context.ApplicationContextAware;
import org.springframework.context.ApplicationContext;

@Component
public class SelfDescribingService implements BeanNameAware, ApplicationContextAware {

    private String beanName;
    private ApplicationContext ctx;

    @Override
    public void setBeanName(String name) {
        this.beanName = name;  // called by Spring before @PostConstruct
    }

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        this.ctx = ctx;  // called by Spring before @PostConstruct
    }

    public String describe() {
        return "I am bean '" + beanName + "' in context with "
            + ctx.getBeanDefinitionCount() + " beans";
    }
}
```

In one sentence: **`Aware` interfaces let a Spring bean request container-level resources (bean name, factory, context, environment, resource loader, etc.) by implementing the corresponding interface — Spring detects and injects the resource during bean creation, before `@PostConstruct`.**

## 2. Why & when

Use `Aware` interfaces when:

- A bean needs to **know its own bean name** (e.g., for logging, JMX registration) — `BeanNameAware`.
- A bean needs **programmatic bean lookup** at runtime — `ApplicationContextAware` (service locator pattern).
- A bean needs to **load classpath/file resources** — `ResourceLoaderAware`.
- A bean needs to **read environment properties or profiles** — `EnvironmentAware`.
- A bean is a **`BeanPostProcessor` or framework component** that needs the `BeanFactory` directly — `BeanFactoryAware`.

Avoid `Aware` interfaces in pure application beans when possible — they couple your code to Spring. Prefer `@Autowired ApplicationContext ctx` (which is simpler and achieves the same result for most cases). Use `Aware` interfaces for framework-level beans, infrastructure, or when `@Autowired` isn't available.

## 3. Core concept

```
Most common Aware interfaces:

Interface                  Method                    Provides
─────────────────────────  ─────────────────────────  ─────────────────────────────────
BeanNameAware              setBeanName(String)        The bean's name in the context
BeanClassLoaderAware       setBeanClassLoader(ClassLoader) The class loader loading the bean
BeanFactoryAware           setBeanFactory(BeanFactory) The owning BeanFactory
EnvironmentAware           setEnvironment(Environment) Spring Environment (props/profiles)
EmbeddedValueResolverAware setEmbeddedValueResolver() StringValueResolver (SpEL/props)
ResourceLoaderAware        setResourceLoader(RL)      For loading classpath/file resources
ApplicationEventPublisherAware setApplicationEventPublisher() For publishing events
MessageSourceAware         setMessageSource(MS)       For i18n message resolution
ApplicationContextAware    setApplicationContext(AC)  Full ApplicationContext
ApplicationStartupAware    setApplicationStartup(AS)  Application startup metrics

Firing order within bean creation:
  ① Constructor
  ② @Autowired injection
  ③ Aware setter methods (BeanNameAware first, then others)
  ④ BeanPostProcessor.postProcessBeforeInitialization()
  ⑤ @PostConstruct / afterPropertiesSet() / init-method
  ⑥ BeanPostProcessor.postProcessAfterInitialization()
  ⑦ Bean ready

Note: all Aware setters fire BEFORE @PostConstruct,
so Aware-provided resources are available in @PostConstruct.
```

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Aware interfaces overview — position in lifecycle and the resource each provides">
  <defs>
    <marker id="a81" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="203" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Aware interfaces — Spring injects the resource between injection and @PostConstruct</text>

  <!-- Timeline -->
  <rect x="15"  y="33" width="80"  height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="55"  y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">construct+inject</text>
  <line x1="95" y1="49" x2="108" y2="49" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a81)"/>
  <rect x="112" y="33" width="120" height="32" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="172" y="49" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Aware setters called</text>
  <text x="172" y="61" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">← you are here</text>
  <line x1="232" y1="49" x2="245" y2="49" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a81)"/>
  <rect x="249" y="33" width="120" height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="309" y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@PostConstruct</text>
  <line x1="369" y1="49" x2="382" y2="49" stroke="#6db33f" stroke-width="1.2" marker-end="url(#a81)"/>
  <rect x="386" y="33" width="90"  height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="431" y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">bean ready</text>

  <!-- Resource table -->
  <rect x="10" y="78" width="655" height="120" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="96" fill="#8b949e" font-size="9" font-family="monospace">Interface                      Setter               Provides</text>
  <line x1="12" y1="100" x2="662" y2="100" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="115" fill="#6db33f" font-size="8.5" font-family="monospace">BeanNameAware              setBeanName(s)         bean's name in context</text>
  <text x="22" y="129" fill="#6db33f" font-size="8.5" font-family="monospace">BeanFactoryAware           setBeanFactory(bf)     BeanFactory (low-level)</text>
  <text x="22" y="143" fill="#6db33f" font-size="8.5" font-family="monospace">ApplicationContextAware    setApplicationContext  full ApplicationContext</text>
  <text x="22" y="157" fill="#8b949e" font-size="8.5" font-family="monospace">EnvironmentAware           setEnvironment(e)      properties + profiles</text>
  <text x="22" y="171" fill="#8b949e" font-size="8.5" font-family="monospace">ResourceLoaderAware        setResourceLoader(rl)  load classpath/file resources</text>
  <text x="22" y="185" fill="#8b949e" font-size="8.5" font-family="monospace">ApplicationEventPublisherAware  setApplicationEventPublisher   publish events</text>
  <text x="22" y="199" fill="#8b949e" font-size="7.5" font-family="sans-serif">Prefer @Autowired ApplicationContext for app code; use Aware for framework/infrastructure.</text>
</svg>

`Aware` setters fire after injection but before `@PostConstruct` — all injected resources are available by the time `@PostConstruct` runs.

## 5. Runnable example

Scenario: a `PluginRegistry` bean that needs to know its own bean name (for logging), the full list of beans in the context (to discover plugins), and the resource loader (to load plugin descriptors from classpath).

### Level 1 — Basic

`BeanNameAware` and `ApplicationContextAware` — access bean name and list other beans in the context.

```java
// AwareOverviewDemo.java — run with: java AwareOverviewDemo.java
import java.util.*;

public class AwareOverviewDemo {

    // ── simulated Spring Aware interfaces ─────────────────────────────
    interface BeanNameAware           { void setBeanName(String name); }
    interface ApplicationContextAware { void setApplicationContext(FakeContext ctx); }

    // ── fake ApplicationContext ────────────────────────────────────────
    static class FakeContext {
        private final Map<String, Object> beans;
        FakeContext(Map<String, Object> beans) { this.beans = beans; }
        String[] getBeanDefinitionNames() { return beans.keySet().toArray(String[]::new); }
        int      getBeanDefinitionCount() { return beans.size(); }
        Object   getBean(String name)     { return beans.get(name); }
    }

    // ── bean implementing two Aware interfaces ─────────────────────────
    static class PluginRegistry implements BeanNameAware, ApplicationContextAware {
        private String      beanName;
        private FakeContext ctx;
        private final List<String> discovered = new ArrayList<>();

        @Override
        public void setBeanName(String name) {
            this.beanName = name;
            System.out.println("  [BeanNameAware.setBeanName] beanName='" + name + "'");
        }

        @Override
        public void setApplicationContext(FakeContext ctx) {
            this.ctx = ctx;
            System.out.println("  [ApplicationContextAware.setApplicationContext] context has "
                + ctx.getBeanDefinitionCount() + " beans");
        }

        // @PostConstruct — both Aware setters already fired
        void postConstruct() {
            System.out.println("  [@PostConstruct] discovering plugins (beanName='" + beanName + "')");
            for (String name : ctx.getBeanDefinitionNames()) {
                if (name.endsWith("Plugin") && !name.equals(beanName)) {
                    discovered.add(name);
                    System.out.println("  [@PostConstruct] discovered plugin: " + name);
                }
            }
            System.out.println("  [@PostConstruct] registry '" + beanName + "' ready with "
                + discovered.size() + " plugins");
        }

        List<String> getDiscovered() { return discovered; }
        String describe() { return beanName + ": " + discovered; }
    }

    // ── simulated container: inject Aware resources ───────────────────
    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        PluginRegistry registry = new PluginRegistry();

        // Build fake context with several beans (simulating what Spring creates)
        Map<String, Object> beans = new LinkedHashMap<>();
        beans.put("pluginRegistry",    registry);
        beans.put("authPlugin",        new Object());
        beans.put("loggingPlugin",     new Object());
        beans.put("metricsPlugin",     new Object());
        beans.put("configService",     new Object());
        FakeContext ctx = new FakeContext(beans);

        System.out.println("\n=== Bean creation: Aware setters fire ===");
        // Spring calls these in order: BeanNameAware first, then other Aware interfaces
        registry.setBeanName("pluginRegistry");           // BeanNameAware
        registry.setApplicationContext(ctx);              // ApplicationContextAware

        System.out.println("\n=== @PostConstruct (both Aware resources available) ===");
        registry.postConstruct();

        System.out.println("\n=== Application ===");
        System.out.println("[REGISTRY] " + registry.describe());
    }
}
```

How to run: `java AwareOverviewDemo.java`

`setBeanName()` fires first (BeanNameAware), then `setApplicationContext()` (ApplicationContextAware). Both fire before `@PostConstruct` — so `postConstruct()` can use both `beanName` and `ctx` safely. The registry discovers three plugin beans by scanning bean definition names.

### Level 2 — Intermediate

`EnvironmentAware` and `ResourceLoaderAware` — read properties and load a classpath resource.

```java
// AwareOverviewDemo2.java — run with: java AwareOverviewDemo2.java
import java.util.*;

public class AwareOverviewDemo2 {

    interface BeanNameAware    { void setBeanName(String name); }
    interface EnvironmentAware { void setEnvironment(FakeEnv env); }
    interface ResourceLoaderAware { void setResourceLoader(FakeRL rl); }

    // ── Fake Environment: properties + active profiles ─────────────────
    static class FakeEnv {
        private final Map<String, String> props;
        private final Set<String> activeProfiles;
        FakeEnv(Map<String, String> props, String... profiles) {
            this.props          = new HashMap<>(props);
            this.activeProfiles = new HashSet<>(Arrays.asList(profiles));
        }
        String getProperty(String key) { return props.get(key); }
        String getProperty(String key, String defaultVal) { return props.getOrDefault(key, defaultVal); }
        boolean acceptsProfiles(String profile) { return activeProfiles.contains(profile); }
        Set<String> getActiveProfiles() { return activeProfiles; }
    }

    // ── Fake ResourceLoader ────────────────────────────────────────────
    static class FakeRL {
        private final Map<String, String> resources;
        FakeRL(Map<String, String> resources) { this.resources = resources; }
        String loadAsString(String location) {
            String content = resources.get(location);
            return content != null ? content : "(resource not found: " + location + ")";
        }
    }

    // ── Bean using three Aware interfaces ─────────────────────────────
    static class ConfigurationLoader implements BeanNameAware, EnvironmentAware, ResourceLoaderAware {
        private String  beanName;
        private FakeEnv env;
        private FakeRL  rl;

        private String resolvedConfigFile;
        private String configContent;
        private boolean productionMode;

        @Override public void setBeanName(String n) { this.beanName = n; System.out.println("  [BeanNameAware]      beanName='" + n + "'"); }
        @Override public void setEnvironment(FakeEnv e) { this.env = e;   System.out.println("  [EnvironmentAware]   profiles=" + e.getActiveProfiles()); }
        @Override public void setResourceLoader(FakeRL r) { this.rl = r;  System.out.println("  [ResourceLoaderAware] resourceLoader set"); }

        void postConstruct() {
            System.out.println("  [@PostConstruct] all Aware resources available:");
            productionMode    = env.acceptsProfiles("prod");
            resolvedConfigFile = env.getProperty("config.file",
                productionMode ? "classpath:config-prod.yaml" : "classpath:config-dev.yaml");
            System.out.println("  [@PostConstruct] env.profile=prod?" + productionMode
                + " configFile=" + resolvedConfigFile);

            configContent = rl.loadAsString(resolvedConfigFile);
            System.out.println("  [@PostConstruct] loaded: '" + configContent + "'");
        }

        String describe() { return beanName + "[prod=" + productionMode + " config='" + configContent + "']"; }
    }

    public static void main(String[] args) {
        System.out.println("=== PRODUCTION profile ===");
        FakeEnv prodEnv = new FakeEnv(
            Map.of("config.file", "classpath:config-prod.yaml", "app.name", "myapp"),
            "prod");
        FakeRL rl = new FakeRL(Map.of(
            "classpath:config-prod.yaml", "db.url=jdbc:postgresql://prod-db:5432/myapp",
            "classpath:config-dev.yaml",  "db.url=jdbc:h2:mem:dev"));

        ConfigurationLoader loader = new ConfigurationLoader();
        loader.setBeanName("configurationLoader");
        loader.setEnvironment(prodEnv);
        loader.setResourceLoader(rl);
        loader.postConstruct();
        System.out.println("[DESCRIBE] " + loader.describe());

        System.out.println("\n=== DEV profile ===");
        FakeEnv devEnv = new FakeEnv(Map.of("app.name", "myapp-dev"), "dev");
        ConfigurationLoader loader2 = new ConfigurationLoader();
        loader2.setBeanName("configurationLoader");
        loader2.setEnvironment(devEnv);
        loader2.setResourceLoader(rl);
        loader2.postConstruct();
        System.out.println("[DESCRIBE] " + loader2.describe());
    }
}
```

How to run: `java AwareOverviewDemo2.java`

`EnvironmentAware` provides the active profiles and properties. `ResourceLoaderAware` provides the resource loader. `@PostConstruct` uses both: reads `config.file` property from the environment, then loads the resource at that path. In production, loads `config-prod.yaml`; in dev, loads `config-dev.yaml`.

### Level 3 — Advanced

Full set of four `Aware` interfaces on one bean — log the exact injection order and show how each resource is used in `@PostConstruct`.

```java
// AwareOverviewDemo3.java — run with: java AwareOverviewDemo3.java
import java.util.*;

public class AwareOverviewDemo3 {

    interface BeanNameAware               { void setBeanName(String n);            }
    interface BeanClassLoaderAware        { void setBeanClassLoader(ClassLoader cl); }
    interface EnvironmentAware            { void setEnvironment(FakeEnv e);        }
    interface ApplicationContextAware     { void setApplicationContext(FakeCtx c); }

    static class FakeEnv {
        private final Map<String, String> props;
        FakeEnv(Map<String, String> p) { this.props = p; }
        String getProperty(String k, String d) { return props.getOrDefault(k, d); }
        boolean acceptsProfiles(String p)      { return props.getOrDefault("spring.profiles.active","").contains(p); }
    }

    static class FakeCtx {
        private final Map<String, Object> beans;
        FakeCtx(Map<String, Object> b) { this.beans = b; }
        String[] getBeanDefinitionNames() { return beans.keySet().toArray(String[]::new); }
        int getBeanDefinitionCount() { return beans.size(); }
        <T> T getBean(String n, Class<T> t) { return t.cast(beans.get(n)); }
    }

    static class InfrastructureBean
        implements BeanNameAware, BeanClassLoaderAware, EnvironmentAware, ApplicationContextAware {

        private String      beanName;
        private ClassLoader classLoader;
        private FakeEnv     env;
        private FakeCtx     ctx;
        private final List<String> awareLog = new ArrayList<>();

        @Override public void setBeanName(String n)          { beanName     = n;  awareLog.add("BeanNameAware"); System.out.println("  [1] BeanNameAware.setBeanName('" + n + "')"); }
        @Override public void setBeanClassLoader(ClassLoader cl){ classLoader= cl; awareLog.add("BeanClassLoaderAware"); System.out.println("  [2] BeanClassLoaderAware.setBeanClassLoader(" + cl.getClass().getSimpleName() + ")"); }
        @Override public void setEnvironment(FakeEnv e)      { env          = e;  awareLog.add("EnvironmentAware"); System.out.println("  [3] EnvironmentAware.setEnvironment()"); }
        @Override public void setApplicationContext(FakeCtx c){ ctx          = c;  awareLog.add("ApplicationContextAware"); System.out.println("  [4] ApplicationContextAware.setApplicationContext()"); }

        void postConstruct() {
            System.out.println("  [5] @PostConstruct — all " + awareLog.size() + " Aware setters done: " + awareLog);
            String profile   = env.getProperty("spring.profiles.active", "default");
            String version   = env.getProperty("app.version", "unknown");
            int    beanCount = ctx.getBeanDefinitionCount();
            String loader    = classLoader.getClass().getSimpleName();
            System.out.printf("  [@PostConstruct] beanName='%s' profile='%s' version='%s' beans=%d classLoader=%s%n",
                beanName, profile, version, beanCount, loader);
        }

        String summary() {
            return String.format("InfrastructureBean[name=%s,awareOrder=%s]", beanName, awareLog);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Simulating Spring Aware injection order ===");
        InfrastructureBean bean = new InfrastructureBean();

        Map<String, Object> beanMap = new LinkedHashMap<>();
        beanMap.put("infrastructureBean", bean);
        beanMap.put("dataSource",         new Object());
        beanMap.put("userService",        new Object());
        beanMap.put("orderService",       new Object());
        FakeCtx ctx = new FakeCtx(beanMap);
        FakeEnv env = new FakeEnv(Map.of("spring.profiles.active","prod","app.version","2.7.1"));

        // Spring calls Aware setters in a defined order:
        // BeanNameAware → BeanClassLoaderAware → BeanFactoryAware → ApplicationContextAware
        bean.setBeanName("infrastructureBean");     // ① BeanNameAware
        bean.setBeanClassLoader(Thread.currentThread().getContextClassLoader()); // ② BeanClassLoaderAware
        bean.setEnvironment(env);                  // ③ EnvironmentAware (via ApplicationContextAwareProcessor)
        bean.setApplicationContext(ctx);           // ④ ApplicationContextAware (via ApplicationContextAwareProcessor)
        bean.postConstruct();                      // ⑤ @PostConstruct

        System.out.println();
        System.out.println("[SUMMARY] " + bean.summary());
    }
}
```

How to run: `java AwareOverviewDemo3.java`

Four `Aware` interfaces fire in Spring's documented order: `BeanNameAware` (1st), `BeanClassLoaderAware` (2nd), `EnvironmentAware` (3rd via `ApplicationContextAwareProcessor`), `ApplicationContextAware` (4th). All four are available in `@PostConstruct`, which uses them to log a complete diagnostic summary.

## 6. Walkthrough

**Level 3 injection sequence:**

```
new InfrastructureBean()                      ← ① constructor
[injection: no @Autowired fields in example]  ← ② injection

Spring checks: does bean implement Aware sub-interfaces?
  BeanNameAware?           YES → setBeanName("infrastructureBean")
                                  awareLog=[BeanNameAware]     ✓

  BeanClassLoaderAware?    YES → setBeanClassLoader(AppCL)
                                  awareLog=[BN, BCL]           ✓

  EnvironmentAware?        YES → setEnvironment(env)
                                  awareLog=[BN, BCL, EA]       ✓

  ApplicationContextAware? YES → setApplicationContext(ctx)
                                  awareLog=[BN, BCL, EA, ACA]  ✓

BeanPostProcessor.postProcessBeforeInitialization() [not shown]

@PostConstruct:
  awareLog.size()=4 (all setters fired)
  profile='prod' version='2.7.1' beans=4 classLoader=AppClassLoader ✓

@PostConstruct fires AFTER all Aware setters → all resources available ✓
```

## 7. Gotchas & takeaways

> **`Aware` setters fire BEFORE `@PostConstruct`** — you can safely use the injected resources in your `@PostConstruct` method. Never rely on Aware resources inside the constructor — they haven't been set yet.

> **`ApplicationContextAware` is the "nuclear option"** — it gives full access to the container. This enables the service locator anti-pattern (pulling beans on demand). Prefer `@Autowired` for direct dependencies. Use `ApplicationContextAware` only when you genuinely need dynamic lookup (plugin systems, factories, abstract generic services).

- For most application beans, `@Autowired ApplicationContext ctx` is simpler and equivalent to `ApplicationContextAware`. Use `ApplicationContextAware` when you need the injection to happen without a `@Autowired` field (e.g., in a base class or when constructing via a factory method).
- `BeanFactoryAware` gives access to a `BeanFactory` (lower-level than `ApplicationContext`). Prefer `ApplicationContextAware` unless you specifically need only `BeanFactory` semantics.
- `BeanNameAware` is useful for diagnostic logging, JMX MBean naming, and frameworks where a bean's name must appear in metrics or traces.
- Implement multiple `Aware` interfaces freely — there's no performance cost. Spring processes them all before `@PostConstruct`.
