---
card: spring-framework
gi: 154
slug: bean-validation-jakarta-validation-jsr-380
title: "Bean Validation (Jakarta Validation / JSR-380)"
---

## 1. What it is

Jakarta Validation (formerly Bean Validation, standardised as JSR-380) is a specification for expressing constraints on Java objects via annotations. Hibernate Validator is the reference implementation. Spring integrates it through `LocalValidatorFactoryBean`, which adapts the Jakarta `javax.validation.Validator` into Spring's own `Validator` SPI so the same API can be used with or without Spring MVC.

```java
class ProductForm {
    @NotBlank(message = "Name is required")
    String name;

    @DecimalMin("0.01") @DecimalMax("999999.99")
    BigDecimal price;

    @Min(1) @Max(10000)
    int quantity;

    @Email
    String contactEmail;
}
```

## 2. Why & when

- **Declarative validation** — constraints live on the model, not scattered across service methods, making them visible and reusable.
- **Standard API** — independent of framework; the same `@NotNull` works in a Spring MVC controller, a Jakarta EE endpoint, or a standalone CLI.
- **Cascaded validation** — `@Valid` on a nested field triggers validation of that field's own constraints.
- **Custom constraints** — define your own `@ValidISBN` annotation backed by a `ConstraintValidator<ValidISBN, String>`.
- Spring Boot auto-configures `LocalValidatorFactoryBean` when `spring-boot-starter-validation` is on the classpath.

## 3. Core concept

Core annotations from `jakarta.validation.constraints`:

| Annotation | Applies to | Meaning |
|---|---|---|
| `@NotNull` | any | value is not null |
| `@NotBlank` | `String` | not null, not empty, not whitespace |
| `@NotEmpty` | `String`, collections | not null and not empty |
| `@Size(min, max)` | `String`, collections, arrays | size within range |
| `@Min(n)`, `@Max(n)` | numbers | numeric range |
| `@DecimalMin`, `@DecimalMax` | `BigDecimal`, `String` | decimal range |
| `@Email` | `String` | valid email format |
| `@Pattern(regexp)` | `String` | matches regex |
| `@Past`, `@Future`, `@PastOrPresent` | date/time | temporal constraint |
| `@Positive`, `@PositiveOrZero` | numbers | sign constraint |

`ConstraintViolation<T>` holds the violated constraint, property path, invalid value, and message. The `Validator` interface has two key methods: `validate(T object, Class<?>... groups)` and `validateProperty(T object, String propertyName, Class<?>... groups)`.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Model -->
  <rect x="10" y="20" width="160" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ProductForm</text>
  <text x="90" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@NotBlank  String name</text>
  <text x="90" y="72" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@DecimalMin("0.01") price</text>
  <text x="90" y="86" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Min(1) int quantity</text>
  <text x="90" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Email String contactEmail</text>
  <text x="90" y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Valid Address address</text>

  <!-- Validator -->
  <rect x="240" y="20" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">jakarta.validation.Validator</text>
  <text x="340" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">validate(object, groups...)</text>
  <text x="340" y="72" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">validateProperty(object, field)</text>

  <!-- Violations -->
  <rect x="510" y="20" width="175" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="597" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ConstraintViolation</text>
  <text x="597" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getPropertyPath()</text>
  <text x="597" y="72" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getMessage()</text>
  <text x="597" y="86" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getInvalidValue()</text>
  <text x="597" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getRootBeanClass()</text>
  <text x="597" y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getConstraintDescriptor()</text>

  <defs>
    <marker id="a154" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="172" y1="70" x2="237" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a154)"/>
  <line x1="442" y1="50" x2="507" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a154)"/>

  <!-- Cascade -->
  <rect x="240" y="100" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="340" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Valid on nested field</text>
  <text x="340" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">triggers cascaded validation</text>

  <text x="350" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">LocalValidatorFactoryBean bridges jakarta.validation.Validator ↔ Spring Validator SPI</text>
</svg>

`LocalValidatorFactoryBean` bridges Jakarta `Validator` into Spring's own `Validator` interface; `@Valid` cascades recursively.

## 5. Runnable example

### Level 1 — Basic

Standalone Jakarta Validation without Spring, using Hibernate Validator.

```java
// BeanValidationBasic.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import java.math.*;
import java.util.*;

class OrderItem {
    @NotBlank(message = "SKU must not be blank")
    String sku;

    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.01", message = "Price must be at least 0.01")
    BigDecimal price;

    @Min(value = 1, message = "Quantity must be at least 1")
    @Max(value = 1000, message = "Quantity cannot exceed 1000")
    int quantity;

    @Email(message = "Contact email is invalid")
    String contactEmail;

    OrderItem(String sku, BigDecimal price, int quantity, String contactEmail) {
        this.sku = sku; this.price = price;
        this.quantity = quantity; this.contactEmail = contactEmail;
    }
}

public class BeanValidationBasic {
    public static void main(String[] args) {
        ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        Validator validator = factory.getValidator();

        // Valid item
        OrderItem valid = new OrderItem("SKU-001", new BigDecimal("9.99"), 5, "buyer@shop.com");
        Set<ConstraintViolation<OrderItem>> ok = validator.validate(valid);
        System.out.println("Valid item violations: " + ok.size());

        // Invalid item
        OrderItem invalid = new OrderItem("", new BigDecimal("-1"), 0, "not-an-email");
        Set<ConstraintViolation<OrderItem>> violations = validator.validate(invalid);
        System.out.println("\nInvalid item violations: " + violations.size());
        violations.stream()
            .sorted(Comparator.comparing(v -> v.getPropertyPath().toString()))
            .forEach(v -> System.out.println(
                "  [" + v.getPropertyPath() + "] " + v.getMessage() +
                " (value: '" + v.getInvalidValue() + "')"));

        factory.close();
    }
}
```

How to run (requires `hibernate-validator` + `jakarta.validation-api` on classpath): `java -cp 'hibernate-validator-*.jar:jakarta.validation-api-*.jar:classmate-*.jar:jboss-logging-*.jar:.' BeanValidationBasic.java`

`Validation.buildDefaultValidatorFactory()` bootstraps the Jakarta Validation runtime. `validator.validate(object)` returns all `ConstraintViolation`s. `getPropertyPath()` gives the field name; `getMessage()` the interpolated message.

### Level 2 — Intermediate

Cascaded validation with `@Valid`; validation groups; `validateProperty`.

```java
// BeanValidationIntermediate.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import jakarta.validation.groups.*;
import java.util.*;

interface OnCreate {}
interface OnUpdate {}

class Address {
    @NotBlank String street;
    @NotBlank String city;
    @Pattern(regexp = "[0-9]{5}", message = "Zip must be 5 digits")
    String zip;

    Address(String street, String city, String zip) {
        this.street = street; this.city = city; this.zip = zip;
    }
}

class Customer {
    @NotBlank(groups = {OnCreate.class, OnUpdate.class})
    String name;

    @Email
    @NotNull(groups = OnCreate.class, message = "Email required on create")
    String email;

    @NotNull(groups = OnCreate.class, message = "Address required on create")
    @Valid
    Address address;

    Customer(String name, String email, Address address) {
        this.name = name; this.email = email; this.address = address;
    }
}

public class BeanValidationIntermediate {
    public static void main(String[] args) {
        ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        Validator validator = factory.getValidator();

        // 1. Create group — address required
        System.out.println("=== OnCreate validation ===");
        Customer noAddr = new Customer("Alice", "alice@example.com", null);
        validator.validate(noAddr, OnCreate.class)
            .forEach(v -> System.out.println("  " + v.getPropertyPath() + ": " + v.getMessage()));

        // 2. Cascaded validation — invalid address
        System.out.println("\n=== Cascaded validation ===");
        Address badAddr = new Address("", "NYC", "ABCDE");
        Customer withBadAddr = new Customer("Bob", "bob@example.com", badAddr);
        validator.validate(withBadAddr, OnCreate.class)
            .forEach(v -> System.out.println("  " + v.getPropertyPath() + ": " + v.getMessage()));

        // 3. validateProperty — single field
        System.out.println("\n=== validateProperty ===");
        Customer partial = new Customer(null, "not-email", null);
        validator.validateProperty(partial, "email")
            .forEach(v -> System.out.println("  email: " + v.getMessage()));

        factory.close();
    }
}
```

How to run: same classpath as Level 1 with `java BeanValidationIntermediate.java`

`@Valid` on `address` field triggers validation of `Address` constraints, with path prefix `address.street`, `address.zip`. Validation groups let you run different constraints in different phases (`OnCreate` vs `OnUpdate`).

### Level 3 — Advanced

Custom constraint annotation + `ConstraintValidator`; class-level constraint; Spring integration via `LocalValidatorFactoryBean`.

```java
// BeanValidationAdvanced.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import java.lang.annotation.*;
import java.math.*;
import java.util.*;
import org.springframework.context.annotation.*;
import org.springframework.validation.beanvalidation.*;
import org.springframework.validation.*;

// Custom annotation
@Documented
@Constraint(validatedBy = SufficientFundsValidator.class)
@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@interface SufficientFunds {
    String message() default "Insufficient funds for this order";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

// Class-level validator
class SufficientFundsValidator implements ConstraintValidator<SufficientFunds, PurchaseOrder> {
    @Override
    public boolean isValid(PurchaseOrder order, ConstraintValidatorContext ctx) {
        if (order.accountBalance == null || order.totalAmount == null) return true; // skip — @NotNull covers these
        return order.accountBalance.compareTo(order.totalAmount) >= 0;
    }
}

@SufficientFunds
class PurchaseOrder {
    @NotBlank String productCode;
    @NotNull @Positive BigDecimal totalAmount;
    @NotNull BigDecimal accountBalance;

    PurchaseOrder(String productCode, BigDecimal totalAmount, BigDecimal accountBalance) {
        this.productCode = productCode;
        this.totalAmount = totalAmount;
        this.accountBalance = accountBalance;
    }
}

@Configuration
class ValidationCfg {
    @Bean
    public LocalValidatorFactoryBean validator() {
        return new LocalValidatorFactoryBean();
    }
}

public class BeanValidationAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ValidationCfg.class);
        SmartValidator validator = ctx.getBean(LocalValidatorFactoryBean.class);

        // Good order
        PurchaseOrder good = new PurchaseOrder("PROD-X", new BigDecimal("100"), new BigDecimal("500"));
        BeanPropertyBindingResult r1 = new BeanPropertyBindingResult(good, "order");
        validator.validate(good, r1);
        System.out.println("Good order errors: " + r1.getErrorCount());

        // Insufficient funds
        PurchaseOrder bad = new PurchaseOrder("PROD-X", new BigDecimal("600"), new BigDecimal("100"));
        BeanPropertyBindingResult r2 = new BeanPropertyBindingResult(bad, "order");
        validator.validate(bad, r2);
        System.out.println("Insufficient funds errors: " + r2.getErrorCount());
        r2.getAllErrors().forEach(e -> System.out.println("  " + e.getDefaultMessage()));

        ctx.close();
    }
}
```

How to run: requires `spring-context`, `hibernate-validator`, `jakarta.validation-api` on classpath.

`LocalValidatorFactoryBean` implements both Spring's `Validator` and Jakarta `Validator`. The class-level `@SufficientFunds` is evaluated after all field constraints; `ConstraintValidatorContext` can be used to build custom messages pointing to specific fields.

## 6. Walkthrough

Execution trace for `validator.validate(bad, r2)` in Level 3:

1. `LocalValidatorFactoryBean.validate(bad, r2)` delegates to the Jakarta `Validator`.
2. Jakarta Validator collects metadata: `@NotBlank`, `@NotNull @Positive`, `@NotNull`, `@SufficientFunds` (class-level).
3. Field constraints run first: `productCode`, `totalAmount`, `accountBalance` all pass.
4. Class-level `SufficientFundsValidator.isValid(bad, ctx)` runs: `100 < 600` → `false`.
5. Violation created with path `""` (class-level) and message `"Insufficient funds for this order"`.
6. `LocalValidatorFactoryBean` converts the `ConstraintViolation` into a Spring `FieldError` or `ObjectError` on the `BindingResult`.

## 7. Gotchas & takeaways

> `@NotEmpty` checks `size() > 0` on collections and `length() > 0` on strings, but does NOT check for whitespace-only strings. Use `@NotBlank` for strings where `"   "` should be invalid.

> Class-level constraints (like `@SufficientFunds` on the class) appear as `ObjectError` in the `BindingResult`, not as `FieldError`. They have an empty property path. Display them separately in form views.

- `@Valid` (Jakarta) triggers cascaded validation; `@Validated` (Spring) also enables method-level validation (AOP-based) and supports group sequences. For field-level cascading, `@Valid` is sufficient.
- Custom `ConstraintValidator.isValid()` must return `true` when the value is `null` if nullability is handled separately by `@NotNull`. Otherwise, `null` triggers both your validator and `@NotNull`.
- Hibernate Validator includes extra constraints not in the spec: `@URL`, `@Length`, `@Range`, `@CreditCardNumber`, `@ISBN`. These are in the `org.hibernate.validator.constraints` package.
- `ValidatorFactory` is heavy — build once and reuse. In Spring, `LocalValidatorFactoryBean` is a singleton bean that manages the factory lifecycle.
