---
card: java
gi: 1001
slug: prototype
title: Prototype
---

## 1. What it is

The **Prototype** pattern creates new objects by **cloning an existing instance** rather than constructing one from scratch. Instead of `new ExpensiveObject(...)` and repeating a costly setup process, you call `existingInstance.clone()` (or a copy constructor) and get a new, independent object pre-populated with the same state — which you can then tweak. It's useful when constructing an object is expensive, or when you want to capture a fully-configured "template" object and stamp out variations of it.

## 2. Why & when

Some objects are expensive or awkward to build from scratch — they might load data from a file, run an expensive calculation to reach their initial state, or have a long chain of configuration calls needed to set them up "just right." Prototype lets you pay that cost once, keep the fully-configured object around as a template, and produce new instances by copying it — usually far cheaper than repeating the original construction process, and it also lets code that doesn't know a concrete class's constructor parameters still produce new instances of it (just by calling `clone()` on whatever prototype it was handed).

Reach for Prototype when object construction is measurably expensive, or when you have a "template" configuration you want to vary slightly for each use (a base enemy configuration in a game, cloned and tweaked per spawn). Skip it for cheap, simple objects — a plain constructor is simpler and cloning adds indirection with no payoff.

## 3. Core concept

```
class Document implements Cloneable {
    private String title;
    private java.util.List<String> paragraphs;

    Document(String title, java.util.List<String> paragraphs) {
        this.title = title;
        this.paragraphs = new java.util.ArrayList<>(paragraphs); // deep copy the mutable list
    }

    @Override
    public Document clone() {
        return new Document(title, paragraphs); // returns an INDEPENDENT copy
    }

    void setTitle(String title) { this.title = title; }
    java.util.List<String> getParagraphs() { return paragraphs; }
}

Document template = new Document("Report Template", java.util.List.of("Intro", "Body", "Conclusion"));
Document reportA = template.clone();
reportA.setTitle("Q1 Report"); // mutating the clone never touches `template`
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A prototype Document being cloned twice, producing two independent copies that can each be modified without affecting the original or each other">
  <rect x="30" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">template (prototype)</text>

  <rect x="300" y="20" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="50" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">clone() -&gt; reportA</text>

  <rect x="300" y="110" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">clone() -&gt; reportB</text>

  <line x1="180" y1="90" x2="300" y2="45" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="180" y1="95" x2="300" y2="135" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each `clone()` call produces an independent copy — mutating `reportA` never affects `template` or `reportB`.

## 5. Runnable example

Scenario: a report-generation system with a fully-configured document template, evolving from a shallow clone that leaks shared mutable state into a safe, deep-copying prototype used to stamp out independent reports.

### Level 1 — Basic

```java
// File: PrototypeBasic.java
import java.util.ArrayList;
import java.util.List;

class Document implements Cloneable {
    String title;
    List<String> paragraphs;

    Document(String title, List<String> paragraphs) {
        this.title = title;
        this.paragraphs = paragraphs;
    }

    @Override
    public Document clone() {
        try {
            return (Document) super.clone(); // shallow clone: paragraphs list is SHARED
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);
        }
    }
}

public class PrototypeBasic {
    public static void main(String[] args) {
        Document template = new Document("Report", new ArrayList<>(List.of("Intro", "Body")));
        Document reportA = template.clone();
        reportA.paragraphs.add("Conclusion"); // oops -- this mutates the SAME list as template

        System.out.println("template: " + template.paragraphs);
        System.out.println("reportA:  " + reportA.paragraphs);
    }
}
```

**How to run:** save as `PrototypeBasic.java`, then `javac PrototypeBasic.java && java PrototypeBasic` (JDK 17+).

Expected output:
```
template: [Intro, Body, Conclusion]
reportA:  [Intro, Body, Conclusion]
```

`super.clone()` performs a **shallow** copy: `reportA` gets its own `Document` object, but `paragraphs` still points at the exact same `ArrayList` as `template` — mutating one mutates both, defeating the point of cloning an independent copy.

### Level 2 — Intermediate

```java
// File: PrototypeIntermediate.java
import java.util.ArrayList;
import java.util.List;

class Document implements Cloneable {
    String title;
    List<String> paragraphs;

    Document(String title, List<String> paragraphs) {
        this.title = title;
        this.paragraphs = paragraphs;
    }

    @Override
    public Document clone() {
        // Deep copy: give the clone its OWN independent paragraphs list.
        return new Document(this.title, new ArrayList<>(this.paragraphs));
    }
}

public class PrototypeIntermediate {
    public static void main(String[] args) {
        Document template = new Document("Report", new ArrayList<>(List.of("Intro", "Body")));
        Document reportA = template.clone();
        reportA.paragraphs.add("Conclusion");

        System.out.println("template: " + template.paragraphs);
        System.out.println("reportA:  " + reportA.paragraphs);
    }
}
```

**How to run:** save as `PrototypeIntermediate.java`, then `javac PrototypeIntermediate.java && java PrototypeIntermediate` (JDK 17+).

Expected output:
```
template: [Intro, Body]
reportA:  [Intro, Body, Conclusion]
```

The real-world concern added: `clone()` now creates a genuinely independent `paragraphs` list for the copy. Mutating `reportA` no longer affects `template` at all — the two are fully separate objects, as cloning should provide.

### Level 3 — Advanced

```java
// File: PrototypeAdvanced.java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// Metadata is a nested mutable object too -- a deep clone must copy it recursively,
// not just the top-level fields, or the same shallow-copy bug reappears one level down.
class Metadata implements Cloneable {
    Map<String, String> tags;
    Metadata(Map<String, String> tags) { this.tags = new HashMap<>(tags); }

    @Override
    public Metadata clone() { return new Metadata(this.tags); }
}

class Document implements Cloneable {
    String title;
    List<String> paragraphs;
    Metadata metadata;

    Document(String title, List<String> paragraphs, Metadata metadata) {
        this.title = title;
        this.paragraphs = paragraphs;
        this.metadata = metadata;
    }

    @Override
    public Document clone() {
        // Deep clone at every level: a fresh list AND a freshly-cloned Metadata object.
        return new Document(this.title, new ArrayList<>(this.paragraphs), this.metadata.clone());
    }

    @Override public String toString() {
        return title + " " + paragraphs + " tags=" + metadata.tags;
    }
}

public class PrototypeAdvanced {
    public static void main(String[] args) {
        Metadata baseMetadata = new Metadata(Map.of("type", "report"));
        Document template = new Document("Report", new ArrayList<>(List.of("Intro", "Body")), baseMetadata);

        Document reportA = template.clone();
        reportA.title = "Q1 Report";
        reportA.paragraphs.add("Conclusion");
        reportA.metadata.tags.put("quarter", "Q1");

        System.out.println("template: " + template);
        System.out.println("reportA:  " + reportA);
    }
}
```

**How to run:** save as `PrototypeAdvanced.java`, then `javac PrototypeAdvanced.java && java PrototypeAdvanced` (JDK 17+).

Expected output:
```
template: Report [Intro, Body] tags={type=report}
reportA:  Q1 Report [Intro, Body, Conclusion] tags={type=report, quarter=Q1}
```

The production-flavored hard case: `Document` now has a nested mutable object (`Metadata`), and cloning it correctly requires recursively cloning that nested object too — `Document.clone()` calls `this.metadata.clone()` rather than sharing the reference, so mutating `reportA.metadata.tags` never leaks back into `template.metadata.tags`.

## 6. Walkthrough

Tracing `template.clone()` followed by the three mutations in `PrototypeAdvanced.main`:

1. `template.clone()` runs `Document.clone()`: it builds a `new Document(...)` passing `this.title` (a `String`, immutable, safe to share), `new ArrayList<>(this.paragraphs)` (a fresh list with copied contents), and `this.metadata.clone()`.
2. `this.metadata.clone()` runs `Metadata.clone()`, which returns `new Metadata(this.tags)` — and `Metadata`'s constructor itself does `new HashMap<>(tags)`, so the clone's `tags` map is also a fresh copy, not a shared reference.
3. The result, `reportA`, is now a fully independent `Document`: its own `title` reference, its own `paragraphs` list object, and its own `metadata` object wrapping its own `tags` map.
4. `reportA.title = "Q1 Report"` reassigns a field only on `reportA` — `template.title` is unaffected since `String` reassignment never mutates shared state anyway.
5. `reportA.paragraphs.add("Conclusion")` mutates `reportA`'s own list (from step 1) — `template.paragraphs` still has only `[Intro, Body]`, since it's a genuinely different `ArrayList` instance.
6. `reportA.metadata.tags.put("quarter", "Q1")` mutates `reportA.metadata`'s own `HashMap` (from step 2) — `template.metadata.tags` still has only `{type=report}`, since it's a genuinely different map instance. The two printed lines confirm every level of the clone is independent.

## 7. Gotchas & takeaways

> **Gotcha:** `Object.clone()` (via `super.clone()`) performs a **shallow** copy by default — every field is copied by reference, meaning any mutable field (a `List`, a `Map`, another object) ends up shared between the original and the clone unless you explicitly deep-copy it yourself.

- Prototype creates new instances by copying an existing "template" object instead of constructing from scratch — useful when construction is expensive or when a pre-configured template is the natural starting point.
- A shallow clone shares mutable fields between original and copy — a classic and easy-to-miss bug; a deep clone recursively copies every mutable field.
- In modern Java, a copy constructor (`new Document(this.title, ...)`) is often clearer and safer than implementing `Cloneable`, which has well-known design warts (no way to enforce implementation, checked `CloneNotSupportedException`).
- Nested mutable objects need their own `clone()` (or equivalent copy logic) too — deep-copying stops being "deep" the moment one nested reference is shared instead of copied.
- Records and immutable value objects sidestep this whole problem: if nothing is mutable, sharing a reference is perfectly safe, and Prototype-style cloning becomes largely unnecessary.
- Prototype is often used alongside [Factory Method](0998-factory-method.md) when a factory needs to produce variations of a pre-configured template rather than building each instance from raw parameters.
