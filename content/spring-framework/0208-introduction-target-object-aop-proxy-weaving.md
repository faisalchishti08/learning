---
card: spring-framework
gi: 208
slug: introduction-target-object-aop-proxy-weaving
title: "Introduction, Target object, AOP proxy, Weaving"
---

## 1. What it is

Four more AOP terms that describe *how* advice gets wired into the program:

- **Target object** — the real bean being proxied. The object that contains the actual business logic.
- **AOP proxy** — the object Spring creates to wrap the target and intercept calls. Spring uses JDK dynamic proxies (interface-based) or CGLIB subclass proxies (class-based).
- **Weaving** — the process of applying aspects to target objects. Spring does this at *runtime* when the application context starts.
- **Introduction** — a special kind of advice that adds new methods or fields to a class without modifying its source. Lets you say "make this existing class implement a new interface."

## 2. Why & when

You need these terms to:
- Understand why Spring creates a proxy wrapper around your beans.
- Diagnose why calling `this.method()` inside a bean bypasses the aspect (self-invocation proxy bypass).
- Know when to use JDK proxy vs CGLIB.
- Use `Introduction` to retrofit behaviour onto existing classes (e.g., add auditable tracking to any bean).

## 3. Core concept

Think of a proxy as a bodyguard. The client talks to the bodyguard; the bodyguard checks credentials (runs advice), then lets the client through to the real person (the target). The client never knows the bodyguard was there.

**Weaving happens at three possible times:**
| When | Who | Spring uses? |
|------|-----|--------------|
| Compile time | AspectJ compiler | No (requires full AspectJ) |
| Load time | Java agent (LTW) | Optional (AspectJ LTW) |
| **Runtime** | Spring proxy | **Yes — default** |

**JDK dynamic proxy** — requires the target to implement at least one interface. The proxy implements the same interface(s).

**CGLIB proxy** — subclasses the target class. Works even without an interface. Cannot proxy `final` classes or `final` methods.

**Introduction** uses `@DeclareParents` to declare that a target type "implements" a new interface, backed by a delegate.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Client -->
  <rect x="15" y="85" width="90" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>

  <!-- Arrow to proxy -->
  <line x1="105" y1="110" x2="175" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="140" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">calls</text>

  <!-- AOP Proxy -->
  <rect x="175" y="70" width="145" height="95" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="248" y="93" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">AOP Proxy</text>
  <line x1="185" y1="100" x2="310" y2="100" stroke="#8b949e" stroke-width="0.5"/>
  <text x="248" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">run advice</text>
  <text x="248" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">delegate to target</text>
  <text x="248" y="150" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">(CGLIB or JDK dynamic)</text>

  <!-- Arrow to target -->
  <line x1="320" y1="110" x2="390" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a2)"/>
  <text x="355" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">delegates</text>

  <!-- Target object -->
  <rect x="390" y="85" width="110" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="445" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Target Object</text>
  <text x="445" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(real bean)</text>

  <!-- Weaving label -->
  <text x="248" y="185" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">← weaving: applied at runtime by Spring →</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Spring *weaves* the aspect into the call chain at startup by creating a proxy that intercepts calls before they reach the target.

## 5. Runnable example

Scenario: a **document service** — first inspecting the proxy vs target, then showing self-invocation bypass, then using Introduction to add a new interface to an existing class.

### Level 1 — Basic

Inspect what Spring gives you: the proxy vs the target, and how to tell them apart.

```java
// ProxyWeavingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class ProxyWeavingDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyWeavingDemo.class);
        DocumentService svc = ctx.getBean(DocumentService.class);

        System.out.println("Bean class:   " + svc.getClass().getName());
        System.out.println("Is proxy:     " + AopUtils.isAopProxy(svc));
        System.out.println("Is CGLIB:     " + AopUtils.isCglibProxy(svc));
        System.out.println("Target class: " + AopUtils.getTargetClass(svc).getName());

        svc.create("doc-1");
        ctx.close();
    }
}

@Service
class DocumentService {
    public void create(String id) {
        System.out.println("Created document: " + id);
    }
}

@Aspect
@Component
class LogAspect {
    @Before("execution(* DocumentService.*(..))")
    public void log(org.aspectj.lang.JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().toShortString());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. ProxyWeavingDemo.java`

`svc.getClass().getName()` prints something like `DocumentService$$SpringCGLIB$$0` — a CGLIB-generated subclass, not `DocumentService` itself. `AopUtils.getTargetClass(svc)` resolves back to the real `DocumentService`.

---

### Level 2 — Intermediate

Self-invocation bypass: `create()` calls `this.archive()` internally — the proxy is bypassed and `@Before` on `archive()` never fires.

```java
// ProxyWeavingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class ProxyWeavingDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyWeavingDemo.class);
        var svc = ctx.getBean(DocumentService.class);

        System.out.println("--- call archive() through proxy ---");
        svc.archive("doc-1");   // proxy intercepts → @Before fires

        System.out.println("--- call create() which internally calls archive() ---");
        svc.create("doc-2");    // proxy intercepts create(); this.archive() bypasses proxy
        ctx.close();
    }
}

@Service
class DocumentService {
    public void create(String id) {
        System.out.println("Creating: " + id);
        this.archive(id); // SELF-INVOCATION: bypasses proxy!
    }
    public void archive(String id) {
        System.out.println("Archived: " + id);
    }
}

@Aspect
@Component
class LogAspect {
    @Before("execution(* DocumentService.archive(..))")
    public void logArchive(JoinPoint jp) {
        System.out.println("[LOG] archive() intercepted via proxy");
    }
}
```

How to run: same classpath

When `create()` calls `this.archive()`, `this` is the real `DocumentService`, not the proxy. The proxy is never involved. The `[LOG]` line appears for the direct `svc.archive()` call but not for the internal `this.archive()` call inside `create()`.

---

### Level 3 — Advanced

`@DeclareParents` (Introduction): add a `Trackable` interface to `DocumentService` without modifying its source code.

```java
// ProxyWeavingDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

// New interface we want to introduce
interface Trackable {
    int getAccessCount();
    void incrementAccess();
}

// Default implementation (delegate)
class DefaultTrackable implements Trackable {
    private int count = 0;
    public int getAccessCount() { return count; }
    public void incrementAccess() { count++; }
}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class ProxyWeavingDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyWeavingDemo.class);
        var svc = ctx.getBean(DocumentService.class);

        svc.create("doc-1");
        svc.create("doc-2");

        // DocumentService now also implements Trackable (via Introduction)
        Trackable trackable = (Trackable) svc;
        System.out.println("Access count: " + trackable.getAccessCount());
        ctx.close();
    }
}

@Service
class DocumentService {
    public void create(String id) {
        System.out.println("Created: " + id);
    }
}

@Aspect
@Component
class TrackingAspect {
    // Introduction: make DocumentService implement Trackable
    @DeclareParents(value = "DocumentService+", defaultImpl = DefaultTrackable.class)
    public static Trackable mixin;

    // Advice: increment access counter on every call
    @Before("execution(* DocumentService.*(..)) && this(trackable)")
    public void track(Trackable trackable) {
        trackable.incrementAccess();
    }
}
```

How to run: same classpath

`@DeclareParents(value = "DocumentService+")` tells Spring: the proxy for `DocumentService` should also implement `Trackable`, backed by `DefaultTrackable`. Casting `svc` to `Trackable` works because the proxy implements both interfaces. The `@Before` advice increments the counter on every call — the counter state lives in the `DefaultTrackable` mixin instance.

## 6. Walkthrough

**Weaving (Level 1):**
1. `AnnotationConfigApplicationContext` starts, creating all beans.
2. `AnnotationAwareAspectJAutoProxyCreator.postProcessAfterInitialization(bean, name)` is called for `DocumentService`.
3. The creator evaluates `LogAspect`'s pointcut `execution(* DocumentService.*(..))` against the bean.
4. Match found → creates a CGLIB proxy subclassing `DocumentService`.
5. The proxy overrides all public non-final methods to route through the advice chain.
6. The context stores the proxy under the bean name `"documentService"`.

**Self-invocation bypass (Level 2):**
- `svc.create("doc-2")` → proxy intercepts → runs `@Before` for `create` (if any) → calls real `create()` on the `DocumentService` target.
- Inside `create()`, `this` refers to the `DocumentService` instance (the target), not the proxy.
- `this.archive(id)` calls `archive` on the target directly — no proxy, no advice.

**Introduction proxy structure (Level 3):**
- The CGLIB proxy created for `DocumentService` is generated to implement both `DocumentService`'s public API AND `Trackable`.
- A `DefaultTrackable` instance is stored inside the proxy.
- Casting `(Trackable) svc` succeeds because the proxy class implements `Trackable`.
- `trackable.getAccessCount()` calls the `DefaultTrackable` instance stored in the proxy.

**State after two `create()` calls:**
- `DefaultTrackable.count = 2` (incremented once per `create()` call).
- `trackable.getAccessCount()` returns `2`.

## 7. Gotchas & takeaways

> **`final` methods cannot be proxied by CGLIB.** CGLIB creates a subclass; it cannot override `final`. Those methods bypass the proxy silently. Use interfaces + JDK proxy, or restructure to avoid `final`.

> **Self-invocation is the most common AOP mistake.** `this.method()` inside the same class skips the proxy. Fix: inject the bean as a field (`@Autowired MyService self`) and call `self.method()`.

- Weaving happens once at startup (runtime weaving). After the context is running, the proxy is fixed — you cannot add/remove aspects at runtime.
- `AopUtils.isAopProxy(bean)` returns true for any Spring AOP proxy (JDK or CGLIB). Use in tests to verify a bean is being proxied.
- `@DeclareParents` (Introduction) is powerful but rare. Most uses are: adding audit/tracking mixins, adding `toString()`/`equals()` implementations, retrofitting interfaces onto third-party classes.
- JDK proxy vs CGLIB: Spring Boot defaults to CGLIB (`@EnableAspectJAutoProxy(proxyTargetClass = true)`). JDK dynamic proxy requires the bean to implement an interface.
