---
card: java
gi: 553
slug: repeating-annotations-repeatable
title: Repeating annotations (@Repeatable)
---

## 1. What it is

Before Java 8, applying the same annotation type more than once to the same declaration wasn't allowed at all — you'd need to invent a wrapper annotation manually (like `@Schedules({@Schedule(...), @Schedule(...)})`) and always write that wrapper explicitly. `@Repeatable` changes this: marking an annotation type with `@Repeatable(ContainerAnnotation.class)` lets you write the annotation multiple times directly on the same target, with the compiler automatically collecting all the repeated instances into the specified container annotation behind the scenes.

## 2. Why & when

Some things genuinely need multiple instances of the same kind of metadata on one target — multiple validation rules on a field, multiple scheduled triggers on a method, multiple author credits on a class. `@Repeatable` lets you express this naturally, writing `@Author("Alice") @Author("Bob")` directly, rather than the older `@Authors({@Author("Alice"), @Author("Bob")})` wrapper syntax — cleaner to write, and just as inspectable via reflection, since the container annotation is still generated and accessible underneath.

## 3. Core concept

```java
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)
@Repeatable(Schedules.class) // marks Schedule as repeatable, with Schedules as its container
@interface Schedule {
    String cron();
}

@Retention(RetentionPolicy.RUNTIME)
@interface Schedules {
    Schedule[] value(); // the container MUST have a value() method returning an array of the repeated type
}

class Job {
    @Schedule(cron = "0 0 * * *")
    @Schedule(cron = "0 12 * * *") // written directly, twice -- no manual wrapper syntax needed
    void run() {}
}
```

The `@Repeatable` annotation on `Schedule` tells the compiler that `Schedules` is its container — writing `@Schedule` twice is automatically equivalent to writing one `@Schedules({...})` with both instances inside.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="the compiler automatically collects repeated annotations into their designated container annotation">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="180" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Schedule("0 0 * * *")</text>
  <rect x="30" y="55" width="180" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="75" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Schedule("0 12 * * *")</text>
  <text x="280" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">compiler auto-collects</text>
  <line x1="215" y1="50" x2="380" y2="50" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowRA)"/>
  <rect x="390" y="35" width="220" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="500" y="55" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Schedules({Schedule,Schedule})</text>
  <defs><marker id="arrowRA" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Writing `@Schedule` twice compiles to the equivalent of a single `@Schedules` container holding both instances — entirely automatic.

## 5. Runnable example

Scenario: building a simple cron-scheduling framework that reads multiple schedule annotations off a method — evolved from defining and using a basic repeatable annotation, through reading the repeated annotations back via reflection, to a version handling both single and multiple repetitions correctly (a common edge case in the underlying reflection API).

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class RepeatableBasic {
    @Retention(RetentionPolicy.RUNTIME)
    @Repeatable(Schedules.class)
    @interface Schedule {
        String cron();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @interface Schedules {
        Schedule[] value();
    }

    static class Job {
        @Schedule(cron = "0 0 * * *")
        @Schedule(cron = "0 12 * * *")
        void run() {
            System.out.println("Job running");
        }
    }

    public static void main(String[] args) throws NoSuchMethodException {
        var method = Job.class.getDeclaredMethod("run");
        Schedule[] schedules = method.getAnnotationsByType(Schedule.class);

        System.out.println("Number of schedules: " + schedules.length);
        for (Schedule s : schedules) {
            System.out.println("Cron: " + s.cron());
        }
    }
}
```

**How to run:** `java RepeatableBasic.java`

Expected output:
```
Number of schedules: 2
Cron: 0 0 * * *
Cron: 0 12 * * *
```

`@Schedule` is applied twice directly on `run()`, made possible because `Schedule` is marked `@Repeatable(Schedules.class)`. `method.getAnnotationsByType(Schedule.class)` — the reflection API specifically designed for repeatable annotations — retrieves both instances as an array, regardless of whether they were originally written as two separate `@Schedule` annotations or as one explicit `@Schedules({...})` wrapper.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;
import java.lang.reflect.*;

public class RepeatableGetAnnotation {
    @Retention(RetentionPolicy.RUNTIME)
    @Repeatable(Schedules.class)
    @interface Schedule {
        String cron();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @interface Schedules {
        Schedule[] value();
    }

    static class Job {
        @Schedule(cron = "0 0 * * *")
        @Schedule(cron = "0 12 * * *")
        void run() {}
    }

    public static void main(String[] args) throws NoSuchMethodException {
        Method method = Job.class.getDeclaredMethod("run");

        // getAnnotation(Schedule.class) -- the OLD, single-annotation lookup -- does NOT work here.
        Schedule single = method.getAnnotation(Schedule.class);
        System.out.println("getAnnotation(Schedule.class) result: " + single);

        // getAnnotation(Schedules.class) -- retrieves the AUTO-GENERATED container directly.
        Schedules container = method.getAnnotation(Schedules.class);
        System.out.println("Container found: " + (container != null));
        System.out.println("Container holds " + container.value().length + " schedules");
    }
}
```

**How to run:** `java RepeatableGetAnnotation.java`

Expected output:
```
getAnnotation(Schedule.class) result: null
Container found: true
Container holds 2 schedules
```

The real-world concern this adds: `method.getAnnotation(Schedule.class)` — the traditional, single-annotation lookup method — returns `null` here, since there are *two* `@Schedule` instances present, not exactly one, and `getAnnotation` only ever returns a single annotation instance or `null`. The compiler-generated `Schedules` container, however, **is** directly retrievable via `getAnnotation(Schedules.class)`, since exactly one `Schedules` container annotation genuinely exists (auto-synthesized by the compiler from the two `@Schedule` instances) — `.value()` on it returns the array of both original `Schedule` instances.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.*;

public class RepeatableSingleVsMultiple {
    @Retention(RetentionPolicy.RUNTIME)
    @Repeatable(Schedules.class)
    @interface Schedule {
        String cron();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @interface Schedules {
        Schedule[] value();
    }

    static class SingleScheduleJob {
        @Schedule(cron = "0 0 * * *") // only ONE -- not actually "repeated"
        void run() {}
    }

    static class MultiScheduleJob {
        @Schedule(cron = "0 0 * * *")
        @Schedule(cron = "0 12 * * *")
        void run() {}
    }

    public static void main(String[] args) throws NoSuchMethodException {
        Method singleMethod = SingleScheduleJob.class.getDeclaredMethod("run");
        Method multiMethod = MultiScheduleJob.class.getDeclaredMethod("run");

        // getAnnotationsByType works correctly for BOTH the single AND the multiple case.
        Schedule[] singleResult = singleMethod.getAnnotationsByType(Schedule.class);
        Schedule[] multiResult = multiMethod.getAnnotationsByType(Schedule.class);

        System.out.println("Single-annotation case, count: " + singleResult.length);
        System.out.println("Multi-annotation case, count: " + multiResult.length);

        // getAnnotation(Schedule.class) WORKS for the single case (no container was even synthesized).
        Schedule directSingle = singleMethod.getAnnotation(Schedule.class);
        System.out.println("Direct getAnnotation on single case: " + (directSingle != null));
    }
}
```

**How to run:** `java RepeatableSingleVsMultiple.java`

Expected output:
```
Single-annotation case, count: 1
Multi-annotation case, count: 2
Direct getAnnotation on single case: true
```

This demonstrates `getAnnotationsByType`'s key advantage: it works **uniformly** regardless of whether the annotation appears once or multiple times. `SingleScheduleJob` has exactly one `@Schedule` — no `Schedules` container is even synthesized by the compiler in this case, since there's nothing to collect — yet `getAnnotationsByType(Schedule.class)` still correctly returns a one-element array. `MultiScheduleJob`, with two `@Schedule` instances, correctly returns a two-element array. Notably, `getAnnotation(Schedule.class)` (the older, single-instance method) *does* work correctly for `SingleScheduleJob` specifically because there's genuinely only one instance and no container involved — it's only the multi-instance case where `getAnnotation(Schedule.class)` fails, as shown in Level 2.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `singleMethod` and `multiMethod` are obtained via reflection for `SingleScheduleJob.run()` and `MultiScheduleJob.run()` respectively.

`singleMethod.getAnnotationsByType(Schedule.class)` is called. Internally, this reflection method first checks whether `Schedule` instances are present directly (not through a container) — since `SingleScheduleJob.run()` has exactly one `@Schedule` annotation written directly on it, and no `Schedules` container was ever synthesized (the compiler only generates a container when the annotation is genuinely repeated more than once), `getAnnotationsByType` finds this single direct annotation and returns it wrapped in a one-element array.

`multiMethod.getAnnotationsByType(Schedule.class)` is called next. `MultiScheduleJob.run()` has two `@Schedule` annotations, which the compiler *did* automatically collect into a synthesized `Schedules` container annotation during compilation. `getAnnotationsByType` detects that no direct `Schedule` instance exists on the method (since the compiler moved both into the container), so it instead looks for the `Schedules` container, finds it, and unpacks its `.value()` array — the two original `Schedule` instances — returning them as a two-element array.

```
SingleScheduleJob.run(): ONE @Schedule written directly, no container synthesized
  getAnnotationsByType(Schedule.class) -> checks for direct instances -> finds 1 -> returns [Schedule]

MultiScheduleJob.run(): TWO @Schedule written, compiler synthesizes a Schedules container
  getAnnotationsByType(Schedule.class) -> checks for direct instances -> finds none
                                       -> checks for Schedules container -> found, unpacks .value()
                                       -> returns [Schedule, Schedule]
```

`singleResult.length` is `1`, printed as `"Single-annotation case, count: 1"`. `multiResult.length` is `2`, printed as `"Multi-annotation case, count: 2"`. Finally, `singleMethod.getAnnotation(Schedule.class)` is called — since `SingleScheduleJob.run()` has exactly one direct `Schedule` instance and no container involved at all, this traditional, single-instance lookup method works correctly here, returning the non-null `Schedule` instance. `directSingle != null` is `true`, printed as `"Direct getAnnotation on single case: true"` — confirming `getAnnotation(Schedule.class)`'s limitation is specifically about the *multiple*-instance case, not repeatable annotations in general.

## 7. Gotchas & takeaways

> `Method.getAnnotation(SomeType.class)` (the traditional lookup) returns `null` whenever a `@Repeatable` annotation is applied **more than once**, since the actual annotation present on the element is the synthesized container, not the individual repeated type — this is easy to miss if code written before an annotation was made repeatable (or before it was actually used repeatedly) still uses the old lookup method. Always use `getAnnotationsByType(SomeType.class)` when working with a `@Repeatable` annotation type, since it correctly and uniformly handles zero, one, or many instances.

- `@Repeatable(ContainerType.class)` on an annotation definition allows that annotation to be written multiple times on the same target, with the compiler auto-generating an instance of the specified container annotation to hold them.
- The container annotation type must itself be defined with a `value()` method returning an array of the repeated annotation type.
- `getAnnotationsByType(Type.class)` is the reflection method designed specifically for repeatable annotations — it works uniformly whether the annotation appears zero, one, or many times.
- `getAnnotation(Type.class)` (the older, single-instance lookup) returns `null` when the annotation is repeated more than once, since the container — not the repeated type itself — is what's actually present in that case.
- `getAnnotation(ContainerType.class)` can directly retrieve the synthesized container annotation itself, useful for accessing it as a whole rather than iterating its unpacked contents via `getAnnotationsByType`.
