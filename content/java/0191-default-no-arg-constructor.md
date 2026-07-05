---
card: java
gi: 191
slug: default-no-arg-constructor
title: Default (no-arg) constructor
---

## 1. What it is

If a class defines **no constructors at all**, the Java compiler automatically generates an invisible **default constructor** — one that takes no arguments and does nothing beyond calling the superclass's no-arg constructor implicitly. This is what allows `new SomeClass()` to work even for a class where you never wrote any constructor yourself. The moment you write **any** constructor of your own, however, this automatic default constructor is no longer generated.

```java
class Empty {
    // no constructor written at all
    int value;
}

Empty e = new Empty(); // works — the compiler silently generated a no-arg constructor for us
```

```java
class WithConstructor {
    int value;
    WithConstructor(int value) { this.value = value; } // one constructor, written explicitly
}

// WithConstructor w = new WithConstructor(); // COMPILE ERROR — no matching constructor exists anymore!
WithConstructor w = new WithConstructor(5); // must supply the required argument
```

Adding `WithConstructor(int value)` removes the compiler's automatically-generated no-arg constructor entirely — if a no-arg constructor is still needed alongside the parameterized one, it must now be written explicitly.

## 2. Why & when

The default constructor exists purely as a convenience, so that simple classes with no special initialization needs don't require boilerplate:

- **Classes with no required initial state** — a simple data holder where every field's default value (`0`, `false`, `null`) is a perfectly reasonable starting point needs no custom setup logic at all.
- **It disappears the moment you add any constructor**, which is a deliberate design choice: once you've decided your class *does* have specific initialization requirements (as expressed by your custom constructor), the compiler assumes you no longer want objects created without going through that logic — an implicit no-arg fallback would undermine any validation your custom constructor performs.
- **This is a very common source of confusion** for anyone extending a previously-simple class by adding its first constructor — existing code calling `new SomeClass()` elsewhere suddenly fails to compile, because the automatic default constructor silently vanished.

You rely on the default constructor when a class genuinely needs no custom initialization; the moment any field requires validation, a required initial value, or any other setup logic, you write an explicit constructor instead — and if a no-arg option should still exist too, you write that explicitly as well (constructor overloading, the next topic).

## 3. Core concept

```java
class Counter {
    int count; // no constructor written — compiler provides an implicit no-arg one
}

class ValidatedCounter {
    int count;
    ValidatedCounter(int startAt) { // one constructor written — no more implicit no-arg constructor
        if (startAt < 0) {
            throw new IllegalArgumentException("Cannot start below zero: " + startAt);
        }
        this.count = startAt;
    }
}

public class DefaultCtorDemo {
    public static void main(String[] args) {
        Counter c = new Counter(); // fine — compiler-generated default constructor
        System.out.println(c.count); // 0 — field default, since nothing set it explicitly

        ValidatedCounter vc = new ValidatedCounter(10); // must supply an argument now
        System.out.println(vc.count); // 10
        // new ValidatedCounter(); // would NOT compile — no matching no-arg constructor exists
    }
}
```

`Counter`'s implicit default constructor does nothing beyond the bare minimum — fields still default to `0`/`false`/`null` exactly as they always do, since the generated constructor contains no assignment logic of its own, only an implicit call to `Object`'s constructor.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A class with zero written constructors automatically gets an invisible no argument constructor from the compiler, but the moment one explicit constructor is added, that automatic one disappears entirely">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class with NO constructors written</text>
  <text x="150" y="66" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">compiler adds an invisible no-arg one</text>

  <rect x="330" y="30" width="240" height="45" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="450" y="50" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">class with ONE constructor written</text>
  <text x="450" y="66" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">no more automatic no-arg constructor</text>

  <text x="300" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Writing any constructor yourself removes the compiler's free default one.</text>
  <text x="300" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">If a no-arg version is still needed, it must be written explicitly.</text>
</svg>

The default constructor is a convenience that vanishes the instant a class defines its own.

## 5. Runnable example

Scenario: a simple `Settings` configuration object — starting with a basic class relying entirely on the implicit default constructor, then extending it with an explicit constructor (which removes the default), then hardening into a class that explicitly provides both a no-arg constructor (for sensible defaults) and a parameterized one, side by side.

### Level 1 — Basic

```java
public class SettingsBasic {
    static class Settings {
        boolean darkMode;
        int fontSize;
        // no constructor written — relies entirely on the compiler-generated default
    }

    public static void main(String[] args) {
        Settings s = new Settings(); // works via the implicit default constructor
        System.out.println("Dark mode: " + s.darkMode + ", font size: " + s.fontSize);
    }
}
```

**How to run:** `java SettingsBasic.java`

`new Settings()` succeeds purely because `Settings` declares no constructors of its own — the compiler silently supplied one, and both fields sit at their type defaults (`false`, `0`), since nothing else assigned them.

### Level 2 — Intermediate

Same idea, now adding an explicit constructor that requires a font size — demonstrating that this immediately removes the ability to call `new Settings()` with no arguments.

```java
public class SettingsIntermediate {
    static class Settings {
        boolean darkMode;
        int fontSize;

        Settings(int fontSize) { // adding this constructor removes the implicit default entirely
            if (fontSize < 8) {
                throw new IllegalArgumentException("Font size too small: " + fontSize);
            }
            this.fontSize = fontSize;
        }
    }

    public static void main(String[] args) {
        Settings s = new Settings(14); // must supply a font size now
        System.out.println("Font size: " + s.fontSize);
        // new Settings(); // this line would NOT compile if uncommented
    }
}
```

**How to run:** `java SettingsIntermediate.java`

Once `Settings(int fontSize)` is written, `new Settings()` (no arguments) is no longer valid Java — the class now requires a font size to be supplied, enforced at compile time, exactly the trade-off this topic covers.

### Level 3 — Advanced

Same `Settings`, now with **both** a sensible no-arg constructor (providing defaults) and a parameterized one written explicitly side by side, giving callers a choice while still guaranteeing validation runs either way.

```java
public class SettingsAdvanced {
    static class Settings {
        boolean darkMode;
        int fontSize;

        Settings() { // explicit no-arg constructor, providing sensible defaults
            this.darkMode = false;
            this.fontSize = 12;
        }

        Settings(int fontSize) { // explicit parameterized constructor, with validation
            if (fontSize < 8) {
                throw new IllegalArgumentException("Font size too small: " + fontSize);
            }
            this.darkMode = false;
            this.fontSize = fontSize;
        }
    }

    public static void main(String[] args) {
        Settings defaults = new Settings();        // uses the explicit no-arg constructor
        Settings custom = new Settings(20);         // uses the explicit parameterized constructor

        System.out.println("Defaults: dark=" + defaults.darkMode + ", font=" + defaults.fontSize);
        System.out.println("Custom: dark=" + custom.darkMode + ", font=" + custom.fontSize);
    }
}
```

**How to run:** `java SettingsAdvanced.java`

Both constructors are written explicitly here — `Settings()` is no longer the *compiler's automatic* default, but a hand-written one providing specific default values (`false`, `12`), coexisting alongside `Settings(int fontSize)` (this coexistence, several constructors with different signatures, is exactly what the next topic, constructor overloading, covers in full).

## 6. Walkthrough

Trace `SettingsAdvanced.main`:

**`new Settings()`.** The no-arg constructor runs: `this.darkMode = false`, `this.fontSize = 12`. Returns a reference, stored in `defaults`.

**`new Settings(20)`.** The parameterized constructor runs: `fontSize < 8` is `20 < 8`, false, so no exception. `this.darkMode = false`, `this.fontSize = 20`. Returns a reference, stored in `custom`.

```
new Settings()      -> darkMode=false, fontSize=12  (explicit no-arg constructor)
new Settings(20)    -> darkMode=false, fontSize=20  (explicit parameterized constructor)
```

**Print.** `"Defaults: dark=false, font=12"` followed by `"Custom: dark=false, font=20"` — both objects fully and correctly initialized by whichever constructor was actually called, since both were written to explicitly set every field.

## 7. Gotchas & takeaways

> **The moment a class defines any constructor, the compiler's automatic no-arg default constructor disappears entirely — even if the constructor you wrote takes different arguments.** This frequently breaks existing calls to `new SomeClass()` scattered elsewhere in a codebase the moment someone adds the class's first parameterized constructor, and the fix (adding an explicit no-arg constructor back) must be done deliberately.

> **The compiler-generated default constructor does nothing beyond an implicit call to the superclass's constructor** — it never assigns any custom initial values. Fields still simply default to `0`/`false`/`null` unless a real constructor (default or otherwise) explicitly sets them.

- A class with zero constructors written gets a free, compiler-generated no-arg constructor automatically.
- Writing even one explicit constructor removes that automatic default constructor completely.
- If a no-arg option is still needed alongside a parameterized constructor, it must be written explicitly, side by side.
- Relying on the implicit default constructor only makes sense for genuinely simple classes with no required setup or validation.
