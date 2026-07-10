---
card: spring-data
gi: 33
slug: enablespringdatawebsupport
title: "@EnableSpringDataWebSupport"
---

## 1. What it is

This card goes deeper on `@EnableSpringDataWebSupport` itself — specifically its `pageSerializationMode` attribute, which controls exactly how a `Page<T>` returned from a controller method gets serialized to JSON. The default, `VIA_DTO`, serializes `Page<T>` through an internal, stable DTO shape (`content`, `pageable`, `totalElements`, and so on) rather than serializing Spring Data's actual `PageImpl` class directly — a distinction that matters because `PageImpl`'s internal fields aren't a published, stable API contract, while the DTO shape is.

```java
@Configuration
@EnableSpringDataWebSupport(pageSerializationMode = EnableSpringDataWebSupport.PageSerializationMode.VIA_DTO)
public class WebConfig {}
```

## 2. Why & when

Early versions of Spring Data's web support serialized `Page<T>` by directly running Jackson over the `PageImpl` object — which worked, but tied the JSON response shape to `PageImpl`'s actual field layout, an internal implementation detail never intended as a stable public contract. `pageSerializationMode = VIA_DTO` (the current default) fixes this by serializing through a dedicated, stable `PagedModel`-like DTO instead, decoupling the JSON contract from Spring Data's internal class structure — but understanding this setting matters because it explains why upgrading Spring Data versions can occasionally change a `Page<T>` response's exact JSON field names, and gives you the lever to control that shape deliberately.

Understanding this setting matters specifically when:

- You're debugging why a `Page<T>` API response's JSON shape doesn't match older documentation or a different Spring Data version's output — `pageSerializationMode` (and the version-driven default it resolves to) is very often the explanation.
- You're building or maintaining an API contract that clients depend on and want to guarantee the `Page<T>` JSON shape stays stable and predictable across Spring Data upgrades — understanding `VIA_DTO`'s DTO-based approach clarifies exactly what stability guarantee you're relying on.
- You're choosing whether to expose `Page<T>` directly from a controller at all, versus mapping it to your own custom response DTO — knowing what Spring Data's default serialization actually produces informs that decision.

## 3. Core concept

```
 Page<T> returned from a @RestController method
        |
        v
 pageSerializationMode = VIA_DTO   (current default)
        |
        v
 Jackson serializes NOT PageImpl directly, but a stable DTO shape:
   {
     "content": [ ... entities or projections ... ],
     "page": {
       "size": 20,
       "number": 0,
       "totalElements": 137,
       "totalPages": 7
     }
   }
        |
        v
 this JSON SHAPE is the stable contract -- independent of PageImpl's
 actual internal Java field names/structure, which CAN change between
 Spring Data versions without breaking this JSON contract
```

The exact JSON field layout has evolved across Spring Data versions (older versions nested pagination metadata differently) — `VIA_DTO`'s point is that the *serialization* is now decoupled from Spring Data's *internal Java types*, giving the framework room to keep improving `PageImpl` without silently breaking every API response shape.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="VIA_DTO serialization decouples the JSON response shape from the internal PageImpl class structure">
  <rect x="10" y="20" width="270" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="145" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PageImpl (internal Java class)</text>
  <text x="145" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">structure can change between versions</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">stable DTO (VIA_DTO)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">content + page{size,number,totalElements,totalPages}</text>

  <rect x="150" y="110" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">JSON clients depend on the STABLE DTO shape, not PageImpl</text>

  <line x1="150" y1="60" x2="380" y2="60" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Serialization goes through a stable DTO layer, insulating API clients from internal Java class changes.

## 5. Runnable example

The scenario: a `Product` listing endpoint, evolving from observing the default `VIA_DTO` JSON shape directly, to confirming the actual field names present in the response, to a comparison endpoint mapping `Page<T>` to a fully custom DTO instead — the alternative many real APIs choose for even tighter control over the response contract.

### Level 1 — Basic

Expose a `Page<Product>`-returning endpoint and inspect the raw JSON response shape produced by the default `VIA_DTO` serialization.

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
public class EnableWebSupportLevel1 {

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
    public EnableWebSupportLevel1(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public Page<Product> list(Pageable pageable) { return repo.findAll(pageable); }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(EnableWebSupportLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:enablews1",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 25; i++) repo.save(new Product("Product" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products?page=0&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("full response body:\n" + response.body());

        boolean hasContent = response.body().contains("\"content\"");
        boolean hasTotalElements = response.body().contains("\"totalElements\":25");
        boolean hasTotalPages = response.body().contains("\"totalPages\":3");

        if (!hasContent) throw new AssertionError("Expected a 'content' field in the response");
        if (!hasTotalElements) throw new AssertionError("Expected totalElements=25");
        if (!hasTotalPages) throw new AssertionError("Expected totalPages=3 for 25 items at page size 10");

        System.out.println("Default VIA_DTO serialization produced the expected stable JSON shape -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa`, `spring-boot-starter-web`, and `com.h2database:h2` on the classpath, then `java EnableWebSupportLevel1.java` on JDK 17+.

Printing the full response body makes the actual `VIA_DTO`-serialized JSON shape directly observable — a `"content"` array holding the page's `Product` entities, alongside pagination metadata fields including `totalElements` and `totalPages`, computed automatically from the `Page<Product>` the controller method returned.

### Level 2 — Intermediate

Confirm the response's pagination metadata correctly reflects a *different* page request, proving the DTO shape's numbers are genuinely computed per-request, not hardcoded or cached.

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
public class EnableWebSupportLevel2 {

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
    public EnableWebSupportLevel2(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products")
    public Page<Product> list(Pageable pageable) { return repo.findAll(pageable); }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(EnableWebSupportLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:enablews2",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 25; i++) repo.save(new Product("Product" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();

        HttpResponse<String> page0 = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products?page=0&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());
        HttpResponse<String> page2 = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products?page=2&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("page 0 metadata snippet: " + extractPageMetadata(page0.body()));
        System.out.println("page 2 metadata snippet: " + extractPageMetadata(page2.body()));

        boolean page0Correct = page0.body().contains("\"number\":0");
        boolean page2Correct = page2.body().contains("\"number\":2") && page2.body().contains("\"size\":5");
        // page 2 (0-indexed, size 10) of 25 items only has 5 remaining items: indices 20-24

        if (!page0Correct) throw new AssertionError("Expected page 0's metadata to report number=0");
        if (!page2.body().contains("\"number\":2")) throw new AssertionError("Expected page 2's metadata to report number=2");

        System.out.println("Pagination metadata correctly recomputed per distinct request -- PASS");
        ctx.close();
    }

    static String extractPageMetadata(String body) {
        int idx = body.indexOf("\"page\":");
        return idx >= 0 ? body.substring(idx, Math.min(body.length(), idx + 100)) : "(no page metadata found)";
    }
}
```

How to run: same classpath as Level 1, `java EnableWebSupportLevel2.java`.

Requesting page `0` and page `2` (both size `10`) against the same 25-row dataset produces two responses whose `"number"` field correctly differs (`0` versus `2`) — confirming the `VIA_DTO` serialization isn't returning a cached or static shape, but genuinely reflects the specific `Pageable` each request resolved to and the specific `Page<Product>` that request produced.

### Level 3 — Advanced

Build a controller endpoint that maps `Page<T>` to a fully custom DTO before returning it — the alternative many real production APIs choose over relying on Spring Data's built-in `VIA_DTO` shape, for even tighter, self-defined control over the exact response contract.

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
import java.util.List;

@SpringBootApplication
@RestController
public class EnableWebSupportLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        protected Product() {}
        public Product(String name) { this.name = name; }
        public String getName() { return name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {}

    // A fully custom, self-defined response contract -- independent of Spring Data's own shape.
    public record ProductListResponse(List<String> productNames, int currentPage, boolean hasMorePages) {}

    private final ProductRepository repo;
    public EnableWebSupportLevel3(ProductRepository repo) { this.repo = repo; }

    @GetMapping("/products-custom")
    public ProductListResponse listCustom(Pageable pageable) {
        Page<Product> page = repo.findAll(pageable);
        return new ProductListResponse(
            page.getContent().stream().map(Product::getName).toList(),
            page.getNumber(),
            page.hasNext());
    }

    public static void main(String[] args) throws Exception {
        ConfigurableApplicationContext ctx = SpringApplication.run(EnableWebSupportLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:enablews3",
            "--spring.jpa.hibernate.ddl-auto=create-drop",
            "--server.port=0");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 12; i++) repo.save(new Product("Product" + i));

        int port = ((ServletWebServerApplicationContext) ctx).getWebServer().getPort();
        HttpClient client = HttpClient.newHttpClient();
        HttpResponse<String> response = client.send(
            HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/products-custom?page=0&size=10")).GET().build(),
            HttpResponse.BodyHandlers.ofString());

        System.out.println("custom DTO response: " + response.body());

        boolean hasCustomShape = response.body().contains("\"productNames\"") && response.body().contains("\"hasMorePages\":true");
        boolean lacksSpringDataShape = !response.body().contains("\"totalElements\"");

        if (!hasCustomShape) throw new AssertionError("Expected the custom DTO's own field names in the response");
        if (!lacksSpringDataShape) throw new AssertionError("Expected NO Spring Data-specific fields, since this uses a fully custom DTO");

        System.out.println("Custom DTO mapping gave complete, self-defined control over the response contract -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java EnableWebSupportLevel3.java`.

`listCustom` extracts exactly what it needs from `Page<Product>` (`getContent()`, `getNumber()`, `hasNext()`) and maps it into `ProductListResponse` — a plain record with entirely self-defined field names (`productNames`, `currentPage`, `hasMorePages`), completely independent of whatever shape `pageSerializationMode` would otherwise produce. This is the escape hatch for any API that wants full, permanent control over its response contract, unaffected by future Spring Data serialization changes.

## 6. Walkthrough

Trace the `GET /products-custom?page=0&size=10` request.

1. **Argument resolution**: exactly as in the earlier cards, `Pageable pageable` is bound automatically from the `page=0&size=10` query parameters via Spring Data's web support.
2. **`repo.findAll(pageable)`** executes, returning a genuine `Page<Product>` — the same kind of object every earlier example in this section has produced, complete with its own internal `VIA_DTO`-serializable structure, which this endpoint deliberately never lets Jackson see directly.
3. **Custom mapping**: `page.getContent().stream().map(Product::getName).toList()` extracts just the product names as a plain `List<String>`; `page.getNumber()` and `page.hasNext()` extract just the two pieces of pagination state this particular API contract cares about.
4. **`ProductListResponse` construction**: these three extracted pieces are assembled into the custom record — at this point, the original `Page<Product>` object is discarded entirely; only the mapped data survives into the response.
5. **Serialization**: Spring MVC's Jackson integration serializes `ProductListResponse` using its own record component names (`productNames`, `currentPage`, `hasMorePages`) — Spring Data's `pageSerializationMode` setting is entirely irrelevant here, since the returned type isn't `Page<T>` at all anymore by the time serialization happens.
6. **Response verification**: the program checks the response contains the custom field names and explicitly checks the *absence* of Spring Data's own `totalElements` field, confirming the mapping genuinely replaced the built-in shape rather than merely adding to it.

```
 repo.findAll(pageable)  -->  Page<Product>  (Spring Data's own rich object)
        |
        v
 MANUAL extraction: getContent(), getNumber(), hasNext()
        |
        v
 new ProductListResponse(names, page, hasMore)   -- a plain record, own field names
        |
        v
 Jackson serializes THIS record -- Page<Product> and pageSerializationMode never involved
```

## 7. Gotchas & takeaways

> **Gotcha:** returning `Page<T>` directly from a controller (Levels 1 and 2) is convenient, but couples your API's response contract to Spring Data's serialization behavior — even with the stability `VIA_DTO` provides over the older direct-`PageImpl`-serialization approach, the exact field set and nesting is still ultimately decided by the Spring Data version in use, not by your own API design. For an API with external consumers and a genuine stability requirement, mapping to a custom DTO (Level 3) is the more defensive choice, even though it's more code to write and maintain.

- `pageSerializationMode = VIA_DTO` (the current default) serializes `Page<T>` through a stable, dedicated DTO shape rather than Jackson-serializing the internal `PageImpl` class directly — decoupling the JSON contract from Spring Data's internal Java structure.
- The resulting default JSON shape includes a `content` array plus nested pagination metadata (`totalElements`, `totalPages`, `number`, `size`) — genuinely recomputed per request, reflecting whatever `Pageable` that specific request resolved to.
- Mapping `Page<T>` to a fully custom response DTO before returning it from a controller remains the most defensive option for APIs that need a response contract entirely independent of Spring Data's own serialization choices, present or future.
- Understanding `pageSerializationMode` explains why a `Page<T>`-returning endpoint's exact JSON shape can differ across Spring Data versions, and gives a deliberate lever (or, via a custom DTO, a complete opt-out) for controlling that shape.
