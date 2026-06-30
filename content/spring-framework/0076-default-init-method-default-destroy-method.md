---
card: spring-framework
gi: 76
slug: default-init-method-default-destroy-method
title: default-init-method / default-destroy-method
---

## 1. What it is

`default-init-method` and `default-destroy-method` are **XML `<beans>` element attributes** that apply a lifecycle method name as a global default to every `<bean>` in that file — without you having to repeat `init-method` / `destroy-method` on each bean. Any bean in the file that has a method matching the default name gets it wired automatically; beans that don't have the method are silently skipped.

```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       default-init-method="init"
       default-destroy-method="destroy">

    <!-- Spring calls init() on this bean at startup if it exists -->
    <bean id="dataSource" class="com.example.SimpleDataSource"/>

    <!-- Per-bean override wins — Spring calls open() / close() here -->
    <bean id="cache" class="com.example.LocalCache"
          init-method="open" destroy-method="close"/>

    <!-- No init/destroy method in this class — silently skipped -->
    <bean id="config" class="com.example.AppConfig"/>
</beans>
```

In one sentence: **`default-init-method` / `default-destroy-method` on the `<beans>` root element auto-wire a lifecycle method by name to every bean in that XML file — a DRY way to enforce a naming convention without repeating attributes on each bean.**

## 2. Why & when

Use global defaults when:

- You have many beans that all follow the **same naming convention** — e.g., every service class has `void init()` and `void destroy()`.
- You are migrating a legacy codebase to Spring and the beans already have init/destroy methods by convention.
- You want to enforce a team standard without requiring annotations or interface implementations.

Don't use global defaults when:

- Most beans have different lifecycle method names — it becomes confusing.
- You use annotation-driven configuration (`@Bean`) — global defaults are XML-only; `@Bean(initMethod=..., destroyMethod=...)` is the per-bean equivalent.

Per-bean `init-method` / `destroy-method` always **override** the global default for that specific bean.

## 3. Core concept

```
<beans default-init-method="init" default-destroy-method="destroy">

For EACH <bean> in this file, Spring checks at startup:
  → Does the class have a public void no-arg method named "init"?
    YES → wire it as init-method (called after @PostConstruct and afterPropertiesSet)
    NO  → silently skip (no error)

  → Per-bean override: <bean init-method="open"> overrides "init" for that bean only

Precedence (highest to lowest):
  1. Per-bean init-method="..." attribute    — explicit override
  2. default-init-method="..." on <beans>   — file-level default
  3. Nothing                                — no init callback

Does NOT apply to:
  ✗ @Component / @Service / @Repository beans (annotation-scanned)
  ✗ @Bean factory methods — use @Bean(initMethod="...", destroyMethod="...")
  ✓ <bean> elements in the same XML file (including imported files IF they share the <beans> root)

Same mechanics as per-bean init-method:
  Fires after: @PostConstruct → afterPropertiesSet() → default-init-method (LAST)
  Destroy fires: @PreDestroy → DisposableBean.destroy() → default-destroy-method (LAST)
```

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="default-init-method scope and precedence">
  <defs>
    <marker id="a76" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="193" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">default-init-method / default-destroy-method — file-level fallback, per-bean overrides win</text>

  <!-- <beans> wrapper -->
  <rect x="15" y="32" width="648" height="100" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="30" y="48" fill="#6db33f" font-size="9" font-family="monospace">&lt;beans default-init-method="init" default-destroy-method="destroy"&gt;</text>

  <!-- Bean A: uses default -->
  <rect x="30"  y="55" width="185" height="68" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="122" y="73" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">SimpleDataSource</text>
  <text x="122" y="87" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">has init() → wired ✓</text>
  <text x="122" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">has destroy() → wired ✓</text>
  <text x="122" y="113" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">uses default</text>

  <!-- Bean B: override -->
  <rect x="230" y="55" width="185" height="68" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="322" y="73" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">LocalCache</text>
  <text x="322" y="87" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">init-method="open" → wired ✓</text>
  <text x="322" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">destroy-method="close" → wired ✓</text>
  <text x="322" y="113" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">per-bean override wins</text>

  <!-- Bean C: no method -->
  <rect x="430" y="55" width="185" height="68" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="522" y="73" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">AppConfig</text>
  <text x="522" y="87" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">no init() → silently skipped</text>
  <text x="522" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">no destroy() → silently skipped</text>
  <text x="522" y="113" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no callback</text>

  <text x="640" y="127" fill="#6db33f" font-size="9" font-family="monospace">&lt;/beans&gt;</text>

  <!-- Precedence table -->
  <rect x="10" y="142" width="655" height="48" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="158" fill="#8b949e" font-size="9" font-family="monospace">Precedence:  per-bean init-method  &gt;  default-init-method  &gt;  nothing</text>
  <text x="22" y="174" fill="#8b949e" font-size="9" font-family="monospace">Scope:       XML &lt;bean&gt; elements only — NOT @Bean / @Component / @Service</text>
  <text x="22" y="184" fill="#8b949e" font-size="7" font-family="sans-serif"> </text>
</svg>

Global defaults apply file-wide; per-bean attributes override them; beans lacking the method are silently skipped.

## 5. Runnable example

Scenario: a configuration center with three service beans that all follow an `init()` / `destroy()` naming convention — Spring picks them up via the global default.

### Level 1 — Basic

Three beans with `init()` / `destroy()` — the global default wires all of them.

```java
// DefaultInitDestroyDemo.java — run with: java DefaultInitDestroyDemo.java
import java.util.*;

public class DefaultInitDestroyDemo {

    // ── three "service" beans — no Spring imports ─────────────────────
    static class DatabasePool {
        private boolean open = false;
        DatabasePool() { System.out.println("  [CONSTRUCT] DatabasePool"); }
        public void init()    { open = true;  System.out.println("  [default-init]    DatabasePool.init() — connections opened"); }
        public void destroy() { open = false; System.out.println("  [default-destroy] DatabasePool.destroy() — connections closed"); }
        boolean isOpen() { return open; }
    }

    static class CacheManager {
        private int entries = 0;
        CacheManager() { System.out.println("  [CONSTRUCT] CacheManager"); }
        public void init()    { entries = 100; System.out.println("  [default-init]    CacheManager.init() — " + entries + " entries preloaded"); }
        public void destroy() { entries = 0;   System.out.println("  [default-destroy] CacheManager.destroy() — cache evicted"); }
        int entries() { return entries; }
    }

    static class MessageRouter {
        private boolean running = false;
        MessageRouter() { System.out.println("  [CONSTRUCT] MessageRouter"); }
        public void init()    { running = true;  System.out.println("  [default-init]    MessageRouter.init() — routing started"); }
        public void destroy() { running = false; System.out.println("  [default-destroy] MessageRouter.destroy() — routing stopped"); }
        boolean isRunning() { return running; }
    }

    // ── AppConfig: no init() / destroy() — silently skipped ───────────
    static class AppConfig {
        private final String env;
        AppConfig(String env) { this.env = env; System.out.println("  [CONSTRUCT] AppConfig env=" + env + " (no init/destroy — skipped)"); }
        String env() { return env; }
    }

    // ── simulated container: calls init() on all beans that have it ───
    @FunctionalInterface interface Lifecycle { void run() throws Exception; }

    static void withContainer(Runnable app, Object... beans) {
        List<Runnable> inits    = new ArrayList<>();
        List<Runnable> destroys = new ArrayList<>();

        for (Object b : beans) {
            try {
                try { var m = b.getClass().getMethod("init");    inits.add(()    -> { try { m.invoke(b); } catch (Exception e) { throw new RuntimeException(e); } }); } catch (NoSuchMethodException ignored) {}
                try { var m = b.getClass().getMethod("destroy"); destroys.add(() -> { try { m.invoke(b); } catch (Exception e) { throw new RuntimeException(e); } }); } catch (NoSuchMethodException ignored) {}
            } catch (Exception e) { throw new RuntimeException(e); }
        }

        System.out.println("  [container] calling default-init-method='init' on all beans...");
        inits.forEach(Runnable::run);
        System.out.println("  [container] all beans ready\n");

        app.run();

        System.out.println("\n  [container] context.close() — calling default-destroy-method='destroy':");
        Collections.reverse(destroys); // reverse of init order
        destroys.forEach(Runnable::run);
        System.out.println("  [container] shutdown complete");
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        var db     = new DatabasePool();
        var cache  = new CacheManager();
        var router = new MessageRouter();
        var config = new AppConfig("production");

        withContainer(() -> {
            System.out.println("[APP] db.open=" + db.isOpen()
                + " cache.entries=" + cache.entries()
                + " router.running=" + router.isRunning()
                + " config.env=" + config.env());
        }, db, cache, router, config); // AppConfig has no init/destroy → skipped
    }
}
```

How to run: `java DefaultInitDestroyDemo.java`

The container uses reflection to call `init()` on every bean that has it — `AppConfig` has no `init()` so it is silently skipped. Destroy fires in reverse order. This mirrors exactly what Spring does when `default-init-method="init"` and `default-destroy-method="destroy"` are set on `<beans>`.

### Level 2 — Intermediate

Per-bean `init-method` overrides the global default — `LocalCache` uses `open()` / `close()` instead of `init()` / `destroy()`.

```java
// DefaultInitDestroyDemo2.java — run with: java DefaultInitDestroyDemo2.java
import java.util.*;
import java.lang.reflect.*;

public class DefaultInitDestroyDemo2 {

    // ── beans that follow the convention ──────────────────────────────
    static class UserRepository {
        private boolean connected = false;
        UserRepository() { System.out.println("  [CONSTRUCT] UserRepository"); }
        public void init()    { connected = true;  System.out.println("  [default-init]    UserRepository.init() — DB connected"); }
        public void destroy() { connected = false; System.out.println("  [default-destroy] UserRepository.destroy() — connection closed"); }
        boolean isConnected() { return connected; }
    }

    static class EmailService {
        private String smtpHost;
        EmailService(String smtpHost) { this.smtpHost = smtpHost; System.out.println("  [CONSTRUCT] EmailService smtp=" + smtpHost); }
        public void init()    { System.out.println("  [default-init]    EmailService.init() — SMTP verified at " + smtpHost); }
        public void destroy() { System.out.println("  [default-destroy] EmailService.destroy() — SMTP connection released"); }
    }

    // ── bean with a DIFFERENT method name — per-bean override needed ──
    static class LocalCache {
        private int size = 0;
        LocalCache() { System.out.println("  [CONSTRUCT] LocalCache (uses open/close — NOT init/destroy)"); }
        public void open()    { size = 50; System.out.println("  [per-bean-init]    LocalCache.open() — " + size + " entries loaded"); }
        public void close()   { size = 0;  System.out.println("  [per-bean-destroy] LocalCache.close() — cache cleared"); }
        int size() { return size; }
    }

    // ── minimal container that respects per-bean overrides ────────────
    record BeanDef(Object instance, String initMethod, String destroyMethod) {}

    static void runContainer(List<BeanDef> defs, Runnable app) {
        String DEFAULT_INIT    = "init";
        String DEFAULT_DESTROY = "destroy";

        List<Runnable> inits    = new ArrayList<>();
        List<Runnable> destroys = new ArrayList<>();

        for (BeanDef def : defs) {
            Object b    = def.instance();
            String im   = def.initMethod()    != null ? def.initMethod()    : DEFAULT_INIT;
            String dm   = def.destroyMethod() != null ? def.destroyMethod() : DEFAULT_DESTROY;
            try {
                try { Method m = b.getClass().getMethod(im);  inits.add(()    -> { try { m.invoke(b); } catch (Exception e) { throw new RuntimeException(e); } }); }
                catch (NoSuchMethodException ignored) { inits.add(() -> {}); }
                try { Method m = b.getClass().getMethod(dm); destroys.add(() -> { try { m.invoke(b); } catch (Exception e) { throw new RuntimeException(e); } }); }
                catch (NoSuchMethodException ignored) { destroys.add(() -> {}); }
            } catch (Exception e) { throw new RuntimeException(e); }
        }

        System.out.println("  [container] startup:");
        inits.forEach(Runnable::run);
        System.out.println("  [container] all ready\n");

        app.run();

        System.out.println("\n  [container] shutdown:");
        List<Runnable> rev = new ArrayList<>(destroys);
        Collections.reverse(rev);
        rev.forEach(Runnable::run);
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting (default-init-method=init, default-destroy-method=destroy) ===");

        UserRepository repo  = new UserRepository();
        EmailService   email = new EmailService("smtp.company.com");
        LocalCache     cache = new LocalCache();

        List<BeanDef> defs = List.of(
            new BeanDef(repo,  null,    null),    // uses default: init / destroy
            new BeanDef(email, null,    null),    // uses default: init / destroy
            new BeanDef(cache, "open",  "close")  // per-bean override: open / close
        );

        runContainer(defs, () -> {
            System.out.println("[APP] repo.connected=" + repo.isConnected()
                + " cache.size=" + cache.size());
        });
    }
}
```

How to run: `java DefaultInitDestroyDemo2.java`

`UserRepository` and `EmailService` pick up the global defaults (`init` / `destroy`). `LocalCache` has a per-bean override (`open` / `close`) — the override wins. The container resolves each bean's lifecycle method at startup using the per-bean value if present, or the global default if not.

### Level 3 — Advanced

Global defaults across multiple XML files (simulated) — beans in imported files also pick up the outer `<beans>` defaults, and we show override precedence clearly.

```java
// DefaultInitDestroyDemo3.java — run with: java DefaultInitDestroyDemo3.java
import java.util.*;
import java.lang.reflect.*;

public class DefaultInitDestroyDemo3 {

    // ── "infrastructure" beans (imagine imported XML) ─────────────────
    static class JdbcPool {
        private int openConns = 0;
        JdbcPool() { System.out.println("  [CONSTRUCT] JdbcPool"); }
        public void init()    { openConns = 10; System.out.println("  [default-init]    JdbcPool.init() — " + openConns + " connections"); }
        public void destroy() { openConns = 0;  System.out.println("  [default-destroy] JdbcPool.destroy() — " + openConns + " connections"); }
        int conns() { return openConns; }
    }

    static class MqBroker {
        private boolean active = false;
        MqBroker() { System.out.println("  [CONSTRUCT] MqBroker"); }
        public void init()    { active = true;  System.out.println("  [default-init]    MqBroker.init() — broker active"); }
        public void destroy() { active = false; System.out.println("  [default-destroy] MqBroker.destroy() — broker stopped"); }
        boolean isActive() { return active; }
    }

    // ── "application" beans ───────────────────────────────────────────
    static class OrderService {
        private final JdbcPool  pool;
        private final MqBroker  mq;
        private int             processed = 0;
        OrderService(JdbcPool p, MqBroker m) {
            this.pool = p; this.mq = m;
            System.out.println("  [CONSTRUCT] OrderService (pool.conns=" + p.conns() + " mq.active=" + m.isActive() + ")");
        }
        // follows convention
        public void init()    { System.out.printf("  [default-init]    OrderService.init() — ready (pool=%d mq=%s)%n", pool.conns(), mq.isActive()); }
        public void destroy() { System.out.printf("  [default-destroy] OrderService.destroy() — processed=%d%n", processed); }
        void process(String id) { processed++; System.out.println("  [PROCESS] order " + id + " (#" + processed + ")"); }
    }

    // ── bean that uses different names — per-bean override ─────────────
    static class AuditLogger {
        private final List<String> log = new ArrayList<>();
        AuditLogger() { System.out.println("  [CONSTRUCT] AuditLogger (uses start/stop, not init/destroy)"); }
        public void start() { System.out.println("  [per-bean-init]    AuditLogger.start() — audit log opened"); }
        public void stop()  { System.out.println("  [per-bean-destroy] AuditLogger.stop() — audit log closed (" + log.size() + " entries)"); }
        void audit(String msg) { log.add(msg); }
    }

    // ── bean with NO lifecycle methods — silently skipped ─────────────
    static class AppProperties {
        private final Map<String, String> props;
        AppProperties(Map<String, String> props) {
            this.props = props;
            System.out.println("  [CONSTRUCT] AppProperties (no lifecycle methods — silently skipped)");
        }
        String get(String k) { return props.getOrDefault(k, ""); }
    }

    // ── Container: resolves method names with precedence ──────────────
    record BeanReg(Object bean, String initOverride, String destroyOverride) {}

    static void startContext(List<BeanReg> regs, String defaultInit, String defaultDestroy, Runnable app) {
        List<Runnable> inits = new ArrayList<>(), destroys = new ArrayList<>();
        for (BeanReg reg : regs) {
            Object b  = reg.bean();
            String im = reg.initOverride()    != null ? reg.initOverride()    : defaultInit;
            String dm = reg.destroyOverride() != null ? reg.destroyOverride() : defaultDestroy;
            try {
                try { Method m = b.getClass().getMethod(im);  inits.add(()    -> { try { m.invoke(b); } catch (Exception e) { throw new RuntimeException(e); } }); System.out.println("  [resolve] " + b.getClass().getSimpleName() + " init-method='" + im + "' ✓"); }
                catch (NoSuchMethodException x) { inits.add(() -> {}); System.out.println("  [resolve] " + b.getClass().getSimpleName() + " no '" + im + "' — skipped"); }
                try { Method m = b.getClass().getMethod(dm); destroys.add(() -> { try { m.invoke(b); } catch (Exception e) { throw new RuntimeException(e); } }); }
                catch (NoSuchMethodException x) { destroys.add(() -> {}); }
            } catch (Exception e) { throw new RuntimeException(e); }
        }
        System.out.println("  [container] init phase:");
        inits.forEach(Runnable::run);
        System.out.println("  [container] ready\n");
        app.run();
        System.out.println("\n  [container] destroy phase (reverse order):");
        List<Runnable> rev = new ArrayList<>(destroys); Collections.reverse(rev);
        rev.forEach(Runnable::run);
        System.out.println("  [container] shutdown complete");
    }

    public static void main(String[] args) {
        System.out.println("=== Container: default-init-method='init'  default-destroy-method='destroy' ===\n");
        System.out.println("--- Bean registration (resolve phase) ---");

        JdbcPool      pool  = new JdbcPool();
        MqBroker      mq    = new MqBroker();
        OrderService  svc   = new OrderService(pool, mq);
        AuditLogger   audit = new AuditLogger();
        AppProperties props = new AppProperties(Map.of("env", "prod", "region", "us-east-1"));

        System.out.println("\n--- Lifecycle method resolution ---");
        List<BeanReg> regs = List.of(
            new BeanReg(pool,  null,    null),          // uses default: init/destroy
            new BeanReg(mq,    null,    null),          // uses default: init/destroy
            new BeanReg(svc,   null,    null),          // uses default: init/destroy
            new BeanReg(audit, "start", "stop"),        // per-bean override: start/stop
            new BeanReg(props, null,    null)           // no init() method → skipped
        );

        startContext(regs, "init", "destroy", () -> {
            audit.audit("startup complete");
            svc.process("ORD-1001");
            svc.process("ORD-1002");
            audit.audit("2 orders processed");
            System.out.println("[STATUS] env=" + props.get("env")
                + " pool.conns=" + pool.conns()
                + " mq.active=" + mq.isActive());
        });
    }
}
```

How to run: `java DefaultInitDestroyDemo3.java`

The container resolves each bean's lifecycle methods at registration time — printing which method it found or "skipped". The global default `init` / `destroy` applies to `JdbcPool`, `MqBroker`, `OrderService`. `AuditLogger`'s per-bean override `start` / `stop` wins. `AppProperties` has no `init()` — silently skipped. Destroy fires in strict reverse order.

## 6. Walkthrough

**Level 3 resolution and init sequence:**

```
Registration (Spring reads XML / @Bean definitions):
  JdbcPool    → initMethod=null → use default "init"  → JdbcPool.init() found ✓
  MqBroker    → initMethod=null → use default "init"  → MqBroker.init() found ✓
  OrderService → initMethod=null → use default "init" → OrderService.init() found ✓
  AuditLogger  → initMethod="start" → per-bean override → AuditLogger.start() found ✓
  AppProperties → initMethod=null → use default "init" → AppProperties.init() NOT found → skip

Init phase (creation order):
  pool.init()    → openConns=10
  mq.init()      → active=true
  svc.init()     → prints pool=10 mq=true
  audit.start()  → log opened  (per-bean "start", not default "init")
  [AppProperties: skipped]

Application:
  audit.audit("startup complete")
  svc.process("ORD-1001"), svc.process("ORD-1002")
  audit.audit("2 orders processed")

Destroy phase (REVERSE order):
  [AppProperties: skipped]
  audit.stop()   → log closed (2 entries)
  svc.destroy()  → processed=2
  mq.destroy()   → active=false
  pool.destroy() → openConns=0
```

## 7. Gotchas & takeaways

> **`default-init-method` silently ignores beans that don't have the named method** — no `BeanDefinitionValidationException`, no warning. This is by design: not every bean needs the hook. But it means a typo in `default-init-method` will silently skip all beans rather than fail fast. Double-check the method name.

> **`default-init-method` only applies to `<bean>` elements in XML** — not to beans discovered via `@ComponentScan` or defined via `@Bean` factory methods. For `@Bean`, use `@Bean(initMethod="...", destroyMethod="...")` per method.

- A per-bean `init-method=""` (empty string) on a `<bean>` element explicitly suppresses the global default for that specific bean — useful to opt individual beans out.
- The global default fires in the same position as a per-bean `init-method`: after `@PostConstruct` and after `InitializingBean.afterPropertiesSet()`.
- If you use `<beans>` XML import (`<import resource="other.xml"/>`), the `default-init-method` attribute of the OUTER file does NOT propagate to the imported file — each file's `<beans>` element has its own defaults.
- In Spring Boot, XML config is rarely used — stick to `@Bean(initMethod="...", destroyMethod="...")` or `@PostConstruct` / `@PreDestroy` in annotation-driven projects.
