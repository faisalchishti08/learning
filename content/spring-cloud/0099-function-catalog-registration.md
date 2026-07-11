---
card: spring-cloud
gi: 99
slug: function-catalog-registration
title: "Function catalog & registration"
---

## 1. What it is

`FunctionCatalog` is the runtime registry Spring Cloud Function builds from every `Supplier`/`Function`/`Consumer` bean in the application context (keyed by bean name), and it's the same lookup mechanism every adapter — web, stream, serverless — and the composition/routing machinery from earlier cards use internally to resolve a name like `"uppercase"` or `"uppercase|reverse"` into an actual invokable function at runtime.

```java
@Autowired
FunctionCatalog catalog;

Function<String, String> fn = catalog.lookup(Function.class, "uppercase|reverse");
String result = (String) fn.apply("hello");
```

```java
@Bean Function<String, String> uppercase() { return String::toUpperCase; }
```

## 2. Why & when

Every earlier card in this section — deployment adapters, composition, routing — depends on some mechanism actually resolving a function's name to its implementation at runtime, and doing so uniformly regardless of how many functions are registered or which adapter is asking. `FunctionCatalog` is that mechanism: it inspects the Spring application context once at startup, finds every bean assignable to `Supplier`, `Function`, or `Consumer`, and indexes them by bean name (or an explicit `@Bean(name=...)` alias), so that any later lookup — whether triggered by an incoming HTTP request path, a `spring.cloud.function.definition` property, or a routing header — is a simple name-to-implementation resolution rather than each adapter needing its own separate function-discovery logic.

Reach for direct `FunctionCatalog` interaction when:

- Building custom infrastructure on top of Spring Cloud Function — a custom adapter for an unsupported transport, a diagnostic endpoint listing every registered function — that needs the same function-resolution behavior the built-in adapters rely on, without duplicating that discovery logic.
- Debugging why a function isn't being found by name — inspecting `catalog.lookup(...)` directly (or the aggregated set of registered names) is the most direct way to confirm whether a bean was actually registered as expected, and under what name.
- Programmatically invoking a function pipeline from within other application code (outside of the standard adapters), such as a scheduled job that needs to run a `spring.cloud.function.definition`-style composed pipeline on a timer rather than in response to a request or message.

## 3. Core concept

```
 Spring application context startup:
   @Bean Function<String,String> uppercase() {...}
   @Bean Function<String,String> reverse() {...}
        |
        v
   FunctionCatalog scans the context, finds both beans,
   indexes them: {"uppercase" -> fn, "reverse" -> fn}
        |
        v
   ANY adapter/lookup asks the catalog by NAME:
     catalog.lookup(Function.class, "uppercase")        -- single function
     catalog.lookup(Function.class, "uppercase|reverse") -- composed pipeline, resolved AND composed by the catalog
```

The catalog is the single source of truth every other piece of Spring Cloud Function machinery (adapters, routing, composition) is built on top of — none of them maintain a separate registry of their own.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The FunctionCatalog indexes every registered function bean by name and every adapter, whether web, stream, or serverless, resolves function names through this one shared catalog rather than maintaining its own registry">
  <rect x="20" y="20" width="140" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">uppercase bean</text>
  <rect x="180" y="20" width="140" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="250" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">reverse bean</text>

  <rect x="100" y="90" width="300" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="250" y="118" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">FunctionCatalog</text>

  <rect x="20" y="170" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="191" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">web adapter</text>
  <rect x="250" y="170" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="191" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">stream adapter</text>
  <rect x="470" y="170" width="140" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="540" y="191" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">serverless adapter</text>

  <defs><marker id="a99" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="90" y1="60" x2="200" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a99)"/>
  <line x1="250" y1="60" x2="270" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a99)"/>
  <line x1="200" y1="136" x2="90" y2="170" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a99)"/>
  <line x1="250" y1="136" x2="320" y2="170" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a99)"/>
  <line x1="300" y1="136" x2="540" y2="170" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a99)"/>
</svg>

Two beans register into one catalog; three different adapters all resolve their function names through that same shared catalog, rather than each maintaining an independent registry.

## 5. Runnable example

The scenario: a minimal catalog implementation that mirrors `FunctionCatalog`'s core job — registering beans by name and resolving lookups, including composed pipeline lookups. Start with basic registration and single-name lookup, then add composed-name lookup (`"a|b"` resolved and chained by the catalog itself), then add a diagnostic method listing all registered names, useful for exactly the kind of "why isn't my function found" debugging the catalog is reached for in practice.

### Level 1 — Basic

A minimal catalog: register beans by name, look one up by name.

```java
import java.util.*;
import java.util.function.Function;

public class FunctionCatalogLevel1 {
    static class SimpleFunctionCatalog {
        Map<String, Function<Object, Object>> registry = new HashMap<>();

        @SuppressWarnings("unchecked")
        void register(String name, Function<?, ?> fn) {
            registry.put(name, (Function<Object, Object>) fn);
        }

        Function<Object, Object> lookup(String name) {
            Function<Object, Object> fn = registry.get(name);
            if (fn == null) throw new NoSuchElementException("no function registered under name: " + name);
            return fn;
        }
    }

    public static void main(String[] args) {
        SimpleFunctionCatalog catalog = new SimpleFunctionCatalog();
        catalog.register("uppercase", (Function<String, String>) String::toUpperCase);

        Function<Object, Object> fn = catalog.lookup("uppercase");
        System.out.println(fn.apply("hello"));
    }
}
```

How to run: `java FunctionCatalogLevel1.java`

`register` and `lookup` are the two operations every adapter relies on: a bean gets indexed by its name exactly once at startup, and any later code resolves it back by that same name, with no adapter needing to know how or when the function was originally created.

### Level 2 — Intermediate

Extend `lookup` to understand pipe-separated composed names, resolving and chaining multiple registered functions from a single lookup call — mirroring how the real `FunctionCatalog` handles a `"uppercase|reverse"`-style definition.

```java
import java.util.*;
import java.util.function.Function;

public class FunctionCatalogLevel2 {
    static class SimpleFunctionCatalog {
        Map<String, Function<Object, Object>> registry = new HashMap<>();

        @SuppressWarnings("unchecked")
        void register(String name, Function<?, ?> fn) {
            registry.put(name, (Function<Object, Object>) fn);
        }

        Function<Object, Object> lookup(String name) {
            if (name.contains("|")) {
                String[] stages = name.split("\\|");
                Function<Object, Object> pipeline = lookupSingle(stages[0]);
                for (int i = 1; i < stages.length; i++) pipeline = pipeline.andThen(lookupSingle(stages[i]));
                return pipeline;
            }
            return lookupSingle(name);
        }

        Function<Object, Object> lookupSingle(String name) {
            Function<Object, Object> fn = registry.get(name);
            if (fn == null) throw new NoSuchElementException("no function registered under name: " + name);
            return fn;
        }
    }

    public static void main(String[] args) {
        SimpleFunctionCatalog catalog = new SimpleFunctionCatalog();
        catalog.register("uppercase", (Function<String, String>) String::toUpperCase);
        catalog.register("reverse", (Function<String, String>) s -> new StringBuilder(s).reverse().toString());

        // ONE lookup call resolves AND composes two registered functions
        Function<Object, Object> pipeline = catalog.lookup("uppercase|reverse");
        System.out.println(pipeline.apply("hello"));
    }
}
```

How to run: `java FunctionCatalogLevel2.java`

`lookup("uppercase|reverse")` internally calls `lookupSingle` twice and chains the results with `andThen`, all inside the catalog itself — callers (adapters, in the real framework) never need to know or implement composition logic themselves; they simply pass whatever name string they were given (an HTTP path segment, a `spring.cloud.function.definition` value) straight to `lookup`.

### Level 3 — Advanced

Add a diagnostic method listing every registered name (useful for debugging "why isn't my function found") and demonstrate a realistic failure: a typo in a definition string caught early with a clear error, plus confirming the full set of registered names via the diagnostic method.

```java
import java.util.*;
import java.util.function.Function;

public class FunctionCatalogLevel3 {
    static class SimpleFunctionCatalog {
        Map<String, Function<Object, Object>> registry = new LinkedHashMap<>();

        @SuppressWarnings("unchecked")
        void register(String name, Function<?, ?> fn) {
            registry.put(name, (Function<Object, Object>) fn);
        }

        Function<Object, Object> lookup(String name) {
            if (name.contains("|")) {
                String[] stages = name.split("\\|");
                Function<Object, Object> pipeline = lookupSingle(stages[0]);
                for (int i = 1; i < stages.length; i++) pipeline = pipeline.andThen(lookupSingle(stages[i]));
                return pipeline;
            }
            return lookupSingle(name);
        }

        Function<Object, Object> lookupSingle(String name) {
            Function<Object, Object> fn = registry.get(name);
            if (fn == null) {
                throw new NoSuchElementException(
                    "no function registered under name: '" + name + "' -- registered names are: " + registeredNames());
            }
            return fn;
        }

        // diagnostic: mirrors FunctionCatalog#getNames(), useful for debugging registration issues
        Set<String> registeredNames() { return registry.keySet(); }
    }

    public static void main(String[] args) {
        SimpleFunctionCatalog catalog = new SimpleFunctionCatalog();
        catalog.register("uppercase", (Function<String, String>) String::toUpperCase);
        catalog.register("reverse", (Function<String, String>) s -> new StringBuilder(s).reverse().toString());

        System.out.println("registered functions: " + catalog.registeredNames());

        try {
            catalog.lookup("uppercase|reveerse"); // deliberate typo
        } catch (NoSuchElementException e) {
            System.out.println("lookup failed as expected: " + e.getMessage());
        }

        // correct spelling succeeds
        Function<Object, Object> pipeline = catalog.lookup("uppercase|reverse");
        System.out.println("correct pipeline result: " + pipeline.apply("hello"));
    }
}
```

How to run: `java FunctionCatalogLevel3.java`

The deliberate typo `"reveerse"` triggers `lookupSingle` to throw with a message that includes `registeredNames()` (`[uppercase, reverse]`), giving immediate, actionable diagnostic information — exactly the kind of detail that turns "my function definition isn't working" from a mystery into a one-line fix, whether debugging a real `FunctionCatalog` lookup failure or this simplified model of it.

## 6. Walkthrough

Trace the `catalog.lookup("uppercase|reveerse")` call in Level 3.

1. `lookup` receives `name = "uppercase|reveerse"`, and `name.contains("|")` is `true`, so it enters the composed-name branch.
2. `name.split("\\|")` produces `["uppercase", "reveerse"]`.
3. `lookupSingle("uppercase")` is called first — `registry.get("uppercase")` finds the registered function successfully, so `pipeline` is assigned that function with no exception.
4. The `for` loop's single iteration (`i=1`) calls `lookupSingle("reveerse")` — `registry.get("reveerse")` returns `null`, because only `"reverse"` (correctly spelled) was ever registered, so the `if (fn == null)` check triggers, throwing `NoSuchElementException` with a message embedding `registeredNames()`, which at this point is `["uppercase", "reverse"]` (the actual, correctly-spelled registered names).
5. This exception propagates out of `lookup` and out of the `try` block in `main`, where the `catch (NoSuchElementException e)` clause catches it and prints the diagnostic message — visibly confirming both what was searched for (`reveerse`) and what actually exists (`uppercase`, `reverse`), making the typo immediately obvious.
6. `main` then calls `catalog.lookup("uppercase|reverse")` (correct spelling this time) — this succeeds through the same code path, producing a working composed pipeline, and `pipeline.apply("hello")` yields `"OLLEH"`, confirming the catalog resolves correctly once the name matches an actually-registered function.

```
lookup("uppercase|reveerse")
  split -> ["uppercase", "reveerse"]
  lookupSingle("uppercase")  -> FOUND
  lookupSingle("reveerse")   -> NOT FOUND -> throw, message includes registeredNames() = [uppercase, reverse]
  caught in main -> diagnostic printed, typo now obvious by comparison
```

## 7. Gotchas & takeaways

> **Gotcha:** a function bean's registered name in the real `FunctionCatalog` is its Spring bean name by default (the `@Bean` method's name, or an explicit `name` attribute) — renaming a `@Bean` method without updating every `spring.cloud.function.definition` property or routing header that references its old name silently breaks those lookups at runtime, since nothing at compile time connects a definition string to the bean it's meant to reference.

- `FunctionCatalog` is the shared registration and resolution mechanism every Spring Cloud Function adapter, and the composition/routing features from earlier cards, are built on top of — understanding it directly demystifies how a plain string like `"uppercase|reverse"` becomes an actual running pipeline.
- A diagnostic listing of registered names (`registeredNames()` here, `FunctionCatalog#getNames()` in the real API) is the fastest way to debug "my function isn't being found" — comparing the requested name against the actual registered set immediately reveals typos, unregistered beans, or naming mismatches.
- Composed-name lookup (`"a|b"`) resolving and chaining multiple registered functions is handled entirely inside the catalog's own lookup logic — no adapter needs to implement composition itself, it simply passes whatever name string it was given straight through to the catalog.
- Treat a function's registered name as a stable, load-bearing identifier once other configuration (definition strings, routing headers, external callers) starts referencing it by that name — renaming the underlying bean without a coordinated update everywhere that name is used is a common, easily-avoidable source of "function not found" failures.
