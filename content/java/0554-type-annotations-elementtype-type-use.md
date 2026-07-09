---
card: java
gi: 554
slug: type-annotations-elementtype-type-use
title: Type annotations (ElementType.TYPE_USE)
---

## 1. What it is

Before Java 8, annotations could only target declarations — a field, a method, a parameter, a class. `ElementType.TYPE_USE`, added in Java 8, expands where an annotation can appear: anywhere a *type* is written, including inside generic type arguments, in cast expressions, on array component types, and even on `this` in an instance method's receiver parameter. An annotation whose `@Target` includes `TYPE_USE` can appear at these new positions, most commonly seen in static analysis tools for nullability (`@NonNull String name`) or immutability annotations.

## 2. Why & when

Declaration-only annotations can't express certain useful distinctions. `@NonNull List<String>` (annotating the `List` itself) versus `List<@NonNull String>` (annotating the generic type argument — meaning the list can be null-containing elements but the list reference itself, or vice versa) is only expressible with `TYPE_USE` annotations, since it needs to attach to a specific *type usage*, not just the field or parameter declaration as a whole. This granularity is primarily useful for static analysis tools (like nullability checkers) that need to reason precisely about which specific type in a complex generic signature a constraint applies to.

## 3. Core concept

```java
import java.lang.annotation.*;

@Target(ElementType.TYPE_USE)
@Retention(RetentionPolicy.RUNTIME)
@interface NonNull {}

class Example {
    @NonNull String name; // annotates the FIELD's type

    void process(@NonNull String input) {} // annotates a PARAMETER's type

    List<@NonNull String> names; // annotates the GENERIC TYPE ARGUMENT specifically -- only possible with TYPE_USE

    String cast(Object obj) {
        return (@NonNull String) obj; // annotates a CAST expression's type -- also only possible with TYPE_USE
    }
}
```

`TYPE_USE` lets the same annotation attach to a type wherever it's written — a field's type, a parameter's type, a generic type argument, or a cast — distinctions a purely declaration-targeted annotation cannot express.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TYPE_USE annotations can attach to a type wherever it appears, including inside generic type arguments">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <text x="20" y="40" fill="#8b949e" font-size="12" font-family="monospace">List&lt;<tspan fill="#6db33f">@NonNull</tspan> String&gt; namesA;  <tspan fill="#8b949e">// elements can't be null</tspan></text>
  <text x="20" y="80" fill="#8b949e" font-size="12" font-family="monospace"><tspan fill="#6db33f">@NonNull</tspan> List&lt;String&gt; namesB;  <tspan fill="#8b949e">// the list reference itself can't be null</tspan></text>
</svg>

Placing `@NonNull` inside versus outside the generic brackets expresses two entirely different constraints — a distinction impossible before `TYPE_USE`.

## 5. Runnable example

Scenario: building a small compile-time-inert nullability annotation and reading it back through reflection to understand how `TYPE_USE` placement affects meaning — evolved from a basic type-use annotation on a field, through distinguishing element-level from collection-level annotation placement, to a version reading annotated type information from a method's generic return type via reflection.

### Level 1 — Basic

```java
import java.lang.annotation.*;
import java.lang.reflect.*;

public class TypeUseBasic {
    @Target(ElementType.TYPE_USE)
    @Retention(RetentionPolicy.RUNTIME)
    @interface NonNull {}

    static class User {
        @NonNull String name; // TYPE_USE lets this annotate the field's TYPE directly
    }

    public static void main(String[] args) throws NoSuchFieldException {
        Field field = User.class.getDeclaredField("name");
        AnnotatedType annotatedType = field.getAnnotatedType();

        System.out.println("Field type: " + field.getType().getSimpleName());
        System.out.println("Has @NonNull: " + annotatedType.isAnnotationPresent(NonNull.class));
    }
}
```

**How to run:** `java TypeUseBasic.java`

Expected output:
```
Field type: String
Has @NonNull: true
```

`@NonNull` is applied directly to `name`'s type, `String`, made possible by `@Target(ElementType.TYPE_USE)`. `field.getAnnotatedType()` retrieves the type-use-annotated view of the field's type (distinct from `field.getAnnotations()`, which would look for annotations on the field declaration itself), and `.isAnnotationPresent(NonNull.class)` confirms the annotation is present on this specific type usage.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class TypeUseGenericPlacement {
    @Target(ElementType.TYPE_USE)
    @Retention(RetentionPolicy.RUNTIME)
    @interface NonNull {}

    static class Roster {
        List<@NonNull String> names; // elements are non-null; the List reference itself could still be null
    }

    public static void main(String[] args) throws NoSuchFieldException {
        Field field = Roster.class.getDeclaredField("names");
        AnnotatedType fieldType = field.getAnnotatedType();

        // fieldType itself (the List) is NOT annotated -- only its generic type argument is.
        System.out.println("List itself has @NonNull: " + fieldType.isAnnotationPresent(NonNull.class));

        // Drilling into the generic type argument reveals the annotation there.
        AnnotatedParameterizedType parameterizedType = (AnnotatedParameterizedType) fieldType;
        AnnotatedType elementType = parameterizedType.getAnnotatedActualTypeArguments()[0];
        System.out.println("Element type has @NonNull: " + elementType.isAnnotationPresent(NonNull.class));
    }
}
```

**How to run:** `java TypeUseGenericPlacement.java`

Expected output:
```
List itself has @NonNull: false
Element type has @NonNull: true
```

The real-world concern this adds: distinguishing *where* within a generic type an annotation actually applies. `List<@NonNull String> names` places `@NonNull` specifically on the `String` type argument, not on the `List` type itself — so `fieldType.isAnnotationPresent(NonNull.class)` (checking the outer `List` type) correctly reports `false`, while drilling into `getAnnotatedActualTypeArguments()[0]` (the first, and only, generic type argument) reveals the annotation is genuinely present there. This precision — annotating one specific nested type within a larger generic signature — is exactly what `TYPE_USE` uniquely enables.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class TypeUseMethodReturn {
    @Target(ElementType.TYPE_USE)
    @Retention(RetentionPolicy.RUNTIME)
    @interface NonNull {}

    @Target(ElementType.TYPE_USE)
    @Retention(RetentionPolicy.RUNTIME)
    @interface Nullable {}

    static class UserService {
        // The METHOD's return type (the Map) is non-null; VALUES in the map may be null; KEYS may not.
        Map<@NonNull String, @Nullable String> fetchUserAttributes() {
            return new HashMap<>();
        }
    }

    public static void main(String[] args) throws NoSuchMethodException {
        Method method = UserService.class.getDeclaredMethod("fetchUserAttributes");
        AnnotatedType returnType = method.getAnnotatedReturnType();

        AnnotatedParameterizedType mapType = (AnnotatedParameterizedType) returnType;
        AnnotatedType[] typeArguments = mapType.getAnnotatedActualTypeArguments();

        AnnotatedType keyType = typeArguments[0];
        AnnotatedType valueType = typeArguments[1];

        System.out.println("Key type has @NonNull: " + keyType.isAnnotationPresent(NonNull.class));
        System.out.println("Value type has @Nullable: " + valueType.isAnnotationPresent(Nullable.class));
        System.out.println("Return type itself has @NonNull: " + returnType.isAnnotationPresent(NonNull.class));
    }
}
```

**How to run:** `java TypeUseMethodReturn.java`

Expected output:
```
Key type has @NonNull: true
Value type has @Nullable: true
Return type itself has @NonNull: false
```

This reads type-use annotations from a **method's return type**, at generic-argument-level granularity: `Map<@NonNull String, @Nullable String>` places different, distinct constraints on the map's key type and value type — keys can never be `null`, values sometimes can be — while saying nothing about the `Map` reference itself (which happens to have neither annotation here). `method.getAnnotatedReturnType()` retrieves the fully-annotated view of the return type, and drilling into `getAnnotatedActualTypeArguments()` separates out each generic parameter's own, independent annotations — exactly the kind of fine-grained nullability contract a real static-analysis tool (like a nullability checker) would need to enforce.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `method` is obtained via reflection for `UserService.fetchUserAttributes()`.

`method.getAnnotatedReturnType()` retrieves an `AnnotatedType` representing the fully-annotated form of the method's declared return type, `Map<@NonNull String, @Nullable String>` — this is distinct from `method.getReturnType()`, which would give just the raw `Class` object (`Map.class`) with no annotation information attached at all.

`(AnnotatedParameterizedType) returnType` casts this to the more specific `AnnotatedParameterizedType` interface, which exposes generic type argument information. `mapType.getAnnotatedActualTypeArguments()` returns an array of `AnnotatedType`, one entry per generic type parameter of `Map` — since `Map<K, V>` has two type parameters, this array has two elements: index `0` for the key type (`String`, with `@NonNull`), index `1` for the value type (`String`, with `@Nullable`).

`keyType = typeArguments[0]` is the annotated form of the key type argument. `keyType.isAnnotationPresent(NonNull.class)` checks whether `@NonNull` is present on this specific type usage — since the source code explicitly wrote `@NonNull String` as the first generic argument, this is `true`.

`valueType = typeArguments[1]` is the annotated form of the value type argument. `valueType.isAnnotationPresent(Nullable.class)` checks for `@Nullable` — since the source wrote `@Nullable String` as the second generic argument, this is `true`.

```
Map<@NonNull String, @Nullable String> fetchUserAttributes()

getAnnotatedReturnType() -> AnnotatedType for the WHOLE "Map<@NonNull String, @Nullable String>" usage
  .isAnnotationPresent(NonNull.class) -> checks the Map type ITSELF -> no annotation there -> false

getAnnotatedActualTypeArguments()[0] -> the "@NonNull String" key type argument -> has @NonNull -> true
getAnnotatedActualTypeArguments()[1] -> the "@Nullable String" value type argument -> has @Nullable -> true
```

Finally, `returnType.isAnnotationPresent(NonNull.class)` checks the *outer* `Map` type itself, not either type argument — since the source code never wrote `@NonNull` directly on `Map` (only inside its generic brackets, on the key), this correctly returns `false`. `main` prints all three results, demonstrating that each of the three distinct positions — the key type, the value type, and the outer `Map` type — carries its own, independently-checkable set of type-use annotations.

## 7. Gotchas & takeaways

> `field.getAnnotations()`/`method.getAnnotations()` (the older, declaration-targeted reflection methods) will **not** find `TYPE_USE` annotations placed on generic type arguments or in other type-usage positions — only `getAnnotatedType()`/`getAnnotatedReturnType()`/`getAnnotatedParameterTypes()` and their associated `AnnotatedType` hierarchy expose this information. Using the wrong reflection API for a `TYPE_USE` annotation silently returns nothing, rather than an error, which can be confusing when debugging.

- `ElementType.TYPE_USE` (added in Java 8) lets an annotation attach anywhere a type is written — field types, parameter types, generic type arguments, cast expressions, and more.
- This enables distinctions declaration-only annotations cannot express, such as `List<@NonNull String>` (elements can't be null) versus `@NonNull List<String>` (the list reference can't be null).
- `TYPE_USE` annotations are read via `getAnnotatedType()`/`getAnnotatedReturnType()`/`getAnnotatedParameterTypes()`, producing an `AnnotatedType` — not the plain `getAnnotations()` methods used for declaration-targeted annotations.
- `AnnotatedParameterizedType.getAnnotatedActualTypeArguments()` drills into a generic type's individual type arguments, each with its own independently-annotatable `AnnotatedType`.
- `TYPE_USE` annotations are primarily consumed by static analysis tools (nullability checkers, immutability checkers) rather than at runtime by ordinary application code — but understanding how to read them via reflection clarifies exactly what such tools are actually inspecting.
