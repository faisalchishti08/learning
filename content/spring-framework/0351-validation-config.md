---
card: spring-framework
gi: 351
slug: validation-config
title: "Validation config"
---

## 1. What it is

Validation config controls which `Validator` implementation Spring MVC uses application-wide for `@Valid`/`@Validated` processing, and lets you register additional custom validators (implementing Spring's `org.springframework.validation.Validator` interface) alongside the standard JSR-380 (Bean Validation / Hibernate Validator) engine. You configure it via `WebMvcConfigurer.getValidator()` or by declaring a `LocalValidatorFactoryBean`.

```java
@Override
public Validator getValidator() {
    return new OptionalValidatorFactoryBean();   // the default, JSR-380-backed validator
}
```

## 2. Why & when

Spring Boot autoconfigures a sensible default validator (`LocalValidatorFactoryBean`, backed by Hibernate Validator) automatically the moment `spring-boot-starter-validation` is on the classpath — most applications never need to touch this configuration at all. You need explicit validation configuration when:

- You want to combine JSR-380 annotation-based validation (`@NotBlank`, `@Positive`) with Spring's own programmatic `Validator` interface for rules that don't fit cleanly into annotations (complex cross-object business rules, rules requiring a database lookup).
- You need a custom `MessageInterpolator` or `MessageSource` integration so validation messages are internationalized consistently with the rest of the application's text.
- You're integrating validation into a non-Boot Spring MVC application, where the default validator isn't autoconfigured and must be wired explicitly.

## 3. Core concept

```
Two validator styles, often used TOGETHER:

  JSR-380 (annotation-based):              Spring's Validator interface
  ─────────────────────────                (programmatic):
  class Product {                          class ProductBusinessRuleValidator
    @NotBlank String name;                     implements Validator {
    @Positive double price;                  boolean supports(Class<?> clazz)
  }                                           void validate(Object target, Errors errors)
  triggered by @Valid/@Validated             }
                                              registered via @InitBinder,
                                              or globally via getValidator()

LocalValidatorFactoryBean:
  the DEFAULT Validator implementation Spring Boot autoconfigures
  - implements BOTH javax/jakarta.validation.Validator (JSR-380 engine)
  - AND org.springframework.validation.Validator (Spring's interface)
  - so @Valid on a JSR-380-annotated class "just works" through it

getValidator() override:
  replaces/customizes the GLOBAL default validator bean
  used for ALL @Valid/@Validated processing application-wide
```

## 4. Diagram

<svg viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="200" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">LocalValidatorFactoryBean bridges JSR-380 and Spring's Validator</text>

  <rect x="20" y="50" width="220" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="72" text-anchor="middle" fill="#6db33f" font-size="10">@NotBlank / @Positive</text>
  <text x="130" y="90" text-anchor="middle" fill="#8b949e" font-size="9">JSR-380 annotations</text>

  <rect x="480" y="50" width="220" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="590" y="72" text-anchor="middle" fill="#79c0ff" font-size="10">Spring Validator interface</text>
  <text x="590" y="90" text-anchor="middle" fill="#8b949e" font-size="9">programmatic cross-field rules</text>

  <line x1="240" y1="80" x2="280" y2="80" stroke="#8b949e" marker-end="url(#a27)"/>
  <line x1="480" y1="80" x2="440" y2="80" stroke="#8b949e" marker-end="url(#a27)"/>

  <rect x="280" y="60" width="160" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="360" y="85" text-anchor="middle" fill="#e6edf3" font-size="10">LocalValidatorFactoryBean</text>

  <text x="360" y="140" text-anchor="middle" fill="#8b949e" font-size="10">both triggered by @Valid / @Validated on a handler parameter</text>

  <defs>
    <marker id="a27" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*One default validator bean bridges JSR-380 annotations and Spring's own programmatic `Validator` interface.*

## 5. Runnable example

### Level 1 — Basic

The default validation setup — no explicit configuration, relying entirely on Spring Boot's autoconfiguration:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

```java
// Product.java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public class Product {
    @NotBlank public String name;
    @Positive public double price;
}
```

```java
// ProductController.java
import jakarta.validation.Valid;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @PostMapping("/products")
    public String create(@Valid @RequestBody Product product, BindingResult result) {
        if (result.hasErrors()) return "Invalid: " + result.getFieldError().getDefaultMessage();
        return "Created: " + product.name;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"","price":-1}'
# Invalid: must not be blank
```

No `Validator` bean is declared anywhere — Spring Boot autoconfigures `LocalValidatorFactoryBean` automatically because `spring-boot-starter-validation` is present, and it's this default bean that `@Valid` delegates to.

### Level 2 — Intermediate

Adding a custom Spring `Validator` for a cross-field rule alongside the JSR-380 annotations, combined via `@InitBinder`:

```java
// ProductBusinessRuleValidator.java
import org.springframework.stereotype.Component;
import org.springframework.validation.Errors;
import org.springframework.validation.Validator;

@Component
public class ProductBusinessRuleValidator implements Validator {

    @Override
    public boolean supports(Class<?> clazz) { return Product.class.equals(clazz); }

    @Override
    public void validate(Object target, Errors errors) {
        Product p = (Product) target;
        if ("premium".equals(p.category) && p.price < 100) {
            errors.rejectValue("price", "price.tooLowForCategory", "Premium products must cost at least $100");
        }
    }
}
```

```java
// Product.java (extended)
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public class Product {
    @NotBlank public String name;
    @Positive public double price;
    public String category;
}
```

```java
// ProductController.java (extended)
import jakarta.validation.Valid;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    private final ProductBusinessRuleValidator businessRuleValidator;
    public ProductController(ProductBusinessRuleValidator businessRuleValidator) {
        this.businessRuleValidator = businessRuleValidator;
    }

    @InitBinder
    public void initBinder(WebDataBinder binder) {
        binder.addValidators(businessRuleValidator);   // layered ON TOP of the default JSR-380 validator
    }

    @PostMapping("/products")
    public String create(@Valid @RequestBody Product product, BindingResult result) {
        if (result.hasErrors()) return "Invalid: " + result.getFieldError().getDefaultMessage();
        return "Created: " + product.name;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"Drill","price":50,"category":"premium"}'
# Invalid: Premium products must cost at least $100

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"","price":50,"category":"premium"}'
# Invalid: must not be blank      <- JSR-380 checked FIRST, business rule not even reached
```

**What changed:** `binder.addValidators(businessRuleValidator)` layers the custom `Validator` onto the `WebDataBinder`'s validation chain, alongside the JSR-380 engine that's already wired in by default. Both run during the same `@Valid` processing pass — annotation-based checks and programmatic checks combine into one `BindingResult`.

### Level 3 — Advanced

Production concern: internationalized validation messages via a `MessageSource`, and explicitly configuring the global default validator to guarantee message resolution works consistently across both JSR-380 and custom validators:

```java
// WebConfig.java
import org.springframework.context.MessageSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.ReloadableResourceBundleMessageSource;
import org.springframework.validation.Validator;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Bean
    public MessageSource messageSource() {
        ReloadableResourceBundleMessageSource source = new ReloadableResourceBundleMessageSource();
        source.setBasename("classpath:messages");   // messages.properties, messages_fr.properties, ...
        source.setDefaultEncoding("UTF-8");
        return source;
    }

    @Bean
    @Override
    public Validator getValidator() {
        LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
        validator.setValidationMessageSource(messageSource());   // JSR-380 messages resolve via the SAME MessageSource
        return validator;
    }
}
```

`Product.java` (production version, message keys instead of literal text):
```java
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public class Product {
    @NotBlank(message = "{product.name.required}")
    public String name;

    @Positive(message = "{product.price.positive}")
    public double price;

    public String category;
}
```

`src/main/resources/messages.properties`:
```properties
product.name.required=Product name is required
product.price.positive=Price must be a positive number
```

`src/main/resources/messages_fr.properties`:
```properties
product.name.required=Le nom du produit est requis
product.price.positive=Le prix doit être un nombre positif
```

```java
// ProductController.java (production version) — UNCHANGED handler logic
import jakarta.validation.Valid;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @PostMapping("/products")
    public String create(@Valid @RequestBody Product product, BindingResult result) {
        if (result.hasErrors()) return "Invalid: " + result.getFieldError().getDefaultMessage();
        return "Created: " + product.name;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -H "Accept-Language: en" -d '{"name":"","price":50}'
# Invalid: Product name is required

curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -H "Accept-Language: fr" -d '{"name":"","price":50}'
# Invalid: Le nom du produit est requis
```

**What changed and why:**
- `{product.name.required}` (curly-brace syntax) tells Hibernate Validator to resolve the message text through a `MessageSource` lookup instead of using the literal annotation string — this is the standard way to internationalize JSR-380 validation messages.
- `setValidationMessageSource(messageSource())` explicitly wires the *same* `MessageSource` bean used elsewhere in the application (for `Formatter`s, Thymeleaf `#{...}` expressions, etc.) into the validator, guaranteeing one consistent message-resolution path rather than a separate, potentially divergent one for validation messages specifically.
- Overriding `getValidator()` and declaring it as a `@Bean` (rather than relying purely on autoconfiguration) is necessary here because the default autoconfigured validator doesn't know about the application's custom `MessageSource` unless explicitly told — this is the case where validation config genuinely needs to be hand-wired rather than left to Spring Boot's defaults.

## 6. Walkthrough

**Request: `POST /products` with `Accept-Language: fr` and body `{"name":"","price":50}` (Level 3 code).**

1. `DispatcherServlet` dispatches toward `create(Product, BindingResult)`. Before invoking the method, Spring must construct and validate the `@Valid @RequestBody Product` argument.
2. Jackson deserializes the JSON body into `Product{name="", price=50.0, category=null}`.
3. `@Valid` triggers validation via the globally configured `Validator` bean — the one explicitly declared by `getValidator()`, a `LocalValidatorFactoryBean` wired with the custom `messageSource`.
4. Hibernate Validator (the JSR-380 engine underneath) checks each constraint: `@NotBlank` on `name` — `""` fails. `@Positive` on `price` — `50.0` passes.
5. For the failed `@NotBlank` constraint, its `message` attribute is `"{product.name.required}"` — recognized as a message-source lookup key (due to the curly braces) rather than literal text.
6. The validator resolves the request's `Locale` (from `Accept-Language: fr` via the configured `LocaleResolver`) → `Locale.FRENCH`, then looks up `product.name.required` in the injected `messageSource` for that locale — finds `messages_fr.properties`, retrieves `"Le nom du produit est requis"`.
7. This resolved, localized message is attached to the `BindingResult` as a `FieldError` for the `name` field.
8. Because a `BindingResult` parameter immediately follows `@Valid`, the handler method executes (rather than an exception being thrown) with `result.hasErrors()` returning `true`.
9. `result.getFieldError().getDefaultMessage()` retrieves the already-resolved French message string.
10. Response:
    ```
    HTTP/1.1 200 OK
    Content-Type: text/plain;charset=UTF-8

    Invalid: Le nom du produit est requis
    ```

## 7. Gotchas & takeaways

> **Forgetting the curly braces around a JSR-380 message key (`message = "product.name.required"` instead of `message = "{product.name.required}"`) causes Hibernate Validator to treat the string as literal text, not a message-source lookup key.** The validation would still "work" (a message is still shown), but it would never be translated, silently defeating internationalization — a subtle, easy-to-miss mistake.

> **A custom `Validator` registered via `binder.addValidators(...)` inside `@InitBinder` is scoped to whatever controller declares that `@InitBinder` method** — not application-wide. For a business rule that should apply everywhere a given type is validated, register it globally instead, either by composing it into the primary `Validator` bean or via a `@ControllerAdvice`-scoped `@InitBinder`.

> **Overriding `getValidator()` replaces the *entire* default validator bean** — if your custom implementation doesn't correctly delegate to JSR-380 processing (as `LocalValidatorFactoryBean` does), you can accidentally disable all annotation-based validation application-wide while only intending to add message-source integration.

- Spring Boot autoconfigures `LocalValidatorFactoryBean` automatically once `spring-boot-starter-validation` is present — most applications need no explicit validation config at all.
- Custom Spring `Validator` implementations (for cross-field/business rules) layer onto the JSR-380 engine via `binder.addValidators(...)`, running in the same `@Valid` pass.
- Use curly-brace message keys (`{key.name}`) in JSR-380 `message` attributes for internationalized validation text, and wire the validator to the application's shared `MessageSource`.
- Overriding `getValidator()` is for genuinely custom validator wiring (like message-source integration) — most projects should leave the default autoconfiguration untouched.
