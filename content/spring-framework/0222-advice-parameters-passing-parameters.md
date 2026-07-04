---
card: spring-framework
gi: 222
slug: advice-parameters-passing-parameters
title: Advice parameters & passing parameters
---

## 1. What it is

Advice methods receive parameters that Spring AOP binds automatically. Beyond the optional `JoinPoint` (or `ProceedingJoinPoint` for `@Around`), you can bind:
- **Method arguments** — via `args(paramName, ..)` in the pointcut, binding actual call-site values by name and type.
- **Return value** — via `returning = "paramName"` in `@AfterReturning`.
- **Thrown exception** — via `throwing = "paramName"` in `@AfterThrowing`.
- **Annotation instance** — by naming the annotation type in the pointcut, giving the advice access to annotation attributes.
- **Target or proxy** — via `target(paramName)` or `this(paramName)`.

This is more ergonomic than casting from `JoinPoint.getArgs()[0]` and also acts as a type filter.

## 2. Why & when

Without parameter binding, accessing method arguments requires:
```java
String email = (String) jp.getArgs()[0]; // error-prone cast
```

With binding:
```java
@Before("execution(* UserService.register(String)) && args(email)")
public void before(String email) { ... } // type-safe, no cast
```

Parameter binding also documents the pointcut's intent: `args(email)` tells readers exactly which argument the advice cares about.

Use parameter binding whenever you need to:
- Access typed method arguments in advice.
- Access annotation attribute values (e.g., `@Cacheable` key attribute).
- Filter by argument type at runtime.

## 3. Core concept

Spring AOP resolves advice parameters by matching the parameter names and types in the advice method signature against the binding specified in the pointcut expression. The matching is name-based — the variable name in `args(email)` must match the parameter name `String email` in the advice method.

How each binding mechanism works:

| Mechanism | Pointcut expression | Advice parameter |
|-----------|--------------------|--------------------|
| Method arg | `args(email, ..)` | `String email` |
| Method arg (typed) | `args(String, ..)` | positional — no binding |
| Annotation instance | `@annotation(logged)` | `Logged logged` |
| Target type | `target(svc)` | `UserService svc` |
| Return value | `returning = "result"` | `String result` (in `@AfterReturning`) |
| Thrown exception | `throwing = "ex"` | `IOException ex` (in `@AfterThrowing`) |

## 4. Diagram

<svg viewBox="0 0 640 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Method call -->
  <rect x="15" y="50" width="200" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="74" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">register("alice@…")</text>
  <text x="115" y="92" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">actual args: ["alice@…"]</text>

  <!-- Arrow -->
  <line x1="215" y1="80" x2="270" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="243" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring binds</text>

  <!-- Advice parameter list -->
  <rect x="270" y="40" width="340" height="140" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="62" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Advice method parameters</text>

  <rect x="285" y="70" width="310" height="25" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="440" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">JoinPoint jp  — always available</text>

  <rect x="285" y="100" width="310" height="25" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="440" y="117" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">String email  ← args(email)</text>

  <rect x="285" y="130" width="310" height="25" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="440" y="147" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Logged ann  ← @annotation(ann)</text>

  <rect x="285" y="158" width="310" height="15" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="440" y="169" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">UserService target  ← target(target)</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#79c0ff"/></marker>
  </defs>
</svg>

Spring binds call-site values to advice parameters by matching names in the pointcut expression to parameter names in the advice method.

## 5. Runnable example

Scenario: a **notification pipeline** — first binding a single argument, then binding an annotation instance, then binding multiple parameters including a target type.

### Level 1 — Basic

Bind the `email` argument of `sendNotification(String email)` to the advice parameter.

```java
// AdviceParamDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AdviceParamDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdviceParamDemo.class);
        ctx.getBean(NotificationService.class).send("alice@example.com", "Welcome!");
        ctx.close();
    }
}

@Service
class NotificationService {
    public void send(String email, String message) {
        System.out.println("Sent '" + message + "' to " + email);
    }
}

@Aspect
@Component
class ParamAspect {
    // args(email, ..) binds the first String argument to 'email' parameter
    @Before("execution(* NotificationService.send(..)) && args(email, ..)")
    public void beforeSend(JoinPoint jp, String email) {
        System.out.println("[PARAM] Sending to: " + email);
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AdviceParamDemo.java`

`args(email, ..)` binds the first argument to `String email`. The `..` matches any additional arguments. No casting required.

---

### Level 2 — Intermediate

Bind an annotation instance to access its attributes in the advice.

```java
// AdviceParamDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Channel { String value() default "email"; String priority() default "normal"; }

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AdviceParamDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdviceParamDemo.class);
        var svc = ctx.getBean(NotificationService.class);
        svc.sendEmail("alice@example.com", "Invoice");
        svc.sendSms("+1-555-0100", "Verification code");
        ctx.close();
    }
}

@Service
class NotificationService {
    @Channel(value = "email", priority = "high")
    public void sendEmail(String address, String message) {
        System.out.println("Email → " + address + ": " + message);
    }

    @Channel(value = "sms", priority = "normal")
    public void sendSms(String phone, String message) {
        System.out.println("SMS → " + phone + ": " + message);
    }
}

@Aspect
@Component
class ChannelAspect {
    // @annotation(ch) binds the @Channel annotation instance to 'ch'
    @Before("@annotation(ch)")
    public void onChannel(JoinPoint jp, Channel ch) {
        System.out.printf("[CHANNEL] method=%s channel=%s priority=%s%n",
            jp.getSignature().getName(), ch.value(), ch.priority());
    }
}
```

How to run: same classpath

`@annotation(ch)` binds the actual `@Channel` instance to the `Channel ch` parameter. `ch.value()` and `ch.priority()` return the annotation attribute values at runtime.

---

### Level 3 — Advanced

Bind multiple parameters simultaneously: method argument, annotation instance, and the target bean.

```java
// AdviceParamDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface RateLimit { int perSecond() default 10; }

interface Sender { void send(String recipient, String body); }

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AdviceParamDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdviceParamDemo.class);
        var svc = ctx.getBean(NotificationService.class);
        svc.send("carol@example.com", "Hello");
        svc.send("dave@example.com", "Hi");
        ctx.close();
    }
}

@Service
class NotificationService implements Sender {
    @RateLimit(perSecond = 5)
    public void send(String recipient, String body) {
        System.out.println("Sent '" + body + "' → " + recipient);
    }
}

@Aspect
@Component
class RateLimitAspect {
    // Bind: annotation instance (rl), first arg (recipient), target bean (svc)
    @Before(
        "execution(* Sender.send(..)) && @annotation(rl) && args(recipient, ..) && target(svc)"
    )
    public void checkRate(JoinPoint jp, RateLimit rl, String recipient, Sender svc) {
        System.out.printf("[RATE_LIMIT] method=%s limit=%d/s recipient=%s svcClass=%s%n",
            jp.getSignature().getName(),
            rl.perSecond(),
            recipient,
            svc.getClass().getSimpleName());
    }
}
```

How to run: same classpath

Four items are bound: `JoinPoint jp` (always available), `RateLimit rl` (annotation instance), `String recipient` (first method arg), `Sender svc` (the target bean). Spring resolves all bindings at startup via parameter name matching and type checking.

## 6. Walkthrough

**Parameter binding resolution at startup:**
1. Spring reads `@Before("... && args(recipient, ..) && target(svc)")`.
2. It parses the pointcut expression and extracts named parameters: `recipient`, `svc`, `rl`.
3. It reads the advice method signature: `(JoinPoint jp, RateLimit rl, String recipient, Sender svc)`.
4. It matches `recipient` → `String recipient` (type `String`), `svc` → `Sender svc` (type `Sender`), `rl` → `RateLimit rl` (annotation type from `@annotation(rl)`).
5. Compiles the final `ArgBinding` rule that maps parameter positions.

**At call time (`svc.send("carol@example.com", "Hello")`):**
1. Proxy intercepts.
2. Spring evaluates the pointcut: does the method match all clauses?
   - `execution(* Sender.send(..))` → yes.
   - `@annotation(rl)` → yes (`@RateLimit` present). Binds annotation instance to `rl`.
   - `args(recipient, ..)` → yes (first arg is `String`). Binds `"carol@example.com"` to `recipient`.
   - `target(svc)` → yes. Binds `NotificationService` instance to `svc`.
3. Calls `RateLimitAspect.checkRate(jp, rateLimit, "carol@example.com", notificationService)`.
4. Advice prints the rate limit info.
5. Real `send` runs.

**`target(svc)` vs `this(svc)` difference:**
- `target(svc)` → `svc` is the real `NotificationService` bean (not the proxy).
- `this(svc)` → `svc` is the CGLIB proxy wrapping it.
- For most advice, `target` is what you want (access real state). Use `this` when you need to call another method on the proxy.

**Expected output:**
```
[RATE_LIMIT] method=send limit=5/s recipient=carol@example.com svcClass=NotificationService
Sent 'Hello' → carol@example.com
[RATE_LIMIT] method=send limit=5/s recipient=dave@example.com svcClass=NotificationService
Sent 'Hi' → dave@example.com
```

## 7. Gotchas & takeaways

> **Parameter name in `args(name)` must exactly match the advice method's parameter name.** `args(email)` requires a parameter named `email` in the advice. If you name it `address`, Spring throws `IllegalArgumentException: Unbound pointcut parameter 'address'` at startup.

> **`args(String)` (no name) is a type-only filter — it does NOT bind.** To bind, you must use `args(paramName)` where `paramName` matches an advice parameter. `args(String, ..)` only checks "is the first argument a String" but does not bind a value to the advice.

- Java 8+ parameter names in compiled bytecode (`-parameters` javac flag) are needed for automatic name resolution in some Spring versions. Otherwise, name matching is done via annotation attribute values.
- `@annotation(ann)` binds the annotation instance; `@within(ann)` and `@target(ann)` can also be used to bind class-level annotations, but they bind the annotation type, not an instance.
- Combining `args(a, b)` with `execution(* *(String, int))` narrows both by position and by name — a powerful combination.
- For `@Around`, `ProceedingJoinPoint pjp` must be the FIRST parameter. Named bindings come after: `(ProceedingJoinPoint pjp, String email)`.
