---
card: java
gi: 384
slug: meta-annotation-inherited
title: 'Meta-annotation @Inherited'
---

## 1. What it is

`@Inherited` is a meta-annotation that makes a custom annotation, when applied to a **class**, automatically apply to that class's subclasses as well — without the subclass needing to repeat the annotation itself. It works only for class-level annotations (`@Target(ElementType.TYPE)`) and only through class inheritance (`extends`); it has no effect on methods, fields, or interfaces, and does not propagate through interface implementation.

## 2. Why & when

By default, annotations are not inherited: if a superclass is annotated `@Loggable` and a subclass extends it without repeating `@Loggable` itself, reflection checking the *subclass* for `@Loggable` (using the ordinary lookup) finds nothing — the annotation is treated as belonging only to the exact class it was written on. `@Inherited` changes this specific behaviour: when the annotated class's own annotation is looked up via `Class.getAnnotation(...)` (not `getDeclaredAnnotation`) on a subclass, and the subclass itself doesn't have its own copy of that annotation, Java walks up the class hierarchy and returns the superclass's inherited one instead.

This is useful for framework-style base classes where a marking on a base type is meant to apply to everything that extends it — for example, a base test class marked `@Category("integration")` that all its concrete test subclasses should inherit automatically, without each one needing to repeat the marking. It's a narrow, specific feature: it only ever applies to class-level annotations found via `getAnnotation` (never `getDeclaredAnnotation`, which always reports only what's actually written on the exact class being asked about), and it does not apply to methods or fields at all, regardless of `@Inherited`.

## 3. Core concept

```java
import java.lang.annotation.*;

public class InheritedDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @Inherited // makes this propagate to subclasses automatically
    @interface Loggable {
    }

    @Loggable
    static class BaseService { }

    static class UserService extends BaseService { } // no @Loggable written here at all

    public static void main(String[] args) {
        System.out.println("UserService has @Loggable (getAnnotation): " +
                UserService.class.isAnnotationPresent(Loggable.class));
        System.out.println("UserService has @Loggable (getDeclaredAnnotation): " +
                (UserService.class.getDeclaredAnnotation(Loggable.class) != null));
    }
}
```

**How to run:** `java InheritedDemo.java`

`UserService` never writes `@Loggable` itself, but because `Loggable` is `@Inherited` and `BaseService` (its superclass) has it, `isAnnotationPresent`/`getAnnotation` on `UserService` finds it anyway — reporting `true`. `getDeclaredAnnotation`, which only ever looks at what's *actually written* on the exact class asked about, correctly reports it as absent (`false`) on `UserService`, since `UserService`'s own source never mentions `@Loggable`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an Inherited class-level annotation on a superclass is found by getAnnotation on a subclass that never wrote it, but not by getDeclaredAnnotation">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="55" fill="#6db33f" font-size="10" text-anchor="middle">@Loggable class BaseService</text>

  <line x1="140" y1="70" x2="140" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#dn)"/>
  <text x="150" y="85" fill="#79c0ff" font-size="9">extends</text>

  <rect x="30" y="100" width="220" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="140" y="125" fill="#8b949e" font-size="10" text-anchor="middle">class UserService  (no @Loggable written)</text>

  <text x="290" y="60" fill="#e6edf3" font-size="10">getAnnotation(UserService) -&gt; finds @Loggable (inherited)</text>
  <text x="290" y="130" fill="#f85149" font-size="10">getDeclaredAnnotation(UserService) -&gt; null (not written here)</text>

  <defs><marker id="dn" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

## 5. Runnable example

Scenario: a `@RequiresTransaction` marker for a service-layer base class, evolved from a non-inherited version that must be repeated on every subclass, through adding `@Inherited` to remove that repetition, to a version demonstrating `@Inherited`'s real limitation: it does not extend to interfaces at all.

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class TransactionNotInherited {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    // no @Inherited -- every subclass must repeat this itself
    @interface RequiresTransaction {
    }

    @RequiresTransaction
    static class BaseRepository { }

    static class UserRepository extends BaseRepository { } // forgot to repeat @RequiresTransaction!

    public static void main(String[] args) {
        System.out.println("UserRepository requires transaction: " +
                UserRepository.class.isAnnotationPresent(RequiresTransaction.class));
    }
}
```

**How to run:** `java TransactionNotInherited.java`

Without `@Inherited`, `UserRepository` needed to repeat `@RequiresTransaction` itself to be recognised as needing one — since it doesn't, `isAnnotationPresent` reports `false`, even though logically every repository extending `BaseRepository` should require a transaction just as much as the base class does.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class TransactionInherited {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @Inherited // the fix: subclasses now automatically inherit this
    @interface RequiresTransaction {
    }

    @RequiresTransaction
    static class BaseRepository { }

    static class UserRepository extends BaseRepository { } // still doesn't repeat it -- doesn't need to

    public static void main(String[] args) {
        System.out.println("UserRepository requires transaction: " +
                UserRepository.class.isAnnotationPresent(RequiresTransaction.class));
    }
}
```

**How to run:** `java TransactionInherited.java`

Adding `@Inherited` to `RequiresTransaction`'s own declaration fixes this without touching `UserRepository` at all — reflection now correctly reports `true`, since `getAnnotation`/`isAnnotationPresent` walks up to `BaseRepository` and finds the inherited annotation there.

### Level 3 — Advanced

```java
import java.lang.annotation.*;

public class InheritedInterfaceLimitation {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @Inherited
    @interface RequiresTransaction {
    }

    @RequiresTransaction
    interface Repository { } // @Inherited does NOT propagate through interfaces at all

    static class ProductRepository implements Repository { } // implements, doesn't extend

    @RequiresTransaction
    static class BaseRepository { }

    static class OrderRepository extends BaseRepository { } // extends -- @Inherited DOES apply here

    public static void main(String[] args) {
        System.out.println("ProductRepository (via interface): " +
                ProductRepository.class.isAnnotationPresent(RequiresTransaction.class));
        System.out.println("OrderRepository (via class extends): " +
                OrderRepository.class.isAnnotationPresent(RequiresTransaction.class));
    }
}
```

**How to run:** `java InheritedInterfaceLimitation.java`

This directly demonstrates `@Inherited`'s specific, narrow scope: `ProductRepository` implements an interface carrying `@RequiresTransaction`, but `@Inherited` explicitly does not propagate through interface implementation, so `isAnnotationPresent` reports `false` for it — while `OrderRepository`, which genuinely `extends` a class carrying the same annotation, correctly reports `true`, matching Level 2's behaviour.

## 6. Walkthrough

Execution starts in `main`. `ProductRepository.class.isAnnotationPresent(RequiresTransaction.class)` is evaluated first. Internally, this checks `ProductRepository`'s own declared annotations (finds none — it never wrote `@RequiresTransaction` itself), then, because `RequiresTransaction` is `@Inherited`, checks up the **class** hierarchy. `ProductRepository`'s superclass is implicitly `Object` (it only *implements* `Repository`, an interface, which is a completely different relationship). `Object` has no `@RequiresTransaction` either. Since `@Inherited` is explicitly documented to apply only through superclass (`extends`) relationships, never through interface implementation, the fact that `Repository` (the interface) carries `@RequiresTransaction` is irrelevant here — it is never consulted at all. The result is `false`.

`OrderRepository.class.isAnnotationPresent(RequiresTransaction.class)` runs next. `OrderRepository` has no declared `@RequiresTransaction` of its own, but its actual superclass, `BaseRepository` (a real `extends` relationship), does carry `@RequiresTransaction`. Because this is a genuine class-inheritance relationship, `@Inherited`'s propagation applies here: the lookup walks from `OrderRepository` up to `BaseRepository`, finds the annotation there, and returns it. The result is `true`.

This contrast is the entire point of the example: `@Inherited` is specifically and only about class-to-subclass inheritance via `extends` — it was designed around the classic base-class-marks-its-family-of-subclasses use case, and interfaces, despite conceptually feeling similar ("implementing a marked interface" versus "extending a marked class"), are deliberately excluded from its behaviour.

Expected output:
```
ProductRepository (via interface): false
OrderRepository (via class extends): true
```

## 7. Gotchas & takeaways

> `@Inherited` never applies to interfaces — annotating an interface and having a class `implements` it does not cause the annotation to be inherited, even though it might seem analogous to extending a class. If you need annotation-like behaviour that propagates through interface implementation, you must write your own reflection logic to walk the implemented interfaces explicitly.

- `@Inherited` only affects class-level annotations (`@Target(ElementType.TYPE)`) looked up via `getAnnotation`/`isAnnotationPresent` — it has no effect on `getDeclaredAnnotation`, which always reports only what's actually written on the exact class asked about.
- It propagates strictly through `extends` (class inheritance) — never through `implements` (interface implementation), and never for method- or field-level annotations regardless of how they're declared.
- Without `@Inherited`, a subclass must repeat an annotation itself for reflection to find it on that subclass; with `@Inherited`, the lookup automatically walks up to the nearest superclass that has it.
- Useful for framework base classes where a marking on the base type is meant to apply uniformly to every subclass without requiring each one to repeat it.
- Given its narrow scope (classes only, `extends` only), don't assume `@Inherited` solves general "annotation propagation" needs — for interfaces, or for method/field-level propagation, you need custom reflection logic that explicitly walks the relevant hierarchy yourself.
