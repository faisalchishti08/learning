---
card: spring-framework
gi: 161
slug: properties-arrays-lists-maps-indexers
title: "Properties, arrays, lists, maps, indexers"
---

## 1. What it is

SpEL provides uniform syntax for navigating object graphs: dot notation for property access and method calls, bracket notation `[n]` for arrays and list indexing, and `['key']` for map access. All forms can be chained: `order.items[0].name`, `config['db']['host']`.

```java
ExpressionParser parser = new SpelExpressionParser();
StandardEvaluationContext ctx = new StandardEvaluationContext(order);
parser.parseExpression("customer.name").getValue(ctx);           // property chain
parser.parseExpression("items[0]").getValue(ctx);                // list index
parser.parseExpression("meta['region']").getValue(ctx, String.class); // map key
```

## 2. Why & when

- **Object graph traversal** — extract deeply nested values from domain objects without writing intermediate accessor code.
- **`@Value` binding** — `@Value("#{config.database.host}")` navigates a nested Spring bean; `@Value("#{settings['timeout']}")` reads a `Map` bean entry.
- **Dynamic indexing** — `items[#idx]` uses a variable as the index, enabling runtime-driven data extraction.
- **Safe navigation** — `order?.customer?.address?.city` avoids `NullPointerException` through deep chains.

## 3. Core concept

| Syntax | Resolves via | Example |
|---|---|---|
| `obj.prop` | `getProperty()` / public field | `customer.name` |
| `obj.method()` | reflected method call | `name.toUpperCase()` |
| `arr[n]` | array element at index | `scores[2]` |
| `list[n]` | `List.get(n)` | `items[0]` |
| `map['key']` | `Map.get("key")` | `meta['region']` |
| `map[key]` | `Map.get(key)` (key is a variable/property) | `meta[regionVar]` |
| `obj?.prop` | safe — returns null if `obj` is null | `order?.customer?.name` |

Index expressions can be nested: `matrix[0][1]` for a 2-D array; `departments['eng'].members[0].name` for a deeply nested map + list + object chain.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg">
  <!-- Object graph -->
  <rect x="10" y="20" width="160" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Order (root)</text>
  <line x1="20" y1="48" x2="160" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="90" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">customer.name</text>
  <text x="90" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">customer.address.city</text>
  <text x="90" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">items[0]</text>
  <text x="90" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">items[items.size()-1]</text>
  <text x="90" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">meta['region']</text>
  <text x="90" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">items[0].name</text>
  <text x="90" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">order?.customer?.name</text>

  <!-- Resolver box -->
  <rect x="230" y="50" width="210" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="70"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">PropertyAccessor chain</text>
  <line x1="240" y1="78" x2="430" y2="78" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="335" y="92"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ReflectivePropertyAccessor (JavaBeans)</text>
  <text x="335" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CompilableMapAccessor</text>
  <text x="335" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ListAccessor / ArrayIndexer</text>
  <text x="335" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">custom PropertyAccessor</text>

  <!-- Results -->
  <rect x="500" y="20" width="190" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="40"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Result</text>
  <line x1="510" y1="48" x2="680" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="595" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Alice"</text>
  <text x="595" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Boston"</text>
  <text x="595" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Item@{name="Widget"}</text>
  <text x="595" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Item@{name="Gadget"}</text>
  <text x="595" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"EMEA"</text>
  <text x="595" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Widget"</text>
  <text x="595" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">null (safe nav)</text>

  <defs>
    <marker id="a161" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="172" y1="90" x2="227" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a161)"/>
  <line x1="442" y1="95" x2="497" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#a161)"/>
</svg>

SpEL resolves property and index access via a `PropertyAccessor` chain; safe navigation `?.` short-circuits on null.

## 5. Runnable example

### Level 1 — Basic

Properties, array, list, and map indexing on simple domain objects.

```java
// SpelIndexersBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Address { public String city, zip;
    Address(String c, String z) { this.city = c; this.zip = z; } }
class Item { public String name; public double price;
    Item(String n, double p) { this.name = n; this.price = p; } }
class Order {
    public String id;
    public Address shippingAddress;
    public List<Item> items;
    public Map<String, String> meta;
    public int[] scores;

    Order(String id, Address addr, List<Item> items, Map<String, String> meta, int[] scores) {
        this.id = id; this.shippingAddress = addr;
        this.items = items; this.meta = meta; this.scores = scores;
    }
}

public class SpelIndexersBasic {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        Order order = new Order(
            "ORD-100",
            new Address("Seattle", "98101"),
            List.of(new Item("Widget", 9.99), new Item("Gadget", 29.99), new Item("Doohickey", 4.99)),
            Map.of("region", "WEST", "tier", "premium"),
            new int[]{10, 20, 30, 40});

        ctx.setRootObject(order);

        // Property chain
        System.out.println(parser.parseExpression("id").getValue(ctx));
        System.out.println(parser.parseExpression("shippingAddress.city").getValue(ctx));
        System.out.println(parser.parseExpression("shippingAddress.zip").getValue(ctx));

        // List index
        System.out.println(parser.parseExpression("items[0].name").getValue(ctx));    // Widget
        System.out.println(parser.parseExpression("items[2].price").getValue(ctx));   // 4.99
        System.out.println(parser.parseExpression("items.size()").getValue(ctx));     // 3

        // Map access
        System.out.println(parser.parseExpression("meta['region']").getValue(ctx));   // WEST
        System.out.println(parser.parseExpression("meta['tier']").getValue(ctx));     // premium

        // Array index
        System.out.println(parser.parseExpression("scores[0]").getValue(ctx));        // 10
        System.out.println(parser.parseExpression("scores[3]").getValue(ctx));        // 40

        // Dynamic index via variable
        ctx.setVariable("idx", 1);
        System.out.println(parser.parseExpression("items[#idx].name").getValue(ctx)); // Gadget
    }
}
```

How to run: `java SpelIndexersBasic.java`

`items[0].name` chains list indexing with property access. `meta['region']` uses the string literal as a map key. `scores[#idx]` uses a variable as the runtime index.

### Level 2 — Intermediate

Deep nesting, `items.size() - 1` as computed index, safe navigation on null.

```java
// SpelIndexersIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Tag { public String name; public String color;
    Tag(String n, String c) { this.name = n; this.color = c; } }
class Department {
    public String name;
    public List<Tag> tags;
    public Map<String, Integer> stats;
    Department(String n, List<Tag> t, Map<String, Integer> s) {
        this.name = n; this.tags = t; this.stats = s; }
}
class Company {
    public String name;
    public Map<String, Department> departments;
    Company(String n, Map<String, Department> d) { this.name = n; this.departments = d; }
}

public class SpelIndexersIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        Company co = new Company("Acme", Map.of(
            "eng", new Department("Engineering",
                List.of(new Tag("backend", "blue"), new Tag("frontend", "green")),
                Map.of("headcount", 45, "openRoles", 3)),
            "mktg", new Department("Marketing",
                List.of(new Tag("digital", "orange")),
                Map.of("headcount", 12, "openRoles", 1))));

        ctx.setRootObject(co);

        // Deep map + property chain
        System.out.println(parser.parseExpression("departments['eng'].name").getValue(ctx));
        System.out.println(parser.parseExpression("departments['eng'].tags[0].name").getValue(ctx)); // backend
        System.out.println(parser.parseExpression("departments['eng'].stats['headcount']").getValue(ctx)); // 45

        // Computed index: last element
        System.out.println(parser.parseExpression(
            "departments['eng'].tags[departments['eng'].tags.size() - 1].name").getValue(ctx)); // frontend

        // Safe navigation on potentially null key
        System.out.println(parser.parseExpression("departments['hr']?.name").getValue(ctx)); // null (no NPE)
        System.out.println(parser.parseExpression("departments['hr']?.stats?.get('headcount')").getValue(ctx)); // null

        // Cross-department comparison via map
        ctx.setVariable("dept", "mktg");
        System.out.println(parser.parseExpression("departments[#dept].stats['headcount']").getValue(ctx)); // 12
    }
}
```

How to run: `java SpelIndexersIntermediate.java`

Computed index `tags[tags.size() - 1]` evaluates the sub-expression inside brackets as a regular SpEL expression. `departments['hr']?.name` returns `null` because the key `'hr'` does not exist and `?.` short-circuits safely.

### Level 3 — Advanced

2-D array, nested maps, `setValue` via indexer, `@Value` usage.

```java
// SpelIndexersAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

@Configuration
class GridCfg {
    @Bean("grid")
    public int[][] grid() {
        return new int[][]{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
    }

    @Bean("config")
    public Map<String, Map<String, Object>> config() {
        return Map.of(
            "db", Map.of("host", "db.prod", "port", 5432),
            "cache", Map.of("host", "cache.prod", "ttl", 300));
    }
}

@org.springframework.stereotype.Component
class InfraSettings {
    @Value("#{grid[1][2]}")     // row 1, col 2 → 6
    private int gridCell;

    @Value("#{config['db']['host']}")
    private String dbHost;

    @Value("#{config['cache']['ttl']}")
    private int cacheTtl;

    public int getGridCell()  { return gridCell; }
    public String getDbHost() { return dbHost; }
    public int getCacheTtl()  { return cacheTtl; }
}

public class SpelIndexersAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(GridCfg.class, InfraSettings.class);
        var settings = ctx.getBean(InfraSettings.class);
        System.out.println("gridCell: " + settings.getGridCell()); // 6
        System.out.println("dbHost:   " + settings.getDbHost());   // db.prod
        System.out.println("cacheTtl: " + settings.getCacheTtl()); // 300

        // Runtime setValue on a mutable list
        var evalCtx = new StandardEvaluationContext();
        List<String> tags = new ArrayList<>(List.of("alpha", "beta", "gamma"));
        evalCtx.setRootObject(tags);
        var parser = new SpelExpressionParser();

        System.out.println("Before: " + tags);
        parser.parseExpression("[1]").setValue(evalCtx, "BETA");  // replace index 1
        System.out.println("After:  " + tags); // [alpha, BETA, gamma]

        ctx.close();
    }
}
```

How to run: `java SpelIndexersAdvanced.java`

`@Value("#{grid[1][2]}")` accesses a 2-D array bean — row 1, column 2 = `6`. `@Value("#{config['db']['host']}")` traverses a nested `Map<String, Map<String, Object>>`. `[1].setValue(evalCtx, "BETA")` mutates the list element at index 1 via SpEL.

## 6. Walkthrough

Execution for `"departments['eng'].tags[0].name"` in Level 2:

1. AST: `PropertyOrFieldReference(name)` → `Indexer(0)` → `PropertyOrFieldReference(tags)` → `Indexer('eng')` → `PropertyOrFieldReference(departments)`.
2. Evaluation (right to left in AST, left to right in reading): resolve `departments` on root `Company` → `Map<String, Department>`.
3. `['eng']` → `Map.get("eng")` → `Department("Engineering", ...)`.
4. `.tags` → `Department.tags` → `List<Tag>`.
5. `[0]` → `List.get(0)` → `Tag("backend", "blue")`.
6. `.name` → `Tag.name` → `"backend"`.

## 7. Gotchas & takeaways

> `map[key]` where `key` is an unquoted identifier resolves `key` as a property or variable of the root object, NOT as a string. Use `map['key']` for literal string map keys. Using `map[key]` when you mean `map['key']` causes subtle bugs that are hard to diagnose.

> Array and list indexers are bounds-checked; an out-of-bounds index throws `EvaluationException`, not `ArrayIndexOutOfBoundsException`. Catch `EvaluationException` in code that uses user-provided index values.

- `list[list.size() - 1]` is the idiomatic way to access the last element. SpEL does not have a `last` keyword or negative indexing.
- Map keys of non-String types work: `map[42]` finds the entry with Integer key `42`. SpEL uses `equals()` for key lookup, matching Java `Map.get()` behavior.
- Property access via `obj.name` tries `getName()` first (JavaBeans), then falls back to public field access. If neither exists, `EvaluationException` is thrown.
