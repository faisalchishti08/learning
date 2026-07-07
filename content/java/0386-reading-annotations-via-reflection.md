---
card: java
gi: 386
slug: reading-annotations-via-reflection
title: Reading annotations via reflection
---

## 1. What it is

The `java.lang.reflect` API lets a running program inspect annotations attached to classes, methods, fields, and other declarations, and read their element values — this is how any framework (Spring, JUnit, Hibernate) actually "sees" and acts on the annotations you write in your code. The key methods are `isAnnotationPresent(Class)` (does this element carry this annotation?), `getAnnotation(Class)` (retrieve it, or `null` if absent), and `getAnnotations()` / `getDeclaredAnnotations()` (retrieve every annotation present). All of this only works for annotations declared with `@Retention(RetentionPolicy.RUNTIME)` (see [[meta-annotation-retention-source-class-runtime]]) — anything else is invisible to these calls.

## 2. Why & when

Annotations by themselves are inert metadata; reflection is the mechanism that turns them into actual behaviour. A dependency-injection framework doesn't magically know which fields need injecting — it scans every field of every managed class with reflection, checks `field.isAnnotationPresent(Autowired.class)`, and if present, sets that field's value. A test runner doesn't hardcode which methods are tests — it reflects over the test class, filters methods by `isAnnotationPresent(Test.class)`, and invokes each one. This pattern (reflect → check presence → read elements → act) is the foundation nearly every annotation-driven Java framework is built on.

You reach for this yourself whenever you're building anything that needs to discover and act on your own custom annotations at runtime — a lightweight test runner, a validation framework, a routing table built from annotated handler methods, or a simple dependency injector.

## 3. Core concept

```java
import java.lang.annotation.*;
import java.lang.reflect.Field;

public class ReflectionReadDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.FIELD)
    @interface Inject {
    }

    static class Service {
        @Inject
        String database;

        String cache; // not annotated -- should be left alone
    }

    public static void main(String[] args) throws Exception {
        Service service = new Service();
        for (Field field : Service.class.getDeclaredFields()) {
            if (field.isAnnotationPresent(Inject.class)) {
                field.setAccessible(true); // needed to write a package-private/default field from outside
                field.set(service, "PostgresConnection"); // simulate injecting a dependency
            }
        }
        System.out.println("database = " + service.database);
        System.out.println("cache = " + service.cache);
    }
}
```

**How to run:** `java ReflectionReadDemo.java`

`Service.class.getDeclaredFields()` returns both fields; the loop checks each with `isAnnotationPresent(Inject.class)`, finding only `database` marked. `field.set(service, "PostgresConnection")` uses reflection to assign a value directly, bypassing any normal constructor or setter — a simplified version of what a real dependency-injection framework does. `cache`, never annotated, is left as its default `null`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="reflection walks every field, checks which ones carry a marker annotation, and acts only on those, leaving unannotated fields untouched">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Service.class.getDeclaredFields() -&gt; [database, cache]</text>

  <rect x="30" y="50" width="260" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="70" fill="#6db33f" font-size="10" text-anchor="middle">database  @Inject</text>
  <text x="160" y="85" fill="#8b949e" font-size="9" text-anchor="middle">isAnnotationPresent -&gt; true -&gt; set()</text>

  <rect x="330" y="50" width="260" height="45" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="70" fill="#8b949e" font-size="10" text-anchor="middle">cache  (unannotated)</text>
  <text x="460" y="85" fill="#8b949e" font-size="9" text-anchor="middle">isAnnotationPresent -&gt; false -&gt; skipped</text>

  <text x="20" y="135" fill="#8b949e" font-size="10">Only fields carrying @Inject are ever touched by the injection logic -- others pass through unchanged.</text>
</svg>

## 5. Runnable example

Scenario: a minimal routing table for handler methods, evolved from hardcoded routing logic, through reflection discovering annotated handlers automatically, to a version reading element values from the annotation to build a genuinely usable route dispatch table.

### Level 1 — Basic

```java
public class RoutingHardcoded {
    static class Handlers {
        String showHome() { return "Welcome!"; }
        String showAbout() { return "About us."; }
    }

    public static void main(String[] args) {
        Handlers handlers = new Handlers();
        System.out.println("/ -> " + handlers.showHome());     // hand-wired, one line per route
        System.out.println("/about -> " + handlers.showAbout());
    }
}
```

**How to run:** `java RoutingHardcoded.java`

Every route has to be wired up by hand in `main` — adding a new handler method means remembering to also add a corresponding line here, with no automatic connection between the method and its intended route path.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class RoutingDiscovered {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface Route {
        String value();
    }

    static class Handlers {
        @Route("/")
        String showHome() { return "Welcome!"; }

        @Route("/about")
        String showAbout() { return "About us."; }

        String helperNotARoute() { return "internal use only"; } // unannotated -- not a route
    }

    public static void main(String[] args) throws Exception {
        Handlers handlers = new Handlers();
        for (Method m : Handlers.class.getDeclaredMethods()) {
            Route route = m.getAnnotation(Route.class);
            if (route != null) {
                Object result = m.invoke(handlers); // dynamically call the discovered handler
                System.out.println(route.value() + " -> " + result);
            }
        }
    }
}
```

**How to run:** `java RoutingDiscovered.java`

Handlers now discover themselves — `main` never mentions `showHome` or `showAbout` by name at all; the loop finds every `@Route`-annotated method via reflection and calls it dynamically. `helperNotARoute` is correctly skipped since it lacks the annotation.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.LinkedHashMap;
import java.util.Map;

public class RoutingTableWithMethodElement {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface Route {
        String path();
        String httpMethod() default "GET"; // second element -- forces named syntax, see marker-single-value-annotations
    }

    static class Handlers {
        @Route(path = "/")
        String showHome() { return "Welcome!"; }

        @Route(path = "/users", httpMethod = "POST")
        String createUser() { return "User created."; }
    }

    public static void main(String[] args) throws Exception {
        Handlers handlers = new Handlers();
        Map<String, Method> routingTable = new LinkedHashMap<>();

        for (Method m : Handlers.class.getDeclaredMethods()) {
            Route route = m.getAnnotation(Route.class);
            if (route != null) {
                String key = route.httpMethod() + " " + route.path();
                routingTable.put(key, m);
            }
        }

        // Simulate two incoming requests being dispatched through the built table
        dispatch(routingTable, handlers, "GET /");
        dispatch(routingTable, handlers, "POST /users");
        dispatch(routingTable, handlers, "DELETE /users"); // no matching route
    }

    static void dispatch(Map<String, Method> table, Handlers handlers, String requestKey) throws Exception {
        Method m = table.get(requestKey);
        if (m == null) {
            System.out.println(requestKey + " -> 404 Not Found");
            return;
        }
        System.out.println(requestKey + " -> " + m.invoke(handlers));
    }
}
```

**How to run:** `java RoutingTableWithMethodElement.java`

This builds a genuine `httpMethod + path` -> `Method` routing table entirely from reflection over `@Route` annotations, then dispatches simulated incoming requests against it — including one (`DELETE /users`) that has no matching handler, correctly falling through to a "not found" response, exactly like a real web framework's router.

## 6. Walkthrough

Execution starts in `main`. The loop `for (Method m : Handlers.class.getDeclaredMethods())` iterates `showHome` and `createUser`. For `showHome`: `m.getAnnotation(Route.class)` retrieves `@Route(path = "/")` — note `httpMethod` was never specified, so it reads back as its default, `"GET"`. `key` becomes `"GET /"`, and `routingTable.put("GET /", showHomeMethod)` stores this mapping. For `createUser`: `@Route(path = "/users", httpMethod = "POST")` gives `key = "POST /users"`, stored similarly.

`dispatch(routingTable, handlers, "GET /")` is called. `table.get("GET /")` finds the stored `showHome` method. Since it's not `null`, `m.invoke(handlers)` dynamically calls `showHome()`, returning `"Welcome!"`. This prints `GET / -> Welcome!`.

`dispatch(routingTable, handlers, "POST /users")` runs similarly: `table.get("POST /users")` finds `createUser`, `m.invoke(handlers)` calls it, returning `"User created."`, printed as `POST /users -> User created.`.

`dispatch(routingTable, handlers, "DELETE /users")` runs last: `table.get("DELETE /users")` finds no entry (the table only ever had `"GET /"` and `"POST /users"` as keys), so `m` is `null`. The `if (m == null)` branch runs, printing `DELETE /users -> 404 Not Found` without ever attempting to invoke anything.

Expected output:
```
GET / -> Welcome!
POST /users -> User created.
DELETE /users -> 404 Not Found
```

## 7. Gotchas & takeaways

> `Method.invoke(...)` wraps any exception the invoked method throws inside an `InvocationTargetException` — catching a plain `Exception` and printing `e.getMessage()` directly will show a confusing, unhelpful message; always call `e.getCause()` first to get the real, original exception the reflected method actually threw.

- `isAnnotationPresent(Class)` and `getAnnotation(Class)` only ever find annotations declared with `@Retention(RetentionPolicy.RUNTIME)` — anything with `SOURCE` or `CLASS` retention is invisible to both, regardless of how the code looks.
- `getDeclaredFields()`/`getDeclaredMethods()` combined with per-element `isAnnotationPresent`/`getAnnotation` checks is the standard "discover what's annotated" pattern nearly every reflection-based framework uses.
- `field.setAccessible(true)` is often necessary to read or write non-`public` fields via reflection — frameworks use this routinely to inject into private fields without requiring public setters.
- `Method.invoke(instance, args...)` dynamically calls a discovered method — this is how a framework calls your annotated handler, test, or listener methods without ever referencing them by name in its own source code.
- Building a small, real routing table or dependency injector by hand (as in this example) is one of the clearest ways to understand what frameworks like Spring are conceptually doing internally, well before you look at their actual, far more elaborate implementations.
