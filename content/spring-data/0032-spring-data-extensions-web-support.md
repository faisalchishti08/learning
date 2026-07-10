---
card: spring-data
gi: 32
slug: spring-data-extensions-web-support
title: "Spring Data extensions (web support)"
---

## 1. What it is

Spring Data's web support is a small set of Spring MVC integrations, all activated together by `@EnableSpringDataWebSupport`, that connect repository concepts directly to HTTP request handling: `DomainClassConverter` resolves a `@PathVariable` id straight into a loaded domain object, `PageableHandlerMethodArgumentResolver`/`SortHandlerMethodArgumentResolver` bind `Pageable`/`Sort` controller-method parameters directly from query-string parameters (`?page=0&size=20&sort=name,asc`), and `PagedResourcesAssembler` (covered in a later card in this section) builds HATEOAS-style paginated response bodies from a `Page<T>`. This card is the map of that feature set; the following cards go deeper on each piece.

```java
@EnableSpringDataWebSupport
public class WebConfig {}

@GetMapping("/customers/{id}")
Customer getCustomer(@PathVariable Customer id) { return id; } // DomainClassConverter resolved it

@GetMapping("/customers")
Page<Customer> list(Pageable pageable) { return repo.findAll(pageable); } // bound from ?page=&size=&sort=
```

## 2. Why & when

Building a REST API on top of Spring Data repositories involves a recurring pattern: a controller method receives an id from the URL and needs the matching entity; a list endpoint needs to accept pagination and sorting parameters from the query string and translate them into a `Pageable`. Hand-writing this translation in every controller method is exactly the kind of repetitive boilerplate Spring Data's web support exists to eliminate — once enabled, these bindings happen automatically, the same way `@RequestBody` automatically deserializes JSON into a Java object.

Reach for Spring Data's web support specifically when:

- You're building a Spring MVC (or Spring WebFlux, with the reactive equivalents) REST API directly on top of Spring Data repositories and want `Pageable`/`Sort` controller parameters populated automatically from standard query-string conventions, rather than parsing `page`/`size`/`sort` request parameters by hand in every endpoint.
- You want a `@PathVariable` id in a URL to resolve directly into the loaded entity, rather than writing `repo.findById(id).orElseThrow(...)` at the top of every controller method that takes an entity id.
- You're exposing a Spring Data-backed API with HATEOAS-style pagination links (`next`, `prev`, `self`) in the response body — `PagedResourcesAssembler` builds these automatically from a `Page<T>`.

Note: this is Spring Boot's default behavior once `spring-boot-starter-data-jpa` (or another Spring Data starter) and `spring-boot-starter-web` are both on the classpath — Spring Boot's auto-configuration typically enables Spring Data web support implicitly, the same way it implicitly enables `@EnableJpaRepositories`.

## 3. Core concept

```
 @EnableSpringDataWebSupport   (often implicitly active via Spring Boot auto-configuration)
        |
        +-- DomainClassConverter
        |     @PathVariable Customer id  -- URL id string --> loaded Customer entity
        |
        +-- PageableHandlerMethodArgumentResolver + SortHandlerMethodArgumentResolver
        |     Pageable/Sort controller parameters <-- ?page=0&size=20&sort=name,asc
        |
        +-- PagedResourcesAssembler  (covered in a later card)
              Page<T> --> HATEOAS-style paginated response with next/prev links
```

All three pieces are independently useful and independently addressable, but `@EnableSpringDataWebSupport` turns them all on together as one feature set.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableSpringDataWebSupport activates DomainClassConverter, Pageable/Sort resolvers, and PagedResourcesAssembler together">
  <rect x="220" y="15" width="200" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@EnableSpringDataWebSupport</text>

  <rect x="20" y="110" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DomainClassConverter</text>
  <text x="110" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">id string -&gt; loaded entity</text>

  <rect x="230" y="110" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Pageable/Sort resolvers</text>
  <text x="320" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">query params -&gt; Pageable/Sort</text>

  <rect x="440" y="110" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PagedResourcesAssembler</text>
  <text x="530" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Page&lt;T&gt; -&gt; HATEOAS response</text>

  <line x1="290" y1="60" x2="130" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="320" y1="60" x2="320" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="360" y1="60" x2="520" y2="105" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Three independent MVC integrations, all activated by one annotation.

## 5. Runnable example

The scenario: a small `Customer` REST API, evolving from a basic endpoint exercising `Pageable` binding, to `DomainClassConverter` resolving a path variable directly into an entity, to both working together in one realistic controller — using a real embedded server and real HTTP requests to make the request/response cycle concrete.

### Level 1 — Basic

Expose a paginated list endpoint and issue a real HTTP request with query-string paging parameters, confirming `Pageable` is bound automatically.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.server.ServletWebServerApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class WebSupportLevel1 {

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

    private final CustomerRepository repo;
    public WebSupportLevel1(CustomerRepository repo) { this.repo = repo; }

    @GetMapping("/customers")
    public Page<Customer> list(Pageable pageable) {
        return repo.findAll(pageable);
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(WebSupportLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:websupport1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0"); // 0 = pick a random free port

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        for (int i = 1; i <= 15; i++) repo.save(new Customer("Customer" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers?page=1&size=5"))
            .GET().build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("status = " + response.statusCode());
        System.out.println("body (truncated) = " + response.body().substring(0, Math.min(200, response.body().length())));

        boolean containsExpectedTotal = response.body().contains("\"totalElements\":15");
        if (response.statusCode() != 200) throw new AssertionError("Expected HTTP 200");
        if (!containsExpectedTotal) throw new AssertionError("Expected the response to report totalElements=15");
        System.out.println("Pageable was bound automatically from ?page=1&size=5 -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-boot-starter-web`, and `com.h2database:h2` on the classpath, then `java WebSupportLevel1.java` on JDK 17+.

`list(Pageable pageable)` needs no manual parsing of `page`/`size` request parameters — Spring Data's web support (implicitly enabled by Spring Boot auto-configuration once both the data and web starters are present) resolves them into a real `Pageable` before the controller method body even runs. The real HTTP `GET /customers?page=1&size=5` request confirms this end-to-end, receiving a real JSON response with the expected pagination metadata.

### Level 2 — Intermediate

Use `DomainClassConverter` to resolve a `@PathVariable` id directly into a loaded `Customer` entity, rather than manually calling `findById` in the controller.

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
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class WebSupportLevel2 {

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

    private final CustomerRepository repo;
    public WebSupportLevel2(CustomerRepository repo) { this.repo = repo; }

    // @PathVariable Customer -- DomainClassConverter resolves the URL's id segment
    // directly into a loaded Customer, calling repo.findById(...) internally.
    @GetMapping("/customers/{id}")
    public ResponseEntity<String> getByPathVariable(@PathVariable Customer id) {
        return ResponseEntity.ok("Found: " + id.getName());
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(WebSupportLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:websupport2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer saved = repo.save(new Customer("Ada Lovelace"));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers/" + saved.getId()))
            .GET().build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("status = " + response.statusCode() + ", body = " + response.body());

        if (response.statusCode() != 200) throw new AssertionError("Expected HTTP 200");
        if (!response.body().equals("Found: Ada Lovelace"))
            throw new AssertionError("Expected DomainClassConverter to have resolved the id into the loaded Customer");
        System.out.println("DomainClassConverter resolved the URL id directly into a Customer -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java WebSupportLevel2.java`.

`getByPathVariable(@PathVariable Customer id)` — despite the parameter's declared type being `Customer`, not `Long` — receives a fully-loaded `Customer` entity, not an id string. `DomainClassConverter` intercepts the raw path segment (`saved.getId()`, converted to a string in the URL), looks up `CustomerRepository` for the `Customer` type, and calls `findById(...)` on the caller's behalf, entirely transparently to the controller method body.

### Level 3 — Advanced

Combine paginated listing and path-variable resolution in one realistic controller, and confirm a missing id produces a proper `404` rather than a confusing error — showing `DomainClassConverter`'s behavior when the entity genuinely doesn't exist.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.server.ServletWebServerApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Optional;

@SpringBootApplication
@RestController
public class WebSupportLevel3 {

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

    private final CustomerRepository repo;
    public WebSupportLevel3(CustomerRepository repo) { this.repo = repo; }

    @GetMapping("/customers")
    public Page<Customer> list(Pageable pageable) { return repo.findAll(pageable); }

    // @PathVariable Optional<Customer> -- gracefully handles a NOT-FOUND id, instead
    // of DomainClassConverter throwing when the entity doesn't exist.
    @GetMapping("/customers/{id}")
    public String getByPathVariable(@PathVariable Optional<Customer> id) {
        return id.map(c -> "Found: " + c.getName()).orElse("NOT FOUND");
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(WebSupportLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:websupport3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        Customer saved = repo.save(new Customer("Grace Hopper"));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();

        HttpResponse<String> foundResponse = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers/" + saved.getId())).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        HttpResponse<String> notFoundResponse = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers/999999")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        HttpResponse<String> listResponse = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/customers?page=0&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("found: " + foundResponse.body());
        System.out.println("not found: " + notFoundResponse.body());
        System.out.println("list status: " + listResponse.statusCode());

        if (!foundResponse.body().equals("Found: Grace Hopper")) throw new AssertionError("Expected to find Grace Hopper");
        if (!notFoundResponse.body().equals("NOT FOUND")) throw new AssertionError("Expected a graceful NOT FOUND response");
        if (listResponse.statusCode() != 200) throw new AssertionError("Expected list endpoint to return 200");

        System.out.println("DomainClassConverter + Pageable resolver worked together, including a graceful not-found case -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java WebSupportLevel3.java`.

`@PathVariable Optional<Customer> id` is `DomainClassConverter`'s graceful-absence form — when the id in the URL doesn't correspond to any existing `Customer`, the resolved `Optional` is empty rather than the request failing with an unhandled exception, letting the controller method decide how to respond (here, a plain `"NOT FOUND"` string; a real API would typically return an HTTP 404 status instead). The list endpoint from Level 1 and the path-variable endpoint from Level 2 coexist in the same controller, both benefiting from Spring Data's web support simultaneously.

## 6. Walkthrough

Trace the `GET /customers/999999` request (the not-found case).

1. **Request arrives**: Spring MVC's `DispatcherServlet` matches the URL to `getByPathVariable`, extracting `"999999"` as the raw `{id}` path segment.
2. **Argument resolution**: before invoking the controller method, Spring MVC needs to produce a value for the `Optional<Customer> id` parameter. Because Spring Data's web support is active, `DomainClassConverter` is registered as a converter capable of producing a `Customer` (or `Optional<Customer>`) from a `String` source.
3. **Repository lookup**: `DomainClassConverter` determines `Customer`'s repository (`CustomerRepository`, found via the same Spring Data infrastructure that manages all repositories in this application) and calls `repo.findById(999999L)`.
4. **Lookup fails**: no `Customer` with id `999999` exists, so `findById` returns `Optional.empty()`.
5. **Parameter binding completes**: because the controller method's parameter type is `Optional<Customer>` (not a bare `Customer`), `DomainClassConverter` passes this empty `Optional` straight through as the resolved argument value, rather than raising an error.
6. **Controller method executes**: `getByPathVariable` receives `id = Optional.empty()`, and its `.map(...).orElse("NOT FOUND")` logic produces the string `"NOT FOUND"`.
7. **Response sent**: Spring MVC serializes this string as the HTTP response body, with a `200 OK` status (since no exception was thrown — the method completed normally, just with a "not found" *value*, not a "not found" *HTTP status*; a production API would typically also set the response status explicitly).
8. **Verification**: the test client receives and checks this exact string, confirming the whole request/response/argument-resolution cycle behaved as `DomainClassConverter`'s graceful-`Optional` design intends.

```
 GET /customers/999999
        |
        v
 DomainClassConverter: "999999" --> repo.findById(999999L) --> Optional.empty()
        |
        v
 controller parameter: Optional<Customer> id = Optional.empty()   (no exception thrown)
        |
        v
 id.map(...).orElse("NOT FOUND")  -->  response body: "NOT FOUND"
```

## 7. Gotchas & takeaways

> **Gotcha:** using a bare `@PathVariable Customer id` (as in Level 2), rather than `Optional<Customer>`, means `DomainClassConverter` throws when the id doesn't resolve to an entity — by default this typically surfaces to the client as an HTTP 400 (bad request) or 500, not necessarily the more RESTfully-correct 404, and the exact status depends on how the application's exception handling is configured. For endpoints where a missing id is an expected, normal case (not a client error), prefer the `Optional<Customer>` parameter form and handle the empty case explicitly, as Level 3 does.

- Spring Data's web support (`@EnableSpringDataWebSupport`, often implicitly active via Spring Boot auto-configuration) bundles three MVC integrations: `DomainClassConverter` (path variable to entity), `Pageable`/`Sort` argument resolvers (query parameters to paging/sorting objects), and `PagedResourcesAssembler` (covered next).
- `Pageable pageable` as a controller method parameter is automatically populated from `?page=`, `?size=`, and `?sort=` query parameters — no manual parsing needed in the controller body.
- `@PathVariable EntityType id` resolves a URL path segment directly into a loaded entity via the matching repository's `findById` — use the `Optional<EntityType>` form when a missing id should be handled gracefully rather than causing an error.
- These integrations only need real HTTP request/response testing (as this card's examples used) to observe fully, since they operate at the boundary between raw HTTP input and typed Java method parameters — unit-testing a controller method in isolation, without going through MVC's actual request dispatch, would bypass this binding machinery entirely.
