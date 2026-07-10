---
card: spring-data
gi: 36
slug: hypermedia-paging-pagedresourcesassembler
title: "Hypermedia paging (PagedResourcesAssembler)"
---

## 1. What it is

`PagedResourcesAssembler<T>` converts a `Page<T>` into a `PagedModel<EntityModel<T>>` — a Spring HATEOAS response type carrying not just the page's content and metadata, but genuine hypermedia navigation links (`self`, `next`, `prev`, `first`, `last`) computed from the original request, letting API clients navigate a paginated resource by following links instead of manually constructing `?page=N` URLs themselves.

```java
@GetMapping("/products")
PagedModel<EntityModel<Product>> list(Pageable pageable, PagedResourcesAssembler<Product> assembler) {
    Page<Product> page = repo.findAll(pageable);
    return assembler.toModel(page);
}
```

## 2. Why & when

A plain `Page<T>` response (as used throughout this section's earlier web-support cards) tells a client the current page's content and enough metadata (`totalPages`, `totalElements`) to *compute* the URL for the next page itself — but the client has to do that computation, coupling it to the exact query-parameter names and URL structure the API happens to use. HATEOAS-style APIs push that responsibility back onto the server: the response itself includes the literal URL for "next page," "previous page," and so on, so a well-behaved client never needs to construct a pagination URL by hand at all — it just follows the link the server already computed.

Reach for `PagedResourcesAssembler` specifically when:

- You're building a HATEOAS-style REST API (following Spring HATEOAS conventions) where responses are expected to include navigable links, not just raw data and metadata.
- You want to decouple API clients from your URL structure — if the pagination query-parameter convention changes later, clients following links rather than constructing URLs themselves are unaffected.
- You're exposing a Spring Data-backed collection resource where "next page" and "previous page" navigation should be a first-class, discoverable part of the response, appropriate for public or long-lived APIs where client-URL-construction coupling is a real maintenance risk.

## 3. Core concept

```
 Page<Product> page = repo.findAll(pageable);
        |
        v
 PagedResourcesAssembler<Product>.toModel(page)
        |
        v
 PagedModel<EntityModel<Product>>:
   {
     "_embedded": { "productList": [ ...each Product wrapped as an EntityModel... ] },
     "_links": {
       "self":  { "href": ".../products?page=1&size=10" },
       "first": { "href": ".../products?page=0&size=10" },
       "prev":  { "href": ".../products?page=0&size=10" },
       "next":  { "href": ".../products?page=2&size=10" },
       "last":  { "href": ".../products?page=6&size=10" }
     },
     "page": { "size": 10, "totalElements": 65, "totalPages": 7, "number": 1 }
   }

 Links are computed from the ORIGINAL incoming request's URL + the page's
 position -- "next" simply doesn't appear at all if the current page is
 already the last one (and likewise "prev" is absent on the first page).
```

The assembler reads the current request's URL (via `ServletUriComponentsBuilder`) to build each link, which is why it needs to be injected as a controller-method parameter rather than constructed manually outside a request context.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PagedResourcesAssembler converts a Page into a PagedModel carrying navigable next/prev/self links computed from the request">
  <rect x="10" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Page&lt;Product&gt;</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">content + counts only</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PagedResourcesAssembler</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.toModel(page)</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PagedModel</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ self/next/prev/first/last links</text>

  <line x1="190" y1="47" x2="225" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="47" x2="445" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The assembler enriches a plain `Page<T>` with computed navigation links, based on the current request.

## 5. Runnable example

The scenario: a `Product` catalog exposed with HATEOAS pagination, evolving from a basic assembled response with `self`/`next` links, to confirming `prev`/`next` correctly appear or disappear at the boundaries, to a custom `EntityModel` mapping adding a resource-specific link alongside the standard pagination links.

### Level 1 — Basic

Wire `PagedResourcesAssembler<Product>` into a controller method and confirm the response includes real, followable `self` and `next` links.

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
import org.springframework.data.web.PagedResourcesAssembler;
import org.springframework.hateoas.EntityModel;
import org.springframework.hateoas.PagedModel;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class PagedAssemblerLevel1 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    private final ProductRepository repo;
    public PagedAssemblerLevel1(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public PagedModel<EntityModel<Product>> list(Pageable pageable, PagedResourcesAssembler<Product> assembler) {
        Page<Product> page = repo.findAll(pageable);
        return assembler.toModel(page);
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagedAssemblerLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:pagedassembler1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 25; i++) repo.save(new Product("Product" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products?page=0&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("response:\n" + response.body());

        boolean hasSelfLink = response.body().contains("\"self\"");
        boolean hasNextLink = response.body().contains("\"next\"");
        boolean hasEmbedded = response.body().contains("_embedded");

        if (!hasSelfLink) throw new AssertionError("Expected a 'self' link in the HATEOAS response");
        if (!hasNextLink) throw new AssertionError("Expected a 'next' link, since more pages exist beyond page 0");
        if (!hasEmbedded) throw new AssertionError("Expected an '_embedded' section containing the actual products");

        System.out.println("PagedResourcesAssembler produced a HATEOAS response with real navigation links -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-boot-starter-web`, `spring-boot-starter-hateoas`, and `com.h2database:h2` on the classpath, then `java PagedAssemblerLevel1.java` on JDK 17+.

`assembler.toModel(page)` transforms the plain `Page<Product>` into a `PagedModel<EntityModel<Product>>` — the raw JSON response includes a `_links` section with `self` (this exact request's URL) and `next` (the URL for page 1), computed automatically from the incoming request's own URL and the page's position within the total result set.

### Level 2 — Intermediate

Request the first, a middle, and the last page, confirming `prev`/`next` links correctly appear or are absent depending on the page's position — exactly the navigational correctness a client relies on.

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
import org.springframework.data.web.PagedResourcesAssembler;
import org.springframework.hateoas.EntityModel;
import org.springframework.hateoas.PagedModel;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class PagedAssemblerLevel2 {

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
    public PagedAssemblerLevel2(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public PagedModel<EntityModel<Product>> list(Pageable pageable, PagedResourcesAssembler<Product> assembler) {
        return assembler.toModel(repo.findAll(pageable));
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagedAssemblerLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:pagedassembler2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 30; i++) repo.save(new Product("Product" + i)); // 3 pages of 10

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();

        String firstPage = get(client, port, "/products?page=0&size=10");
        String middlePage = get(client, port, "/products?page=1&size=10");
        String lastPage = get(client, port, "/products?page=2&size=10");

        boolean firstHasNoPrev = !firstPage.contains("\"prev\"");
        boolean firstHasNext = firstPage.contains("\"next\"");
        boolean middleHasBoth = middlePage.contains("\"prev\"") && middlePage.contains("\"next\"");
        boolean lastHasNoNext = !lastPage.contains("\"next\"");
        boolean lastHasPrev = lastPage.contains("\"prev\"");

        System.out.println("first page: no prev=" + firstHasNoPrev + ", has next=" + firstHasNext);
        System.out.println("middle page: has both=" + middleHasBoth);
        System.out.println("last page: no next=" + lastHasNoNext + ", has prev=" + lastHasPrev);

        if (!firstHasNoPrev) throw new AssertionError("Expected NO 'prev' link on the first page");
        if (!firstHasNext) throw new AssertionError("Expected a 'next' link on the first page");
        if (!middleHasBoth) throw new AssertionError("Expected BOTH 'prev' and 'next' on the middle page");
        if (!lastHasNoNext) throw new AssertionError("Expected NO 'next' link on the last page");
        if (!lastHasPrev) throw new AssertionError("Expected a 'prev' link on the last page");

        System.out.println("prev/next links correctly appeared and disappeared at page boundaries -- PASS");
        ctx.close();
    }

    static String get(HttpClient client, int port, String path) throws Exception {
        return client.send(HttpRequest.newBuilder(URI.create("http://localhost:" + port + path)).GET().build(),
            HttpResponse.BodyHandlers.ofString()).body();
    }
}
```

How to run: same classpath as Level 1, `java PagedAssemblerLevel2.java`.

With 30 products at page size 10 (3 total pages, indices 0–2), the first page's response correctly has no `prev` link (there's nothing before it) but does have `next`; the last page has `prev` but no `next`; the middle page has both — `PagedResourcesAssembler` computes exactly the links that make navigational sense for each page's specific position, not a fixed set of links present on every response regardless of position.

### Level 3 — Advanced

Provide a custom `RepresentationModelAssembler` to add a resource-specific link (a link to a related sub-resource) to each individual `Product` inside the page, alongside the standard pagination-level links — the realistic shape of a fully-linked HATEOAS resource.

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
import org.springframework.data.web.PagedResourcesAssembler;
import org.springframework.hateoas.EntityModel;
import org.springframework.hateoas.Link;
import org.springframework.hateoas.PagedModel;
import org.springframework.hateoas.server.RepresentationModelAssembler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@SpringBootApplication
@RestController
public class PagedAssemblerLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
        public Long getId() { return id; }
        public String getName() { return name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    // A custom assembler adding a resource-specific "reviews" link to EACH Product.
    public static class ProductModelAssembler implements RepresentationModelAssembler<Product, EntityModel<Product>> {
        @Override
        public EntityModel<Product> toModel(Product product) {
            return EntityModel.of(product,
                Link.of("/products/" + product.getId(), "self"),
                Link.of("/products/" + product.getId() + "/reviews", "reviews"));
        }
    }

    private final ProductRepository repo;
    private final ProductModelAssembler productAssembler = new ProductModelAssembler();
    public PagedAssemblerLevel3(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public PagedModel<EntityModel<Product>> list(Pageable pageable, PagedResourcesAssembler<Product> pagedAssembler) {
        Page<Product> page = repo.findAll(pageable);
        return pagedAssembler.toModel(page, productAssembler); // custom per-item assembler + standard page links
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagedAssemblerLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:pagedassembler3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        Product saved = repo.save(new Product("Widget"));
        repo.save(new Product("Gadget"));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products?page=0&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("response:\n" + response.body());

        boolean hasReviewsLink = response.body().contains("/products/" + saved.getId() + "/reviews");
        boolean hasPageSelfLink = response.body().contains("\"self\"");

        if (!hasReviewsLink) throw new AssertionError("Expected each Product to have its own 'reviews' link");
        if (!hasPageSelfLink) throw new AssertionError("Expected the page-level 'self' link to still be present");

        System.out.println("Custom per-item links coexisted with standard page-level navigation links -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java PagedAssemblerLevel3.java`.

`pagedAssembler.toModel(page, productAssembler)` — the two-argument overload — combines the standard page-level navigation links (`self`, `next`, `prev`) with a *custom* `RepresentationModelAssembler` applied to each individual `Product` in the page's content, adding a `reviews` link pointing at each product's own sub-resource. The result is a fully-linked response: navigate between pages using the page-level links, or navigate into a specific product's related resources using its own per-item links — both kinds of hypermedia navigation present in one response.

## 6. Walkthrough

Trace `pagedAssembler.toModel(page, productAssembler)` in Level 3.

1. **`repo.findAll(pageable)`** produces a plain `Page<Product>`, exactly as in every earlier pagination example in this section — content plus count metadata, no links yet.
2. **`pagedAssembler.toModel(page, productAssembler)`** begins assembly: first, it computes the page-level navigation links (`self`, `next`, `prev`, and so on) exactly as the single-argument `toModel(page)` overload from Levels 1 and 2 did, based on the current request's URL and the page's position.
3. **Per-item transformation**: for *each* `Product` in the page's content, instead of using the default, bare `EntityModel.of(product)` wrapping (no links), the assembler delegates to the supplied `productAssembler.toModel(product)`.
4. **`ProductModelAssembler.toModel(product)`** builds a custom `EntityModel<Product>` with two explicit links: a `self` link (`/products/{id}`) and a `reviews` link (`/products/{id}/reviews`) — both computed directly from the product's own `id`, independent of the surrounding page's position.
5. **Assembly combines both layers**: the final `PagedModel<EntityModel<Product>>` contains the page-level links in its top-level `_links`, and each embedded `Product` entry carries its own per-item links (`self`, `reviews`) within its own `_links` section.
6. **Serialization**: Jackson (via Spring HATEOAS's media-type support) serializes this nested link structure into the JSON response — both the page-level and item-level links appear, at their respective nesting levels.
7. **Verification**: the program checks both the presence of a per-item `reviews` link referencing the specific saved product's id, and the continued presence of the page-level `self` link, confirming both layers of hypermedia navigation coexist correctly in the assembled response.

```
 Page<Product> (2 items)
        |
        v
 pagedAssembler.toModel(page, productAssembler)
        |
        +-- page-level links: self, next, prev  (computed from the request + page position)
        |
        +-- FOR EACH Product: delegate to productAssembler.toModel(product)
                    |
                    v
              EntityModel<Product> with self + reviews links (computed from product.id)
        |
        v
 PagedModel<EntityModel<Product>>  -- BOTH layers of links present in one response
```

## 7. Gotchas & takeaways

> **Gotcha:** `PagedResourcesAssembler` must be injected as a controller-method parameter (as every example in this card does), not constructed manually or injected as a field — its link computation depends on the current HTTP request's context (`ServletUriComponentsBuilder.fromCurrentRequest()`), which is only reliably available within the scope of an active request being handled. Attempting to use a `PagedResourcesAssembler` outside a request (in a scheduled job, a test running without a mock request context, or a field-injected singleton reused across requests) typically produces incorrect or failing link computation.

- `PagedResourcesAssembler<T>` converts a plain `Page<T>` into a `PagedModel<EntityModel<T>>` carrying computed, request-aware navigation links (`self`, `next`, `prev`, `first`, `last`) — letting HATEOAS-following clients navigate pagination without constructing URLs themselves.
- Navigation links correctly appear or disappear based on the page's actual position — no `prev` on the first page, no `next` on the last page — computed automatically from the page's own state, not hardcoded.
- The two-argument `toModel(page, customAssembler)` overload combines standard page-level links with a custom `RepresentationModelAssembler` applied to each individual item, letting a response carry both pagination navigation and resource-specific links simultaneously.
- Because link computation depends on the active HTTP request's context, always obtain `PagedResourcesAssembler` as a controller-method parameter (letting Spring inject a request-scoped instance) rather than trying to construct or reuse one outside an active request.
