---
card: spring-framework
gi: 157
slug: spring-mvc-validation-integration
title: "Spring MVC validation integration"
---

## 1. What it is

Spring MVC validation integration connects Jakarta Validation and Spring's own `Validator` SPI to the MVC request-handling pipeline. When `@Valid` or `@Validated` is placed on a `@RequestBody`, `@ModelAttribute`, or method parameter, Spring MVC validates the bound object before the controller method body executes. Validation errors land in a `BindingResult` (if declared as the next parameter) or throw `MethodArgumentNotValidException`.

```java
@PostMapping("/orders")
public ResponseEntity<OrderResponse> createOrder(
        @RequestBody @Valid CreateOrderRequest body,
        BindingResult errors) {
    if (errors.hasErrors()) return ResponseEntity.badRequest().build();
    return ResponseEntity.ok(orderService.create(body));
}
```

## 2. Why & when

- **Controller-layer safety net** — validates incoming HTTP requests before business logic, providing structured 400 error responses.
- **`@ModelAttribute` for form binding** — HTML form data bound to a command object is validated before the handler runs.
- **`@RequestParam` / `@PathVariable`** — scalar parameters annotated with `@NotBlank`, `@Min`, etc., are validated by `MethodValidationPostProcessor` (requires `@Validated` on the controller class).
- **Global error handling** — use `@ExceptionHandler(MethodArgumentNotValidException.class)` in a `@ControllerAdvice` to return structured JSON error bodies.

## 3. Core concept

Two distinct validation paths in Spring MVC:

| Scenario | Annotation | Error mechanism |
|---|---|---|
| `@RequestBody` / `@ModelAttribute` | `@Valid` or `@Validated` on parameter | `MethodArgumentNotValidException` or `BindingResult` |
| `@RequestParam` / `@PathVariable` scalars | `@NotBlank` etc. on parameter; `@Validated` on controller | `ConstraintViolationException` |

`WebMvcConfigurationSupport` wires `LocalValidatorFactoryBean` as the default `Validator` and creates `DefaultFormattingConversionService` automatically. Both are shared across the MVC stack.

Request binding flow for `@RequestBody @Valid`:
1. `HttpMessageConverter` deserializes JSON → POJO.
2. `SmartValidator` validates POJO against Jakarta constraints.
3. If errors: populate `BindingResult` or throw `MethodArgumentNotValidException`.
4. Controller method executes.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- HTTP Request -->
  <rect x="10" y="30" width="100" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="60" y="48" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">HTTP POST</text>
  <text x="60" y="62" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">JSON body</text>

  <!-- DispatcherServlet -->
  <rect x="145" y="20" width="140" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="215" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <text x="215" y="57" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">HandlerMethodArgumentResolver</text>
  <text x="215" y="70" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">deserialize + bind</text>

  <!-- Validator -->
  <rect x="318" y="20" width="150" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="393" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">LocalValidator</text>
  <text x="393" y="57" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">FactoryBean</text>
  <text x="393" y="70" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">validate(object, errors)</text>

  <!-- Controller -->
  <rect x="500" y="20" width="190" height="140" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="42"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@RestController</text>
  <line x1="512" y1="52" x2="680" y2="52" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="595" y="68"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Valid body → BindingResult</text>
  <text x="595" y="81"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">if (errors.hasErrors()) 400</text>
  <text x="595" y="99"  fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">or: no BindingResult →</text>
  <text x="595" y="112" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">MethodArgumentNotValidException</text>
  <text x="595" y="130" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ @ControllerAdvice</text>
  <text x="595" y="143" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ 400 body with field errors</text>

  <!-- Paths -->
  <rect x="145" y="100" width="325" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="307" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@RequestParam @NotBlank → ConstraintViolationException (controller must be @Validated)</text>

  <defs>
    <marker id="a157" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="112" y1="50" x2="142" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a157)"/>
  <line x1="287" y1="50" x2="315" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a157)"/>
  <line x1="470" y1="50" x2="497" y2="50" stroke="#6db33f" stroke-width="2" marker-end="url(#a157)"/>
</svg>

`@Valid` on `@RequestBody` triggers validation after deserialization; errors reach the controller via `BindingResult` or exception.

## 5. Runnable example

### Level 1 — Basic

Controller with `@RequestBody @Valid`, explicit `BindingResult` handling.

```java
// SpringMvcValidationBasic.java
import jakarta.validation.constraints.*;
import org.springframework.context.annotation.*;
import org.springframework.http.*;
import org.springframework.validation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;

class CreateProductRequest {
    @NotBlank(message = "name is required")
    public String name;

    @DecimalMin(value = "0.01", message = "price must be >= 0.01")
    public double price;

    @Min(value = 0, message = "stock must be >= 0")
    public int stock;
}

class ValidationErrorResponse {
    public int status;
    public java.util.Map<String, String> errors;

    ValidationErrorResponse(int status, java.util.Map<String, String> fieldErrors) {
        this.status = status;
        this.errors = fieldErrors;
    }
}

@RestController
@RequestMapping("/products")
class ProductController {
    @PostMapping
    public ResponseEntity<?> create(@RequestBody @Valid CreateProductRequest req,
                                    BindingResult bindingResult) {
        if (bindingResult.hasErrors()) {
            var fieldErrors = new java.util.LinkedHashMap<String, String>();
            bindingResult.getFieldErrors().forEach(e ->
                fieldErrors.put(e.getField(), e.getDefaultMessage()));
            return ResponseEntity.badRequest()
                .body(new ValidationErrorResponse(400, fieldErrors));
        }
        return ResponseEntity.ok("Created: " + req.name);
    }
}

@Configuration
@EnableWebMvc
class WebCfg implements WebMvcConfigurer {
    // LocalValidatorFactoryBean auto-registered by @EnableWebMvc / Spring Boot
}

// Note: run this with a Spring Boot or embedded Tomcat setup.
// Demonstrated here as configuration only — actual HTTP requires an embedded server.
public class SpringMvcValidationBasic {
    public static void main(String[] args) {
        // Standalone demo: simulate validation flow without HTTP
        var factory = new org.springframework.validation.beanvalidation.LocalValidatorFactoryBean();
        factory.afterPropertiesSet();

        CreateProductRequest req = new CreateProductRequest();
        req.name = "";
        req.price = -1.0;
        req.stock = -5;

        BeanPropertyBindingResult errors = new BeanPropertyBindingResult(req, "product");
        factory.validate(req, errors);

        System.out.println("Errors: " + errors.getErrorCount());
        errors.getFieldErrors().forEach(e ->
            System.out.println("  [" + e.getField() + "] " + e.getDefaultMessage()));

        factory.destroy();
    }
}
```

How to run: `java SpringMvcValidationBasic.java`

When `@Valid` is placed before `BindingResult`, Spring does NOT throw an exception on validation failure — errors are stored in `BindingResult`. If `BindingResult` is absent, Spring throws `MethodArgumentNotValidException` automatically.

### Level 2 — Intermediate

`@ControllerAdvice` handling `MethodArgumentNotValidException`; structured error response.

```java
// SpringMvcValidationIntermediate.java
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.validation.*;
import org.springframework.web.bind.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.stream.*;

// DTO
class OrderRequest {
    @NotBlank(message = "customerId required")
    public String customerId;

    @NotEmpty(message = "items list must not be empty")
    public List<@NotBlank(message = "each item code must not be blank") String> items;

    @Min(value = 1, message = "quantity must be at least 1")
    public int quantity;
}

// Error response structure
record ApiError(int status, String message, Map<String, List<String>> fieldErrors) {}

// Global handler
@ControllerAdvice
class GlobalExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex) {
        Map<String, List<String>> fieldErrors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .collect(Collectors.groupingBy(
                FieldError::getField,
                Collectors.mapping(FieldError::getDefaultMessage, Collectors.toList())));

        return ResponseEntity
            .badRequest()
            .body(new ApiError(400, "Validation failed", fieldErrors));
    }
}

@RestController
@RequestMapping("/orders")
class OrderController {
    // No BindingResult — let MethodArgumentNotValidException propagate to @ControllerAdvice
    @PostMapping
    public ResponseEntity<String> placeOrder(@RequestBody @Valid OrderRequest order) {
        return ResponseEntity.ok("Order placed for " + order.customerId);
    }
}

// Standalone demo
public class SpringMvcValidationIntermediate {
    public static void main(String[] args) {
        var factory = new org.springframework.validation.beanvalidation.LocalValidatorFactoryBean();
        factory.afterPropertiesSet();

        OrderRequest req = new OrderRequest();
        req.customerId = "";
        req.items = List.of();
        req.quantity = 0;

        BeanPropertyBindingResult errors = new BeanPropertyBindingResult(req, "order");
        factory.validate(req, errors);

        // Simulate what @ControllerAdvice does
        Map<String, List<String>> fieldErrors = errors.getFieldErrors()
            .stream()
            .collect(Collectors.groupingBy(
                FieldError::getField,
                Collectors.mapping(FieldError::getDefaultMessage, Collectors.toList())));

        System.out.println("Field errors: " + fieldErrors);

        factory.destroy();
    }
}
```

How to run: `java SpringMvcValidationIntermediate.java`

Without `BindingResult` next to `@Valid`, Spring throws `MethodArgumentNotValidException`. The `@ControllerAdvice` extracts field errors and returns a structured 400 body. `Collectors.groupingBy(FieldError::getField, ...)` accumulates multiple errors per field into a list.

### Level 3 — Advanced

`@RequestParam` and `@PathVariable` scalar validation via `@Validated` on the controller; `ConstraintViolationException` handling.

```java
// SpringMvcValidationAdvanced.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.validation.annotation.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;
import java.util.stream.*;

@Validated  // enables MethodValidationPostProcessor on controller
@RestController
@RequestMapping("/search")
class SearchController {
    @GetMapping("/products")
    public ResponseEntity<List<String>> search(
            @RequestParam @NotBlank(message = "query must not be blank") String q,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return ResponseEntity.ok(List.of("result1", "result2"));
    }

    @GetMapping("/products/{id}")
    public ResponseEntity<String> getById(
            @PathVariable @Min(value = 1, message = "id must be positive") long id) {
        return ResponseEntity.ok("product-" + id);
    }
}

@ControllerAdvice
class ScalarValidationHandler {
    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<Map<String, Object>> handleScalarViolation(
            ConstraintViolationException ex) {
        List<Map<String, String>> violations = ex.getConstraintViolations()
            .stream()
            .map(v -> Map.of(
                "param",   v.getPropertyPath().toString(),
                "message", v.getMessage(),
                "value",   String.valueOf(v.getInvalidValue())))
            .collect(Collectors.toList());

        return ResponseEntity.badRequest()
            .body(Map.of("status", 400, "violations", violations));
    }
}

// Standalone demo — simulate what MVC does for @RequestParam validation
public class SpringMvcValidationAdvanced {
    public static void main(String[] args) {
        var factory = new org.springframework.validation.beanvalidation.LocalValidatorFactoryBean();
        factory.afterPropertiesSet();

        // Simulate: q="", page=-1, size=200
        // In MVC, these params arrive as strings and are converted before validation
        jakarta.validation.Validator v = factory.getValidator();

        // We can't easily simulate @RequestParam validation outside MVC, so show the concept:
        System.out.println("In Spring MVC:");
        System.out.println("  @Validated on controller + @Min/@Max on @RequestParam");
        System.out.println("  → MethodValidationInterceptor fires");
        System.out.println("  → ConstraintViolationException on bad params");
        System.out.println("  → @ExceptionHandler(ConstraintViolationException.class) → 400 JSON");
        System.out.println("\nKey difference:");
        System.out.println("  @RequestBody @Valid → MethodArgumentNotValidException");
        System.out.println("  @RequestParam @NotNull (+ @Validated on class) → ConstraintViolationException");

        factory.destroy();
    }
}
```

How to run: `java SpringMvcValidationAdvanced.java`

`@Validated` on the controller class enables `MethodValidationPostProcessor` interception. `@RequestParam @NotBlank` triggers `ConstraintViolationException`, not `MethodArgumentNotValidException` — these are separate exception types requiring separate `@ExceptionHandler` methods.

## 6. Walkthrough

Execution trace for a POST to `/orders` with an empty `customerId` (Level 2):

1. HTTP POST arrives; `DispatcherServlet` selects `OrderController.placeOrder`.
2. `RequestResponseBodyMethodProcessor` reads JSON body via `MappingJackson2HttpMessageConverter`.
3. `SmartValidator` (backed by `LocalValidatorFactoryBean`) validates `OrderRequest`.
4. `customerId = ""` fails `@NotBlank`, `items = []` fails `@NotEmpty`.
5. No `BindingResult` parameter → Spring wraps violations in `MethodArgumentNotValidException`.
6. `DispatcherServlet` catches exception; `ExceptionHandlerExceptionResolver` finds `GlobalExceptionHandler.handleValidation`.
7. Handler extracts `FieldError`s from `ex.getBindingResult()`, returns `ApiError` as JSON with status 400.

## 7. Gotchas & takeaways

> **Two different exceptions, two different handlers.** `@RequestBody @Valid` → `MethodArgumentNotValidException` (contains a `BindingResult`). `@RequestParam @NotBlank` (with `@Validated` on class) → `ConstraintViolationException` (contains `ConstraintViolation` set). You need separate `@ExceptionHandler` methods for each.

> The `BindingResult` parameter MUST immediately follow the `@Valid`-annotated parameter. `create(@Valid Foo foo, String other, BindingResult errors)` does NOT work — `errors` is not adjacent to `foo`.

- `@Validated(Group.class)` on a `@RequestBody` parameter runs only constraints in that group. Useful for differentiating create vs. update endpoints sharing the same DTO class.
- `@Valid` on a `@ModelAttribute` nested object field does not work for HTML form binding unless the nested field is also annotated with `@Valid`. Spring does not auto-cascade `@Valid` for multi-level nesting in `@ModelAttribute` binding.
- Spring Boot's `DefaultHandlerExceptionResolver` returns empty 400 bodies for `MethodArgumentNotValidException`. For structured error bodies, always add a custom `@ExceptionHandler`.
- `@PathVariable` `@Min` validation requires `@Validated` on the class AND `MethodValidationPostProcessor` to be registered. The latter is auto-configured in Spring Boot; in plain Spring MVC, add it as a `@Bean`.
