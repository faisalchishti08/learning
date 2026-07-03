---
card: spring-framework
gi: 162
slug: inline-lists-maps
title: "Inline lists & maps"
---

## 1. What it is

SpEL supports constructing `java.util.List` and `java.util.Map` instances directly inside an expression using brace syntax. Inline lists use `{e1, e2, ...}`; inline maps use `{key1: val1, key2: val2, ...}`. Elements can be literals, variables, or sub-expressions.

```java
parser.parseExpression("{1, 2, 3}").getValue();                  // List [1, 2, 3]
parser.parseExpression("{'a', 'b', 'c'}").getValue();            // List [a, b, c]
parser.parseExpression("{name: 'Alice', age: 30}").getValue();   // Map {name=Alice, age=30}
```

## 2. Why & when

- **`@Value` constants** — `@Value("#{{'read', 'write', 'admin'}}")` injects a `List<String>` without a bean definition.
- **Default fallback sets** — use inline lists as defaults in Elvis expressions: `config.allowedRoles ?: {'user', 'guest'}`.
- **Quick maps in tests** — construct expected maps inline for assertion expressions.
- **Collection filters on inline data** — filter an inline list directly: `{10, 20, 30}.?[#this > 15]`.

## 3. Core concept

| Syntax | Result type | Example |
|---|---|---|
| `{}`  | `Collections.emptyList()` | empty list |
| `{1, 2, 3}` | `List<Integer>` | `[1, 2, 3]` |
| `{'a', 'b'}` | `List<String>` | `[a, b]` |
| `{1, 'two', true}` | `List<Object>` | mixed types |
| `{:}` | `Collections.emptyMap()` | empty map |
| `{k: v, k2: v2}` | `Map<Object, Object>` | map literal |
| `{k: {1,2,3}}` | `Map` with `List` value | nested |
| `{{1,2},{3,4}}` | `List<List<Integer>>` | nested list |

Keys in inline maps are SpEL expressions (can be literals or variables). Inline lists and maps are **immutable** — produced by `Collections.unmodifiableList` / `Collections.unmodifiableMap`. Write to them via `setValue` throws `UnsupportedOperationException`.

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="15" width="320" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="36" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Inline List  {e1, e2, ...}</text>
  <line x1="20" y1="44" x2="320" y2="44" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="170" y="59"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{1, 2, 3}         → [1, 2, 3]</text>
  <text x="170" y="73"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{'red','green'}    → [red, green]</text>
  <text x="170" y="87"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{{1,2},{3,4}}      → [[1,2],[3,4]]</text>
  <text x="170" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{}.class.name      → java.util.Collections$EmptyList</text>
  <text x="170" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{1,2,3}.?[#this>1] → [2, 3]</text>
  <text x="170" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Result: unmodifiable List</text>

  <rect x="370" y="15" width="320" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="36" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Inline Map  {key: val, ...}</text>
  <line x1="380" y1="44" x2="680" y2="44" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="530" y="59"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{:}                  → {}</text>
  <text x="530" y="73"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{'a':1,'b':2}         → {a=1, b=2}</text>
  <text x="530" y="87"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{'roles':{1,2,3}}     → {roles=[1,2,3]}</text>
  <text x="530" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{#var: 'val'}         → {resolved key: val}</text>
  <text x="530" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{'k':'v'}.get('k')    → v</text>
  <text x="530" y="132" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Result: unmodifiable Map</text>
</svg>

Inline `{}` constructs immutable lists; `{k:v}` constructs immutable maps — elements are SpEL sub-expressions.

## 5. Runnable example

### Level 1 — Basic

Construct and inspect inline lists and maps.

```java
// SpelInlineCollectionsBasic.java
import org.springframework.expression.spel.standard.*;
import java.util.*;

public class SpelInlineCollectionsBasic {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        // Inline lists
        System.out.println(p.parseExpression("{1, 2, 3}").getValue());
        System.out.println(p.parseExpression("{'alpha', 'beta', 'gamma'}").getValue());
        System.out.println(p.parseExpression("{}").getValue());              // empty list
        System.out.println(p.parseExpression("{true, false, true}").getValue());

        // Nested list
        System.out.println(p.parseExpression("{{1,2},{3,4},{5,6}}").getValue()); // [[1,2],[3,4],[5,6]]

        // Inline maps
        System.out.println(p.parseExpression("{:}").getValue());             // empty map
        System.out.println(p.parseExpression("{'host':'localhost','port':5432}").getValue());
        System.out.println(p.parseExpression("{'active':true,'count':0}").getValue());

        // Access element of inline collection
        System.out.println(p.parseExpression("{'a','b','c'}[1]").getValue()); // b
        System.out.println(p.parseExpression("{'x':10,'y':20}['x']").getValue()); // 10

        // Type
        System.out.println(p.parseExpression("{1,2,3}").getValueType()); // List type
        System.out.println(p.parseExpression("{:}").getValueType());      // Map type
    }
}
```

How to run: `java SpelInlineCollectionsBasic.java`

`{}` evaluates to an empty list, not an empty map. `{:}` is the empty map syntax. Inline collections support immediate indexing: `{'a','b','c'}[1]` → `"b"`.

### Level 2 — Intermediate

Inline list with filter/projection; inline map with dynamic keys from variables.

```java
// SpelInlineCollectionsIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

public class SpelInlineCollectionsIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();
        ctx.setVariable("min", 15);
        ctx.setVariable("region", "WEST");

        // Filter inline list: elements > #min
        System.out.println(parser.parseExpression("{5, 10, 20, 30}.?[#this > #min]").getValue(ctx));
        // → [20, 30]

        // Project inline list: square each element
        System.out.println(parser.parseExpression("{2, 3, 4}.![#this * #this]").getValue(ctx));
        // → [4, 9, 16]

        // Dynamic map key from variable
        ctx.setVariable("key", "status");
        System.out.println(parser.parseExpression("{#key: 'active', 'code': 200}").getValue(ctx));
        // → {status=active, code=200}

        // Nested map within list
        System.out.println(parser.parseExpression(
            "{{'id':1,'name':'Alice'}, {'id':2,'name':'Bob'}}").getValue());
        // → [{id=1, name=Alice}, {id=2, name=Bob}]

        // Elvis with inline list as default
        ctx.setRootObject(Map.of("roles", Collections.emptyList()));
        System.out.println(parser.parseExpression(
            "roles.size() > 0 ? roles : {'guest', 'viewer'}").getValue(ctx));
        // → [guest, viewer]
    }
}
```

How to run: `java SpelInlineCollectionsIntermediate.java`

`{5,10,20,30}.?[#this > #min]` applies selection directly to an inline list — `#this` refers to each element. Dynamic key `{#key: 'active'}` resolves the variable `#key` to build the map key at runtime.

### Level 3 — Advanced

`@Value` injecting inline list/map; inline collection in method argument; coercion to typed collection.

```java
// SpelInlineCollectionsAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.util.*;

@Configuration
class InlineCfg {}

@org.springframework.stereotype.Component
class SecurityPolicy {
    @Value("#{ {'GET', 'HEAD', 'OPTIONS'} }")
    private List<String> readOnlyMethods;

    @Value("#{ {'prod': 8443, 'staging': 8080, 'dev': 8000} }")
    private Map<String, Integer> portMap;

    @Value("#{ { {'role':'admin','level':3}, {'role':'user','level':1} } }")
    private List<Map<String, Object>> roleDefs;

    public List<String> getReadOnlyMethods()        { return readOnlyMethods; }
    public Map<String, Integer> getPortMap()         { return portMap; }
    public List<Map<String, Object>> getRoleDefs()  { return roleDefs; }
}

public class SpelInlineCollectionsAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(InlineCfg.class, SecurityPolicy.class);
        var policy = ctx.getBean(SecurityPolicy.class);

        System.out.println("readOnlyMethods: " + policy.getReadOnlyMethods());
        System.out.println("portMap:         " + policy.getPortMap());
        System.out.println("roleDefs:        " + policy.getRoleDefs());

        // Inline collection coercion
        var parser = new org.springframework.expression.spel.standard.SpelExpressionParser();
        // Coerce to Integer[] via getValue(type)
        Integer[] arr = parser.parseExpression("{10, 20, 30}").getValue(Integer[].class);
        System.out.println("as array: " + Arrays.toString(arr)); // [10, 20, 30]

        ctx.close();
    }
}
```

How to run: `java SpelInlineCollectionsAdvanced.java`

`@Value("#{ {'GET','HEAD','OPTIONS'} }")` — note the outer `#{}` SpEL delimiters wrapping the `{}` list literal. Without the `#{ }` wrapper the brace would be treated as property token syntax. `getValue(Integer[].class)` coerces the `List<Integer>` result to `Integer[]` via `ConversionService`.

## 6. Walkthrough

Execution for `"{5,10,20,30}.?[#this > #min]"` with `#min = 15`:

1. SpEL parses: `InlineList(5,10,20,30)` → `Selection(predicate: #this > #min)`.
2. `InlineList` evaluates to `[5, 10, 20, 30]` (unmodifiable).
3. `Selection` iterates; for each element `e`, evaluates `#this > #min` with `#this = e`, `#min = 15`.
4. `5 > 15` → false. `10 > 15` → false. `20 > 15` → true. `30 > 15` → true.
5. Result: `[20, 30]` (new modifiable `ArrayList`).

## 7. Gotchas & takeaways

> `{}` is an **inline list**, not an inline map. The empty map is `{:}`. Mixing them up silently produces the wrong type and fails at runtime when the receiving field expects a `Map`.

> Inline lists and maps produced by SpEL are **unmodifiable**. Calling `list.add(...)` on a `@Value`-injected inline list throws `UnsupportedOperationException`. Wrap in `new ArrayList<>(...)` if the bean needs a mutable copy.

- In `@Value`, wrap the SpEL expression in `#{}`: `@Value("#{ {'a','b'} }")`. Without the `#{}` delimiters, Spring treats the content as a property substitution token and looks for `{` in `application.properties`.
- Keys in inline maps are expressions, not bare identifiers. `{name: 'Alice'}` is parsed as `{<expr:name>: 'Alice'}` — it resolves `name` as a property of the current context. Use `{'name': 'Alice'}` to use string literal keys.
- `#this` inside `.?[]` and `.![]` refers to the current collection element, not the root object. This is the only place `#this` has collection-element semantics.
