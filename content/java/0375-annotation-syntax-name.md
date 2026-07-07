---
card: java
gi: 375
slug: annotation-syntax-name
title: Annotation syntax @Name
---

## 1. What it is

An **annotation** is a piece of metadata attached to code — a class, method, field, parameter, or other declaration — written as `@Name` right before the thing it describes. Unlike a comment, an annotation is a real, structured part of the program the compiler and other tools can read and act on. Java 5 introduced the `@` syntax and the built-in annotations `@Override`, `@Deprecated`, and `@SuppressWarnings`, along with the ability for anyone to declare custom annotations of their own.

## 2. Why & when

Before annotations, metadata about code — "this method overrides a superclass method," "this class should be treated specially by a framework," "suppress this warning here" — either lived only in comments (which tools can't read or enforce) or required separate configuration files disconnected from the code they described (an old, painful pattern still seen in some legacy XML-configured frameworks). Annotations solve this by putting machine-readable metadata directly in the source, right next to the code it applies to, where the compiler, IDE, and libraries can all inspect it.

You use annotations constantly, often without thinking of them as a distinct feature: `@Override` on every overriding method, `@Test` on every JUnit test method, `@Entity` on every JPA-mapped class, `@GetMapping` on every Spring REST endpoint. Annotations are how modern Java frameworks configure behaviour without requiring a separate configuration file — the framework reads the annotations (via reflection) and acts accordingly.

## 3. Core concept

```java
public class AnnotationSyntaxDemo {
    static class Animal {
        void speak() {
            System.out.println("...");
        }
    }

    static class Dog extends Animal {
        @Override // annotation: tells the compiler "this MUST override a superclass method"
        void speak() {
            System.out.println("Woof!");
        }
    }

    public static void main(String[] args) {
        Animal a = new Dog();
        a.speak();
    }
}
```

**How to run:** `java AnnotationSyntaxDemo.java`

`@Override`, written directly above `speak()`, is the annotation: it's not a comment and not executable code, but metadata the compiler checks — it verifies that `Dog.speak()` genuinely overrides a method from `Animal` (or an interface), and fails to compile if it doesn't (for example, if the method name were misspelled).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an annotation attaches structured metadata directly above a declaration, read by the compiler or by reflection at runtime, distinct from an ordinary comment">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="53" fill="#79c0ff" font-size="11" text-anchor="middle">@Override</text>

  <text x="220" y="53" fill="#8b949e" font-size="10">attaches to -&gt;</text>

  <rect x="320" y="30" width="280" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="53" fill="#6db33f" font-size="11" text-anchor="middle">void speak() { ... }</text>

  <text x="20" y="100" fill="#e6edf3" font-size="10">Compiler reads @Override and CHECKS it -- a real, enforced fact, not just documentation.</text>
  <text x="20" y="122" fill="#8b949e" font-size="10">A plain comment (// overrides speak) would carry the same intent but nothing verifies it.</text>
</svg>

## 5. Runnable example

Scenario: a small animal hierarchy, evolved from relying on comments alone to document intent, through adding `@Override` to get compiler enforcement, to a version where `@Override` catches a genuine typo bug immediately.

### Level 1 — Basic

```java
public class AnimalCommentOnly {
    static class Animal {
        void speak() { System.out.println("..."); }
    }

    static class Cat extends Animal {
        // overrides speak() -- just a comment, the compiler doesn't check this claim at all
        void speek() { // TYPO: should be speak()
            System.out.println("Meow!");
        }
    }

    public static void main(String[] args) {
        Animal a = new Cat();
        a.speak(); // calls Animal's "..." -- Cat's speek() is a totally different, unrelated method
    }
}
```

**How to run:** `java AnimalCommentOnly.java`

The comment claims this overrides `speak()`, but the actual method name is misspelled as `speek()` — a brand new, unrelated method that never overrides anything. The compiler has no way to check a comment, so this compiles fine and silently does the wrong thing: `a.speak()` calls `Animal`'s original `"..."` behaviour, not `Cat`'s intended `"Meow!"`.

### Level 2 — Intermediate

```java
public class AnimalOverrideCorrect {
    static class Animal {
        void speak() { System.out.println("..."); }
    }

    static class Cat extends Animal {
        @Override // now the compiler actively verifies this claim
        void speak() {
            System.out.println("Meow!");
        }
    }

    public static void main(String[] args) {
        Animal a = new Cat();
        a.speak(); // correctly calls Cat's "Meow!"
    }
}
```

**How to run:** `java AnimalOverrideCorrect.java`

With the typo fixed and `@Override` added, the compiler confirms `speak()` genuinely overrides `Animal.speak()`. `a.speak()` now correctly dispatches to `Cat`'s version, printing `Meow!`.

### Level 3 — Advanced

```java
public class AnimalOverrideCatchesTypo {
    static class Animal {
        void speak() { System.out.println("..."); }
    }

    static class Cat extends Animal {
        @Override
        void speek() { // same typo as Level 1, but NOW annotated
            System.out.println("Meow!");
        }
    }

    public static void main(String[] args) {
        System.out.println("If this compiled, @Override would have caught the typo above.");
    }
}
```

**How to run:** `javac AnimalOverrideCatchesTypo.java` (deliberately fails to compile)

Adding `@Override` above the same misspelled `speek()` from Level 1 turns the silent, hard-to-notice bug into a hard compile error: `method does not override or implement a method from a supertype`. This is the entire value proposition of `@Override` — it converts "the compiler trusts your comment" into "the compiler verifies your claim," catching exactly this class of typo immediately, at compile time, instead of as a confusing runtime behaviour discovered much later.

## 6. Walkthrough

Compare Level 1 and Level 2 side by side to see the effect end-to-end. In Level 1, compilation proceeds normally because `speek()` (misspelled) is treated by the compiler as a perfectly ordinary new method on `Cat` — nothing links it to `Animal.speak()` at all, since Java only ties an override to a superclass method by exact name and signature match, and there is no `@Override` present to make the compiler check that a match was intended.

At runtime, `Animal a = new Cat()` creates a `Cat` object referenced through an `Animal`-typed variable. `a.speak()` performs a polymorphic call: the JVM looks up `speak()` starting from `Cat`'s actual runtime class. `Cat` does not define a `speak()` method (only the unrelated `speek()`), so the lookup falls through to `Animal.speak()`, which prints `...` — silently the wrong behaviour, since the program's intent was clearly for `Cat` to say `Meow!`.

In Level 2, the same class structure but with the typo corrected and `@Override` added: the compiler, upon seeing `@Override`, actively searches `Cat`'s supertypes for a method matching `speak()`'s exact name and parameter list. It finds `Animal.speak()`, confirms the match, and compilation succeeds silently (no error, since the claim is true). At runtime, `a.speak()` now correctly resolves to `Cat.speak()`, printing `Meow!`.

In Level 3, the typo from Level 1 is reintroduced, but now with `@Override` present. The compiler performs the same search as in Level 2 but finds no matching `speak()` method to override — `Cat` only has `speek()`. Since `@Override` asserts "this overrides something," and nothing does, the compiler raises a hard error and refuses to produce a class file at all, catching the exact mistake Level 1 let through silently.

Expected output (Level 1): `...`
Expected output (Level 2): `Meow!`
Expected result (Level 3): compilation fails with an error pointing at `speek()`.

## 7. Gotchas & takeaways

> Always add `@Override` when you intend to override a method — it costs nothing when you're right, and it turns a silent, hard-to-debug typo (like `speek()` instead of `speak()`) into an immediate, precisely-located compile error instead of a confusing runtime mystery.

- An annotation, written `@Name`, attaches structured, machine-readable metadata to a declaration — distinct from a comment, which only humans (not the compiler or tools) can read.
- Java 5 introduced both the `@` annotation syntax and several built-in annotations (`@Override`, `@Deprecated`, `@SuppressWarnings`), covered individually in the topics that follow this one.
- The compiler, IDEs, and libraries can all read annotations via reflection or at compile time and act on them — this is the foundation for how frameworks like Spring and JUnit configure behaviour directly from annotated code.
- `@Override` specifically causes the compiler to verify that the annotated method genuinely overrides (or implements) a method from a supertype or interface — a typo in the method name or parameter list becomes an immediate compile error instead of a silently-wrong new method.
- Anyone can declare custom annotations for their own frameworks or tools (see [[declaring-custom-annotations]]) — the built-in ones are just the most commonly used examples of the same general mechanism.
