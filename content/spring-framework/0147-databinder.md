---
card: spring-framework
gi: 147
slug: databinder
title: "DataBinder"
---

## 1. What it is

`DataBinder` binds property values (from a `Map<String, Object>` or `PropertyValues`) onto a target JavaBean. It handles type conversion automatically and accumulates binding errors in an `Errors` / `BindingResult`. It also applies `Validator` objects before or after binding.

```java
DataBinder binder = new DataBinder(target, "order");
binder.bind(new MutablePropertyValues(Map.of(
    "amount", "250.00",
    "currency", "USD"
)));
BindingResult result = binder.getBindingResult();
```

## 2. Why & when

- **CLI / batch input binding** — bind incoming key-value maps (parsed CSV rows, command-line args, message queue payloads) onto domain objects without web-layer infrastructure.
- **Test support** — simulate Spring MVC form binding in unit tests without spinning up a `MockMvc`.
- **Custom binding** — register `PropertyEditor` or `ConversionService` converters to handle custom type mappings during binding.
- **Service-layer binding + validation** — bind then validate in a single unit:
  ```java
  binder.validate();
  if (result.hasErrors()) { /* handle */ }
  ```
- **Whitelist / blacklist fields** — `setAllowedFields` / `setDisallowedFields` prevent mass-assignment vulnerabilities.

## 3. Core concept

`DataBinder` lifecycle:

1. **Create** — `new DataBinder(targetObject, objectName)`.
2. **Configure** — set `ConversionService`, allowed/disallowed fields, required fields, validators.
3. **Bind** — `binder.bind(new MutablePropertyValues(map))` applies the values.
4. **Validate** — `binder.validate()` runs registered `Validator` objects.
5. **Inspect** — `binder.getBindingResult()` (a `BindingResult` with binding errors + validation errors).

Key configuration methods:

| Method | Purpose |
|---|---|
| `setAllowedFields("name","email")` | Whitelist — only these fields can be bound |
| `setDisallowedFields("role","admin")` | Blacklist — these fields are never bound |
| `setRequiredFields("name","amount")` | Fail binding if these keys are absent |
| `setConversionService(cs)` | Custom type conversion |
| `addValidators(v1, v2)` | Register validators to run on `validate()` |
| `setBindingErrorProcessor(...)` | Customize binding-error → `Errors` mapping |

`BeanPropertyBindingResult` (what `binder.getBindingResult()` returns) implements both `Errors` and `BindingResult`.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Input map -->
  <rect x="10" y="50" width="150" height="90" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="75" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Input Map</text>
  <text x="85" y="93" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">"amount" → "250.00"</text>
  <text x="85" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"currency" → "USD"</text>
  <text x="85" y="121" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"admin" → "true"</text>

  <!-- DataBinder -->
  <rect x="220" y="30" width="200" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">DataBinder</text>
  <text x="320" y="70" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">allowedFields: [amount, currency]</text>
  <text x="320" y="84" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">disallowedFields: [admin]</text>
  <text x="320" y="98" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">type: "250.00" → double 250.0</text>
  <text x="320" y="112" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">validate() → Validator runs</text>
  <text x="320" y="126" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getBindingResult()</text>
  <text x="320" y="140" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">→ BindingResult (errors + values)</text>

  <!-- Target -->
  <rect x="485" y="50" width="200" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="73" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Target JavaBean</text>
  <text x="585" y="91" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">amount = 250.0 (bound)</text>
  <text x="585" y="107" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">currency = "USD" (bound)</text>
  <text x="585" y="123" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">admin = unchanged (blocked)</text>

  <defs>
    <marker id="a147" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="162" y1="95" x2="217" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a147)"/>
  <line x1="422" y1="95" x2="482" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a147)"/>

  <text x="350" y="183" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DataBinder: type-converts input, enforces field whitelist, then runs Validators</text>
</svg>

`DataBinder` converts and binds input values to a target bean, blocking disallowed fields and running validators.

## 5. Runnable example

### Level 1 — Basic

Bind a string map to a JavaBean; observe type conversion; check binding errors.

```java
// DataBinderBasic.java
import org.springframework.validation.*;

class Product {
    private String name;
    private double price;
    private int quantity;
    private boolean active;

    public void setName(String name)         { this.name = name; }
    public void setPrice(double price)       { this.price = price; }
    public void setQuantity(int quantity)    { this.quantity = quantity; }
    public void setActive(boolean active)    { this.active = active; }

    public String getName()    { return name; }
    public double getPrice()   { return price; }
    public int getQuantity()   { return quantity; }
    public boolean isActive()  { return active; }

    @Override
    public String toString() {
        return "Product{name=" + name + ",price=" + price +
            ",quantity=" + quantity + ",active=" + active + "}";
    }
}

public class DataBinderBasic {
    public static void main(String[] args) {
        Product target = new Product();
        DataBinder binder = new DataBinder(target, "product");

        // Bind string values — DataBinder converts to correct types
        MutablePropertyValues pvs = new MutablePropertyValues();
        pvs.add("name",     "Widget Pro");
        pvs.add("price",    "49.99");     // String → double
        pvs.add("quantity", "100");       // String → int
        pvs.add("active",   "true");      // String → boolean

        binder.bind(pvs);

        System.out.println("Bound: " + target);
        System.out.println("Errors: " + binder.getBindingResult().getErrorCount());

        // Introduce a type mismatch
        Product target2 = new Product();
        DataBinder binder2 = new DataBinder(target2, "product");
        MutablePropertyValues pvs2 = new MutablePropertyValues();
        pvs2.add("price",    "not-a-number");  // will cause binding error
        pvs2.add("quantity", "abc");           // will cause binding error
        pvs2.add("name",     "Broken Widget");

        binder2.bind(pvs2);
        BindingResult result = binder2.getBindingResult();

        System.out.println("\nBound with errors: " + target2);
        System.out.println("Error count: " + result.getErrorCount());
        result.getFieldErrors().forEach(fe ->
            System.out.println("  field=" + fe.getField() +
                " code=" + fe.getCode() +
                " rejected='" + fe.getRejectedValue() + "'"));
    }
}
```

How to run: `java DataBinderBasic.java`

Successful binding converts `"49.99"` → `double`, `"100"` → `int`, `"true"` → `boolean`. Failed binding for `"not-a-number"` records a `typeMismatch` error; the field retains its zero value, not the rejected string.

### Level 2 — Intermediate

`setAllowedFields` whitelist; `setRequiredFields` mandatory check; integrated `Validator`.

```java
// DataBinderSecurity.java
import org.springframework.validation.*;
import java.util.*;

class UserRegistration {
    private String username;
    private String email;
    private String password;
    private String role;       // must NOT be settable from user input

    public void setUsername(String u) { this.username = u; }
    public void setEmail(String e)    { this.email = e; }
    public void setPassword(String p) { this.password = p; }
    public void setRole(String r)     { this.role = r; }

    public String getUsername() { return username; }
    public String getEmail()    { return email; }
    public String getPassword() { return password; }
    public String getRole()     { return role; }

    @Override
    public String toString() {
        return "User{username=" + username + ",email=" + email + ",role=" + role + "}";
    }
}

class UserRegistrationValidator implements Validator {
    @Override
    public boolean supports(Class<?> c) {
        return UserRegistration.class.isAssignableFrom(c);
    }

    @Override
    public void validate(Object t, Errors errors) {
        UserRegistration u = (UserRegistration) t;
        ValidationUtils.rejectIfEmptyOrWhitespace(errors, "username", "username.blank");
        if (u.getEmail() == null || !u.getEmail().contains("@")) {
            errors.rejectValue("email", "email.invalid", "Must be a valid email");
        }
        if (u.getPassword() == null || u.getPassword().length() < 8) {
            errors.rejectValue("password", "password.weak",
                "Password must be at least 8 characters");
        }
    }
}

public class DataBinderSecurity {
    static void bindAndValidate(Map<String, Object> input) {
        System.out.println("\n=== Input: " + input + " ===");
        UserRegistration target = new UserRegistration();
        DataBinder binder = new DataBinder(target, "userRegistration");

        // Security: whitelist only user-provided fields
        binder.setAllowedFields("username", "email", "password");
        // Required fields must be present
        binder.setRequiredFields("username", "email", "password");

        binder.addValidators(new UserRegistrationValidator());

        binder.bind(new MutablePropertyValues(input));
        binder.validate();

        BindingResult result = binder.getBindingResult();
        System.out.println("  target: " + target);
        if (result.hasErrors()) {
            result.getAllErrors().forEach(e ->
                System.out.println("  ERROR [" + e.getCode() + "]: " + e.getDefaultMessage()));
        } else {
            System.out.println("  VALID — would save user");
        }
    }

    public static void main(String[] args) {
        // Valid registration
        bindAndValidate(Map.of(
            "username", "alice",
            "email",    "alice@example.com",
            "password", "Secur3P@ss"));

        // Mass-assignment attack attempt (role is not in allowedFields)
        bindAndValidate(Map.of(
            "username", "mallory",
            "email",    "mallory@evil.com",
            "password", "password123",
            "role",     "ADMIN"));       // silently ignored

        // Missing required fields
        bindAndValidate(Map.of(
            "username", "bob",
            "email",    "not-an-email"));  // missing password, invalid email
    }
}
```

How to run: `java DataBinderSecurity.java`

`setAllowedFields` whitelists bind targets — `role` is silently ignored even though it's in the input. `setRequiredFields` adds a missing-field error if `password` is absent. `addValidators` runs `UserRegistrationValidator` on `binder.validate()`.

### Level 3 — Advanced

Custom `ConversionService` for bespoke types; `setBindingErrorProcessor`; nested bean binding.

```java
// DataBinderAdvanced.java
import org.springframework.core.convert.*;
import org.springframework.core.convert.support.*;
import org.springframework.format.support.*;
import org.springframework.validation.*;
import java.util.*;

// Custom value types
record Money(double amount, String currency) {
    @Override public String toString() { return amount + " " + currency; }
}

record Priority(String level) {
    static Priority of(String s) {
        return switch (s.toUpperCase()) {
            case "HIGH", "MEDIUM", "LOW" -> new Priority(s.toUpperCase());
            default -> throw new ConversionFailedException(
                TypeDescriptor.valueOf(String.class),
                TypeDescriptor.valueOf(Priority.class),
                s, new IllegalArgumentException("Unknown priority: " + s));
        };
    }
}

// Converters
class StringToMoneyConverter implements Converter<String, Money> {
    @Override
    public Money convert(String source) {
        // Expected format: "250.00 USD"
        String[] parts = source.split(" ");
        if (parts.length != 2) throw new IllegalArgumentException("Invalid money format: " + source);
        return new Money(Double.parseDouble(parts[0]), parts[1]);
    }
}

class StringToPriorityConverter implements Converter<String, Priority> {
    @Override
    public Priority convert(String source) { return Priority.of(source); }
}

// Target bean with custom types
class WorkOrder {
    private String title;
    private Money  budget;
    private Priority priority;
    private int     daysEstimated;

    public void setTitle(String t)         { this.title = t; }
    public void setBudget(Money m)         { this.budget = m; }
    public void setPriority(Priority p)    { this.priority = p; }
    public void setDaysEstimated(int d)    { this.daysEstimated = d; }

    public String getTitle()      { return title; }
    public Money getBudget()      { return budget; }
    public Priority getPriority() { return priority; }
    public int getDaysEstimated() { return daysEstimated; }

    @Override
    public String toString() {
        return "WorkOrder{title=" + title + ",budget=" + budget +
            ",priority=" + priority + ",days=" + daysEstimated + "}";
    }
}

public class DataBinderAdvanced {
    static FormattingConversionService buildConversionService() {
        var cs = new FormattingConversionService();
        cs.addConverter(new StringToMoneyConverter());
        cs.addConverter(new StringToPriorityConverter());
        return cs;
    }

    static void bind(Map<String, Object> input) {
        System.out.println("\n=== " + input + " ===");
        WorkOrder target = new WorkOrder();
        DataBinder binder = new DataBinder(target, "workOrder");
        binder.setConversionService(buildConversionService());
        binder.setAllowedFields("title", "budget", "priority", "daysEstimated");
        binder.setRequiredFields("title", "budget", "priority");

        binder.bind(new MutablePropertyValues(input));
        BindingResult result = binder.getBindingResult();

        System.out.println("  target: " + target);
        if (result.hasErrors()) {
            result.getAllErrors().forEach(e -> {
                String field = e instanceof FieldError fe ? "[" + fe.getField() + "] " : "[global] ";
                System.out.println("  ERROR " + field + e.getDefaultMessage()
                    + " (code: " + e.getCode() + ")");
            });
        } else {
            System.out.println("  VALID");
        }
    }

    public static void main(String[] args) {
        bind(Map.of("title", "Office Renovation",
            "budget", "15000.00 USD",
            "priority", "HIGH",
            "daysEstimated", "30"));  // all valid

        bind(Map.of("title", "Server Migration",
            "budget", "bad-format",         // conversion failure
            "priority", "CRITICAL",         // not a valid priority
            "daysEstimated", "not-a-number"));  // type mismatch
    }
}
```

How to run: `java DataBinderAdvanced.java`

`FormattingConversionService` with custom converters enables `"15000.00 USD"` → `Money` and `"HIGH"` → `Priority` binding. Conversion failures produce `typeMismatch` errors in `BindingResult`. The `DataBinder` handles all three error types (missing required, type mismatch, conversion failure) in the same `BindingResult`.

## 6. Walkthrough

Execution for Level 3 valid case:

1. **`binder.setConversionService(cs)`** — registers `StringToMoneyConverter` and `StringToPriorityConverter`.
2. **`binder.bind(pvs)`** — processes each allowed field:
   - `"title" = "Office Renovation"` → `String` → assigned.
   - `"budget" = "15000.00 USD"` → `StringToMoneyConverter` → `Money(15000.0, "USD")` → assigned.
   - `"priority" = "HIGH"` → `StringToPriorityConverter` → `Priority("HIGH")` → assigned.
   - `"daysEstimated" = "30"` → default `String→int` converter → `30` → assigned.
3. **`result.hasErrors()`** → `false`.
4. **`target.toString()`** → `WorkOrder{title=Office Renovation,budget=15000.0 USD,priority=Priority[level=HIGH],days=30}`.

## 7. Gotchas & takeaways

> **`setAllowedFields` prevents mass-assignment attacks**. Without it, any property on the target bean can be bound from user input — including security-critical fields like `role`, `enabled`, `isAdmin`. Always declare an allowed-fields whitelist for beans bound from external input.

> `binder.validate()` runs validators AFTER binding. If binding itself produced errors (type mismatches), those errors are already in `BindingResult` — `validate()` adds validation errors on top. Check `result.getBindingErrorCount()` separately from `result.getFieldErrorCount()` to distinguish binding failures from business-rule violations.

- `setRequiredFields` checks for key PRESENCE in the source map, not for non-null/non-empty values. For business-rule empty checks, use `ValidationUtils.rejectIfEmptyOrWhitespace` in a `Validator`.
- `DataBinder` is the foundation of Spring MVC's model binding — `@ModelAttribute` uses `DataBinder` internally with `WebDataBinder` (which adds HTTP request parameter support).
- In Spring MVC, `@InitBinder` methods configure a `WebDataBinder` that applies to every request in a controller — use them to register custom editors, converters, and validators.
- `binder.getBindingResult()` always returns a `BindingResult` — you don't need to call `binder.validate()` if you only care about binding errors.
