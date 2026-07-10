---
card: spring-data
gi: 34
slug: domainclassconverter
title: "DomainClassConverter"
---

## 1. What it is

`DomainClassConverter` is a Spring `Converter` (registered into the application's `ConversionService` once `@EnableSpringDataWebSupport` is active) that converts an identifier's `String` representation into a fully-loaded entity — the mechanism the previous card's `@PathVariable Customer id` examples relied on. This card looks at the converter itself, independent of any specific controller: what it actually does, how it picks which repository to use, and how to invoke it directly through Spring's `ConversionService` to understand the mechanism at a lower level than the request-handling cards around it.

```java
// What @PathVariable Customer id does internally, roughly:
Customer customer = conversionService.convert("42", Customer.class);
// DomainClassConverter looked up CustomerRepository, called findById(42L)
```

## 2. Why & when

Every earlier card in this section (and the previous two web-support cards) used `DomainClassConverter` implicitly, through `@PathVariable`. Understanding the converter itself — as a `Converter<String, T>` plugged into the standard Spring type-conversion system — clarifies why it works everywhere a `String`-to-domain-type conversion is needed (not just `@PathVariable`, but `@RequestParam`, `@ModelAttribute` binding, and manual `ConversionService` use), and what determines whether it can resolve a given type at all.

Understanding `DomainClassConverter` at this level matters specifically when:

- You're debugging why a particular type *doesn't* resolve via `@PathVariable` — the converter only handles types with a genuine, discoverable Spring Data repository; a plain, non-entity class will never be handled by it.
- You want to use the same id-to-entity resolution outside of `@PathVariable` binding — in a `@RequestParam`, a custom `HandlerMethodArgumentResolver`, or directly through `ConversionService` in application code.
- You're customizing or replacing the default conversion behavior — perhaps needing a different lookup strategy (by a business key instead of the primary id) for a specific type.

## 3. Core concept

```
 DomainClassConverter<C extends FormattingConversionService> implements
     ConditionalGenericConverter

 matches(sourceType, targetType):
   -- returns true ONLY IF targetType has a discoverable Spring Data
      repository registered in the application's Repositories registry

 convert(source, sourceType, targetType):
   1. determine the repository for targetType (e.g. Customer -> CustomerRepository)
   2. convert the raw source String into the repository's ID type
      (using the SAME ConversionService, e.g. "42" -> 42L for a Long id)
   3. call repository.findById(convertedId)
   4. return the loaded entity (or throw / return empty, depending on
      whether the target parameter type itself is Optional<T> or a bare T)

 Registered automatically into the application's ConversionService
 as part of @EnableSpringDataWebSupport's configuration.
```

`DomainClassConverter` is a genuine `ConditionalGenericConverter` — Spring's type-conversion machinery consults it, among all other registered converters, for any conversion Spring attempts from a `String` to a type it doesn't already know how to handle another way.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DomainClassConverter is registered in the ConversionService and used for any String-to-entity conversion the framework attempts, not just PathVariable binding">
  <rect x="10" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">"42" (String)</text>
  <text x="110" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">from @PathVariable, @RequestParam, or manual use</text>

  <rect x="250" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DomainClassConverter</text>
  <text x="350" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">finds the repository, calls findById</text>

  <rect x="490" y="20" width="140" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="560" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Customer entity</text>
  <text x="560" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">fully loaded</text>

  <line x1="210" y1="47" x2="245" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="450" y1="47" x2="485" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The converter is a general-purpose plug-in to Spring's type-conversion system, not special-cased to `@PathVariable` binding.

## 5. Runnable example

The scenario: proving `DomainClassConverter`'s general applicability by invoking it directly through `ConversionService`, then through `@RequestParam` binding (not just `@PathVariable`), then confirming it correctly refuses to handle a type with no registered repository.

### Level 1 — Basic

Invoke the conversion directly through `ConversionService`, entirely outside of any HTTP request, to observe the converter's raw mechanism.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.convert.ConversionService;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class DomainConverterLevel1 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DomainConverterLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:domconv1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer saved = repo.save(new Customer("Ada Lovelace"));

        // Invoke the conversion DIRECTLY -- no HTTP request, no controller involved at all.
        ConversionService conversionService = ctx.getBean("mvcConversionService", ConversionService.class);
        Customer converted = conversionService.convert(String.valueOf(saved.getId()), Customer.class);

        System.out.println("directly converted 'idString' -> Customer: " + (converted != null ? converted.getName() : "null"));

        if (converted == null || !converted.getName().equals("Ada Lovelace"))
            throw new AssertionError("Expected DomainClassConverter to resolve the id string directly");
        System.out.println("DomainClassConverter worked via direct ConversionService.convert(), no HTTP involved -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-boot-starter-web`, and `com.h2database:h2` on the classpath, then `java DomainConverterLevel1.java` on JDK 17+.

`conversionService.convert(String.valueOf(saved.getId()), Customer.class)` invokes exactly the same underlying mechanism `@PathVariable Customer id` relies on, but called directly, with no HTTP request or controller in the picture at all — proving `DomainClassConverter` is a genuine, independently-usable piece of Spring's type-conversion infrastructure, not something magically tied to request handling specifically.

### Level 2 — Intermediate

Use the same conversion through `@RequestParam` (a query-string parameter, not a path variable), showing `DomainClassConverter` applies wherever Spring's argument-resolution encounters a `String`-to-entity conversion need.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.server.ServletWebServerApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class DomainConverterLevel2 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    private final CustomerRepository repo;
    public DomainConverterLevel2(CustomerRepository repo) { this.repo = repo; }

    // @RequestParam, NOT @PathVariable -- resolved from ?customer=<id> in the query string.
    @GetMapping("/lookup")
    public String lookup(@RequestParam("customer") Customer customer) {
        return "Resolved via @RequestParam: " + customer.getName();
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(DomainConverterLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:domconv2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        var saved = repo.save(new Customer("Grace Hopper"));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/lookup?customer=" + saved.getId())).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("response = " + response.body());

        if (!response.body().equals("Resolved via @RequestParam: Grace Hopper"))
            throw new AssertionError("Expected DomainClassConverter to resolve the @RequestParam too");
        System.out.println("DomainClassConverter also worked for @RequestParam, not just @PathVariable -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java DomainConverterLevel2.java`.

`@RequestParam("customer") Customer customer` needs the exact same `String`-to-`Customer` conversion `@PathVariable` relies on — Spring's argument resolution for `@RequestParam` also consults the `ConversionService`, and `DomainClassConverter` is registered there the same way regardless of which annotation triggered the conversion attempt. This confirms the converter's registration is general-purpose, not specific to path variables.

### Level 3 — Advanced

Attempt conversion for a type with **no** registered Spring Data repository, and confirm `DomainClassConverter` correctly declines to handle it (via its `matches(...)` check), falling through to a normal "no converter found" failure rather than attempting (and failing) a repository lookup that was never possible.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.convert.ConversionService;
import org.springframework.core.convert.ConverterNotFoundException;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class DomainConverterLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Customer() {}
        public Customer(String name) { this.name = name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {}

    // A PLAIN class with NO Spring Data repository anywhere -- DomainClassConverter
    // cannot and should not attempt to handle conversions targeting this type.
    public static class PlainNonEntityClass {
        private final String value;
        public PlainNonEntityClass(String value) { this.value = value; }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DomainConverterLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:domconv3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        var saved = repo.save(new Customer("Ada"));

        ConversionService conversionService = ctx.getBean("mvcConversionService", ConversionService.class);

        // This DOES work -- Customer has a repository.
        Customer converted = conversionService.convert(String.valueOf(saved.getId()), Customer.class);
        System.out.println("Customer conversion (has a repository) succeeded: " + (converted != null));

        // This should NOT be handled by DomainClassConverter (no repository for it) --
        // and since there's no OTHER registered converter for String -> PlainNonEntityClass either,
        // it should fail with a clear "no converter" error, not a confusing repository-lookup error.
        boolean threwConverterNotFound = false;
        try {
            conversionService.convert("some-value", PlainNonEntityClass.class);
        } catch (ConverterNotFoundException expected) {
            threwConverterNotFound = true;
            System.out.println("correctly failed with ConverterNotFoundException for a non-entity type");
        }

        if (converted == null) throw new AssertionError("Expected the Customer conversion to succeed");
        if (!threwConverterNotFound) throw new AssertionError("Expected a ConverterNotFoundException for a type with no repository");

        System.out.println("DomainClassConverter correctly declined a type with no Spring Data repository -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java DomainConverterLevel3.java`.

`PlainNonEntityClass` is a plain Java class with no corresponding Spring Data repository anywhere in the application — `DomainClassConverter`'s `matches(sourceType, targetType)` check (part of its `ConditionalGenericConverter` contract) returns `false` for this target type, meaning the converter never even attempts a repository lookup for it. Since no other registered converter can handle `String → PlainNonEntityClass` either, `ConversionService.convert(...)` fails with a standard `ConverterNotFoundException` — the same clean failure any unsupported conversion would produce, not a confusing error about a missing repository.

## 6. Walkthrough

Trace the failed conversion attempt in Level 3.

1. **`conversionService.convert("some-value", PlainNonEntityClass.class)`** is called — Spring's `ConversionService` needs to find a registered `Converter` (or `GenericConverter`) capable of producing a `PlainNonEntityClass` from a `String`.
2. **Candidate consultation**: among the registered converters, including `DomainClassConverter`, the `ConversionService` asks each candidate whether it can handle this specific source-type/target-type pair.
3. **`DomainClassConverter.matches(sourceType, targetType)`** is invoked with `targetType = PlainNonEntityClass`. Internally, this check consults Spring Data's `Repositories` registry (which tracks every entity type that has a discoverable repository) — `PlainNonEntityClass` isn't in it, since no repository was ever declared for it.
4. **`matches(...)` returns `false`**: `DomainClassConverter` declines this conversion — it never proceeds to attempt a repository lookup, since it correctly recognizes upfront that it has no repository to look up through.
5. **No other converter matches either**: since `PlainNonEntityClass` has no other registered conversion path from `String`, the `ConversionService` exhausts its candidates without finding a match.
6. **Failure**: `ConversionService.convert(...)` throws `ConverterNotFoundException` — a standard, well-understood Spring exception indicating no applicable converter exists, not a domain-specific or confusing error about repositories.
7. **Contrast with the `Customer` conversion**: earlier in the same method, `conversionService.convert(String.valueOf(saved.getId()), Customer.class)` succeeded, because `DomainClassConverter.matches(...)` correctly returned `true` for `Customer` (which does have `CustomerRepository`), then proceeded through the full lookup-and-load process.
8. **Verification**: the program confirms both outcomes — success for the entity type with a repository, and a clean, expected failure for the plain type without one — demonstrating the `matches(...)` guard is doing genuine, correct work, not just always attempting and sometimes failing a lookup.

```
 convert("42", Customer.class)              convert("some-value", PlainNonEntityClass.class)
        |                                              |
        v                                              v
 DomainClassConverter.matches(...)           DomainClassConverter.matches(...)
        |                                              |
   Customer HAS a repository                   PlainNonEntityClass has NO repository
        |                                              |
     matches = TRUE                                matches = FALSE
        |                                              |
   proceeds: findById(42L)                   declines -- no OTHER converter found either
        |                                              |
   returns loaded Customer                    ConverterNotFoundException
```

## 7. Gotchas & takeaways

> **Gotcha:** `DomainClassConverter`'s `matches(...)` check depends on Spring Data's `Repositories` registry already knowing about a given entity type's repository — if a repository interface hasn't been scanned and registered yet (an unusual timing issue, but possible with certain lazy-bootstrap or multi-context setups), a conversion that *should* eventually work can fail simply because the registry query happened too early. This is rare in typical single-context Spring Boot applications but worth knowing about when debugging conversion failures in more complex multi-module or multi-context setups.

- `DomainClassConverter` is a genuine, general-purpose `Converter` registered into the application's `ConversionService` by `@EnableSpringDataWebSupport` — not a special case hardwired only into `@PathVariable` handling.
- It applies anywhere Spring's type-conversion machinery is consulted for a `String`-to-entity conversion — `@PathVariable`, `@RequestParam`, and even direct, manual `ConversionService.convert(...)` calls in application code, as Level 1 demonstrated.
- The converter's `matches(...)` check correctly declines to handle any type without a discoverable Spring Data repository, letting such conversions fail with a standard, clear `ConverterNotFoundException` rather than attempting a lookup that could never succeed.
- Understanding the converter as a standard piece of Spring's type-conversion system (rather than MVC-specific magic) explains both its reach (anywhere `ConversionService` is consulted) and its limits (only for types with a genuine, registered repository).
