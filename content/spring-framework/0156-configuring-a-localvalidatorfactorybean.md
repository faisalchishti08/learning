---
card: spring-framework
gi: 156
slug: configuring-a-localvalidatorfactorybean
title: "Configuring a LocalValidatorFactoryBean"
---

## 1. What it is

`LocalValidatorFactoryBean` is Spring's central integration point for Jakarta Validation. It bootstraps a `ValidatorFactory` and exposes both the Jakarta `javax.validation.Validator` interface and Spring's own `org.springframework.validation.Validator` interface from a single bean. It also accepts a `MessageSource` for integrating constraint messages with Spring's message resolution.

```java
@Bean
public LocalValidatorFactoryBean validator() {
    LocalValidatorFactoryBean bean = new LocalValidatorFactoryBean();
    bean.setValidationMessageSource(messageSource()); // use Spring messages
    return bean;
}
```

## 2. Why & when

- **Unified API** — one bean that is injectable as `jakarta.validation.Validator`, `jakarta.validation.ValidatorFactory`, and `org.springframework.validation.Validator`.
- **Spring MessageSource integration** — interpolates constraint messages using `{key}` lookups in Spring's `MessageSource` rather than the default `ValidationMessages.properties`.
- **Custom `ConstraintValidator` injection** — when `LocalValidatorFactoryBean` is configured as the Spring-managed validator, custom `ConstraintValidator` implementations can have their own dependencies `@Autowired`.
- **`MethodValidationPostProcessor`** — must be wired with the same `LocalValidatorFactoryBean` to share message interpolation.

## 3. Core concept

Key configuration hooks on `LocalValidatorFactoryBean`:

| Method | Purpose |
|---|---|
| `setValidationMessageSource(MessageSource)` | Use Spring's `MessageSource` for `{key}` interpolation |
| `setConstraintValidatorFactory(ConstraintValidatorFactory)` | Custom factory (usually Spring-delegating for `@Autowired` in validators) |
| `setMappingLocations(Resource[])` | Extra XML constraint mapping files |
| `setProviderClass(Class)` | Force a specific provider (e.g., Hibernate Validator) |
| `afterPropertiesSet()` | Called by Spring container; call manually when outside Spring |

`SpringConstraintValidatorFactory` is the factory that delegates `ConstraintValidator` instantiation to the Spring `ApplicationContext`, enabling `@Autowired` fields inside validators.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- LocalValidatorFactoryBean box -->
  <rect x="200" y="20" width="300" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="350" y="44" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">LocalValidatorFactoryBean</text>
  <line x1="210" y1="52" x2="490" y2="52" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="350" y="68"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements Spring Validator</text>
  <text x="350" y="82"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements jakarta ValidatorFactory</text>
  <text x="350" y="96"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements jakarta Validator</text>
  <line x1="210" y1="106" x2="490" y2="106" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="350" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setValidationMessageSource → MessageSource</text>
  <text x="350" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setConstraintValidatorFactory → Spring beans</text>
  <text x="350" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setMappingLocations → XML constraints</text>

  <!-- Inputs -->
  <rect x="10" y="30"  width="155" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="87"  y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">MessageSource (messages.properties)</text>

  <rect x="10" y="75"  width="155" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="87" y="95"  fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SpringConstraintValidatorFactory</text>

  <rect x="10" y="120" width="155" height="30" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="87" y="140" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">XML constraint mapping</text>

  <!-- Outputs -->
  <rect x="535" y="30"  width="150" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="50"  fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Spring MVC / DataBinder</text>

  <rect x="535" y="75"  width="150" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="95"  fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">MethodValidationPostProcessor</text>

  <rect x="535" y="120" width="150" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Inject as jakarta Validator</text>

  <defs>
    <marker id="a156" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="167" y1="45"  x2="197" y2="80"  stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a156)"/>
  <line x1="167" y1="90"  x2="197" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a156)"/>
  <line x1="167" y1="135" x2="197" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a156)"/>
  <line x1="502" y1="80"  x2="532" y2="45"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a156)"/>
  <line x1="502" y1="100" x2="532" y2="90"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a156)"/>
  <line x1="502" y1="120" x2="532" y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a156)"/>
</svg>

One `LocalValidatorFactoryBean` bean satisfies three interfaces and integrates with Spring's message resolution and dependency injection.

## 5. Runnable example

### Level 1 — Basic

Configure `LocalValidatorFactoryBean` manually and validate using both APIs.

```java
// LocalValidatorFactoryBeanBasic.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import org.springframework.validation.*;
import org.springframework.validation.beanvalidation.*;
import java.util.*;

class UserDto {
    @NotBlank(message = "{user.name.blank}")
    String name;

    @Min(value = 18, message = "Age must be at least {value}")
    int age;

    UserDto(String name, int age) { this.name = name; this.age = age; }
    public String getName() { return name; }
    public int getAge()     { return age; }
}

public class LocalValidatorFactoryBeanBasic {
    public static void main(String[] args) {
        LocalValidatorFactoryBean lvfb = new LocalValidatorFactoryBean();
        lvfb.afterPropertiesSet(); // required outside Spring container

        UserDto user = new UserDto("", 15);

        // Path 1: Spring Validator API
        BeanPropertyBindingResult springResult = new BeanPropertyBindingResult(user, "user");
        lvfb.validate(user, springResult);
        System.out.println("=== Spring Validator ===");
        springResult.getFieldErrors()
            .forEach(e -> System.out.println("  [" + e.getField() + "] " + e.getDefaultMessage()));

        // Path 2: Jakarta Validator API
        Validator jakartaValidator = lvfb.getValidator();
        Set<ConstraintViolation<UserDto>> violations = jakartaValidator.validate(user);
        System.out.println("\n=== Jakarta Validator ===");
        violations.forEach(v ->
            System.out.println("  [" + v.getPropertyPath() + "] " + v.getMessage()));

        lvfb.destroy();
    }
}
```

How to run: `java LocalValidatorFactoryBeanBasic.java`

`lvfb.getValidator()` returns the underlying Jakarta `Validator`. `lvfb.validate(object, errors)` uses the Spring `Validator` SPI. Both point to the same underlying factory. The `{value}` expression in `@Min(message = "... {value}")` is resolved by Jakarta Validation's expression interpolator.

### Level 2 — Intermediate

Integrate `MessageSource` so `{user.name.blank}` resolves from Spring's `messages.properties`.

```java
// LocalValidatorFactoryBeanMessages.java
import jakarta.validation.constraints.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.support.*;
import org.springframework.validation.*;
import org.springframework.validation.beanvalidation.*;
import java.util.*;

class ArticleDto {
    @NotBlank(message = "{article.title.required}")
    String title;

    @Size(min = 50, max = 5000, message = "{article.body.size}")
    String body;

    @NotNull(message = "{article.author.required}")
    String author;

    ArticleDto(String title, String body, String author) {
        this.title = title; this.body = body; this.author = author;
    }
    public String getTitle()  { return title; }
    public String getBody()   { return body; }
    public String getAuthor() { return author; }
}

@Configuration
class MsgCfg {
    @Bean
    public MessageSource messageSource() {
        ResourceBundleMessageSource ms = new ResourceBundleMessageSource();
        ms.setDefaultEncoding("UTF-8");
        // In real code: ms.setBasename("messages")
        // For demo, we'll use StaticMessageSource
        return ms;
    }

    @Bean
    public LocalValidatorFactoryBean validator() {
        LocalValidatorFactoryBean bean = new LocalValidatorFactoryBean();

        // Use StaticMessageSource for the demo (no .properties file needed)
        StaticMessageSource sms = new StaticMessageSource();
        sms.addMessage("article.title.required", Locale.ENGLISH, "Article title cannot be empty");
        sms.addMessage("article.body.size",      Locale.ENGLISH, "Body must be between 50 and 5000 characters");
        sms.addMessage("article.author.required", Locale.ENGLISH, "Author is required");

        bean.setValidationMessageSource(sms);
        return bean;
    }
}

public class LocalValidatorFactoryBeanMessages {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MsgCfg.class);
        LocalValidatorFactoryBean validator = ctx.getBean(LocalValidatorFactoryBean.class);

        ArticleDto article = new ArticleDto("", "too short", null);
        BeanPropertyBindingResult errors = new BeanPropertyBindingResult(article, "article");
        validator.validate(article, errors);

        System.out.println("Violations: " + errors.getErrorCount());
        errors.getFieldErrors().forEach(e ->
            System.out.println("  [" + e.getField() + "] " + e.getDefaultMessage()));

        ctx.close();
    }
}
```

How to run: `java LocalValidatorFactoryBeanMessages.java`

`setValidationMessageSource(sms)` replaces the default `ValidationMessages.properties` lookup. Annotation messages like `{article.title.required}` are looked up in `sms` first; if not found, the literal string is returned.

### Level 3 — Advanced

`SpringConstraintValidatorFactory` enables `@Autowired` in `ConstraintValidator`; full wiring with `MethodValidationPostProcessor`.

```java
// LocalValidatorFactoryBeanAdvanced.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import java.lang.annotation.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.validation.annotation.*;
import org.springframework.validation.beanvalidation.*;
import java.util.*;

// Simulated repository — in real code this would be a @Repository
class UsernameRepository {
    private static final Set<String> TAKEN = Set.of("admin", "root", "superuser");
    public boolean exists(String username) { return TAKEN.contains(username.toLowerCase()); }
}

@Documented
@Constraint(validatedBy = UniqueUsernameValidator.class)
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
@interface UniqueUsername {
    String message() default "Username is already taken";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

class UniqueUsernameValidator implements ConstraintValidator<UniqueUsername, String> {
    @Autowired   // injected by SpringConstraintValidatorFactory
    UsernameRepository repo;

    @Override
    public boolean isValid(String value, ConstraintValidatorContext ctx) {
        if (value == null || value.isBlank()) return true; // let @NotBlank handle that
        return !repo.exists(value);
    }
}

class SignupRequest {
    @NotBlank @UniqueUsername String username;
    @Email @NotNull           String email;

    SignupRequest(String username, String email) {
        this.username = username; this.email = email;
    }
    public String getUsername() { return username; }
    public String getEmail()    { return email; }
}

@Configuration
class AdvancedValCfg {
    @Bean public UsernameRepository usernameRepository() { return new UsernameRepository(); }

    @Bean
    public LocalValidatorFactoryBean validator(AutowireCapableBeanFactory beanFactory) {
        LocalValidatorFactoryBean bean = new LocalValidatorFactoryBean();
        // Enable @Autowired in ConstraintValidator implementations
        bean.setConstraintValidatorFactory(new SpringConstraintValidatorFactory(beanFactory));
        return bean;
    }

    @Bean
    public MethodValidationPostProcessor mvpp(LocalValidatorFactoryBean validator) {
        MethodValidationPostProcessor p = new MethodValidationPostProcessor();
        p.setValidator(validator);
        return p;
    }
}

@Validated
class SignupService {
    public String register(@Valid SignupRequest req) {
        return "Registered: " + req.getUsername();
    }
}

@Configuration
@Import(AdvancedValCfg.class)
class AppCfg {
    @Bean public SignupService signupService() { return new SignupService(); }
}

public class LocalValidatorFactoryBeanAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        SignupService svc = ctx.getBean(SignupService.class);

        // Valid username
        try {
            System.out.println(svc.register(new SignupRequest("newuser", "new@example.com")));
        } catch (ConstraintViolationException e) {
            e.getConstraintViolations().forEach(v -> System.out.println("Error: " + v.getMessage()));
        }

        // Taken username
        try {
            System.out.println(svc.register(new SignupRequest("admin", "admin@example.com")));
        } catch (ConstraintViolationException e) {
            System.out.println("Caught: " + e.getConstraintViolations().size() + " violation(s)");
            e.getConstraintViolations().forEach(v ->
                System.out.println("  " + v.getPropertyPath() + ": " + v.getMessage()));
        }

        ctx.close();
    }
}
```

How to run: `java LocalValidatorFactoryBeanAdvanced.java`

`SpringConstraintValidatorFactory` intercepts `ConstraintValidator` instantiation and runs Spring's autowiring on each instance, allowing `@Autowired UsernameRepository repo` to be populated. Without this factory, the `repo` field would be `null`.

## 6. Walkthrough

Execution trace for `svc.register(new SignupRequest("admin", "..."))` in Level 3:

1. AOP proxy intercepts `register()`; `MethodValidationInterceptor` fires.
2. `validator.forExecutables().validateParameters(svc, method, [req])` is called.
3. `@Valid` on `req` triggers cascaded field validation.
4. `@UniqueUsername` on `username` → `UniqueUsernameValidator.isValid("admin", ctx)`.
5. `SpringConstraintValidatorFactory` has already `@Autowired` the validator with `UsernameRepository`.
6. `repo.exists("admin")` returns `true` → `isValid` returns `false`.
7. Violation created; `ConstraintViolationException` thrown before `register()` body runs.

## 7. Gotchas & takeaways

> `LocalValidatorFactoryBean` implements `DisposableBean`. If you create it manually (outside Spring context), call `bean.destroy()` at shutdown. Otherwise, the native validator factory leaks threads (Hibernate Validator uses background threads for constraint caching).

> `{key}` in annotation messages is looked up in the `MessageSource` provided via `setValidationMessageSource`. If the key is not found in `MessageSource`, Jakarta Validation falls back to `ValidationMessages.properties`. Do not mix both resolution strategies — pick one and be consistent.

- `SpringConstraintValidatorFactory` requires the `ConstraintValidator` class to be a Spring bean (e.g., annotated with `@Component`) OR be instantiatable by Spring's `AutowireCapableBeanFactory.createBean()`. Prototype beans are fine — each validation creates a new instance.
- In Spring Boot, `LocalValidatorFactoryBean` is auto-configured. Injecting `javax.validation.Validator` or `org.springframework.validation.Validator` in a `@Bean` method receives the same auto-configured instance.
- `LocalValidatorFactoryBean` is `SmartValidator` (extension of Spring's `Validator`) which also supports `validateValue(Class, String, Object, Errors, Object...)` for validating a value before binding it to an object.
