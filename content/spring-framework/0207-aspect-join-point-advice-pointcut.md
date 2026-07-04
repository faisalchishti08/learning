---
card: spring-framework
gi: 207
slug: aspect-join-point-advice-pointcut
title: "Aspect, Join point, Advice, Pointcut"
---

## 1. What it is

AOP has four core vocabulary terms that every Spring developer needs to know:

- **Aspect** — the module that packages a cross-cutting concern. A class annotated `@Aspect`.
- **Join point** — a specific point during program execution where an aspect *could* be applied. In Spring AOP, this is always a method invocation.
- **Advice** — the *action* taken at a join point. What actually runs: `@Before`, `@After`, `@Around`, etc.
- **Pointcut** — a *predicate* (expression) that matches a set of join points. Advice is associated with a pointcut to say "run this advice on *these* join points."

## 2. Why & when

Without this vocabulary, reading Spring AOP documentation and error messages is opaque. Understanding each term precisely lets you:
- Write correct pointcut expressions the first time.
- Interpret Spring AOP warnings ("No eligible advice for join point…").
- Know which advice type to choose (`@Before` vs `@Around` vs `@AfterReturning`).

## 3. Core concept

An analogy: imagine a city with surveillance cameras (aspects). A join point is any intersection in the city (any method call). A pointcut is a rule that says "film all intersections in the financial district" — it selects which intersections to watch. Advice is what the camera does: record before a car passes, or after, or wrap the entire event.

| Term | Analogy | Spring AOP |
|------|---------|------------|
| Aspect | Camera system | `@Aspect` class |
| Join point | Any intersection | Any Spring bean method call |
| Pointcut | "Film financial district" | `execution(* com.example.service.*.*(..))` |
| Advice | What camera does | `@Before`, `@After`, `@Around`, `@AfterReturning`, `@AfterThrowing` |

A single aspect can contain multiple advice methods, each with its own pointcut.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg">
  <!-- Aspect box -->
  <rect x="15" y="20" width="610" height="195" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="42" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Aspect (@Aspect)</text>

  <!-- Pointcut -->
  <rect x="35" y="55" width="180" height="55" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="125" y="76" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Pointcut</text>
  <text x="125" y="93" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">execution(* svc.*(..))</text>

  <!-- Matches arrow -->
  <line x1="215" y1="82" x2="270" y2="82" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="243" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">matches</text>

  <!-- Join points -->
  <rect x="270" y="55" width="160" height="130" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 2"/>
  <text x="350" y="76" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Join points</text>
  <text x="350" y="96"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">svc.place()</text>
  <text x="350" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">svc.cancel()</text>
  <text x="350" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">svc.ship()</text>
  <text x="350" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(all methods of svc)</text>

  <!-- Advice arrow -->
  <line x1="430" y1="82" x2="470" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a2)"/>
  <text x="450" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">triggers</text>

  <!-- Advice box -->
  <rect x="470" y="55" width="140" height="130" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="76" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Advice</text>
  <text x="540" y="96"  fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Before</text>
  <text x="540" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@After</text>
  <text x="540" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Around</text>
  <text x="540" y="147" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@AfterReturning</text>
  <text x="540" y="164" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@AfterThrowing</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

An `@Aspect` class holds both the pointcut (which join points to intercept) and the advice (what to do at those points).

## 5. Runnable example

Scenario: an **audit trail** for a banking service — first illustrating each term in isolation, then combining them, then showing multiple advice types in one aspect.

### Level 1 — Basic

Identify each AOP term with comments, then run the simplest `@Before` advice.

```java
// AopVocabDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AopVocabDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AopVocabDemo.class);
        ctx.getBean(BankService.class).deposit(100.0);
        ctx.close();
    }
}

@Service
class BankService {
    // JOIN POINT: this method invocation is a potential join point
    public void deposit(double amount) {
        System.out.println("Deposited $" + amount);
    }
}

// ASPECT: the class that holds the cross-cutting concern
@Aspect
@Component
class AuditAspect {
    // POINTCUT: expression that selects the join points to intercept
    // ADVICE: @Before — runs before the matched join point
    @Before("execution(* BankService.*(..))")
    public void logBefore(JoinPoint jp) {
        System.out.println("[AUDIT] Before: " + jp.getSignature().getName());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. AopVocabDemo.java`

`AuditAspect` is the aspect. `execution(* BankService.*(..))` is the pointcut. `logBefore` is the advice. The invocation of `deposit(100.0)` is the join point that matches the pointcut and triggers the advice.

---

### Level 2 — Intermediate

Two different advice types (`@Before` and `@AfterReturning`) in one aspect, both bound to the same named pointcut.

```java
// AopVocabDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AopVocabDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AopVocabDemo.class);
        var bank = ctx.getBean(BankService.class);
        bank.deposit(200.0);
        bank.withdraw(50.0);
        ctx.close();
    }
}

@Service
class BankService {
    private double balance = 500.0;

    public double deposit(double amount) {
        balance += amount;
        System.out.println("Deposit $" + amount + " → balance $" + balance);
        return balance;
    }

    public double withdraw(double amount) {
        balance -= amount;
        System.out.println("Withdraw $" + amount + " → balance $" + balance);
        return balance;
    }
}

@Aspect
@Component
class AuditAspect {
    // Named pointcut — reused by both advice methods
    @Pointcut("execution(* BankService.*(..))")
    private void bankOps() {}

    // Advice 1: runs before the join point
    @Before("bankOps()")
    public void logCall(JoinPoint jp) {
        System.out.println("[AUDIT] Calling: " + jp.getSignature().toShortString()
            + " args=" + java.util.Arrays.toString(jp.getArgs()));
    }

    // Advice 2: runs after a normal return; binds the return value
    @AfterReturning(pointcut = "bankOps()", returning = "result")
    public void logReturn(JoinPoint jp, Object result) {
        System.out.println("[AUDIT] Returned: " + jp.getSignature().getName()
            + " → " + result);
    }
}
```

How to run: same as Level 1

`@Pointcut("execution(* BankService.*(..))")` declares a reusable named pointcut `bankOps()`. Both `@Before("bankOps()")` and `@AfterReturning(pointcut = "bankOps()")` refer to it. The join points are `deposit(200.0)` and `withdraw(50.0)`.

---

### Level 3 — Advanced

All five advice types in one aspect, demonstrating when each runs, plus `@Around` that controls whether the join point proceeds.

```java
// AopVocabDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class AopVocabDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AopVocabDemo.class);
        var bank = ctx.getBean(BankService.class);
        System.out.println("--- deposit ---");
        bank.deposit(100.0);
        System.out.println("--- bad withdraw ---");
        try { bank.withdraw(9999.0); } catch (Exception e) { System.out.println("Caught: " + e.getMessage()); }
        ctx.close();
    }
}

@Service
class BankService {
    private double balance = 500.0;

    public double deposit(double amount) {
        balance += amount; return balance;
    }

    public double withdraw(double amount) {
        if (amount > balance) throw new IllegalStateException("Insufficient funds");
        balance -= amount; return balance;
    }
}

@Aspect
@Component
class FullAuditAspect {
    @Pointcut("execution(* BankService.*(..))")
    private void bankOps() {}

    @Before("bankOps()")
    public void before(JoinPoint jp) {
        System.out.println("  [@Before]  " + jp.getSignature().getName());
    }

    @Around("bankOps()")
    public Object around(ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("  [@Around]  entering " + pjp.getSignature().getName());
        Object result = pjp.proceed(); // let the method run
        System.out.println("  [@Around]  exiting  " + pjp.getSignature().getName());
        return result;
    }

    @AfterReturning(pointcut = "bankOps()", returning = "rv")
    public void afterReturning(JoinPoint jp, Object rv) {
        System.out.println("  [@AfterReturning] " + jp.getSignature().getName() + " = " + rv);
    }

    @AfterThrowing(pointcut = "bankOps()", throwing = "ex")
    public void afterThrowing(JoinPoint jp, Throwable ex) {
        System.out.println("  [@AfterThrowing] " + jp.getSignature().getName() + ": " + ex.getMessage());
    }

    @After("bankOps()")
    public void after(JoinPoint jp) {
        System.out.println("  [@After]   " + jp.getSignature().getName() + " (finally)");
    }
}
```

How to run: same classpath

The execution order is: `@Around` (enter) → `@Before` → method body → `@Around` (exit) → `@AfterReturning` OR `@AfterThrowing` → `@After`. `@After` is "finally" — runs whether or not an exception occurred.

## 6. Walkthrough

**Spring proxy creation:**
`@EnableAspectJAutoProxy` registers a `BeanPostProcessor`. After `BankService` is created, the post-processor evaluates `FullAuditAspect`'s pointcuts against `BankService`. All methods match `execution(* BankService.*(..))`. A CGLIB proxy subclass of `BankService` is created that intercepts all method calls.

**Advice execution chain for `deposit(100.0)` (normal path):**
1. Caller calls proxy's `deposit(100.0)`.
2. `@Around` advice `around()` runs — prints "entering deposit", calls `pjp.proceed()`.
3. `pjp.proceed()` triggers `@Before` advice `before()` — prints "@Before deposit".
4. Real `BankService.deposit(100.0)` runs — balance = 600.
5. Returns 600.0 back to `pjp.proceed()`.
6. `@Around` resumes after `pjp.proceed()` — prints "exiting deposit", returns 600.0.
7. `@AfterReturning` fires — prints "@AfterReturning deposit = 600.0".
8. `@After` fires (finally) — prints "@After deposit (finally)".

**Advice execution chain for `withdraw(9999.0)` (exception path):**
1–3. Same as above up to `pjp.proceed()`.
4. Real `withdraw` throws `IllegalStateException`.
5. Exception propagates through `pjp.proceed()` — `@Around` does NOT catch it (it rethrows).
6. `@AfterThrowing` fires — prints "@AfterThrowing withdraw: Insufficient funds".
7. `@After` fires (finally).
8. Exception propagates to caller.

**`JoinPoint` vs `ProceedingJoinPoint`:** `@Before`/`@After`/`@AfterReturning`/`@AfterThrowing` get a `JoinPoint` — read-only view of the intercepted call. `@Around` gets a `ProceedingJoinPoint` which adds `proceed()` — the ability to invoke the real method (or skip it).

**Expected output:**
```
--- deposit ---
  [@Around]  entering deposit
  [@Before]  deposit
  [@Around]  exiting  deposit
  [@AfterReturning] deposit = 600.0
  [@After]   deposit (finally)
--- bad withdraw ---
  [@Around]  entering withdraw
  [@Before]  withdraw
  [@AfterThrowing] withdraw: Insufficient funds
  [@After]   withdraw (finally)
Caught: Insufficient funds
```

## 7. Gotchas & takeaways

> **`@After` is "finally", not "after success".** It fires even when an exception is thrown. If you only want to run on success, use `@AfterReturning`; for exceptions only, use `@AfterThrowing`.

> **`@Around` must call `pjp.proceed()` or the real method never runs.** Forgetting `pjp.proceed()` silently skips the method — a hard-to-debug blank behaviour.

- A single `@Aspect` class can have many advice methods, each with its own pointcut or reusing a named `@Pointcut`.
- `JoinPoint.getArgs()` returns the arguments as `Object[]`; cast carefully.
- `@AfterReturning(returning = "rv")` only fires when the method returns normally — its `rv` parameter is bound to the actual return value.
- The five advice types in execution order: `@Around` enter → `@Before` → method → `@Around` exit → (`@AfterReturning` XOR `@AfterThrowing`) → `@After`.
- Spring AOP supports only method-execution join points; for field access or constructor interception use full AspectJ with load-time weaving.
