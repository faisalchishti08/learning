---
card: spring-framework
gi: 218
slug: afterreturning-advice
title: "@AfterReturning advice"
---

## 1. What it is

`@AfterReturning` is an AOP advice type that runs *after* a matched method returns **normally** (i.e., without throwing an exception). Its key feature is the optional `returning` attribute: you name a parameter in your advice method, and Spring binds the method's actual return value to it.

```java
@AfterReturning(pointcut = "execution(* OrderService.place(..))", returning = "order")
public void afterPlace(JoinPoint jp, Order order) {
    System.out.println("Order placed: " + order.getId());
}
```

Unlike `@After`, which runs regardless of outcome, `@AfterReturning` skips entirely if the method throws.

## 2. Why & when

Use `@AfterReturning` when you need to:
- **Inspect or log the return value** after a successful call (without modifying it).
- **Trigger side effects on success**: send an event, update a cache, notify a monitor.
- **Record audit trail** of what was returned, not just that the method was called.

If you need to *modify* the return value, use `@Around` instead — `@AfterReturning` cannot change what the caller receives. It can only observe.

## 3. Core concept

Think of `@AfterReturning` as a quality-control inspector at a factory exit. Every product (method return value) that passes successfully gets inspected. Products that fail (exceptions) don't reach the inspector — they go to the exception handler (`@AfterThrowing`).

The `returning` attribute binds the return value by name matching:

```java
@AfterReturning(pointcut = "myPointcut()", returning = "result")
public void check(JoinPoint jp, Object result) { ... }
//                                     ^^^^^^  must match "result"
```

The type declared for the parameter also acts as a filter: if `result` is declared as `String`, the advice only fires when the method returns a `String`. Declare as `Object` to match any return type.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg">
  <!-- Timeline -->
  <line x1="20" y1="85" x2="610" y2="85" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>

  <!-- Caller -->
  <rect x="20" y="60" width="70" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="83" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>
  <line x1="90" y1="80" x2="140" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Method -->
  <rect x="140" y="55" width="140" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="210" y="77" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Real method</text>
  <text x="210" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">returns "Order#1"</text>

  <!-- Normal return arrow -->
  <line x1="280" y1="72" x2="340" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="310" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">return value</text>

  <!-- @AfterReturning -->
  <rect x="340" y="50" width="165" height="55" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="423" y="73" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@AfterReturning</text>
  <text x="423" y="90" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">binds return value</text>

  <!-- Return to caller -->
  <line x1="505" y1="72" x2="570" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- Exception path skips -->
  <line x1="210" y1="105" x2="210" y2="140" stroke="#e06c75" stroke-width="1.5" stroke-dasharray="4 2" marker-end="url(#ae)"/>
  <text x="290" y="155" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">exception → @AfterReturning skipped</text>

  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="ae" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#e06c75"/></marker>
  </defs>
</svg>

`@AfterReturning` intercepts the return value on the successful path; it is bypassed entirely when the method throws.

## 5. Runnable example

Scenario: a **user registration service** — first observing the return value, then type-filtering with the returning parameter, then triggering a side-effect (cache update) on success.

### Level 1 — Basic

Log the return value of `registerUser` after it returns successfully.

```java
// AfterReturningDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterReturningDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterReturningDemo.class);
        ctx.getBean(UserService.class).register("alice@example.com");
        ctx.close();
    }
}

@Service
class UserService {
    private long nextId = 1;
    public long register(String email) {
        System.out.println("Registering: " + email);
        return nextId++;
    }
}

@Aspect
@Component
class RegistrationAspect {
    @AfterReturning(
        pointcut = "execution(* UserService.register(..))",
        returning = "userId")
    public void afterRegister(JoinPoint jp, long userId) {
        System.out.println("[AFTER_RETURNING] Registered with ID=" + userId
            + " for " + jp.getArgs()[0]);
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AfterReturningDemo.java`

`returning = "userId"` binds the `long` return value to the `userId` parameter. The advice only fires for a normal return — if `register` threw, this advice would be skipped.

---

### Level 2 — Intermediate

Returning-type filter: declare the advice parameter as `String` — the advice only fires when the return type is assignable to `String`.

```java
// AfterReturningDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterReturningDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterReturningDemo.class);
        var svc = ctx.getBean(UserService.class);
        System.out.println("--- register (returns String token) ---");
        svc.registerAndGetToken("bob@example.com");  // returns String → advice fires
        System.out.println("--- count (returns int) ---");
        svc.count();  // returns int → advice does NOT fire (not String)
        ctx.close();
    }
}

@Service
class UserService {
    private int total = 0;
    public String registerAndGetToken(String email) {
        System.out.println("Registered: " + email);
        total++;
        return "token-" + total;
    }
    public int count() {
        System.out.println("Count: " + total);
        return total;
    }
}

@Aspect
@Component
class TokenAspect {
    // returning declared as String → only fires when return value is a String
    @AfterReturning(pointcut = "execution(* UserService.*(..))", returning = "token")
    public void onStringReturn(JoinPoint jp, String token) {
        System.out.println("[AfterReturning/String] method=" + jp.getSignature().getName()
            + " token=" + token);
    }
}
```

How to run: same classpath

`registerAndGetToken` returns `String` → advice fires. `count()` returns `int` → Spring checks `int` is not assignable to `String` → advice is skipped. This type-based filtering avoids explicit `instanceof` checks.

---

### Level 3 — Advanced

Trigger a side effect on success: update an in-memory cache with the newly registered user's details.

```java
// AfterReturningDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.util.*;
import java.util.concurrent.*;

record UserDto(long id, String email) {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AfterReturningDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AfterReturningDemo.class);
        var svc = ctx.getBean(UserService.class);
        svc.register("carol@example.com");
        svc.register("dave@example.com");
        var cache = ctx.getBean(UserCache.class);
        System.out.println("Cache contents: " + cache.all());
        ctx.close();
    }
}

@Service
class UserService {
    private long nextId = 100;
    public UserDto register(String email) {
        var dto = new UserDto(nextId++, email);
        System.out.println("Saved to DB: " + dto);
        return dto;
    }
}

@Component
class UserCache {
    private final Map<Long, UserDto> store = new ConcurrentHashMap<>();
    public void put(UserDto u) { store.put(u.id(), u); }
    public Collection<UserDto> all() { return store.values(); }
}

@Aspect
@Component
class CachePopulatorAspect {
    @org.springframework.beans.factory.annotation.Autowired
    private UserCache cache;

    @AfterReturning(pointcut = "execution(* UserService.register(..))", returning = "dto")
    public void populateCache(UserDto dto) {
        cache.put(dto);
        System.out.println("[CACHE] Stored: " + dto.id());
    }
}
```

How to run: same classpath

`@AfterReturning` fires only after a successful `register` call, safely populating the cache. If `register` threw (DB error), the cache is not updated — consistency is maintained without try/catch in `UserService`.

## 6. Walkthrough

**Proxy call for `register("carol@example.com")` (Level 3):**
1. Proxy intercepts `register("carol@example.com")`.
2. No `@Before` advice here — real method runs directly.
3. `UserService.register` creates `UserDto(100, "carol@example.com")` and prints "Saved to DB".
4. Returns `UserDto(100, "carol@example.com")`.
5. Spring catches the return value in the advice chain.
6. Evaluates `@AfterReturning` matching: `execution(* UserService.register(..))` → yes.
7. Checks parameter type: `returning = "dto"` bound to `UserDto dto` — is `UserDto(100, …)` assignable to `UserDto`? Yes.
8. Calls `CachePopulatorAspect.populateCache(dto)` with the return value.
9. `cache.put(dto)` stores it; prints `[CACHE] Stored: 100`.
10. Advice returns (void). Proxy returns `UserDto(100, …)` to the original caller.

**What `@AfterReturning` cannot do:**
- It cannot change the return value. Even if `populateCache` returned a different `UserDto`, the original `UserDto(100, …)` is what the caller receives.
- It cannot suppress exceptions thrown after it runs (it has no try/catch scope).
- For modification, use `@Around` which controls both `pjp.proceed()` and the returned value.

**Type filter evaluation (Level 2):**
- `returning = "token"` + parameter type `String`.
- After `count()` returns `int` (autoboxed to `Integer`).
- Spring checks: `Integer.class.isAssignableFrom(String.class)` → false.
- Advice is skipped entirely.

**Expected output (Level 3):**
```
Saved to DB: UserDto[id=100, email=carol@example.com]
[CACHE] Stored: 100
Saved to DB: UserDto[id=101, email=dave@example.com]
[CACHE] Stored: 101
Cache contents: [UserDto[id=100, ...], UserDto[id=101, ...]]
```

## 7. Gotchas & takeaways

> **`@AfterReturning` cannot modify the return value.** Whatever the method returned is what the caller gets. To transform or replace the return value, use `@Around` and return a different object from the advice.

> **`returning` parameter name must exactly match the `returning` attribute string.** `returning = "result"` requires the advice parameter to be named `result`. A mismatch causes a startup error: `java.lang.IllegalArgumentException: Unbound pointcut parameter`.

- Declare the returning parameter as `Object` to match any return type; declare it as a specific type to restrict firing to that type.
- `@AfterReturning` fires BEFORE `@After` (finally) in the same aspect — use `@After` when you need to run regardless of success/failure.
- Void methods also trigger `@AfterReturning` — the `returning` parameter receives `null`.
- Avoid heavy work in `@AfterReturning` advice (DB calls, remote API) — the caller's thread blocks while the advice runs.
