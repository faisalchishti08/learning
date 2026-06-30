---
card: spring-framework
gi: 85
slug: other-aware-interfaces-resourceloaderaware-environmentaware
title: Other *Aware interfaces (ResourceLoaderAware, EnvironmentAware, etc.)
---

## 1. What it is

Beyond `BeanNameAware`, `BeanFactoryAware`, and `ApplicationContextAware`, Spring provides several more `*Aware` interfaces that inject narrowly-scoped infrastructure objects. Each is a focused alternative to `ApplicationContextAware` when you only need one specific capability — keeping the coupling minimal.

```java
import org.springframework.context.*;
import org.springframework.core.env.*;
import org.springframework.core.io.*;

@Component
public class ConfigLoader implements ResourceLoaderAware, EnvironmentAware {

    private ResourceLoader resourceLoader;
    private Environment    environment;

    @Override
    public void setResourceLoader(ResourceLoader rl) {
        this.resourceLoader = rl;
    }

    @Override
    public void setEnvironment(Environment env) {
        this.environment = env;
    }

    @PostConstruct
    public void load() throws Exception {
        String profile = environment.getActiveProfiles()[0];  // "prod" or "dev"
        Resource config = resourceLoader.getResource("classpath:config-" + profile + ".yml");
        System.out.println("Loaded: " + config.getURI() + " (" + config.contentLength() + " bytes)");
    }
}
```

In one sentence: **The specialized `*Aware` interfaces — `ResourceLoaderAware`, `EnvironmentAware`, `ApplicationEventPublisherAware`, `MessageSourceAware`, and others — inject a single focused infrastructure object, keeping coupling narrower than the full `ApplicationContextAware`.**

## 2. Why & when

| Interface | What it injects | Use when |
|---|---|---|
| `ResourceLoaderAware` | `ResourceLoader` | Load `classpath:`, `file:`, `url:` resources |
| `EnvironmentAware` | `Environment` | Read properties, check active profiles |
| `ApplicationEventPublisherAware` | `ApplicationEventPublisher` | Publish events without full `ApplicationContext` |
| `MessageSourceAware` | `MessageSource` | Resolve i18n message codes |
| `EmbeddedValueResolverAware` | `StringValueResolver` | Resolve `${...}` / SpEL strings programmatically |
| `ApplicationStartupAware` | `ApplicationStartup` | Record startup metrics/steps |
| `NotificationPublisherAware` | `NotificationPublisher` | Spring JMX notification publisher |

Use these when `@Autowired ApplicationContext ctx` is too broad — only inject what the class actually needs, making it easier to test in isolation.

## 3. Core concept

```
All *Aware interfaces fire in the same phase — between @Autowired injection
and @PostConstruct:

  ① Constructor
  ② @Autowired / @Value injection
  ③ Aware setters (all *Aware interfaces) — order within this phase:
       BeanNameAware           → setBeanName()
       BeanClassLoaderAware    → setBeanClassLoader()
       BeanFactoryAware        → setBeanFactory()
       EnvironmentAware        → setEnvironment()         ← covered here
       EmbeddedValueResolverAware → setEmbeddedValueResolver()
       ResourceLoaderAware     → setResourceLoader()      ← covered here
       ApplicationEventPublisherAware → setApplicationEventPublisher()  ← covered here
       MessageSourceAware      → setMessageSource()
       ApplicationContextAware → setApplicationContext()
  ④ BeanPostProcessor.postProcessBeforeInitialization()
  ⑤ @PostConstruct / afterPropertiesSet() / init-method
  ⑥ Bean ready

ResourceLoader:
  getResource("classpath:config.yaml") → Resource
  getResource("file:/etc/app/config")  → Resource
  getResource("https://example.com/config.json") → Resource

Environment:
  getProperty("db.url")                → String or null
  getProperty("db.pool.size", Integer.class, 10) → int with default
  acceptsProfiles(Profiles.of("prod")) → boolean
  getActiveProfiles()                  → String[]
```

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Specialized Aware interfaces, their injection object, and typical use">
  <defs>
    <marker id="a85" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="203" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Specialized *Aware interfaces — inject only what you need</text>

  <!-- Interface → capability mapping -->
  <rect x="10" y="32" width="655" height="162" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="50" fill="#8b949e" font-size="9" font-family="monospace">Interface                      Injects              Key capability</text>
  <line x1="12" y1="54" x2="662" y2="54" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="69" fill="#6db33f" font-size="9" font-family="monospace">ResourceLoaderAware        ResourceLoader       getResource(location)</text>
  <text x="22" y="83" fill="#6db33f" font-size="9" font-family="monospace">EnvironmentAware           Environment          getProperty / acceptsProfiles</text>
  <text x="22" y="97" fill="#6db33f" font-size="9" font-family="monospace">ApplicationEventPublisherAware ApplicationEventPublisher publishEvent(event)</text>
  <text x="22" y="111" fill="#8b949e" font-size="9" font-family="monospace">MessageSourceAware         MessageSource        getMessage(code, args, locale)</text>
  <text x="22" y="125" fill="#8b949e" font-size="9" font-family="monospace">EmbeddedValueResolverAware StringValueResolver  resolveStringValue("${key}")</text>
  <text x="22" y="139" fill="#8b949e" font-size="9" font-family="monospace">BeanClassLoaderAware       ClassLoader          load classes / resources</text>
  <text x="22" y="153" fill="#8b949e" font-size="9" font-family="monospace">ApplicationStartupAware    ApplicationStartup   record startup steps/metrics</text>
  <line x1="12" y1="158" x2="662" y2="158" stroke="#8b949e" stroke-width="0.4" stroke-dasharray="3,3"/>
  <text x="22" y="173" fill="#79c0ff" font-size="9" font-family="sans-serif">Prefer narrow interface over ApplicationContextAware — easier to test, less coupling.</text>
  <text x="22" y="187" fill="#79c0ff" font-size="9" font-family="sans-serif">Alternative: @Autowired Environment env / @Autowired ResourceLoader rl — same result for @Component.</text>
</svg>

Each `*Aware` interface is a focused alternative to `ApplicationContextAware`. Use the narrowest one that gives you what you need.

## 5. Runnable example

Scenario: a `ConfigurationService` that reads active profile from `EnvironmentAware`, loads a profile-specific config file via `ResourceLoaderAware`, and publishes a `ConfigReadyEvent` via `ApplicationEventPublisherAware`.

### Level 1 — Basic

`EnvironmentAware` reads properties and resolves the active profile.

```java
// OtherAwareDemo.java — run with: java OtherAwareDemo.java
import java.util.*;

public class OtherAwareDemo {

    interface EnvironmentAware { void setEnvironment(FakeEnv e); }

    static class FakeEnv {
        private final Map<String, String> props;
        private final Set<String> profiles;
        FakeEnv(Map<String, String> props, String... profiles) {
            this.props    = new HashMap<>(props);
            this.profiles = new HashSet<>(Arrays.asList(profiles));
        }
        String   getProperty(String key)                           { return props.get(key); }
        String   getProperty(String key, String defaultVal)        { return props.getOrDefault(key, defaultVal); }
        <T> T    getProperty(String key, Class<T> type, T def)    {
            String v = props.get(key);
            if (v == null) return def;
            if (type == Integer.class) return type.cast(Integer.parseInt(v));
            if (type == Boolean.class) return type.cast(Boolean.parseBoolean(v));
            return type.cast(v);
        }
        boolean  acceptsProfile(String p)                          { return profiles.contains(p); }
        String[] getActiveProfiles()                               { return profiles.toArray(String[]::new); }
    }

    static class DataSourceConfig implements EnvironmentAware {
        private FakeEnv env;

        @Override
        public void setEnvironment(FakeEnv e) {
            this.env = e;
            System.out.println("  [EnvironmentAware.setEnvironment] profiles=" + Arrays.toString(e.getActiveProfiles()));
        }

        void postConstruct() {
            String url      = env.getProperty("spring.datasource.url",         "jdbc:h2:mem:default");
            int    poolSize = env.getProperty("spring.datasource.pool.size",    Integer.class, 5);
            boolean isProd  = env.acceptsProfile("prod");
            System.out.printf("  [@PostConstruct] url='%s' poolSize=%d isProd=%s%n", url, poolSize, isProd);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== PROD profile ===");
        DataSourceConfig ds1 = new DataSourceConfig();
        ds1.setEnvironment(new FakeEnv(
            Map.of("spring.datasource.url", "jdbc:postgresql://prod:5432/mydb",
                   "spring.datasource.pool.size", "20"),
            "prod"));
        ds1.postConstruct();

        System.out.println("\n=== DEV profile ===");
        DataSourceConfig ds2 = new DataSourceConfig();
        ds2.setEnvironment(new FakeEnv(
            Map.of("spring.datasource.url", "jdbc:h2:mem:testdb"),
            "dev"));
        ds2.postConstruct();
    }
}
```

How to run: `java OtherAwareDemo.java`

`setEnvironment()` fires before `@PostConstruct`. `postConstruct()` reads three values from the environment: the JDBC URL (with fallback), pool size (typed as `Integer` with default 5), and profile check. Different environments produce different configurations.

### Level 2 — Intermediate

`ResourceLoaderAware` and `EnvironmentAware` combined — load a profile-specific resource file.

```java
// OtherAwareDemo2.java — run with: java OtherAwareDemo2.java
import java.util.*;
import java.io.*;

public class OtherAwareDemo2 {

    interface EnvironmentAware    { void setEnvironment(FakeEnv e);       }
    interface ResourceLoaderAware { void setResourceLoader(FakeRL rl);    }

    static class FakeEnv {
        private final Map<String, String> props;
        private final String[] activeProfiles;
        FakeEnv(String[] profiles, Map<String, String> props) { this.activeProfiles = profiles; this.props = props; }
        String getProperty(String k, String def) { return props.getOrDefault(k, def); }
        String[] getActiveProfiles() { return activeProfiles; }
    }

    // ── Fake ResourceLoader: resolves classpath: prefixes from in-memory map ──
    static class FakeRL {
        private final Map<String, String> resources;
        FakeRL(Map<String, String> res) { this.resources = res; }
        FakeResource getResource(String location) { return new FakeResource(location, resources.get(location)); }
    }

    record FakeResource(String location, String content) {
        boolean exists()     { return content != null; }
        String readContent() { return content != null ? content : "(not found)"; }
        long   contentLength() { return content != null ? content.length() : 0; }
    }

    // ── Bean using both Aware interfaces ────────────────────────────────
    static class ApplicationConfigLoader implements EnvironmentAware, ResourceLoaderAware {
        private FakeEnv env;
        private FakeRL  rl;

        private String   configContent;
        private String   configPath;

        @Override public void setEnvironment(FakeEnv e)    { this.env = e; System.out.println("  [EnvironmentAware] profiles=" + Arrays.toString(e.getActiveProfiles())); }
        @Override public void setResourceLoader(FakeRL r)  { this.rl  = r; System.out.println("  [ResourceLoaderAware] resourceLoader set"); }

        void postConstruct() {
            // Determine config file based on active profile
            String profile   = env.getActiveProfiles().length > 0 ? env.getActiveProfiles()[0] : "default";
            String explicitPath = env.getProperty("app.config.file", null);
            configPath = explicitPath != null ? explicitPath : "classpath:application-" + profile + ".yaml";

            System.out.println("  [@PostConstruct] loading config from: " + configPath);
            FakeResource resource = rl.getResource(configPath);
            if (!resource.exists()) {
                System.out.println("  [@PostConstruct] profile-specific config not found, falling back to default");
                resource = rl.getResource("classpath:application.yaml");
            }
            configContent = resource.readContent();
            System.out.printf("  [@PostConstruct] loaded %d bytes from %s%n",
                resource.contentLength(), resource.location());
        }

        String getConfigContent() { return configContent; }
        String getConfigPath()    { return configPath; }
    }

    public static void main(String[] args) {
        Map<String, String> resources = Map.of(
            "classpath:application.yaml",      "db.url: jdbc:h2:mem:default\npool.size: 5",
            "classpath:application-prod.yaml", "db.url: jdbc:postgresql://prod/db\npool.size: 20",
            "classpath:application-dev.yaml",  "db.url: jdbc:h2:mem:dev\npool.size: 2"
        );
        FakeRL rl = new FakeRL(resources);

        System.out.println("=== PROD profile ===");
        ApplicationConfigLoader loader1 = new ApplicationConfigLoader();
        loader1.setEnvironment(new FakeEnv(new String[]{"prod"}, Map.of()));
        loader1.setResourceLoader(rl);
        loader1.postConstruct();
        System.out.println("[CONFIG]\n" + loader1.getConfigContent());

        System.out.println("\n=== STAGING profile (no staging config → falls back to default) ===");
        ApplicationConfigLoader loader2 = new ApplicationConfigLoader();
        loader2.setEnvironment(new FakeEnv(new String[]{"staging"}, Map.of()));
        loader2.setResourceLoader(rl);
        loader2.postConstruct();
        System.out.println("[CONFIG]\n" + loader2.getConfigContent());
    }
}
```

How to run: `java OtherAwareDemo2.java`

`setEnvironment()` injects the active profile list. `setResourceLoader()` injects the resource resolver. `postConstruct()` builds a profile-specific config path and loads it via `getResource()`. If the profile-specific file doesn't exist, it falls back to the default `application.yaml`.

### Level 3 — Advanced

All three — `EnvironmentAware`, `ResourceLoaderAware`, and `ApplicationEventPublisherAware` — in one bean.

```java
// OtherAwareDemo3.java — run with: java OtherAwareDemo3.java
import java.util.*;

public class OtherAwareDemo3 {

    interface EnvironmentAware            { void setEnvironment(FakeEnv e);               }
    interface ResourceLoaderAware         { void setResourceLoader(FakeRL rl);             }
    interface ApplicationEventPublisherAware { void setApplicationEventPublisher(FakeAEP p); }

    static class FakeEnv {
        private final Map<String, String> props;
        private final String[] profiles;
        FakeEnv(String[] profiles, Map<String, String> props) { this.profiles = profiles; this.props = props; }
        String   get(String k, String def)   { return props.getOrDefault(k, def); }
        String[] getActiveProfiles()         { return profiles; }
        boolean  isProd()                    { return Arrays.asList(profiles).contains("prod"); }
    }

    static class FakeRL {
        private final Map<String, String> res;
        FakeRL(Map<String, String> res) { this.res = res; }
        String load(String loc) { return res.getOrDefault(loc, "(not found: " + loc + ")"); }
    }

    record ConfigReadyEvent(String profile, String configContent, boolean validated) {}

    static class FakeAEP {
        private final List<ConfigReadyEvent> published = new ArrayList<>();
        void publishEvent(ConfigReadyEvent e) { published.add(e); System.out.println("  [AEP.publishEvent] " + e); }
        List<ConfigReadyEvent> getPublished() { return published; }
    }

    // ── Fake @EventListener bean ────────────────────────────────────────
    static class StartupReporter {
        private final List<String> log = new ArrayList<>();
        void onConfigReady(ConfigReadyEvent e) {
            String msg = "Config ready for profile=" + e.profile() + " validated=" + e.validated();
            log.add(msg);
            System.out.println("  [StartupReporter] " + msg);
        }
    }

    // ── Bean using three *Aware interfaces ────────────────────────────
    static class SmartConfigService
        implements EnvironmentAware, ResourceLoaderAware, ApplicationEventPublisherAware {

        private FakeEnv env;
        private FakeRL  rl;
        private FakeAEP publisher;
        private final List<String> awareLog = new ArrayList<>();

        @Override public void setEnvironment(FakeEnv e)                  { env=e;       awareLog.add("EnvironmentAware");            System.out.println("  [EnvironmentAware]            profiles=" + Arrays.toString(e.getActiveProfiles())); }
        @Override public void setResourceLoader(FakeRL r)                 { rl=r;        awareLog.add("ResourceLoaderAware");         System.out.println("  [ResourceLoaderAware]         resource loader set"); }
        @Override public void setApplicationEventPublisher(FakeAEP p)     { publisher=p; awareLog.add("ApplicationEventPublisherAware"); System.out.println("  [ApplicationEventPublisherAware] publisher set"); }

        void postConstruct() {
            System.out.println("  [@PostConstruct] all " + awareLog.size() + " Aware setters done: " + awareLog);

            // Use EnvironmentAware: resolve config file name
            String profile    = env.getActiveProfiles().length > 0 ? env.getActiveProfiles()[0] : "default";
            String configFile = "classpath:config-" + profile + ".yaml";

            // Use ResourceLoaderAware: load the config
            String content    = rl.load(configFile);
            boolean valid     = !content.startsWith("(not found");
            System.out.printf("  [@PostConstruct] loaded config for profile='%s' valid=%s%n", profile, valid);
            if (!valid) System.out.println("  [@PostConstruct] WARN: config file missing — using defaults");

            // Use ApplicationEventPublisherAware: notify other beans
            publisher.publishEvent(new ConfigReadyEvent(profile, content, valid));
        }
    }

    // ── Simulate registering the event listener ────────────────────────
    public static void main(String[] args) {
        System.out.println("=== PROD run ===");
        FakeAEP pub = new FakeAEP();
        StartupReporter reporter = new StartupReporter();
        pub.getPublished();  // just reference; in real Spring this would be @EventListener

        SmartConfigService svc = new SmartConfigService();
        svc.setEnvironment(new FakeEnv(new String[]{"prod"}, Map.of("app.feature.x", "true")));
        svc.setResourceLoader(new FakeRL(Map.of(
            "classpath:config-prod.yaml", "feature.x: true\ndb.pool: 20")));
        svc.setApplicationEventPublisher(pub);
        svc.postConstruct();

        // Simulate @EventListener
        pub.getPublished().forEach(reporter::onConfigReady);

        System.out.println("\n=== DEV run — missing config file ===");
        FakeAEP pub2 = new FakeAEP();
        SmartConfigService svc2 = new SmartConfigService();
        svc2.setEnvironment(new FakeEnv(new String[]{"dev"}, Map.of()));
        svc2.setResourceLoader(new FakeRL(Map.of())); // no files registered
        svc2.setApplicationEventPublisher(pub2);
        svc2.postConstruct();
        pub2.getPublished().forEach(reporter::onConfigReady);

        System.out.println("\n[REPORTER LOG] " + reporter.log);
    }
}
```

How to run: `java OtherAwareDemo3.java`

All three Aware setters fire before `@PostConstruct`. `postConstruct()` uses all three: `EnvironmentAware` resolves the profile, `ResourceLoaderAware` loads the config file for that profile, `ApplicationEventPublisherAware` broadcasts a `ConfigReadyEvent` so other beans (the `StartupReporter`) can react. Missing config produces `validated=false` in the event.

## 6. Walkthrough

**Level 3 PROD run sequence:**

```
new SmartConfigService()                        ← ① constructor

[injection: none in this example]               ← ② inject

Aware setters (in order):
  setEnvironment(env)                           ← ③a EnvironmentAware
    env = FakeEnv(profiles=["prod"], ...)
    awareLog=["EnvironmentAware"]

  setResourceLoader(rl)                         ← ③b ResourceLoaderAware
    rl = FakeRL({classpath:config-prod.yaml → "feature.x:true\n..."})
    awareLog=["EnvironmentAware","ResourceLoaderAware"]

  setApplicationEventPublisher(pub)             ← ③c ApplicationEventPublisherAware
    publisher = pub
    awareLog=["EnvironmentAware","ResourceLoaderAware","ApplicationEventPublisherAware"]

svc.postConstruct():                            ← ④ @PostConstruct
  profile    = "prod"
  configFile = "classpath:config-prod.yaml"
  content    = rl.load("classpath:config-prod.yaml")
             = "feature.x: true\ndb.pool: 20"
  valid      = true
  publisher.publishEvent(ConfigReadyEvent("prod", "feature.x:...", true))
    → StartupReporter.onConfigReady(event)
      log.add("Config ready for profile=prod validated=true")

[REPORTER LOG] [Config ready for profile=prod validated=true,
                Config ready for profile=dev validated=false]
```

## 7. Gotchas & takeaways

> **`EmbeddedValueResolverAware` is the right choice when you need to resolve `${property}` or `#{expression}` strings programmatically** — for example, in a framework component that processes annotation attributes containing property placeholders. It does exactly what `@Value` does, but on a `String` you provide at runtime.

> **`@Autowired ResourceLoader rl` and `ResourceLoaderAware` are equivalent for `@Component` beans** — Spring auto-detects `ResourceLoader` as an injectable type. Use the `@Autowired` form for application code; use `ResourceLoaderAware` for framework components or base classes that can't use field injection.

- `Environment.acceptsProfiles(Profiles.of("prod | dev"))` supports logical expressions — OR, AND, NOT — for complex profile conditions.
- `ResourceLoader.getResource("classpath*:META-INF/*.yaml")` (with `*`) returns multiple resources; the simpler `ResourceLoader` returns only one. For multi-resource loading, use `ResourcePatternResolver` (a sub-interface), which `ApplicationContext` implements.
- `ApplicationEventPublisher` is a narrower interface than `ApplicationContext` — it exposes only `publishEvent()`. Prefer it over `ApplicationContextAware` when event publishing is all you need.
- `MessageSourceAware` is rarely needed directly — use `@Autowired MessageSource ms` or call `ctx.getMessage()` if you have `ApplicationContextAware`. Use `MessageSourceAware` only in framework beans that must remain loosely coupled to the context.
