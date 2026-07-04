---
card: spring-framework
gi: 223
slug: generics-with-advice-parameters
title: Generics with advice parameters
---

## 1. What it is

When a pointcut binds method arguments or return values that involve generic types, Spring AOP handles two scenarios:

1. **Generic interface method with a concrete type argument** — `args(account)` where the advice parameter is `Account` and the method signature uses a generic `T`. Spring resolves the concrete type at runtime.
2. **Collection or generic container arguments** — `args(accounts)` where `accounts` is `List<Account>`. Due to Java's type erasure, Spring cannot filter on the generic type parameter at runtime; it only sees `List`.

The key rule: Spring AOP's type-checking for generics is limited by Java's type erasure — `List<Account>` and `List<String>` look identical at runtime.

## 2. Why & when

This matters when:
- You have a generic repository or service interface (`Repository<T>`) and want aspect advice to run only for `Repository<Account>`, not for `Repository<Order>`.
- You want to bind a typed collection argument and use its elements in the advice.
- You migrate to `@Around` or `@AfterReturning` that deal with generic return types.

Understanding the limitation prevents a subtle bug: writing `args(List<Account>)` expecting it to filter by element type — it doesn't.

## 3. Core concept

Java's type erasure removes generic type parameters at compile time. At runtime, `List<Account>` is just `List`, and `List<Order>` is also just `List`. Spring AOP evaluates pointcut expressions at runtime — it cannot distinguish the two.

**What works:**

```java
// Generic interface
interface Repository<T> { void save(T entity); }
class AccountRepository implements Repository<Account> { ... }

// This WORKS: the concrete method's erased type is Account
@Before("execution(* AccountRepository.save(..)) && args(account)")
public void beforeSave(Account account) { ... }
```

**What does NOT work:**

```java
// This does NOT filter by element type — sees only List
@Before("execution(* *.saveAll(..)) && args(items)")
public void beforeSaveAll(List<Account> items) { ... } // matches ANY List
```

For collections, Spring AOP will generate a warning and the advice fires for all `List` arguments regardless of element type.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Left: generic method resolved -->
  <rect x="15" y="20" width="270" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Generic method — WORKS</text>
  <rect x="25" y="52" width="250" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="150" y="67" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">AccountRepository.save(Account)</text>
  <text x="150" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">concrete type visible at runtime</text>
  <line x1="150" y1="87" x2="150" y2="107" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ag)"/>
  <rect x="25" y="107" width="250" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="122" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">args(account) → Account account</text>
  <text x="150" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✓ type-safe binding</text>

  <!-- Right: collection erasure -->
  <rect x="355" y="20" width="270" height="140" rx="8" fill="#1c2430" stroke="#e06c75" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e06c75" font-size="11" text-anchor="middle" font-family="sans-serif">Collection arg — LIMITED</text>
  <rect x="365" y="52" width="250" height="35" rx="5" fill="#0d1117" stroke="#e06c75" stroke-width="1"/>
  <text x="490" y="67" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">saveAll(List&lt;Account&gt;)</text>
  <text x="490" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">erased to List at runtime</text>
  <line x1="490" y1="87" x2="490" y2="107" stroke="#e06c75" stroke-width="1.5" marker-end="url(#ae)"/>
  <rect x="365" y="107" width="250" height="35" rx="5" fill="#0d1117" stroke="#e06c75" stroke-width="1.5"/>
  <text x="490" y="122" fill="#e06c75" font-size="10" text-anchor="middle" font-family="monospace">args(items) → List&lt;Account&gt;</text>
  <text x="490" y="137" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">⚠ matches any List — no element filtering</text>

  <defs>
    <marker id="ag" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="ae" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#e06c75"/></marker>
  </defs>
</svg>

Concrete generic types resolve correctly; collection element types are erased and cannot be used for filtering.

## 5. Runnable example

Scenario: a **data persistence layer** — first showing successful generic type binding, then demonstrating the collection erasure limitation, then a workaround using instance checking.

### Level 1 — Basic

Generic interface method — concrete type is visible at runtime.

```java
// GenericsAopDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

interface Repository<T> { void save(T entity); }

record Account(long id, String name) {}
record Order(long id, double amount) {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class GenericsAopDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GenericsAopDemo.class);
        ctx.getBean(AccountRepo.class).save(new Account(1, "Alice"));
        ctx.getBean(OrderRepo.class).save(new Order(10, 99.0));
        ctx.close();
    }
}

@org.springframework.stereotype.Repository
class AccountRepo implements Repository<Account> {
    public void save(Account account) {
        System.out.println("Saved account: " + account.name());
    }
}

@org.springframework.stereotype.Repository
class OrderRepo implements Repository<Order> {
    public void save(Order order) {
        System.out.println("Saved order: " + order.amount());
    }
}

@Aspect
@Component
class PersistAspect {
    // Works: concrete Account type is visible — args(account) binds it correctly
    @Before("execution(* AccountRepo.save(..)) && args(account)")
    public void beforeAccountSave(Account account) {
        System.out.println("[ASPECT] Saving account: " + account.id());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. GenericsAopDemo.java`

`AccountRepo.save(Account)` compiles to a concrete method whose argument type is `Account`. Spring sees `Account` at runtime → `args(account)` binds successfully. `OrderRepo.save` does NOT match the pointcut — correct.

---

### Level 2 — Intermediate

Demonstrate collection erasure: `args(items)` with `List<Account> items` matches any `List`.

```java
// GenericsAopDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.util.*;

record Account(long id, String name) {}
record Order(long id, double amount) {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class GenericsAopDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GenericsAopDemo.class);
        var svc = ctx.getBean(BulkService.class);

        System.out.println("--- save List<Account> ---");
        svc.saveAll(List.of(new Account(1, "Alice"), new Account(2, "Bob")));

        System.out.println("--- save List<Order> ---");
        svc.saveAll(List.of(new Order(10, 99.0)));  // also matches — erasure!
        ctx.close();
    }
}

@Service
class BulkService {
    public void saveAll(List<?> items) {
        System.out.println("Saved " + items.size() + " items: " + items);
    }
}

@Aspect
@Component
class BulkAspect {
    // Attempting to bind List<Account> — Spring warns and matches ANY List
    @SuppressWarnings("unchecked")
    @Before("execution(* BulkService.saveAll(..)) && args(items)")
    public void beforeBulk(JoinPoint jp, List<Account> items) {
        System.out.println("[BULK] size=" + items.size()
            + " first element type=" + (items.isEmpty() ? "N/A" : items.get(0).getClass().getSimpleName()));
    }
}
```

How to run: same classpath

Both calls trigger `[BULK]` — even the `List<Order>` call. The element type check `items.get(0).getClass().getSimpleName()` shows `Account` vs `Order`. Spring cannot distinguish at the pointcut level.

---

### Level 3 — Advanced

Workaround: use `Object items` in the advice parameter and do a runtime `instanceof` check to filter by element type.

```java
// GenericsAopDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.util.*;

record Account(long id, String name) {}
record Order(long id, double amount) {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class GenericsAopDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GenericsAopDemo.class);
        var svc = ctx.getBean(BulkService.class);

        System.out.println("--- Account list ---");
        svc.saveAll(List.of(new Account(1, "Alice"), new Account(2, "Bob")));

        System.out.println("--- Order list ---");
        svc.saveAll(List.of(new Order(10, 55.0)));

        System.out.println("--- Empty list ---");
        svc.saveAll(List.of());
        ctx.close();
    }
}

@Service
class BulkService {
    public void saveAll(List<?> items) {
        System.out.println("Saved " + items.size() + " items");
    }
}

@Aspect
@Component
class TypedBulkAspect {
    @SuppressWarnings("unchecked")
    @Before("execution(* BulkService.saveAll(..)) && args(items)")
    public void beforeBulk(Object items) {
        if (!(items instanceof List<?> list)) return;

        // Workaround: check element type at runtime
        if (!list.isEmpty() && list.get(0) instanceof Account) {
            List<Account> accounts = (List<Account>) list;
            System.out.println("[ASPECT/Account] bulk save accounts: "
                + accounts.stream().map(Account::name).toList());
        } else if (!list.isEmpty() && list.get(0) instanceof Order) {
            List<Order> orders = (List<Order>) list;
            System.out.printf("[ASPECT/Order] bulk save %d orders total=$%.2f%n",
                orders.size(), orders.stream().mapToDouble(Order::amount).sum());
        } else {
            System.out.println("[ASPECT] empty or unknown list");
        }
    }
}
```

How to run: same classpath

Declaring `Object items` avoids the impossible generic type filter. The advice manually checks `list.get(0) instanceof Account` — standard Java runtime type checking applied inside the advice.

## 6. Walkthrough

**Generic method resolution (Level 1):**
At compile time, `AccountRepo.save(Account)` is generated as a bridge method alongside the generic `save(Object)`. Spring AOP's `execution(* AccountRepo.save(..))` matcher uses `MethodMatcher.matches(Method, Class)` which resolves the concrete declared method — `save(Account account)` — not the bridge. `args(account)` therefore correctly binds an `Account` instance.

**Collection erasure (Level 2):**
`BulkService.saveAll(List<?> items)` compiles to `saveAll(List items)` at the bytecode level. At runtime, `args(items)` evaluates: "is the first argument a `List`?" Yes — for both `List<Account>` and `List<Order>`. Spring has no way to inspect the element type. It logs a warning at startup: `Unable to extract return type for generic advice... Only the raw type will be considered`.

**Workaround correctness (Level 3):**
Declaring the advice parameter as `Object items` removes the generic type assertion entirely. The advice then uses `instanceof` pattern matching (Java 16+) for type-safe narrowing. This is the recommended approach when aspect behaviour must vary by collection element type.

**Expected output (Level 3):**
```
--- Account list ---
[ASPECT/Account] bulk save accounts: [Alice, Bob]
Saved 2 items
--- Order list ---
[ASPECT/Order] bulk save 1 orders total=$55.00
Saved 1 items
--- Empty list ---
[ASPECT] empty or unknown list
Saved 0 items
```

## 7. Gotchas & takeaways

> **`args(List<Account>)` is not a valid generic filter.** Spring AOP emits a warning and widens the match to any `List`. Never rely on generic element types in `args()` for filtering.

> **Bridge methods can confuse `execution` patterns.** When a generic interface is implemented, the compiler may generate a synthetic bridge method. An overly broad `execution` pattern might match the bridge. Use concrete class patterns (`AccountRepo.save(..)`) rather than generic interface patterns for precision.

- For entity-specific logic in a generic repository, target the concrete class in the pointcut: `execution(* AccountRepo.*(..))` is safer than `execution(* Repository.*(..))`.
- The `@AfterReturning(returning = "result")` parameter with a generic return type also suffers from erasure — declare as `Object result` and cast inside the advice.
- Kotlin's `reified` type parameters and Scala's manifests are not supported by Spring AOP — the JVM-level erasure is the relevant boundary.
