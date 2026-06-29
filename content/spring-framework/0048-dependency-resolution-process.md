---
card: spring-framework
gi: 48
slug: dependency-resolution-process
title: Dependency resolution process
---

## 1. What it is

The **dependency resolution process** is the multi-step algorithm Spring runs during container startup to wire all beans together. It happens as part of `AbstractApplicationContext.refresh()` and consists of:

1. **Load and parse `BeanDefinition` objects** from all config sources (XML, annotations, Java config).
2. **Build a complete dependency graph** — for each bean, determine what it needs before it can be created.
3. **Detect potential problems** — circular constructor dependencies, missing required beans, ambiguous matches.
4. **Instantiate beans in dependency order** — dependencies first, then the bean that needs them.
5. **Inject** via constructor, setter, or field.

```
BeanDefinitionReader → BeanDefinition registry
                     → dependency graph
                     → topological sort
                     → instantiation in order
                     → injection
                     → @PostConstruct
                     → ready
```

In one sentence: **The dependency resolution process is how Spring parses configuration, builds a dependency graph, and instantiates beans in the correct order so that every injected dependency is ready before the bean that needs it is created.**

## 2. Why & when

Understanding resolution helps when:

- Debugging `UnsatisfiedDependencyException` — which bean is missing and why.
- Diagnosing slow context startup — many beans with deep dependency chains.
- Understanding why `@Lazy` or `@DependsOn` exists — some dependencies are not inferrable from injection points alone.
- Reasoning about `BeanPostProcessor` and `BeanFactoryPostProcessor` — they must be created early, before regular beans.

## 3. Core concept

```
Resolution pipeline (simplified):

  Step 1: Parse config
    @ComponentScan → find @Component classes → register BeanDefinitions
    @Configuration → find @Bean methods → register BeanDefinitions
    (All defs registered BEFORE any bean is created)

  Step 2: Resolve BeanFactoryPostProcessors first
    Process @PropertySource, ${...} expressions, etc.

  Step 3: Register BeanPostProcessors
    AutowiredAnnotationBeanPostProcessor (handles @Autowired)
    etc.

  Step 4: Pre-instantiate singletons (eager)
    For each non-lazy singleton BeanDefinition:
      a. Find all its injection points (constructor params, @Autowired fields, setters)
      b. For each injection point, find a matching bean:
           type match → 1 candidate → use it
                      → 0 → NoSuchBeanDefinitionException
                      → >1 → check @Primary, @Qualifier → or NoUniqueBeanDefinitionException
      c. Ensure the dependency bean is created first (recursive)
      d. Create this bean, inject deps, run @PostConstruct
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dependency resolution pipeline: parse config, build dependency graph, instantiate in topological order">
  <defs>
    <marker id="a48" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- 5 pipeline steps -->
  <rect x="10"  y="60" width="110" height="88" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65"  y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. Parse</text>
  <text x="65"  y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">BeanDefinitions</text>
  <text x="65"  y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">from XML /</text>
  <text x="65"  y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">annotations</text>

  <rect x="140" y="60" width="110" height="88" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="195" y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2. BeanFactory</text>
  <text x="195" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">PostProcessors</text>
  <text x="195" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">${...} resolved</text>
  <text x="195" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">profiles applied</text>

  <rect x="270" y="60" width="110" height="88" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="84" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">3. BeanPost</text>
  <text x="325" y="100" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">Processors reg.</text>
  <text x="325" y="116" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="325" y="132" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">processor ready</text>

  <rect x="400" y="60" width="110" height="88" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="455" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">4. Resolve deps</text>
  <text x="455" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">type/name/qual</text>
  <text x="455" y="116" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">dep order</text>
  <text x="455" y="132" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">detect circular</text>

  <rect x="530" y="60" width="140" height="88" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="600" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">5. Instantiate</text>
  <text x="600" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">new Bean(deps)</text>
  <text x="600" y="116" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">inject setters</text>
  <text x="600" y="132" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@PostConstruct</text>

  <line x1="120" y1="104" x2="137" y2="104" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>
  <line x1="250" y1="104" x2="267" y2="104" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>
  <line x1="380" y1="104" x2="397" y2="104" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a48)"/>
  <line x1="510" y1="104" x2="527" y2="104" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a48)"/>

  <text x="340" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">AbstractApplicationContext.refresh() — all 5 steps run at startup</text>
  <text x="340" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Beans are created in dependency order: leaf deps first, their consumers second.</text>
</svg>

Steps 1–3 happen before any application bean is instantiated. Step 4 resolves the dependency graph. Step 5 creates beans in topological order.

## 5. Runnable example

Scenario: a three-tier application (`Repository → Service → Controller`). Show the dependency graph, resolution order, and what happens when a dependency is missing.

### Level 1 — Basic

Linear three-tier dependency chain: Repository → Service → Controller.

```java
// DepResolutionDemo.java — run with: java DepResolutionDemo.java
import java.util.*;

public class DepResolutionDemo {

    // --- Beans ---
    static class OrderRepository {
        OrderRepository() { System.out.println("  [CREATED] OrderRepository"); }
        List<String> findAll() { return List.of("ORD-001", "ORD-002", "ORD-003"); }
    }

    static class OrderService {
        private final OrderRepository repository;
        OrderService(OrderRepository repository) {
            System.out.println("  [CREATED] OrderService ← OrderRepository");
            this.repository = repository;
        }
        List<String> listOrders() { return repository.findAll(); }
    }

    static class OrderController {
        private final OrderService service;
        OrderController(OrderService service) {
            System.out.println("  [CREATED] OrderController ← OrderService");
            this.service = service;
        }
        String handleRequest() { return "Orders: " + service.listOrders(); }
    }

    // --- Container with dependency graph ---
    static class BeanDef {
        final String name;
        final Class<?> type;
        final List<String> dependsOn;  // bean names it needs

        BeanDef(String name, Class<?> type, String... deps) {
            this.name = name; this.type = type; this.dependsOn = List.of(deps);
        }
    }

    static class Ctx {
        private final Map<String, BeanDef>  defs  = new LinkedHashMap<>();
        private final Map<String, Object>   beans = new LinkedHashMap<>();
        private final List<String>          order = new ArrayList<>();

        void define(BeanDef def) { defs.put(def.name, def); }

        void refresh() throws Exception {
            System.out.println("  [CTX] Building dependency graph...");
            // Topological sort: for each bean, ensure its deps are created first
            Set<String> visited  = new LinkedHashSet<>();
            Set<String> creating = new LinkedHashSet<>();
            for (String name : defs.keySet()) {
                instantiate(name, visited, creating);
            }
        }

        private void instantiate(String name, Set<String> visited, Set<String> creating) throws Exception {
            if (visited.contains(name)) return;
            if (creating.contains(name))
                throw new RuntimeException("Circular dependency detected: " + creating + " → " + name);

            BeanDef def = defs.get(name);
            if (def == null) throw new RuntimeException("No bean defined: " + name);

            creating.add(name);
            // Recurse: ensure all deps created first
            for (String dep : def.dependsOn) {
                instantiate(dep, visited, creating);
            }
            creating.remove(name);

            // All deps are ready — create this bean
            Object[] depBeans = def.dependsOn.stream().map(beans::get).toArray();
            Object bean = createBean(def.type, depBeans);
            beans.put(name, bean);
            visited.add(name);
            order.add(name);
        }

        private Object createBean(Class<?> type, Object... args) throws Exception {
            if (args.length == 0) return type.getDeclaredConstructors()[0].newInstance();
            return type.getDeclaredConstructors()[0].newInstance(args);
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
        List<String> getCreationOrder() { return order; }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();
        System.out.println("=== Phase 1: Register BeanDefinitions ===");
        ctx.define(new BeanDef("orderController", OrderController.class, "orderService"));
        ctx.define(new BeanDef("orderService",    OrderService.class,    "orderRepository"));
        ctx.define(new BeanDef("orderRepository", OrderRepository.class));
        System.out.println("  Defined: orderController, orderService, orderRepository");

        System.out.println("\n=== Phase 2: Refresh (dependency resolution + instantiation) ===");
        ctx.refresh();

        System.out.println("\n=== Creation order ===");
        System.out.println("  " + ctx.getCreationOrder());

        System.out.println("\n=== Application running ===");
        OrderController ctrl = ctx.getBean("orderController");
        System.out.println("  " + ctrl.handleRequest());
    }
}
```

How to run: `java DepResolutionDemo.java`

The definitions are registered in reverse dependency order (controller first), but the container resolves them in the correct order: `orderRepository` → `orderService` → `orderController`. The topological sort ensures each bean's dependencies are created before the bean itself.

### Level 2 — Intermediate

Missing dependency detection and `@Primary`-style disambiguation for multiple candidates.

```java
// DepResolutionDemo2.java — run with: java DepResolutionDemo2.java
import java.util.*;

public class DepResolutionDemo2 {

    interface NotificationChannel { void send(String msg); }

    static class EmailChannel implements NotificationChannel {
        final boolean isPrimary;
        EmailChannel(boolean isPrimary) {
            System.out.println("  [CREATED] EmailChannel(primary=" + isPrimary + ")");
            this.isPrimary = isPrimary;
        }
        @Override public void send(String msg) { System.out.println("  [EMAIL] " + msg); }
    }

    static class SmsChannel implements NotificationChannel {
        SmsChannel() { System.out.println("  [CREATED] SmsChannel"); }
        @Override public void send(String msg) { System.out.println("  [SMS] " + msg); }
    }

    static class AlertService {
        private final NotificationChannel channel;
        AlertService(NotificationChannel channel) {
            System.out.println("  [CREATED] AlertService ← " + channel.getClass().getSimpleName());
            this.channel = channel;
        }
        void alert(String msg) { channel.send("[ALERT] " + msg); }
    }

    static class BeanDef {
        final String   name;
        final Object   instance;
        final Class<?> type;
        final boolean  primary;
        BeanDef(String n, Object inst, Class<?> type, boolean primary) {
            this.name = n; this.instance = inst; this.type = type; this.primary = primary;
        }
    }

    static class Ctx {
        final List<BeanDef>      defs  = new ArrayList<>();
        final Map<String,Object> beans = new LinkedHashMap<>();

        void register(BeanDef d) { defs.add(d); beans.put(d.name, d.instance); }

        <T> T resolveByType(Class<T> type) {
            List<BeanDef> candidates = defs.stream()
                .filter(d -> type.isAssignableFrom(d.type)).toList();
            if (candidates.isEmpty())
                throw new RuntimeException("NoSuchBeanDefinitionException: no bean of type " + type.getSimpleName());
            if (candidates.size() == 1)
                return type.cast(candidates.get(0).instance);
            // Multiple candidates — check @Primary
            var primary = candidates.stream().filter(d -> d.primary).toList();
            if (primary.size() == 1) {
                System.out.println("  [CTX] type ambiguity resolved via @Primary → " + primary.get(0).name);
                return type.cast(primary.get(0).instance);
            }
            throw new RuntimeException("NoUniqueBeanDefinitionException: " + candidates.size()
                + " beans of type " + type.getSimpleName() + " (none/multiple @Primary)");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Scenario 1: no candidates → NoSuchBeanDefinitionException ===");
        Ctx c1 = new Ctx();
        try {
            c1.resolveByType(NotificationChannel.class);
        } catch (RuntimeException e) {
            System.out.println("  " + e.getMessage());
        }

        System.out.println("\n=== Scenario 2: multiple candidates, no @Primary → ambiguous ===");
        Ctx c2 = new Ctx();
        c2.register(new BeanDef("emailChannel", new EmailChannel(false), EmailChannel.class, false));
        c2.register(new BeanDef("smsChannel",   new SmsChannel(),        SmsChannel.class,   false));
        try {
            c2.resolveByType(NotificationChannel.class);
        } catch (RuntimeException e) {
            System.out.println("  " + e.getMessage());
        }

        System.out.println("\n=== Scenario 3: multiple candidates, one @Primary → resolved ===");
        Ctx c3 = new Ctx();
        c3.register(new BeanDef("emailChannel", new EmailChannel(true),  EmailChannel.class, true));
        c3.register(new BeanDef("smsChannel",   new SmsChannel(),        SmsChannel.class,   false));

        NotificationChannel ch = c3.resolveByType(NotificationChannel.class);
        AlertService svc = new AlertService(ch);
        svc.alert("Server CPU > 90%");
    }
}
```

How to run: `java DepResolutionDemo2.java`

Three scenarios: no bean (throws), ambiguous (throws), one primary (resolved). The container uses `@Primary` as the tiebreaker when type alone is ambiguous. Scenario 3 resolves to `EmailChannel` and the alert is sent.

### Level 3 — Advanced

Full resolution pipeline with `BeanFactoryPostProcessor` pre-processing and `BeanPostProcessor` wrapping.

```java
// DepResolutionDemo3.java — run with: java DepResolutionDemo3.java
import java.util.*;

public class DepResolutionDemo3 {

    // BeanDefinition
    record Def(String name, Map<String, String> props, List<String> deps) {}

    // Interfaces for pipeline hooks
    interface BeanFactoryPostProcessor { void postProcess(Map<String, Def> defs, Map<String, String> props); }
    interface BeanPostProcessor        { Object wrapBean(String name, Object bean); }

    // --- Beans ---
    static class DataSource {
        final String url; final int maxConn;
        DataSource(String url, int maxConn) {
            System.out.println("  [CREATED] DataSource(url=" + url + " maxConn=" + maxConn + ")");
            this.url = url; this.maxConn = maxConn;
        }
    }

    static class UserRepository {
        final DataSource ds;
        UserRepository(DataSource ds) {
            System.out.println("  [CREATED] UserRepository ← DataSource");
            this.ds = ds;
        }
        String findUser(String id) { return "User{id=" + id + " via=" + ds.url + "}"; }
    }

    static class UserService {
        final UserRepository repo;
        UserService(UserRepository repo) {
            System.out.println("  [CREATED] UserService ← UserRepository");
            this.repo = repo;
        }
        String getUser(String id) { return repo.findUser(id); }
    }

    // --- Pipeline hooks ---
    static class PropertyResolvingBFPP implements BeanFactoryPostProcessor {
        private final Map<String, String> envProps;
        PropertyResolvingBFPP(Map<String, String> envProps) { this.envProps = envProps; }
        @Override
        public void postProcess(Map<String, Def> defs, Map<String, String> props) {
            System.out.println("  [BFPP] Resolving ${...} variables");
            props.replaceAll((k, v) -> {
                for (var e : envProps.entrySet()) {
                    v = v.replace("${" + e.getKey() + "}", e.getValue());
                }
                return v;
            });
        }
    }

    static class TimingBPP implements BeanPostProcessor {
        @Override
        public Object wrapBean(String name, Object bean) {
            System.out.println("  [BPP] TimingBPP applied to '" + name + "'");
            return bean;  // in real Spring, returns a proxy; simplified here
        }
    }

    // --- Minimal container with resolution pipeline ---
    static class Ctx {
        final Map<String, Def>    defs    = new LinkedHashMap<>();
        final Map<String, String> props   = new HashMap<>();
        final List<BeanFactoryPostProcessor> bfpps = new ArrayList<>();
        final List<BeanPostProcessor>        bpps  = new ArrayList<>();
        final Map<String, Object>            beans = new LinkedHashMap<>();
        final List<String>                   order = new ArrayList<>();

        void define(Def d)  { defs.put(d.name(), d); }
        void property(String k, String v) { props.put(k, v); }
        void addBFPP(BeanFactoryPostProcessor p) { bfpps.add(p); }
        void addBPP(BeanPostProcessor p)          { bpps.add(p); }

        void refresh() throws Exception {
            System.out.println("\n  [PHASE 1] BeanFactoryPostProcessors");
            for (var p : bfpps) p.postProcess(defs, props);

            System.out.println("\n  [PHASE 2] Register BeanPostProcessors (ready)");

            System.out.println("\n  [PHASE 3] Pre-instantiate singletons");
            Set<String> done = new LinkedHashSet<>();
            Set<String> seen = new LinkedHashSet<>();
            for (String name : defs.keySet()) instantiate(name, done, seen);
        }

        private void instantiate(String name, Set<String> done, Set<String> seen) throws Exception {
            if (done.contains(name)) return;
            if (seen.contains(name)) throw new RuntimeException("Circular: " + seen + " → " + name);
            seen.add(name);
            Def d = defs.get(name);
            for (String dep : d.deps()) instantiate(dep, done, seen);
            seen.remove(name);

            // Resolve ${...} in props for this bean
            Map<String, String> resolved = new HashMap<>();
            d.props().forEach((k, v) -> resolved.put(k, resolveValue(v)));

            Object bean = createBean(name, resolved);

            // Apply BeanPostProcessors
            for (var bpp : bpps) bean = bpp.wrapBean(name, bean);

            beans.put(name, bean);
            done.add(name);
            order.add(name);
        }

        private String resolveValue(String v) {
            return props.getOrDefault(v, v.replace("${", "").replace("}", ""));
        }

        private Object createBean(String name, Map<String, String> p) throws Exception {
            Def d = defs.get(name);
            Object[] depBeans = d.deps().stream().map(beans::get).toArray();
            return switch (name) {
                case "dataSource" -> new DataSource(p.get("url"), Integer.parseInt(p.get("maxConn")));
                case "userRepository" -> new UserRepository((DataSource) depBeans[0]);
                case "userService"    -> new UserService((UserRepository) depBeans[0]);
                default -> throw new RuntimeException("Unknown bean: " + name);
            };
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) throws Exception {
        Ctx ctx = new Ctx();

        System.out.println("=== Phase 0: Register defs + properties ===");
        // Properties with ${...} variables
        ctx.property("db.url",     "${env.DB_HOST}:5432/app");
        ctx.property("db.maxConn", "20");

        ctx.define(new Def("userService",    Map.of(), List.of("userRepository")));
        ctx.define(new Def("userRepository", Map.of(), List.of("dataSource")));
        ctx.define(new Def("dataSource",
            Map.of("url", "jdbc:postgresql://${env.DB_HOST}:5432/app", "maxConn", "20"),
            List.of()));

        // BFPP resolves ${env.DB_HOST} → actual value
        ctx.addBFPP(new PropertyResolvingBFPP(Map.of("env.DB_HOST", "prod-db-01.internal")));
        ctx.addBPP(new TimingBPP());

        System.out.println("=== Refresh ===");
        ctx.refresh();

        System.out.println("\n=== Creation order ===");
        System.out.println("  " + ctx.order);

        System.out.println("\n=== Application running ===");
        UserService svc = ctx.getBean("userService");
        System.out.println("  " + svc.getUser("alice"));
    }
}
```

How to run: `java DepResolutionDemo3.java`

Three phases: (1) `BeanFactoryPostProcessor` resolves `${env.DB_HOST}` before any bean is created, (2) `BeanPostProcessor` wraps each bean after creation, (3) beans are created in dependency order: `dataSource` → `userRepository` → `userService`. The resolved URL `jdbc:postgresql://prod-db-01.internal:5432/app` is injected into `DataSource`.

## 6. Walkthrough

**Level 3 — resolution order:**

```
Phase 1 (BFPP):
  props["db.url"] = "${env.DB_HOST}:5432/app" → not directly used
  dataSource props["url"] = "jdbc:postgresql://${env.DB_HOST}:5432/app"
    → resolves to "jdbc:postgresql://prod-db-01.internal:5432/app"

Phase 3 (pre-instantiate singletons):
  instantiate("userService"):
    dep="userRepository" → not done → recurse
    instantiate("userRepository"):
      dep="dataSource" → not done → recurse
      instantiate("dataSource"):
        no deps → create DataSource("jdbc:...prod-db-01...", 20)
        BPP.wrapBean("dataSource", bean) → TimingBPP logged
        done["dataSource"] = bean
      create UserRepository(dataSource)
      done["userRepository"] = bean
    create UserService(userRepository)
    done["userService"] = bean

Order: [dataSource, userRepository, userService]
```

## 7. Gotchas & takeaways

> **`BeanDefinition` objects are parsed eagerly but beans are created lazily by default in XML, or eagerly for `@Component` singletons.** Adding `@Lazy` to a bean delays creation until first `getBean()` call — missing deps are then detected at request time, not startup time.

> **`BeanFactoryPostProcessor` beans are created before regular beans.** If a `BeanFactoryPostProcessor` has a dependency on a regular bean, that regular bean is also created early — it escapes normal lifecycle ordering. Avoid injecting non-infrastructure beans into `BeanFactoryPostProcessor` implementations.

- Spring's actual resolution uses `DefaultListableBeanFactory.preInstantiateSingletons()` which iterates the definition map and calls `getBean(name)` for each non-lazy singleton.
- `@DependsOn("beanA")` is a signal to Spring that this bean needs `beanA` to be initialized first, even if there's no injection relationship — useful for initializing shared resources (e.g., a database migration bean that must run before any repository).
- `UnsatisfiedDependencyException` is the most common resolution failure: it wraps the actual `NoSuchBeanDefinitionException` and names both the failing bean and the injection point.
