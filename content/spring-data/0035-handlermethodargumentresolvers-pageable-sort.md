---
card: spring-data
gi: 35
slug: handlermethodargumentresolvers-pageable-sort
title: "HandlerMethodArgumentResolvers (Pageable/Sort)"
---

## 1. What it is

`PageableHandlerMethodArgumentResolver` and `SortHandlerMethodArgumentResolver` are the specific Spring MVC `HandlerMethodArgumentResolver` implementations behind every `Pageable pageable`/`Sort sort` controller parameter used throughout this section's web-support cards. This card goes deeper into their configuration surface: default page size, a maximum page size cap (protecting against a client requesting an unreasonably large page), one-based-indexing support, and using `@Qualifier` to support *multiple* `Pageable` parameters on a single controller method.

```java
@GetMapping("/products")
Page<Product> list(
    @PageableDefault(size = 20, sort = "name") Pageable pageable) { ... }
```

## 2. Why & when

The default resolver behavior (zero-based page numbers, no size cap, a default size if none is specified) works for many APIs unchanged, but real production concerns push against those defaults regularly: a client requesting `?size=1000000` without any server-side cap can cause a genuinely damaging query; some client conventions (and most non-technical users) expect page numbers starting at 1, not 0; and some endpoints genuinely need two independent paginated result sets in one response.

Reach for these configuration options specifically when:

- You need to cap the maximum page size a client can request, protecting the database and application from an accidentally or maliciously huge `?size=` value.
- You want `@PageableDefault` to specify sensible defaults (a default sort order, a default page size) for an endpoint when the client's request omits paging parameters entirely.
- Your API needs one-based page numbering (`?page=1` meaning the first page) to match a specific client or UI convention, rather than Spring Data's default zero-based numbering.
- You need two distinct paginated inputs on the same controller method — `@Qualifier` differentiates them by prefixing each one's query parameters.

## 3. Core concept

```
 @PageableDefault(size = 20, page = 0, sort = "name", direction = Sort.Direction.ASC)
   -- supplies DEFAULTS used when the client's request omits page/size/sort entirely

 spring.data.web.pageable.max-page-size (application property)
   -- caps the LARGEST size a client can request, regardless of what they ask for
   -- (a request for size=999999 gets silently CAPPED to this maximum, not rejected)

 spring.data.web.pageable.one-indexed-parameters=true (application property)
   -- makes ?page=1 mean the FIRST page (client-facing), while internally
      Spring Data's own Pageable/Page objects remain zero-indexed as always

 @Qualifier("primary")/@Qualifier("secondary") on TWO Pageable parameters
   -- differentiates their query parameters: primary_page/primary_size vs
      secondary_page/secondary_size, letting one endpoint paginate two
      independent result sets simultaneously
```

These settings tune the resolver's behavior globally (application properties) or per-parameter (`@PageableDefault`, `@Qualifier`) without requiring any change to how `Pageable`/`Sort` are actually used once resolved.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="max-page-size caps requested size, PageableDefault supplies defaults, and Qualifier differentiates two Pageable parameters on one method">
  <rect x="10" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">max-page-size</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">caps huge ?size= requests</text>

  <rect x="230" y="20" width="190" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@PageableDefault</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">defaults when params omitted</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Qualifier x2</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TWO Pageable params, one method</text>
</svg>

Three independent knobs, each solving a distinct real-world pagination-request concern.

## 5. Runnable example

The scenario: a product search endpoint, evolving from `max-page-size` capping an oversized request, to `@PageableDefault` supplying sensible defaults, to two independent `Pageable` parameters differentiated via `@Qualifier`.

### Level 1 — Basic

Configure `spring.data.web.pageable.max-page-size` and confirm a client requesting an oversized page is silently capped, not rejected.

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
public class ArgResolverLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    private final ProductRepository repo;
    public ArgResolverLevel1(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public Page<Product> list(Pageable pageable) { return repo.findAll(pageable); }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(ArgResolverLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:argresolver1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0",
            "--spring.data.web.pageable.max-page-size=50"); // cap requested size at 50

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 60; i++) repo.save(new Product("Product" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        // Client asks for size=1000 -- WAY over the configured max of 50.
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products?page=0&size=1000")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("response snippet: " + response.body().substring(0, Math.min(150, response.body().length())));

        boolean cappedTo50 = response.body().contains("\"size\":50");
        if (response.statusCode() != 200) throw new AssertionError("Expected HTTP 200, not a rejection");
        if (!cappedTo50) throw new AssertionError("Expected the requested size=1000 to be silently capped to 50");
        System.out.println("max-page-size silently capped an oversized ?size= request -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-boot-starter-web`, and `com.h2database:h2` on the classpath, then `java ArgResolverLevel1.java` on JDK 17+.

Even though the client requests `?size=1000`, the response reports `"size":50` — `spring.data.web.pageable.max-page-size=50` caps whatever the resolver produces at that ceiling, protecting the application from an oversized request without needing the controller to validate the size manually or reject the request outright.

### Level 2 — Intermediate

Use `@PageableDefault` to supply a default size and sort order, applied only when the client's request omits those parameters entirely.

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
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class ArgResolverLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private double price;
        protected Product() {}
        public Product(String name, double price) { this.name = name; this.price = price; }
        public String getName() { return name; }
        public double getPrice() { return price; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    private final ProductRepository repo;
    public ArgResolverLevel2(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public Page<Product> list(
        @PageableDefault(size = 5, sort = "price", direction = Sort.Direction.DESC) Pageable pageable) {
        return repo.findAll(pageable);
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(ArgResolverLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:argresolver2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Cheap", 5.0));
        repo.save(new Product("Mid", 25.0));
        repo.save(new Product("Expensive", 50.0));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        // NO query parameters at all -- @PageableDefault's values should apply.
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("response (no query params, relying on @PageableDefault): " + response.body());

        boolean firstIsExpensive = response.body().indexOf("Expensive") < response.body().indexOf("Cheap");
        boolean sizeFive = response.body().contains("\"size\":5");

        if (!firstIsExpensive) throw new AssertionError("Expected @PageableDefault's sort=price DESC to apply with no explicit sort param");
        if (!sizeFive) throw new AssertionError("Expected @PageableDefault's size=5 to apply with no explicit size param");
        System.out.println("@PageableDefault applied its defaults when the client supplied no paging parameters -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java ArgResolverLevel2.java`.

Requesting `/products` with zero query parameters at all still produces a properly sorted, sized page — `@PageableDefault(size = 5, sort = "price", direction = Sort.Direction.DESC)` supplies those values only in the absence of client-supplied `page`/`size`/`sort` parameters; a client that *does* supply its own would override these defaults exactly as expected.

### Level 3 — Advanced

Support two independent, simultaneously-paginated result sets on one controller method using `@Qualifier`, differentiated by prefixed query parameters.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.annotation.Qualifier;
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
public class ArgResolverLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
    }

    @Entity
    public static class Review {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String text;
        protected Review() {}
        public Review(String text) { this.text = text; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}
    public interface ReviewRepository extends JpaRepository<Review, Long> {}

    private final ProductRepository productRepo;
    private final ReviewRepository reviewRepo;
    public ArgResolverLevel3(ProductRepository productRepo, ReviewRepository reviewRepo) {
        this.productRepo = productRepo; this.reviewRepo = reviewRepo;
    }

    // TWO Pageable parameters on ONE method, distinguished by @Qualifier prefixes:
    // ?products_page=&products_size=  and  ?reviews_page=&reviews_size=
    @GetMapping("/dashboard")
    public String dashboard(
        @Qualifier("products") Pageable productsPageable,
        @Qualifier("reviews") Pageable reviewsPageable) {
        Page<Product> products = productRepo.findAll(productsPageable);
        Page<Review> reviews = reviewRepo.findAll(reviewsPageable);
        return "products page size=" + products.getSize() + ", reviews page size=" + reviews.getSize();
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(ArgResolverLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:argresolver3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository productRepo = ctx.getBean(ProductRepository.class);
        ReviewRepository reviewRepo = ctx.getBean(ReviewRepository.class);
        for (int i = 0; i < 10; i++) productRepo.save(new Product("Product" + i));
        for (int i = 0; i < 10; i++) reviewRepo.save(new Review("Review" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port
                + "/dashboard?products_page=0&products_size=3&reviews_page=0&reviews_size=7")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("response = " + response.body());

        if (!response.body().equals("products page size=3, reviews page size=7"))
            throw new AssertionError("Expected the two @Qualifier-differentiated Pageable params to resolve independently");
        System.out.println("Two independent Pageable parameters on one method, via @Qualifier -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java ArgResolverLevel3.java`.

`@Qualifier("products")` and `@Qualifier("reviews")` on the two `Pageable` parameters tell `PageableHandlerMethodArgumentResolver` to look for query parameters prefixed accordingly — `products_page`/`products_size` for the first, `reviews_page`/`reviews_size` for the second — resolving two entirely independent `Pageable` instances from one request's query string, each driving its own separate `Page<T>` query against a different repository.

## 6. Walkthrough

Trace Level 3's request resolution.

1. **Request arrives**: `GET /dashboard?products_page=0&products_size=3&reviews_page=0&reviews_size=7` is matched to the `dashboard` controller method.
2. **First parameter resolution**: for `@Qualifier("products") Pageable productsPageable`, `PageableHandlerMethodArgumentResolver` recognizes the qualifier and looks specifically for `products_page`/`products_size`/`products_sort` query parameters — finding `products_page=0` and `products_size=3`, it builds a `Pageable` with page 0, size 3.
3. **Second parameter resolution**: for `@Qualifier("reviews") Pageable reviewsPageable`, the same resolver mechanism looks for `reviews_page`/`reviews_size`/`reviews_sort` instead — finding `reviews_page=0` and `reviews_size=7`, it builds a separate `Pageable` with page 0, size 7.
4. **Controller body executes**: `productRepo.findAll(productsPageable)` executes with the 3-sized `Pageable`, returning a `Page<Product>` with `getSize() == 3`; `reviewRepo.findAll(reviewsPageable)` executes independently with the 7-sized `Pageable`, returning a `Page<Review>` with `getSize() == 7`.
5. **Response construction**: the method builds a plain string combining both page sizes, confirming both were resolved correctly and independently from the single incoming request.
6. **Verification**: the test client checks the exact response string, confirming the two `@Qualifier`-differentiated `Pageable` parameters truly resolved to different values, sourced from their respective prefixed query parameters, in one single HTTP request.

```
 GET /dashboard?products_page=0&products_size=3&reviews_page=0&reviews_size=7
        |
        +-- @Qualifier("products") --> reads products_* params --> Pageable(page=0, size=3)
        |
        +-- @Qualifier("reviews")  --> reads reviews_* params  --> Pageable(page=0, size=7)
        |
        v
 dashboard(productsPageable, reviewsPageable)
        |
        +-- productRepo.findAll(productsPageable) --> Page<Product> size=3
        +-- reviewRepo.findAll(reviewsPageable)    --> Page<Review>  size=7
```

## 7. Gotchas & takeaways

> **Gotcha:** without `@Qualifier` on two or more `Pageable` parameters in the same controller method, `PageableHandlerMethodArgumentResolver` would try to resolve both from the *same* unprefixed `page`/`size`/`sort` query parameters — producing two `Pageable` instances with identical values, not the independent pagination each parameter is presumably meant to represent. Any controller method genuinely needing more than one `Pageable` parameter must use `@Qualifier` on each to avoid this silent, easy-to-miss collision.

- `max-page-size` (an application property, not a per-method annotation) is the global safety cap protecting against a client requesting an unreasonably large page — always worth setting explicitly in a production API rather than relying on the unbounded default.
- `@PageableDefault` supplies sensible defaults (size, sort property, sort direction) used only when the client's request omits the corresponding query parameters, without preventing the client from overriding any of them explicitly.
- `one-indexed-parameters=true` (an application property) shifts the client-facing page numbering to start at 1 instead of 0, while Spring Data's internal `Pageable`/`Page` objects remain zero-indexed as always — a translation applied purely at the resolver boundary.
- `@Qualifier` is required whenever a single controller method needs more than one independent `Pageable`/`Sort` parameter — it prefixes each parameter's expected query-parameter names, preventing the collision that would otherwise occur.
