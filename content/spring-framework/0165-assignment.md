---
card: spring-framework
gi: 165
slug: assignment
title: "Assignment"
---

## 1. What it is

SpEL supports writing values back to a target object's property, array element, list slot, or map entry using the assignment operator `=` inside an expression or via the `setValue` method on an `Expression`. The expression on the left side must resolve to a settable location (a property with a setter, a public field, an indexed slot, or a map entry).

```java
Expression expr = parser.parseExpression("name");
expr.setValue(ctx, "Alice");                        // sets root.name = "Alice"

parser.parseExpression("address.city = 'Boston'").getValue(ctx); // setValue inline
parser.parseExpression("scores[1] = 99").getValue(ctx);          // list/array slot
```

## 2. Why & when

- **Mutation via expression string** — update nested fields of a domain object without knowing its concrete type at the call site.
- **Rule engines** — configuration-driven field assignment: `"penalty = baseAmount * rate"` reads from context and writes back to the root object.
- **Test data setup** — quickly seed object graphs without builder boilerplate.
- **Spring Data SpEL projections** — projection interfaces use `@Value("#{target.fieldName}")` for computed property reads; writes are less common.
- **`DataBinder` integration** — internally SpEL assignment drives some write-path operations in Spring's binding infrastructure.

## 3. Core concept

Two ways to assign:

| Approach | Syntax | Description |
|---|---|---|
| `setValue(ctx, value)` | programmatic | call `Expression.setValue` with context + value |
| `= operator` in expression | inline | embed assignment in expression string |

Left-hand side requirements — the LHS must be one of:
- A property path (`name`, `address.city`) that resolves to a JavaBeans setter or writable public field.
- An index expression (`list[0]`, `map['key']`, `arr[2]`).
- A combination: `orders[0].status`.

`setValue` is also available directly on `ExpressionParser` as `parser.parseExpression(lhs).setValue(ctx, value)`. The `=` operator inside an expression string evaluates the RHS and calls `setValue` on the LHS path — the expression result is the assigned value.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg">
  <!-- Root object -->
  <rect x="10" y="20" width="180" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Root Object</text>
  <line x1="18" y1="48" x2="182" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="100" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">String name = "Alice"</text>
  <text x="100" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Address address.city = "NY"</text>
  <text x="100" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">List&lt;String&gt; tags[0]="v1"</text>
  <text x="100" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Map meta['k']="val"</text>
  <text x="100" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">int[] scores[2]=30</text>

  <!-- Assignment paths -->
  <rect x="250" y="20" width="230" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="365" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Assignment expressions</text>
  <line x1="258" y1="48" x2="472" y2="48" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="365" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">expr.setValue(ctx, "Alice")</text>
  <text x="365" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"address.city = 'NY'"</text>
  <text x="365" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"tags[0] = 'v2'"</text>
  <text x="365" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"meta['k'] = 'newval'"</text>
  <text x="365" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"scores[2] = 30"</text>
  <text x="365" y="136" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">requires setter / writable field / mutable slot</text>

  <!-- PropertyAccessor chain -->
  <rect x="540" y="45" width="152" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="616" y="64"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">PropertyAccessor</text>
  <text x="616" y="79"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">canWrite(ctx, target, name)</text>
  <text x="616" y="93"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">write(ctx, target, name, val)</text>
  <text x="616" y="107" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ calls setter / sets field</text>

  <defs>
    <marker id="a165" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="192" y1="85" x2="247" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a165)"/>
  <line x1="482" y1="85" x2="537" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a165)"/>
</svg>

SpEL assignment routes through `PropertyAccessor.write()` — calling JavaBeans setters or directly writing fields.

## 5. Runnable example

### Level 1 — Basic

`setValue` on simple and nested properties.

```java
// SpelAssignmentBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Person {
    private String name;
    private int age;
    private Address address;

    Person(String name, int age, Address address) {
        this.name = name; this.age = age; this.address = address;
    }
    public String getName()       { return name; }
    public int getAge()           { return age; }
    public Address getAddress()   { return address; }
    public void setName(String v) { this.name = v; }
    public void setAge(int v)     { this.age = v; }
}

class Address {
    public String city;
    public String zip;
    Address(String city, String zip) { this.city = city; this.zip = zip; }
    public String getCity() { return city; }
    public String getZip()  { return zip; }
    public void setCity(String v) { this.city = v; }
}

public class SpelAssignmentBasic {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();
        Person person = new Person("Alice", 30, new Address("Boston", "02101"));
        ctx.setRootObject(person);

        // Read before
        System.out.println("Before: " + person.getName() + ", " + person.getAge() + ", " + person.getAddress().getCity());

        // setValue via Expression object
        parser.parseExpression("name").setValue(ctx, "Bob");
        parser.parseExpression("age").setValue(ctx, 35);

        // setValue via inline = operator in expression
        parser.parseExpression("address.city = 'New York'").getValue(ctx);

        System.out.println("After: " + person.getName() + ", " + person.getAge() + ", " + person.getAddress().getCity());
        // After: Bob, 35, New York

        // Assignment returns the assigned value
        Object returned = parser.parseExpression("name = 'Charlie'").getValue(ctx);
        System.out.println("Returned: " + returned);  // Charlie
        System.out.println("Confirmed: " + person.getName()); // Charlie
    }
}
```

How to run: `java SpelAssignmentBasic.java`

The `=` operator in a SpEL expression string assigns and also returns the assigned value. `parser.parseExpression("name").setValue(ctx, "Bob")` is equivalent to `parser.parseExpression("name = 'Bob'").getValue(ctx)`.

### Level 2 — Intermediate

Assignment to list slots, map entries, and array elements.

```java
// SpelAssignmentIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Config {
    public List<String> tags;
    public Map<String, Object> props;
    public int[] values;

    Config(List<String> tags, Map<String, Object> props, int[] values) {
        this.tags = tags; this.props = props; this.values = values;
    }
    public List<String> getTags()         { return tags; }
    public Map<String, Object> getProps() { return props; }
    public int[] getValues()              { return values; }
}

public class SpelAssignmentIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        Config cfg = new Config(
            new ArrayList<>(List.of("v1", "v2", "v3")),
            new HashMap<>(Map.of("timeout", 30, "retry", 3)),
            new int[]{10, 20, 30});
        ctx.setRootObject(cfg);

        System.out.println("Before tags:   " + cfg.getTags());
        System.out.println("Before props:  " + cfg.getProps());
        System.out.println("Before values: " + Arrays.toString(cfg.getValues()));

        // List slot
        parser.parseExpression("tags[0] = 'v1-updated'").getValue(ctx);
        parser.parseExpression("tags[2]").setValue(ctx, "v3-updated");

        // Map entry
        parser.parseExpression("props['timeout'] = 60").getValue(ctx);
        parser.parseExpression("props['maxRetries']").setValue(ctx, 5); // new key

        // Array element
        parser.parseExpression("values[1] = 99").getValue(ctx);

        System.out.println("After tags:    " + cfg.getTags());
        System.out.println("After props:   " + cfg.getProps());
        System.out.println("After values:  " + Arrays.toString(cfg.getValues()));

        // Chained: compute then assign
        ctx.setVariable("scale", 2);
        parser.parseExpression("values[2] = values[2] * #scale").getValue(ctx);
        System.out.println("Scaled[2]: " + cfg.getValues()[2]); // 60
    }
}
```

How to run: `java SpelAssignmentIntermediate.java`

`props['maxRetries']` adds a new map entry when the key doesn't exist. List slot assignment via `list[n] =` calls `List.set(n, value)` — the list must be mutable (`ArrayList`, not `List.of()`). Array assignment directly sets the element.

### Level 3 — Advanced

Multi-step assignment chain; `setValue` in a loop; deep nested path assignment.

```java
// SpelAssignmentAdvanced.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Department {
    public String name;
    public List<String> members = new ArrayList<>();
    public Map<String, Integer> budget = new HashMap<>();
    Department(String name) { this.name = name; }
    public String getName()                   { return name; }
    public void setName(String v)             { this.name = v; }
    public List<String> getMembers()          { return members; }
    public Map<String, Integer> getBudget()   { return budget; }
}

class Company {
    public Map<String, Department> departments = new HashMap<>();
    public String ceo;
    Company(String ceo) { this.ceo = ceo; }
    public String getCeo()                  { return ceo; }
    public void setCeo(String v)            { this.ceo = v; }
    public Map<String, Department> getDepartments(){ return departments; }
}

public class SpelAssignmentAdvanced {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        Company co = new Company("Alice");
        Department eng = new Department("Engineering");
        eng.members.addAll(List.of("Bob", "Carol", "Dave"));
        eng.budget.put("q1", 100_000);
        co.departments.put("eng", eng);

        ctx.setRootObject(co);

        // Deep nested assignment
        parser.parseExpression("ceo = 'Eve'").getValue(ctx);
        parser.parseExpression("departments['eng'].name = 'Platform Engineering'").getValue(ctx);
        parser.parseExpression("departments['eng'].members[0] = 'Robert'").getValue(ctx);
        parser.parseExpression("departments['eng'].budget['q2'] = 120000").getValue(ctx);

        System.out.println("ceo:     " + co.getCeo());
        System.out.println("dept:    " + eng.getName());
        System.out.println("member:  " + eng.getMembers());
        System.out.println("budget:  " + eng.getBudget());

        // Batch assignment via a loop: increase all budget entries by 10%
        Map<String, Expression> assignments = Map.of(
            "departments['eng'].budget['q1']",
                parser.parseExpression("departments['eng'].budget['q1'] * 1.10"),
            "departments['eng'].budget['q2']",
                parser.parseExpression("departments['eng'].budget['q2'] * 1.10"));

        assignments.forEach((path, valueExpr) -> {
            Object newVal = valueExpr.getValue(ctx);
            parser.parseExpression(path).setValue(ctx, newVal);
        });

        System.out.println("Updated budget: " + eng.getBudget());

        ctx.close();
    }
}
```

How to run: `java SpelAssignmentAdvanced.java`

`departments['eng'].budget['q2'] = 120000` chains map access → property → map assignment. Batch assignment combines read expressions and `setValue` calls: read the new value with one expression, write it with another path expression.

## 6. Walkthrough

Execution for `"departments['eng'].members[0] = 'Robert'"`:

1. SpEL parses: `Assign(Indexer(0, PropertyOrFieldRef(members, PropertyOrFieldRef(departments['eng']))), 'Robert')`.
2. Evaluate LHS chain to locate writable target:
   - `departments` → `Map<String, Department>`.
   - `['eng']` → `Department eng`.
   - `members` → `List<String>`.
   - `[0]` → index 0 slot.
3. `PropertyAccessor.write` for a list index calls `list.set(0, "Robert")`.
4. Original `"Bob"` replaced by `"Robert"`.
5. Expression returns assigned value `"Robert"`.

## 7. Gotchas & takeaways

> Assignment via SpEL requires the target to be **mutable**. Trying to `setValue` on an unmodifiable list (from `List.of()` or `Collections.unmodifiableList()`) throws `UnsupportedOperationException` at runtime. Always use `ArrayList`, `HashMap`, or other mutable collections for mutable paths.

> The `=` operator inside a SpEL expression is **not guarded by `SimpleEvaluationContext.forReadOnlyDataBinding()`** — but the context created by `forReadWriteDataBinding()` is needed. `forReadOnlyDataBinding()` makes `canWrite` return `false`, causing `setValue` to throw. Check which context you configure when allowing user-supplied expressions.

- `setValue(ctx, value)` uses `ConversionService` for type coercion. Setting a `double` field with an `Integer` value works because Spring coerces it. Explicitly typed values avoid ambiguity.
- A failed assignment (no setter, read-only field, immutable collection) throws `SpelEvaluationException` with message `"setValueInternal"` — check the full stack trace for the property path.
- Assignments in `@Value` expressions are executed once at bean initialization and are not reactive — the field does not update when the root object changes later.
