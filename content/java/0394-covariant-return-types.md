---
card: java
gi: 394
slug: covariant-return-types
title: Covariant return types
---

## 1. What it is

A **covariant return type**, allowed since Java 5, lets an overriding method declare a return type that is a *subtype* of the return type declared by the method it overrides, rather than requiring an exact match. If `Animal.reproduce()` returns `Animal`, a subclass `Dog` overriding `reproduce()` may declare it as returning `Dog` specifically — still a valid override, since every `Dog` genuinely *is* an `Animal`, so the override's promise ("I'll give you at least an `Animal`") is honoured just as well, or better, by promising a more specific `Dog`.

## 2. Why & when

Before Java 5, an overriding method had to declare the exact same return type as the method it overrode, even when the overriding class logically knew it would always return something more specific. This forced callers who knew they were dealing with the more specific subtype to write an explicit downcast after calling the method (`Dog puppy = (Dog) someDog.reproduce();`), purely because the method's declared return type couldn't express what was actually, always true at runtime.

Covariant returns remove that unnecessary cast. This matters most for the classic "clone-like" or "self-returning" pattern: a method like `copy()` or `withName(String)` that's meant to return "the same kind of thing you called it on." A base class can declare the method returning the base type, and each subclass overriding it can narrow the return type to its own type — callers working directly with the subclass get the more specific type back automatically, with no cast, while callers working through the base type still get a valid, compatible reference.

## 3. Core concept

```java
public class CovariantReturnDemo {
    static class Animal {
        Animal reproduce() { // declares it returns Animal
            return new Animal();
        }
    }

    static class Dog extends Animal {
        @Override
        Dog reproduce() { // covariant: Dog is a subtype of Animal -- still a valid override
            return new Dog();
        }
    }

    public static void main(String[] args) {
        Dog parent = new Dog();
        Dog puppy = parent.reproduce(); // no cast needed! the compiler knows this returns Dog specifically
        System.out.println(puppy.getClass().getSimpleName());
    }
}
```

**How to run:** `java CovariantReturnDemo.java`

`Dog.reproduce()` overrides `Animal.reproduce()` while narrowing its return type from `Animal` to `Dog` — legal precisely because `Dog` is a subtype of `Animal`. Calling `parent.reproduce()` on a variable statically typed as `Dog` returns a `Dog` directly, with no cast required, since the compiler already knows `Dog.reproduce()`'s more specific return type applies here.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an overriding method may narrow its return type to a subtype of the original declared return type, letting callers avoid an explicit downcast when working with the more specific type directly">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="55" fill="#6db33f" font-size="10" text-anchor="middle">Animal reproduce() { return Animal; }</text>

  <text x="320" y="55" fill="#8b949e" font-size="10">overridden by -&gt;</text>

  <rect x="380" y="30" width="230" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="495" y="55" fill="#79c0ff" font-size="10" text-anchor="middle">Dog reproduce() { return Dog; }</text>

  <text x="20" y="110" fill="#e6edf3" font-size="10">Dog is a subtype of Animal, so narrowing the return type here is a VALID override, not an overload.</text>
  <text x="20" y="130" fill="#8b949e" font-size="10">Callers using a Dog-typed reference get a Dog back directly -- no downcast needed.</text>
</svg>

## 5. Runnable example

Scenario: a fluent "builder-style" configuration object supporting method chaining, evolved from a version forcing an awkward cast after every subclass-specific chained call, through covariant returns eliminating that cast, to a version chaining several subclass-specific methods together cleanly.

### Level 1 — Basic

```java
public class ConfigNoCovariance {
    static class BaseConfig {
        String name = "default";
        BaseConfig withName(String name) { // returns the base type
            this.name = name;
            return this;
        }
    }

    static class WebConfig extends BaseConfig {
        int port = 8080;
        WebConfig withPort(int port) { // subclass-specific method, only exists on WebConfig
            this.port = port;
            return this;
        }
    }

    public static void main(String[] args) {
        WebConfig config = new WebConfig();
        BaseConfig afterName = config.withName("api-server"); // returns BaseConfig -- loses the WebConfig type!
        // afterName.withPort(9090); // compile error: BaseConfig has no withPort method
        WebConfig castBack = (WebConfig) afterName; // explicit cast needed to continue chaining WebConfig methods
        castBack.withPort(9090);
        System.out.println(castBack.name + ":" + castBack.port);
    }
}
```

**How to run:** `java ConfigNoCovariance.java`

`withName` returns plain `BaseConfig`, so chaining directly into `withPort` (a `WebConfig`-only method) doesn't compile — the caller is forced to add an explicit cast back to `WebConfig` before continuing, purely because `withName`'s declared return type couldn't express that it was actually still working with a `WebConfig` all along.

### Level 2 — Intermediate

```java
public class ConfigWithCovariance {
    static class BaseConfig {
        String name = "default";
        BaseConfig withName(String name) {
            this.name = name;
            return this;
        }
    }

    static class WebConfig extends BaseConfig {
        int port = 8080;

        @Override
        WebConfig withName(String name) { // covariant override: narrows BaseConfig -> WebConfig
            super.withName(name);
            return this;
        }

        WebConfig withPort(int port) {
            this.port = port;
            return this;
        }
    }

    public static void main(String[] args) {
        WebConfig config = new WebConfig()
                .withName("api-server") // returns WebConfig now, thanks to the covariant override
                .withPort(9090);        // chains directly -- no cast needed
        System.out.println(config.name + ":" + config.port);
    }
}
```

**How to run:** `java ConfigWithCovariance.java`

`WebConfig` overrides `withName` with a covariant return type (`WebConfig` instead of `BaseConfig`), calling `super.withName(name)` to reuse the base logic and then returning `this` (already known to be a `WebConfig` from the calling context). The full chain — `.withName(...).withPort(...)` — now compiles directly, with no intermediate cast needed at all.

### Level 3 — Advanced

```java
public class ConfigThreeLevelChain {
    static class BaseConfig {
        String name = "default";
        BaseConfig withName(String name) { this.name = name; return this; }
    }

    static class WebConfig extends BaseConfig {
        int port = 8080;
        @Override WebConfig withName(String name) { super.withName(name); return this; }
        WebConfig withPort(int port) { this.port = port; return this; }
    }

    static class SecureWebConfig extends WebConfig {
        boolean tlsEnabled = false;
        @Override SecureWebConfig withName(String name) { super.withName(name); return this; } // covariant again
        @Override SecureWebConfig withPort(int port) { super.withPort(port); return this; }    // covariant again
        SecureWebConfig withTls(boolean enabled) { this.tlsEnabled = enabled; return this; }
    }

    public static void main(String[] args) {
        SecureWebConfig config = new SecureWebConfig()
                .withName("secure-api")  // SecureWebConfig, thanks to its own covariant override
                .withPort(9443)          // still SecureWebConfig, chains straight through
                .withTls(true);          // now the subclass-only method, no cast needed anywhere in the chain

        System.out.println(config.name + ":" + config.port + " tls=" + config.tlsEnabled);
    }
}
```

**How to run:** `java ConfigThreeLevelChain.java`

`SecureWebConfig` re-overrides both `withName` and `withPort`, each time narrowing the return type one level further (to `SecureWebConfig`), purely to keep the fluent chain flowing through every level of the hierarchy without ever needing a cast — this three-level chain compiles and runs cleanly precisely because each override's covariant return type accurately reflects that `this` really is always a `SecureWebConfig` in this context.

## 6. Walkthrough

Execution starts in `main`. `new SecureWebConfig()` constructs an instance and immediately calls `.withName("secure-api")` on it.

Because the compile-time (static) type of `new SecureWebConfig()` is `SecureWebConfig`, and `SecureWebConfig` overrides `withName` with a covariant return type of `SecureWebConfig`, this call resolves to `SecureWebConfig.withName`. Inside, `super.withName(name)` calls `WebConfig.withName`, which calls `super.withName(name)` again, reaching `BaseConfig.withName`, which sets `this.name = "secure-api"` and returns `this` (typed as `BaseConfig` at that level, but the actual object is still the `SecureWebConfig` instance). Back in `WebConfig.withName`, `return this` returns the same object, now typed as `WebConfig` at that level. Back in `SecureWebConfig.withName`, `return this` returns it once more, now typed as `SecureWebConfig` — matching its covariant declaration.

The expression `.withPort(9443)` is called on this returned value. Because the compiler knows (from `SecureWebConfig.withName`'s covariant return type) that the result is statically typed as `SecureWebConfig`, it resolves `.withPort` to `SecureWebConfig.withPort` directly — no cast needed. This sets `port` to `9443` and, through the same super-call chain, returns `this` typed as `SecureWebConfig` again.

`.withTls(true)` is called next — this method exists *only* on `SecureWebConfig`, and since the previous step's result is already statically known to be a `SecureWebConfig`, this compiles without any cast. It sets `tlsEnabled = true` and returns `this`.

`config` now holds a fully-configured `SecureWebConfig` with `name = "secure-api"`, `port = 9443`, `tlsEnabled = true`. `System.out.println` prints these three fields.

Expected output:
```
secure-api:9443 tls=true
```

## 7. Gotchas & takeaways

> Covariant return types only apply to overriding — the overriding method's return type must be a genuine subtype of the original method's return type. Narrowing to an unrelated type is not an override at all; it's either a compile error (if the method signature otherwise matches) or an entirely separate overload, silently breaking the intended polymorphic relationship.

- A covariant return type lets an overriding method declare a more specific (subtype) return type than the method it overrides — still a valid, genuine override, not a new overload.
- This eliminates the need for callers to write an explicit downcast when they already know, from context, that they're working with the more specific subtype.
- The classic use case is a fluent, "self-returning" method (`withX(...)`, `copy()`) on a class hierarchy, where each subclass overrides such methods purely to narrow the return type, keeping method chains type-safe without casts.
- `Object.clone()` is a well-known real example: many classes override it with a covariant return type (returning their own specific type) instead of the base `Object` type `clone()` originally declares.
- When building a fluent hierarchy several levels deep, every level that wants chaining to "stay narrow" typically needs to re-override each chainable method with its own covariant return type — as `SecureWebConfig` does for both `withName` and `withPort` in the advanced example.
