---
card: java
gi: 1000
slug: builder
title: Builder
---

## 1. What it is

The **Builder** pattern separates the construction of a complex object from its representation, letting the same step-by-step construction process produce different configurations. In Java it most commonly shows up as a **fluent builder**: a class with chained setter-like methods (`.name("Ana").age(30)`) that each return the builder itself, ending in a `.build()` call that assembles the final, often-immutable object. It replaces constructors that would otherwise need many parameters — most of them optional — where callers struggle to remember the right order or end up passing `null` for things they don't need.

## 2. Why & when

A constructor with many parameters, several of them optional, forces every caller to either provide all of them in a fixed, easy-to-mix-up order, or forces you to write an unwieldy pile of overloaded constructors ("telescoping constructors") to cover every combination of optional fields. Builder exists to make optional configuration readable and order-independent: each `.field(value)` call is self-documenting at the call site, unlike a bare positional argument, and omitted fields simply fall back to sensible defaults.

Reach for Builder when a class has four or more constructor parameters, several of which are optional, or when you want the constructed object to be immutable (all fields `final`, set once by `build()`) while still allowing flexible, readable construction. It's unnecessary for a class with one or two required fields and no optional ones — a plain constructor is simpler and just as clear there.

## 3. Core concept

```
class User {
    private final String name;   // required
    private final int age;       // required
    private final String email;  // optional
    private final boolean isAdmin; // optional, defaults to false

    private User(Builder b) {
        this.name = b.name; this.age = b.age; this.email = b.email; this.isAdmin = b.isAdmin;
    }

    static class Builder {
        private final String name; // required, set via constructor
        private final int age;
        private String email = null;      // optional, has a default
        private boolean isAdmin = false;   // optional, has a default

        Builder(String name, int age) { this.name = name; this.age = age; }
        Builder email(String email) { this.email = email; return this; } // returns `this` -- chainable
        Builder admin(boolean isAdmin) { this.isAdmin = isAdmin; return this; }
        User build() { return new User(this); }
    }
}

User user = new User.Builder("Ana", 30).email("ana@example.com").admin(true).build();
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chain of Builder method calls, each returning the same builder instance, ending in build which produces the final immutable User object">
  <rect x="20" y="60" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">new Builder(...)</text>

  <rect x="170" y="60" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="225" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.email(...)</text>

  <rect x="320" y="60" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.admin(true)</text>

  <rect x="470" y="60" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.build() -&gt; User</text>

  <line x1="130" y1="80" x2="170" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="280" y1="80" x2="320" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="430" y1="80" x2="470" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">each call returns the SAME builder instance</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each chained call mutates and returns the same builder; only the final `.build()` call produces the actual, immutable target object.

## 5. Runnable example

Scenario: constructing a `User` object with several optional fields, evolving from an unwieldy telescoping-constructor design into a fluent, immutable builder.

### Level 1 — Basic

```java
// File: BuilderBasic.java
class User {
    private final String name;
    private final int age;
    private final String email;
    private final boolean isAdmin;

    // Telescoping constructors: one per combination of optional fields.
    User(String name, int age) { this(name, age, null, false); }
    User(String name, int age, String email) { this(name, age, email, false); }
    User(String name, int age, String email, boolean isAdmin) {
        this.name = name; this.age = age; this.email = email; this.isAdmin = isAdmin;
    }

    @Override public String toString() {
        return name + " (" + age + "), email=" + email + ", admin=" + isAdmin;
    }
}

public class BuilderBasic {
    public static void main(String[] args) {
        User basic = new User("Ana", 30);
        User withEmail = new User("Ben", 25, "ben@example.com");
        // What if you need email=null but isAdmin=true? No constructor fits --
        // you'd have to pass null explicitly and remember the exact parameter order.
        User admin = new User("Cara", 40, null, true);

        System.out.println(basic);
        System.out.println(withEmail);
        System.out.println(admin);
    }
}
```

**How to run:** save as `BuilderBasic.java`, then `javac BuilderBasic.java && java BuilderBasic` (JDK 17+).

Expected output:
```
Ana (30), email=null, admin=false
Ben (25), email=ben@example.com, admin=false
Cara (40), email=null, admin=true
```

Passing `null, true` for `admin` is neither self-documenting nor safe from mistakes — swapping the last two positional arguments would compile fine and silently produce wrong data.

### Level 2 — Intermediate

```java
// File: BuilderIntermediate.java
class User {
    private final String name;
    private final int age;
    private final String email;
    private final boolean isAdmin;

    private User(Builder b) {
        this.name = b.name; this.age = b.age; this.email = b.email; this.isAdmin = b.isAdmin;
    }

    @Override public String toString() {
        return name + " (" + age + "), email=" + email + ", admin=" + isAdmin;
    }

    static class Builder {
        private final String name;
        private final int age;
        private String email = null;
        private boolean isAdmin = false;

        Builder(String name, int age) { this.name = name; this.age = age; }
        Builder email(String email) { this.email = email; return this; }
        Builder admin(boolean isAdmin) { this.isAdmin = isAdmin; return this; }
        User build() { return new User(this); }
    }
}

public class BuilderIntermediate {
    public static void main(String[] args) {
        User admin = new User.Builder("Cara", 40).admin(true).build();
        System.out.println(admin);
    }
}
```

**How to run:** save as `BuilderIntermediate.java`, then `javac BuilderIntermediate.java && java BuilderIntermediate` (JDK 17+).

Expected output:
```
Cara (40), email=null, admin=true
```

The real-world concern added: `.admin(true)` self-documents what it sets, `email` is simply omitted (defaulting to `null`) instead of passed explicitly, and no telescoping constructor overload is needed for this new combination of fields.

### Level 3 — Advanced

```java
// File: BuilderAdvanced.java
import java.util.Objects;

class User {
    private final String name;
    private final int age;
    private final String email;
    private final boolean isAdmin;

    private User(Builder b) {
        this.name = b.name; this.age = b.age; this.email = b.email; this.isAdmin = b.isAdmin;
    }

    @Override public String toString() {
        return name + " (" + age + "), email=" + email + ", admin=" + isAdmin;
    }

    static class Builder {
        private final String name;
        private final int age;
        private String email = null;
        private boolean isAdmin = false;

        Builder(String name, int age) {
            // Validate required fields at the point they're set, not silently later.
            this.name = Objects.requireNonNull(name, "name is required");
            if (age < 0) throw new IllegalArgumentException("age must be non-negative");
            this.age = age;
        }

        Builder email(String email) {
            if (email != null && !email.contains("@")) {
                throw new IllegalArgumentException("invalid email: " + email);
            }
            this.email = email;
            return this;
        }

        Builder admin(boolean isAdmin) { this.isAdmin = isAdmin; return this; }

        User build() {
            // Cross-field validation: rules spanning MULTIPLE fields, only checkable
            // once every field is set -- this is exactly why validation belongs in
            // build(), not scattered across each individual setter.
            if (isAdmin && email == null) {
                throw new IllegalStateException("admin users must have an email");
            }
            return new User(this);
        }
    }
}

public class BuilderAdvanced {
    public static void main(String[] args) {
        User valid = new User.Builder("Cara", 40).email("cara@example.com").admin(true).build();
        System.out.println(valid);

        try {
            new User.Builder("Dev", 22).admin(true).build(); // admin with no email
        } catch (IllegalStateException e) {
            System.out.println("build failed: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `BuilderAdvanced.java`, then `javac BuilderAdvanced.java && java BuilderAdvanced` (JDK 17+).

Expected output:
```
Cara (40), email=cara@example.com, admin=true
build failed: admin users must have an email
```

The production-flavored hard case: validating a rule that spans multiple fields (admins must have an email) can only correctly happen in `build()`, once every field the caller intends to set has actually been set — checking it inside `admin(true)` alone would be too early, since `email` might be set afterward in the chain.

## 6. Walkthrough

Tracing `new User.Builder("Dev", 22).admin(true).build()` in `BuilderAdvanced.main`:

1. `new User.Builder("Dev", 22)` runs the builder's constructor: `Objects.requireNonNull(name, ...)` passes since `"Dev"` isn't null, and `age < 0` is false since `22 >= 0`, so `name` and `age` are set on the builder. `email` stays at its default, `null`.
2. `.admin(true)` sets `isAdmin = true` on the same builder instance and returns `this` — no validation happens here yet, since this method has no way of knowing whether `.email(...)` will be called next in the chain.
3. `.build()` is called. First, the cross-field check runs: `isAdmin && email == null` evaluates to `true && true`, which is `true` — so a `new IllegalStateException("admin users must have an email")` is thrown immediately, and `new User(this)` never executes.
4. That exception propagates up out of `build()` to `main`'s `try` block, where the `catch (IllegalStateException e)` clause catches it and prints `"build failed: admin users must have an email"`.
5. Compare with the first construction, `new User.Builder("Cara", 40).email("cara@example.com").admin(true).build()`: here `.email(...)` is called before `.admin(true)`, so by the time `.build()` runs, `email` is `"cara@example.com"` — the cross-field check `isAdmin && email == null` evaluates `true && false`, which is `false`, so validation passes and `new User(this)` constructs the final object, printed as `"Cara (40), email=cara@example.com, admin=true"`.
6. Note the chain's method call *order* didn't matter for correctness in the successful case — `.email(...)` and `.admin(...)` could have appeared in either order — because validation is deferred to `build()`, after every field the caller wanted to set has already been set.

## 7. Gotchas & takeaways

> **Gotcha:** validation that depends on more than one field (like "admins must have an email") must live in `build()`, not in an individual setter method — a setter can't know what other setters will be called later in the same chain, so checking too early produces false failures or misses real ones.

- Builder replaces constructors with many (especially optional) parameters with a fluent, self-documenting chain of setter-like calls ending in `.build()`.
- Each builder method mutates and returns the same builder instance (`return this`), which is what makes the fluent chaining syntax work.
- Required fields are best enforced in the builder's own constructor; optional fields get sensible defaults; cross-field validation belongs in `build()`, where every field is guaranteed to already be set.
- The final built object is typically immutable (all `final` fields, no setters) — the builder is the only place mutation happens, and only during construction.
- Don't reach for Builder for a class with one or two required fields and nothing optional — a plain constructor is simpler and equally clear.
- Builder is often used together with [Factory Method](0998-factory-method.md) or [Abstract Factory](0999-abstract-factory.md) when the *type* of object being built also needs to vary, not just its field values.
