---
card: spring-data
gi: 5
slug: listcrudrepository
title: "ListCrudRepository"
---

## 1. What it is

`ListCrudRepository<T, ID>` is a variant of `CrudRepository<T, ID>`, introduced in Spring Data 3.0, that overrides the collection-returning methods (`findAll()`, `findAllById(Iterable<ID>)`, `saveAll(Iterable<S>)`) to return `List<T>` directly instead of `Iterable<T>` — the same operations, the same underlying implementation, just a more convenient and more commonly-needed return type.

```java
public interface CustomerRepository extends ListCrudRepository<Customer, Long> {}

List<Customer> all = repo.findAll(); // List<Customer>, not Iterable<Customer>
```

## 2. Why & when

`CrudRepository.findAll()` returns `Iterable<T>` because Spring Data Commons is designed to work across stores that don't all naturally produce a `List` — some reactive or streaming stores are more naturally exposed as an `Iterable` (or, for genuinely reactive stores, a `Flux`, covered in a later card). But for the common case — a relational database with `JpaRepository`, or any store where the results are realistically already materialized as a list — forcing every caller to convert `Iterable<T>` to `List<T>` themselves (`StreamSupport.stream(iterable.spliterator(), false).toList()`, or a manual loop) is unnecessary ceremony most call sites don't want.

Reach for `ListCrudRepository` specifically when:

- You're writing a new repository interface for a store where `List<T>` is a natural, always-available return type (virtually all relational and document stores) and want `findAll()` to hand you a `List` directly, without a manual conversion step at every call site.
- You're calling `.get(index)`, `.size()`, `.stream()`, or other `List`-specific operations on a repository's `findAll()` result and are tired of writing the `Iterable`-to-`List` boilerplate.
- You're migrating an older Spring Data codebase built on `CrudRepository` and want to reduce repetitive `Iterable`-to-`List` conversions scattered across the calling code, without giving up any of `CrudRepository`'s existing behavior.

Store-specific interfaces like `JpaRepository` already extend `ListCrudRepository` (along with `ListPagingAndSortingRepository`, covered next), so applications using `JpaRepository` get `List`-returning methods automatically without needing to reach for `ListCrudRepository` directly — this interface matters most when working with `Repository<T,ID>` extensions directly, or documenting exactly which interface introduced this convenience.

## 3. Core concept

```
 CrudRepository<T, ID>                        ListCrudRepository<T, ID>
 ----------------------                        --------------------------
 Iterable<T> findAll()                          List<T> findAll()          (override)
 Iterable<T> findAllById(Iterable<ID> ids)       List<T> findAllById(...)  (override)
 <S extends T> Iterable<S> saveAll(...)          <S extends T> List<S> saveAll(...) (override)
 (everything else identical: save, findById,     (inherits everything else unchanged)
  existsById, count, deleteById, delete, ...)
```

`ListCrudRepository` doesn't add new capabilities — it narrows three existing method signatures' return types from the more general `Iterable<T>` to the more specific and more convenient `List<T>`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ListCrudRepository extends CrudRepository, overriding three methods to return List instead of Iterable">
  <rect x="60" y="20" width="230" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="175" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CrudRepository&lt;T, ID&gt;</text>
  <text x="175" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">findAll() returns Iterable&lt;T&gt;</text>

  <rect x="350" y="20" width="240" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ListCrudRepository&lt;T, ID&gt;</text>
  <text x="470" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">findAll() returns List&lt;T&gt;</text>

  <line x1="290" y1="47" x2="345" y2="47" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <text x="317" y="40" fill="#79c0ff" font-size="14" text-anchor="middle" font-family="sans-serif">extends</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same operations underneath — only the declared return types differ, narrowing from `Iterable<T>` to `List<T>`.

## 5. Runnable example

The scenario: a `Book` repository, evolving from a plain `CrudRepository` requiring manual `Iterable`-to-`List` conversion, to `ListCrudRepository` eliminating that step, to a full comparison proving both interfaces are backed by the identical underlying implementation and identical data.

### Level 1 — Basic

Use `CrudRepository`'s `findAll()` and show the manual conversion needed to get a `List<Book>`.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.CrudRepository;

import java.util.List;
import java.util.stream.StreamSupport;

@SpringBootApplication
public class ListCrudLevel1 {

    @Entity
    public static class Book {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        protected Book() {}
        public Book(String title) { this.title = title; }
        public String getTitle() { return title; }
    }

    public interface BookRepository extends CrudRepository<Book, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ListCrudLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:listcrud1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        BookRepository repo = ctx.getBean(BookRepository.class);
        repo.save(new Book("Effective Java"));
        repo.save(new Book("Clean Code"));

        Iterable<Book> allIterable = repo.findAll();
        System.out.println("findAll() return type = " + allIterable.getClass().getSimpleName());

        // Manual conversion required to get a List, since CrudRepository only promises Iterable.
        List<Book> allList = StreamSupport.stream(allIterable.spliterator(), false).toList();
        System.out.println("converted to List, size = " + allList.size());

        if (allList.size() != 2) throw new AssertionError("Expected 2 books after manual conversion");
        System.out.println("CrudRepository required a manual Iterable -> List conversion -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ListCrudLevel1.java` on JDK 17+.

`repo.findAll()` returns `Iterable<Book>` per `CrudRepository`'s contract — to get list operations like `.size()` or `.get(index)`, calling code must convert it, here via `StreamSupport.stream(...).toList()`. This manual step is exactly the friction `ListCrudRepository` removes.

### Level 2 — Intermediate

Switch the same repository to extend `ListCrudRepository` instead, and show `findAll()` now returns `List<Book>` directly, with no conversion step.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.ListCrudRepository;

import java.util.List;

@SpringBootApplication
public class ListCrudLevel2 {

    @Entity
    public static class Book {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        protected Book() {}
        public Book(String title) { this.title = title; }
        public String getTitle() { return title; }
    }

    public interface BookRepository extends ListCrudRepository<Book, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ListCrudLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:listcrud2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        BookRepository repo = ctx.getBean(BookRepository.class);
        repo.save(new Book("Effective Java"));
        repo.save(new Book("Clean Code"));
        repo.save(new Book("Domain-Driven Design"));

        List<Book> all = repo.findAll(); // List<Book> directly -- no conversion
        System.out.println("findAll() returned a List directly, size = " + all.size());
        System.out.println("first title = " + all.get(0).getTitle()); // List-specific method, no cast needed

        if (all.size() != 3) throw new AssertionError("Expected 3 books");
        System.out.println("ListCrudRepository.findAll() returned List<Book> with zero conversion -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java ListCrudLevel2.java`.

The only source change from Level 1 is `extends ListCrudRepository<Book, Long>` instead of `extends CrudRepository<Book, Long>` — `findAll()` now has the compile-time return type `List<Book>`, so `.get(0)` is callable directly with no cast or conversion. This is a pure ergonomics improvement: the underlying SQL and Hibernate behavior are identical to Level 1.

### Level 3 — Advanced

Prove both interfaces are backed by the exact same implementation and data by running equivalent operations through both a `CrudRepository`-based and a `ListCrudRepository`-based interface over the *same* underlying table, confirming they produce identical results — only the declared return type differs, nothing about the actual persistence behavior.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.repository.CrudRepository;
import org.springframework.data.repository.ListCrudRepository;

import java.util.List;
import java.util.stream.StreamSupport;

@SpringBootApplication
public class ListCrudLevel3 {

    @Entity
    public static class Book {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        protected Book() {}
        public Book(String title) { this.title = title; }
        public String getTitle() { return title; }
    }

    // Two interfaces over the SAME entity/table, one Iterable-based, one List-based.
    public interface BookIterableRepository extends CrudRepository<Book, Long> {}
    public interface BookListRepository extends ListCrudRepository<Book, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ListCrudLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:listcrud3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        BookIterableRepository iterableRepo = ctx.getBean(BookIterableRepository.class);
        BookListRepository listRepo = ctx.getBean(BookListRepository.class);

        // Insert through ONE of the repositories -- both point at the same table.
        listRepo.saveAll(List.of(new Book("Effective Java"), new Book("Clean Code")));

        Iterable<Book> viaIterable = iterableRepo.findAll();
        List<Book> viaIterableConverted = StreamSupport.stream(viaIterable.spliterator(), false).toList();
        List<Book> viaList = listRepo.findAll();

        List<String> titlesFromIterable = viaIterableConverted.stream().map(Book::getTitle).sorted().toList();
        List<String> titlesFromList = viaList.stream().map(Book::getTitle).sorted().toList();

        System.out.println("titles via CrudRepository (converted)  = " + titlesFromIterable);
        System.out.println("titles via ListCrudRepository (direct) = " + titlesFromList);

        if (!titlesFromIterable.equals(titlesFromList))
            throw new AssertionError("Both repositories should see identical data from the shared table");
        System.out.println("Both interfaces returned identical data -- only the return type differs -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java ListCrudLevel3.java`.

`BookIterableRepository` and `BookListRepository` are two entirely separate generated proxies, but both operate against the same `Book` table via Hibernate. Data inserted through `listRepo.saveAll(...)` is immediately visible through `iterableRepo.findAll()` (after conversion) and produces an identical sorted title list to `listRepo.findAll()` — concrete proof that `ListCrudRepository` changes only the Java-level return type, not the underlying query, storage, or behavior in any way.

## 6. Walkthrough

Trace Level 3's data flow.

1. **Two proxies generated**: at startup, Spring Data JPA generates a proxy for `BookIterableRepository` (backed by `SimpleJpaRepository`, `findAll()` returning `Iterable<Book>`) and a separate proxy for `BookListRepository` (also backed by `SimpleJpaRepository`, but with `findAll()`'s declared return type as `List<Book>`) — both target the same `Book` JPA entity and therefore the same database table.
2. **`listRepo.saveAll(...)`** inserts two rows via the `BookListRepository` proxy's `saveAll`, which — like `CrudRepository`'s — performs two (or a batched set of) `INSERT` statements against the `book` table.
3. **`iterableRepo.findAll()`** queries the same table independently through the other proxy, returning an `Iterable<Book>` — under the hood, for `SimpleJpaRepository`, this is very often *already* a `List` internally (Hibernate's JPQL query execution naturally produces a `List`), just exposed through the narrower `Iterable` interface type at the `CrudRepository` contract level.
4. **Manual conversion**: `StreamSupport.stream(viaIterable.spliterator(), false).toList()` converts the `Iterable` to a genuine `List<Book>` for comparison purposes.
5. **`listRepo.findAll()`** queries the same table again, this time already typed as `List<Book>` per `ListCrudRepository`'s contract — no manual conversion needed.
6. **Comparison**: both result lists are mapped to sorted title lists and compared for equality — they match exactly, since both queries hit the identical underlying data.
7. **Verification**: the assertion confirms the two independently-obtained result sets are identical, proving `ListCrudRepository` is purely a return-type refinement over the same behavior `CrudRepository` already provides.

```
 book table (shared)
   ^                                  ^
   |                                  |
 BookIterableRepository          BookListRepository
   findAll() -> Iterable<Book>      findAll() -> List<Book>
   (needs manual .toList())         (already a List)
   |                                  |
   +---------- same rows, same data --+
```

## 7. Gotchas & takeaways

> **Gotcha:** `ListCrudRepository` only changes the return type of `findAll()`, `findAllById(...)`, and `saveAll(...)` — any custom derived-query method you declare yourself (like `findByTitle(...)`) still returns whatever type *you* declare for it; extending `ListCrudRepository` instead of `CrudRepository` doesn't retroactively change custom method signatures you write, only the three inherited methods it explicitly overrides.

- `ListCrudRepository<T, ID>` is functionally identical to `CrudRepository<T, ID>` — it changes nothing about behavior, only narrows `findAll()`, `findAllById(...)`, and `saveAll(...)` to return `List<T>` instead of `Iterable<T>`.
- Store-specific interfaces like `JpaRepository` already extend `ListCrudRepository` (as of Spring Data 3.0+), so most JPA-based applications get `List`-returning methods automatically without ever mentioning `ListCrudRepository` directly.
- Switching an existing `CrudRepository`-based interface to `ListCrudRepository` is a safe, low-risk refactor — the only observable change is the compile-time return type of the three affected methods, removing manual conversion boilerplate at call sites.
- This card completes the picture of `CrudRepository`'s family — the next card covers `PagingAndSortingRepository`/`ListPagingAndSortingRepository`, which add page- and sort-aware querying on top of this same foundation.
