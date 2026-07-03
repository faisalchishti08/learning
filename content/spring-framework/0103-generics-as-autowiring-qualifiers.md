---
card: spring-framework
gi: 103
slug: generics-as-autowiring-qualifiers
title: Generics as autowiring qualifiers
---

## 1. What it is

Since Spring 4, **generic type parameters act as implicit qualifiers** during autowiring. If you have `Repository<User>` and `Repository<Order>` as beans, injecting `@Autowired Repository<User>` automatically selects the right one — without any `@Qualifier` annotation. Spring uses the full generic type signature for matching.

## 2. Why & when

Generic-based qualification shines in patterns where the same generic interface has multiple typed implementations:

- `Repository<T>` implementations per entity (`UserRepository`, `OrderRepository`).
- `Converter<S, T>` implementations per conversion pair.
- `Validator<T>` implementations per model type.
- `EventHandler<E>` implementations per event type.

Without this feature you'd need a `@Qualifier("user")` on every `Repository<User>` injection. With generic qualification, the type parameter *is* the qualifier — zero extra annotations.

## 3. Core concept

Spring's `ResolvableType` utility resolves generic type information at runtime from class metadata (not type erasure — Spring uses bytecode analysis). When wiring `@Autowired Repository<User> userRepo`:

1. Spring collects all beans that implement `Repository`.
2. For each candidate, it checks whether the generic parameter of the bean's `Repository` implementation matches `User`.
3. Only the bean whose full generic signature matches `Repository<User>` is selected.

This works for fields, constructor parameters, setter parameters, and collection injection (`List<Repository<User>>`). Spring handles covariance: `Repository<? extends User>` matches `Repository<Admin>` if `Admin extends User`.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Beans -->
  <rect x="10" y="50" width="185" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="102" y="73" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">UserRepositoryImpl</text>
  <text x="102" y="87" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">implements Repository&lt;User&gt;</text>

  <rect x="10" y="115" width="185" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="102" y="138" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">OrderRepositoryImpl</text>
  <text x="102" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">implements Repository&lt;Order&gt;</text>

  <!-- Injection points -->
  <rect x="295" y="50" width="200" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="73" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="395" y="87" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Repository&lt;User&gt; userRepo</text>

  <rect x="295" y="115" width="200" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="395" y="138" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="395" y="152" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Repository&lt;Order&gt; orderRepo</text>

  <line x1="197" y1="72" x2="292" y2="72" stroke="#6db33f" stroke-width="2" marker-end="url(#a103)"/>
  <line x1="197" y1="137" x2="292" y2="137" stroke="#79c0ff" stroke-width="2" marker-end="url(#b103)"/>
  <defs>
    <marker id="a103" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b103" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="195" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Generic type parameter acts as implicit qualifier — no @Qualifier annotation needed</text>
</svg>

Spring resolves `Repository<User>` and `Repository<Order>` independently using the full generic signature.

## 5. Runnable example

### Level 1 — Basic

Two `Store<T>` implementations; Spring selects the right one at each generic injection point.

```java
// GenericsBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface Store<T> {
    void save(T item);
    String type();
}

@Component
class UserStore implements Store<String> {  // T = String represents User name
    public void save(String name) { System.out.println("[UserStore] saved: " + name); }
    public String type() { return "User"; }
}

@Component
class OrderStore implements Store<Integer> {  // T = Integer represents Order id
    public void save(Integer id) { System.out.println("[OrderStore] saved: " + id); }
    public String type() { return "Order"; }
}

@Service
class AppService {
    @Autowired private Store<String>  userStore;   // gets UserStore
    @Autowired private Store<Integer> orderStore;  // gets OrderStore

    public void run() {
        userStore.save("alice");
        orderStore.save(42);
        System.out.println("userStore  type = " + userStore.type());
        System.out.println("orderStore type = " + orderStore.type());
    }
}

@Configuration
@ComponentScan
class GenCfg {}

public class GenericsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GenCfg.class);
        ctx.getBean(AppService.class).run();
        ctx.close();
    }
}
```

How to run: `java GenericsBasic.java`

`Store<String>` matches `UserStore` (implements `Store<String>`); `Store<Integer>` matches `OrderStore`. No `@Qualifier` needed — the type parameter distinguishes them.

### Level 2 — Intermediate

A generic `Converter<S, T>` pattern where Spring injects the right converter for each type pair.

```java
// GenericsConverter.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface Converter<S, T> {
    T convert(S source);
}

@Component
class StringToIntConverter implements Converter<String, Integer> {
    public Integer convert(String s) {
        System.out.println("StringToInt: \"" + s + "\"");
        return Integer.parseInt(s.trim());
    }
}

@Component
class IntToStringConverter implements Converter<Integer, String> {
    public String convert(Integer n) {
        System.out.println("IntToString: " + n);
        return "#" + n;
    }
}

@Component
class StringToBoolConverter implements Converter<String, Boolean> {
    public Boolean convert(String s) {
        System.out.println("StringToBool: \"" + s + "\"");
        return Boolean.parseBoolean(s);
    }
}

@Service
class DataPipeline {
    @Autowired private Converter<String, Integer> toInt;
    @Autowired private Converter<Integer, String> toStr;
    @Autowired private Converter<String, Boolean> toBool;

    public void process(String raw) {
        int num   = toInt.convert(raw);
        String s  = toStr.convert(num);
        boolean b = toBool.convert("true");
        System.out.printf("Pipeline: \"%s\" → %d → \"%s\", bool=%b%n", raw, num, s, b);
    }
}

@Configuration
@ComponentScan
class ConvCfg {}

public class GenericsConverter {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ConvCfg.class);
        ctx.getBean(DataPipeline.class).process("42");
        ctx.close();
    }
}
```

How to run: `java GenericsConverter.java`

Three `Converter` beans with different type-parameter pairs, each injected by its full two-parameter generic signature. Spring distinguishes `Converter<String, Integer>` from `Converter<Integer, String>` — same outer type, different parameters.

### Level 3 — Advanced

Combine generic injection with collection injection: get all `Validator<User>` beans as a `List`, and show that `Validator<Order>` beans are excluded from the `User` list.

```java
// GenericsCollection.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.*;
import java.util.List;

record User(String name, String email) {}
record Order(int id, double amount) {}

interface Validator<T> {
    boolean validate(T item);
    String ruleName();
}

@Component @Order(1)
class UserNotBlankValidator implements Validator<User> {
    public boolean validate(User u) { return u.name() != null && !u.name().isBlank(); }
    public String ruleName() { return "user.name.notBlank"; }
}

@Component @Order(2)
class UserEmailValidator implements Validator<User> {
    public boolean validate(User u) { return u.email() != null && u.email().contains("@"); }
    public String ruleName() { return "user.email.format"; }
}

@Component @Order(1)
class OrderPositiveAmountValidator implements Validator<Order> {
    public boolean validate(Order o) { return o.amount() > 0; }
    public String ruleName() { return "order.amount.positive"; }
}

@Service
class UserValidationService {
    // Only Validator<User> beans — Order validators excluded automatically
    @Autowired
    private List<Validator<User>> validators;

    public boolean validate(User user) {
        System.out.println("Validating: " + user);
        System.out.println("Validators count: " + validators.size()
            + " (Order validators NOT included)");
        boolean ok = true;
        for (var v : validators) {
            boolean pass = v.validate(user);
            System.out.printf("  [%s]: %s%n", v.ruleName(), pass ? "PASS" : "FAIL");
            if (!pass) ok = false;
        }
        return ok;
    }
}

@Configuration
@ComponentScan
class CollGenCfg {}

public class GenericsCollection {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CollGenCfg.class);
        var svc = ctx.getBean(UserValidationService.class);
        System.out.println("Valid:   " + svc.validate(new User("Alice", "alice@example.com")));
        System.out.println();
        System.out.println("Invalid: " + svc.validate(new User("", "not-an-email")));
        ctx.close();
    }
}
```

How to run: `java GenericsCollection.java`

`List<Validator<User>>` collects only `UserNotBlankValidator` and `UserEmailValidator`. `OrderPositiveAmountValidator` is a `Validator<Order>`, not `Validator<User>`, so it is excluded — despite all three implementing the same raw interface.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Component scan** — finds all four service/component classes.
2. **Validators instantiated** — three `Validator` beans created; no deps.
3. **`UserValidationService` instantiated** — `AutowiredAnnotationBeanPostProcessor` resolves `List<Validator<User>>`.
4. **Generic collection resolution** — Spring inspects all `Validator` beans:
   - `UserNotBlankValidator` implements `Validator<User>` → matches `Validator<User>` → included.
   - `UserEmailValidator` implements `Validator<User>` → included.
   - `OrderPositiveAmountValidator` implements `Validator<Order>` → does NOT match `Validator<User>` → excluded.
   - Result: `[UserNotBlankValidator, UserEmailValidator]` (ordered by `@Order`).
5. **`validate(new User("Alice", "alice@example.com"))`** — both validators pass.
6. **`validate(new User("", "not-an-email"))`** — `UserNotBlankValidator` fails (blank name); `UserEmailValidator` fails (no `@`).

Expected output (first call):
```
Validating: User[name=Alice, email=alice@example.com]
Validators count: 2 (Order validators NOT included)
  [user.name.notBlank]: PASS
  [user.email.format]: PASS
Valid:   true
```

## 7. Gotchas & takeaways

> Generic qualification uses Spring's `ResolvableType` — it reads bytecode signatures, not runtime type erasure. This means it works correctly even though Java erases generics at runtime.

> If two beans have the same generic signature (e.g., two different `UserStore` beans), Spring falls back to name-based or `@Qualifier`-based disambiguation — generics alone don't resolve that ambiguity.

- Works on field injection, constructor parameters, and setter parameters.
- For `List<GenericInterface<T>>` injection, Spring collects only beans whose generic parameter matches `T`.
- Wildcards are respected: `Repository<? extends Number>` matches both `Repository<Integer>` and `Repository<Long>`.
- Available since Spring 4.0 — no special configuration needed.
- Combine with `@Order` to control list ordering when collecting all matching generic beans.
