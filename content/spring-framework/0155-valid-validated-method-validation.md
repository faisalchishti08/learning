---
card: spring-framework
gi: 155
slug: valid-validated-method-validation
title: "@Valid / @Validated & method validation"
---

## 1. What it is

`@Valid` (Jakarta) and `@Validated` (Spring) control how and where Jakarta Validation constraints are applied:

- **`@Valid`** triggers cascaded bean validation when used on a method parameter, return value, or nested field.
- **`@Validated`** is Spring's enhancement that additionally supports validation groups and activates **method-level validation** via a Spring AOP proxy (`MethodValidationPostProcessor`).

```java
@Service
@Validated  // enables AOP method validation for all methods in this class
class OrderService {
    public Receipt placeOrder(@Valid OrderRequest request) { ... }  // validates OrderRequest
    public @Valid OrderDetails getOrder(@NotBlank String id) { ... } // validates return value
}
```

## 2. Why & when

- **`@Valid` in Spring MVC** — `@RequestBody @Valid OrderRequest body` validates the incoming JSON body; binding errors land in `BindingResult`.
- **`@Validated` on a service/repository** — validates method parameters and return values at the AOP boundary; throws `ConstraintViolationException` (not caught by `BindingResult`).
- **Groups** — `@Validated(OnCreate.class)` runs only constraints in the `OnCreate` group; `@Valid` has no group support.
- **Cross-layer validation** — validate at the service layer to catch calls that bypass the web layer (scheduled jobs, CLI, tests).

## 3. Core concept

| Feature | `@Valid` | `@Validated` |
|---|---|---|
| Spec | Jakarta Validation | Spring (wraps Jakarta) |
| Groups | No | Yes (`@Validated(Group.class)`) |
| MVC `BindingResult` | Yes (method params) | No (throws exception) |
| Method return value | Yes (manually) | Yes (AOP-backed) |
| Cascaded bean validation | Yes | Yes |
| Requires AOP proxy | No (DataBinder-based) | Yes (`MethodValidationPostProcessor`) |

`MethodValidationPostProcessor` is a `BeanPostProcessor` that wraps beans annotated with `@Validated` in an AOP proxy. On method entry, it invokes `javax.validation.Validator.forExecutables()` to validate parameters; on method exit, it validates the return value. Spring Boot auto-registers `MethodValidationPostProcessor` when `spring-boot-starter-validation` is present.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Spring MVC path -->
  <rect x="10" y="15" width="145" height="65" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="82" y="35"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Spring MVC</text>
  <text x="82" y="50"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@RequestBody @Valid</text>
  <text x="82" y="63"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Errors → BindingResult</text>
  <text x="82" y="75"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">no exception</text>

  <!-- AOP path -->
  <rect x="10" y="100" width="145" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="82" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Validated (AOP)</text>
  <text x="82" y="135" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">MethodValidationInterceptor</text>
  <text x="82" y="148" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Errors → throws</text>
  <text x="82" y="161" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">ConstraintViolationException</text>

  <!-- LocalValidatorFactoryBean -->
  <rect x="250" y="55" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="75"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">LocalValidatorFactoryBean</text>
  <text x="350" y="92"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">implements Spring Validator</text>
  <text x="350" y="105" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">implements jakarta Validator</text>

  <!-- Violations -->
  <rect x="530" y="15" width="160" height="65" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="610" y="35"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">BindingResult</text>
  <text x="610" y="50"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">hasErrors(), getFieldErrors()</text>
  <text x="610" y="63"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ 400 in MVC</text>
  <text x="610" y="75"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(when next to @Valid param)</text>

  <rect x="530" y="100" width="160" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ConstraintViolationException</text>
  <text x="610" y="136" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getConstraintViolations()</text>
  <text x="610" y="150" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ caught by</text>
  <text x="610" y="163" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@ExceptionHandler</text>

  <defs>
    <marker id="a155" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="157" y1="47"  x2="247" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a155)"/>
  <line x1="157" y1="135" x2="247" y2="95" stroke="#6db33f"  stroke-width="1.5" marker-end="url(#a155)"/>
  <line x1="452" y1="75" x2="527" y2="47" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a155)"/>
  <line x1="452" y1="95" x2="527" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a155)"/>
</svg>

`@Valid` routes errors to `BindingResult` in MVC; `@Validated` uses an AOP proxy and throws `ConstraintViolationException`.

## 5. Runnable example

### Level 1 — Basic

`@Valid` in a standalone `DataBinder` context.

```java
// MethodValidationBasic.java
import jakarta.validation.constraints.*;
import org.springframework.format.support.*;
import org.springframework.validation.*;
import org.springframework.validation.beanvalidation.*;

class RegistrationRequest {
    @NotBlank(message = "Username is required")
    String username;

    @Email(message = "Invalid email")
    @NotNull
    String email;

    @Size(min = 8, message = "Password must be at least 8 chars")
    String password;

    RegistrationRequest(String username, String email, String password) {
        this.username = username; this.email = email; this.password = password;
    }
    public String getUsername() { return username; }
    public String getEmail()    { return email; }
    public String getPassword() { return password; }
}

public class MethodValidationBasic {
    public static void main(String[] args) {
        LocalValidatorFactoryBean lvfb = new LocalValidatorFactoryBean();
        lvfb.afterPropertiesSet(); // initialize outside Spring context

        RegistrationRequest req = new RegistrationRequest("", "bad-email", "short");
        BeanPropertyBindingResult errors = new BeanPropertyBindingResult(req, "reg");
        lvfb.validate(req, errors);  // Spring Validator SPI

        System.out.println("Error count: " + errors.getErrorCount());
        errors.getFieldErrors().forEach(e ->
            System.out.println("  [" + e.getField() + "] " + e.getDefaultMessage()));
    }
}
```

How to run: `java MethodValidationBasic.java` (requires Hibernate Validator + Spring Context on classpath)

`LocalValidatorFactoryBean.afterPropertiesSet()` initializes the factory outside of a Spring context. `lvfb.validate(req, errors)` bridges Jakarta Validation into `BindingResult` via the Spring `Validator` SPI.

### Level 2 — Intermediate

`@Validated` on a Spring service; method parameter and return value validation; `ConstraintViolationException` handling.

```java
// MethodValidationIntermediate.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.validation.annotation.*;
import org.springframework.validation.beanvalidation.*;
import java.util.*;

class CreateUserCmd {
    @NotBlank String username;
    @Email @NotNull String email;

    CreateUserCmd(String username, String email) {
        this.username = username; this.email = email;
    }
    public String getUsername() { return username; }
    public String getEmail()    { return email; }
}

@Validated  // all methods in this bean validated via AOP
class UserService {
    @NotNull
    public String createUser(@Valid CreateUserCmd cmd) {
        return "user:" + cmd.getUsername();
    }

    public List<String> findByName(@NotBlank String name) {
        return List.of("result-for-" + name);
    }
}

@Configuration
class SvcCfg {
    @Bean public UserService userService() { return new UserService(); }
    @Bean public LocalValidatorFactoryBean validator() { return new LocalValidatorFactoryBean(); }
    @Bean public MethodValidationPostProcessor mvpp(LocalValidatorFactoryBean v) {
        MethodValidationPostProcessor p = new MethodValidationPostProcessor();
        p.setValidator(v);
        return p;
    }
}

public class MethodValidationIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SvcCfg.class);
        UserService svc = ctx.getBean(UserService.class);

        // Valid call
        System.out.println(svc.createUser(new CreateUserCmd("alice", "alice@example.com")));

        // Invalid parameter — @NotBlank on name
        try {
            svc.findByName("");
        } catch (ConstraintViolationException e) {
            System.out.println("Caught: " + e.getMessage());
            e.getConstraintViolations().forEach(v ->
                System.out.println("  path=" + v.getPropertyPath() + " msg=" + v.getMessage()));
        }

        ctx.close();
    }
}
```

How to run: `java MethodValidationIntermediate.java` (requires Spring Context + AOP + Hibernate Validator)

`MethodValidationPostProcessor` registers a `MethodValidationInterceptor` that intercepts calls to `@Validated` beans. `@NotBlank` on method parameter `name` fires when `findByName("")` is called.

### Level 3 — Advanced

Validation groups with `@Validated`; cross-service chaining; exception to `BindingResult` adapter.

```java
// MethodValidationAdvanced.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import jakarta.validation.groups.*;
import org.springframework.context.annotation.*;
import org.springframework.validation.annotation.*;
import org.springframework.validation.beanvalidation.*;

interface OnCreate {}
interface OnUpdate {}

class ProductCmd {
    @NotBlank(groups = {OnCreate.class, OnUpdate.class})
    String name;

    @NotNull(groups = OnCreate.class, message = "Category required on create")
    String category;

    @Positive(groups = {OnCreate.class, OnUpdate.class})
    double price;

    ProductCmd(String name, String category, double price) {
        this.name = name; this.category = category; this.price = price;
    }
    public String getName()     { return name; }
    public String getCategory() { return category; }
    public double getPrice()    { return price; }
}

@Validated
class ProductService {
    @Validated(OnCreate.class)
    public String create(@Valid ProductCmd cmd) { return "created:" + cmd.getName(); }

    @Validated(OnUpdate.class)
    public String update(@Valid ProductCmd cmd) { return "updated:" + cmd.getName(); }
}

@Configuration
class ProdCfg {
    @Bean public ProductService productService() { return new ProductService(); }
    @Bean public LocalValidatorFactoryBean validator() { return new LocalValidatorFactoryBean(); }
    @Bean public MethodValidationPostProcessor mvpp(LocalValidatorFactoryBean v) {
        var p = new MethodValidationPostProcessor();
        p.setValidator(v);
        return p;
    }
}

public class MethodValidationAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProdCfg.class);
        ProductService svc = ctx.getBean(ProductService.class);

        // Update without category — OK for OnUpdate group
        try {
            System.out.println(svc.update(new ProductCmd("Widget", null, 9.99)));
        } catch (ConstraintViolationException e) {
            System.out.println("Update failed: " + e.getConstraintViolations().size() + " violations");
        }

        // Create without category — FAILS OnCreate group
        try {
            System.out.println(svc.create(new ProductCmd("Widget", null, 9.99)));
        } catch (ConstraintViolationException e) {
            System.out.println("Create failed: " + e.getConstraintViolations().size() + " violation(s)");
            e.getConstraintViolations().forEach(v ->
                System.out.println("  " + v.getPropertyPath() + ": " + v.getMessage()));
        }

        ctx.close();
    }
}
```

How to run: `java MethodValidationAdvanced.java`

`@Validated(OnCreate.class)` on the method restricts which constraints run. Category is `@NotNull(groups = OnCreate.class)` — it's validated only in the `create` path, not `update`. This lets the same `ProductCmd` class serve both create and update use cases.

## 6. Walkthrough

Execution trace for `svc.create(new ProductCmd("Widget", null, 9.99))`:

1. AOP proxy intercepts `create()` call on the `@Validated` bean.
2. `MethodValidationInterceptor` reads `@Validated(OnCreate.class)` from the method.
3. Calls `validator.forExecutables().validateParameters(svc, createMethod, [cmd], OnCreate.class)`.
4. Jakarta Validator validates `cmd` fields using only `OnCreate.class` group.
5. `category = null` violates `@NotNull(groups = OnCreate.class)`.
6. Interceptor collects violations and throws `ConstraintViolationException` before the method body executes.

## 7. Gotchas & takeaways

> `@Valid` on a Spring MVC method parameter routes errors to the next argument if it is a `BindingResult`. If no `BindingResult` follows, Spring throws a `MethodArgumentNotValidException` automatically (which becomes a 400 response). If you add `BindingResult` next to `@Valid`, Spring will NOT throw — you must check `errors.hasErrors()` yourself.

> `@Validated` AOP validation requires the bean to be invoked through the Spring proxy. **Self-invocation** (calling another method within the same bean) bypasses the proxy, so constraints on the inner method are not checked.

- `MethodValidationPostProcessor` must use the same `ValidatorFactory` as `LocalValidatorFactoryBean` to share constraint metadata and message interpolators. Pass the `LocalValidatorFactoryBean` bean to `p.setValidator()`.
- On Spring Boot 3+, `MethodValidationPostProcessor` is auto-registered. You only need to add `@Validated` to the bean class.
- Use `@Validated` at the class level to enable interception for all methods. Placing it only on individual methods has no effect — the annotation must be on the class or interface.
- `ConstraintViolationException` should be caught in a `@ControllerAdvice` / `@ExceptionHandler` to return structured 400 responses for REST APIs.
