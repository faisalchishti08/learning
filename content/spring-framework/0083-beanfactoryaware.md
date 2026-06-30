---
card: spring-framework
gi: 83
slug: beanfactoryaware
title: BeanFactoryAware
---

## 1. What it is

`BeanFactoryAware` is a Spring interface with one method — `setBeanFactory(BeanFactory beanFactory)` — that Spring calls **before `@PostConstruct`** to give the bean direct access to the `BeanFactory` that created it. `BeanFactory` is the root interface of Spring's IoC container — it provides `getBean()`, `containsBean()`, `isSingleton()`, `getType()`, and related low-level methods.

```java
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;

@Component
public class DynamicRouter implements BeanFactoryAware {

    private BeanFactory beanFactory;

    @Override
    public void setBeanFactory(BeanFactory beanFactory) {
        this.beanFactory = beanFactory;
    }

    public void route(String handlerName, String payload) {
        // look up a handler bean by name at runtime — strategy pattern
        MessageHandler handler = beanFactory.getBean(handlerName, MessageHandler.class);
        handler.handle(payload);
    }
}
```

In one sentence: **`BeanFactoryAware` injects the owning `BeanFactory` into a bean before `@PostConstruct`, enabling programmatic bean lookup, type checking, and scope inspection — used for factory beans, plugin systems, and dynamic dispatch patterns.**

## 2. Why & when

Use `BeanFactoryAware` when:

- A bean implements a **factory or strategy pattern** — it needs to look up collaborator beans by name or type at runtime, not at wiring time.
- A bean manages **prototype scoped** beans — it must call `beanFactory.getBean(protoType.class)` to get a fresh instance each time.
- A **framework or infrastructure bean** needs `BeanFactory` access before the full `ApplicationContext` is available (e.g., during early initialisation).
- You need `isSingleton(name)` / `isPrototype(name)` / `getType(name)` for conditional logic.

Prefer `@Autowired ApplicationContext ctx` for application beans — `ApplicationContext` extends `BeanFactory` and is simpler to inject. Use `BeanFactoryAware` for:
- Framework-level beans that specifically need only `BeanFactory` (not the full `ApplicationContext`).
- Beans that must be usable in a standalone `BeanFactory` without a full context (e.g., unit tests with `DefaultListableBeanFactory`).

## 3. Core concept

```
BeanFactory interface (subset of most-used methods):

  Object getBean(String name)
  <T> T  getBean(String name, Class<T> requiredType)
  <T> T  getBean(Class<T> requiredType)
  boolean containsBean(String name)
  boolean isSingleton(String name)
  boolean isPrototype(String name)
  Class<?>getType(String name)
  String[]getAliases(String name)

BeanFactory vs ApplicationContext:
  BeanFactory               ApplicationContext (extends BeanFactory)
  ─────────────────────────  ──────────────────────────────────────────
  Core IoC                  Core IoC + full app framework
  getBean() / containsBean  + Event publication
  No i18n                   + MessageSource (i18n)
  No auto-PostProcessor     + Auto-registers BeanPostProcessors
  No resource loading        + ResourceLoader
  setBeanFactory() available + setApplicationContext() available

When setBeanFactory() fires:
  ① Constructor
  ② @Autowired / @Value injection
  ③ setBeanName()   (BeanNameAware, if implemented)
  ④ setBeanFactory() ← HERE
  ⑤ setApplicationContext() (if ApplicationContextAware)
  ⑥ @PostConstruct / afterPropertiesSet / init-method
  ⑦ bean ready
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeanFactoryAware position in lifecycle and BeanFactory vs ApplicationContext">
  <defs>
    <marker id="a83" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="183" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanFactoryAware — fires after BeanNameAware, before ApplicationContextAware and @PostConstruct</text>

  <!-- Timeline -->
  <rect x="10"  y="33" width="68"  height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="44"  y="51" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">① construct</text>
  <line x1="78" y1="47" x2="86" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a83)"/>
  <rect x="89"  y="33" width="68"  height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="123" y="51" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">② inject</text>
  <line x1="157" y1="47" x2="165" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a83)"/>
  <rect x="168" y="33" width="85"  height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="210" y="51" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">③ setBeanName</text>
  <line x1="253" y1="47" x2="261" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a83)"/>
  <rect x="264" y="33" width="100" height="28" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="314" y="47" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">④ setBeanFactory</text>
  <text x="314" y="58" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">← BeanFactoryAware</text>
  <line x1="364" y1="47" x2="372" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a83)"/>
  <rect x="375" y="33" width="100" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="425" y="51" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">⑤ setAppContext</text>
  <line x1="475" y1="47" x2="483" y2="47" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a83)"/>
  <rect x="486" y="33" width="100" height="28" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="536" y="51" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">⑥ @PostConstruct</text>

  <!-- BeanFactory vs ApplicationContext -->
  <rect x="10" y="75" width="310" height="100" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="0.9"/>
  <text x="165" y="92" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">BeanFactory (lower-level)</text>
  <text x="22"  y="107" fill="#8b949e" font-size="8" font-family="monospace">getBean(name) / getBean(type)</text>
  <text x="22"  y="120" fill="#8b949e" font-size="8" font-family="monospace">containsBean(name)</text>
  <text x="22"  y="133" fill="#8b949e" font-size="8" font-family="monospace">isSingleton(name) / isPrototype(name)</text>
  <text x="22"  y="146" fill="#8b949e" font-size="8" font-family="monospace">getType(name) / getAliases(name)</text>
  <text x="22"  y="162" fill="#8b949e" font-size="7.5" font-family="sans-serif">No events, no i18n, no ResourceLoader</text>

  <rect x="335" y="75" width="330" height="100" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="0.9"/>
  <text x="500" y="92" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">ApplicationContext (extends BeanFactory)</text>
  <text x="347" y="107" fill="#8b949e" font-size="8" font-family="monospace">All BeanFactory methods +</text>
  <text x="347" y="120" fill="#8b949e" font-size="8" font-family="monospace">publishEvent() / MessageSource (i18n)</text>
  <text x="347" y="133" fill="#8b949e" font-size="8" font-family="monospace">ResourceLoader / Environment</text>
  <text x="347" y="146" fill="#8b949e" font-size="8" font-family="monospace">Auto-registers BeanPostProcessors</text>
  <text x="347" y="162" fill="#79c0ff" font-size="7.5" font-family="sans-serif">Prefer this for app beans via @Autowired</text>
</svg>

`BeanFactory` gives low-level container access (lookup, type checking, scope). `ApplicationContext` adds events, i18n, and resource loading on top.

## 5. Runnable example

Scenario: a `HandlerRegistry` that dispatches requests to handler beans looked up by name — a classic runtime strategy / plugin dispatch pattern.

### Level 1 — Basic

`BeanFactoryAware` used to look up a collaborator bean by name at runtime.

```java
// BeanFactoryAwareDemo.java — run with: java BeanFactoryAwareDemo.java
import java.util.*;

public class BeanFactoryAwareDemo {

    interface BeanFactoryAware { void setBeanFactory(FakeBeanFactory bf); }

    // ── Handler contract ──────────────────────────────────────────────
    interface MessageHandler { String handle(String payload); }

    // ── Two concrete handlers registered in the fake factory ──────────
    static class EmailHandler  implements MessageHandler {
        @Override public String handle(String payload) { return "[EMAIL]  sent: " + payload; }
    }

    static class SmsHandler    implements MessageHandler {
        @Override public String handle(String payload) { return "[SMS]    sent: " + payload; }
    }

    // ── Fake BeanFactory ──────────────────────────────────────────────
    static class FakeBeanFactory {
        private final Map<String, Object> beans;
        FakeBeanFactory(Map<String, Object> beans) { this.beans = beans; }
        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) {
            Object b = beans.get(name);
            if (b == null) throw new NoSuchElementException("No bean: " + name);
            return type.cast(b);
        }
        boolean containsBean(String name) { return beans.containsKey(name); }
    }

    // ── Router using BeanFactoryAware ─────────────────────────────────
    static class MessageRouter implements BeanFactoryAware {
        private FakeBeanFactory beanFactory;

        @Override
        public void setBeanFactory(FakeBeanFactory bf) {
            this.beanFactory = bf;
            System.out.println("  [setBeanFactory] factory injected");
        }

        String route(String handlerBeanName, String payload) {
            if (!beanFactory.containsBean(handlerBeanName))
                return "[ERROR] unknown handler: " + handlerBeanName;
            MessageHandler handler = beanFactory.getBean(handlerBeanName, MessageHandler.class);
            return handler.handle(payload);
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");
        Map<String, Object> beans = new LinkedHashMap<>();
        beans.put("emailHandler", new EmailHandler());
        beans.put("smsHandler",   new SmsHandler());
        FakeBeanFactory factory = new FakeBeanFactory(beans);

        MessageRouter router = new MessageRouter();
        router.setBeanFactory(factory);   // Spring calls this

        System.out.println("\n=== Routing messages ===");
        System.out.println(router.route("emailHandler", "Your order has shipped"));
        System.out.println(router.route("smsHandler",   "OTP: 482910"));
        System.out.println(router.route("pushHandler",  "Notification")); // unknown
    }
}
```

How to run: `java BeanFactoryAwareDemo.java`

`MessageRouter.route()` looks up handler beans by name at call time — not at wiring time. New handlers can be added to the context without changing `MessageRouter`. `containsBean()` guards against missing handlers.

### Level 2 — Intermediate

`BeanFactoryAware` used to get a fresh prototype bean on each request — prototypes must be fetched via `beanFactory.getBean()`, not `@Autowired` (which only gets one instance).

```java
// BeanFactoryAwareDemo2.java — run with: java BeanFactoryAwareDemo2.java
import java.util.*;

public class BeanFactoryAwareDemo2 {

    interface BeanFactoryAware { void setBeanFactory(FakeBF bf); }

    // ── Prototype-scoped bean: each getBean() returns a NEW instance ──
    static class DatabaseTransaction {
        private final String txId;
        private final List<String> operations = new ArrayList<>();
        private boolean committed = false;

        DatabaseTransaction(String txId) {
            this.txId = txId;
            System.out.println("    [NEW TRANSACTION] " + txId);
        }

        void addOp(String sql)  { operations.add(sql); System.out.println("    [" + txId + "] " + sql); }
        void commit()           { committed = true;    System.out.println("    [" + txId + "] COMMIT (" + operations.size() + " ops)"); }
        void rollback()         { committed = false;   System.out.println("    [" + txId + "] ROLLBACK"); }
        String id()             { return txId; }
    }

    // ── Fake BF: creates a NEW DatabaseTransaction on each getBean() ──
    static class FakeBF {
        private int txSeq = 0;
        @SuppressWarnings("unchecked")
        <T> T getBean(String name, Class<T> type) {
            if ("databaseTransaction".equals(name)) {
                // Prototype: new instance every time
                return type.cast(new DatabaseTransaction("TX-" + (++txSeq)));
            }
            throw new NoSuchElementException("No bean: " + name);
        }
        boolean isPrototype(String name) { return "databaseTransaction".equals(name); }
        boolean isSingleton(String name) { return !isPrototype(name); }
    }

    // ── Service using BeanFactoryAware to get fresh prototypes ────────
    static class OrderService implements BeanFactoryAware {
        private FakeBF beanFactory;

        @Override
        public void setBeanFactory(FakeBF bf) { this.beanFactory = bf; }

        void placeOrder(String orderId, String[] sqls) {
            System.out.println("\n[placeOrder] orderId=" + orderId);
            // Must fetch a NEW transaction via beanFactory — @Autowired would give same instance
            DatabaseTransaction tx = beanFactory.getBean("databaseTransaction", DatabaseTransaction.class);
            System.out.println("  isPrototype=true → new TX id=" + tx.id());
            try {
                for (String sql : sqls) tx.addOp(sql);
                tx.commit();
                System.out.println("  [ORDER] " + orderId + " → committed via " + tx.id());
            } catch (Exception e) {
                tx.rollback();
            }
        }
    }

    public static void main(String[] args) {
        FakeBF factory = new FakeBF();
        OrderService svc = new OrderService();
        svc.setBeanFactory(factory);

        System.out.println("=== Placing orders — each gets a fresh DatabaseTransaction ===");
        svc.placeOrder("ORD-001", new String[]{"INSERT INTO orders ...", "UPDATE inventory ..."});
        svc.placeOrder("ORD-002", new String[]{"INSERT INTO orders ...", "INSERT INTO shipments ..."});
        svc.placeOrder("ORD-003", new String[]{"INSERT INTO orders ..."});
        System.out.println("\n[NOTE] TX-1, TX-2, TX-3 are separate instances — prototype scope");
    }
}
```

How to run: `java BeanFactoryAwareDemo2.java`

Each call to `placeOrder()` fetches a new `DatabaseTransaction` via `beanFactory.getBean()`. If `OrderService` used `@Autowired DatabaseTransaction tx`, Spring would inject the same instance for all orders — because `@Autowired` resolves at wiring time, not at each method call. `BeanFactoryAware` is the correct pattern for consuming prototype beans from a singleton.

### Level 3 — Advanced

`BeanFactoryAware` with full metadata inspection: use `getType()`, `isSingleton()`, `isPrototype()` to build a diagnostic report of all registered beans.

```java
// BeanFactoryAwareDemo3.java — run with: java BeanFactoryAwareDemo3.java
import java.util.*;

public class BeanFactoryAwareDemo3 {

    interface BeanFactoryAware { void setBeanFactory(FakeBF bf); }

    // ── Fake BeanFactory with metadata ────────────────────────────────
    record BeanMeta(Class<?> type, boolean singleton, String[] aliases) {}

    static class FakeBF {
        private final Map<String, BeanMeta> registry;
        FakeBF(Map<String, BeanMeta> registry) { this.registry = registry; }
        boolean containsBean(String n)  { return registry.containsKey(n); }
        boolean isSingleton(String n)   { return registry.containsKey(n) && registry.get(n).singleton(); }
        boolean isPrototype(String n)   { return registry.containsKey(n) && !registry.get(n).singleton(); }
        Class<?> getType(String n)      { return registry.containsKey(n) ? registry.get(n).type() : null; }
        String[] getAliases(String n)   { return registry.containsKey(n) ? registry.get(n).aliases() : new String[0]; }
        Set<String> names()             { return registry.keySet(); }
    }

    // ── Diagnostic bean using BeanFactoryAware ────────────────────────
    static class ContainerDiagnostics implements BeanFactoryAware {
        private FakeBF beanFactory;

        @Override
        public void setBeanFactory(FakeBF bf) {
            this.beanFactory = bf;
            System.out.println("  [setBeanFactory] factory injected with " + bf.names().size() + " beans");
        }

        void postConstruct() {
            System.out.println("  [@PostConstruct] scanning container...");
            Map<String, String> report = new LinkedHashMap<>();
            for (String name : beanFactory.names()) {
                String scope   = beanFactory.isSingleton(name) ? "singleton" : "prototype";
                Class<?> type  = beanFactory.getType(name);
                String[] aliases = beanFactory.getAliases(name);
                String entry = String.format("scope=%-10s type=%-35s aliases=%s",
                    scope, type != null ? type.getSimpleName() : "?", Arrays.toString(aliases));
                report.put(name, entry);
            }
            System.out.println("  [@PostConstruct] container report:");
            report.forEach((name, info) -> System.out.printf("    %-30s %s%n", name, info));
        }

        boolean isHealthy() {
            // Example health check: ensure all expected beans are singletons
            List<String> required = List.of("dataSource", "transactionManager", "orderService");
            for (String name : required) {
                if (!beanFactory.containsBean(name)) { System.out.println("  [HEALTH] MISSING: " + name); return false; }
                if (!beanFactory.isSingleton(name))  { System.out.println("  [HEALTH] NOT SINGLETON: " + name); return false; }
            }
            return true;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Container starting ===");

        // Simulate Spring's bean registry
        Map<String, BeanMeta> reg = new LinkedHashMap<>();
        reg.put("dataSource",        new BeanMeta(FakeBF.class,         true,  new String[]{"ds"}));
        reg.put("transactionManager",new BeanMeta(Object.class,          true,  new String[]{}));
        reg.put("orderService",      new BeanMeta(Object.class,          true,  new String[]{"orders"}));
        reg.put("dbTransaction",     new BeanMeta(Object.class,          false, new String[]{}));
        reg.put("containerDiagnostics", new BeanMeta(ContainerDiagnostics.class, true, new String[]{}));
        FakeBF factory = new FakeBF(reg);

        ContainerDiagnostics diag = new ContainerDiagnostics();
        diag.setBeanFactory(factory);  // BeanFactoryAware
        diag.postConstruct();          // @PostConstruct

        System.out.println("\n=== Health check ===");
        System.out.println("[HEALTHY] " + diag.isHealthy());

        System.out.println("\n=== Spot checks ===");
        System.out.println("dataSource is singleton: " + factory.isSingleton("dataSource"));
        System.out.println("dbTransaction is prototype: " + factory.isPrototype("dbTransaction"));
        System.out.println("dataSource aliases: " + Arrays.toString(factory.getAliases("dataSource")));
        System.out.println("dataSource type: " + factory.getType("dataSource").getSimpleName());
    }
}
```

How to run: `java BeanFactoryAwareDemo3.java`

`ContainerDiagnostics` uses `BeanFactoryAware` to scan every registered bean: `getType()`, `isSingleton()`, `isPrototype()`, `getAliases()`. The `@PostConstruct` prints a full container report. `isHealthy()` verifies that three required beans are registered and are singletons.

## 6. Walkthrough

**Level 2 prototype fetch sequence:**

```
svc.setBeanFactory(factory)                    ← ④ BeanFactoryAware fires
  svc.beanFactory = factory

placeOrder("ORD-001", sqls):
  factory.getBean("databaseTransaction", DatabaseTransaction.class)
    → factory.txSeq++ = 1
    → new DatabaseTransaction("TX-1")
    → return TX-1

  TX-1.addOp("INSERT INTO orders ...")
  TX-1.addOp("UPDATE inventory ...")
  TX-1.commit()  → COMMIT (2 ops)

placeOrder("ORD-002", sqls):
  factory.getBean("databaseTransaction", DatabaseTransaction.class)
    → factory.txSeq++ = 2
    → new DatabaseTransaction("TX-2")      ← NEW instance, not TX-1!

  TX-2.addOp(...)  TX-2.commit()

placeOrder("ORD-003", sqls):
  → TX-3 (fresh instance)

Result: three separate transactions TX-1, TX-2, TX-3
  If @Autowired had been used: all three calls would share the same instance!
```

## 7. Gotchas & takeaways

> **`BeanFactoryAware` couples your class to Spring.** For application beans, prefer `@Autowired ApplicationContext ctx` — same result, less boilerplate, easier to test. Use `BeanFactoryAware` for framework/infrastructure beans that need to work with a bare `BeanFactory`.

> **Calling `beanFactory.getBean()` inside the constructor is unsafe** — the `BeanFactory` hasn't been injected yet. Call it in `@PostConstruct` or in methods invoked after the bean is fully initialised.

- `BeanFactory.getBean(Class<T>)` throws `NoUniqueBeanDefinitionException` if more than one bean of that type exists — use `getBean(name, type)` to be explicit.
- `BeanFactory` does NOT auto-register `BeanPostProcessors` (unlike `ApplicationContext`). If you use a raw `BeanFactory` in tests or tools, register processors manually.
- Prototype beans injected via `BeanFactoryAware.getBean()` are NOT tracked — no `@PreDestroy` / `DisposableBean.destroy()` is called on them. The caller is responsible for cleanup.
- `ObjectProvider<T>` (injected via `@Autowired ObjectProvider<MyPrototype> provider`) is a modern, type-safe alternative to `BeanFactoryAware + getBean()` for prototype fetch patterns — prefer it in Spring Boot 3+ code.
