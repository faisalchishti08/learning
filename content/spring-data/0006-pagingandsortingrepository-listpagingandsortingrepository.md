---
card: spring-data
gi: 6
slug: pagingandsortingrepository-listpagingandsortingrepository
title: "PagingAndSortingRepository / ListPagingAndSortingRepository"
---

## 1. What it is

`PagingAndSortingRepository<T, ID>` extends `CrudRepository<T, ID>` and adds two methods for retrieving results a page at a time, sorted however the caller specifies: `findAll(Sort sort)` (all results, sorted, no paging) and `findAll(Pageable pageable)` (one page of results, sorted, with total-count metadata attached). `ListPagingAndSortingRepository<T, ID>` is its `List`-returning counterpart, the same relationship `ListCrudRepository` has to `CrudRepository` — `findAll(Sort)` returns `List<T>` instead of `Iterable<T>`.

```java
public interface CustomerRepository extends PagingAndSortingRepository<Customer, Long> {}

Page<Customer> page1 = repo.findAll(PageRequest.of(0, 20, Sort.by("lastName")));
```

## 2. Why & when

Fetching an entire table's rows into memory works fine for a few hundred records, but breaks down completely for a table with millions — a UI showing "page 3 of customer results" needs the database itself to return only the relevant slice, along with enough metadata (total pages, total elements) to render pagination controls, not the whole table filtered client-side. `PagingAndSortingRepository` exists specifically to push that slicing and counting down to the database, where it belongs.

Reach for `PagingAndSortingRepository` (or, more commonly today, a store-specific interface like `JpaRepository` that already extends it) specifically when:

- You're building a paginated list view — an admin table, a search-results page, an infinite-scroll feed — where fetching everything at once would be wasteful or simply too large to hold in memory.
- You need consistent, caller-controlled sorting on a query, independent of whatever the database's default row order happens to be — `Sort` lets a caller specify one or more properties and directions without writing `ORDER BY` clauses by hand.
- You want pagination metadata (total number of elements, total number of pages, whether this is the first/last page) alongside the actual page of results, which `Page<T>` (as opposed to a bare `List<T>`) provides out of the box.

## 3. Core concept

```
 PagingAndSortingRepository<T, ID> extends CrudRepository<T, ID> {
     Iterable<T> findAll(Sort sort);
     Page<T> findAll(Pageable pageable);
 }

 ListPagingAndSortingRepository<T, ID> extends PagingAndSortingRepository<T, ID> {
     List<T> findAll(Sort sort);      -- overridden to return List<T>
     Page<T> findAll(Pageable pageable);   -- unchanged; Page already IS a rich, list-like type
 }

 Sort           -- "how to order the results" (one or more properties + direction)
 Pageable       -- Sort + "which page" (page number, page size)
 PageRequest    -- the standard concrete Pageable implementation:
                    PageRequest.of(pageNumber, pageSize, sort)
 Page<T>        -- the RESULT of a Pageable query: this page's content
                    PLUS getTotalElements(), getTotalPages(), isFirst(), isLast(), ...
```

`Pageable` is the *request* (which page, what size, what order); `Page<T>` is the *response* (this page's data, plus enough metadata to know how many more pages exist) — they're deliberately separate types, not the same object reused for both directions.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Pageable request specifying page number, size, and sort produces a Page result containing content plus total-count metadata">
  <rect x="10" y="20" width="200" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PageRequest.of(0, 20, sort)</text>
  <text x="110" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the REQUEST: page, size, order</text>

  <rect x="250" y="20" width="150" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findAll(pageable)</text>
  <text x="325" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2 queries: page + count</text>

  <rect x="440" y="20" width="190" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Page&lt;T&gt; result</text>
  <text x="535" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getContent(), getTotalElements()</text>
  <text x="535" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getTotalPages(), isLast()</text>

  <line x1="210" y1="47" x2="245" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="400" y1="47" x2="435" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Pageable` describes what page you want; `Page<T>` tells you what you got, plus how much more there is.

## 5. Runnable example

The scenario: a product catalog large enough to need pagination, evolving from basic sorted retrieval, to page-by-page navigation with metadata, to a full setup combining a derived-query filter with pagination — the realistic shape of a filtered, paginated product listing.

### Level 1 — Basic

Use `findAll(Sort)` to retrieve every row, sorted, with no paging — the simpler of the two added methods.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Sort;
import org.springframework.data.repository.ListPagingAndSortingRepository;

import java.util.List;

@SpringBootApplication
public class PagingLevel1 {

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

    public interface ProductRepository extends ListPagingAndSortingRepository<Product, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:paging1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        // Note: this repository interface has no save()/saveAll() declared -- ListPagingAndSortingRepository
        // extends CrudRepository too, so those are still inherited and available.

        List<Product> sortedByPrice = repo.findAll(Sort.by("price").ascending());
        System.out.println("sorted (empty table): " + sortedByPrice.size());

        // Seed via the inherited CrudRepository methods.
        for (double price : new double[]{29.99, 9.99, 49.99, 19.99}) {
            repo.save(new Product("Item-" + price, price));
        }

        List<Product> sorted = repo.findAll(Sort.by("price").ascending());
        System.out.println("sorted by price ascending: " + sorted.stream().map(Product::getPrice).toList());

        if (sorted.size() != 4) throw new AssertionError("Expected 4 products");
        if (sorted.get(0).getPrice() != 9.99) throw new AssertionError("Expected the cheapest product first");
        System.out.println("findAll(Sort) returned every row correctly ordered -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java PagingLevel1.java` on JDK 17+.

`repo.findAll(Sort.by("price").ascending())` fetches every `Product` row, ordered by `price` ascending at the database level (an `ORDER BY price ASC` clause), returning `List<Product>` directly because the repository extends `ListPagingAndSortingRepository`. No pagination happens here — every row comes back, just in the requested order.

### Level 2 — Intermediate

Use `findAll(Pageable)` to fetch one page at a time, and inspect the returned `Page<T>`'s metadata to navigate through multiple pages.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.repository.ListPagingAndSortingRepository;

@SpringBootApplication
public class PagingLevel2 {

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

    public interface ProductRepository extends ListPagingAndSortingRepository<Product, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagingLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:paging2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 25; i++) {
            repo.save(new Product("Item-" + i, i * 5.0));
        }

        int pageSize = 10;
        int pageNumber = 0;
        int totalFetched = 0;
        Page<Product> page;
        do {
            page = repo.findAll(PageRequest.of(pageNumber, pageSize, Sort.by("price").descending()));
            System.out.println("page " + pageNumber + "/" + (page.getTotalPages() - 1)
                + ", content size=" + page.getContent().size()
                + ", isLast=" + page.isLast());
            totalFetched += page.getContent().size();
            pageNumber++;
        } while (page.hasNext());

        System.out.println("total elements reported = " + page.getTotalElements());
        System.out.println("total fetched across pages = " + totalFetched);

        if (page.getTotalElements() != 25) throw new AssertionError("Expected 25 total elements");
        if (totalFetched != 25) throw new AssertionError("Expected to fetch exactly 25 rows across all pages");
        if (page.getTotalPages() != 3) throw new AssertionError("Expected 3 pages of size 10 for 25 rows");
        System.out.println("Paged through all results using Page metadata -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java PagingLevel2.java`.

The `do`/`while (page.hasNext())` loop walks through every page without knowing the total count in advance — each `Page<Product>` carries `getTotalElements()`, `getTotalPages()`, and `hasNext()`, computed from a `SELECT COUNT(*)` query Spring Data issues alongside the actual page-fetching query. 25 rows at page size 10 produce 3 pages (10, 10, 5), and the loop correctly fetches all 25 without the caller ever hardcoding the page count.

### Level 3 — Advanced

Combine a derived-query filter method with `Pageable`, the realistic shape of "search results, paginated" — Spring Data lets any derived-query method accept a trailing `Pageable` parameter and return `Page<T>`, not just the inherited `findAll`.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.repository.ListPagingAndSortingRepository;

@SpringBootApplication
public class PagingLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String category;
        private double price;
        protected Product() {}
        public Product(String name, String category, double price) {
            this.name = name; this.category = category; this.price = price;
        }
        public String getName() { return name; }
        public String getCategory() { return category; }
        public double getPrice() { return price; }
    }

    public interface ProductRepository extends ListPagingAndSortingRepository<Product, Long> {
        // Derived query PLUS Pageable -- returns a Page<T>, filtered AND paginated together.
        Page<Product> findByCategory(String category, Pageable pageable);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PagingLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:paging3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        for (int i = 1; i <= 12; i++) repo.save(new Product("Gadget-" + i, "electronics", i * 3.0));
        for (int i = 1; i <= 5; i++) repo.save(new Product("Shirt-" + i, "apparel", i * 2.0));

        Page<Product> electronicsPage1 = repo.findByCategory("electronics",
            PageRequest.of(0, 5, Sort.by("price").ascending()));

        System.out.println("electronics page 1: " + electronicsPage1.getContent().stream().map(Product::getName).toList());
        System.out.println("electronics total elements = " + electronicsPage1.getTotalElements());

        Page<Product> apparelPage1 = repo.findByCategory("apparel", PageRequest.of(0, 5));
        System.out.println("apparel total elements = " + apparelPage1.getTotalElements());

        if (electronicsPage1.getTotalElements() != 12) throw new AssertionError("Expected 12 electronics products total");
        if (electronicsPage1.getContent().size() != 5) throw new AssertionError("Expected page size 5");
        if (apparelPage1.getTotalElements() != 5) throw new AssertionError("Expected 5 apparel products total");

        System.out.println("Derived query + Pageable combined into a filtered, paginated result -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java PagingLevel3.java`.

`findByCategory(String category, Pageable pageable)` combines query derivation (matching the `category` field, covered fully in a later card) with an appended `Pageable` parameter — Spring Data recognizes this pattern and generates a query that filters by category *and* applies the requested page/sort, plus a matching `COUNT` query scoped to the same filter (12 electronics products total, not 17 — the count respects the `WHERE category = 'electronics'` clause, not the whole table).

## 6. Walkthrough

Trace Level 3's `findByCategory("electronics", PageRequest.of(0, 5, ...))` call.

1. **Query derivation at startup**: when the `ProductRepository` proxy is built, Spring Data's `PartTree` parser recognizes `findByCategory` as a derived query matching the `category` property, and separately recognizes the trailing `Pageable` parameter as a signal to generate a paginated, `Page`-returning query rather than a simple list-returning one.
2. **Call time — content query**: `findByCategory("electronics", pageRequest)` executes `SELECT p FROM Product p WHERE p.category = ?1 ORDER BY p.price ASC` with a `LIMIT 5 OFFSET 0` (H2's equivalent of page 0, size 5), returning the 5 cheapest electronics products.
3. **Call time — count query**: Spring Data automatically issues a second query, `SELECT COUNT(p) FROM Product p WHERE p.category = ?1`, to populate `getTotalElements()` — critically, this count is scoped to the *same* `WHERE` clause as the content query, so it reports 12 (electronics only), not 17 (the full table).
4. **`Page<Product>` assembly**: Spring Data wraps the 5 returned rows plus the total count (12) plus the requesting `Pageable` into a single `PageImpl` instance, from which `getContent()`, `getTotalElements()`, `getTotalPages()` (would be 3, at page size 5), and similar methods are all derivable.
5. **Second call**: `findByCategory("apparel", PageRequest.of(0, 5))` (no explicit sort this time, so database default order applies) repeats the same two-query pattern, scoped to `category = 'apparel'`, correctly reporting 5 total elements — since there are only 5 apparel products, page 0 at size 5 contains all of them.
6. **Verification**: the program checks both categories' total counts and the electronics page's content size, confirming the filter, pagination, and count all correctly scoped to each category independently.

```
 findByCategory("electronics", PageRequest.of(0, 5, sort))
        |
        +-- content query: WHERE category='electronics' ORDER BY price LIMIT 5 OFFSET 0
        |        -> 5 rows
        |
        +-- count query:   WHERE category='electronics' (no limit)
        |        -> 12
        |
        v
 Page<Product> { content: [5 rows], totalElements: 12, totalPages: 3, ... }
```

## 7. Gotchas & takeaways

> **Gotcha:** `Page<T>`'s count query runs as a genuinely separate database round-trip from the content query — for a very large table with an expensive `WHERE` clause, this doubles the query cost of every paginated call. When the exact total count isn't actually needed by the caller (an infinite-scroll UI that only needs to know "is there a next page," for instance), Spring Data's `Slice<T>` (a lighter-weight alternative not covered in depth here, returned by declaring a method's return type as `Slice<T>` instead of `Page<T>`) avoids the count query entirely, fetching one extra row instead to determine `hasNext()`.

- `PagingAndSortingRepository` adds exactly two methods over `CrudRepository` — `findAll(Sort)` for ordered-but-unpaged results, and `findAll(Pageable)` for paged-and-ordered results with count metadata.
- `Pageable` (the request) and `Page<T>` (the response) are deliberately distinct types — `PageRequest.of(pageNumber, pageSize, sort)` is the standard way to construct a `Pageable` to pass in.
- Any derived-query or `@Query` method can accept a trailing `Pageable` parameter and return `Page<T>` (or `Slice<T>`), not just the inherited `findAll` — pagination composes with filtering, as Level 3 demonstrated.
- `ListPagingAndSortingRepository` is to `PagingAndSortingRepository` exactly what `ListCrudRepository` is to `CrudRepository` — a `List`-returning refinement of `findAll(Sort)`, with `findAll(Pageable)` unchanged since `Page<T>` is already a rich enough type not to need this treatment.
