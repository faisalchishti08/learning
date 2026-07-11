---
card: spring-data
gi: 166
slug: cypher-dsl
title: "Cypher-DSL"
---

## 1. What it is

The Cypher-DSL is a Java library (bundled with Spring Data Neo4j) for building Cypher queries programmatically — chained Java method calls that generate valid Cypher text, instead of concatenating query strings by hand. It's the Neo4j-world equivalent of `Criteria`/`CriteriaQuery` from the JPA and Elasticsearch sections earlier in this course.

```java
Node customer = Cypher.node("Customer").named("c");
Statement statement = Cypher.match(customer)
    .where(customer.property("name").isEqualTo(Cypher.parameter("name")))
    .returning(customer)
    .build();
```

## 2. Why & when

Hand-written `@Query` Cypher strings (previous card) work well for fixed queries, but become awkward the moment a query's shape depends on runtime conditions — an optional filter, a dynamically chosen relationship type, a search form with several optional fields. String concatenation for that is exactly the fragile pattern `Criteria`/`CriteriaQuery` exist to replace elsewhere in this course.

Reach for the Cypher-DSL when:

- A query's `WHERE` clause has optional conditions that depend on which parameters were actually supplied.
- Building queries programmatically inside custom repository fragments, where composing Java objects is safer than composing strings.
- You want compile-time checking of query structure — the DSL's builder methods catch a class of mistakes a raw Cypher string only reveals at runtime.

## 3. Core concept

```
 Cypher DSL builder calls                       Generated Cypher

 Node c = Cypher.node("Customer").named("c");
 Cypher.match(c)
     .where(c.property("name").isEqualTo(...))    ->  MATCH (c:Customer)
     .returning(c)                                     WHERE c.name = $name
     .build()                                           RETURN c
```

Each DSL call corresponds to a fragment of Cypher text; the builder assembles them into one `Statement`, which Spring Data Neo4j then executes exactly like a hand-written `@Query`.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cypher-DSL builder calls assemble into a Statement which compiles to Cypher text executed against the graph">
  <rect x="20" y="20" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="130" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Cypher.match(c)</text>
  <text x="130" y="60" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">.where(...).returning(c)</text>

  <line x1="240" y1="47" x2="290" y2="47" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a5)"/>

  <rect x="300" y="20" width="140" height="55" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="52" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Statement</text>

  <line x1="440" y1="47" x2="490" y2="47" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a5)"/>

  <rect x="500" y="20" width="120" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="560" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Cypher text</text>

  <defs><marker id="a5" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A `Statement`, once built, compiles to Cypher text and executes the same way whether it came from the DSL or a hand-written string.

## 5. Runnable example

The scenario: building a customer search programmatically, evolving from a fixed-shape DSL query, to a query with an optional condition appended only when a parameter is present, to a fully dynamic query built from a multi-field search form.

### Level 1 — Basic

Model a fixed Cypher-DSL-style query as a small Java builder that assembles a `Statement` object, mirroring the DSL's builder API without pulling in the real dependency.

```java
import java.util.*;

public class CypherDslLevel1 {
    public static void main(String[] args) {
        Statement statement = MatchBuilder.match("Customer", "c")
            .where("c.name = $name")
            .returning("c")
            .build();

        System.out.println("Generated Cypher: " + statement.cypher);
    }
}

class Statement { String cypher; Statement(String cypher) { this.cypher = cypher; } }

// Stands in for org.neo4j.cypherdsl.core.Cypher's builder chain.
class MatchBuilder {
    private final String label, var;
    private String whereClause = null, returnClause = "*";
    private MatchBuilder(String label, String var) { this.label = label; this.var = var; }
    static MatchBuilder match(String label, String var) { return new MatchBuilder(label, var); }
    MatchBuilder where(String clause) { this.whereClause = clause; return this; }
    MatchBuilder returning(String var) { this.returnClause = var; return this; }
    Statement build() {
        StringBuilder sb = new StringBuilder("MATCH (" + var + ":" + label + ")");
        if (whereClause != null) sb.append(" WHERE ").append(whereClause);
        sb.append(" RETURN ").append(returnClause);
        return new Statement(sb.toString());
    }
}
```

How to run: `java CypherDslLevel1.java`

`MatchBuilder.match(...).where(...).returning(...).build()` mirrors the shape of the real Cypher-DSL's fluent API — each call appends a fragment, and `build()` assembles the final `Statement`, which is what gets handed to Neo4j for execution.

### Level 2 — Intermediate

Add an optional condition that's only appended when a parameter is actually supplied — the concrete problem the DSL solves better than string concatenation.

```java
import java.util.*;

public class CypherDslLevel2 {
    public static void main(String[] args) {
        System.out.println(buildSearch("Amara", null).cypher);
        System.out.println(buildSearch(null, "Lagos").cypher);
        System.out.println(buildSearch("Amara", "Lagos").cypher);
    }

    static Statement buildSearch(String name, String city) {
        MatchBuilder builder = MatchBuilder.match("Customer", "c");
        List<String> conditions = new ArrayList<>();
        if (name != null) conditions.add("c.name = $name");
        if (city != null) conditions.add("c.city = $city");
        if (!conditions.isEmpty()) builder.where(String.join(" AND ", conditions));
        return builder.returning("c").build();
    }
}

class Statement { String cypher; Statement(String cypher) { this.cypher = cypher; } }

class MatchBuilder {
    private final String label, var;
    private String whereClause = null, returnClause = "*";
    private MatchBuilder(String label, String var) { this.label = label; this.var = var; }
    static MatchBuilder match(String label, String var) { return new MatchBuilder(label, var); }
    MatchBuilder where(String clause) { this.whereClause = clause; return this; }
    MatchBuilder returning(String var) { this.returnClause = var; return this; }
    Statement build() {
        StringBuilder sb = new StringBuilder("MATCH (" + var + ":" + label + ")");
        if (whereClause != null) sb.append(" WHERE ").append(whereClause);
        sb.append(" RETURN ").append(returnClause);
        return new Statement(sb.toString());
    }
}
```

How to run: `java CypherDslLevel2.java`

`buildSearch` composes zero, one, or two `WHERE` conditions depending on which parameters are non-null, joined with `AND` only when needed — building this correctly by hand-concatenating raw Cypher strings, with correct spacing and `AND` placement in every combination, is exactly the error-prone work the DSL's builder pattern avoids.

### Level 3 — Advanced

Extend to a dynamic multi-field search covering a relationship condition too (customers who bought a given product), composing node patterns, relationship patterns, and conditions together — production-flavored, since real search forms rarely filter on just one entity's own properties.

```java
import java.util.*;

public class CypherDslLevel3 {
    public static void main(String[] args) {
        Map<String, Object> params1 = new HashMap<>();
        params1.put("name", "Amara");
        System.out.println(buildSearch(params1, null).cypher);

        Map<String, Object> params2 = new HashMap<>();
        params2.put("city", "Lagos");
        System.out.println(buildSearch(params2, "kettle").cypher);
    }

    static Statement buildSearch(Map<String, Object> properties, String boughtProduct) {
        MatchBuilder builder = MatchBuilder.match("Customer", "c");
        List<String> conditions = new ArrayList<>();
        for (String key : properties.keySet()) conditions.add("c." + key + " = $" + key);

        if (boughtProduct != null) {
            builder.relate("BOUGHT", "Product", "p", "name", boughtProduct);
        }
        if (!conditions.isEmpty()) builder.where(String.join(" AND ", conditions));
        return builder.returning("c").build();
    }
}

class Statement { String cypher; Statement(String cypher) { this.cypher = cypher; } }

class MatchBuilder {
    private final String label, var;
    private String whereClause = null, returnClause = "*";
    private String relationClause = "";
    private MatchBuilder(String label, String var) { this.label = label; this.var = var; }
    static MatchBuilder match(String label, String var) { return new MatchBuilder(label, var); }
    MatchBuilder where(String clause) { this.whereClause = clause; return this; }
    MatchBuilder returning(String var) { this.returnClause = var; return this; }
    // Composes an additional relationship pattern onto the match, e.g. -[:BOUGHT]->(p:Product {name:$name})
    MatchBuilder relate(String relType, String targetLabel, String targetVar, String propKey, Object propValue) {
        this.relationClause = "-[:" + relType + "]->(" + targetVar + ":" + targetLabel
            + " {" + propKey + ": $" + propKey + "})";
        return this;
    }
    Statement build() {
        StringBuilder sb = new StringBuilder("MATCH (" + var + ":" + label + ")" + relationClause);
        if (whereClause != null) sb.append(" WHERE ").append(whereClause);
        sb.append(" RETURN ").append(returnClause);
        return new Statement(sb.toString());
    }
}
```

How to run: `java CypherDslLevel3.java`

`relate(...)` appends a relationship pattern to the node pattern the same way `where(...)` appends a condition — the builder composes node patterns, relationship patterns, and filters independently, then assembles them in the correct Cypher order in `build()`, which is far safer than manually tracking clause ordering and parameter placeholders in a hand-built string.

## 6. Walkthrough

Execution starts in `main` for Level 3. The first call passes `{name: "Amara"}` with no `boughtProduct`, producing:

```
MATCH (c:Customer) WHERE c.name = $name RETURN c
```

The second call passes `{city: "Lagos"}` with `boughtProduct = "kettle"`. Inside `buildSearch`, the `relate(...)` call first appends the relationship pattern to `relationClause`, then the loop over `properties` builds the `WHERE` condition on `c.city`, and `build()` assembles both pieces in the correct order — node pattern, then relationship pattern, then `WHERE`, then `RETURN`:

```
MATCH (c:Customer)-[:BOUGHT]->(p:Product {name: $name}) WHERE c.city = $city RETURN c
```

Each of these `Statement` objects, once built, would be handed to Spring Data Neo4j's `Neo4jClient` for execution exactly like a hand-written `@Query` string — the DSL only changes *how* the Cypher text gets assembled, not how it runs. The request/response shape at execution time is identical to the previous card: parameters bound in, mapped `Customer` results out.

## 7. Gotchas & takeaways

> Gotcha: mixing raw string fragments back into a Cypher-DSL-built query (e.g. splicing unescaped user input into a condition string) reintroduces the exact injection risk the DSL exists to prevent — always bind dynamic *values* as parameters (`Cypher.parameter(...)`), never interpolate them directly into clause text.

> Gotcha: the real Cypher-DSL's `Statement` objects are immutable once built — calling further builder methods on an already-built statement doesn't mutate it, a common surprise for anyone used to a mutable `StringBuilder`-style API.

- The Cypher-DSL is to Cypher what `Criteria`/`CriteriaQuery` are to JPQL and Elasticsearch queries — a programmatic, composable alternative to raw query strings, useful once a query's shape becomes conditional.
- It shines specifically for optional conditions and dynamically composed relationship patterns, where string concatenation becomes error-prone.
- Values should always be bound as parameters, never spliced into clause text as raw strings, to avoid Cypher injection.
- A DSL-built `Statement` executes identically to a hand-written `@Query` string once compiled — the DSL only changes how the query text is assembled.
