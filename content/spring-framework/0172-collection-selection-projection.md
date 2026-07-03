---
card: spring-framework
gi: 172
slug: collection-selection-projection
title: "Collection selection & projection"
---

## 1. What it is

SpEL lets you filter and transform collections inline using two operators that parallel SQL `WHERE` and `SELECT`:

- **Selection** `.?[predicate]` — filters a collection to elements where the predicate is `true`. `#this` refers to the current element during evaluation.
- **Projection** `.![expression]` — maps each element to a new value. Again `#this` is the current element.
- **First-match** `.^[predicate]` — returns the *single* first element that satisfies the predicate.
- **Last-match** `.$[predicate]` — returns the *single* last element that satisfies the predicate.

```java
List<Integer> nums = List.of(1, 2, 3, 4, 5);
parser.parseExpression("#nums.?[#this % 2 == 0]").getValue(ctx, List.class); // [2, 4]
parser.parseExpression("#nums.![#this * #this]").getValue(ctx, List.class);  // [1, 4, 9, 16, 25]
```

Operators chain left-to-right: `books.?[price < 20].![title]` selects cheap books, then extracts only their titles.

## 2. Why & when

- **`@Value` on collections** — filter a bean's list property inline: `@Value("#{@catalog.books.?[price < 20].![title]}")` injects `List<String>` without any Java code.
- **Security trimming** — `items.?[owner == #currentUser]` strips items the caller doesn't own before sending to the view layer.
- **Config subsetting** — select only datasource beans with a given tag: `@datasources.?[environment == 'test']`.
- **Validation** — `orders.?[total < 0]` should be empty; if not, raise an alert.
- **Display projection** — convert a list of rich domain objects to display strings without a DTO: `users.![displayName + ' <' + email + '>']`.
- **Map slicing** — select entries from a `Map<String, T>` where the value meets a condition: `inventory.?[value > 100]` returns a sub-map.

## 3. Core concept

Both operators iterate the source collection. For each element they set `#this` to the element and evaluate the inner expression.

| Operator | Form | Returns | Behaviour |
|---|---|---|---|
| All-match selection | `.?[pred]` | `List` (or `Map` for Map sources) | every element where `pred == true` |
| First-match | `.^[pred]` | single element or **null** | first element where `pred == true` |
| Last-match | `.$[pred]` | single element or **null** | last element where `pred == true` |
| Projection | `.![expr]` | `List` | one transformed result per element |

**`Map` sources** — the "element" is a `Map.Entry`; use `key` and `value` properties directly in the predicate or expression (`inventory.?[value > 50]` returns a sub-`Map`; `inventory.![key + '=' + value]` returns a `List<String>`).

**Chaining** — each operator returns a new collection which becomes the source for the next operator. `books.?[price < 30].?[inStock].![title]` applies two filters then one projection in sequence. The original list is never modified.

**`#this` vs. root object** — when a root object is set, field names resolve against it directly; `#this` is only needed to make the element reference explicit, e.g. `#this.class.simpleName`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="sa172" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pa172" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Selection panel -->
  <rect x="8" y="8" width="320" height="224" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="168" y="28" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Selection  .?[predicate]</text>

  <!-- Input items (left column) -->
  <rect x="22" y="40" width="130" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="87" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Clean Code"  $18 ✓</text>
  <rect x="22" y="65" width="130" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1" opacity="0.6"/>
  <text x="87" y="79" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Eff. Java"  $45  ✗</text>
  <rect x="22" y="90" width="130" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="87" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Kubernetes"  $25 ✓</text>
  <rect x="22" y="115" width="130" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1" opacity="0.6"/>
  <text x="87" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Spring"  $55  ✗</text>
  <rect x="22" y="140" width="130" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="87" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Cloud Native"  $12 ✓</text>

  <!-- Arrow and label -->
  <line x1="157" y1="100" x2="178" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#sa172)"/>
  <text x="168" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.?[price&lt;30]</text>

  <!-- Output items (right column) -->
  <rect x="182" y="55" width="130" height="20" rx="3" fill="#6db33f" opacity="0.35"/>
  <text x="247" y="69" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Clean Code"  $18</text>
  <rect x="182" y="80" width="130" height="20" rx="3" fill="#6db33f" opacity="0.35"/>
  <text x="247" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Kubernetes"  $25</text>
  <rect x="182" y="105" width="130" height="20" rx="3" fill="#6db33f" opacity="0.35"/>
  <text x="247" y="119" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Cloud Native"  $12</text>

  <text x="168" y="182" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">only matching elements kept</text>
  <text x="168" y="197" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.^[price&lt;30] → first match ("Clean Code")</text>
  <text x="168" y="212" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.$[price&lt;30] → last  match ("Cloud Native")</text>

  <!-- Projection panel -->
  <rect x="342" y="8" width="350" height="224" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="517" y="28" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Projection  .![expression]</text>

  <!-- Source items -->
  <rect x="355" y="40" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.15"/>
  <text x="420" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Clean Code"  $18</text>
  <rect x="355" y="65" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.15"/>
  <text x="420" y="79" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Effective Java"  $45</text>
  <rect x="355" y="90" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.15"/>
  <text x="420" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Kubernetes"  $25</text>

  <line x1="490" y1="80" x2="510" y2="80" stroke="#79c0ff" stroke-width="2" marker-end="url(#pa172)"/>
  <text x="500" y="68" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">.![title]</text>

  <!-- Result items -->
  <rect x="514" y="40" width="162" height="20" rx="3" fill="#79c0ff" opacity="0.25"/>
  <text x="595" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Clean Code"</text>
  <rect x="514" y="65" width="162" height="20" rx="3" fill="#79c0ff" opacity="0.25"/>
  <text x="595" y="79" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Effective Java"</text>
  <rect x="514" y="90" width="162" height="20" rx="3" fill="#79c0ff" opacity="0.25"/>
  <text x="595" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"Kubernetes"</text>

  <text x="517" y="150" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">same count as input — every element transformed</text>
  <text x="517" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">element type can change (Book → String)</text>
  <text x="517" y="185" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">chain: .?[price&lt;30].![title] → filter THEN project</text>
  <text x="517" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Map .![key+'='+value] → List&lt;String&gt;</text>
  <text x="517" y="215" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">#this = current element in both operators</text>
</svg>

Selection keeps matching elements (same type, fewer count); projection transforms every element (same count, possibly different type). Chain them left-to-right to filter then reshape.

## 5. Runnable example

All three levels model a bookstore catalog — the same `Book` objects, the expressions growing in complexity.

### Level 1 — Basic

Selection and projection on a plain `List<Integer>`, then on simple Book records to establish the syntax.

```java
// SpelCollectionBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

public class SpelCollectionBasic {
    record Book(String title, double price) {}

    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx    = new StandardEvaluationContext();

        // --- integer selection & projection ---
        ctx.setVariable("nums", List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10));

        List<?> evens = parser.parseExpression("#nums.?[#this % 2 == 0]")
                              .getValue(ctx, List.class);
        System.out.println("Even:        " + evens);       // [2, 4, 6, 8, 10]

        List<?> squares = parser.parseExpression("#nums.![#this * #this]")
                                .getValue(ctx, List.class);
        System.out.println("Squares:     " + squares);     // [1, 4, 9, 16, 25, ...]

        Integer firstMod3 = parser.parseExpression("#nums.^[#this % 3 == 0]")
                                  .getValue(ctx, Integer.class);
        Integer lastMod3  = parser.parseExpression("#nums.$[#this % 3 == 0]")
                                  .getValue(ctx, Integer.class);
        System.out.println("First /3:    " + firstMod3);   // 3
        System.out.println("Last  /3:    " + lastMod3);    // 9

        // --- book selection & projection ---
        List<Book> books = List.of(
            new Book("Clean Code",    18.0),
            new Book("Eff. Java",     45.0),
            new Book("Kubernetes Up", 25.0),
            new Book("Spring Guide",  55.0),
            new Book("Cloud Native",  12.0)
        );
        ctx.setVariable("books", books);

        List<?> cheap = parser.parseExpression("#books.?[price < 30]")
                              .getValue(ctx, List.class);
        System.out.println("Cheap:       " + cheap);       // [Clean Code, Kubernetes Up, Cloud Native]

        List<?> titles = parser.parseExpression("#books.![title]")
                               .getValue(ctx, List.class);
        System.out.println("All titles:  " + titles);      // [Clean Code, Eff. Java, ...]

        // chain: select cheap, then project to title
        List<?> cheapTitles = parser.parseExpression("#books.?[price < 30].![title]")
                                    .getValue(ctx, List.class);
        System.out.println("Cheap titles:" + cheapTitles); // [Clean Code, Kubernetes Up, Cloud Native]
    }
}
```

How to run: `java SpelCollectionBasic.java`

`.?[price < 30]` filters `Book` records — the property `price` is resolved against each element via its getter `getPrice()`. `.![title]` creates a new `List<String>` by extracting the `title` field from each element. Chaining applies both in order: filter first, project the filtered result.

### Level 2 — Intermediate

Same bookstore — richer `Book` objects with category and stock, chained multi-condition selection, computed projection.

```java
// SpelCollectionIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Book2 {
    public final String title, category;
    public final double price;
    public final boolean inStock;
    Book2(String t, String c, double p, boolean s) {
        title=t; category=c; price=p; inStock=s;
    }
    public String getTitle()    { return title; }
    public String getCategory() { return category; }
    public double getPrice()    { return price; }
    public boolean isInStock()  { return inStock; }
    public String toString()    { return title + "($" + price + ")"; }
}

public class SpelCollectionIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx    = new StandardEvaluationContext();

        List<Book2> books = List.of(
            new Book2("Effective Java",        "Java",   45.0, true),
            new Book2("Clean Code",            "Java",   18.0, true),
            new Book2("Spring in Action",      "Spring", 55.0, false),
            new Book2("Cloud Native Patterns", "Cloud",  38.0, true),
            new Book2("Kubernetes Up",         "Cloud",  25.0, true),
            new Book2("Domain-Driven Design",  "Arch",   60.0, false)
        );
        ctx.setVariable("books", books);

        // Multi-condition selection
        List<?> inStockCloud = parser.parseExpression(
            "#books.?[inStock and category == 'Cloud']").getValue(ctx, List.class);
        System.out.println("In-stock Cloud: " + inStockCloud);
        // [Cloud Native Patterns($38.0), Kubernetes Up($25.0)]

        // Computed projection: discounted price string
        List<?> cloudSale = parser.parseExpression(
            "#books.?[inStock and category == 'Cloud'].![title + ' -> $' + (price * 0.9)]")
            .getValue(ctx, List.class);
        System.out.println("Cloud sale:     " + cloudSale);
        // [Cloud Native Patterns -> $34.2, Kubernetes Up -> $22.5]

        // Project a computed boolean column
        List<?> available = parser.parseExpression(
            "#books.![title + ': ' + (inStock ? 'AVAILABLE' : 'OUT')]")
            .getValue(ctx, List.class);
        System.out.println("Availability:   " + available);

        // First and last from filtered set
        Book2 cheapest = parser.parseExpression(
            "#books.^[price < 30]").getValue(ctx, Book2.class);
        Book2 lastExpensive = parser.parseExpression(
            "#books.$[price > 50]").getValue(ctx, Book2.class);
        System.out.println("First < $30:    " + cheapest);
        System.out.println("Last  > $50:    " + lastExpensive);

        // Double-filter: out-of-stock books over $50
        List<?> blocked = parser.parseExpression(
            "#books.?[!inStock].?[price > 50].![title]")
            .getValue(ctx, List.class);
        System.out.println("Blocked > $50:  " + blocked);
        // [Spring in Action, Domain-Driven Design]
    }
}
```

How to run: `java SpelCollectionIntermediate.java`

`inStock and category == 'Cloud'` — `and` is SpEL's keyword for logical AND (also accepts `&&`). The expression `(price * 0.9)` inside projection does arithmetic per element. Chaining `.?[].?[]` applies two selections sequentially — each selection returns a new list fed into the next. `.^[]` and `.$[]` always scan from the *beginning* or *end* of the collection they're called on.

### Level 3 — Advanced

`@Value` wiring with chained selection + projection, and `Map` selection — the full production scenario.

```java
// SpelCollectionAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class CatalogBook {
    private final String title, category;
    private final double price;
    CatalogBook(String t, String c, double p) { title=t; category=c; price=p; }
    public String getTitle()    { return title; }
    public String getCategory() { return category; }
    public double getPrice()    { return price; }
    public String toString()    { return title; }
}

class BookCatalog {
    private final List<CatalogBook> books;
    BookCatalog(List<CatalogBook> books) { this.books = books; }
    public List<CatalogBook> getBooks() { return books; }
}

@Configuration
class CatalogCfg {
    @Bean
    public BookCatalog catalog() {
        return new BookCatalog(List.of(
            new CatalogBook("Effective Java",   "Java",   45.0),
            new CatalogBook("Clean Code",       "Java",   18.0),
            new CatalogBook("Spring in Action", "Spring", 55.0),
            new CatalogBook("Cloud Native",     "Cloud",  38.0),
            new CatalogBook("Kubernetes Up",    "Cloud",  25.0)
        ));
    }
}

@org.springframework.stereotype.Component
class RecommendationService {
    // Select Java books under $30, project to titles
    @Value("#{@catalog.books.?[category == 'Java' and price < 30].![title]}")
    private List<String> budgetJavaTitles;

    // Project all books over $40 to "title ($price)"
    @Value("#{@catalog.books.?[price > 40].![title + ' ($' + price + ')']}")
    private List<String> premiumLabels;

    public void print() {
        System.out.println("Budget Java: " + budgetJavaTitles);
        System.out.println("Premium:     " + premiumLabels);
    }
}

public class SpelCollectionAdvanced {
    public static void main(String[] args) {
        // Spring context: @Value selection + projection
        var springCtx = new AnnotationConfigApplicationContext(
            CatalogCfg.class, RecommendationService.class);
        springCtx.getBean(RecommendationService.class).print();
        springCtx.close();

        // Map selection and projection
        var parser = new SpelExpressionParser();
        var ctx    = new StandardEvaluationContext();

        Map<String, Integer> inventory = new LinkedHashMap<>();
        inventory.put("Java",         150);
        inventory.put("Spring",        80);
        inventory.put("Kubernetes",   220);
        inventory.put("Cloud",         45);
        inventory.put("Architecture",  10);
        ctx.setVariable("inv", inventory);

        // Map selection: returns a sub-Map
        Map<?,?> highStock = parser.parseExpression("#inv.?[value > 100]")
                                   .getValue(ctx, Map.class);
        System.out.println("High stock:  " + highStock);   // {Java=150, Kubernetes=220}

        // Map projection: returns a List of transformed values
        List<?> summary = parser.parseExpression("#inv.![key + '=' + value]")
                                .getValue(ctx, List.class);
        System.out.println("Summary:     " + summary);
        // [Java=150, Spring=80, Kubernetes=220, Cloud=45, Architecture=10]

        // Select entries with key length > 5, project to key
        List<?> longKeys = parser.parseExpression(
            "#inv.?[key.length() > 5].![key]").getValue(ctx, List.class);
        System.out.println("Long keys:   " + longKeys);    // [Spring, Kubernetes, Architecture]
    }
}
```

How to run: `java SpelCollectionAdvanced.java`

`@Value("#{@catalog.books.?[category == 'Java' and price < 30].![title]}")` — Spring resolves `@catalog` to the `BookCatalog` bean, calls `.getBooks()`, runs selection, then projection, and injects the resulting `List<String>` directly — zero boilerplate. For `Map` sources: `.?[value > 100]` returns a sub-`Map` (matching entries); `.![key + '=' + value]` returns a `List<String>` — projection always returns a `List` regardless of source type.

## 6. Walkthrough

Tracing `#books.?[inStock and category == 'Cloud'].![title + ' -> $' + (price * 0.9)]` from Level 2 step by step.

**Entry point** — `parser.parseExpression(...)` builds an AST. `.getValue(ctx, List.class)` triggers evaluation.

**Step 1 — Resolve `#books`:** the variable lookup finds the `List<Book2>` (6 elements) bound in the context.

**Step 2 — Selection `.?[inStock and category == 'Cloud']`:**

SpEL creates an empty `ArrayList`. It iterates the list, setting `#this` = current element each time:

| # | `#this` | `inStock` | `category` | result |
|---|---|---|---|---|
| 1 | Effective Java | `true` | `"Java"` | `false` — skipped |
| 2 | Clean Code | `true` | `"Java"` | `false` — skipped |
| 3 | Spring in Action | `false` | `"Spring"` | `false` — skipped |
| 4 | Cloud Native Patterns | `true` | `"Cloud"` | **`true`** — added |
| 5 | Kubernetes Up | `true` | `"Cloud"` | **`true`** — added |
| 6 | Domain-Driven Design | `false` | `"Arch"` | `false` — skipped |

After selection: `[Cloud Native Patterns($38.0), Kubernetes Up($25.0)]`

**Step 3 — Projection `.![title + ' -> $' + (price * 0.9)]`:**

SpEL iterates the *filtered* list of 2 elements:

| # | `#this` | `title` | `price * 0.9` | result string |
|---|---|---|---|---|
| 1 | Cloud Native Patterns | `"Cloud Native Patterns"` | `34.2` | `"Cloud Native Patterns -> $34.2"` |
| 2 | Kubernetes Up | `"Kubernetes Up"` | `22.5` | `"Kubernetes Up -> $22.5"` |

**Final result:** `["Cloud Native Patterns -> $34.2", "Kubernetes Up -> $22.5"]`

<svg viewBox="0 0 700 130" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="wla" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wlb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <!-- Input -->
  <rect x="5" y="10" width="155" height="110" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="82" y="28" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Input: 6 books</text>
  <text x="82" y="45" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Effective Java</text>
  <text x="82" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Clean Code</text>
  <text x="82" y="71" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Spring in Action</text>
  <text x="82" y="84" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Cloud Native ✓</text>
  <text x="82" y="97" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes Up ✓</text>
  <text x="82" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Domain-Driven Design</text>

  <text x="200" y="58" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.?[inStock and</text>
  <text x="200" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">category=='Cloud']</text>
  <line x1="163" y1="65" x2="237" y2="65" stroke="#6db33f" stroke-width="2" marker-end="url(#wla)"/>

  <!-- Filtered -->
  <rect x="240" y="25" width="170" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="45" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Filtered: 2 books</text>
  <text x="325" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Cloud Native Patterns ($38)</text>
  <text x="325" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Kubernetes Up ($25)</text>

  <text x="448" y="55" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">.![title+</text>
  <text x="448" y="67" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">'->$'+(p*0.9)]</text>
  <line x1="413" y1="62" x2="482" y2="62" stroke="#79c0ff" stroke-width="2" marker-end="url(#wlb)"/>

  <!-- Projected -->
  <rect x="485" y="25" width="207" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="588" y="45" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Projected: 2 strings</text>
  <text x="588" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"Cloud Native Patterns -&gt; $34.2"</text>
  <text x="588" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"Kubernetes Up -&gt; $22.5"</text>
</svg>

Each step creates a new `ArrayList`; the original `books` list is never mutated. The projection step receives only the 2 filtered elements — `#this` within `.![]` is never bound to any of the 4 skipped books.

## 7. Gotchas & takeaways

> **`.^[]` and `.$[]` return `null` when no element matches** — they never throw. Guard downstream access: `books.^[price < 0]?.title ?: 'none'`. The all-match `.?[]` returns an empty `ArrayList` (never `null`), so it's safer to chain.

> **Elvis treats `0` as falsy, but `.?[count == 0]` does not.** A predicate is evaluated as a boolean expression, not an Elvis check — `count == 0` returns `true` when count is zero, which is what you want. The falsy rules only apply to the Elvis `?:` operator, not to `.?[]` predicates.

- `.?[]` on a **`List`/array** returns a `List`; on a **`Map`** returns a `Map` (sub-map with matching entries). Always match the `getValue` type argument accordingly.
- `.![]` always returns a `List` regardless of whether the source is a `List` or `Map`.
- Chaining creates intermediate `ArrayList` objects — for very large collections prefer Java streams in plain code; use SpEL chains in config/`@Value` where brevity matters more than throughput.
- `#this` is not needed when a root object is set and you access its properties directly: `parseExpression("books.?[price < 30]").getValue(catalog, List.class)` — but `#this` *is* needed when the collection holds primitive wrappers: `nums.?[#this > 5]`.
- Mutations to the returned `List` (add/remove) do not affect the source list — SpEL selection and projection always produce a *new* `ArrayList`.
