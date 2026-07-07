---
card: java
gi: 382
slug: meta-annotation-target
title: 'Meta-annotation @Target'
---

## 1. What it is

`@Target` is a meta-annotation that restricts *where* your custom annotation is allowed to be applied — on a method, a field, a class, a parameter, and so on. You specify one or more values from the `ElementType` enum: `ElementType.METHOD`, `ElementType.FIELD`, `ElementType.TYPE` (classes, interfaces, enums), `ElementType.PARAMETER`, `ElementType.CONSTRUCTOR`, and several others. If you omit `@Target` entirely, the annotation may be applied almost anywhere — fields, methods, classes, parameters, local variables, and more — which is rarely what you actually want.

## 2. Why & when

An annotation designed with a specific meaning in mind — say, `@Column`, meant to describe how a *field* maps to a database column — makes no logical sense on a method or a class. Without `@Target`, nothing stops a confused caller from accidentally writing `@Column` above a method, producing an annotation that's syntactically legal but semantically meaningless, a mistake that would otherwise only surface later, and confusingly, when whatever reads `@Column` fails to find it where expected or misbehaves trying to process it somewhere it was never designed to appear.

`@Target` turns that class of misuse into an immediate compile error: applying an annotation restricted to `ElementType.FIELD` on a method produces `annotation type not applicable to this kind of declaration`, exactly at the point of the mistake. You should specify `@Target` on essentially every custom annotation you write, restricted to precisely the kinds of declarations where the annotation is actually meaningful.

## 3. Core concept

```java
import java.lang.annotation.*;

public class TargetDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.FIELD) // restricted to fields only
    @interface Column {
        String name() default "";
    }

    static class User {
        @Column(name = "user_email")
        String email; // legal: FIELD

        // @Column(name = "oops")
        // void save() { } // would be a COMPILE ERROR: Column is not applicable to methods
    }

    public static void main(String[] args) {
        System.out.println("Compiles fine -- @Column correctly restricted to fields.");
    }
}
```

**How to run:** `java TargetDemo.java`

`@Target(ElementType.FIELD)` on `Column`'s own declaration means `@Column` can only ever be applied to fields. The commented-out use on `save()` (a method) demonstrates what would happen if uncommented: an immediate compile error, since `ElementType.METHOD` was never included in `Column`'s allowed targets.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Target restricts an annotation to specific kinds of declarations; applying it elsewhere is a compile error, not a silent runtime issue">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">@Target(ElementType.FIELD)  @interface Column { ... }</text>

  <rect x="30" y="50" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="75" fill="#6db33f" font-size="10" text-anchor="middle">@Column String email;  -- FIELD, legal</text>

  <rect x="330" y="50" width="260" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="460" y="75" fill="#f85149" font-size="10" text-anchor="middle">@Column void save() { }  -- METHOD, illegal!</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">Applying @Column to a method is a compile error, not a silent runtime problem discovered later.</text>
</svg>

## 5. Runnable example

Scenario: a custom `@ApiEndpoint` annotation meant strictly for methods, evolved from an unrestricted version that can be misapplied anywhere, through adding `@Target(ElementType.METHOD)` to lock it down, to a version supporting two related targets at once for a companion annotation.

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class ApiEndpointUnrestricted {
    @Retention(RetentionPolicy.RUNTIME)
    @interface ApiEndpoint { // no @Target -- can be applied almost anywhere, even nonsensically
        String path();
    }

    @ApiEndpoint(path = "/users") // intended use: on a method
    static void listUsers() { }

    @ApiEndpoint(path = "/oops") // ALSO legal, even though a class isn't really "an endpoint"
    static class ConfusingMisuse { }

    public static void main(String[] args) {
        System.out.println("Both uses above compile -- @ApiEndpoint on a class is meaningless but allowed.");
    }
}
```

**How to run:** `java ApiEndpointUnrestricted.java`

`ApiEndpoint` has no `@Target`, so it's legal (if nonsensical) on both a method and, separately, a class — nothing in the annotation's own declaration expresses "this only makes sense on methods," so a confused caller placing it on the wrong kind of declaration gets no warning at all, only whatever confusing downstream behaviour eventually results.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class ApiEndpointRestricted {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD) // now explicitly restricted to methods only
    @interface ApiEndpoint {
        String path();
    }

    @ApiEndpoint(path = "/users") // legal: METHOD
    static void listUsers() { }

    // @ApiEndpoint(path = "/oops")
    // static class ConfusingMisuse { } // now a COMPILE ERROR if uncommented

    public static void main(String[] args) {
        System.out.println("Only the method usage compiles now -- misuse on a class is rejected.");
    }
}
```

**How to run:** `java ApiEndpointRestricted.java`

With `@Target(ElementType.METHOD)` added, the class-level misuse from Level 1 (shown commented out) would now fail to compile immediately with `annotation type not applicable to this kind of declaration` — exactly the class of mistake `@Target` exists to prevent.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class ApiEndpointMultiTarget {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface ApiEndpoint {
        String path();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target({ ElementType.METHOD, ElementType.PARAMETER }) // legal on EITHER of two kinds
    @interface Deprecated2 { // (illustrative -- multiple ElementType values in one @Target)
        String reason() default "";
    }

    static class Controller {
        @ApiEndpoint(path = "/users")
        void listUsers(@Deprecated2(reason = "unused legacy filter") String legacyFilter) { }
    }

    public static void main(String[] args) throws Exception {
        Method m = Controller.class.getDeclaredMethod("listUsers", String.class);
        ApiEndpoint endpoint = m.getAnnotation(ApiEndpoint.class);
        System.out.println("Endpoint path: " + endpoint.path());

        Deprecated2 paramAnnotation = m.getParameters()[0].getAnnotation(Deprecated2.class);
        System.out.println("Parameter deprecation reason: " + paramAnnotation.reason());
    }
}
```

**How to run:** `java ApiEndpointMultiTarget.java`

`@Target({ ElementType.METHOD, ElementType.PARAMETER })` shows that `@Target` accepts an array of allowed kinds — `Deprecated2` here is legal on either a method or a parameter (though this example only uses it on a parameter), demonstrating that `@Target` restricts to a *set* of allowed places, not necessarily just one.

## 6. Walkthrough

Execution starts in `main`. `Controller.class.getDeclaredMethod("listUsers", String.class)` uses reflection to locate the `listUsers` method, identified by its name and single `String` parameter. This returns a `Method` object representing that declaration.

`m.getAnnotation(ApiEndpoint.class)` retrieves the `@ApiEndpoint(path = "/users")` annotation attached directly to `listUsers` itself (a method-level annotation, matching `ApiEndpoint`'s `@Target(ElementType.METHOD)` restriction). `endpoint.path()` reads the `path` element, returning `"/users"`, which is printed as `Endpoint path: /users`.

`m.getParameters()[0]` retrieves the `Parameter` object for `listUsers`'s first (and only) parameter, `legacyFilter`. `.getAnnotation(Deprecated2.class)` retrieves the `@Deprecated2(reason = "unused legacy filter")` annotation attached to that specific parameter — this is legal precisely because `Deprecated2`'s `@Target` includes `ElementType.PARAMETER`. `paramAnnotation.reason()` reads the `reason` element, returning `"unused legacy filter"`, printed as `Parameter deprecation reason: unused legacy filter`.

Note that `ApiEndpoint` (restricted to `ElementType.METHOD` only) could never have been legally applied to `legacyFilter` — attempting `@ApiEndpoint(path = "/x") String legacyFilter` would be a compile error, since `PARAMETER` isn't among `ApiEndpoint`'s allowed targets.

Expected output:
```
Endpoint path: /users
Parameter deprecation reason: unused legacy filter
```

## 7. Gotchas & takeaways

> `@Target` accepts either a single `ElementType` or an array (`{ ElementType.METHOD, ElementType.PARAMETER }`) — forgetting the curly braces when you mean to allow multiple kinds is a compile error, since `@Target(ElementType.METHOD, ElementType.PARAMETER)` (without braces) isn't valid syntax for an array-valued element.

- `@Target` restricts where a custom annotation may legally be applied, using values from the `ElementType` enum (`METHOD`, `FIELD`, `TYPE`, `PARAMETER`, `CONSTRUCTOR`, and others).
- Omitting `@Target` allows the annotation to be applied almost anywhere — nearly always a mistake for a purpose-built annotation, since it removes the compiler's ability to catch obviously wrong placements.
- Misapplying a `@Target`-restricted annotation is a compile-time error (`annotation type not applicable to this kind of declaration`), not a silent runtime surprise discovered much later.
- Specify `@Target` on virtually every custom annotation you write, restricted to precisely the declaration kinds where the annotation is semantically meaningful.
- `@Target({ A, B })` (an array) permits the annotation on either kind of declaration; this is common for annotations meaningfully applicable to both, for example, methods and parameters.
