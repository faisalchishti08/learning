---
card: java
gi: 381
slug: meta-annotation-retention-source-class-runtime
title: 'Meta-annotation @Retention (SOURCE/CLASS/RUNTIME)'
---

## 1. What it is

`@Retention` is a **meta-annotation** — an annotation that goes on your custom annotation's declaration, controlling how that annotation itself behaves. `@Retention` specifically controls how long an annotation's presence is kept around: `RetentionPolicy.SOURCE` (discarded immediately after compilation, never even reaches the `.class` file), `RetentionPolicy.CLASS` (kept in the compiled `.class` file, but not loaded into the JVM at runtime — this is the default if you omit `@Retention` entirely), or `RetentionPolicy.RUNTIME` (kept in the `.class` file *and* available to reflection while the program runs).

## 2. Why & when

Different annotations serve entirely different purposes at different points in a program's life, and each policy matches one of those purposes precisely. `SOURCE` retention suits annotations meant purely for compiler checks or code-generation tools that run *before* compilation finishes — `@Override` and `@SuppressWarnings` are both `SOURCE`-retained, since their entire job is done by the time the `.class` file exists; keeping them around afterward would be pure waste. `CLASS` retention (the default) suits bytecode-level tools that inspect `.class` files directly without running the program — relatively rare in everyday application code. `RUNTIME` retention is what nearly every custom annotation you write for reflection-based use needs, since it's the only policy that lets `Class.getAnnotation(...)` and similar reflection calls actually see the annotation while the program is running.

The single most common beginner mistake with custom annotations is forgetting `@Retention(RetentionPolicy.RUNTIME)` entirely — the annotation compiles fine, applies fine, but silently vanishes before any reflection code gets a chance to look for it, since the default (`CLASS`) doesn't survive into the running JVM.

## 3. Core concept

```java
import java.lang.annotation.*;

public class RetentionDemo {
    @Retention(RetentionPolicy.SOURCE)
    @interface CompileTimeOnly { }

    @Retention(RetentionPolicy.RUNTIME)
    @interface VisibleAtRuntime { }

    @CompileTimeOnly
    @VisibleAtRuntime
    static class Marked { }

    public static void main(String[] args) {
        System.out.println("RUNTIME present: " +
                Marked.class.isAnnotationPresent(VisibleAtRuntime.class));
        System.out.println("SOURCE present: " +
                Marked.class.isAnnotationPresent(CompileTimeOnly.class));
    }
}
```

**How to run:** `java RetentionDemo.java`

Both annotations are applied identically to `Marked`, but reflection only finds `@VisibleAtRuntime` (`RUNTIME` retention) — `@CompileTimeOnly` (`SOURCE` retention) was stripped away entirely during compilation and never made it into the `.class` file at all, so `isAnnotationPresent` correctly reports it as absent, even though it's clearly written right there in the source.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SOURCE retention is discarded at compile time, CLASS retention survives into the class file but not the running JVM, RUNTIME retention survives all the way through and is visible to reflection">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#8b949e" font-size="10">source .java --&gt; compiled .class --&gt; running JVM (reflection)</text>

  <text x="20" y="60" fill="#f85149" font-size="10">SOURCE:</text>
  <line x1="90" y1="56" x2="230" y2="56" stroke="#f85149" stroke-width="2"/>
  <text x="240" y="60" fill="#f85149" font-size="9">discarded here -- never reaches .class file</text>

  <text x="20" y="100" fill="#79c0ff" font-size="10">CLASS (default):</text>
  <line x1="120" y1="96" x2="380" y2="96" stroke="#79c0ff" stroke-width="2"/>
  <text x="390" y="100" fill="#79c0ff" font-size="9">discarded here -- not loaded by JVM</text>

  <text x="20" y="140" fill="#6db33f" font-size="10">RUNTIME:</text>
  <line x1="100" y1="136" x2="560" y2="136" stroke="#6db33f" stroke-width="2"/>
  <text x="500" y="130" fill="#6db33f" font-size="9">visible to reflection</text>

  <text x="20" y="170" fill="#8b949e" font-size="10">Only RUNTIME-retained annotations can ever be found by Class.getAnnotation() or isAnnotationPresent().</text>
</svg>

## 5. Runnable example

Scenario: a custom `@Audited` annotation meant to be picked up by a reflection-based scanner, evolved from the classic forgotten-retention mistake (annotation silently invisible), through fixing it with `RUNTIME`, to a version comparing all three policies side by side to make the difference concrete.

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class AuditedMissingRetention {
    @interface Audited { // no @Retention at all -- defaults to CLASS, invisible to reflection
    }

    @Audited
    static class Account { }

    public static void main(String[] args) {
        boolean found = Account.class.isAnnotationPresent(Audited.class);
        System.out.println("Found @Audited via reflection: " + found); // false, surprisingly!
    }
}
```

**How to run:** `java AuditedMissingRetention.java`

`@Audited` is clearly present in the source and applied to `Account` — but with no `@Retention` specified, it defaults to `RetentionPolicy.CLASS`, which never gets loaded into the running JVM's reflection data. `isAnnotationPresent` correctly, if surprisingly, reports `false` — this is the classic "why isn't my annotation being detected?" bug.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class AuditedFixedRetention {
    @Retention(RetentionPolicy.RUNTIME) // the fix: explicitly keep it available at runtime
    @interface Audited {
    }

    @Audited
    static class Account { }

    public static void main(String[] args) {
        boolean found = Account.class.isAnnotationPresent(Audited.class);
        System.out.println("Found @Audited via reflection: " + found); // true now
    }
}
```

**How to run:** `java AuditedFixedRetention.java`

Adding `@Retention(RetentionPolicy.RUNTIME)` to `Audited`'s own declaration is the entire fix — nothing about how `@Audited` is applied to `Account` changes at all, but now reflection can actually see it, since it's retained all the way through to the running JVM.

### Level 3 — Advanced

```java
import java.lang.annotation.*;

public class RetentionComparison {
    @Retention(RetentionPolicy.SOURCE)
    @interface SourceOnly { }

    @Retention(RetentionPolicy.CLASS) // explicit, though it's also the implicit default
    @interface ClassOnly { }

    @Retention(RetentionPolicy.RUNTIME)
    @interface RuntimeVisible { }

    @SourceOnly
    @ClassOnly
    @RuntimeVisible
    static class TripleMarked { }

    public static void main(String[] args) {
        System.out.println("SourceOnly:     " + TripleMarked.class.isAnnotationPresent(SourceOnly.class));
        System.out.println("ClassOnly:      " + TripleMarked.class.isAnnotationPresent(ClassOnly.class));
        System.out.println("RuntimeVisible: " + TripleMarked.class.isAnnotationPresent(RuntimeVisible.class));
    }
}
```

**How to run:** `java RetentionComparison.java`

All three annotations are applied identically to `TripleMarked` in the source. Only `RuntimeVisible`, with explicit `RUNTIME` retention, is found by reflection — `SourceOnly` never survives past compilation, and `ClassOnly` survives into the `.class` file but is not loaded into the JVM's runtime reflection data, demonstrating all three retention levels' actual, observable behaviour in one place.

## 6. Walkthrough

Execution starts in `main`. `TripleMarked.class.isAnnotationPresent(SourceOnly.class)` is evaluated first: internally, this asks the JVM's runtime reflection data for `TripleMarked` whether a `SourceOnly` annotation is attached. Because `SourceOnly` is declared `@Retention(RetentionPolicy.SOURCE)`, the compiler discarded every trace of `@SourceOnly` on `TripleMarked` back when it produced the `.class` file — the annotation was used only during compilation (in this case, for nothing in particular, since no compiler plugin reads it) and then thrown away. The runtime reflection data therefore has no record of it at all, so `isAnnotationPresent` returns `false`.

`TripleMarked.class.isAnnotationPresent(ClassOnly.class)` runs next. `ClassOnly` is retained into the compiled `.class` file's bytecode (the annotation *is* physically present in the `.class` file on disk), but `RetentionPolicy.CLASS` tells the JVM's class loader not to expose it through the runtime reflection API. So even though the data technically exists in the file, `isAnnotationPresent` still returns `false` — it's checking the runtime-visible view, not the raw bytecode.

`TripleMarked.class.isAnnotationPresent(RuntimeVisible.class)` runs last. Because `RuntimeVisible` is declared `RetentionPolicy.RUNTIME`, the class loader does expose it through the runtime reflection API. `isAnnotationPresent` finds it and returns `true`.

Expected output:
```
SourceOnly:     false
ClassOnly:      false
RuntimeVisible: true
```

## 7. Gotchas & takeaways

> If you write a custom annotation intended to be read via reflection (by your own code, or a framework you're building) and it seems to silently "not exist" when you check for it, the first thing to check is whether `@Retention(RetentionPolicy.RUNTIME)` is present on the annotation's own declaration — omitting it defaults to `CLASS`, which is invisible to `isAnnotationPresent`/`getAnnotation` at runtime.

- `@Retention` is a meta-annotation: it annotates your annotation's *declaration*, not the code your annotation is later applied to.
- `RetentionPolicy.SOURCE` — discarded at compile time; used for compiler-only checks (`@Override`, `@SuppressWarnings`).
- `RetentionPolicy.CLASS` — the default if `@Retention` is omitted; kept in the `.class` file but not exposed to runtime reflection.
- `RetentionPolicy.RUNTIME` — kept and exposed to runtime reflection; required for any annotation your own code or a framework needs to detect with `isAnnotationPresent`/`getAnnotation` while the program is running.
- Nearly every custom annotation intended for framework-style, reflection-driven behaviour (like [[declaring-custom-annotations]]) needs `RUNTIME` retention — it is the one detail most likely to be forgotten when writing your first custom annotation.
