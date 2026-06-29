---
card: spring-boot
gi: 270
slug: validation-bean-validation-auto-config
title: Validation (Bean Validation) auto-config
---

## 1. What it is

**Bean Validation** (Jakarta Bean Validation / JSR-380) is a standard Java API for declaring constraints on classes using annotations (`@NotNull`, `@Size`, `@Email`, `@Pattern`, etc.). Spring Boot auto-configures a `Validator` bean (backed by Hibernate Validator, the reference implementation) when `spring-boot-starter-validation` is on the classpath.

Key integration points:
- **`@Valid` / `@Validated` on controller method parameters** — validates incoming request body or query params automatically, returning `400 Bad Request` with error details on failure.
- **`@Validated` on service classes** — validates method arguments and return values at the service layer.
- **Validation of `@ConfigurationProperties` classes** — validates configuration at startup.
- **Custom constraint annotations** — implement `ConstraintValidator<A, T>` to define your own rules.

Add with: `spring-boot-starter-validation` (includes `hibernate-validator`).

## 2. Why & when

Validation at the controller layer catches bad input before it reaches the database, preventing constraint violation exceptions and providing user-friendly error messages. Bean Validation is preferable to manual `if` checks because:

- Declarative — constraints live with the model class, not scattered in service logic.
- Reusable — the same `@Email @NotBlank String email` field is validated consistently everywhere it appears.
- Internationalised — error messages come from `messages.properties` with locale support.
- Composable — multiple constraints on one field (`@NotBlank @Size(max=100)`).

Use `@Valid` for controller request bodies. Use `@Validated` for service-layer method argument validation (requires a Spring proxy). Use `@Validated` on `@ConfigurationProperties` to catch misconfiguration at startup instead of at runtime.

## 3. Core concept

The validation pipeline for a `@PostMapping`:

1. Jackson deserialises the JSON body to a Java object.
2. Because the parameter is annotated `@Valid`, `MethodValidationInterceptor` calls the `javax.validation.Validator`.
3. The validator checks all constraint annotations on the object.
4. If any constraint fails, Spring throws `MethodArgumentNotValidException`.
5. A `@ExceptionHandler` or Spring's default `DefaultHandlerExceptionResolver` converts this to a `400 Bad Request` response with field-level error details.

Common constraint annotations:

| Annotation | Validates |
|---|---|
| `@NotNull` | Field is not null |
| `@NotBlank` | String not null, not empty after trim |
| `@Size(min, max)` | String/collection length |
| `@Min` / `@Max` | Numeric range |
| `@Email` | Email format |
| `@Pattern(regexp)` | Custom regex |
| `@Positive` / `@PositiveOrZero` | Number > 0 or >= 0 |
| `@Future` / `@Past` | Date in future or past |
| `@Valid` | Cascade validation to nested objects |

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bean Validation pipeline from HTTP request to validated object or 400 error">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arrr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>

  <rect x="10" y="95" width="100" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">POST /users</text>
  <text x="60" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JSON body</text>

  <rect x="160" y="85" width="130" height="70" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="225" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Jackson</text>
  <text x="225" y="126" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Deserialise JSON</text>
  <text x="225" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ UserRequest obj</text>

  <rect x="340" y="85" width="130" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="405" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Validator</text>
  <text x="405" y="126" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Check constraints</text>
  <text x="405" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Valid @NotBlank...</text>

  <!-- Success path -->
  <rect x="520" y="55" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="600" y="78" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Controller method runs ✓</text>

  <!-- Failure path -->
  <rect x="520" y="145" width="160" height="40" rx="6" fill="#1c2430" stroke="#8b1a1a" stroke-width="1.5"/>
  <text x="600" y="162" fill="#ff7b72" font-size="10" text-anchor="middle" font-family="sans-serif">400 Bad Request ✗</text>
  <text x="600" y="177" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">field errors in body</text>

  <line x1="110" y1="120" x2="158" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="290" y1="120" x2="338" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="470" y1="100" x2="518" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="470" y1="140" x2="518" y2="157" stroke="#ff7b72" stroke-width="1.5" marker-end="url(#arrr)"/>
</svg>

Valid input flows to the controller; invalid input returns a `400` with field-level error messages before the controller runs.

## 5. Runnable example

```java
// ValidationAutoConfigDemo.java — run with: java ValidationAutoConfigDemo.java
// Demonstrates Bean Validation constraints and programmatic validator usage —
// equivalent to what Spring Boot wires automatically via @Valid.

import jakarta.validation.*;
import jakarta.validation.constraints.*;
import java.util.Set;

public class ValidationAutoConfigDemo {

    // A request body class — Spring's @Valid triggers validation on this
    record CreateUserRequest(
        @NotBlank(message = "Name is required")
        @Size(min = 2, max = 100, message = "Name must be 2–100 characters")
        String name,

        @NotBlank(message = "Email is required")
        @Email(message = "Must be a valid email address")
        String email,

        @Min(value = 18, message = "Must be at least 18")
        @Max(value = 120, message = "Must be at most 120")
        int age,

        @Pattern(regexp = "\\+?[0-9 ()-]{7,15}",
                 message = "Phone must be a valid number")
        String phone  // nullable — null is valid (not @NotNull)
    ) {}

    public static void main(String[] args) {
        System.out.println("=== Bean Validation Auto-config Demo ===\n");

        // Build a validator (Spring Boot creates this automatically via ValidatorAutoConfiguration)
        ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        Validator validator = factory.getValidator();

        validateAndPrint(validator, "VALID request",
            new CreateUserRequest("Alice", "alice@example.com", 30, "+1 555 1234"));

        validateAndPrint(validator, "INVALID: blank name, bad email, underage",
            new CreateUserRequest("", "not-an-email", 15, null));

        validateAndPrint(validator, "INVALID: name too short, bad phone",
            new CreateUserRequest("A", "bob@example.com", 25, "abc"));

        printSpringIntegration();
    }

    static void validateAndPrint(Validator v, String label, CreateUserRequest req) {
        Set<ConstraintViolation<CreateUserRequest>> violations = v.validate(req);
        System.out.println("--- " + label + " ---");
        if (violations.isEmpty()) {
            System.out.println("  OK: All constraints satisfied");
        } else {
            violations.forEach(cv ->
                System.out.printf("  VIOLATION: [%s] %s%n",
                    cv.getPropertyPath(), cv.getMessage()));
        }
        System.out.println();
    }

    static void printSpringIntegration() {
        System.out.println("--- Spring Boot controller integration ---");
        System.out.println("""
            @RestController
            @RequestMapping("/users")
            public class UserController {

                @PostMapping
                public ResponseEntity<UserDto> create(
                        @Valid @RequestBody CreateUserRequest req,   // @Valid triggers validation
                        BindingResult result) {                       // optional — captures errors
                    if (result.hasErrors()) {
                        // Return custom error response
                        return ResponseEntity.badRequest().body(null);
                    }
                    return ResponseEntity.ok(userService.create(req));
                }
            }

            // Without BindingResult, Spring throws MethodArgumentNotValidException → 400
            // With RFC 9457 (spring.mvc.problemdetails.enabled=true):
            // {
            //   "type": "about:blank",
            //   "title": "Bad Request",
            //   "status": 400,
            //   "detail": "Invalid request content.",
            //   "errors": [{ "field": "email", "message": "Must be a valid email" }]
            // }
            """);

        System.out.println("--- @Validated on @ConfigurationProperties ---");
        System.out.println("""
            @Validated
            @ConfigurationProperties(prefix = "app.mail")
            public class MailProperties {
                @NotBlank String host;
                @Min(1) @Max(65535) int port;
                @Email String from;
                // Validated at startup — misconfiguration prevents app start
            }
            """);
    }
}
```

**How to run:** `java ValidationAutoConfigDemo.java` (requires `hibernate-validator` on classpath — included with `spring-boot-starter-validation`)

## 6. Walkthrough

- **`@NotBlank` vs `@NotNull` vs `@NotEmpty`** — `@NotNull` only checks for `null`. `@NotEmpty` fails on empty strings/collections but not blank ones. `@NotBlank` trims whitespace before checking — the strongest for strings. Use `@NotBlank` for string fields users fill in.
- **`phone = null` passes validation** — `@Pattern` (like all constraints except `@NotNull` and `@NotBlank`) treats `null` as valid by default. This allows optional fields. If `phone` is optional but must be formatted when provided, `@Pattern` on a nullable field is correct.
- **`Set<ConstraintViolation<T>>`** — the raw validation API Spring uses internally. Each violation has `getPropertyPath()` (the field name) and `getMessage()` (the constraint message). In a Spring controller, these are wrapped in a `BindingResult` with `FieldError` objects.
- **`spring.mvc.problemdetails.enabled=true`** — enables RFC 9457 "Problem Details" format for all Spring MVC errors including validation failures. The response includes structured JSON with `errors` array showing field-level details.
- **`@Validated` on `@ConfigurationProperties`** — validation runs at application startup. `@NotBlank` on `host` means the app refuses to start if `app.mail.host` is absent or empty. This is far better than discovering misconfiguration when the first email is sent.

## 7. Gotchas & takeaways

> **`@Valid` and `@Validated` are not interchangeable.** `@Valid` is the standard Jakarta annotation — use it on controller parameters to validate the request body. `@Validated` is Spring's annotation — use it on classes (service beans) to enable method-level validation via AOP proxy, and on `@ConfigurationProperties` to validate at startup. On controller parameters, both work the same.

> **Validation error messages are customisable via `messages.properties`.** The default message for `@NotBlank` is `"must not be blank"`. Override it: add `NotBlank=This field is required` to `messages.properties`. Use the constraint name (`NotBlank`, `Size`, `Email`) or the fully qualified key (`jakarta.validation.constraints.NotBlank.message`).

- Add `spring-boot-starter-validation` — validation is not included in `starter-web` by default.
- Use `@Valid` for cascaded validation on nested objects: `@Valid @NotNull Address address` inside a request class validates all `Address` constraints too.
- `@Validated(group = Create.class)` enables validation groups — different constraints for create vs update scenarios.
- Custom validators implement `ConstraintValidator<MyAnnotation, MyType>` — Spring Boot auto-detects them as beans.
- Actuator's `/actuator/health` uses Spring's `Validator` for `@ConfigurationProperties` validation at startup health check.
