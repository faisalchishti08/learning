---
card: spring-framework
gi: 217
slug: before-advice
title: "@Before advice"
---

## 1. What it is

`@Before` is a Spring AOP advice type that runs a method *before* the matched join point executes. The annotated method receives a `JoinPoint` (optional parameter) giving access to the method signature and arguments. The real method always runs after `@Before` returns — unlike `@Around`, `@Before` cannot skip or replace the method call.

```java
@Before("execution(* OrderService.place(..))")
public void beforePlace(JoinPoint jp) {
    System.out.println("About to place order: " + jp.getArgs()[0]);
}
```

## 2. Why & when

Use `@Before` when you need to:
- **Log** that a method is about to be called, including its arguments.
- **Validate** pre-conditions (throw `IllegalArgumentException` if invalid — this prevents the method from running).
- **Security check** — if the check throws, the method never executes.
- **Metrics**: record "method invocation count" before execution.

`@Before` is simpler than `@Around` when you don't need to modify arguments, change the return value, or catch the return. If you only care about what happens *before* the method and don't need to intercept the result, `@Before` is the right choice.

## 3. Core concept

Think of `@Before` as a doorman at a restaurant. Guests (callers) approach the door; the doorman checks the guest list (validates/logs), then opens the door (the method runs). The doorman can refuse entry by throwing an exception — but if he says nothing, the guest walks in regardless.

Key properties:
- Cannot prevent the method from running (unless it throws an exception).
- Cannot modify arguments.
- Cannot see the return value.
- Multiple `@Before` advice methods can match the same join point — they all run.
- `JoinPoint` parameter is optional; omit it if you don't need method details.

```java
@Before("myPointcut()")
public void noArgsBefore() { /* JoinPoint not needed */ }

@Before("myPointcut()")
public void withJoinPoint(JoinPoint jp) {
    jp.getSignature(); // method name, return type, params
    jp.getArgs();      // actual argument values
    jp.getTarget();    // the real bean (not the proxy)
    jp.getThis();      // the proxy
}
```

## 4. Diagram

<svg viewBox="0 0 640 175" xmlns="http://www.w3.org/2000/svg">
  <!-- Timeline -->
  <line x1="20" y1="90" x2="610" y2="90" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="315" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">time →</text>

  <!-- Caller -->
  <rect x="20" y="60" width="80" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="60" y="83" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>
  <line x1="100" y1="80" x2="160" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- @Before -->
  <rect x="160" y="55" width="130" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="225" y="77" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Before</text>
  <text x="225" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">advice runs here</text>
  <line x1="290" y1="80" x2="370" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Method -->
  <rect x="370" y="55" width="140" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="77" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Real method</text>
  <text x="440" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">always executes</text>
  <line x1="510" y1="80" x2="590" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Return -->
  <rect x="555" y="60" width="55" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="582" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">return</text>

  <!-- Exception path -->
  <line x1="225" y1="105" x2="225" y2="140" stroke="#e06c75" stroke-width="1.5" stroke-dasharray="4 2" marker-end="url(#ae)"/>
  <text x="225" y="155" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">throw → method skipped</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="ae" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#e06c75"/>
    </marker>
  </defs>
</svg>

`@Before` fires before the real method. If it throws, the method is skipped; otherwise the method always runs.

## 5. Runnable example

Scenario: an **inventory service** — first basic pre-logging, then argument validation via `@Before`, then binding argument values to the advice method's parameters.

### Level 1 — Basic

Log every method call before it executes.

```java
// BeforeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class BeforeDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BeforeDemo.class);
        var inv = ctx.getBean(InventoryService.class);
        inv.add("Bolt", 100);
        inv.remove("Bolt", 30);
        ctx.close();
    }
}

@Service
class InventoryService {
    public void add(String item, int qty) {
        System.out.println("Added " + qty + " x " + item);
    }
    public void remove(String item, int qty) {
        System.out.println("Removed " + qty + " x " + item);
    }
}

@Aspect
@Component
class LogBeforeAspect {
    @Before("execution(* InventoryService.*(..))")
    public void logBefore(JoinPoint jp) {
        System.out.printf("[BEFORE] %s args=%s%n",
            jp.getSignature().getName(),
            java.util.Arrays.toString(jp.getArgs()));
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. BeforeDemo.java`

`[BEFORE]` prints before each method. `jp.getArgs()` returns `["Bolt", 100]` and `["Bolt", 30]` respectively.

---

### Level 2 — Intermediate

Use `@Before` for validation: throw `IllegalArgumentException` if quantity is negative, preventing the method from executing.

```java
// BeforeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class BeforeDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BeforeDemo.class);
        var inv = ctx.getBean(InventoryService.class);
        System.out.println("--- valid add ---");
        inv.add("Bolt", 50);
        System.out.println("--- invalid add (negative qty) ---");
        try {
            inv.add("Nut", -5);  // @Before throws → method never runs
        } catch (IllegalArgumentException e) {
            System.out.println("Blocked: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class InventoryService {
    public void add(String item, int qty) {
        System.out.println("Added " + qty + " x " + item);
    }
}

@Aspect
@Component
class ValidationAspect {
    @Before("execution(* InventoryService.add(String, int)) && args(item, qty)")
    public void validateQuantity(JoinPoint jp, String item, int qty) {
        if (qty < 0) {
            throw new IllegalArgumentException(
                "Quantity must be non-negative for item: " + item + " (was " + qty + ")");
        }
        System.out.println("[VALIDATE] OK: " + item + " qty=" + qty);
    }
}
```

How to run: same classpath

`args(item, qty)` in the pointcut binds the method's actual arguments to the advice parameters `String item` and `int qty` — no casting from `Object[]` required. When qty is negative, the exception propagates directly to the caller and `add()` is never executed.

---

### Level 3 — Advanced

Multiple `@Before` methods for the same join point — ordered with `@Order`. First security check, then validation, then logging.

```java
// BeforeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.core.annotation.Order;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class BeforeDemo {
    static boolean authenticated = true; // simulate security context

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(BeforeDemo.class);
        var inv = ctx.getBean(InventoryService.class);

        System.out.println("=== authenticated, valid ===");
        inv.add("Gear", 10);

        System.out.println("=== authenticated, invalid ===");
        try { inv.add("Spring", -1); } catch (IllegalArgumentException e) {
            System.out.println("Blocked by validation: " + e.getMessage());
        }

        System.out.println("=== unauthenticated ===");
        authenticated = false;
        try { inv.add("Screw", 5); } catch (SecurityException e) {
            System.out.println("Blocked by security: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class InventoryService {
    public void add(String item, int qty) {
        System.out.println("Added " + qty + " x " + item);
    }
}

@Aspect @Component @Order(1)
class SecurityBeforeAspect {
    @Before("execution(* InventoryService.*(..))")
    public void checkAuth() {
        if (!BeforeDemo.authenticated) {
            throw new SecurityException("Not authenticated");
        }
        System.out.println("[SECURITY] Auth OK");
    }
}

@Aspect @Component @Order(2)
class ValidationBeforeAspect {
    @Before("execution(* InventoryService.add(String, int)) && args(item, qty)")
    public void validate(String item, int qty) {
        if (qty < 0) throw new IllegalArgumentException("Negative qty for " + item);
        System.out.println("[VALIDATE] OK");
    }
}

@Aspect @Component @Order(3)
class LogBeforeAspect {
    @Before("execution(* InventoryService.*(..))")
    public void log(JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().getName()
            + " " + java.util.Arrays.toString(jp.getArgs()));
    }
}
```

How to run: same classpath

`@Order(1)` makes `SecurityBeforeAspect` the outermost (runs first). If security throws, `ValidationBeforeAspect` and `LogBeforeAspect` never run and the method is skipped. If validation throws, `LogBeforeAspect` never runs. Only if all three pass does the real `add()` execute.

## 6. Walkthrough

**`inv.add("Gear", 10)` — happy path (Level 3):**
1. Proxy intercepts `add("Gear", 10)`.
2. Advice chain in `@Order` order:
   - `SecurityBeforeAspect.checkAuth()` — `authenticated = true` → prints `[SECURITY] Auth OK`.
   - `ValidationBeforeAspect.validate("Gear", 10)` — qty >= 0 → prints `[VALIDATE] OK`.
   - `LogBeforeAspect.log(jp)` — prints `[LOG] add [Gear, 10]`.
3. Real `add("Gear", 10)` runs → prints `Added 10 x Gear`.

**`inv.add("Spring", -1)` — validation failure:**
1. Proxy intercepts.
2. `SecurityBeforeAspect.checkAuth()` → passes.
3. `ValidationBeforeAspect.validate("Spring", -1)` → throws `IllegalArgumentException`.
4. Exception propagates directly through the advice chain — `LogBeforeAspect` is skipped.
5. Caller receives the exception.

**`args(item, qty)` binding (Level 2 in detail):**
- The pointcut `args(item, qty)` tells AspectJ to match methods whose first parameter is a `String` and second is an `int`, AND bind those values to `item` and `qty` in the advice method signature.
- Spring resolves `String item` and `int qty` from the advice method's parameter types.
- At the call site, Spring calls `advice.validateQuantity(jp, args[0], args[1])` — no casting.

**Expected output (authenticated, valid):**
```
=== authenticated, valid ===
[SECURITY] Auth OK
[VALIDATE] OK
[LOG] add [Gear, 10]
Added 10 x Gear
```

## 7. Gotchas & takeaways

> **`@Before` cannot modify arguments.** The arguments seen by `JoinPoint.getArgs()` are the originals. If you need to change what the method receives, use `@Around` with `pjp.proceed(newArgs)`.

> **An exception in `@Before` skips the real method.** This is intentional for validation/security. But an unintended exception (NullPointerException in the advice itself) will also silently prevent the method from running — always guard advice code carefully.

- `jp.getArgs()` returns `Object[]` — cast carefully. Use `args(typedParam)` in the pointcut to get type-safe binding.
- `JoinPoint.getSignature()` returns a `MethodSignature` when cast: `((MethodSignature) jp.getSignature()).getMethod()` gives the full `java.lang.reflect.Method`.
- For void methods, `@Before` is often sufficient. For methods with return values that you need to inspect or modify, use `@AfterReturning` or `@Around`.
- Multiple `@Before` methods matching the same join point run in an unspecified order within the same aspect; use `@Order` on the aspect classes to control cross-aspect order.
