---
card: spring-data
gi: 15
slug: supported-keywords-and-or-between-lessthan-like-in-etc
title: "Supported keywords (And, Or, Between, LessThan, Like, In, etc.)"
---

## 1. What it is

This card is the reference for the full vocabulary of keywords `PartTree` recognizes when parsing a derived query method name: combinators (`And`, `Or`), comparisons (`Between`, `LessThan`, `LessThanEqual`, `GreaterThan`, `GreaterThanEqual`, `After`, `Before`), null checks (`IsNull`, `IsNotNull`), string matching (`Like`, `NotLike`, `Containing`, `StartingWith`, `EndingWith`), membership (`In`, `NotIn`), boolean checks (`True`, `False`), and negation (`Not`) — the complete grammar behind every derived method used throughout this section.

```java
List<Product> findByPriceBetween(double min, double max);
List<Product> findByNameContainingIgnoreCase(String part);
List<Product> findByCategoryIn(List<String> categories);
List<Product> findByDiscontinuedFalse();
```

## 2. Why & when

Earlier cards in this section used several of these keywords individually without cataloging the full set — this card exists as the complete reference so a derived method name's capability isn't guessed at or under-utilized. Knowing the full vocabulary changes the calculus of "is this simple enough for derivation, or do I need `@Query`" — many queries that look like they'd need a hand-written query are actually directly expressible once the full keyword set is known.

This reference matters specifically when:

- You're writing a new finder and aren't sure whether a particular comparison (a range, a substring match, a set-membership check) has a derivation keyword — checking this list first can save reaching for `@Query` unnecessarily.
- You're reading an unfamiliar derived method name and need to decode exactly what it does — recognizing each keyword segment is the skill this reference builds.
- You're deciding between two equivalent-looking keywords — `Like` versus `Containing`, for instance — and need to know the precise difference (covered in the runnable example below).

## 3. Core concept

```
 COMBINATORS:        And, Or

 COMPARISON:         (none, implicit equals)
                      Between, LessThan, LessThanEqual, GreaterThan, GreaterThanEqual
                      After, Before          (date/time-oriented aliases for GreaterThan/LessThan)
                      IsNull, IsNotNull (or just Null / NotNull)

 STRING MATCHING:     Like, NotLike           -- raw LIKE pattern, YOU supply % wildcards
                      Containing / Contains   -- auto-wraps the value: %value%
                      StartingWith            -- auto-wraps: value%
                      EndingWith              -- auto-wraps: %value

 COLLECTION:          In, NotIn               -- parameter is a Collection

 BOOLEAN:             True, False             -- for a boolean property, no parameter needed

 NEGATION:            Not                     -- e.g. findByStatusNot(...)

 MODIFIERS (appended, combinable with the above):
   IgnoreCase          -- case-insensitive comparison
   OrderBy...Asc/Desc  -- result ordering (covered in an earlier card)
```

`Like` requires the caller to supply wildcard characters (`%`) explicitly in the argument; `Containing`/`StartingWith`/`EndingWith` add them automatically — a frequent source of confusion when a `Like` query "doesn't match anything" because the caller forgot the `%`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Like requires explicit wildcards from the caller, while Containing, StartingWith, and EndingWith add them automatically">
  <rect x="10" y="20" width="290" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findByNameLike("%wid%")</text>
  <text x="155" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">caller supplies the % wildcards</text>

  <rect x="340" y="20" width="290" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findByNameContaining("wid")</text>
  <text x="485" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Data adds %...% automatically</text>

  <rect x="150" y="110" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="monospace">both produce: WHERE name LIKE '%wid%'</text>
</svg>

`Like` and `Containing` can produce identical SQL, but only one of them adds the wildcards for you.

## 5. Runnable example

The scenario: a product search repository, evolving from basic comparison and string-matching keywords, to `In`/boolean/negation keywords, to a combined realistic filter using several keywords together, including the `Like`-versus-`Containing` distinction made concrete.

### Level 1 — Basic

Use `Between`, `GreaterThan`, and `Containing` — the most commonly reached-for comparison and string-matching keywords.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class KeywordsLevel1 {

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

    public interface ProductRepository extends JpaRepository<Product, Long> {
        List<Product> findByPriceBetween(double min, double max);
        List<Product> findByPriceGreaterThan(double min);
        List<Product> findByNameContaining(String part);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(KeywordsLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:kw1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", 9.99));
        repo.save(new Product("Super Widget", 29.99));
        repo.save(new Product("Gadget", 49.99));

        List<Product> midRange = repo.findByPriceBetween(9.0, 30.0);
        List<Product> expensive = repo.findByPriceGreaterThan(30.0);
        List<Product> widgets = repo.findByNameContaining("Widget");

        System.out.println("mid-range (9-30) = " + midRange.size());
        System.out.println("expensive (>30) = " + expensive.size());
        System.out.println("containing 'Widget' = " + widgets.size());

        if (midRange.size() != 2) throw new AssertionError("Expected 2 products in the 9-30 range");
        if (expensive.size() != 1) throw new AssertionError("Expected 1 product over 30");
        if (widgets.size() != 2) throw new AssertionError("Expected 2 products containing 'Widget'");
        System.out.println("Between, GreaterThan, and Containing all resolved correctly -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java KeywordsLevel1.java` on JDK 17+.

`findByPriceBetween(min, max)` translates to `WHERE price BETWEEN ?1 AND ?2` (inclusive on both ends). `findByNameContaining("Widget")` automatically wraps the argument, producing `WHERE name LIKE '%Widget%'` — the caller passes the bare substring, with no `%` characters of their own.

### Level 2 — Intermediate

Use `In` for set-membership, `False`/`True` for boolean properties (with no parameter at all), and `Not` for negation.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class KeywordsLevel2 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String category;
        private boolean discontinued;
        protected Product() {}
        public Product(String name, String category, boolean discontinued) {
            this.name = name; this.category = category; this.discontinued = discontinued;
        }
        public String getName() { return name; }
        public String getCategory() { return category; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        List<Product> findByCategoryIn(List<String> categories);
        List<Product> findByDiscontinuedFalse();
        List<Product> findByCategoryNot(String category);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(KeywordsLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:kw2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget", "tools", false));
        repo.save(new Product("Gadget", "electronics", true));
        repo.save(new Product("Gizmo", "electronics", false));
        repo.save(new Product("Old Tool", "tools", true));

        List<Product> toolsOrElectronics = repo.findByCategoryIn(List.of("tools", "electronics"));
        List<Product> active = repo.findByDiscontinuedFalse();
        List<Product> notTools = repo.findByCategoryNot("tools");

        System.out.println("tools or electronics = " + toolsOrElectronics.size());
        System.out.println("active (not discontinued) = " + active.size());
        System.out.println("not tools = " + notTools.size());

        if (toolsOrElectronics.size() != 4) throw new AssertionError("Expected all 4 products to match In(tools, electronics)");
        if (active.size() != 2) throw new AssertionError("Expected 2 non-discontinued products");
        if (notTools.size() != 2) throw new AssertionError("Expected 2 products not in 'tools'");
        System.out.println("In, False, and Not keywords all resolved correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java KeywordsLevel2.java`.

`findByCategoryIn(List<String> categories)` translates to `WHERE category IN (?1)`, accepting a `Collection` parameter directly. `findByDiscontinuedFalse()` needs no parameter at all — the keyword `False` itself supplies the comparison value for the boolean `discontinued` property. `findByCategoryNot("tools")` translates to `WHERE category <> ?1`.

### Level 3 — Advanced

Combine several keywords in one realistic filter method, and demonstrate the `Like`-versus-`Containing` distinction directly by showing `Like` fails to match without explicit wildcards, while `Containing` succeeds with the same bare input.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class KeywordsLevel3 {

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String category;
        private double price;
        private boolean discontinued;
        protected Product() {}
        public Product(String name, String category, double price, boolean discontinued) {
            this.name = name; this.category = category; this.price = price; this.discontinued = discontinued;
        }
        public String getName() { return name; }
    }

    public interface ProductRepository extends JpaRepository<Product, Long> {
        List<Product> findByNameLike(String pattern); // caller must supply % wildcards
        List<Product> findByNameContaining(String part); // auto-wraps with %

        // A realistic combined filter: category match AND price range AND not discontinued.
        List<Product> findByCategoryAndPriceBetweenAndDiscontinuedFalse(String category, double min, double max);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(KeywordsLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:kw3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ProductRepository repo = ctx.getBean(ProductRepository.class);
        repo.save(new Product("Widget Pro", "tools", 25.0, false));
        repo.save(new Product("Widget Basic", "tools", 8.0, false));
        repo.save(new Product("Old Widget", "tools", 15.0, true)); // discontinued
        repo.save(new Product("Gadget", "electronics", 20.0, false));

        List<Product> likeWithoutWildcards = repo.findByNameLike("Widget"); // no % -- exact match only
        List<Product> containingBareWord = repo.findByNameContaining("Widget"); // auto-wrapped

        System.out.println("findByNameLike('Widget') [no wildcards] = " + likeWithoutWildcards.size());
        System.out.println("findByNameContaining('Widget') = " + containingBareWord.size());

        List<Product> combined = repo.findByCategoryAndPriceBetweenAndDiscontinuedFalse("tools", 10.0, 30.0);
        System.out.println("tools, 10-30, active = " + combined.stream().map(Product::getName).toList());

        if (!likeWithoutWildcards.isEmpty())
            throw new AssertionError("Expected findByNameLike('Widget') with no wildcards to match nothing (exact match only)");
        if (containingBareWord.size() != 3)
            throw new AssertionError("Expected findByNameContaining('Widget') to match all 3 'Widget'-named products");
        if (combined.size() != 1 || !combined.get(0).getName().equals("Widget Pro"))
            throw new AssertionError("Expected only 'Widget Pro' to satisfy all three combined conditions");

        System.out.println("Like vs Containing distinction, and a 3-keyword combined filter, both worked -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java KeywordsLevel3.java`.

`findByNameLike("Widget")` with no `%` wildcards in the argument produces `WHERE name LIKE 'Widget'` — an exact match, since a bare `LIKE` pattern with no wildcard characters behaves identically to `=`. None of the three "Widget"-containing product names equal exactly `"Widget"`, so this returns zero results. `findByNameContaining("Widget")`, given the identical bare argument `"Widget"`, automatically produces `WHERE name LIKE '%Widget%'`, correctly matching all three. The combined method chains three keywords (`And` twice) into one query, correctly narrowing to exactly the one product satisfying all three conditions simultaneously.

## 6. Walkthrough

Trace the `Like`-versus-`Containing` comparison specifically, since it's the most commonly misunderstood pair in this keyword set.

1. **Startup — `findByNameLike` resolution**: `PartTree` recognizes the `Like` keyword and builds a query template `WHERE p.name LIKE ?1` — critically, the parameter is bound *exactly as passed*, with no modification to the argument string.
2. **Startup — `findByNameContaining` resolution**: `PartTree` recognizes the `Containing` keyword and builds a template that, at call time, wraps the bound parameter with `%` on both sides before binding it — effectively `WHERE p.name LIKE CONCAT('%', ?1, '%')`.
3. **Call: `findByNameLike("Widget")`**: the literal string `"Widget"` (no wildcards) is bound directly to the `LIKE` clause, producing `WHERE p.name LIKE 'Widget'` — SQL's `LIKE` operator without any `%` or `_` wildcard characters behaves exactly like `=`, so this only matches a product named *exactly* `"Widget"`. None of the three seeded products are named exactly that (they're `"Widget Pro"`, `"Widget Basic"`, `"Old Widget"`), so the result is empty.
4. **Call: `findByNameContaining("Widget")`**: the same literal string `"Widget"` is passed, but `Containing`'s auto-wrapping produces `WHERE p.name LIKE '%Widget%'` — a genuine substring match, correctly matching all three "Widget"-containing product names.
5. **Combined filter call**: `findByCategoryAndPriceBetweenAndDiscontinuedFalse("tools", 10.0, 30.0)` produces `WHERE category = ?1 AND price BETWEEN ?2 AND ?3 AND discontinued = false`, evaluated against all four products — only `"Widget Pro"` (tools, 25.0, not discontinued) satisfies every condition simultaneously; `"Widget Basic"` fails the price range (8.0 < 10.0), and `"Old Widget"` fails the discontinued check.
6. **Verification**: the program checks all three result sets, confirming the `Like`/`Containing` distinction produced the expected different outcomes for identical input, and the combined filter correctly narrowed to exactly one matching product.

```
 findByNameLike("Widget")        -->  WHERE name LIKE 'Widget'         --> 0 matches (exact only)
 findByNameContaining("Widget")  -->  WHERE name LIKE '%Widget%'       --> 3 matches (substring)
                                              ^
                                   Containing added the % automatically;
                                   Like used the argument exactly as given
```

## 7. Gotchas & takeaways

> **Gotcha:** `findByNameLike(pattern)` gives the caller full control over `LIKE` wildcard placement (useful for prefix-only or suffix-only matches by supplying `"Widget%"` or `"%Widget"` manually), but it's easy to forget the wildcards are the *caller's* responsibility with `Like` — passing a bare substring, expecting `Containing`-style automatic wrapping, silently produces an exact-match query that returns nothing. When in doubt about which keyword auto-wraps, `Containing`/`StartingWith`/`EndingWith` are the safer, more explicit choices for substring searches.

- The full derivation keyword vocabulary — combinators, comparisons, string matching, membership, boolean checks, and negation — covers the overwhelming majority of everyday filtering needs without writing a query string by hand.
- `Like` requires the caller to supply any `%`/`_` wildcards explicitly; `Containing`, `StartingWith`, and `EndingWith` add the appropriate wildcards automatically — these are not interchangeable despite sometimes producing identical SQL for particular inputs.
- `True`/`False` keywords need no method parameter at all, since the keyword itself supplies the comparison value for a boolean property.
- Multiple keywords combine freely via `And`/`Or` into a single method name, as the three-condition combined filter in Level 3 demonstrated — there's no hard limit on how many conditions a derived method can express, though readability degrades well before any technical limit is reached.
