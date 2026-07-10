---
card: java
gi: 983
slug: reflection-api-deep-dive
title: Reflection API deep dive
---

## 1. What it is

Reflection is the ability of a running Java program to inspect and manipulate its own classes, methods, fields, and constructors at runtime, as ordinary objects — `Class<?>`, `Method`, `Field`, and `Constructor` from `java.lang.reflect` let you discover a class's structure (what methods it has, what fields, what their types and modifiers are) and invoke methods, read or write fields, or construct instances, all without having known any of that structure at compile time. `obj.getClass().getMethod("someMethod").invoke(obj)` calls `someMethod` on `obj` exactly as `obj.someMethod()` would, but the method's name and existence are only resolved at runtime, from a string — this is the essential thing reflection provides: turning what's normally fixed, compile-time-checked structure into something a program can query and act upon dynamically.

## 2. Why & when

Reflection is the mechanism underlying an enormous amount of everyday Java infrastructure that would otherwise be impossible to write generically: a dependency-injection framework (Spring, for instance) uses reflection to discover a class's constructors and fields, deciding what to inject without that framework's own code ever having been compiled against your specific classes; a JSON library uses reflection to discover a POJO's fields and generate/parse JSON without needing hand-written serialization code for every single class; a test framework uses reflection to find and invoke methods annotated `@Test`, without ever needing to know those methods' names in advance. Reach for reflection directly in your own code specifically when you're building this kind of generic, framework-style infrastructure meant to operate uniformly over arbitrary, unknown-in-advance classes — for ordinary application code, calling a method directly (`obj.someMethod()`) is always faster (reflection has real runtime overhead per call, though the JIT compiler can optimize much of this away for repeated reflective calls) and, critically, checked by the compiler, catching a typo or type mismatch at compile time rather than as a runtime `NoSuchMethodException`.

## 3. Core concept

```java
class Point {
    private int x, y;
    public Point(int x, int y) { this.x = x; this.y = y; }
    public int getX() { return x; }
}

Class<?> clazz = Point.class;                    // the Class object representing Point itself
Constructor<?> ctor = clazz.getConstructor(int.class, int.class);
Object point = ctor.newInstance(3, 4);            // constructs a Point WITHOUT "new Point(3, 4)" in source

Method getX = clazz.getMethod("getX");
Object result = getX.invoke(point);               // calls getX() dynamically -- result is 3

Field xField = clazz.getDeclaredField("x");        // 'x' is PRIVATE -- getDeclaredField sees it anyway
xField.setAccessible(true);                        // must explicitly bypass access checks
int xValue = (int) xField.get(point);              // reads the PRIVATE field directly
```

Reflection can discover and invoke a class's public API exactly as ordinary code could, but it can also — with an explicit, deliberate `setAccessible(true)` call — bypass normal access modifiers entirely, reaching private fields and methods that ordinary compiled code could never touch directly.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Class object providing reflective access to a class's constructors, methods, and fields, letting code construct instances and invoke methods purely from string names at runtime" >
  <rect x="20" y="30" width="140" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Class&lt;Point&gt;</text>
  <text x="90" y="70" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getConstructor(...)</text>
  <text x="90" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getMethod("getX")</text>
  <text x="90" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getDeclaredField("x")</text>

  <rect x="220" y="30" width="140" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="290" y="49" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">ctor.newInstance(3,4)</text>
  <rect x="220" y="70" width="140" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="290" y="89" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">getX.invoke(point)</text>

  <rect x="420" y="50" width="180" height="30" fill="#1c2430" stroke="#f0883e"/>
  <text x="510" y="69" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">a real Point instance, result=3</text>

  <line x1="160" y1="50" x2="220" y2="45" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="160" y1="85" x2="220" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="360" y1="60" x2="420" y2="65" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*Reflection lets code discover and use a class's structure purely from names, resolved at runtime, without having been compiled against that specific class.*

## 5. Runnable example

Scenario: build a small generic object-inspection and construction utility, evolving from a basic reflective method call, to a realistic generic factory constructing arbitrary objects from a class name and arguments, to a more advanced case using reflection to build a simple, generic property-copying utility that works uniformly across any object type.

### Level 1 — Basic

```java
import java.lang.reflect.*;

public class ReflectionBasic {
    static class Greeting {
        public String greet(String name) { return "Hello, " + name + "!"; }
    }

    public static void main(String[] args) throws Exception {
        Greeting greeting = new Greeting();

        Class<?> clazz = greeting.getClass();
        Method method = clazz.getMethod("greet", String.class);
        Object result = method.invoke(greeting, "Ada");

        System.out.println("reflective call result: " + result);
    }
}
```

**How to run:** `java ReflectionBasic.java` (JDK 17+).

Expected output:
```
reflective call result: Hello, Ada!
```

`clazz.getMethod("greet", String.class)` looks up the `greet` method purely by its name and parameter types, as strings and `Class` objects rather than compile-time-checked syntax, and `method.invoke(greeting, "Ada")` calls it dynamically — functionally identical to `greeting.greet("Ada")`, but resolved entirely at runtime.

### Level 2 — Intermediate

```java
import java.lang.reflect.*;

public class ReflectionGenericFactory {
    static class Circle {
        double radius;
        Circle(double radius) { this.radius = radius; }
        public String toString() { return "Circle(radius=" + radius + ")"; }
    }
    static class Square {
        double side;
        Square(double side) { this.side = side; }
        public String toString() { return "Square(side=" + side + ")"; }
    }

    static Object createInstance(String className, Object... args) throws Exception {
        Class<?> clazz = Class.forName(className);
        Class<?>[] paramTypes = new Class<?>[args.length];
        for (int i = 0; i < args.length; i++) {
            paramTypes[i] = args[i].getClass() == Double.class ? double.class : args[i].getClass();
        }
        Constructor<?> ctor = clazz.getDeclaredConstructor(paramTypes);
        return ctor.newInstance(args);
    }

    public static void main(String[] args) throws Exception {
        Object circle = createInstance("ReflectionGenericFactory$Circle", 5.0);
        Object square = createInstance("ReflectionGenericFactory$Square", 3.0);
        System.out.println(circle);
        System.out.println(square);
    }
}
```

**How to run:** `java ReflectionGenericFactory.java` (JDK 17+).

Expected output:
```
Circle(radius=5.0)
Square(side=3.0)
```

The real-world concern added: `createInstance` constructs an object of *any* class, given only its fully-qualified name as a string plus constructor arguments — this generic factory pattern is exactly how a plugin system, a dependency-injection container, or a configuration-driven object-creation framework works, instantiating classes it was never compiled against, discovered purely by name at runtime, often from an external configuration file.

### Level 3 — Advanced

```java
import java.lang.reflect.*;

public class ReflectionPropertyCopier {
    static class SourceData {
        private String name = "Ada";
        private int age = 30;
    }
    static class TargetData {
        private String name;
        private int age;
        public String toString() { return "TargetData[name=" + name + ", age=" + age + "]"; }
    }

    // A GENERIC utility that copies same-named fields from ANY source object
    // to ANY target object, regardless of the specific classes involved --
    // works purely through reflection, with no compile-time knowledge of either type.
    static void copyMatchingFields(Object source, Object target) throws Exception {
        for (Field sourceField : source.getClass().getDeclaredFields()) {
            try {
                Field targetField = target.getClass().getDeclaredField(sourceField.getName());
                sourceField.setAccessible(true);
                targetField.setAccessible(true);
                targetField.set(target, sourceField.get(source));
            } catch (NoSuchFieldException e) {
                // target doesn't have a matching field -- skip it, this is a best-effort copy
            }
        }
    }

    public static void main(String[] args) throws Exception {
        SourceData source = new SourceData();
        TargetData target = new TargetData();

        copyMatchingFields(source, target);

        System.out.println(target);
    }
}
```

**How to run:** `java ReflectionPropertyCopier.java` (JDK 17+).

Expected output:
```
TargetData[name=Ada, age=30]
```

The production-flavored hard case: `copyMatchingFields` works generically across any two unrelated classes, discovering `SourceData`'s private fields via `getDeclaredFields()`, matching each by name against `TargetData`'s own fields, and copying values across using `setAccessible(true)` to bypass the normal `private` access restriction — this is exactly the kind of generic, class-structure-agnostic logic that mapping libraries (like MapStruct's reflection-based alternatives, or simpler bean-copying utilities) rely on, requiring no hand-written, per-class-pair copying code at all.

## 6. Walkthrough

Tracing `copyMatchingFields(source, target)` end to end from `ReflectionPropertyCopier.main`:

1. `source.getClass().getDeclaredFields()` returns an array of `Field` objects representing every field declared directly on `SourceData` — including private ones, since `getDeclaredFields` (unlike `getFields`) returns fields regardless of their access modifier, though actually *reading* a private field's value still requires bypassing the access check separately.
2. The loop's first iteration processes the `name` field: `target.getClass().getDeclaredField("name")` looks up a field with the exact same name on `TargetData` — since `TargetData` does declare a `name` field, this lookup succeeds, returning that field's own `Field` object.
3. `sourceField.setAccessible(true)` and `targetField.setAccessible(true)` are both called — since both fields are declared `private`, ordinary reflective access would otherwise throw `IllegalAccessException`; this call explicitly requests the JVM bypass that normal access-control check for these specific `Field` objects.
4. `sourceField.get(source)` reads the actual current value of `source`'s `name` field (`"Ada"`), and `targetField.set(target, ...)` writes that value into `target`'s own `name` field — this is a direct, reflective field read-then-write, entirely independent of any getter/setter methods either class may or may not define.
5. The loop's second iteration processes the `age` field identically — `target.getClass().getDeclaredField("age")` succeeds, both fields are made accessible, and `30` is copied from `source` to `target`.
6. Because `SourceData` has exactly two declared fields, both of which happen to have matching names on `TargetData`, the loop completes having copied both values without ever hitting the `catch (NoSuchFieldException e)` branch — printing `target` afterward shows both fields correctly populated (`TargetData[name=Ada, age=30]`), confirming this entirely generic, name-matching-based copy succeeded without either `SourceData` or `TargetData` needing any shared interface, common superclass, or hand-written copying logic between them at all.

## 7. Gotchas & takeaways

> **Gotcha:** `Field.setAccessible(true)` can fail at runtime with `InaccessibleObjectException` on modules that don't explicitly `opens` the target package to reflection (a Java Platform Module System restriction introduced in Java 9, strengthened in later versions specifically to limit unrestricted reflective access to a module's internals) — code relying on deep reflective access into a *different* module's private state should be aware this access can be restricted at the module boundary, requiring an explicit `opens` directive in that module's `module-info.java`, or the `--add-opens` command-line flag as a workaround.

- Reflection lets a program inspect and manipulate classes, methods, fields, and constructors at runtime, as ordinary objects (`Class`, `Method`, `Field`, `Constructor`), resolving structure and behavior from names rather than compile-time-checked syntax.
- It underlies most generic, framework-style Java infrastructure — dependency injection, JSON serialization libraries, test frameworks — that must operate uniformly over classes it was never compiled against.
- `setAccessible(true)` explicitly bypasses normal access-modifier checks, letting reflective code read or write private fields and invoke private methods that ordinary compiled code could never reach directly.
- Reflective calls have real runtime overhead compared to direct method calls and lose compile-time type checking — prefer direct calls in ordinary application code, reserving reflection for genuinely generic infrastructure code.
- Since Java 9's module system, deep reflective access into another module's internals can be restricted unless that module explicitly `opens` the relevant package, or the JVM is launched with `--add-opens`.
- See [dynamic proxies (java.lang.reflect.Proxy)](0985-dynamic-proxies-java-lang-reflect-proxy.md) for a specific, powerful application of reflection — generating an entire interface implementation at runtime — and [MethodHandles & VarHandles](0984-methodhandles-varhandles.md) for a more modern, often faster alternative to some classic reflection use cases.
