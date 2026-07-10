---
card: java
gi: 950
slug: super-type-tokens-typereference-pattern
title: "Super type tokens (TypeReference pattern)"
---

## 1. What it is

A super type token is a technique for recovering a generic type's full parameterization (like `List<String>`, as opposed to just `List`) at runtime, despite [type erasure](0359-type-erasure.md) normally discarding that information entirely by the time the program runs. The trick exploits one specific place erasure does *not* apply: a class's *supertype*, as recorded in its `.class` file's generic signature, is preserved and reflectively readable, even though a variable's or object's own generic type argument is not. So instead of trying to capture `List<String>`'s type argument directly (impossible after erasure), you create an anonymous subclass of a generic class, parameterized with the specific type you want to remember (`new TypeReference<List<String>>() {}`), and then use reflection on *that anonymous subclass* to read back its declared supertype's generic signature — which the JVM does still have stored, since the anonymous class's `extends TypeReference<List<String>>` clause is part of its own class definition, not an erased type argument on some instance.

## 2. Why & when

This pattern exists specifically because ordinary generics cannot express "give me a `Class<List<String>>`" — `List<String>.class` isn't valid Java at all, since after erasure there is only one `List.class`, shared by every parameterization. Yet many real APIs genuinely need this information at runtime: JSON libraries (Jackson's `TypeReference`, Gson's `TypeToken`) need to know a target type is specifically `List<User>` (not just `List`) to correctly deserialize a JSON array's elements as `User` objects rather than raw `LinkedHashMap`s; dependency-injection frameworks need to distinguish a binding for `Provider<Foo>` from `Provider<Bar>`; and generic event-bus or cache APIs often need to key entries by their full parameterized type, not just the raw class. Understanding this pattern matters both for using these libraries correctly (recognizing why you're asked to write `new TypeReference<List<User>>() {}` instead of just passing `List.class`) and, more rarely, for building your own generic APIs that need the same capability.

## 3. Core concept

```
List<String>.class                         // INVALID -- erasure means there's only one List.class

class TypeRef<T> {
    Type capture() {
        // getGenericSuperclass() reads the SUPERCLASS'S generic signature --
        // this is preserved by the JVM even though a plain type ARGUMENT is not.
        ParameterizedType pt = (ParameterizedType) getClass().getGenericSuperclass();
        return pt.getActualTypeArguments()[0];
    }
}

TypeRef<List<String>> ref = new TypeRef<List<String>>() {}; // ANONYMOUS subclass --
                                                              // its "extends TypeRef<List<String>>"
                                                              // clause IS preserved in its own .class file
ref.capture();  // returns: java.util.List<java.lang.String>  -- full type recovered!
```

The `{}` after the constructor call is essential: it creates a new, anonymous named class extending `TypeRef<List<String>>`, and it is *that class's* declaration (not any instance's erased fields) which the JVM preserves and reflection can read back.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An anonymous subclass extending TypeReference of List of String, whose class file preserves the generic superclass signature, readable via reflection's getGenericSuperclass" >
  <rect x="20" y="30" width="220" height="50" fill="#1c2430" stroke="#8b949e"/>
  <text x="130" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Instance's type argument</text>
  <text x="130" y="65" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">ERASED -- not recoverable</text>

  <rect x="280" y="30" width="340" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Anonymous class's own .class file</text>
  <text x="450" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">"extends TypeReference&lt;List&lt;String&gt;&gt;"</text>
  <text x="450" y="85" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">PRESERVED in the class's generic signature attribute</text>
  <text x="450" y="102" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">readable via getGenericSuperclass()</text>

  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The trick: put the type you want to remember in the SUPERCLASS relationship, not an instance field</text>
</svg>

*The super type token trick smuggles a full generic type through the one part of the class file erasure does not touch: a class's own supertype signature.*

## 5. Runnable example

Scenario: build a tiny generic type-capturing utility from scratch and use it to solve a real problem — starting with a basic proof that the trick works at all, then applying it to a realistic "safe generic cast/deserialize" helper, then handling the harder case of nested and nested-generic type parameters, which is exactly what real JSON libraries need to handle correctly.

### Level 1 — Basic

```java
import java.lang.reflect.*;
import java.util.*;

public class SuperTypeTokenBasic {
    static class TypeReference<T> {
        final Type type;
        protected TypeReference() {
            Type superclass = getClass().getGenericSuperclass();
            this.type = ((ParameterizedType) superclass).getActualTypeArguments()[0];
        }
    }

    public static void main(String[] args) {
        TypeReference<List<String>> ref = new TypeReference<List<String>>() {}; // note the {}
        System.out.println("captured type: " + ref.type);
    }
}
```

**How to run:** `java SuperTypeTokenBasic.java` (JDK 17+).

Expected output:
```
captured type: java.util.List<java.lang.String>
```

Despite `List<String>`'s type argument being erased from any ordinary instance, creating an anonymous subclass of `TypeReference<List<String>>` preserves that exact parameterization in the anonymous class's own generic-signature metadata, which `getGenericSuperclass()` reads back correctly at runtime — proof the trick genuinely recovers full generic type information erasure would otherwise discard.

### Level 2 — Intermediate

```java
import java.lang.reflect.*;
import java.util.*;

public class SuperTypeTokenSafeCast {
    static class TypeReference<T> {
        final Type type;
        protected TypeReference() {
            Type superclass = getClass().getGenericSuperclass();
            this.type = ((ParameterizedType) superclass).getActualTypeArguments()[0];
        }
    }

    // A tiny "registry" keyed by FULL generic type, not just raw Class --
    // distinguishing Map<String,Integer> entries from Map<String,String> entries, for example.
    static final Map<Type, Object> registry = new HashMap<>();

    static <T> void register(TypeReference<T> key, T value) {
        registry.put(key.type, value);
    }

    @SuppressWarnings("unchecked")
    static <T> T lookup(TypeReference<T> key) {
        return (T) registry.get(key.type);
    }

    public static void main(String[] args) {
        register(new TypeReference<List<String>>() {}, List.of("Ada", "Grace"));
        register(new TypeReference<List<Integer>>() {}, List.of(1, 2, 3));

        List<String> names = lookup(new TypeReference<List<String>>() {});
        List<Integer> nums = lookup(new TypeReference<List<Integer>>() {});
        System.out.println("names: " + names);
        System.out.println("nums: " + nums);
    }
}
```

**How to run:** `java SuperTypeTokenSafeCast.java` (JDK 17+).

Expected output:
```
names: [Ada, Grace]
nums: [1, 2, 3]
```

The real-world concern added: without super type tokens, a registry keyed only by raw `Class` (`List.class`) could not distinguish a `List<String>` entry from a `List<Integer>` entry — both erase to the identical `List.class` key; keying the registry by the full `Type` (obtained via the token pattern) lets `register`/`lookup` correctly distinguish these otherwise-identical-at-runtime parameterizations, which is exactly the capability real JSON libraries and dependency-injection frameworks rely on this pattern for.

### Level 3 — Advanced

```java
import java.lang.reflect.*;
import java.util.*;

public class SuperTypeTokenNestedGenerics {
    static class TypeReference<T> {
        final Type type;
        protected TypeReference() {
            Type superclass = getClass().getGenericSuperclass();
            this.type = ((ParameterizedType) superclass).getActualTypeArguments()[0];
        }
    }

    static void describe(Type type) {
        if (type instanceof ParameterizedType pt) {
            System.out.print(((Class<?>) pt.getRawType()).getSimpleName() + "<");
            Type[] args = pt.getActualTypeArguments();
            for (int i = 0; i < args.length; i++) {
                if (i > 0) System.out.print(", ");
                describe(args[i]); // RECURSE -- handles arbitrarily nested generics
            }
            System.out.print(">");
        } else {
            System.out.print(((Class<?>) type).getSimpleName());
        }
    }

    public static void main(String[] args) {
        TypeReference<Map<String, List<Integer>>> ref = new TypeReference<Map<String, List<Integer>>>() {};
        describe(ref.type);
        System.out.println();
    }
}
```

**How to run:** `java SuperTypeTokenNestedGenerics.java` (JDK 17+).

Expected output:
```
Map<String, List<Integer>>
```

The production-flavored hard case: real-world generic types are frequently nested (`Map<String, List<Integer>>`, or deeper), and the reflective `Type` returned by the token pattern is itself a full tree — a `ParameterizedType` whose own type arguments can themselves be further `ParameterizedType`s — so correctly handling arbitrary nesting (as any real JSON deserialization library must) requires recursively walking this `Type` tree rather than assuming a single flat type argument, exactly what the recursive `describe` method demonstrates.

## 6. Walkthrough

Tracing `SuperTypeTokenNestedGenerics.main` end to end:

1. `new TypeReference<Map<String, List<Integer>>>() {}` creates an anonymous class whose declaration is, in effect, `class Anon$1 extends TypeReference<Map<String, List<Integer>>> {}` — this exact `extends` clause, including its full nested generic parameterization, is recorded in the anonymous class's own `.class` file metadata (its "generic signature" attribute), which the JVM preserves regardless of any instance-level erasure.
2. `TypeReference`'s constructor runs, calling `getClass()` — since this is invoked from within the constructor, `getClass()` returns the actual runtime class of `this`, which is the anonymous subclass, not `TypeReference` itself.
3. `getGenericSuperclass()` reads that anonymous class's recorded supertype signature, returning a `ParameterizedType` object representing `TypeReference<Map<String, List<Integer>>>` — this is the reflective object that actually carries the full, un-erased generic information.
4. `getActualTypeArguments()[0]` extracts the single type argument to `TypeReference` in that signature — here, the `Type` object representing `Map<String, List<Integer>>` itself, which is stored in the `type` field for later use.
5. `describe(ref.type)` is called with this `Map<String, List<Integer>>` type object; since it's a `ParameterizedType`, the method prints its raw type's simple name (`Map`) followed by `<`, then recursively calls `describe` on each of its own type arguments in turn.
6. The first type argument, `String`, is not itself a `ParameterizedType` (it has no further generic parameters), so it hits the `else` branch and prints simply `String`; the second type argument, `List<Integer>`, *is* itself a `ParameterizedType`, so `describe` recurses into it exactly as it did for the outer `Map`, printing `List<` then recursing again into `Integer` (which, having no further parameters, prints as plain `Integer`), then closing with `>`.
7. The recursive calls unwind, each closing its own `>`, producing the fully-formed, correctly nested output `Map<String, List<Integer>>` — demonstrating that the super type token pattern doesn't just recover a single flat type argument, but the entire generic type tree, arbitrarily deep, which is exactly the fidelity a real generic-aware JSON deserializer or dependency-injection framework needs to correctly reconstruct complex nested types at runtime.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting the anonymous-class braces (`{}`) after the constructor call — writing `new TypeReference<List<String>>()` instead of `new TypeReference<List<String>>() {}` — silently creates a plain instance of `TypeReference` itself rather than an anonymous subclass, and `getGenericSuperclass()` on a plain `TypeReference` instance returns `TypeReference`'s own erased declaration (`class TypeReference<T>`, no useful type argument), not the caller's intended parameterization — this typically manifests as a confusing `ClassCastException` or an unexpected raw type at runtime, with no compile-time warning that the trick silently failed.

- Super type tokens recover a generic type's full parameterization at runtime by exploiting the one place erasure doesn't apply: a class's supertype signature, as recorded in its own `.class` file.
- The pattern requires creating an anonymous subclass (`new TypeReference<List<String>>() {}`, note the `{}`) — omitting the braces silently defeats the trick with no compile error.
- `getGenericSuperclass()` plus `ParameterizedType.getActualTypeArguments()` is the reflective API that reads back the preserved type; nested generics require recursively walking the resulting `Type` tree.
- This is exactly the mechanism behind Jackson's `TypeReference`, Gson's `TypeToken`, and similar constructs in dependency-injection frameworks — recognizing the pattern explains why these APIs ask you to instantiate an anonymous subclass rather than simply pass a `Class` object.
- See [type erasure](0359-type-erasure.md) for the underlying limitation this pattern works around, and [heap pollution](0951-heap-pollution.md) for a different, related consequence of erasure's interaction with generics and arrays.
