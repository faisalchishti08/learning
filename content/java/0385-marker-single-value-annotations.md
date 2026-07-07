---
card: java
gi: 385
slug: marker-single-value-annotations
title: Marker & single-value annotations
---

## 1. What it is

Annotations come in a few common shapes, distinguished by how many elements they declare. A **marker annotation** has zero elements — it carries no data at all, just its presence or absence (`@Deprecated`, a bare custom `@Flagged`-style marker). A **single-value annotation** has exactly one element, conventionally named `value`, which lets it use a shorthand syntax: `@SuppressWarnings("unchecked")` instead of the fully-qualified `@SuppressWarnings(value = "unchecked")`. Both are just ordinary annotations — the "marker" and "single-value" labels describe usage patterns, not a distinct language feature.

## 2. Why & when

Choosing between these shapes (versus a full multi-element annotation, covered in [[annotation-elements-default-values]]) comes down to how much information the annotation genuinely needs to carry. A marker annotation is right whenever the only useful fact is "is this thing marked or not?" — `@Override`, `@Deprecated`, and a custom `@ThreadSafe` are all naturally binary. A single-value annotation is right when there's exactly one clearly-primary piece of data — `@SuppressWarnings`'s warning category, or a custom `@Author("Jane")` naming exactly one person.

The `value` shorthand exists specifically to keep these common, simple cases visually clean: `@Author("Jane")` reads naturally, almost like a function call, whereas `@Author(value = "Jane")` is needlessly verbose for something with only one thing to say. Reach for a marker when there's truly nothing more to configure; reach for single-value when there's one dominant piece of information; reach for full multi-element syntax only when an annotation genuinely needs several independent pieces of data.

## 3. Core concept

```java
import java.lang.annotation.*;

public class MarkerSingleValueDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @interface Experimental { // marker: zero elements, pure presence/absence
    }

    @Retention(RetentionPolicy.RUNTIME)
    @interface Author { // single-value: one element named 'value'
        String value();
    }

    @Experimental
    @Author("Priya") // shorthand -- equivalent to @Author(value = "Priya")
    static void newFeature() { }

    public static void main(String[] args) {
        System.out.println("Both annotations applied using their natural shorthand forms.");
    }
}
```

**How to run:** `java MarkerSingleValueDemo.java`

`@Experimental` has no elements at all — it's applied with no parentheses, a pure marker. `@Author("Priya")` uses the single-`value`-element shorthand: because `Author` declares exactly one element, and it's named `value`, the `value =` prefix can be omitted entirely.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a marker annotation carries no data at all; a single-value annotation carries exactly one element named value, which allows a shorthand call syntax">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="50" fill="#79c0ff" font-size="10" text-anchor="middle">@Experimental</text>
  <text x="160" y="65" fill="#8b949e" font-size="9" text-anchor="middle">marker -- zero elements</text>

  <rect x="330" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="50" fill="#6db33f" font-size="10" text-anchor="middle">@Author("Priya")</text>
  <text x="460" y="65" fill="#8b949e" font-size="9" text-anchor="middle">single-value -- one 'value' element, shorthand syntax</text>

  <text x="20" y="115" fill="#8b949e" font-size="10">@Author("Priya") is shorthand for @Author(value = "Priya") -- only works because 'value' is the ONLY element.</text>
</svg>

## 5. Runnable example

Scenario: annotating configuration classes with ownership and stability information, evolved from a marker-only version, through adding a single-value element for the owning team, to a version where mixing multiple elements forces dropping the shorthand entirely.

### Level 1 — Basic

```java
import java.lang.annotation.*;

public class ConfigMarkerOnly {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @interface Unstable { // pure marker: no way to say WHO decided it's unstable, or why
    }

    @Unstable
    static class ExperimentalConfig { }

    public static void main(String[] args) {
        System.out.println("ExperimentalConfig marked @Unstable: " +
                ExperimentalConfig.class.isAnnotationPresent(Unstable.class));
    }
}
```

**How to run:** `java ConfigMarkerOnly.java`

`@Unstable` is a pure marker — useful for a simple yes/no fact, but it can never express additional context like which team owns the decision or why it's considered unstable.

### Level 2 — Intermediate

```java
import java.lang.annotation.*;

public class ConfigSingleValue {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @interface OwnedBy { // single-value: exactly one dominant piece of data
        String value();
    }

    @OwnedBy("platform-team") // shorthand -- no need to write value=
    static class ExperimentalConfig { }

    public static void main(String[] args) {
        OwnedBy owner = ExperimentalConfig.class.getAnnotation(OwnedBy.class);
        System.out.println("Owned by: " + owner.value());
    }
}
```

**How to run:** `java ConfigSingleValue.java`

`@OwnedBy("platform-team")` carries exactly the one piece of information that matters here — the owning team — using the terse shorthand syntax, since `value` is `OwnedBy`'s sole element.

### Level 3 — Advanced

```java
import java.lang.annotation.*;

public class ConfigMultiElementForcesFullSyntax {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @interface OwnedBy {
        String team();          // now two elements -- shorthand no longer applies
        String contactEmail() default "";
    }

    // @OwnedBy("platform-team") // this would NOT compile anymore -- 'team' isn't named 'value'
    @OwnedBy(team = "platform-team", contactEmail = "platform@example.com") // must name every element now
    static class ExperimentalConfig { }

    public static void main(String[] args) {
        OwnedBy owner = ExperimentalConfig.class.getAnnotation(OwnedBy.class);
        System.out.println("Team: " + owner.team() + ", contact: " + owner.contactEmail());
    }
}
```

**How to run:** `java ConfigMultiElementForcesFullSyntax.java`

Once `OwnedBy` grows a second element (`contactEmail`), the shorthand from Level 2 is no longer available — even though `team` is conceptually "the main thing," it isn't named `value`, so every use site must now name both elements explicitly. This shows the concrete boundary of the single-value shorthand: it only ever applies when there's exactly one element, and it must specifically be named `value`.

## 6. Walkthrough

Execution starts in `main`. `ExperimentalConfig.class.getAnnotation(OwnedBy.class)` retrieves the `@OwnedBy(team = "platform-team", contactEmail = "platform@example.com")` annotation instance attached to `ExperimentalConfig`.

`owner.team()` calls the generated accessor method for the `team` element, returning the string `"platform-team"` exactly as written at the annotation's use site. `owner.contactEmail()` similarly returns `"platform@example.com"`.

These two values are concatenated into the message `"Team: platform-team, contact: platform@example.com"` and printed by `System.out.println`.

Contrast this with the commented-out line above it: `@OwnedBy("platform-team")` — the Level 2-style shorthand — would fail to compile here, because `OwnedBy` (in this Level 3 version) no longer has a single element named `value`; it has two elements, `team` and `contactEmail`, neither of which is named `value`. The compiler requires every element to be named explicitly whenever the shorthand's specific condition (exactly one element, named `value`) isn't met.

Expected output:
```
Team: platform-team, contact: platform@example.com
```

## 7. Gotchas & takeaways

> The single-element shorthand (`@Author("Jane")`) works *only* when the annotation has exactly one element and that element is specifically named `value` — an annotation with one element named anything else (like `team()` instead of `value()`) never gets the shorthand, no matter how "obviously singular" that one element feels.

- A marker annotation has zero elements and carries pure presence/absence information — `@Override`, `@Deprecated`, and simple custom flags are typical examples.
- A single-value annotation has exactly one element, conventionally named `value`, enabling the shorthand `@Name("x")` instead of `@Name(value = "x")`.
- The shorthand is purely syntactic sugar tied to the specific element name `value` — it disappears the moment a second element is added, or if the sole element isn't named `value`.
- Choosing marker vs. single-value vs. multi-element should be driven by how much genuinely independent information the annotation needs to carry, not by a preference for terser syntax alone.
- When designing your own annotation, naming its most essential element `value` (if there's exactly one) is a small, deliberate choice that keeps the common usage clean and readable at every call site.
