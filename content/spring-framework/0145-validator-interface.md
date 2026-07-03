---
card: spring-framework
gi: 145
slug: validator-interface
title: "Validator interface"
---

## 1. What it is

`Validator` is Spring's programmatic validation interface with two methods: `supports(Class)` (can this validator validate objects of this type?) and `validate(Object, Errors)` (perform the validation; record failures via `Errors`). It is independent of any web layer — usable in any Spring application layer.

```java
class OrderValidator implements Validator {
    @Override
    public boolean supports(Class<?> clazz) {
        return Order.class.isAssignableFrom(clazz);
    }

    @Override
    public void validate(Object target, Errors errors) {
        Order o = (Order) target;
        if (o.getAmount() <= 0) {
            errors.rejectValue("amount", "amount.negative",
                "Amount must be positive");
        }
    }
}
```

## 2. Why & when

- **Service-layer validation** — validate domain objects before they reach the database, independent of the web layer.
- **Complex rules** — cross-field checks, database lookups, or business rules that can't be expressed with Bean Validation annotations.
- **Reusable rules** — compose validators (`ValidationUtils`, nested `Validator` delegation).
- **Spring MVC integration** — bound to `@InitBinder` in controllers to run automatically on form submissions.
- **Pre-JSR-303 style** — still useful for domain-specific validation where annotation-driven Bean Validation is awkward.

## 3. Core concept

`Errors` (also implemented by `BindingResult` in MVC) accumulates validation failures:

| Method | Usage |
|---|---|
| `errors.reject(code)` | Global error (not tied to a field) |
| `errors.reject(code, defaultMessage)` | Global error with fallback message |
| `errors.rejectValue(field, code)` | Field-level error |
| `errors.rejectValue(field, code, args, message)` | Field error with message arguments |
| `errors.hasErrors()` | True if any errors were recorded |
| `errors.getFieldErrors()` | List of field-level errors |

`ValidationUtils` provides convenience methods:

```java
ValidationUtils.rejectIfEmpty(errors, "name", "name.empty");
ValidationUtils.rejectIfEmptyOrWhitespace(errors, "email", "email.blank");
```

Nested validation via `errors.pushNestedPath("address")` / `errors.popNestedPath()` lets you delegate to a child validator for nested objects.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Validator -->
  <rect x="10" y="25" width="165" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="92" y="46" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">&lt;&lt;Validator&gt;&gt;</text>
  <text x="92" y="62" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">supports(Class) : boolean</text>
  <text x="92" y="76" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">validate(Object, Errors)</text>

  <!-- Errors -->
  <rect x="235" y="25" width="190" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">&lt;&lt;Errors&gt;&gt;</text>
  <text x="330" y="62" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">reject(code, defaultMsg)</text>
  <text x="330" y="76" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">rejectValue(field, code)</text>
  <text x="330" y="90" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">hasErrors() / getFieldErrors()</text>
  <text x="330" y="104" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">pushNestedPath / popNestedPath</text>

  <!-- BeanPropertyBindingResult -->
  <rect x="235" y="130" width="190" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="150" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BeanPropertyBindingResult</text>
  <text x="330" y="162" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">standalone Errors impl</text>

  <!-- ValidationUtils -->
  <rect x="490" y="25" width="200" height="55" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="590" y="45" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ValidationUtils</text>
  <text x="590" y="61" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">rejectIfEmpty(errors, field, code)</text>
  <text x="590" y="73" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">rejectIfEmptyOrWhitespace</text>

  <defs>
    <marker id="a145" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b145" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <line x1="177" y1="55" x2="232" y2="55" stroke="#6db33f" stroke-width="2" marker-end="url(#a145)"/>
  <line x1="330" y1="117" x2="330" y2="127" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b145)"/>

  <text x="350" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Validator writes failures to Errors; BeanPropertyBindingResult is the standalone Errors implementation</text>
</svg>

`Validator` writes failures to `Errors`; `BeanPropertyBindingResult` is the standalone `Errors` implementation for service-layer use.

## 5. Runnable example

### Level 1 — Basic

A simple `Validator` for an `Order` domain object; standalone usage with `BeanPropertyBindingResult`.

```java
// ValidatorBasic.java
import org.springframework.validation.*;

class Order {
    private String customerId;
    private double amount;
    private String currency;

    Order(String customerId, double amount, String currency) {
        this.customerId = customerId;
        this.amount = amount;
        this.currency = currency;
    }

    public String getCustomerId() { return customerId; }
    public double getAmount()     { return amount; }
    public String getCurrency()   { return currency; }
}

class OrderValidator implements Validator {
    @Override
    public boolean supports(Class<?> clazz) {
        return Order.class.isAssignableFrom(clazz);
    }

    @Override
    public void validate(Object target, Errors errors) {
        Order o = (Order) target;

        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "customerId",
            "customerId.blank", "Customer ID is required");

        if (o.getAmount() <= 0) {
            errors.rejectValue("amount", "amount.nonPositive",
                "Amount must be greater than zero");
        }
        if (o.getAmount() > 100_000) {
            errors.rejectValue("amount", "amount.tooLarge",
                new Object[]{100_000}, "Amount exceeds maximum of {0}");
        }

        if (o.getCurrency() == null || !o.getCurrency().matches("[A-Z]{3}")) {
            errors.rejectValue("currency", "currency.invalid",
                "Currency must be a 3-letter ISO code");
        }
    }
}

public class ValidatorBasic {
    static void validate(Order o) {
        Errors errors = new BeanPropertyBindingResult(o, "order");
        new OrderValidator().validate(o, errors);

        System.out.println("Order: customerId=" + o.getCustomerId() +
            " amount=" + o.getAmount() + " currency=" + o.getCurrency());
        if (errors.hasErrors()) {
            errors.getAllErrors().forEach(e ->
                System.out.println("  ERROR [" + e.getCode() + "] " + e.getDefaultMessage()));
        } else {
            System.out.println("  VALID");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        validate(new Order("CUST-001", 250.00, "USD"));   // valid
        validate(new Order("", -10.00, "usd"));           // 3 errors
        validate(new Order("CUST-002", 150_000, "EUR"));  // amount too large
        validate(new Order("CUST-003", 0, "GBP"));        // amount zero
    }
}
```

How to run: `java ValidatorBasic.java`

`BeanPropertyBindingResult` wraps the target object and accumulates errors. `ValidationUtils.rejectIfEmptyOrWhitespace` handles null and blank checks. Multiple `rejectValue` calls accumulate all violations before the method returns.

### Level 2 — Intermediate

Nested object validation with `pushNestedPath`; composing two validators.

```java
// ValidatorNested.java
import org.springframework.validation.*;

class Address {
    private String street;
    private String city;
    private String zipCode;

    Address(String street, String city, String zipCode) {
        this.street  = street;
        this.city    = city;
        this.zipCode = zipCode;
    }

    public String getStreet()  { return street;  }
    public String getCity()    { return city;    }
    public String getZipCode() { return zipCode; }
}

class Customer {
    private String name;
    private String email;
    private Address billingAddress;

    Customer(String name, String email, Address billingAddress) {
        this.name           = name;
        this.email          = email;
        this.billingAddress = billingAddress;
    }

    public String getName()           { return name;           }
    public String getEmail()          { return email;          }
    public Address getBillingAddress(){ return billingAddress; }
}

class AddressValidator implements Validator {
    @Override
    public boolean supports(Class<?> c) { return Address.class.isAssignableFrom(c); }

    @Override
    public void validate(Object target, Errors errors) {
        Address a = (Address) target;
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "street",  "street.blank");
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "city",    "city.blank");
        if (a.getZipCode() == null || !a.getZipCode().matches("\\d{5}")) {
            errors.rejectValue("zipCode", "zipCode.invalid", "Must be 5 digits");
        }
    }
}

class CustomerValidator implements Validator {
    private final AddressValidator addressValidator = new AddressValidator();

    @Override
    public boolean supports(Class<?> c) { return Customer.class.isAssignableFrom(c); }

    @Override
    public void validate(Object target, Errors errors) {
        Customer c = (Customer) target;
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "name", "name.blank");

        if (c.getEmail() == null || !c.getEmail().contains("@")) {
            errors.rejectValue("email", "email.invalid", "Must be a valid email");
        }

        if (c.getBillingAddress() != null) {
            // Delegate to AddressValidator with nested path
            errors.pushNestedPath("billingAddress");
            ValidationUtils.invokeValidator(addressValidator, c.getBillingAddress(), errors);
            errors.popNestedPath();
        } else {
            errors.rejectValue("billingAddress", "billingAddress.null");
        }
    }
}

public class ValidatorNested {
    static void validate(Customer c) {
        Errors errors = new BeanPropertyBindingResult(c, "customer");
        new CustomerValidator().validate(c, errors);

        System.out.println("Customer: " + c.getName() + " <" + c.getEmail() + ">");
        if (errors.hasErrors()) {
            errors.getAllErrors().forEach(e ->
                System.out.println("  ERROR [" + e.getCode() + "]: " + e.getDefaultMessage()));
        } else {
            System.out.println("  VALID");
        }
        System.out.println();
    }

    public static void main(String[] args) {
        validate(new Customer("Alice", "alice@example.com",
            new Address("123 Main St", "Springfield", "12345")));     // valid

        validate(new Customer("Bob", "not-an-email",
            new Address("", "Portland", "ABCDE")));                   // email + address errors

        validate(new Customer("Carol", "carol@test.com", null));       // null address
    }
}
```

How to run: `java ValidatorNested.java`

`errors.pushNestedPath("billingAddress")` prepends the nested path to all subsequent error codes: field `"street"` becomes `"billingAddress.street"`. `ValidationUtils.invokeValidator` is the recommended delegate call — it checks `supports()` before calling `validate()`.

### Level 3 — Advanced

`Validator` integrated into a service layer; collect all errors; return structured validation results; registration via `DataBinder`.

```java
// ValidatorServiceLayer.java
import org.springframework.validation.*;
import java.util.*;

// Domain model
record Product(String sku, String name, double price, int stock, String category) {}

// Validation result DTO
record ValidationResult(boolean valid, List<String> errors) {
    static ValidationResult of(Errors e) {
        if (!e.hasErrors()) return new ValidationResult(true, List.of());
        return new ValidationResult(false,
            e.getAllErrors().stream()
             .map(oe -> oe.getObjectName() + (oe instanceof FieldError fe ? "." + fe.getField() : "")
                 + ": " + oe.getDefaultMessage())
             .toList());
    }
}

class ProductValidator implements Validator {
    private static final Set<String> VALID_CATEGORIES =
        Set.of("electronics", "clothing", "food", "furniture");

    @Override
    public boolean supports(Class<?> c) { return Product.class.isAssignableFrom(c); }

    @Override
    public void validate(Object target, Errors errors) {
        Product p = (Product) target;

        if (p.sku() == null || !p.sku().matches("[A-Z]{3}-\\d{4}")) {
            errors.rejectValue("sku", "sku.format", "SKU must match AAA-0000");
        }

        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "name", "name.blank", "Name required");

        if (p.price() < 0) {
            errors.rejectValue("price", "price.negative", "Price cannot be negative");
        }
        if (p.price() > 99_999.99) {
            errors.rejectValue("price", "price.tooHigh",
                new Object[]{99_999.99}, "Price exceeds maximum of {0}");
        }

        if (p.stock() < 0) {
            errors.rejectValue("stock", "stock.negative", "Stock cannot be negative");
        }

        if (!VALID_CATEGORIES.contains(p.category())) {
            errors.rejectValue("category", "category.unknown",
                new Object[]{VALID_CATEGORIES}, "Unknown category; valid: {0}");
        }
    }
}

// Service that validates before persisting
class ProductService {
    private final ProductValidator validator = new ProductValidator();

    public ValidationResult save(Product p) {
        Errors errors = new BeanPropertyBindingResult(p, "product");
        validator.validate(p, errors);
        ValidationResult result = ValidationResult.of(errors);

        if (result.valid()) {
            System.out.println("[ProductService] saved: " + p.sku() + " – " + p.name());
        } else {
            System.out.println("[ProductService] rejected: " + p.sku());
        }
        return result;
    }
}

public class ValidatorServiceLayer {
    public static void main(String[] args) {
        var svc = new ProductService();

        var products = List.of(
            new Product("ELC-1001", "Laptop Pro",  1499.99, 10, "electronics"),
            new Product("bad-sku",  "Shirt",       29.99,   50, "clothing"),
            new Product("FOO-9999", "",            -5.00,   -1, "unknown-cat"),
            new Product("FRN-0042", "Office Chair", 0,       0, "furniture")
        );

        for (Product p : products) {
            ValidationResult result = svc.save(p);
            if (!result.valid()) {
                result.errors().forEach(e -> System.out.println("  " + e));
            }
            System.out.println();
        }
    }
}
```

How to run: `java ValidatorServiceLayer.java`

`ProductService.save()` creates a fresh `BeanPropertyBindingResult`, runs validation, and converts the `Errors` object into a structured `ValidationResult`. All validation failures are collected before returning — no early exit.

## 6. Walkthrough

Execution for the invalid product `new Product("FOO-9999", "", -5.00, -1, "unknown-cat")`:

1. **`validate(p, errors)`** called.
2. `p.sku() = "FOO-9999"` matches `[A-Z]{3}-\d{4}` → no error.
3. `ValidationUtils.rejectIfEmptyOrWhitespace(errors, "name", ...)` → `""` is whitespace → `errors.rejectValue("name", "name.blank", "Name required")`.
4. `p.price() = -5.00 < 0` → `errors.rejectValue("price", "price.negative", "Price cannot be negative")`.
5. `p.stock() = -1 < 0` → `errors.rejectValue("stock", "stock.negative", "Stock cannot be negative")`.
6. `VALID_CATEGORIES.contains("unknown-cat")` → `false` → `errors.rejectValue("category", "category.unknown", ...)`.
7. `errors.hasErrors()` → `true` (4 errors).
8. `ValidationResult.of(errors)` → `valid=false`, 4 error messages.

## 7. Gotchas & takeaways

> `Validator.validate()` should be side-effect-free and collect ALL validation failures before returning — do not throw exceptions for individual field failures. The caller needs the full list of errors to present to the user, not just the first one. Return early only for catastrophic preconditions where further validation is meaningless (e.g., a null target).

> `ValidationUtils.invokeValidator(childValidator, childObject, errors)` checks `childValidator.supports(childObject.getClass())` before calling `validate()`. If you call `childValidator.validate(childObject, errors)` directly and the types don't match, you get a `ClassCastException` at the cast site, not a helpful error.

- `Errors` (the service-layer interface) and `BindingResult` (the MVC extension) share the same rejection API — a `Validator` written against `Errors` works unchanged in Spring MVC controllers.
- Error codes follow a hierarchy: Spring resolves `amount.nonPositive.order.amount` → `amount.nonPositive.amount` → `amount.nonPositive` → `nonPositive` (using `DefaultMessageCodesResolver`).
- For annotation-driven Bean Validation (JSR-303), use `@Valid` / `@Validated` — Spring's `Validator` is the programmatic complement for rules that can't be expressed as annotations.
- Composing validators: use `ValidationUtils.invokeValidator(delegatedValidator, nestedObject, errors)` rather than calling `validate()` directly to get type checking.
