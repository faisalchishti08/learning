---
card: spring-data
gi: 16
slug: special-parameter-handling-pageable-sort-limit
title: "Special parameter handling (Pageable, Sort, Limit)"
---

## 1. What it is

Beyond the filter parameters query derivation matches against entity properties, Spring Data recognizes three special parameter *types* — `Pageable`, `Sort`, and `Limit` — that any derived-query or `@Query` method can accept as a trailing parameter, regardless of what the rest of the method name says. These aren't matched against entity properties at all; Spring Data recognizes them by their Java type and uses them to control pagination, ordering, or result-count limiting at the query-execution level.

```java
List<Customer> findByStatus(String status, Sort sort);
Page<Customer> findByStatus(String status, Pageable pageable);
List<Customer> findByStatus(String status, Limit limit);
```

## 2. Why & when

An earlier card in this section (on `PagingAndSortingRepository`) already showed `Pageable` appended to a derived method — this card generalizes that pattern and introduces its sibling, `Limit` (a more recent, lighter-weight alternative to `Top`/`First` for a caller-supplied, runtime-determined limit rather than a limit baked into the method name at compile time). Understanding these as a *category* of special parameters — recognized by type, not by name-matching — clarifies why they can be added to almost any derived or `@Query` method without changing anything else about how that method's filtering works.

Reach for these specifically when:

- You need caller-controlled sort order without hardcoding it into the method name via `OrderBy` — `Sort` lets each call site decide its own ordering.
- You need one method that supports both "give me a page" and "give me everything, sorted" call patterns — `Pageable` (via `PageRequest.of(...)`) and `Sort` (passed directly) can often share the same underlying method signature pattern.
- You need a result-count limit determined at runtime (a user-configurable "show top N" setting, for instance) rather than fixed at compile time the way `findTop5By...` bakes `5` into the method name — `Limit.of(n)`, passed as a parameter, achieves this.

## 3. Core concept

```
 Special parameter TYPES (recognized by Java type, not by name):

   org.springframework.data.domain.Sort
     -- controls ORDER BY; can be combined with OrderBy in the method name

   org.springframework.data.domain.Pageable
     -- controls LIMIT/OFFSET + carries Sort too; changes the method's
        return type expectation (commonly Page<T> or Slice<T>)

   org.springframework.data.domain.Limit  (Spring Data 3.2+)
     -- controls ONLY a result-count cap, no offset, no page metadata --
        a lighter-weight alternative to Top/First when the limit is
        determined at runtime rather than fixed in the method name

 These parameters are always appended AFTER the regular filter parameters,
 and are excluded from the positional query-parameter binding (?1, ?2, ...)
 that the filter parameters use.
```

Because these are recognized by type rather than position-in-name, a method can mix ordinary filter parameters with any one of these special ones in the same signature, in the natural trailing position.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sort, Pageable, and Limit are recognized by parameter type and appended after the regular filter parameters">
  <rect x="10" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Sort</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ORDER BY only</text>

  <rect x="230" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Pageable</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">LIMIT + OFFSET + Sort</text>

  <rect x="450" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Limit</text>
  <text x="540" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">LIMIT only, runtime-set</text>

  <rect x="150" y="110" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">recognized by TYPE, appended after filter params</text>
</svg>

Each special type controls a different slice of query behavior — ordering, paging, or capping — independently addable to a method's signature.

## 5. Runnable example

The scenario: an `Article` search repository, evolving from `Sort`-controlled ordering, to `Pageable`-controlled full pagination, to `Limit` for a lightweight runtime-determined cap without page metadata overhead.

### Level 1 — Basic

Accept a `Sort` parameter alongside a filter argument, letting the caller choose the ordering at each call site.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class SpecialParamLevel1 {

    @Entity
    public static class Article {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String title;
        private String status;
        private int views;
        protected Article() {}
        public Article(String title, String status, int views) { this.title = title; this.status = status; this.views = views; }
        public String getTitle() { return title; }
        public int getViews() { return views; }
    }

    public interface ArticleRepository extends JpaRepository<Article, Long> {
        List<Article> findByStatus(String status, Sort sort); // caller controls the order
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecialParamLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:special1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ArticleRepository repo = ctx.getBean(ArticleRepository.class);
        repo.save(new Article("Intro to Spring", "published", 150));
        repo.save(new Article("Advanced Spring", "published", 400));
        repo.save(new Article("Spring Basics", "published", 90));

        List<Article> byViewsDesc = repo.findByStatus("published", Sort.by("views").descending());
        List<Article> byTitleAsc = repo.findByStatus("published", Sort.by("title").ascending());

        System.out.println("by views desc: " + byViewsDesc.stream().map(Article::getViews).toList());
        System.out.println("by title asc: " + byTitleAsc.stream().map(Article::getTitle).toList());

        if (byViewsDesc.get(0).getViews() != 400) throw new AssertionError("Expected the highest-view article first");
        if (!byTitleAsc.get(0).getTitle().equals("Advanced Spring")) throw new AssertionError("Expected alphabetically-first title first");
        System.out.println("Sort parameter let the caller choose ordering independently of the method name -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java SpecialParamLevel1.java` on JDK 17+.

`findByStatus(String status, Sort sort)` filters by `status` (a normal derived condition) and orders by whatever `Sort` the caller supplies — the same method produces two entirely different result orderings across the two calls, purely because a different `Sort` instance was passed each time, with no change to the method itself.

### Level 2 — Intermediate

Use `Pageable` for a fully paginated, sorted view — combining paging and ordering in one call via a single `PageRequest` argument.

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
import org.springframework.data.jpa.repository.JpaRepository;

@SpringBootApplication
public class SpecialParamLevel2 {

    @Entity
    public static class Article {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private int views;
        protected Article() {}
        public Article(String status, int views) { this.status = status; this.views = views; }
        public int getViews() { return views; }
    }

    public interface ArticleRepository extends JpaRepository<Article, Long> {
        Page<Article> findByStatus(String status, Pageable pageable);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecialParamLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:special2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ArticleRepository repo = ctx.getBean(ArticleRepository.class);
        for (int i = 1; i <= 12; i++) repo.save(new Article("published", i * 10));
        repo.save(new Article("draft", 5));

        Pageable request = PageRequest.of(0, 5, Sort.by("views").descending());
        Page<Article> page1 = repo.findByStatus("published", request);

        System.out.println("page 1: " + page1.getContent().stream().map(Article::getViews).toList());
        System.out.println("total published = " + page1.getTotalElements() + ", total pages = " + page1.getTotalPages());

        if (page1.getTotalElements() != 12) throw new AssertionError("Expected 12 published articles total");
        if (page1.getContent().size() != 5) throw new AssertionError("Expected page size 5");
        if (page1.getContent().get(0).getViews() != 120) throw new AssertionError("Expected the highest-view article first");
        System.out.println("Pageable combined paging + sorting in a single parameter -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java SpecialParamLevel2.java`.

`PageRequest.of(0, 5, Sort.by("views").descending())` bundles page number, page size, and sort order into one `Pageable` value — `findByStatus("published", request)` filters by status, applies that sort, and returns exactly one page's worth of results wrapped in `Page<Article>`, complete with `getTotalElements()`/`getTotalPages()` metadata computed via Spring Data's automatic accompanying count query (covered in an earlier paging card).

### Level 3 — Advanced

Use `Limit` for a runtime-determined result cap with no page metadata overhead, and compare it directly against a compile-time-fixed `Top5` method on the same data — showing when each approach is the better fit.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Limit;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class SpecialParamLevel3 {

    @Entity
    public static class Article {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private int views;
        protected Article() {}
        public Article(String status, int views) { this.status = status; this.views = views; }
        public int getViews() { return views; }
    }

    public interface ArticleRepository extends JpaRepository<Article, Long> {
        // Runtime-determined cap -- the caller decides "how many" at call time.
        List<Article> findByStatusOrderByViewsDesc(String status, Limit limit);

        // Compile-time-fixed cap -- ALWAYS exactly 5, baked into the method name.
        List<Article> findTop5ByStatusOrderByViewsDesc(String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpecialParamLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:special3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ArticleRepository repo = ctx.getBean(ArticleRepository.class);
        for (int i = 1; i <= 12; i++) repo.save(new Article("published", i * 10));

        // Simulate a user-configurable "show top N" setting, decided at runtime.
        int userConfiguredLimit = 3;
        List<Article> runtimeLimited = repo.findByStatusOrderByViewsDesc("published", Limit.of(userConfiguredLimit));
        List<Article> fixedTop5 = repo.findTop5ByStatusOrderByViewsDesc("published");

        System.out.println("runtime Limit.of(" + userConfiguredLimit + ") = " + runtimeLimited.stream().map(Article::getViews).toList());
        System.out.println("fixed Top5 = " + fixedTop5.stream().map(Article::getViews).toList());

        if (runtimeLimited.size() != 3) throw new AssertionError("Expected exactly 3 results from Limit.of(3)");
        if (fixedTop5.size() != 5) throw new AssertionError("Expected exactly 5 results from findTop5By...");
        if (runtimeLimited.get(0).getViews() != 120 || fixedTop5.get(0).getViews() != 120)
            throw new AssertionError("Expected both to start with the highest-view article");

        System.out.println("Limit (runtime cap) and Top5 (compile-time cap) both worked, at their own limits -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java SpecialParamLevel3.java`.

`findByStatusOrderByViewsDesc(String status, Limit limit)` accepts a `Limit` parameter — `Limit.of(userConfiguredLimit)` lets the actual cap be decided at runtime, from a variable, rather than fixed in the method's source code. `findTop5ByStatusOrderByViewsDesc(String status)` has its cap of `5` permanently baked into the method name — perfect for a genuinely fixed business rule ("always show exactly the top 5"), but unable to adapt to a runtime-configurable value the way `Limit` can. Both return a plain `List<T>`, unlike `Pageable`'s `Page<T>` — neither carries total-count metadata, since a "top N" query doesn't need to know how many rows exist beyond what was requested.

## 6. Walkthrough

Trace Level 3's `Limit`-based call.

1. **Startup — method resolution**: `PartTree` parses `findByStatusOrderByViewsDesc` into a filter condition (`status = ?1`) plus an ordering clause (`ORDER BY views DESC`) — exactly as any derived query would. Separately, Spring Data recognizes the trailing `Limit` parameter by its type, noting that this method's generated query should apply a result cap supplied at call time rather than a fixed one.
2. **Call**: `repo.findByStatusOrderByViewsDesc("published", Limit.of(3))` binds `"published"` as the filter parameter and reads `3` from the `Limit` instance as the cap — neither value collides with the other in positional binding, since `Limit` (like `Sort` and `Pageable`) is excluded from the regular `?1, ?2, ...` parameter sequence.
3. **Query execution**: H2 executes `SELECT a FROM Article a WHERE a.status = 'published' ORDER BY a.views DESC` with a `LIMIT 3` applied, returning the 3 highest-`views` published articles.
4. **Comparison call**: `repo.findTop5ByStatusOrderByViewsDesc("published")` executes conceptually the same query shape, but with its cap of `5` fixed at the method-name level rather than supplied as a parameter — no `Limit` argument exists on this method at all.
5. **Verification**: the program checks the runtime-limited call returned exactly 3 results and the fixed-`Top5` call returned exactly 5, and that both start with the same highest-`views` article (`120`), confirming both mechanisms correctly ordered and capped the same underlying data, just with the cap sourced differently — one from a runtime value, one from the method name itself.

```
 findByStatusOrderByViewsDesc("published", Limit.of(3))
        |
        v
 WHERE status='published' ORDER BY views DESC LIMIT 3   (3 -- from the Limit parameter, at call time)

 findTop5ByStatusOrderByViewsDesc("published")
        |
        v
 WHERE status='published' ORDER BY views DESC LIMIT 5   (5 -- fixed in the method name, at compile time)
```

## 7. Gotchas & takeaways

> **Gotcha:** a `Pageable` parameter changes what return type a method is expected to have (`Page<T>` to get count metadata, or `Slice<T>`/`List<T>` to skip the extra count query) — but `Sort` and `Limit` do not carry this expectation; they work equally well with a plain `List<T>` return type. Mixing these up (declaring a method with a `Pageable` parameter but a bare `List<T>` return type) still compiles and often still works, but silently loses the page-count metadata a `Page<T>` would have provided, which can be a confusing gap to debug later.

- `Sort`, `Pageable`, and `Limit` are recognized by Spring Data through their Java type, not through any keyword in the method name — this is what lets them be added to virtually any derived-query or `@Query` method as a trailing parameter.
- `Sort` controls ordering only; `Pageable` bundles ordering with page number and page size (and typically pairs with a `Page<T>` or `Slice<T>` return type); `Limit` controls only a result-count cap, with no offset or page metadata at all.
- `Limit` (introduced in Spring Data 3.2) is the right choice specifically when a result cap needs to be determined at runtime — `Top`/`First` keywords remain the right choice when the cap is a fixed, unchanging business rule that belongs directly in the method's name.
- All three special parameters are excluded from the regular positional parameter binding filter conditions use — they never collide with, or need to be counted alongside, the `?1`, `?2`, and so on that ordinary filter arguments bind to.
