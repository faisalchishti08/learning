---
card: spring-data
gi: 88
slug: schema-requirements-limitations-vs-jpa
title: "Schema requirements & limitations vs JPA"
---

## 1. What it is

This card is a direct, side-by-side comparison closing out the Spring Data JDBC section: what schema you must provide by hand (Spring Data JDBC has no schema-generation tool at all, unlike JPA's optional `ddl-auto`), and what capabilities JPA has that Spring Data JDBC deliberately omits — lazy loading, a persistence context, multi-level entity graphs, bidirectional relationships, and inheritance mapping strategies.

```java
// Spring Data JDBC: this schema must ALREADY exist before the app starts -- no auto-creation, ever.
// CREATE TABLE "order" (id BIGINT PRIMARY KEY, status VARCHAR(50));
// CREATE TABLE line_item ("order" BIGINT REFERENCES "order"(id), description VARCHAR(255));
```

## 2. Why & when

Every card in this section has, piece by piece, shown a simpler alternative to a JPA capability from the earlier section — this card makes the tradeoff explicit and complete, so choosing between the two modules for a new project (or explaining the choice already made) is a matter of checking this list rather than rediscovering each gap one bug at a time.

Reach for this comparison specifically when:

- Deciding between Spring Data JPA and Spring Data JDBC for a new project — the deciding factors are almost always on this list: do you need lazy loading, bidirectional relationships, or entity inheritance (JPA), or do you want simpler, more predictable, more explicit SQL behavior (JDBC)?
- Onboarding onto an existing Spring Data JDBC codebase coming from a JPA background — this list is the fastest way to recalibrate expectations about what "just works" automatically versus what needs to be handled explicitly.
- Explaining to a team why a particular feature request (e.g., "can we lazy-load this collection?") isn't straightforward in the current module — the answer is often "that's a JPA feature, not available here by design."

## 3. Core concept

```
                          Spring Data JPA                    Spring Data JDBC
 Schema:                  ddl-auto can generate it            must be written by hand, always
 Persistence context:     yes -- dirty checking, identity map  none -- every save/load is explicit
 Lazy loading:             yes, per association                none -- aggregates always load fully
 Bidirectional relations: yes (mappedBy)                       no -- aggregate references are one-directional
 Inheritance mapping:      yes (SINGLE_TABLE, JOINED, ...)      no built-in support
 Query language:           JPQL (portable) + native SQL         native SQL only
 Complexity/predictability: richer, more implicit               simpler, more explicit
```

Every capability JPA adds comes with corresponding implicit behavior (lazy loading timing, flush timing, cascade rules); Spring Data JDBC trades all of that away for a smaller, fully explicit surface.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="A feature comparison table contrasting Spring Data JPA's richer implicit behavior against Spring Data JDBC's simpler explicit model">
  <rect x="20" y="10" width="290" height="170" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data JPA</text>
  <text x="35" y="55" fill="#8b949e" font-size="8.5" font-family="sans-serif">+ ddl-auto schema generation</text>
  <text x="35" y="75" fill="#8b949e" font-size="8.5" font-family="sans-serif">+ persistence context, dirty checking</text>
  <text x="35" y="95" fill="#8b949e" font-size="8.5" font-family="sans-serif">+ lazy loading per association</text>
  <text x="35" y="115" fill="#8b949e" font-size="8.5" font-family="sans-serif">+ bidirectional relationships</text>
  <text x="35" y="135" fill="#8b949e" font-size="8.5" font-family="sans-serif">+ inheritance mapping strategies</text>
  <text x="35" y="155" fill="#8b949e" font-size="8.5" font-family="sans-serif">- more implicit, more "magic"</text>

  <rect x="330" y="10" width="290" height="170" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring Data JDBC</text>
  <text x="345" y="55" fill="#8b949e" font-size="8.5" font-family="sans-serif">- schema must be hand-written, always</text>
  <text x="345" y="75" fill="#8b949e" font-size="8.5" font-family="sans-serif">- no persistence context at all</text>
  <text x="345" y="95" fill="#8b949e" font-size="8.5" font-family="sans-serif">- no lazy loading, ever</text>
  <text x="345" y="115" fill="#8b949e" font-size="8.5" font-family="sans-serif">- one-directional aggregate references only</text>
  <text x="345" y="135" fill="#8b949e" font-size="8.5" font-family="sans-serif">- no built-in inheritance support</text>
  <text x="345" y="155" fill="#8b949e" font-size="8.5" font-family="sans-serif">+ simpler, fully explicit, predictable SQL</text>
</svg>

Each module's gains are the other's deliberate omissions — the choice is a tradeoff, not a strict upgrade in either direction.

## 5. Runnable example

The scenario: modeling the same order/line-item/customer domain, evolving from JPA-style code leaning on the features this card lists, to the Spring Data JDBC equivalent making every one of those omissions explicit, to a small decision-helper function summarizing which module fits a given set of requirements.

### Level 1 — Basic

Model a JPA-style approach relying on lazy loading and a persistence context, to have something concrete to contrast against.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

// JPA-style: lazy collection, populated on first access via a hidden proxy/query.
class Order {
    long id; String status;
    private List<LineItem> lineItems; // null until "lazily loaded"
    Order(long id, String status) { this.id = id; this.status = status; }

    // Simulates JPA's lazy-loading proxy: transparently fetches on first access.
    List<LineItem> getLineItems(Map<Long, List<LineItem>> lazySource) {
        if (lineItems == null) {
            System.out.println("  [lazy load triggered] fetching line items for order " + id);
            lineItems = lazySource.getOrDefault(id, List.of());
        }
        return lineItems;
    }
}

public class SchemaCompareLevel1 {
    public static void main(String[] args) {
        Map<Long, List<LineItem>> lazySource = Map.of(1L, List.of(new LineItem("Widget")));
        Order order = new Order(1, "PENDING"); // line items NOT loaded yet -- no query issued so far

        System.out.println("Order fetched, no line-item query issued yet.");
        List<LineItem> items = order.getLineItems(lazySource); // triggers the lazy load HERE, implicitly
        System.out.println("Now have " + items.size() + " line items, fetched on first access.");
    }
}
```

How to run: `java SchemaCompareLevel1.java`

The "Order fetched" line prints *before* any line-item query happens — the lazy load only triggers when `getLineItems` is actually called, an implicit behavior entirely dependent on where in the code that access happens; this is the lazy-loading convenience (and unpredictability) that JPA offers and Spring Data JDBC omits.

### Level 2 — Intermediate

Model the equivalent Spring Data JDBC approach: no lazy loading at all — the entire aggregate, including all line items, loads together, always, every time.

```java
import java.util.*;

class LineItem { String description; LineItem(String d) { description = d; } }

// Spring Data JDBC-style: an aggregate ALWAYS loads fully -- no lazy proxy, no partial state possible.
class Order {
    long id; String status;
    List<LineItem> lineItems; // ALWAYS populated by the time this object exists at all
    Order(long id, String status, List<LineItem> lineItems) { this.id = id; this.status = status; this.lineItems = lineItems; }
}

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    Optional<Order> findById(long id) {
        System.out.println("  SELECT * FROM \"order\" o LEFT JOIN line_item li ON li.\"order\" = o.id WHERE o.id = " + id);
        return Optional.ofNullable(db.get(id)); // the WHOLE aggregate, line items included, in ONE call
    }
}

public class SchemaCompareLevel2 {
    public static void main(String[] args) {
        OrderRepository repo = new OrderRepository();
        repo.db.put(1L, new Order(1, "PENDING", List.of(new LineItem("Widget"))));

        Order found = repo.findById(1L).orElseThrow(); // line items are ALREADY here, no separate step
        System.out.println("Order fetched WITH " + found.lineItems.size() + " line items, in the SAME call.");
    }
}
```

How to run: `java SchemaCompareLevel2.java`

There is no separate "lazy load triggered" moment — `found.lineItems` is already fully populated the instant `findById` returns, because Spring Data JDBC's aggregate model has no concept of partial loading at all: the whole `Order` aggregate, line items included, is fetched in one query, every single time, with no way to opt out.

### Level 3 — Advanced

Build a small decision-helper that recommends JPA or JDBC based on a checklist of requirements, encoding the tradeoffs from the concept section as executable logic.

```java
import java.util.*;

record ProjectRequirements(
    boolean needsLazyLoading,
    boolean needsBidirectionalRelationships,
    boolean needsEntityInheritance,
    boolean wantsAutoSchemaGeneration,
    boolean prioritizesSimplicityAndPredictability
) {}

public class SchemaCompareLevel3 {
    static String recommend(ProjectRequirements req) {
        List<String> jpaReasons = new ArrayList<>();
        if (req.needsLazyLoading()) jpaReasons.add("lazy loading");
        if (req.needsBidirectionalRelationships()) jpaReasons.add("bidirectional relationships");
        if (req.needsEntityInheritance()) jpaReasons.add("entity inheritance mapping");
        if (req.wantsAutoSchemaGeneration()) jpaReasons.add("automatic schema generation (ddl-auto)");

        if (!jpaReasons.isEmpty()) {
            return "Spring Data JPA -- required because of: " + String.join(", ", jpaReasons);
        }
        if (req.prioritizesSimplicityAndPredictability()) {
            return "Spring Data JDBC -- no JPA-specific feature needed, and simplicity/predictability is a stated priority";
        }
        return "Either could work -- no JPA-specific feature is required; JDBC is the simpler default unless other factors favor JPA";
    }

    public static void main(String[] args) {
        ProjectRequirements richDomainModel = new ProjectRequirements(true, true, false, true, false);
        ProjectRequirements simpleAggregateService = new ProjectRequirements(false, false, false, false, true);
        ProjectRequirements neutralCase = new ProjectRequirements(false, false, false, false, false);

        System.out.println("Rich domain model with bidirectional associations: " + recommend(richDomainModel));
        System.out.println("Simple, predictable aggregate service: " + recommend(simpleAggregateService));
        System.out.println("No strong requirements either way: " + recommend(neutralCase));
    }
}
```

How to run: `java SchemaCompareLevel3.java`

`recommend` mechanically applies the tradeoff checklist from the concept section: any genuine need for a JPA-specific feature (lazy loading, bidirectional relationships, inheritance, auto-schema) routes to JPA regardless of other preferences, since Spring Data JDBC simply doesn't offer those; only when none of those apply does the simplicity/predictability preference (or an even split) decide the recommendation.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `richDomainModel` is constructed with `needsLazyLoading=true`, `needsBidirectionalRelationships=true`, `wantsAutoSchemaGeneration=true`, and `prioritizesSimplicityAndPredictability=false`. `recommend(richDomainModel)` runs: the `jpaReasons` list collects `"lazy loading"`, `"bidirectional relationships"`, and `"automatic schema generation (ddl-auto)"` (each added because its corresponding boolean is `true`); since this list isn't empty, the method returns immediately with "Spring Data JPA -- required because of: lazy loading, bidirectional relationships, automatic schema generation (ddl-auto)" — the `prioritizesSimplicityAndPredictability` flag is never even consulted, because a genuine JPA-only requirement takes precedence.

Next, `simpleAggregateService` is constructed with every JPA-specific flag `false` and `prioritizesSimplicityAndPredictability=true`. `recommend` finds `jpaReasons` empty (none of the four JPA-specific booleans are `true`), so it falls through to the `prioritizesSimplicityAndPredictability` check, which is `true` — returning "Spring Data JDBC -- no JPA-specific feature needed, and simplicity/predictability is a stated priority".

Finally, `neutralCase` has every flag `false`, including `prioritizesSimplicityAndPredictability`. `recommend` again finds `jpaReasons` empty, then finds the simplicity check also `false`, falling through to the final catch-all return: "Either could work -- no JPA-specific feature is required; JDBC is the simpler default unless other factors favor JPA".

```
richDomainModel:         jpaReasons=[lazy loading, bidirectional, auto-schema] -> JPA (reasons override everything)
simpleAggregateService:  jpaReasons=[] , prioritizesSimplicity=true             -> JDBC
neutralCase:              jpaReasons=[] , prioritizesSimplicity=false           -> "either could work"
```

In practice, this same decision plays out at the architecture stage of a real project: a team modeling a domain with genuinely complex, deeply bidirectional object graphs and needing the database schema to evolve automatically during development would reach for Spring Data JPA and accept its complexity; a team building a set of well-bounded aggregate services (in the DDD sense from the very first card of this section) that values predictable, fully-visible SQL over rich object-graph convenience would reach for Spring Data JDBC and write their schema by hand (typically via Flyway/Liquibase migrations) from the start.

## 7. Gotchas & takeaways

> Gotcha: it's possible (and sometimes appropriate) to use *both* modules in the same application for different parts of the domain — a complex, deeply-relational subdomain via Spring Data JPA, and simpler, well-bounded aggregates via Spring Data JDBC — but this adds genuine operational complexity (two different persistence mechanisms, two different sets of assumptions to keep straight) and should be a deliberate architectural decision, not an accident of different teams choosing differently without coordinating.

- Spring Data JDBC has no schema-generation tool at all — the database schema must always be created by hand or via a migration tool, unlike JPA's optional `ddl-auto`.
- JPA-exclusive features include lazy loading, a persistence context (dirty checking, identity map), bidirectional relationships, and entity inheritance mapping strategies — none of these exist in Spring Data JDBC by design.
- Spring Data JDBC's tradeoff is a smaller, fully explicit feature set in exchange for simpler, more predictable behavior with no hidden queries or deferred writes.
- Choosing between the two modules should be driven by which specific JPA-only features (if any) the domain genuinely requires — not by default habit or familiarity alone.
