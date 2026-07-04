---
card: spring-framework
gi: 225
slug: introductions-declareparents
title: "Introductions (@DeclareParents)"
---

## 1. What it is

An **introduction** adds new methods or interfaces to an existing class without modifying its source code. In Spring AOP this is achieved with the `@DeclareParents` annotation in an `@Aspect` class. It tells Spring: "make the proxy for these target types also implement this new interface, backed by this default implementation."

```java
@DeclareParents(value = "com.example.service.*+", defaultImpl = DefaultAuditable.class)
public static Auditable mixin;
```

After this declaration, every bean whose class is in `com.example.service` (including subclasses) can be cast to `Auditable` at runtime.

## 2. Why & when

Introductions are useful when:
- You want to **retrofit behaviour** onto existing classes without inheritance.
- You want to add **tracking state** to beans at runtime (access counter, last-modified timestamp).
- You want a class to **appear to implement a new interface** for integration purposes (legacy code that must satisfy a new contract).
- You want to add `equals`/`hashCode` or `toString` based on a mixin.

Introductions are rare but powerful. The most common real-world use is adding an auditing mixin (e.g., `Auditable { getCreatedBy(); setCreatedBy(); }`) to all entities in a Spring Data context.

## 3. Core concept

Think of an introduction as a costume prop room. Every actor (bean) gets a prop (the mixin interface + implementation) handed to them at the stage door (proxy creation). The audience (caller code) can now interact with the actor via the prop. The actor's original script (source code) hasn't changed.

`@DeclareParents` has two attributes:
- `value` — AspectJ type pattern selecting which beans receive the introduction. `+` means "and all subtypes."
- `defaultImpl` — the class that provides the implementation of the introduced interface.

The mixin instance (a `defaultImpl` instance) is stored per-proxy. Each proxy gets its own `defaultImpl` instance — state is per bean, not shared.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Original class -->
  <rect x="15" y="60" width="140" height="80" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="85" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">ProductService</text>
  <text x="85" y="102" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">create()</text>
  <text x="85" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">delete()</text>

  <!-- @DeclareParents arrow -->
  <line x1="155" y1="100" x2="210" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a)"/>
  <text x="183" y="92" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@DeclareParents</text>

  <!-- CGLIB Proxy (implements both) -->
  <rect x="210" y="40" width="200" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="62" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">CGLIB Proxy</text>
  <line x1="220" y1="70" x2="400" y2="70" stroke="#8b949e" stroke-width="0.5"/>

  <rect x="225" y="78" width="165" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="313" y="96" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ProductService API</text>

  <rect x="225" y="112" width="165" height="28" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="313" y="130" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Auditable (introduced)</text>

  <rect x="225" y="146" width="165" height="20" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="313" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DefaultAuditable (state)</text>

  <!-- Cast arrow -->
  <line x1="410" y1="125" x2="470" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>
  <text x="440" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cast to</text>
  <rect x="470" y="107" width="130" height="36" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="128" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Auditable</text>

  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#79c0ff"/></marker>
  </defs>
</svg>

The proxy simultaneously exposes `ProductService`'s original API and the introduced `Auditable` interface.

## 5. Runnable example

Scenario: a **product catalogue** where all service beans get an `Auditable` mixin without modifying any service source code.

### Level 1 — Basic

Minimal introduction: cast any service bean to `Auditable` and call its methods.

```java
// DeclareParentsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

interface Auditable {
    String getCreatedBy();
    void   setCreatedBy(String user);
}

class DefaultAuditable implements Auditable {
    private String createdBy = "system";
    public String getCreatedBy() { return createdBy; }
    public void   setCreatedBy(String user) { this.createdBy = user; }
}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class DeclareParentsDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclareParentsDemo.class);
        Object svc = ctx.getBean(ProductService.class);

        // Original API
        ((ProductService) svc).create("Widget");

        // Introduced API — cast to the mixin interface
        Auditable auditable = (Auditable) svc;
        auditable.setCreatedBy("alice");
        System.out.println("Created by: " + auditable.getCreatedBy());
        ctx.close();
    }
}

@Service
class ProductService {
    public void create(String name) { System.out.println("Created product: " + name); }
}

@Aspect
@Component
class AuditIntroductionAspect {
    @DeclareParents(value = "ProductService+", defaultImpl = DefaultAuditable.class)
    public static Auditable mixin;
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. DeclareParentsDemo.java`

`(Auditable) svc` succeeds because the CGLIB proxy implements `Auditable`. `auditable.setCreatedBy("alice")` stores state in the `DefaultAuditable` instance held inside the proxy.

---

### Level 2 — Intermediate

Apply the introduction to all beans in a package (wildcard type pattern) and use it across multiple service beans.

```java
// DeclareParentsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

interface AccessTracked {
    int  getAccessCount();
    void recordAccess();
}

class DefaultAccessTracked implements AccessTracked {
    private int count = 0;
    public int  getAccessCount() { return count; }
    public void recordAccess()   { count++; }
}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class DeclareParentsDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclareParentsDemo.class);
        var product = ctx.getBean(ProductService.class);
        var order   = ctx.getBean(OrderService.class);

        product.create("Bolt");
        product.create("Nut");
        order.place("ORD-1");

        System.out.println("Product accesses: " + ((AccessTracked) product).getAccessCount());
        System.out.println("Order accesses:   " + ((AccessTracked) order).getAccessCount());
        ctx.close();
    }
}

@Service class ProductService { public void create(String n) { System.out.println("Created: " + n); } }
@Service class OrderService   { public void place(String id)  { System.out.println("Placed: " + id); } }

@Aspect
@Component
class TrackingIntroductionAspect {
    // Introduce AccessTracked to ALL classes annotated @Service
    @DeclareParents(value = "@within(org.springframework.stereotype.Service)+",
                    defaultImpl = DefaultAccessTracked.class)
    public static AccessTracked mixin;

    // Advice: increment counter on every service method call
    @Before("execution(* *(..)) && this(tracked)")
    public void countAccess(AccessTracked tracked) {
        tracked.recordAccess();
    }
}
```

How to run: same classpath

`@within(org.springframework.stereotype.Service)+` matches all classes (and subtypes) annotated with `@Service`. Both `ProductService` and `OrderService` get the mixin. Each has its own `DefaultAccessTracked` instance — separate counters.

---

### Level 3 — Advanced

Use the introduced interface in advice: combine `@DeclareParents` with `@Before` that reads from the mixin to implement conditional throttling.

```java
// DeclareParentsDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;
import java.util.concurrent.atomic.*;

interface RateLimited {
    boolean tryConsume();
    long    getCallCount();
}

class LeakyBucket implements RateLimited {
    private final AtomicLong count = new AtomicLong();
    private final int limit;
    LeakyBucket(int limit) { this.limit = limit; }
    LeakyBucket() { this(5); }  // default ctor required by Spring
    public boolean tryConsume() {
        long c = count.incrementAndGet();
        return c <= limit;
    }
    public long getCallCount() { return count.get(); }
}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class DeclareParentsDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclareParentsDemo.class);
        var svc = ctx.getBean(ApiService.class);
        for (int i = 1; i <= 7; i++) {
            try {
                svc.fetch("resource-" + i);
            } catch (IllegalStateException e) {
                System.out.println("Throttled call #" + i + ": " + e.getMessage());
            }
        }
        System.out.println("Total call count: " + ((RateLimited) svc).getCallCount());
        ctx.close();
    }
}

@Service
class ApiService {
    public String fetch(String resource) {
        System.out.println("Fetched: " + resource);
        return "data:" + resource;
    }
}

@Aspect
@Component
class ThrottleIntroductionAspect {
    @DeclareParents(value = "ApiService+", defaultImpl = LeakyBucket.class)
    public static RateLimited mixin;

    @Before("execution(* ApiService.*(..)) && this(bucket)")
    public void throttle(RateLimited bucket) {
        if (!bucket.tryConsume()) {
            throw new IllegalStateException("Rate limit exceeded (calls=" + bucket.getCallCount() + ")");
        }
    }
}
```

How to run: same classpath

The `@Before` advice uses `this(bucket)` to bind the proxy itself as `RateLimited` (the introduced interface). `bucket.tryConsume()` checks the per-bean counter stored in `LeakyBucket`. After 5 successful calls, attempts 6 and 7 are throttled.

## 6. Walkthrough

**Proxy creation with `@DeclareParents` (Level 1):**
1. `AnnotationAwareAspectJAutoProxyCreator` processes `AuditIntroductionAspect`.
2. It finds `@DeclareParents(value = "ProductService+", defaultImpl = DefaultAuditable.class)`.
3. When creating the CGLIB proxy for `ProductService`, it adds `Auditable` to the list of interfaces the proxy implements.
4. A `DefaultAuditable` instance is created and associated with the proxy as the `IntroductionAdvisor`'s delegate.

**Cast mechanics (Level 1):**
- `(Auditable) svc` → CGLIB proxy implements `Auditable` → cast succeeds.
- `auditable.setCreatedBy("alice")` → proxy's `IntroductionInterceptor` delegates to `DefaultAuditable.setCreatedBy("alice")`.
- `auditable.getCreatedBy()` → delegates to `DefaultAuditable.getCreatedBy()` → returns `"alice"`.

**Per-bean state (Level 2):**
- `ProductService` proxy gets its own `DefaultAccessTracked` instance (call it A).
- `OrderService` proxy gets its own `DefaultAccessTracked` instance (call it B).
- `product.create()` calls twice → A.count = 2.
- `order.place()` calls once → B.count = 1.
- Independent state: `((AccessTracked) product).getAccessCount()` = 2, `((AccessTracked) order).getAccessCount()` = 1.

**`this(tracked)` binding in `@Before` (Level 3):**
- `this(tracked)` binds the AOP proxy itself (not the target) to `RateLimited tracked`.
- Since the proxy implements `RateLimited` (via `@DeclareParents`), the cast and binding succeed.
- Every call to any `ApiService` method goes through this `@Before`, which decrements the bucket.

## 7. Gotchas & takeaways

> **The `defaultImpl` class must have a no-arg constructor.** Spring instantiates it with reflection. If the class only has parameterised constructors, Spring throws `BeanInstantiationException`. Add a no-arg constructor (even package-private).

> **`this(tracked)` gives you the proxy; `target(tracked)` gives you the real bean.** For introductions, you almost always want `this(tracked)` because the introduced interface is on the proxy, not on the target class. `target(tracked)` will fail to bind since the target doesn't implement `RateLimited`.

- Introductions add methods but not fields to the target class. State lives in the `defaultImpl` instance stored in the proxy, not in the original bean.
- Each proxied bean gets its own `defaultImpl` instance — per-instance state, not shared across all beans.
- `@DeclareParents` is rarely needed but powerful for retrofitting. Spring Data uses a similar mechanism internally for repository implementations.
- The static field type of `mixin` must match the introduced interface — it is a compile-time declaration hint, not a runtime instance.
