---
card: spring-framework
gi: 112
slug: providing-a-scope-scope-scopemetadataresolver
title: Providing a scope (@Scope, ScopeMetadataResolver)
---

## 1. What it is

`@Scope` controls **how many instances** Spring creates for a bean and **how long they live**. By default every bean is a singleton — one instance for the whole context. `@Scope` lets you override that per-bean. `ScopeMetadataResolver` is the interface Spring calls to derive scope metadata from a `BeanDefinition`, letting you plug in custom scoping strategies.

Built-in scope names:

| Scope | Meaning |
|---|---|
| `singleton` (default) | One shared instance per container |
| `prototype` | New instance on every `getBean()` / injection |
| `request` | One instance per HTTP request (web contexts) |
| `session` | One instance per HTTP session (web contexts) |
| `application` | One instance per `ServletContext` (web) |
| Custom | Anything you register with `ConfigurableBeanFactory` |

## 2. Why & when

Singleton is correct for stateless services. Use other scopes when:

- **Prototype** — the bean holds mutable per-call state (a builder, a command object, a formatter for one request).
- **Request / session** — web beans that carry request-scoped or session-scoped data (current user, cart).
- **Custom** — refresh scope (Spring Cloud), thread scope, conversation scope.

## 3. Core concept

`@Scope` attributes:

- `value` (or `scopeName`) — the scope name string.
- `proxyMode` — controls how a narrower-scoped bean (prototype, request) is injected into a wider-scoped bean (singleton). Options: `NO` (default), `TARGET_CLASS` (CGLIB proxy), `INTERFACES` (JDK proxy).

**Why `proxyMode` matters**: if a singleton `@Autowired` a request-scoped bean directly, it captures one instance at wiring time and reuses it — defeating the scope. A scoped proxy wraps the injection: each method call on the proxy delegates to the *current* scope instance.

`ScopeMetadataResolver` interface:
```java
ScopeMetadata resolveScopeMetadata(BeanDefinition definition);
```
Returns a `ScopeMetadata` with the scope name and proxy mode. The default resolver reads `@Scope`; custom resolvers can derive scope from any class metadata (package, naming convention, etc.).

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Singleton -->
  <rect x="10" y="30" width="160" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="53" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">singleton</text>
  <text x="90" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1 instance / context</text>

  <!-- Prototype -->
  <rect x="10" y="95" width="160" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="118" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">prototype</text>
  <text x="90" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">new instance / getBean</text>

  <!-- Request/session -->
  <rect x="10" y="160" width="160" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="183" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">request / session / …</text>

  <!-- Proxy -->
  <rect x="265" y="80" width="175" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="352" y="103" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Scoped Proxy</text>
  <text x="352" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">proxyMode=TARGET_CLASS</text>

  <!-- Singleton consumer -->
  <rect x="535" y="80" width="155" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="612" y="103" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Singleton bean</text>
  <text x="612" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">always sees fresh scope</text>

  <line x1="172" y1="120" x2="262" y2="107" stroke="#79c0ff" stroke-width="2" marker-end="url(#a112)"/>
  <line x1="442" y1="107" x2="532" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#b112)"/>
  <defs>
    <marker id="a112" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="b112" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Scoped proxy bridges lifetime mismatch between singleton and shorter-lived beans</text>
</svg>

A scoped proxy sits between a singleton and a shorter-lived bean, delivering the right instance per call.

## 5. Runnable example

### Level 1 — Basic

Compare singleton and prototype: show that `getBean()` returns the same instance for singleton but a new one for prototype.

```java
// ScopeBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component                          // default: singleton
class SingletonCounter {
    private int count = 0;
    public int increment() { return ++count; }
}

@Component
@Scope("prototype")                 // new instance per getBean()
class PrototypeCounter {
    private int count = 0;
    public int increment() { return ++count; }
}

@Configuration
@ComponentScan
class ScopeCfg {}

public class ScopeBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ScopeCfg.class);

        var s1 = ctx.getBean(SingletonCounter.class);
        var s2 = ctx.getBean(SingletonCounter.class);
        System.out.println("Singleton same instance: " + (s1 == s2));   // true
        System.out.println("s1.increment(): " + s1.increment());         // 1
        System.out.println("s2.increment(): " + s2.increment());         // 2 (shared!)

        var p1 = ctx.getBean(PrototypeCounter.class);
        var p2 = ctx.getBean(PrototypeCounter.class);
        System.out.println("Prototype same instance: " + (p1 == p2));   // false
        System.out.println("p1.increment(): " + p1.increment());         // 1
        System.out.println("p2.increment(): " + p2.increment());         // 1 (independent)
        ctx.close();
    }
}
```

How to run: `java ScopeBasic.java`

Singleton: both references point to the same object — incrementing via `s2` affects `s1`. Prototype: each call produces a fresh object — state is independent.

### Level 2 — Intermediate

Use `proxyMode = ScopedProxyMode.TARGET_CLASS` to inject a prototype-scoped bean into a singleton safely.

```java
// ScopeProxy.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component
@Scope(value = "prototype", proxyMode = ScopedProxyMode.TARGET_CLASS)
class RequestIdGenerator {
    private final String id = "REQ-" + System.nanoTime();

    public String getId() { return id; }
}

@Service   // singleton
class RequestHandler {
    @Autowired
    private RequestIdGenerator generator;  // proxy injected, not the real prototype

    public void handle(String name) {
        // Each call to generator.getId() via the proxy gives a fresh prototype instance
        System.out.println(name + " → " + generator.getId());
    }
}

@Configuration
@ComponentScan
class ProxyCfg {}

public class ScopeProxy {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyCfg.class);
        var handler = ctx.getBean(RequestHandler.class);

        handler.handle("alice");
        handler.handle("bob");
        handler.handle("carol");

        // Calling getId() twice in the same handle() would return the SAME id
        // (one prototype per proxy method call invocation chain — actually per getBean in underlying scope)
        ctx.close();
    }
}
```

How to run: `java ScopeProxy.java`

Without `proxyMode`, the singleton captures one `RequestIdGenerator` forever. With `TARGET_CLASS`, each method call on the proxy delegates to a new prototype instance — a different `id` per call.

### Level 3 — Advanced

Custom `ScopeMetadataResolver`: derive scope from a naming convention (`*Singleton` → singleton, `*Prototype` → prototype) without requiring `@Scope` on every class.

```java
// ScopeResolver.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.config.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// Naming-convention scope resolver
class ConventionScopeMetadataResolver implements ScopeMetadataResolver {
    @Override
    public ScopeMetadata resolveScopeMetadata(BeanDefinition definition) {
        var metadata = new ScopeMetadata();
        String className = definition.getBeanClassName();
        if (className != null && className.endsWith("Prototype")) {
            metadata.setScopeName(BeanDefinition.SCOPE_PROTOTYPE);
            System.out.println("[Resolver] prototype scope → " + className);
        } else {
            metadata.setScopeName(BeanDefinition.SCOPE_SINGLETON);
        }
        return metadata;
    }
}

// No @Scope annotation — resolver determines scope from class name
@Component
class CacheManagerSingleton {
    private int hits = 0;
    public String get(String key) { return "cached-" + key + "-hit-" + (++hits); }
}

@Component
class RequestContextPrototype {
    private final long id = System.nanoTime();
    public String info() { return "ctx-" + id; }
}

@Service
class AppService {
    @Autowired CacheManagerSingleton cache;
    @Autowired org.springframework.context.ApplicationContext ctx;

    public void run() {
        System.out.println("Cache (singleton): " + cache.get("item1"));
        System.out.println("Cache (singleton): " + cache.get("item2"));  // hit=2

        // Get fresh prototypes manually (proxy not set up in this example)
        var rc1 = ctx.getBean(RequestContextPrototype.class);
        var rc2 = ctx.getBean(RequestContextPrototype.class);
        System.out.println("Proto 1: " + rc1.info());
        System.out.println("Proto 2: " + rc2.info());
        System.out.println("Same? " + (rc1 == rc2));   // false
    }
}

@Configuration
@ComponentScan(
    basePackageClasses = ScopeResolver.class,
    scopeResolver = ConventionScopeMetadataResolver.class   // custom resolver
)
class ResolverCfg {}

public class ScopeResolver {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ResolverCfg.class);
        ctx.getBean(AppService.class).run();
        ctx.close();
    }
}
```

How to run: `java ScopeResolver.java`

The resolver reads the class name: `*Singleton` → singleton, `*Prototype` → prototype. No `@Scope` annotation needed on individual classes — convention drives scoping.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context created** — scanner uses `ConventionScopeMetadataResolver` for every discovered bean.
2. **`CacheManagerSingleton` scanned** — class name ends in `"Singleton"` → resolver returns `singleton`. BeanDefinition scope = `"singleton"`.
3. **`RequestContextPrototype` scanned** — ends in `"Prototype"` → resolver returns `prototype`. BeanDefinition scope = `"prototype"`.
4. **`AppService` scanned** — neither suffix → singleton (default).
5. **`CacheManagerSingleton` instantiated once** — shared across all callers.
6. **`cache.get("item1")`** → `"cached-item1-hit-1"`. Counter = 1.
7. **`cache.get("item2")`** → `"cached-item2-hit-2"`. Same singleton, counter = 2.
8. **`ctx.getBean(RequestContextPrototype.class)` × 2** — prototype scope: two distinct objects with different `nanoTime` ids.
9. **`rc1 == rc2`** → `false`.

Expected output:
```
[Resolver] prototype scope → RequestContextPrototype
Cache (singleton): cached-item1-hit-1
Cache (singleton): cached-item2-hit-2
Proto 1: ctx-123456789
Proto 2: ctx-987654321
Same? false
```

## 7. Gotchas & takeaways

> Injecting a `prototype`-scoped bean into a `singleton` via plain `@Autowired` (without `proxyMode`) **does not give you a new prototype per call**. The singleton captures one prototype instance at construction time and reuses it forever. Use `proxyMode = TARGET_CLASS`, `ObjectProvider<T>`, or `ApplicationContext.getBean()` to get a fresh prototype each time.

> `@PreDestroy` is **not called** for prototype beans — the container hands them off and never tracks them. If a prototype bean holds resources (connections, threads), manage their lifecycle manually.

- `proxyMode = ScopedProxyMode.TARGET_CLASS` requires CGLIB (spring-aop + objenesis on the classpath). `INTERFACES` mode uses JDK proxies but requires the bean to implement an interface.
- `ScopeMetadataResolver` is called once per class during scanning. Return `prototype` scope only when the resolver is certain — mistakes silently create excessive instances.
- Web scopes (`request`, `session`, `application`) require a web application context or a `RequestContextListener` / `RequestContextFilter` to be active.
- Custom scopes are registered via `ctx.getBeanFactory().registerScope("myScope", new MyScope())`.
