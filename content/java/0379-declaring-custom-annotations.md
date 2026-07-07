---
card: java
gi: 379
slug: declaring-custom-annotations
title: Declaring custom annotations
---

## 1. What it is

You can declare your own annotation type using `@interface` instead of `class` or `interface` — `public @interface Reminder { }`. Once declared, it can be applied to code exactly like a built-in annotation (`@Reminder`). By itself, a bare custom annotation is inert: it attaches metadata, but nothing happens automatically unless something — the compiler, a framework, or your own code using reflection — is written to look for it and act on it.

## 2. Why & when

Built-in annotations like `@Override` cover general-purpose language concerns, but real applications constantly need their own metadata: "this method must run inside a transaction," "this field maps to this database column," "this endpoint requires authentication." Frameworks like Spring and JPA are built almost entirely around custom annotations — `@Entity`, `@GetMapping`, `@Autowired` are all `@interface` declarations, just like the one you'd write yourself, defined by those frameworks and then interpreted by their own reflection-based scanning code at startup or request time.

You declare a custom annotation whenever you want to attach structured, machine-readable metadata to your own code that some other piece of code — a test runner, a build tool, a dependency-injection framework, or a simple in-house reflection-based checker — will read and act on. The annotation declaration itself is just the "shape" of the metadata; the behaviour lives entirely in whatever reads it.

## 3. Core concept

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class CustomAnnotationDemo {
    @Retention(RetentionPolicy.RUNTIME) // must be RUNTIME to be visible via reflection (see meta-annotation-retention topic)
    @interface Reminder {
    }

    static class Report {
        @Reminder
        void generateSummary() { System.out.println("Generating summary..."); }

        void generateChart() { System.out.println("Generating chart..."); } // no @Reminder here
    }

    public static void main(String[] args) throws Exception {
        for (Method m : Report.class.getDeclaredMethods()) {
            if (m.isAnnotationPresent(Reminder.class)) { // reflection reads the custom annotation
                System.out.println("Still needs work: " + m.getName());
            }
        }
    }
}
```

**How to run:** `java CustomAnnotationDemo.java`

`@interface Reminder { }` declares a brand-new, empty annotation type. `@Reminder` is applied to `generateSummary()` but not `generateChart()`. The reflection loop over `Report.class.getDeclaredMethods()` checks `m.isAnnotationPresent(Reminder.class)` for each method — only `generateSummary` has it, so only its name is printed.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a custom annotation declared with at-interface attaches metadata that only reflection code explicitly checking for it will ever act on">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">@interface Reminder {}   -- declares a new annotation TYPE, shaped like a bare marker</text>

  <rect x="30" y="50" width="260" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="72" fill="#f85149" font-size="10" text-anchor="middle">@Reminder  generateSummary()</text>

  <rect x="330" y="50" width="260" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="72" fill="#8b949e" font-size="10" text-anchor="middle">generateChart() -- unmarked</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">Nothing happens automatically -- reflection code (isAnnotationPresent) must explicitly look for @Reminder.</text>
</svg>

## 5. Runnable example

Scenario: a lightweight in-house test runner, evolved from ordinary method calls with no metadata at all, through declaring a custom `@SmokeTest` annotation to mark which methods should run, to a version that uses reflection to discover and execute every annotated method automatically.

### Level 1 — Basic

```java
public class TestRunnerManual {
    static class Checks {
        void checkDatabaseConnection() { System.out.println("DB connection OK"); }
        void checkDiskSpace() { System.out.println("Disk space OK"); }
        void helperNotATest() { System.out.println("(should not run as a test)"); }
    }

    public static void main(String[] args) {
        Checks checks = new Checks();
        checks.checkDatabaseConnection(); // manually listed -- easy to forget one, or call the wrong one
        checks.checkDiskSpace();
    }
}
```

**How to run:** `java TestRunnerManual.java`

Every "test" method has to be manually called by name in `main` — nothing marks which methods are meant to be tests versus ordinary helpers, and it's easy to forget to add a call when a new check method is written later.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class TestRunnerAnnotated {
    @Retention(RetentionPolicy.RUNTIME)
    @interface SmokeTest { // custom annotation marking which methods are smoke tests
    }

    static class Checks {
        @SmokeTest
        void checkDatabaseConnection() { System.out.println("DB connection OK"); }

        @SmokeTest
        void checkDiskSpace() { System.out.println("Disk space OK"); }

        void helperNotATest() { System.out.println("(should not run as a test)"); }
    }

    public static void main(String[] args) {
        System.out.println("Declared; discovery happens in the next level.");
    }
}
```

**How to run:** `java TestRunnerAnnotated.java`

`@SmokeTest` now marks exactly the two real test methods, distinguishing them from `helperNotATest` — but by itself, this annotation still does nothing at runtime; it's just metadata waiting for something to read it, which the next level adds.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class TestRunnerReflective {
    @Retention(RetentionPolicy.RUNTIME)
    @interface SmokeTest {
    }

    static class Checks {
        @SmokeTest
        void checkDatabaseConnection() { System.out.println("DB connection OK"); }

        @SmokeTest
        void checkDiskSpace() {
            throw new RuntimeException("Disk almost full!"); // simulates a failing check
        }

        void helperNotATest() { System.out.println("(should not run as a test)"); }
    }

    public static void main(String[] args) throws Exception {
        Checks checks = new Checks();
        int passed = 0, failed = 0;

        for (Method m : Checks.class.getDeclaredMethods()) {
            if (!m.isAnnotationPresent(SmokeTest.class)) continue; // skip non-test methods entirely

            try {
                m.invoke(checks); // dynamically calls the annotated method by reflection
                passed++;
            } catch (Exception e) {
                System.out.println("FAILED " + m.getName() + ": " + e.getCause().getMessage());
                failed++;
            }
        }
        System.out.println("Passed: " + passed + ", Failed: " + failed);
    }
}
```

**How to run:** `java TestRunnerReflective.java`

This is a minimal but genuine test runner: it discovers every `@SmokeTest`-annotated method via reflection (`getDeclaredMethods()` + `isAnnotationPresent`) and invokes each one dynamically with `m.invoke(checks)` — no method needs to be called by name in `main` at all, and `helperNotATest` is automatically skipped since it lacks the annotation. Adding a new `@SmokeTest` method to `Checks` later would be picked up automatically, with zero changes needed to `main`.

## 6. Walkthrough

Execution starts in `main`. `Checks.class.getDeclaredMethods()` returns an array containing all three declared methods: `checkDatabaseConnection`, `checkDiskSpace`, and `helperNotATest` (order is not guaranteed by the JVM, but assume this order for tracing).

For `checkDatabaseConnection`: `m.isAnnotationPresent(SmokeTest.class)` returns `true`, so the loop proceeds. `m.invoke(checks)` dynamically calls this method on the `checks` instance — inside, it prints `DB connection OK` and returns normally. No exception is thrown, so `passed` becomes `1`.

For `checkDiskSpace`: `isAnnotationPresent` is again `true`. `m.invoke(checks)` calls it; inside, `throw new RuntimeException("Disk almost full!")` executes. Reflection wraps any exception thrown by the invoked method inside an `InvocationTargetException`, which `m.invoke` itself throws — this is caught by the `catch (Exception e)` block. `e.getCause()` retrieves the original `RuntimeException`, and `.getMessage()` gives `"Disk almost full!"`. This prints `FAILED checkDiskSpace: Disk almost full!`, and `failed` becomes `1`.

For `helperNotATest`: `isAnnotationPresent(SmokeTest.class)` returns `false` (it was never annotated), so `continue` skips it entirely — it is never invoked, and never appears in the pass/fail counts.

After the loop, `main` prints `Passed: 1, Failed: 1`.

Expected output:
```
DB connection OK
FAILED checkDiskSpace: Disk almost full!
Passed: 1, Failed: 1
```

## 7. Gotchas & takeaways

> A custom annotation declared without `@Retention(RetentionPolicy.RUNTIME)` is invisible to reflection at runtime by default — the `isAnnotationPresent`/`getAnnotation` calls used here would simply never find it. This is covered in depth in [[meta-annotation-retention-source-class-runtime]], but it's the single most common mistake when first writing your own annotations.

- Declare a custom annotation with `@interface Name { }` — by itself, an annotation is purely descriptive metadata; it does nothing until something reads it.
- Frameworks like Spring (`@GetMapping`, `@Autowired`) and JPA (`@Entity`, `@Column`) are built almost entirely from custom annotations exactly like the ones you can declare yourself, interpreted by the framework's own reflection-based scanning logic.
- `Class.getDeclaredMethods()` combined with `Method.isAnnotationPresent(YourAnnotation.class)` is the standard pattern for discovering which methods carry a given annotation at runtime.
- `Method.invoke(instance)` dynamically calls a method found via reflection — exceptions it throws are wrapped in `InvocationTargetException`, and the real exception is retrieved via `.getCause()`.
- Writing your own tiny reflection-driven tool (like this smoke-test runner) is a genuinely useful way to understand what frameworks like JUnit and Spring are doing conceptually under the hood.
