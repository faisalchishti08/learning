---
card: spring-data
gi: 19
slug: limiting-query-results-first-top
title: "Limiting query results (First, Top)"
---

## 1. What it is

`First` and `Top` are query-derivation keywords (`Top` and `First` are synonyms — they behave identically) that cap the number of results a derived query returns, with an optional numeric suffix: `findFirstByStatus`, `findTop5ByStatus`, `findTop10ByOrderByCreatedAtDesc`. With no number, they default to `1`, returning a single result rather than a collection — a convenient shortcut for "give me just the most relevant match" queries.

```java
Optional<Order> findFirstByStatusOrderByCreatedAtDesc(String status); // the single latest one
List<Order> findTop5ByStatusOrderByCreatedAtDesc(String status);       // the 5 latest
```

## 2. Why & when

The previous cards on `Limit` and `Pageable` both cover result-count capping too, but `Top`/`First` differ in one important way: the cap is baked directly into the method name at compile time, making the intent ("this method always returns at most 5") self-documenting and impossible to accidentally bypass at a call site. That's exactly the right fit for genuinely fixed business rules — "the dashboard always shows the top 5 orders" — as opposed to `Limit`, which is the better fit when the cap needs to vary at runtime.

Reach for `Top`/`First` specifically when:

- The result-count cap is a permanent, unchanging business rule — "show the most recent order," "list the top 10 highest scorers" — that should be visible directly in the method's name and signature, not passed in as a parameter that could be forgotten or overridden.
- You want a single-result convenience method for "the most recent" or "the first matching" record, especially combined with `OrderBy` to make "most recent" or "first" concrete and unambiguous.
- You're choosing between `Top5`/`First` and a `Pageable`-based `PageRequest.of(0, 5, sort)` for the same fixed cap — `Top5` is simpler to call (no `Pageable` object to construct) and makes the cap visible in the method signature itself, at the cost of not being adjustable per call.

## 3. Core concept

```
 findFirstBy<Conditions>              -- returns AT MOST 1 result (no number needed)
 findTop1By<Conditions>               -- identical to findFirstBy (Top1 == First)
 findTop5By<Conditions>               -- returns AT MOST 5 results
 findFirst10By<Conditions>            -- returns AT MOST 10 results (First and Top are interchangeable)

 Return type pairing:
   No number (First/Top1)   -->  a single T, or Optional<T>
   With a number (TopN)      -->  List<T> (or another collection type)

 ALWAYS combine with OrderBy to make the "first N" deterministic --
 without an explicit order, "the first 5" depends on the store's
 unspecified natural row order, which may not be meaningful or stable.
```

`Top`/`First` are parsed by the same `PartTree` mechanism as every other derivation keyword — the numeric suffix (if present) becomes a `maxResults`/`LIMIT` value baked into the generated query template at startup.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Top and First keywords cap the result count at compile time, ideally paired with an explicit OrderBy for determinism">
  <rect x="10" y="20" width="270" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="145" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findTop5ByStatus(...)</text>
  <text x="145" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cap of 5, fixed at compile time</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">...OrderByCreatedAtDesc</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">makes "top 5" deterministic</text>
</svg>

`Top`/`First` alone caps the count; `OrderBy` alongside it determines which rows actually make the cut.

## 5. Runnable example

The scenario: an order-history lookup, evolving from `findFirstBy` for a single latest record, to `findTop5By` for a bounded recent-history list, to a comparison showing why omitting `OrderBy` produces a non-deterministic, easy-to-misuse result.

### Level 1 — Basic

Use `findFirstByStatusOrderByPlacedAtDesc` to fetch the single most recent order matching a status.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.Optional;

@SpringBootApplication
public class TopFirstLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private Instant placedAt;
        protected Order() {}
        public Order(String status, Instant placedAt) { this.status = status; this.placedAt = placedAt; }
        public Instant getPlacedAt() { return placedAt; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        Optional<Order> findFirstByStatusOrderByPlacedAtDesc(String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(TopFirstLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:topfirst1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Instant base = Instant.parse("2026-01-01T00:00:00Z");
        repo.save(new Order("shipped", base.plusSeconds(100)));
        repo.save(new Order("shipped", base.plusSeconds(300))); // most recent shipped
        repo.save(new Order("shipped", base.plusSeconds(200)));
        repo.save(new Order("cancelled", base.plusSeconds(500))); // most recent overall, but different status

        Optional<Order> mostRecentShipped = repo.findFirstByStatusOrderByPlacedAtDesc("shipped");
        System.out.println("most recent shipped order placedAt = " + mostRecentShipped.map(Order::getPlacedAt).orElse(null));

        if (mostRecentShipped.isEmpty() || !mostRecentShipped.get().getPlacedAt().equals(base.plusSeconds(300)))
            throw new AssertionError("Expected the order placed at +300s to be the most recent 'shipped' one");
        System.out.println("findFirstBy...OrderByDesc correctly returned exactly one, the most recent match -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java TopFirstLevel1.java` on JDK 17+.

`findFirstByStatusOrderByPlacedAtDesc(String status)` filters by `status`, orders by `placedAt` descending, and returns only the single first row of that ordered result — `Optional<Order>` because, like any single-result derived method, the match might not exist at all. The `"cancelled"` order, despite being placed later than every `"shipped"` order, is correctly excluded, since the `status` filter is applied before the `OrderBy`/limit.

### Level 2 — Intermediate

Use `findTop5By` for a bounded, ordered result list — a typical "recent activity" panel.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;

@SpringBootApplication
public class TopFirstLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String customerEmail;
        private Instant placedAt;
        protected Order() {}
        public Order(String customerEmail, Instant placedAt) { this.customerEmail = customerEmail; this.placedAt = placedAt; }
        public Instant getPlacedAt() { return placedAt; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        List<Order> findTop3ByCustomerEmailOrderByPlacedAtDesc(String email);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(TopFirstLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:topfirst2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        Instant base = Instant.parse("2026-01-01T00:00:00Z");
        for (int i = 1; i <= 7; i++) {
            repo.save(new Order("ada@example.com", base.plusSeconds(i * 100)));
        }
        repo.save(new Order("grace@example.com", base.plusSeconds(999))); // different customer

        List<Order> recentThree = repo.findTop3ByCustomerEmailOrderByPlacedAtDesc("ada@example.com");
        System.out.println("Ada's 3 most recent orders (of 7 total): " + recentThree.stream().map(Order::getPlacedAt).toList());

        if (recentThree.size() != 3) throw new AssertionError("Expected exactly 3 results, capped by Top3");
        if (!recentThree.get(0).getPlacedAt().equals(base.plusSeconds(700)))
            throw new AssertionError("Expected the most recent order (+700s) first");
        System.out.println("findTop3By...OrderByDesc capped and correctly ordered the result list -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java TopFirstLevel2.java`.

Ada has 7 orders, but `findTop3ByCustomerEmailOrderByPlacedAtDesc` returns exactly 3 — the cap of `3` (from `Top3`) is applied *after* filtering by `customerEmail` and ordering by `placedAt` descending, so the 3 returned are genuinely her 3 most recent, not an arbitrary 3 out of the 7.

### Level 3 — Advanced

Compare `findTop3By...` with and without an explicit `OrderBy`, demonstrating concretely why omitting the ordering makes the "top 3" result non-deterministic and dependent on unspecified database behavior.

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
public class TopFirstLevel3 {

    @Entity
    public static class Score {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String player;
        private int points;
        protected Score() {}
        public Score(String player, int points) { this.player = player; this.points = points; }
        public String getPlayer() { return player; }
        public int getPoints() { return points; }
    }

    public interface ScoreRepository extends JpaRepository<Score, Long> {
        // No explicit order -- relies on unspecified database/insertion-order behavior.
        List<Score> findTop3ByPointsGreaterThan(int threshold);

        // Explicit order -- deterministic: genuinely the 3 highest scores.
        List<Score> findTop3ByPointsGreaterThanOrderByPointsDesc(int threshold);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(TopFirstLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:topfirst3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        ScoreRepository repo = ctx.getBean(ScoreRepository.class);
        // Insert deliberately NOT in descending point order, to expose the difference.
        repo.save(new Score("Ada", 50));
        repo.save(new Score("Grace", 90));
        repo.save(new Score("Katherine", 70));
        repo.save(new Score("Margaret", 100));
        repo.save(new Score("Dorothy", 60));

        List<Score> unordered = repo.findTop3ByPointsGreaterThan(40);
        List<Score> ordered = repo.findTop3ByPointsGreaterThanOrderByPointsDesc(40);

        System.out.println("WITHOUT explicit OrderBy: " + unordered.stream().map(s -> s.getPlayer() + "=" + s.getPoints()).toList());
        System.out.println("WITH explicit OrderByPointsDesc: " + ordered.stream().map(s -> s.getPlayer() + "=" + s.getPoints()).toList());

        boolean orderedIsGenuinelyTopThree = ordered.stream().map(Score::getPoints).toList().equals(List.of(100, 90, 70));

        if (!orderedIsGenuinelyTopThree)
            throw new AssertionError("Expected the explicitly-ordered Top3 to be exactly the 3 highest scores: 100, 90, 70");
        System.out.println("Explicit OrderBy guaranteed a deterministic, genuinely-correct 'top 3'; unordered did not promise this -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java TopFirstLevel3.java`.

`findTop3ByPointsGreaterThan(int threshold)`, with no `OrderBy`, returns *some* 3 rows satisfying `points > threshold` — which 3, out of the 5 that qualify, depends entirely on unspecified row order (often insertion order for a simple table with no other index in play, but this is an implementation detail, not a guarantee). `findTop3ByPointsGreaterThanOrderByPointsDesc(int threshold)`, with the explicit order, is guaranteed to return the 3 *highest*-scoring qualifying players — `Margaret` (100), `Grace` (90), `Katherine` (70) — regardless of insertion order, database internals, or version.

## 6. Walkthrough

Trace the two `findTop3By...` calls in Level 3.

1. **`findTop3ByPointsGreaterThan(40)` resolution (startup)**: `PartTree` parses `Top3` as a limit of 3, `PointsGreaterThan` as the condition `points > ?1`, and — critically — no `OrderBy` segment at all. The generated query is `SELECT s FROM Score s WHERE s.points > ?1` with a `LIMIT 3` (via `setMaxResults(3)`), but with *no* `ORDER BY` clause.
2. **Execution**: H2 executes this query. Without an `ORDER BY`, the database is free to return matching rows in whatever order is most convenient for it — commonly (but not reliably) related to physical storage or insertion order for a simple, unindexed query like this one, and this can change entirely with a different query plan, a different database, or even a different H2 version.
3. **`findTop3ByPointsGreaterThanOrderByPointsDesc(40)` resolution (startup)**: `PartTree` parses the same limit and condition, plus `OrderByPointsDesc`, producing `SELECT s FROM Score s WHERE s.points > ?1 ORDER BY s.points DESC` with `LIMIT 3`.
4. **Execution**: H2 sorts all 5 qualifying rows by `points` descending *before* applying the limit, guaranteeing the 3 returned are genuinely the 3 highest — `Margaret` (100), `Grace` (90), `Katherine` (70), in that order.
5. **Comparison**: the program prints both results side by side — the ordered one is checked against the known-correct expected set `[100, 90, 70]`; the unordered one is printed for illustration only, with no correctness assertion made against it, since its correctness (or lack thereof) is exactly the point being demonstrated.
6. **Verification**: the assertion targets only the explicitly-ordered method's result, confirming it reliably identifies the true top 3 — the takeaway being that `Top`/`First` without an accompanying `OrderBy` should be treated as returning an unspecified subset of matches, not a meaningful "top" selection.

```
 findTop3ByPointsGreaterThan(40)              -- NO OrderBy
        |
        v
 WHERE points > 40  LIMIT 3   (no ORDER BY -- which 3 rows come back is unspecified)

 findTop3ByPointsGreaterThanOrderByPointsDesc(40)   -- WITH OrderBy
        |
        v
 WHERE points > 40  ORDER BY points DESC  LIMIT 3   -- guaranteed: the 3 highest scores
```

## 7. Gotchas & takeaways

> **Gotcha:** `Top`/`First` without an accompanying `OrderBy` compiles fine and often "happens to work" during development (since a simple, unindexed table frequently does return rows in insertion order in practice) — but this is never a guarantee the database makes, and it can silently change with a schema change, an added index, a query planner update, or a database migration. Any `Top`/`First` method intended to mean "the N most important/recent/highest" should always pair with an explicit `OrderBy`.

- `Top` and `First` are synonyms, both capping a derived query's result count — used with no number they default to a single result (paired with `Optional<T>` or a bare `T`); used with a number (`Top5`, `First10`) they cap a `List<T>`.
- Always pair `Top`/`First` with an explicit `OrderBy` when the selection is meant to represent "the most/least/highest/most-recent N" — without it, the specific N rows returned are database-implementation-dependent, not a guaranteed selection.
- `Top`/`First` are the right choice for genuinely fixed, unchanging caps that belong in the method's name (self-documenting, impossible to bypass at a call site) — the earlier card's `Limit` type is the better choice when the cap needs to vary per call, at runtime.
- Under the hood, `Top`/`First` are implemented via the same `LIMIT`/`setMaxResults` mechanism as `Pageable` and `Limit` — the difference is purely where the cap value comes from (the method name, versus a runtime parameter), not a fundamentally different execution strategy.
