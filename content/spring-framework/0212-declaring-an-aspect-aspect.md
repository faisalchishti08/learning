---
card: spring-framework
gi: 212
slug: declaring-an-aspect-aspect
title: "Declaring an aspect (@Aspect)"
---

## 1. What it is

An **aspect** is a class annotated with `@Aspect` (from `org.aspectj.lang.annotation`) that encapsulates one cross-cutting concern. It is also a Spring bean (annotated `@Component` or declared as a `@Bean`) so the container manages its lifecycle. Inside, it holds `@Pointcut` definitions and advice methods (`@Before`, `@After`, `@Around`, etc.).

`@Aspect` alone does nothing at runtime — it marks the class so `AnnotationAwareAspectJAutoProxyCreator` can find it. The aspect class must also be detected by Spring (via component scan or explicit bean declaration).

## 2. Why & when

Declaring an aspect class is step zero of AOP. Before you can write pointcuts and advice, you need a container for them. Key design choices:

- **One aspect per concern** — a `SecurityAspect` for security checks, a `LoggingAspect` for logging. Mixing concerns in one aspect defeats the purpose.
- **Aspect as a Spring bean** — this lets you inject other beans (`@Autowired`) into the aspect, e.g., inject a `Logger` or a `MetricRegistry`.
- **Aspect ordering** — when multiple aspects match the same join point, use `@Order(n)` to specify execution order (lower value = outer advice).

## 3. Core concept

Think of an aspect class as a department in a company. The "Compliance Department" (aspect) is responsible for all compliance work (cross-cutting concern) across all divisions (service beans). Each of its staff members (advice methods) handles a specific type of compliance event (join point). The department head (`@Aspect`) gives it authority; HR listing it as a department (`@Component`) makes it reachable.

Requirements for a valid aspect bean:

1. Annotated `@Aspect`.
2. Detected by Spring: either `@Component` + `@ComponentScan`, or declared as `@Bean` in `@Configuration`.
3. `@EnableAspectJAutoProxy` present in the context.
4. Not `final` — CGLIB needs to subclass it if it is itself a proxy target (rare, but avoid `final` on aspect classes).

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Aspect class box -->
  <rect x="100" y="20" width="440" height="160" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="45" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Aspect  @Component</text>
  <text x="320" y="62" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">class LoggingAspect</text>

  <line x1="120" y1="72" x2="520" y2="72" stroke="#8b949e" stroke-width="0.5"/>

  <!-- Fields -->
  <rect x="120" y="80" width="185" height="38" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="213" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Autowired Logger logger</text>
  <text x="213" y="111" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(inject dependencies)</text>

  <!-- Pointcut -->
  <rect x="120" y="127" width="185" height="40" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="213" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">@Pointcut(...)</text>
  <text x="213" y="159" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">void serviceLayer() {}</text>

  <!-- Advice methods -->
  <rect x="335" y="80" width="165" height="38" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="418" y="97" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@Before("serviceLayer()")</text>
  <text x="418" y="111" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">void logBefore() { ... }</text>

  <rect x="335" y="127" width="165" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="418" y="145" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@Around("serviceLayer()")</text>
  <text x="418" y="159" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Object time(PJP p) { ... }</text>
</svg>

An aspect class combines field injection, pointcut declarations, and advice methods in one place — the complete encapsulation of one cross-cutting concern.

## 5. Runnable example

Scenario: a **payment processing pipeline** with a dedicated `AuditAspect` — first the minimal aspect skeleton, then an aspect with injected dependencies, then multiple ordered aspects.

### Level 1 — Basic

Minimal valid aspect: `@Aspect` + `@Component` + one `@Before` advice.

```java
// DeclareAspectDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class DeclareAspectDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DeclareAspectDemo.class);
        ctx.getBean(PaymentService.class).charge(99.0);
        ctx.close();
    }
}

@Service
class PaymentService {
    public void charge(double amount) {
        System.out.println("Charged $" + amount);
    }
}

// THE ASPECT
@Aspect
@Component
class AuditAspect {
    @Before("execution(* PaymentService.*(..))")
    public void audit() {
        System.out.println("[AUDIT] Payment operation starting");
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. DeclareAspectDemo.java`

`@Aspect` marks it as an aspect; `@Component` makes it a Spring bean. The `@Before` advice fires before `charge()`.

---

### Level 2 — Intermediate

Aspect with `@Autowired` dependencies — inject a bean (a simple audit log store) to record events.

```java
// DeclareAspectDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.util.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class DeclareAspectDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(DeclareAspectDemo.class);
        ctx.getBean(PaymentService.class).charge(50.0);
        ctx.getBean(PaymentService.class).refund(20.0);
        var log = ctx.getBean(AuditLog.class);
        System.out.println("Audit log: " + log.entries());
        ctx.close();
    }
}

@Service
class PaymentService {
    public void charge(double amount) { System.out.println("Charged $" + amount); }
    public void refund(double amount) { System.out.println("Refunded $" + amount); }
}

@Component
class AuditLog {
    private final List<String> log = new ArrayList<>();
    public void record(String entry) { log.add(entry); }
    public List<String> entries() { return Collections.unmodifiableList(log); }
}

@Aspect
@Component
class AuditAspect {
    @org.springframework.beans.factory.annotation.Autowired
    private AuditLog auditLog;  // injected dependency

    @Before("execution(* PaymentService.*(..))")
    public void audit(JoinPoint jp) {
        String entry = jp.getSignature().getName() + "(" + Arrays.toString(jp.getArgs()) + ")";
        auditLog.record(entry);
        System.out.println("[AUDIT] Recorded: " + entry);
    }
}
```

How to run: same classpath

`@Autowired AuditLog auditLog` injects the `AuditLog` bean into the aspect. The aspect stores call records for later retrieval — a pattern used by security auditing, compliance logging, and analytics.

---

### Level 3 — Advanced

Multiple ordered aspects — `SecurityAspect` (outer, `@Order(1)`) checks authorisation before `AuditAspect` (inner, `@Order(2)`) records the event.

```java
// DeclareAspectDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.core.annotation.Order;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.util.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class DeclareAspectDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new AnnotationConfigApplicationContext(DeclareAspectDemo.class);
        System.out.println("--- authorised user ---");
        ctx.getBean(PaymentService.class).charge(100.0);

        System.out.println("--- unauthorised user ---");
        try {
            ctx.getBean(PaymentService.class).chargeAsGuest(50.0);
        } catch (SecurityException e) {
            System.out.println("Blocked: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class PaymentService {
    public void charge(double amount) { System.out.println("Charged $" + amount); }
    public void chargeAsGuest(double amount) { System.out.println("Guest charge $" + amount); }
}

@Aspect
@Component
@Order(1)   // outer — runs first on entry, last on exit
class SecurityAspect {
    @Around("execution(* PaymentService.chargeAsGuest(..))")
    public Object checkSecurity(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("[SECURITY] Checking authorisation...");
        throw new SecurityException("Guest users may not charge");
    }

    @Before("execution(* PaymentService.charge(..))")
    public void allowCharge(JoinPoint jp) {
        System.out.println("[SECURITY] Authorised: charge()");
    }
}

@Aspect
@Component
@Order(2)   // inner — runs after Security enters, before Security exits
class AuditAspect {
    @Before("execution(* PaymentService.*(..))")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

`@Order(1)` on `SecurityAspect` makes it the outermost advice — it enters first and exits last. On `chargeAsGuest`, `SecurityAspect.checkSecurity` throws before even calling `pjp.proceed()`, so `AuditAspect` never sees the join point (it's inside `SecurityAspect`). On `charge`, `SecurityAspect.allowCharge` runs first (order 1), then `AuditAspect.audit` (order 2).

## 6. Walkthrough

**Aspect detection at startup:**
1. `@ComponentScan` discovers `AuditAspect` and `SecurityAspect` — creates them as beans.
2. `AnnotationAwareAspectJAutoProxyCreator` calls `isAspect(beanClass)` — finds `@Aspect` on both.
3. Both are added to the list of advisor sources.

**Proxy creation for `PaymentService`:**
1. `PaymentService` is instantiated.
2. `AnnotationAwareAspectJAutoProxyCreator` evaluates all advisors against `PaymentService`.
3. `SecurityAspect` matches `chargeAsGuest` and `charge`; `AuditAspect` matches all methods.
4. CGLIB proxy wrapping `PaymentService` is created with the advice chain ordered by `@Order`.

**`charge(100.0)` execution flow:**
- Proxy receives call → advice chain: `SecurityAspect.allowCharge` (`@Order(1)`) → `AuditAspect.audit` (`@Order(2)`) → real `PaymentService.charge(100.0)`.
- Returns.

**`chargeAsGuest(50.0)` execution flow:**
- Proxy receives call → `SecurityAspect.checkSecurity` (`@Order(1)`) throws `SecurityException`.
- `AuditAspect.audit` is *never called* — it is inside `SecurityAspect` in the advice stack.
- Exception propagates to caller.

**Dependency injection into aspects:**
- `AuditAspect` is a singleton bean. `@Autowired AuditLog auditLog` is resolved by the container the same way it is for any other bean.
- The aspect is fully Spring-managed: supports `@PostConstruct`, `@PreDestroy`, `@Value`, `@Conditional`.

**Expected output:**
```
--- authorised user ---
[SECURITY] Authorised: charge()
[AUDIT] charge
Charged $100.0
--- unauthorised user ---
[SECURITY] Checking authorisation...
Blocked: Guest users may not charge
```

## 7. Gotchas & takeaways

> **`@Aspect` alone is not enough — the class must also be a Spring bean.** If you forget `@Component` (or a `@Bean` declaration), Spring will not detect the aspect and no proxies are created. No error is thrown.

> **Aspect classes should not be proxied themselves.** If an `@Aspect` bean matches its own pointcut, Spring detects the circular proxy scenario and skips proxying the aspect class. Design pointcuts to exclude the aspect package.

- Keep aspects focused: one concern per aspect (logging, security, metrics, transactions — each in its own class).
- Use `@Order` explicitly when aspects share join points — undefined order leads to non-deterministic behaviour.
- Aspect beans are singletons by default, like any Spring bean. Their fields are shared across all advice invocations — make them thread-safe.
- `@DependsOn("someBean")` works on aspects — use it when the aspect must initialise after a particular bean.
- In Spring Boot, annotating the aspect `@Component` is sufficient; explicit `@EnableAspectJAutoProxy` is provided by `spring-boot-starter-aop`.
