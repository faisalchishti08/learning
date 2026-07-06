---
card: java
gi: 334
slug: class-forname
title: Class.forName()
---

## 1. What it is

`Class.forName("fully.qualified.ClassName")` loads a class by its name, given only as a `String`, at runtime — it triggers class loading (and static initialization) if the class hasn't been loaded yet, and returns the corresponding `Class` object. This is the way to obtain a `Class` reference when you only know the type's name as data (read from a config file, a command-line argument, a database column) rather than having a compile-time reference to the type itself.

```java
public class ForNameDemo {
    public static void main(String[] args) throws ClassNotFoundException {
        Class<?> stringClass = Class.forName("java.lang.String");
        System.out.println("Loaded: " + stringClass.getName());
    }
}
```

`Class.forName` throws the checked exception `ClassNotFoundException` if no class with that exact name is on the classpath — a real, expected failure mode whenever the name comes from external, untrusted, or misconfigured input.

## 2. Why & when

Some designs genuinely don't know which concrete class they need until runtime — a plugin system reading a class name from a config file, a JDBC driver being loaded by name (historically required before JDBC 4's automatic driver discovery), or a serialization framework reconstructing an object whose type name was stored alongside its data. `Class.forName` is the bridge from "a class name as a string" to "a usable `Class` object" you can then instantiate or inspect.

- **Plugin and extension systems** — reading a fully-qualified class name from configuration and loading it dynamically, so new implementations can be added without changing the code that loads them.
- **Framework internals** — many frameworks (ORMs, dependency injection containers, serialization libraries) use `Class.forName` internally to instantiate types they only know about as configured strings.
- **Explicitly triggering static initialization** — `Class.forName(name)` (the single-argument form) guarantees the class's static initializer block runs, which matters for classes whose static blocks register something as a side effect (like older JDBC drivers registering themselves).

Because it works from a `String`, `Class.forName` bypasses compile-time type checking entirely — a typo in the class name, or a class that simply isn't present on the classpath at runtime, only fails when that line actually executes, not when the code is compiled. This makes it inherently riskier than using `.class` literals wherever a compile-time reference is possible.

## 3. Core concept

```java
public class ForNameCore {
    public static void main(String[] args) {
        String[] classNames = { "java.util.ArrayList", "java.lang.NoSuchClassEver" };
        for (String name : classNames) {
            try {
                Class<?> clazz = Class.forName(name);
                System.out.println(name + " loaded successfully: " + clazz.getSimpleName());
            } catch (ClassNotFoundException e) {
                System.out.println(name + " could not be found on the classpath.");
            }
        }
    }
}
```

**How to run:** `java ForNameCore.java`

The first name resolves to a real JDK class and loads successfully; the second is a deliberately fake name, demonstrating that `ClassNotFoundException` is a normal, expected outcome to handle whenever a class name originates outside the compiler's view.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a class name string is looked up on the classpath at runtime, either resolving to a Class object or failing with ClassNotFoundException">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="45" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="70" fill="#79c0ff" font-size="10" text-anchor="middle">"com.example.Widget"</text>

  <text x="235" y="70" fill="#8b949e" font-size="12">Class.forName() →</text>

  <rect x="400" y="20" width="170" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="485" y="42" fill="#6db33f" font-size="9" text-anchor="middle">found: Class object</text>

  <rect x="400" y="65" width="170" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="485" y="87" fill="#f85149" font-size="9" text-anchor="middle">not found: exception</text>
</svg>

## 5. Runnable example

Scenario: a tiny plugin loader that reads a class name and creates a new instance of it, evolved from a hardcoded, unchecked attempt, into a version with proper error handling, into a production-style loader that validates the loaded type actually implements an expected interface before trusting it.

### Level 1 — Basic

```java
public class PluginLoaderBasic {
    public interface Greeter { String greet(); }

    public static class EnglishGreeter implements Greeter {
        public String greet() { return "Hello!"; }
    }

    public static void main(String[] args) throws Exception {
        String className = "PluginLoaderBasic$EnglishGreeter"; // nested class binary name
        Class<?> clazz = Class.forName(className);
        Object instance = clazz.getDeclaredConstructor().newInstance();
        Greeter greeter = (Greeter) instance; // unchecked cast -- assumes correctness
        System.out.println(greeter.greet());
    }
}
```

**How to run:** `java PluginLoaderBasic.java`

This works only because the caller happens to know `className` really does implement `Greeter` — if the configured class name pointed at some unrelated class, the cast to `Greeter` would throw an unhandled `ClassCastException` at runtime, with no earlier warning.

### Level 2 — Intermediate

```java
public class PluginLoaderIntermediate {
    public interface Greeter { String greet(); }

    public static class EnglishGreeter implements Greeter {
        public String greet() { return "Hello!"; }
    }

    public static void main(String[] args) {
        String[] namesToTry = {
                "PluginLoaderIntermediate$EnglishGreeter",
                "PluginLoaderIntermediate$DoesNotExist"
        };
        for (String className : namesToTry) {
            loadAndGreet(className);
        }
    }

    static void loadAndGreet(String className) {
        try {
            Class<?> clazz = Class.forName(className);
            Object instance = clazz.getDeclaredConstructor().newInstance();
            Greeter greeter = (Greeter) instance;
            System.out.println(className + " -> " + greeter.greet());
        } catch (ClassNotFoundException e) {
            System.out.println(className + " -> class not found.");
        } catch (ReflectiveOperationException e) {
            System.out.println(className + " -> could not instantiate: " + e.getMessage());
        } catch (ClassCastException e) {
            System.out.println(className + " -> loaded, but does not implement Greeter.");
        }
    }
}
```

**How to run:** `java PluginLoaderIntermediate.java`

Each of the three realistic failure points — class not found, unable to construct an instance (e.g., no no-arg constructor), and loaded-but-wrong-type — now has its own distinct, informative handling instead of one class name being allowed to crash the whole program.

### Level 3 — Advanced

```java
public class PluginLoaderAdvanced {
    public interface Greeter { String greet(); }

    public static class EnglishGreeter implements Greeter {
        public String greet() { return "Hello!"; }
    }

    public static class NotAGreeter {} // valid class, wrong contract

    public static void main(String[] args) {
        String[] namesToTry = {
                "PluginLoaderAdvanced$EnglishGreeter",
                "PluginLoaderAdvanced$NotAGreeter",
                "PluginLoaderAdvanced$DoesNotExist"
        };
        for (String className : namesToTry) {
            Greeter greeter = loadGreeter(className);
            System.out.println(className + " -> " + (greeter != null ? greeter.greet() : "unavailable"));
        }
    }

    static Greeter loadGreeter(String className) {
        try {
            Class<?> clazz = Class.forName(className);
            if (!Greeter.class.isAssignableFrom(clazz)) { // validate BEFORE instantiating/casting
                System.out.println("  (" + className + " does not implement Greeter, skipping)");
                return null;
            }
            Object instance = clazz.getDeclaredConstructor().newInstance();
            return (Greeter) instance; // now provably safe
        } catch (ClassNotFoundException e) {
            System.out.println("  (" + className + " not found on classpath)");
            return null;
        } catch (ReflectiveOperationException e) {
            System.out.println("  (" + className + " could not be instantiated: " + e.getMessage() + ")");
            return null;
        }
    }
}
```

**How to run:** `java PluginLoaderAdvanced.java`

`Greeter.class.isAssignableFrom(clazz)` checks, before ever constructing an instance, whether the loaded class actually implements the expected interface — turning a would-be runtime `ClassCastException` (or worse, a silently wrong plugin) into an early, explicit, and gracefully handled rejection.

## 6. Walkthrough

Execution starts in `main`, which iterates `namesToTry` and calls `loadGreeter` for each name in turn.

**First name — the real `EnglishGreeter`:** `Class.forName` locates and loads the class, returning its `Class` object. `Greeter.class.isAssignableFrom(clazz)` checks whether `Greeter` is a supertype (interface) of `clazz` — since `EnglishGreeter` does implement `Greeter`, this returns `true`. `clazz.getDeclaredConstructor().newInstance()` reflectively finds the no-argument constructor and invokes it, producing a new `EnglishGreeter` instance, which is cast to `Greeter` and returned. Back in `main`, `greeter.greet()` is called normally, printing `Hello!`.

**Second name — `NotAGreeter`:** `Class.forName` again succeeds (the class does exist), but `isAssignableFrom` returns `false`, since `NotAGreeter` implements no such interface. The method prints the skip message and returns `null` *without ever attempting to instantiate or cast the class* — this is the key improvement over Level 1/2, where the mistake would only have been discovered via a runtime `ClassCastException` after already constructing the object.

**Third name — a nonexistent class:** `Class.forName` itself throws `ClassNotFoundException` before anything else happens; the `catch` block prints the not-found message and returns `null`.

Back in `main`, each result is printed: the first prints `Hello!`, the second and third print `unavailable` (since `greeter` was `null` in both cases), following the ternary check `greeter != null ? greeter.greet() : "unavailable"`.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="three class names go through forName, then a contract check via isAssignableFrom, before any instantiation or casting occurs">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">EnglishGreeter: forName OK -&gt; isAssignableFrom TRUE -&gt; newInstance() -&gt; cast OK -&gt; greet() -&gt; "Hello!"</text>
  <text x="20" y="55" fill="#f85149" font-size="10">NotAGreeter: forName OK -&gt; isAssignableFrom FALSE -&gt; skipped, no instantiation attempted</text>
  <text x="20" y="80" fill="#f85149" font-size="10">DoesNotExist: forName throws ClassNotFoundException -&gt; caught, null returned</text>
  <text x="20" y="110" fill="#8b949e" font-size="10">Validating the contract (isAssignableFrom) BEFORE construction avoids ever holding</text>
  <text x="20" y="130" fill="#8b949e" font-size="10">an instance of the wrong type, instead of discovering the mismatch via ClassCastException.</text>
</svg>

## 7. Gotchas & takeaways

> `Class.forName` runs the target class's static initializer block as a side effect of loading it — if that class has expensive or side-effecting static initialization (registering a driver, opening a resource), simply *checking* whether a class name is loadable can trigger real work you didn't intend.

- `Class.forName` requires the exact, fully-qualified (and, for nested classes, binary — using `$`) class name as a `String`; a typo fails only at runtime, not at compile time.
- Always handle `ClassNotFoundException` explicitly wherever a class name comes from configuration, user input, or any source outside the compiler's view.
- Validate a dynamically-loaded class against the interface or supertype you expect (`ExpectedType.class.isAssignableFrom(clazz)`) *before* instantiating and casting — this turns a potential `ClassCastException` into an earlier, clearer rejection.
- `newInstance()` (deprecated) and `getDeclaredConstructor().newInstance()` both require a no-argument constructor to exist on the target class, and both can throw checked reflective exceptions that must be handled.
- Prefer compile-time references (`.class` literals, direct type usage) whenever the type is actually known at compile time — reserve `Class.forName` for genuine cases where the type is only known as data at runtime.
