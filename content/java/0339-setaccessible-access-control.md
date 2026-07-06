---
card: java
gi: 339
slug: setaccessible-access-control
title: setAccessible() & access control
---

## 1. What it is

`AccessibleObject.setAccessible(boolean)` — inherited by `Field`, `Method`, and `Constructor` — controls whether Java's normal access-control checks (`private`, `protected`, package-private) are enforced when that reflective member is used. Calling `setAccessible(true)` tells the JVM to skip those checks for this specific reflective object going forward, which is what makes it possible to read a `private` field or invoke a `private` method from code that would never be allowed to do so directly.

```java
import java.lang.reflect.Field;

public class SetAccessibleDemo {
    static class Secret { private String value = "hidden"; }

    public static void main(String[] args) throws Exception {
        Field field = Secret.class.getDeclaredField("value");
        try {
            System.out.println(field.get(new Secret())); // fails: still private
        } catch (IllegalAccessException e) {
            System.out.println("Blocked without setAccessible: " + e.getMessage());
        }
        field.setAccessible(true);
        System.out.println("After setAccessible: " + field.get(new Secret()));
    }
}
```

Without `setAccessible(true)`, reflection still respects the *same* access rules as ordinary code — `field.get()` on a `private` field from outside its class throws `IllegalAccessException`, exactly as directly writing `secret.value` from outside `Secret` would fail to compile.

## 2. Why & when

Frameworks that need to read, write, or invoke a class's internals generically — regardless of that class's own access modifiers — rely on `setAccessible(true)` to do so. Serialization libraries, dependency injection containers, and testing tools all use it to reach into objects in ways their own public API doesn't (and by design, shouldn't) expose.

- **Serialization and deserialization frameworks** — reconstructing an object's exact internal state, including private fields, when converting to/from JSON, XML, or a binary format.
- **Testing internal state** — some test frameworks use `setAccessible(true)` to inspect or set up private fields that aren't exposed through the class's public API, when testing implementation details directly is genuinely necessary.
- **Dependency injection** — DI containers commonly inject values directly into `private` fields annotated for injection, which requires bypassing normal access control.

Since Java 9's module system, `setAccessible(true)` can fail with `InaccessibleObjectException` for members belonging to a module that hasn't explicitly `opens` that package for reflection — this is a *stronger* boundary than plain `private`, and no reflective trick bypasses it without the module owner's explicit permission (via `module-info.java` or a JVM flag).

## 3. Core concept

```java
import java.lang.reflect.Field;

public class SetAccessibleCore {
    static class Locked { private final int value = 42; }

    public static void main(String[] args) throws Exception {
        Field field = Locked.class.getDeclaredField("value");
        System.out.println("Accessible before: " + field.canAccess(new Locked()));
        field.setAccessible(true);
        System.out.println("Accessible after: " + field.canAccess(new Locked()));
        System.out.println("Value: " + field.get(new Locked()));
    }
}
```

**How to run:** `java SetAccessibleCore.java`

`field.canAccess(instance)` reports whether the current accessibility setting would permit access to that field on that instance, letting code check access *before* attempting an operation that might throw `IllegalAccessException`.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="setAccessible(true) disables Java's normal private/protected access checks for a specific reflective member going forward">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="250" height="40" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="145" y="55" fill="#f85149" font-size="10" text-anchor="middle">default: normal access rules apply</text>

  <rect x="20" y="85" width="250" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="145" y="110" fill="#6db33f" font-size="10" text-anchor="middle">after setAccessible(true): rules bypassed</text>

  <text x="340" y="55" fill="#8b949e" font-size="9">private field.get() -&gt; IllegalAccessException</text>
  <text x="340" y="110" fill="#8b949e" font-size="9">private field.get() -&gt; succeeds</text>
</svg>

## 5. Runnable example

Scenario: a tiny generic "dump internal state" debugging helper, evolved from one that only works on public fields, into one that reflectively opens up private fields, into a production-style helper that checks accessibility first and reports per-field access failures instead of crashing.

### Level 1 — Basic

```java
import java.lang.reflect.Field;

public class DumpBasic {
    static class Session { public String id = "abc123"; }

    public static void main(String[] args) throws Exception {
        Session session = new Session();
        for (Field field : Session.class.getDeclaredFields()) {
            System.out.println(field.getName() + " = " + field.get(session)); // works, field is public
        }
    }
}
```

**How to run:** `java DumpBasic.java`

This works only because `id` happens to be `public` — the moment a field is marked `private`, `field.get(session)` would throw `IllegalAccessException`, since this code never calls `setAccessible`.

### Level 2 — Intermediate

```java
import java.lang.reflect.Field;

public class DumpIntermediate {
    static class Session { private String id = "abc123"; private long createdAt = 1000L; }

    public static void main(String[] args) throws Exception {
        Session session = new Session();
        for (Field field : Session.class.getDeclaredFields()) {
            field.setAccessible(true); // now required since fields are private
            System.out.println(field.getName() + " = " + field.get(session));
        }
    }
}
```

**How to run:** `java DumpIntermediate.java`

Calling `field.setAccessible(true)` before `get()` lets the dump helper read `private` fields — but if `setAccessible` itself ever failed (e.g., blocked by the module system), this code has no fallback and would crash with an unhandled exception.

### Level 3 — Advanced

```java
import java.lang.reflect.Field;
import java.lang.reflect.InaccessibleObjectException;

public class DumpAdvanced {
    static class Session { private String id = "abc123"; private long createdAt = 1000L; }

    public static void main(String[] args) {
        Session session = new Session();
        for (Field field : Session.class.getDeclaredFields()) {
            System.out.println(field.getName() + " = " + safeRead(field, session));
        }
    }

    static Object safeRead(Field field, Object instance) {
        try {
            if (!field.canAccess(instance)) {
                field.setAccessible(true); // only attempt this if actually needed
            }
            return field.get(instance);
        } catch (InaccessibleObjectException e) {
            return "<blocked by module system: " + e.getMessage() + ">";
        } catch (IllegalAccessException e) {
            return "<inaccessible: " + e.getMessage() + ">";
        }
    }
}
```

**How to run:** `java DumpAdvanced.java`

`field.canAccess(instance)` is checked first so `setAccessible` is only called when genuinely needed, and both realistic failure modes are handled distinctly — a plain access-control failure (`IllegalAccessException`) versus the module system actively refusing to open the package (`InaccessibleObjectException`) — so one blocked field doesn't crash the entire dump.

## 6. Walkthrough

Execution starts in `main`, which creates one `Session` instance and iterates its two declared fields, `id` and `createdAt`, calling `safeRead(field, session)` for each.

For `id`: `field.canAccess(instance)` checks whether the current accessibility setting already permits reading this `private` field on this specific instance — since `setAccessible` hasn't been called yet, this returns `false`. The `if` branch runs, calling `field.setAccessible(true)`, which succeeds (no module boundary is blocking it in this simple single-file program). `field.get(instance)` then reads the value, returning `"abc123"`, which `safeRead` returns to `main` and gets printed as `id = abc123`.

For `createdAt`: the exact same sequence runs — `canAccess` returns `false`, `setAccessible(true)` succeeds, and `field.get(instance)` returns the boxed `Long` value `1000`, printed as `createdAt = 1000`.

In a scenario where either field belonged to a class in a different module that hadn't `opens`-declared itself for reflection, `field.setAccessible(true)` would instead throw `InaccessibleObjectException`, which `safeRead`'s `catch` block would convert into a descriptive fallback string rather than letting the exception propagate and abort the rest of the dump — the other, accessible fields would still be printed normally.

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each field is checked for existing access, made accessible only if needed, then read, with two distinct failure modes handled separately">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">canAccess(instance) == false -&gt; setAccessible(true) -&gt; field.get(instance) -&gt; value returned</text>
  <text x="20" y="55" fill="#8b949e" font-size="10">canAccess(instance) == true  -&gt; setAccessible skipped -&gt; field.get(instance) directly</text>
  <text x="20" y="85" fill="#f85149" font-size="10">setAccessible fails (module boundary) -&gt; InaccessibleObjectException -&gt; caught, fallback text returned</text>
  <text x="20" y="107" fill="#f85149" font-size="10">get() fails (still blocked)          -&gt; IllegalAccessException      -&gt; caught, fallback text returned</text>
</svg>

## 7. Gotchas & takeaways

> `setAccessible(true)` bypasses Java's language-level access control (`private`/`protected`/package-private), but it does *not* bypass a security manager's `checkPermission` (where one is configured) or the Java Platform Module System's `opens` requirement — treat it as "removes one specific barrier," not "removes all barriers."

- `field.canAccess(instance)`/`method.canAccess(instance)` let you check accessibility before attempting an operation, avoiding an exception for the common case where access is already permitted.
- Since Java 9, reflective access to a class in another module can throw `InaccessibleObjectException` even after calling `setAccessible(true)` — the target module must `opens` the package, or the JVM must be started with an `--add-opens` flag.
- `setAccessible(true)` affects only the specific `Field`/`Method`/`Constructor` object it's called on — obtaining the same member again via a fresh reflective lookup resets accessibility to its default state.
- Reserve `setAccessible(true)` for genuine framework, testing, or tooling needs — routinely bypassing encapsulation in application code defeats the purpose of `private` and makes future refactoring more fragile.
- Wrap reflective access in specific exception handling (`IllegalAccessException`, `InaccessibleObjectException`) rather than a broad catch-all, since they represent genuinely different causes with different possible remedies.
