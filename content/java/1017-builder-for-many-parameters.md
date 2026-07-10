---
card: java
gi: 1017
slug: builder-for-many-parameters
title: Builder for many parameters
---

## 1. What it is

When a class needs many constructor parameters — especially several optional ones — there are three classic approaches, and Effective Java's famous advice is to reach for the third: **telescoping constructors** (a pile of overloaded constructors covering different parameter subsets), the **JavaBeans pattern** (a no-arg constructor plus setters called one at a time), or the **Builder pattern** (a nested builder class assembling the object before it's ever exposed as complete). Builder wins because it gives readable, order-independent construction *and* keeps the final object immutable and never observable in a half-constructed state — something neither of the other two approaches can offer at the same time.

## 2. Why & when

Telescoping constructors force callers into a rigid parameter order and don't scale past a handful of optional fields (see [Builder](1000-builder.md)'s sibling entry for that specific problem). The JavaBeans pattern solves readability (`user.setName("Ana"); user.setAge(30);`) but introduces a worse problem: the object exists in an **inconsistent, partially-constructed state** between the no-arg constructor and the last setter call — if another thread reads the object mid-construction, or if the caller simply forgets a required setter, there's no way to guarantee validity. It also permanently prevents the class from being immutable, since setters must remain available for the pattern to work at all.

Reach for Builder specifically when a class has enough optional parameters that telescoping constructors become unwieldy, *and* you want the final object to be immutable and never observable before it's fully and validly constructed. This is the deciding factor over JavaBeans: Builder assembles state in a separate, mutable builder object, and only calls the real constructor once, atomically, inside `build()` — the target object itself never exists in a half-finished state.

## 3. Core concept

```
// JavaBeans pattern: readable, but the object is INCONSISTENT between setter calls,
// and can never be made immutable since setters must stay public.
class UserBean {
    private String name;   // no final -- can't be, setters need to reassign it
    private int age;
    void setName(String name) { this.name = name; }
    void setAge(int age) { this.age = age; }
}
UserBean bean = new UserBean(); // at this instant, name is null, age is 0 -- INVALID state exists
bean.setName("Ana");            // still invalid: age is 0
bean.setAge(30);                // only NOW is it in a valid state -- nothing enforces this timing

// Builder pattern: readable, AND the User itself is immutable and never half-built.
class User {
    final String name; final int age; // final -- genuinely immutable
    private User(Builder b) { this.name = b.name; this.age = b.age; }
    static class Builder {
        String name; int age;
        Builder name(String name) { this.name = name; return this; }
        Builder age(int age) { this.age = age; return this; }
        User build() { return new User(this); } // ONE atomic construction step
    }
}
User user = new User.Builder().name("Ana").age(30).build(); // never observable before this line
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JavaBeans construction passing through an invalid intermediate state between setter calls versus Builder construction where the User object only comes into existence fully formed">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">JavaBeans: exposed inconsistent states</text>
  <rect x="20" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="75" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">new UserBean()</text>
  <rect x="150" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="205" y="61" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">name set, age=0 (invalid!)</text>
  <rect x="280" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="335" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fully valid</text>
  <line x1="130" y1="57" x2="150" y2="57" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="260" y1="57" x2="280" y2="57" stroke="#8b949e" marker-end="url(#a)"/>

  <text x="480" y="110" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Builder: no intermediate exposed</text>
  <rect x="400" y="130" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="460" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Builder mutating itself</text>
  <rect x="540" y="130" width="90" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">User (final)</text>
  <line x1="520" y1="147" x2="540" y2="147" stroke="#6db33f" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The JavaBeans object itself passes through an invalid state visible to anyone holding a reference; the Builder's mutable scratch space is separate from the final immutable `User`, which only ever exists fully formed.

## 5. Runnable example

Scenario: constructing a `User` with several fields, evolving from the JavaBeans pattern's exposed inconsistent states into a Builder that guarantees the object is only ever seen fully valid.

### Level 1 — Basic

```java
// File: BuilderManyParamsBasic.java
class UserBean {
    private String name;
    private int age;
    private String email;

    void setName(String name) { this.name = name; }
    void setAge(int age) { this.age = age; }
    void setEmail(String email) { this.email = email; }

    @Override public String toString() {
        return "name=" + name + ", age=" + age + ", email=" + email;
    }
}

public class BuilderManyParamsBasic {
    public static void main(String[] args) {
        UserBean bean = new UserBean();
        // At THIS point, bean already exists with name=null, age=0, email=null --
        // an invalid, half-constructed User is fully accessible to any code holding `bean`.
        System.out.println("mid-construction state: " + bean);

        bean.setName("Ana");
        bean.setAge(30);
        bean.setEmail("ana@example.com");
        System.out.println("final state: " + bean);
    }
}
```

**How to run:** save as `BuilderManyParamsBasic.java`, then `javac BuilderManyParamsBasic.java && java BuilderManyParamsBasic` (JDK 17+).

Expected output:
```
mid-construction state: name=null, age=0, email=null
final state: name=Ana, age=30, email=ana@example.com
```

`bean` is fully accessible in its invalid, half-constructed state right after `new UserBean()` — if this object were shared with another thread, or if any setter call were accidentally skipped, code could observe or act on obviously wrong data with no compiler warning at all.

### Level 2 — Intermediate

```java
// File: BuilderManyParamsIntermediate.java
class User {
    private final String name;
    private final int age;
    private final String email;

    private User(Builder b) {
        this.name = b.name; this.age = b.age; this.email = b.email;
    }

    @Override public String toString() {
        return "name=" + name + ", age=" + age + ", email=" + email;
    }

    static class Builder {
        private String name;
        private int age;
        private String email;

        Builder name(String name) { this.name = name; return this; }
        Builder age(int age) { this.age = age; return this; }
        Builder email(String email) { this.email = email; return this; }
        User build() { return new User(this); } // the ONE point User comes into existence
    }
}

public class BuilderManyParamsIntermediate {
    public static void main(String[] args) {
        User user = new User.Builder()
            .name("Ana")
            .age(30)
            .email("ana@example.com")
            .build();

        System.out.println(user);
    }
}
```

**How to run:** save as `BuilderManyParamsIntermediate.java`, then `javac BuilderManyParamsIntermediate.java && java BuilderManyParamsIntermediate` (JDK 17+).

Expected output:
```
name=Ana, age=30, email=ana@example.com
```

The real-world concern added: no `User` object exists at all until `.build()` runs — there's no reference anyone could hold to a half-constructed `User`. The `Builder` object accumulates state, but it's a completely separate, disposable object from the final immutable `User`.

### Level 3 — Advanced

```java
// File: BuilderManyParamsAdvanced.java
import java.util.Objects;

class User {
    private final String name;
    private final int age;
    private final String email;

    private User(Builder b) {
        this.name = b.name; this.age = b.age; this.email = b.email;
    }

    @Override public String toString() {
        return "name=" + name + ", age=" + age + ", email=" + email;
    }

    static class Builder {
        private String name;
        private int age = -1; // sentinel: "not yet set"
        private String email;

        Builder name(String name) {
            this.name = Objects.requireNonNull(name, "name is required");
            return this;
        }
        Builder age(int age) {
            if (age < 0) throw new IllegalArgumentException("age must be non-negative");
            this.age = age;
            return this;
        }
        Builder email(String email) { this.email = email; return this; }

        User build() {
            // Required-field checks happen HERE, atomically, right before the
            // real User is ever created -- never partway through, never skippable.
            if (name == null) throw new IllegalStateException("name is required");
            if (age < 0) throw new IllegalStateException("age is required");
            return new User(this);
        }
    }
}

public class BuilderManyParamsAdvanced {
    public static void main(String[] args) {
        User complete = new User.Builder().name("Ana").age(30).email("ana@example.com").build();
        System.out.println(complete);

        try {
            new User.Builder().name("Ben").build(); // age never set
        } catch (IllegalStateException e) {
            System.out.println("build failed: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `BuilderManyParamsAdvanced.java`, then `javac BuilderManyParamsAdvanced.java && java BuilderManyParamsAdvanced` (JDK 17+).

Expected output:
```
name=Ana, age=30, email=ana@example.com
build failed: age is required
```

The production-flavored hard case: `build()` validates that every required field was actually set (using a sentinel value, `-1`, to detect "age was never called") before constructing the real `User` — a missing required field is caught in exactly one place, at the exact moment construction would otherwise complete, and no invalid `User` is ever created.

## 6. Walkthrough

Tracing `new User.Builder().name("Ben").build()` in `BuilderManyParamsAdvanced.main`:

1. `new User.Builder()` creates a builder with `name = null`, `age = -1` (the "not set" sentinel), `email = null`.
2. `.name("Ben")` calls `Objects.requireNonNull("Ben", ...)`, which passes since `"Ben"` isn't null, sets `this.name = "Ben"`, and returns the builder itself (`this`) for chaining.
3. `.build()` is called directly next — `age` was never set, so it's still `-1`.
4. Inside `build()`, `if (name == null)` is `false` (name is `"Ben"`), so that check passes. `if (age < 0)` evaluates `-1 < 0`, which is `true` — so `throw new IllegalStateException("age is required")` executes immediately, and `new User(this)` is never reached.
5. That exception propagates out of `build()` to `main`'s `try` block, caught by `catch (IllegalStateException e)`, printing `"build failed: age is required"`.
6. Compare with the successful construction just above it: `new User.Builder().name("Ana").age(30).email("ana@example.com").build()` sets all three fields before `build()` runs, so both required-field checks pass, `new User(this)` executes, and the fully-valid `User` is returned and printed. At no point during either construction attempt did an actual `User` object exist in an invalid state — the failure happened entirely within the disposable `Builder`.

## 7. Gotchas & takeaways

> **Gotcha:** a sentinel value (like `age = -1` meaning "not set") only works cleanly when the valid range excludes that sentinel naturally (ages are never negative). For a field where every possible value is legitimate, a separate `boolean` flag (`ageWasSet`) is the safer way to distinguish "never set" from "set to a value that happens to look like the default."

- Builder solves what neither telescoping constructors nor the JavaBeans pattern can offer together: readable, order-independent construction *and* an immutable final object that's never observable before it's fully and validly constructed.
- The JavaBeans pattern's core weakness isn't verbosity — it's that the object under construction is genuinely inconsistent and externally visible between setter calls, with nothing enforcing that every required setter gets called.
- Builder achieves atomicity by keeping all in-progress state inside a separate, mutable `Builder` object; the real target object is constructed exactly once, inside `build()`, from a fully-populated builder.
- Required-field validation belongs inside `build()`, checked all at once, right before the real object is constructed — this is also where cross-field validation rules belong (see [Builder](1000-builder.md)'s sibling entry for an example spanning multiple fields).
- This pattern is a major reason Builder-constructed objects are easy to reason about under concurrency: since the object is never visible until fully built, there's no partially-constructed state another thread could ever observe.
- Don't reach for a full Builder when a class only has one or two required fields and nothing optional — a plain constructor remains simpler, and the JavaBeans/telescoping/Builder tradeoff only matters once parameter count and optionality genuinely grow.
