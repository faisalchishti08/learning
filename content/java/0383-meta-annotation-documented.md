---
card: java
gi: 383
slug: meta-annotation-documented
title: 'Meta-annotation @Documented'
---

## 1. What it is

`@Documented` is a meta-annotation that tells the Javadoc tool to include your custom annotation in the generated documentation for any element it's applied to. Without `@Documented`, an annotation's presence is invisible in the generated HTML documentation, even though it's still fully present and functional in the actual `.class` file and at runtime — `@Documented` affects *only* what shows up in Javadoc output, nothing about compilation or runtime behaviour.

## 2. Why & when

Some annotations are purely internal bookkeeping — implementation details that a library's own build process cares about but that consumers of the library's public API don't need to see. Others carry information that's genuinely part of the *contract* a caller needs to understand — whether a method is thread-safe, whether a parameter must be non-null, whether an API is experimental and subject to change. For that second category, `@Documented` ensures the annotation shows up right in the generated Javadoc, alongside the method or class signature, so anyone reading the documentation (not just anyone reading the source code directly) sees the annotation's presence and meaning.

A well-known real example is `@Deprecated` itself, which is `@Documented` — this is exactly why deprecated methods show up with a visible "Deprecated" marker and explanation in generated Javadoc pages, not just as a compiler warning invisible to someone only reading the docs.

## 3. Core concept

```java
import java.lang.annotation.*;

public class DocumentedDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @Documented // this annotation's presence WILL show up in generated Javadoc
    @interface ThreadSafe {
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    // no @Documented -- this annotation's presence will NOT show up in generated Javadoc
    @interface InternalUseOnly {
    }

    static class Cache {
        /** Retrieves a cached value. */
        @ThreadSafe
        @InternalUseOnly
        Object get(String key) { return null; }
    }

    public static void main(String[] args) {
        System.out.println("Run 'javadoc' on this file to see @ThreadSafe appear, @InternalUseOnly not.");
    }
}
```

**How to run:** `java DocumentedDemo.java` runs the program (which just prints a note); to see the actual documentation effect, run `javadoc DocumentedDemo.java` and inspect the generated HTML for the `get` method.

Both `@ThreadSafe` and `@InternalUseOnly` are applied identically to `get`, and both are fully present and functional at runtime (both have `RUNTIME` retention). The only difference is that `@ThreadSafe` carries `@Documented`, so the generated Javadoc page for `get` will visibly list `@ThreadSafe` in its signature; `@InternalUseOnly`, lacking `@Documented`, is invisible in that same generated page even though `get`'s actual `.class` file and runtime reflection data still carry it.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Documented controls only whether an annotation appears in generated Javadoc HTML, with no effect on compilation, the class file, or runtime reflection">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">@ThreadSafe @InternalUseOnly  Object get(String key) { ... }  -- both present at runtime</text>

  <rect x="30" y="50" width="260" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="72" fill="#6db33f" font-size="10" text-anchor="middle">@ThreadSafe -- @Documented</text>
  <text x="160" y="87" fill="#8b949e" font-size="9" text-anchor="middle">shows up in generated Javadoc</text>

  <rect x="330" y="50" width="260" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="460" y="72" fill="#f85149" font-size="10" text-anchor="middle">@InternalUseOnly -- no @Documented</text>
  <text x="460" y="87" fill="#8b949e" font-size="9" text-anchor="middle">invisible in generated Javadoc</text>

  <text x="20" y="130" fill="#8b949e" font-size="10">Both still fully exist in the .class file and via reflection at runtime -- only the Javadoc output differs.</text>
</svg>

## 5. Runnable example

Scenario: a small library exposing a `@Beta` annotation to signal experimental APIs, evolved from an undocumented version invisible to API consumers reading the docs, through adding `@Documented`, to a version reflecting on both an internal and a public-facing annotation to show that the runtime behaviour never differs — only documentation visibility does.

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class BetaUndocumented {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface Beta { // consumers reading generated Javadoc will NEVER see this marker
    }

    static class ApiClient {
        /** Sends a request using the new streaming protocol. */
        @Beta
        void sendStreaming() { }
    }

    public static void main(String[] args) {
        System.out.println("javadoc output for sendStreaming() would NOT mention @Beta at all.");
    }
}
```

**How to run:** `java BetaUndocumented.java` (and separately, `javadoc BetaUndocumented.java` to inspect the generated HTML)

`@Beta` is fully applied to `sendStreaming` and fully visible to reflection — but anyone reading the generated Javadoc page for this method, rather than the raw source, would have no idea it's marked experimental, since `@Beta` itself isn't `@Documented`.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class BetaDocumented {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @Documented // the fix: this marker will now show up in generated Javadoc pages
    @interface Beta {
    }

    static class ApiClient {
        /** Sends a request using the new streaming protocol. */
        @Beta
        void sendStreaming() { }
    }

    public static void main(String[] args) {
        System.out.println("javadoc output for sendStreaming() will now show @Beta in its signature.");
    }
}
```

**How to run:** `java BetaDocumented.java` (and `javadoc BetaDocumented.java` to inspect the generated HTML)

Adding `@Documented` to `Beta`'s own declaration is the entire fix — `sendStreaming`'s Java source, compiled `.class` file, and runtime reflection data are all completely unchanged from Level 1; only the generated Javadoc HTML now visibly includes `@Beta` next to the method signature.

### Level 3 — Advanced

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;

public class BetaReflectionUnaffected {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @Documented
    @interface Beta {
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface Internal { // deliberately NOT @Documented
    }

    static class ApiClient {
        @Beta
        @Internal
        void sendStreaming() { }
    }

    public static void main(String[] args) throws Exception {
        Method m = ApiClient.class.getDeclaredMethod("sendStreaming");
        // Both are found identically via reflection -- @Documented has ZERO effect here
        System.out.println("Has @Beta (documented):    " + m.isAnnotationPresent(Beta.class));
        System.out.println("Has @Internal (undocumented): " + m.isAnnotationPresent(Internal.class));
    }
}
```

**How to run:** `java BetaReflectionUnaffected.java`

This makes the key point concrete: reflection finds `@Beta` and `@Internal` identically, both `true` — `@Documented`'s effect is entirely confined to Javadoc HTML generation and has absolutely no bearing on retention, reflection visibility, or any other runtime behaviour, which are governed purely by `@Retention` (see [[meta-annotation-retention-source-class-runtime]]).

## 6. Walkthrough

Execution starts in `main`. `ApiClient.class.getDeclaredMethod("sendStreaming")` uses reflection to locate the no-argument `sendStreaming` method, returning a `Method` object.

`m.isAnnotationPresent(Beta.class)` checks whether a `Beta` annotation is attached to this method in the runtime reflection data. Because `Beta` is declared with `@Retention(RetentionPolicy.RUNTIME)`, it is present in that data regardless of whether `@Documented` is also attached — `@Documented` plays no role whatsoever in this check. The result is `true`, printed as `Has @Beta (documented): true`.

`m.isAnnotationPresent(Internal.class)` performs the identical check for `Internal`. `Internal` also has `RetentionPolicy.RUNTIME`, so it is equally present in the runtime reflection data, despite lacking `@Documented`. The result is also `true`, printed as `Has @Internal (undocumented): true`.

The only place these two annotations would ever behave differently is in a separate, offline step never exercised by this program at all: running the `javadoc` tool over the source file. That tool would include `@Beta` in the generated HTML documentation for `sendStreaming` (because `Beta` carries `@Documented`) and omit `@Internal` entirely from that same generated page (because `Internal` does not) — a difference invisible to reflection, invisible at runtime, and invisible to the compiler, existing solely within Javadoc's own output.

Expected output:
```
Has @Beta (documented):    true
Has @Internal (undocumented): true
```

## 7. Gotchas & takeaways

> `@Documented` has zero effect on compilation, the generated `.class` file, or runtime reflection — it is purely a signal to the `javadoc` tool about what to include in generated HTML documentation. Confusing it with `@Retention(RetentionPolicy.RUNTIME)` (which does control runtime/reflection visibility) is an easy mistake for newcomers to annotations.

- `@Documented` controls only whether an annotation's presence appears in generated Javadoc HTML for the element it's applied to.
- It has no bearing whatsoever on compilation, the compiled `.class` file's contents, or whether the annotation is visible to reflection at runtime — those are governed entirely by `@Retention`.
- Apply `@Documented` to any custom annotation that carries meaning a caller of your public API genuinely needs to know about (thread-safety guarantees, nullability, experimental-API status) — skip it for purely internal, implementation-detail annotations.
- A well-known real-world example: `@Deprecated` itself is `@Documented`, which is why deprecated methods visibly show a "Deprecated" marker in generated Javadoc pages, not just a compiler warning.
- When designing a custom annotation, decide `@Documented`'s inclusion based purely on "should this show up in generated docs for API consumers?" — a question entirely separate from `@Retention`'s "should this be visible at runtime?" question.
