---
card: spring-framework
gi: 86
slug: beanpostprocessor-interface
title: BeanPostProcessor interface
---

## 1. What it is

`BeanPostProcessor` is a Spring hook that lets you intercept **every bean in the container** at two points in its lifecycle: before `@PostConstruct` fires (`postProcessBeforeInitialization`) and after it fires (`postProcessAfterInitialization`). Spring applies all registered `BeanPostProcessors` to every bean — making it the core extension point for AOP proxying, annotation processing, validation, and more.

```java
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.beans.BeansException;

@Component
public class LoggingBeanPostProcessor implements BeanPostProcessor {

    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) throws BeansException {
        System.out.println("About to init: " + beanName);
        return bean;  // MUST return the bean (or a replacement/proxy)
    }

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) throws BeansException {
        System.out.println("Finished init: " + beanName);
        return bean;  // MUST return the bean (or a replacement/proxy)
    }
}
```

In one sentence: **`BeanPostProcessor` is a container-level extension point that intercepts every bean's creation — before and after init callbacks — letting you wrap beans in proxies, validate them, apply annotations, or transform them; returning a replacement is how AOP creates proxies.**

## 2. Why & when

Use `BeanPostProcessor` when:

- You want to **apply behavior to every bean** without modifying each bean's class — e.g., add logging, validation, or metrics to every bean automatically.
- You are writing a **framework annotation** (like `@Transactional`, `@Cacheable`) that must post-process beans to wrap them in a proxy.
- You need to **validate every bean** after initialisation — check invariants that span multiple beans.
- You need to **replace** a bean with a subclass or proxy dynamically.

Don't use `BeanPostProcessor` for per-bean logic — use `@PostConstruct` or `InitializingBean`. `BeanPostProcessor` is for cross-cutting concerns that apply to many beans.

## 3. Core concept

```
Per-bean lifecycle with BeanPostProcessor:

  ① Constructor
  ② @Autowired / @Value injection
  ③ Aware setter methods (BeanNameAware etc.)
  ④ postProcessBeforeInitialization(bean, beanName)   ← BPP BEFORE init
  ⑤ @PostConstruct / afterPropertiesSet / init-method  ← bean's own init
  ⑥ postProcessAfterInitialization(bean, beanName)    ← BPP AFTER init
  ⑦ bean stored in singleton cache — ready for use

Return value rules:
  • Both methods MUST return a non-null object.
  • Return the original bean to leave it unchanged.
  • Return a different object (proxy/wrapper) to REPLACE the bean in the context.
    → The replacement must be compatible with the bean's type.
    → Other beans that @Autowire this bean get the replacement.

Spring's own BeanPostProcessors (built-in):
  CommonAnnotationBeanPostProcessor → @PostConstruct / @PreDestroy / @Resource
  AutowiredAnnotationBeanPostProcessor → @Autowired / @Value / @Inject
  AbstractAdvisorAutoProxyCreator → @Transactional, @Cacheable → CGLIB/JDK proxy

Multiple BeanPostProcessors:
  All registered BPPs run on every bean, in PriorityOrdered → Ordered → unordered order.
  A BPP can return a proxy that the next BPP then also processes.
```

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeanPostProcessor in the bean lifecycle — before and after init">
  <defs>
    <marker id="a86" markerWidth="8" markerHeight="6" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <rect x="5" y="5" width="670" height="203" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.2"/>
  <text x="338" y="22" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanPostProcessor wraps every bean's init phase — return a proxy to replace it</text>

  <!-- Step boxes -->
  <rect x="8"   y="33" width="68"  height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="42"  y="53" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">① construct</text>

  <rect x="83"  y="33" width="68"  height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="117" y="53" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">② inject</text>

  <rect x="158" y="33" width="68"  height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="192" y="53" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">③ Aware</text>

  <rect x="233" y="33" width="130" height="32" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="298" y="49" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">④ postProcessBefore</text>
  <text x="298" y="61" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">Initialization(bean, name)</text>

  <rect x="370" y="33" width="120" height="32" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="430" y="49" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">⑤ @PostConstruct</text>
  <text x="430" y="61" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">/ afterPropertiesSet</text>

  <rect x="497" y="33" width="130" height="32" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1.8"/>
  <text x="562" y="49" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">⑥ postProcessAfter</text>
  <text x="562" y="61" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">Initialization(bean, name)</text>

  <!-- Arrows -->
  <line x1="76"  y1="49" x2="81"  y2="49" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a86)"/>
  <line x1="151" y1="49" x2="156" y2="49" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a86)"/>
  <line x1="226" y1="49" x2="231" y2="49" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a86)"/>
  <line x1="363" y1="49" x2="368" y2="49" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a86)"/>
  <line x1="490" y1="49" x2="495" y2="49" stroke="#6db33f" stroke-width="1.1" marker-end="url(#a86)"/>

  <!-- Proxy replacement highlight -->
  <rect x="10" y="80" width="655" height="115" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="0.8"/>
  <text x="22" y="98" fill="#8b949e" font-size="9" font-family="monospace">Return value — key contract:</text>
  <line x1="12" y1="102" x2="662" y2="102" stroke="#8b949e" stroke-width="0.5"/>
  <text x="22" y="117" fill="#6db33f" font-size="9" font-family="monospace">return bean;                         → unchanged (pass-through)</text>
  <text x="22" y="131" fill="#6db33f" font-size="9" font-family="monospace">return new MyProxy(bean);            → REPLACE bean with proxy in context</text>
  <text x="22" y="145" fill="#8b949e" font-size="9" font-family="monospace">return null;                         → IllegalStateException (forbidden)</text>
  <line x1="12" y1="150" x2="662" y2="150" stroke="#8b949e" stroke-width="0.4" stroke-dasharray="3,3"/>
  <text x="22" y="165" fill="#79c0ff" font-size="9" font-family="sans-serif">postProcessBeforeInitialization  → fires before @PostConstruct</text>
  <text x="22" y="179" fill="#79c0ff" font-size="9" font-family="sans-serif">postProcessAfterInitialization   → fires after @PostConstruct; return proxy here for AOP</text>
</svg>

Both BPP methods must return non-null. Returning a different object replaces the bean with a proxy for all injection targets.

## 5. Runnable example

Scenario: a `ProfilingBeanPostProcessor` that wraps service beans in a timing proxy — every method call is automatically measured without touching the service class.

### Level 1 — Basic

A `BeanPostProcessor` that logs bean creation events — pure pass-through, no modification.

```java
// BPPDemo.java — run with: java BPPDemo.java
import java.util.*;

public class BPPDemo {

    // ── Simulated BeanPostProcessor interface ─────────────────────────
    interface BeanPostProcessor {
        Object postProcessBeforeInitialization(Object bean, String beanName);
        Object postProcessAfterInitialization(Object bean, String beanName);
    }

    // ── Application beans ─────────────────────────────────────────────
    static class UserService {
        private final List<String> users = new ArrayList<>();
        void postConstruct() { users.add("system"); System.out.println("    [UserService.@PostConstruct] system user added"); }
        void addUser(String name) { users.add(name); }
        List<String> list() { return users; }
    }

    static class OrderService {
        private int count = 0;
        void postConstruct() { System.out.println("    [OrderService.@PostConstruct] ready"); }
        void placeOrder(String id) { count++; System.out.println("    [OrderService] order " + id + " (#" + count + ")"); }
    }

    // ── BeanPostProcessor: logging observer ───────────────────────────
    static class DiagnosticBPP implements BeanPostProcessor {
        private final List<String> log = new ArrayList<>();

        @Override
        public Object postProcessBeforeInitialization(Object bean, String beanName) {
            System.out.println("  [BPP.beforeInit] " + beanName + " (" + bean.getClass().getSimpleName() + ")");
            log.add("before:" + beanName);
            return bean;  // pass-through — no modification
        }

        @Override
        public Object postProcessAfterInitialization(Object bean, String beanName) {
            System.out.println("  [BPP.afterInit]  " + beanName + " (" + bean.getClass().getSimpleName() + ")");
            log.add("after:" + beanName);
            return bean;  // pass-through
        }

        List<String> log() { return log; }
    }

    // ── Simulated container: applies BPP to every bean ────────────────
    static <T> T initBean(T bean, String name, BeanPostProcessor bpp, Runnable postConstruct) {
        Object result = bpp.postProcessBeforeInitialization(bean, name);  // ④ before init
        postConstruct.run();                                               // ⑤ @PostConstruct
        result = bpp.postProcessAfterInitialization(result, name);        // ⑥ after init
        return (T) result;
    }

    public static void main(String[] args) {
        DiagnosticBPP bpp = new DiagnosticBPP();

        System.out.println("=== Creating beans ===");
        UserService users   = new UserService();
        OrderService orders = new OrderService();

        UserService  wUsers  = initBean(users,  "userService",  bpp, users::postConstruct);
        OrderService wOrders = initBean(orders, "orderService", bpp, orders::postConstruct);

        System.out.println("\n=== Application ===");
        wUsers.addUser("alice");
        wUsers.addUser("bob");
        wOrders.placeOrder("ORD-1");
        System.out.println("[USERS] " + wUsers.list());

        System.out.println("\n[BPP LOG] " + bpp.log());
    }
}
```

How to run: `java BPPDemo.java`

The `DiagnosticBPP` fires `before:userService`, then `UserService.@PostConstruct`, then `after:userService` — for every bean. The BPP log shows the exact sequence. Returning `bean` unchanged is the pass-through pattern.

### Level 2 — Intermediate

`BeanPostProcessor` that wraps service beans in a timing proxy in `postProcessAfterInitialization` — all method calls go through the proxy without touching service classes.

```java
// BPPDemo2.java — run with: java BPPDemo2.java
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BPPDemo2 {

    interface BeanPostProcessor {
        Object postProcessBeforeInitialization(Object bean, String beanName);
        Object postProcessAfterInitialization(Object bean, String beanName);
    }

    // ── Service interface + implementation ────────────────────────────
    interface ProductService {
        List<String> search(String query);
        String       getById(String id);
    }

    static class ProductServiceImpl implements ProductService {
        private final Map<String, String> products = Map.of("p1","Notebook","p2","Pen","p3","Backpack");
        void init() { System.out.println("    [ProductServiceImpl.init] ready, " + products.size() + " products"); }
        @Override public List<String> search(String q) {
            simulateLatency(20);
            return products.values().stream().filter(v -> v.toLowerCase().contains(q.toLowerCase())).toList();
        }
        @Override public String getById(String id) {
            simulateLatency(5);
            return products.getOrDefault(id, "NOT_FOUND");
        }
        private void simulateLatency(long ms) { try { Thread.sleep(ms); } catch (InterruptedException ignored) {} }
    }

    // ── Dynamic proxy timing wrapper ──────────────────────────────────
    static class TimingProxy implements InvocationHandler {
        private final Object target;
        private final String beanName;
        private final Map<String, Long> callCounts = new ConcurrentHashMap<>();
        private final Map<String, Long> totalMs    = new ConcurrentHashMap<>();

        TimingProxy(Object target, String beanName) { this.target = target; this.beanName = beanName; }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            long start = System.currentTimeMillis();
            Object result = method.invoke(target, args);
            long elapsed = System.currentTimeMillis() - start;
            callCounts.merge(method.getName(), 1L, Long::sum);
            totalMs.merge(method.getName(), elapsed, Long::sum);
            System.out.printf("  [TIMING][%s.%s] %dms%n", beanName, method.getName(), elapsed);
            return result;
        }

        void printStats() {
            System.out.println("  [STATS for " + beanName + "]");
            callCounts.forEach((m, c) ->
                System.out.printf("    %s: %d calls, total=%dms, avg=%.1fms%n",
                    m, c, totalMs.get(m), totalMs.get(m) / (double) c));
        }
    }

    // ── BPP that wraps services in timing proxies ─────────────────────
    static class TimingBPP implements BeanPostProcessor {
        private final Map<String, TimingProxy> proxies = new LinkedHashMap<>();

        @Override
        public Object postProcessBeforeInitialization(Object bean, String beanName) {
            return bean;  // nothing before init
        }

        @Override
        public Object postProcessAfterInitialization(Object bean, String beanName) {
            // Only wrap beans implementing ProductService (could also use annotation-based)
            if (bean instanceof ProductService) {
                System.out.println("  [BPP.afterInit] wrapping '" + beanName + "' in TimingProxy");
                TimingProxy tp    = new TimingProxy(bean, beanName);
                Object      proxy = Proxy.newProxyInstance(
                    bean.getClass().getClassLoader(),
                    bean.getClass().getInterfaces(),
                    tp);
                proxies.put(beanName, tp);
                return proxy;  // REPLACE the original bean with the proxy
            }
            return bean;
        }

        void printAllStats() { proxies.values().forEach(TimingProxy::printStats); }
    }

    static <T> T initBean(T bean, String name, BeanPostProcessor bpp, Runnable init) {
        Object r = bpp.postProcessBeforeInitialization(bean, name);
        init.run();
        r = bpp.postProcessAfterInitialization(r, name);
        return (T) r;
    }

    public static void main(String[] args) throws Exception {
        TimingBPP bpp = new TimingBPP();

        System.out.println("=== Creating beans ===");
        ProductServiceImpl impl    = new ProductServiceImpl();
        ProductService     service = initBean(impl, "productService", bpp, impl::init);
        // service is now the PROXY, not the impl

        System.out.println("\n[IS PROXY?] " + (service.getClass().getName().contains("$Proxy")));
        System.out.println("\n=== Application — calls go through timing proxy ===");
        System.out.println("[SEARCH 'book'] " + service.search("book"));
        System.out.println("[GET p2] "        + service.getById("p2"));
        System.out.println("[SEARCH 'pen']  " + service.search("pen"));
        System.out.println("[GET p9] "        + service.getById("p9"));

        System.out.println();
        bpp.printAllStats();
    }
}
```

How to run: `java BPPDemo2.java`

`postProcessAfterInitialization` detects that the bean implements `ProductService` and returns a JDK dynamic proxy wrapping the original. The proxy intercepts every call, measures elapsed time, and delegates to the real bean. Callers receive the proxy — they see `ProductService`, not `ProductServiceImpl`. Stats are collected transparently.

### Level 3 — Advanced

`BeanPostProcessor` that reads a custom annotation (`@Validated`) on beans and replaces them with proxies that enforce parameter validation — a mini-framework.

```java
// BPPDemo3.java — run with: java BPPDemo3.java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class BPPDemo3 {

    interface BeanPostProcessor {
        Object postProcessBeforeInitialization(Object bean, String beanName);
        Object postProcessAfterInitialization(Object bean, String beanName);
    }

    // ── Custom validation annotation ──────────────────────────────────
    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE)
    @interface AutoValidated {}

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.PARAMETER)
    @interface NotBlank { String field() default "param"; }

    @Retention(RetentionPolicy.RUNTIME) @Target(ElementType.PARAMETER)
    @interface Positive { String field() default "param"; }

    // ── Service with validation annotations ───────────────────────────
    interface OrderService {
        String placeOrder(@NotBlank(field="productId") String productId,
                          @Positive(field="quantity") int quantity,
                          @NotBlank(field="customerId") String customerId);
        String cancelOrder(@NotBlank(field="orderId") String orderId);
    }

    @AutoValidated
    static class OrderServiceImpl implements OrderService {
        private int seq = 0;
        void init() { System.out.println("    [OrderServiceImpl.init] ready"); }

        @Override
        public String placeOrder(String productId, int quantity, String customerId) {
            return "ORD-" + (++seq) + "[" + productId + "×" + quantity + " for " + customerId + "]";
        }
        @Override
        public String cancelOrder(String orderId) { return "CANCELLED:" + orderId; }
    }

    // ── Validation proxy ──────────────────────────────────────────────
    static class ValidationProxy implements InvocationHandler {
        private final Object target;
        private final String beanName;

        ValidationProxy(Object target, String beanName) { this.target = target; this.beanName = beanName; }

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            if (args != null) {
                Parameter[] params = method.getParameters();
                for (int i = 0; i < args.length; i++) {
                    NotBlank nb = params[i].getAnnotation(NotBlank.class);
                    Positive  p  = params[i].getAnnotation(Positive.class);
                    if (nb != null && (args[i] == null || args[i].toString().isBlank()))
                        throw new IllegalArgumentException("[" + beanName + "." + method.getName()
                            + "] '" + nb.field() + "' must not be blank, got: " + args[i]);
                    if (p != null && args[i] instanceof Number n && n.intValue() <= 0)
                        throw new IllegalArgumentException("[" + beanName + "." + method.getName()
                            + "] '" + p.field() + "' must be positive, got: " + args[i]);
                }
            }
            System.out.println("  [VALIDATE OK] " + beanName + "." + method.getName());
            return method.invoke(target, args);
        }
    }

    // ── BPP that reads @AutoValidated and wraps matching beans ────────
    static class ValidationBPP implements BeanPostProcessor {
        private final Set<String> wrapped = new HashSet<>();

        @Override
        public Object postProcessBeforeInitialization(Object bean, String beanName) { return bean; }

        @Override
        public Object postProcessAfterInitialization(Object bean, String beanName) {
            if (bean.getClass().isAnnotationPresent(AutoValidated.class)) {
                System.out.println("  [ValidationBPP] @AutoValidated found on '" + beanName + "' — wrapping");
                wrapped.add(beanName);
                return Proxy.newProxyInstance(
                    bean.getClass().getClassLoader(),
                    bean.getClass().getInterfaces(),
                    new ValidationProxy(bean, beanName));
            }
            return bean;
        }

        Set<String> wrapped() { return wrapped; }
    }

    @SuppressWarnings("unchecked")
    static <T> T initBean(T bean, String name, BeanPostProcessor bpp, Runnable init) {
        Object r = bpp.postProcessBeforeInitialization(bean, name);
        init.run();
        r = bpp.postProcessAfterInitialization(r, name);
        return (T) r;
    }

    public static void main(String[] args) {
        ValidationBPP bpp = new ValidationBPP();

        System.out.println("=== Container starting ===");
        OrderServiceImpl impl    = new OrderServiceImpl();
        OrderService     service = initBean(impl, "orderService", bpp, impl::init);

        System.out.println("\n[WRAPPED] " + bpp.wrapped());

        System.out.println("\n=== Valid calls ===");
        System.out.println(service.placeOrder("Notebook", 2, "alice"));
        System.out.println(service.placeOrder("Pen",      5, "bob"));
        System.out.println(service.cancelOrder("ORD-1"));

        System.out.println("\n=== Validation failures ===");
        try { service.placeOrder("",         2, "alice"); }
        catch (IllegalArgumentException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
        try { service.placeOrder("Notebook", 0, "alice"); }
        catch (IllegalArgumentException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
        try { service.placeOrder("Notebook", 3, ""); }
        catch (IllegalArgumentException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
        try { service.cancelOrder("   "); }
        catch (IllegalArgumentException e) { System.out.println("[EXPECTED] " + e.getMessage()); }
    }
}
```

How to run: `java BPPDemo3.java`

`ValidationBPP.postProcessAfterInitialization` checks whether the bean class has `@AutoValidated`. If so, it returns a proxy that reads `@NotBlank` and `@Positive` parameter annotations on each method call and validates the arguments before delegating. The `OrderServiceImpl` class has no validation logic — the `BeanPostProcessor` injects it transparently.

## 6. Walkthrough

**Level 3 proxy-wrapping trace:**

```
=== Container startup ===
  new OrderServiceImpl()                    ← ① constructor
  bpp.postProcessBeforeInitialization(impl, "orderService")
    → bean.getClass().isAnnotationPresent(@AutoValidated) = false (before check)
    → return impl (unchanged)               ← ④ beforeInit
  impl.init()                              ← ⑤ @PostConstruct
  bpp.postProcessAfterInitialization(impl, "orderService")
    → @AutoValidated found on OrderServiceImpl → YES
    → Proxy.newProxyInstance([OrderService], ValidationProxy(impl, "orderService"))
    → return proxy                          ← ⑥ afterInit — REPLACED in context!

=== service = the PROXY (not impl) ===

service.placeOrder("", 2, "alice"):
  ValidationProxy.invoke(method=placeOrder, args=["", 2, "alice"])
    param[0]: @NotBlank(field="productId")  → "" is blank → throw IllegalArgumentException
    → [EXPECTED] [orderService.placeOrder] 'productId' must not be blank, got: 

service.placeOrder("Notebook", 0, "alice"):
  param[1]: @Positive(field="quantity") → 0 <= 0 → throw IllegalArgumentException
    → [EXPECTED] ... 'quantity' must be positive, got: 0

service.placeOrder("Notebook", 2, "alice"):
  All params valid → [VALIDATE OK] orderService.placeOrder
  method.invoke(impl, ["Notebook", 2, "alice"]) → "ORD-1[Notebook×2 for alice]"
```

## 7. Gotchas & takeaways

> **`BeanPostProcessor` beans themselves are instantiated early — before any other beans.** Spring detects BPPs in the bean definitions and instantiates them first so they can process all other beans. A BPP cannot be `@Autowired` with other application beans during its own construction (those beans don't exist yet). Use `BeanFactoryAware` or `@Lazy` for late-resolved dependencies.

> **Returning `null` from either method throws `IllegalStateException`.** Always return a non-null object. If the bean must be replaced with null (extremely rare), Spring has other mechanisms — but null from a BPP is a bug.

- AOP proxying (`@Transactional`, `@Cacheable`, `@Async`) is implemented by `AbstractAutoProxyCreator extends BeanPostProcessor`. The proxy is returned from `postProcessAfterInitialization` — so `@PostConstruct` runs on the original, but callers of the bean get the proxy.
- A BPP can selectively process beans by checking `beanName` or the bean's class/annotations. Processing every bean in `postProcessBeforeInitialization` when you only care about a few is wasteful — filter early.
- `InstantiationAwareBeanPostProcessor` (extends `BeanPostProcessor`) adds hooks for before and after property injection — even before construction in some cases. Spring's `@Autowired` processing uses this.
- Thread safety: BPP methods may be called concurrently if beans are created in parallel (Spring uses parallel bean creation). Keep BPP state immutable or synchronized.
