---
card: java
gi: 337
slug: constructor-reflection-newinstance
title: Constructor reflection & newInstance()
---

## 1. What it is

Constructor reflection uses `java.lang.reflect.Constructor` to look up and invoke a class's constructor by its parameter types, at runtime, creating new instances without the compiler ever seeing a `new SomeClass(...)` expression. `Class.getDeclaredConstructor(parameterTypes...)` finds a specific constructor, and `constructor.newInstance(args...)` calls it, returning a freshly-built object — even for a `private` constructor, once `setAccessible(true)` has been applied.

```java
import java.lang.reflect.Constructor;

public class ConstructorReflectionDemo {
    static class Point {
        int x, y;
        public Point(int x, int y) { this.x = x; this.y = y; }
        public String toString() { return "(" + x + ", " + y + ")"; }
    }

    public static void main(String[] args) throws Exception {
        Constructor<Point> ctor = Point.class.getDeclaredConstructor(int.class, int.class);
        Point p = ctor.newInstance(3, 4);
        System.out.println(p);
    }
}
```

`getDeclaredConstructor(int.class, int.class)` finds the constructor whose parameters match exactly `(int, int)`, and `newInstance(3, 4)` invokes it, equivalent to `new Point(3, 4)` but resolved entirely at runtime.

## 2. Why & when

Ordinary object creation (`new SomeClass(...)`) requires the compiler to know the class and constructor signature ahead of time. Constructor reflection exists for the cases where the class to instantiate is only known as data — a class name loaded via `Class.forName`, a plugin registered by configuration, or a framework that needs to build objects of types it has never seen at compile time.

- **Frameworks that instantiate arbitrary classes** — dependency injection containers, ORMs building entity objects from database rows, and JSON deserializers reconstructing objects all need to call *some* constructor without knowing the class in advance.
- **Building instances of dynamically-loaded classes** — this is the natural next step after using `Class.forName` to load a class by name: once you have the `Class` object, constructor reflection is how you actually create an instance of it.
- **Working around limited or absent public constructors** — some frameworks legitimately need to invoke a `private` no-argument constructor (a common pattern for classes meant to be built only through a factory or deserialization).

Legacy code sometimes calls the deprecated `Class.newInstance()` directly; the modern idiom is always `getDeclaredConstructor().newInstance()`, because `newInstance()` on `Class` only works with a public no-argument constructor and hides checked exceptions in a confusing way (it can throw the target constructor's own exceptions without declaring them).

## 3. Core concept

```java
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;

public class ConstructorReflectionCore {
    static class Account {
        int balance;
        public Account(int startingBalance) {
            if (startingBalance < 0) throw new IllegalArgumentException("balance can't be negative");
            this.balance = startingBalance;
        }
    }

    public static void main(String[] args) throws Exception {
        Constructor<Account> ctor = Account.class.getDeclaredConstructor(int.class);
        try {
            Account bad = ctor.newInstance(-5); // triggers the constructor's own validation
            System.out.println(bad.balance);
        } catch (InvocationTargetException e) {
            System.out.println("Constructor rejected the arguments: " + e.getCause().getMessage());
        }
    }
}
```

**How to run:** `java ConstructorReflectionCore.java`

Just like method reflection, any exception the constructor itself throws (here, `IllegalArgumentException` from its own validation logic) is wrapped in `InvocationTargetException` by `newInstance()` — the real exception is only available via `getCause()`.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="getDeclaredConstructor finds a constructor by parameter types; newInstance builds an object, wrapping any thrown exception in InvocationTargetException">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="250" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="145" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">getDeclaredConstructor(types...)</text>

  <text x="285" y="52" fill="#8b949e" font-size="12">→ Constructor object</text>

  <rect x="20" y="85" width="250" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="145" y="107" fill="#6db33f" font-size="10" text-anchor="middle">newInstance(args...)</text>

  <text x="440" y="52" fill="#8b949e" font-size="9">success → new instance</text>
  <text x="440" y="107" fill="#f85149" font-size="9">failure → InvocationTargetException</text>
</svg>

## 5. Runnable example

Scenario: a tiny generic object factory that builds instances from a class name and constructor arguments, evolved from a single hardcoded call, into one with proper error handling, into a production-style factory that also supports private constructors and reports each distinct failure mode separately.

### Level 1 — Basic

```java
import java.lang.reflect.Constructor;

public class FactoryBasic {
    static class Point {
        int x, y;
        public Point(int x, int y) { this.x = x; this.y = y; }
        public String toString() { return "(" + x + ", " + y + ")"; }
    }

    public static void main(String[] args) throws Exception {
        Constructor<Point> ctor = Point.class.getDeclaredConstructor(int.class, int.class);
        Point p = ctor.newInstance(1, 2);
        System.out.println(p);
    }
}
```

**How to run:** `java FactoryBasic.java`

This builds exactly one hardcoded object reflectively, with no error handling — if the constructor didn't exist with those exact parameter types, or if construction failed, the whole program would simply crash with an unhandled exception.

### Level 2 — Intermediate

```java
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;

public class FactoryIntermediate {
    static class Point {
        int x, y;
        public Point(int x, int y) {
            if (x < 0 || y < 0) throw new IllegalArgumentException("coordinates must be non-negative");
            this.x = x; this.y = y;
        }
        public String toString() { return "(" + x + ", " + y + ")"; }
    }

    public static void main(String[] args) {
        create(1, 2);
        create(-1, 5); // triggers the constructor's own validation
    }

    static void create(int x, int y) {
        try {
            Constructor<Point> ctor = Point.class.getDeclaredConstructor(int.class, int.class);
            Point p = ctor.newInstance(x, y);
            System.out.println("Created: " + p);
        } catch (NoSuchMethodException e) {
            System.out.println("No matching constructor found.");
        } catch (InvocationTargetException e) {
            System.out.println("Construction failed: " + e.getCause().getMessage());
        } catch (ReflectiveOperationException e) {
            System.out.println("Reflection error: " + e.getMessage());
        }
    }
}
```

**How to run:** `java FactoryIntermediate.java`

The second call's negative coordinates trigger the constructor's own validation, and because that failure is now caught specifically as `InvocationTargetException`, the code reports the real validation message via `getCause()` instead of crashing the whole program.

### Level 3 — Advanced

```java
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;

public class FactoryAdvanced {
    static class InternalWidget {
        String label;
        private InternalWidget(String label) { this.label = label; } // deliberately private
        public String toString() { return "Widget[" + label + "]"; }
    }

    public static void main(String[] args) {
        Object w1 = create(InternalWidget.class, new Class<?>[]{String.class}, "gadget");
        System.out.println(w1);
        create(InternalWidget.class, new Class<?>[]{Integer.class}, 42); // wrong parameter type on purpose
    }

    static Object create(Class<?> type, Class<?>[] paramTypes, Object... args) {
        try {
            Constructor<?> ctor = type.getDeclaredConstructor(paramTypes);
            ctor.setAccessible(true); // required since InternalWidget's constructor is private
            return ctor.newInstance(args);
        } catch (NoSuchMethodException e) {
            System.out.println(type.getSimpleName() + " -> no constructor matching " + java.util.Arrays.toString(paramTypes));
            return null;
        } catch (InvocationTargetException e) {
            System.out.println(type.getSimpleName() + " -> constructor threw: " + e.getCause());
            return null;
        } catch (ReflectiveOperationException e) {
            System.out.println(type.getSimpleName() + " -> reflection error: " + e.getMessage());
            return null;
        }
    }
}
```

**How to run:** `java FactoryAdvanced.java`

`ctor.setAccessible(true)` is what makes it possible to call `InternalWidget`'s deliberately `private` constructor from outside its own class; the second `create` call deliberately passes `Integer.class` as the parameter type when the real constructor expects `String.class`, demonstrating that `NoSuchMethodException` is reported cleanly instead of crashing the factory.

## 6. Walkthrough

Execution starts in `main`, which calls `create(InternalWidget.class, new Class<?>[]{String.class}, "gadget")` first.

Inside `create`, `type.getDeclaredConstructor(paramTypes)` looks up `InternalWidget`'s constructor accepting exactly one `String` parameter — this succeeds, returning a `Constructor<?>` object, even though that constructor is `private`. `ctor.setAccessible(true)` overrides the normal access check. `ctor.newInstance(args)` — where `args` is `{"gadget"}` — then actually runs the constructor body, setting `label = "gadget"` and returning the new `InternalWidget` instance, which `create` returns up to `main`.

`main` prints the returned object via its `toString()`, producing `Widget[gadget]`.

`main` then calls `create(InternalWidget.class, new Class<?>[]{Integer.class}, 42)`. This time, `type.getDeclaredConstructor(paramTypes)` searches for a constructor accepting exactly one `Integer` parameter — no such constructor exists (the real one takes a `String`), so `getDeclaredConstructor` itself throws `NoSuchMethodException` before `setAccessible` or `newInstance` are ever reached. The `catch (NoSuchMethodException e)` block runs, printing `InternalWidget -> no constructor matching [class java.lang.Integer]`, and `create` returns `null` — the constructor body never executes at all for this call.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="first call finds the private constructor by exact parameter type, makes it accessible, and constructs an object; second call fails at the lookup stage because no constructor matches the wrong parameter type">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">create(InternalWidget, [String], "gadget"):</text>
  <text x="20" y="52" fill="#6db33f" font-size="10">  getDeclaredConstructor([String]) OK -&gt; setAccessible(true) -&gt; newInstance("gadget") -&gt; Widget[gadget]</text>
  <text x="20" y="85" fill="#f85149" font-size="10">create(InternalWidget, [Integer], 42):</text>
  <text x="20" y="107" fill="#f85149" font-size="10">  getDeclaredConstructor([Integer]) -&gt; NO MATCH -&gt; NoSuchMethodException -&gt; newInstance never reached</text>
</svg>

## 7. Gotchas & takeaways

> `getDeclaredConstructor(paramTypes)` matches parameter types *exactly* — passing `Integer.class` when the constructor declares `int.class` (a primitive) will also fail to match, since reflection distinguishes boxed and primitive types precisely, unlike normal autoboxing at a direct call site.

- Prefer `getDeclaredConstructor().newInstance()` over the deprecated `Class.newInstance()` — the latter only works with public no-arg constructors and has confusing exception-handling behavior.
- Any exception thrown inside the constructor's own body is wrapped in `InvocationTargetException`; unwrap it with `getCause()` to see the real failure.
- `setAccessible(true)` is required to call a `private`/`protected` constructor reflectively, exactly as with field and method reflection.
- `NoSuchMethodException` means the lookup itself failed (no constructor with that exact parameter list exists) — this happens before any object is constructed, and before `InvocationTargetException` even becomes possible.
- Constructor reflection is the natural companion to `Class.forName` — together they let a program go from "a class name as a string" all the way to "a working instance," which is exactly what plugin systems and deserialization frameworks need.
