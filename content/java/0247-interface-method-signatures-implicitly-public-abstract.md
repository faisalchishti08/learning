---
card: java
gi: 247
slug: interface-method-signatures-implicitly-public-abstract
title: Interface method signatures (implicitly public abstract)
---

## 1. What it is

Just as interface fields are implicitly `public static final` (the previous topic), classic interface methods with no body are implicitly `public` and `abstract` — writing `void draw();` inside an interface is exactly equivalent to writing `public abstract void draw();`, whether or not those modifiers are spelled out.

```java
interface Drawable {
    void draw();                     // implicitly: public abstract void draw();
    public abstract void resize();    // explicit form — identical meaning, just more verbose
}

class Circle implements Drawable {
    @Override
    public void draw() { System.out.println("Drawing circle"); } // MUST be public
    @Override
    public void resize() { System.out.println("Resizing circle"); }
}
```

`draw()` and `resize()` are declared identically in meaning inside `Drawable`, despite one being terse and the other spelling out `public abstract` explicitly — both compile to the exact same thing, and `Circle`'s overrides must be `public`, since an override can never reduce the visibility inherited from the interface.

## 2. Why & when

Understanding that interface methods are implicitly `public abstract` matters mainly for correctly writing implementing classes and for reading interface declarations without being confused by their apparent terseness.

- **Consistency with the interface's purpose** — since an interface describes a contract meant to be usable by any caller, every one of its methods being `public` makes sense: there would be little point in an interface method too restricted for callers to actually invoke.
- **Avoiding a common beginner mistake** — a very frequent early error is declaring an overriding method in an implementing class with default (package-private) visibility, forgetting that the interface method is implicitly `public` — this fails to compile with a "attempting to assign weaker access privileges" error, which understanding this topic prevents.
- **Reading terse interface code correctly** — much real-world interface code omits the redundant `public abstract` keywords entirely (as `Drawable.draw()` does above), so recognizing that a bodyless method inside an interface is always `public abstract`, even with zero modifiers written, is essential for reading idiomatic Java.

Always write overriding methods in implementing classes as `public`, matching what the interface always implicitly requires — and feel free to omit `public abstract` when declaring interface methods yourself, since virtually all Java style guides consider the explicit keywords redundant noise.

## 3. Core concept

```java
interface Validator {
    boolean isValid(String input); // implicitly public abstract
}

class EmailValidator implements Validator {
    // boolean isValid(String input) { ... } // COMPILE ERROR if uncommented: reduces visibility below public
    @Override
    public boolean isValid(String input) { // must match or exceed the interface's implicit public
        return input != null && input.contains("@");
    }
}
```

The commented-out version omitting `public` would fail to compile with an error along the lines of "isValid() in EmailValidator cannot override isValid() in Validator; attempting to assign weaker access privileges" — because `Validator.isValid` is implicitly `public`, and Java's overriding rules never allow narrowing visibility.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bodyless interface method is implicitly public abstract, the implementing class must declare its override as public, never a narrower visibility">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="120" y="20" width="360" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">boolean isValid(String input); == public abstract</text>

  <line x1="300" y1="55" x2="300" y2="75" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="120" y="80" width="360" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="102" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">public boolean isValid(String input) { ... }</text>

  <text x="300" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The override must be public — anything narrower is a compile error.</text>
</svg>

Interface methods are implicitly `public abstract`; overrides must be declared `public`, never narrower.

## 5. Runnable example

Scenario: a validation framework where interface methods are used unqualified, evolved from a single validator into several validators combined, then hardened to show exactly what happens (and why) if visibility is accidentally narrowed.

### Level 1 — Basic

```java
public class InterfaceMethodBasic {
    interface Validator {
        boolean isValid(String input);
    }

    static class NotEmptyValidator implements Validator {
        @Override
        public boolean isValid(String input) { // public required
            return input != null && !input.isEmpty();
        }
    }

    public static void main(String[] args) {
        Validator v = new NotEmptyValidator();
        System.out.println(v.isValid(""));      // false
        System.out.println(v.isValid("hello")); // true
    }
}
```

**How to run:** `java InterfaceMethodBasic.java`

`NotEmptyValidator.isValid` is declared `public`, matching the implicit visibility `Validator.isValid` requires; calling it through the interface-typed reference `v` works exactly as expected.

### Level 2 — Intermediate

Same validation idea, now composing two validators into a chain — demonstrating interface methods used together across multiple implementing classes, each independently satisfying the same public contract.

```java
import java.util.List;

public class InterfaceMethodIntermediate {
    interface Validator {
        boolean isValid(String input);
    }

    static class NotEmptyValidator implements Validator {
        @Override
        public boolean isValid(String input) { return input != null && !input.isEmpty(); }
    }

    static class MaxLengthValidator implements Validator {
        int maxLength;
        MaxLengthValidator(int maxLength) { this.maxLength = maxLength; }
        @Override
        public boolean isValid(String input) { return input != null && input.length() <= maxLength; }
    }

    static boolean validateAll(String input, List<Validator> validators) {
        for (Validator v : validators) {
            if (!v.isValid(input)) return false; // short-circuits on the first failing validator
        }
        return true;
    }

    public static void main(String[] args) {
        List<Validator> chain = List.of(new NotEmptyValidator(), new MaxLengthValidator(10));

        System.out.println(validateAll("hello", chain));         // true — passes both
        System.out.println(validateAll("", chain));               // false — fails NotEmptyValidator
        System.out.println(validateAll("this is too long", chain)); // false — fails MaxLengthValidator
    }
}
```

**How to run:** `java InterfaceMethodIntermediate.java`

`validateAll` calls `v.isValid(input)` on each element of the `List<Validator>`, regardless of which concrete class it actually is — this works uniformly because every `Validator` implementation's `isValid` is guaranteed `public` by the interface contract, so it is always callable through the interface-typed reference.

### Level 3 — Advanced

Same validation chain, now demonstrating the compile error that results from attempting to narrow visibility (shown as a comment, since it would prevent compilation), plus a validator that itself delegates to a private helper method — showing that only the interface method itself must be `public`, while helper methods used internally are free to have any visibility.

```java
import java.util.List;

public class InterfaceMethodAdvanced {
    interface Validator {
        boolean isValid(String input);
    }

    static class RegexLikeValidator implements Validator {
        @Override
        public boolean isValid(String input) { // the interface method itself: MUST be public
            return input != null && containsOnlyLettersAndDigits(input); // delegates to a private helper
        }

        private boolean containsOnlyLettersAndDigits(String input) { // helper: free to be private
            for (char c : input.toCharArray()) {
                if (!Character.isLetterOrDigit(c)) return false;
            }
            return true;
        }
    }

    // The following would NOT compile if uncommented, demonstrating the visibility rule:
    // static class BrokenValidator implements Validator {
    //     boolean isValid(String input) { return true; } // ERROR: attempting to assign weaker access
    // }

    public static void main(String[] args) {
        List<Validator> chain = List.of(new RegexLikeValidator());

        System.out.println(chain.get(0).isValid("abc123"));  // true
        System.out.println(chain.get(0).isValid("abc-123")); // false — contains a hyphen
    }
}
```

**How to run:** `java InterfaceMethodAdvanced.java`

`isValid` (the actual interface method) is `public`, satisfying the contract, while `containsOnlyLettersAndDigits` (a private helper it delegates to internally) has no such requirement, since it is not declared by any interface — this distinction (the interface method itself must be `public`; anything it calls internally can be as restricted as needed) is a common point of confusion this example clarifies directly.

## 6. Walkthrough

Trace both calls to `isValid` in `InterfaceMethodAdvanced.main`.

**`chain.get(0).isValid("abc123")`.** `chain.get(0)` is a `RegexLikeValidator`, accessed through its `Validator` interface type. Calling `isValid("abc123")` dispatches to `RegexLikeValidator.isValid`, which checks `input != null` (`true`) and then calls the private helper `containsOnlyLettersAndDigits("abc123")`. Inside the helper, the loop examines each character: `'a'`, `'b'`, `'c'`, `'1'`, `'2'`, `'3'` — every one satisfies `Character.isLetterOrDigit`, so the loop completes without returning `false`, and the helper returns `true`. Back in `isValid`, the `&&` of `true && true` is `true`, so `isValid` returns `true`.

**`chain.get(0).isValid("abc-123")`.** Same entry path: `input != null` is `true`, so the helper `containsOnlyLettersAndDigits("abc-123")` runs. The loop reaches the character `'-'`: `Character.isLetterOrDigit('-')` is `false`, so `!false` is `true`, and the helper returns `false` immediately, without examining the remaining characters. Back in `isValid`, `true && false` is `false`, so `isValid` returns `false`.

```
isValid("abc123"):
  input != null -> true
  containsOnlyLettersAndDigits: 'a','b','c','1','2','3' all letter-or-digit -> loop completes -> true
  true && true -> true

isValid("abc-123"):
  input != null -> true
  containsOnlyLettersAndDigits: reaches '-' -> not letter-or-digit -> returns false immediately
  true && false -> false
```

**Final output.**
```
true
false
```

## 7. Gotchas & takeaways

> **Declaring an interface method's override with anything less visible than `public` (package-private, `protected`, or `private`) is a compile error**, precisely because the interface method itself is always implicitly `public`, and Java forbids overrides from narrowing visibility. The error message ("attempting to assign weaker access privileges") is one of the most common early Java compiler errors related to interfaces.

> **Only the interface method itself must be `public`; any private helper methods the implementation calls internally are unaffected by this rule** — as `containsOnlyLettersAndDigits` demonstrated, a class implementing an interface is free to use `private` (or any other visibility) helper methods internally, as long as the actual interface-mandated method is `public`.

- Interface methods with no body are implicitly `public abstract`, whether or not those keywords are written explicitly.
- Implementing classes must declare their overriding methods as `public`, since overrides can never reduce inherited visibility.
- Omitting `public abstract` when declaring interface methods is idiomatic and universally understood — the compiler adds them automatically.
- Private (or any non-public) helper methods used internally by an implementation are unaffected by the interface's visibility requirement, which applies only to the interface method itself.
