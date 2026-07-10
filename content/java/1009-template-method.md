---
card: java
gi: 1009
slug: template-method
title: Template Method
---

## 1. What it is

The **Template Method** pattern defines the overall **skeleton** of an algorithm in a base class method, deferring some of its individual steps to subclasses. The base class controls the sequence — what happens first, second, third — while each subclass fills in the specific details of one or more steps by overriding them. Callers always invoke the same base-class method; the *shape* of the algorithm never changes, only the customizable steps inside it.

## 2. Why & when

When several variants of a process share the same overall sequence but differ in a few specific steps — parsing a CSV file versus a JSON file both involve "open, read, parse, close," but the "parse" step differs — duplicating the entire sequence in each variant means the shared structure (and any bug fix to it) has to be repeated and kept in sync across every variant. Template Method exists to write that shared sequence exactly once, in the base class, and let subclasses override only the steps that genuinely differ.

Reach for Template Method when you have a multi-step process where the order of steps is fixed and shared, but one or a few of those steps vary by subclass. It's unnecessary when every step of the process varies independently between contexts — that's more naturally expressed with [Strategy](1007-strategy.md), which composes an object with a swappable algorithm reference rather than committing to an inheritance hierarchy.

## 3. Core concept

```
abstract class DataProcessor {
    // The template method: defines the fixed SEQUENCE, marked final so subclasses can't reorder it
    final void process() {
        openSource();
        readData();
        String parsed = parseData(); // the ONE step subclasses customize
        System.out.println("Processed: " + parsed);
        closeSource();
    }

    void openSource() { System.out.println("Opening source"); }
    void readData() { System.out.println("Reading raw data"); }
    abstract String parseData(); // subclasses MUST provide this
    void closeSource() { System.out.println("Closing source"); }
}

class CsvProcessor extends DataProcessor {
    String parseData() { return "parsed as CSV rows"; }
}
class JsonProcessor extends DataProcessor {
    String parseData() { return "parsed as JSON tree"; }
}

new CsvProcessor().process();  // same sequence, different parseData() step
new JsonProcessor().process();
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DataProcessor's fixed process method calling openSource, readData, parseData, closeSource in order, with parseData being the only step overridden differently by CsvProcessor and JsonProcessor">
  <rect x="220" y="10" width="200" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="31" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">process() [fixed sequence]</text>

  <rect x="40" y="70" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">openSource()</text>
  <rect x="180" y="70" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="240" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">readData()</text>
  <rect x="320" y="70" width="120" height="30" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="380" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">parseData() *</text>
  <rect x="460" y="70" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="520" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">closeSource()</text>

  <rect x="280" y="140" width="100" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="160" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CsvProcessor</text>
  <rect x="400" y="140" width="100" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="450" y="160" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JsonProcessor</text>

  <line x1="330" y1="140" x2="380" y2="100" stroke="#f0883e" marker-end="url(#a)"/>
  <line x1="450" y1="140" x2="380" y2="100" stroke="#f0883e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker></defs>
</svg>

The `*`-marked step, `parseData()`, is the only one subclasses override — the surrounding sequence is fixed in the base class.

## 5. Runnable example

Scenario: a data-import pipeline supporting multiple file formats, evolving from duplicated sequence logic per format into a shared template method with one customizable step.

### Level 1 — Basic

```java
// File: TemplateMethodBasic.java
class CsvProcessor {
    void process() {
        System.out.println("Opening source");
        System.out.println("Reading raw data");
        System.out.println("Processed: parsed as CSV rows");
        System.out.println("Closing source");
    }
}
class JsonProcessor {
    void process() {
        System.out.println("Opening source");
        System.out.println("Reading raw data");
        System.out.println("Processed: parsed as JSON tree");
        System.out.println("Closing source");
    }
}

public class TemplateMethodBasic {
    public static void main(String[] args) {
        new CsvProcessor().process();
        System.out.println("---");
        new JsonProcessor().process();
    }
}
```

**How to run:** save as `TemplateMethodBasic.java`, then `javac TemplateMethodBasic.java && java TemplateMethodBasic` (JDK 17+).

Expected output:
```
Opening source
Reading raw data
Processed: parsed as CSV rows
Closing source
---
Opening source
Reading raw data
Processed: parsed as JSON tree
Closing source
```

The "opening," "reading," and "closing" steps are duplicated identically in both classes — a change to how the source is opened has to be made in every processor class separately, and it's easy for them to drift out of sync.

### Level 2 — Intermediate

```java
// File: TemplateMethodIntermediate.java
abstract class DataProcessor {
    final void process() {
        openSource();
        readData();
        String parsed = parseData();
        System.out.println("Processed: " + parsed);
        closeSource();
    }

    void openSource() { System.out.println("Opening source"); }
    void readData() { System.out.println("Reading raw data"); }
    abstract String parseData();
    void closeSource() { System.out.println("Closing source"); }
}

class CsvProcessor extends DataProcessor {
    String parseData() { return "parsed as CSV rows"; }
}
class JsonProcessor extends DataProcessor {
    String parseData() { return "parsed as JSON tree"; }
}

public class TemplateMethodIntermediate {
    public static void main(String[] args) {
        new CsvProcessor().process();
        System.out.println("---");
        new JsonProcessor().process();
    }
}
```

**How to run:** save as `TemplateMethodIntermediate.java`, then `javac TemplateMethodIntermediate.java && java TemplateMethodIntermediate` (JDK 17+).

Expected output:
```
Opening source
Reading raw data
Processed: parsed as CSV rows
Closing source
---
Opening source
Reading raw data
Processed: parsed as JSON tree
Closing source
```

The real-world concern added: `openSource`, `readData`, and `closeSource` now live exactly once, in `DataProcessor`. Each subclass only implements `parseData()` — the one step that genuinely varies. `process()` is marked `final` so subclasses can't reorder or skip steps.

### Level 3 — Advanced

```java
// File: TemplateMethodAdvanced.java
abstract class DataProcessor {
    final void process() {
        openSource();
        readData();
        String parsed = parseData();
        System.out.println("Processed: " + parsed);
        if (shouldValidate()) { // an optional "hook" -- subclasses opt in by overriding it
            validate(parsed);
        }
        closeSource();
    }

    void openSource() { System.out.println("Opening source"); }
    void readData() { System.out.println("Reading raw data"); }
    abstract String parseData();

    // Hook methods: have a sensible default, subclasses MAY override, unlike parseData()
    // which they MUST override.
    boolean shouldValidate() { return false; }
    void validate(String parsed) { /* no-op by default */ }

    void closeSource() { System.out.println("Closing source"); }
}

class CsvProcessor extends DataProcessor {
    String parseData() { return "parsed as CSV rows"; }
}

// Overrides the OPTIONAL hooks too, adding validation without touching process() at all.
class JsonProcessor extends DataProcessor {
    String parseData() { return "parsed as JSON tree"; }

    @Override boolean shouldValidate() { return true; }
    @Override void validate(String parsed) {
        System.out.println("Validating: " + parsed + " -- looks well-formed");
    }
}

public class TemplateMethodAdvanced {
    public static void main(String[] args) {
        new CsvProcessor().process();
        System.out.println("---");
        new JsonProcessor().process();
    }
}
```

**How to run:** save as `TemplateMethodAdvanced.java`, then `javac TemplateMethodAdvanced.java && java TemplateMethodAdvanced` (JDK 17+).

Expected output:
```
Opening source
Reading raw data
Processed: parsed as CSV rows
Closing source
---
Opening source
Reading raw data
Processed: parsed as JSON tree
Validating: parsed as JSON tree -- looks well-formed
Closing source
```

The production-flavored hard case: `shouldValidate()` and `validate(...)` are optional "hook" methods with harmless defaults — `CsvProcessor` doesn't override them and simply skips validation, while `JsonProcessor` opts in by overriding both, adding a whole new conditional step to the sequence without ever touching `DataProcessor.process()` itself.

## 6. Walkthrough

Tracing `new JsonProcessor().process()` in `TemplateMethodAdvanced.main`:

1. `process()` is inherited unchanged from `DataProcessor` (it's `final`, so `JsonProcessor` can't override it). It calls `openSource()`, which resolves to `DataProcessor`'s own default implementation (neither subclass overrides it), printing `"Opening source"`.
2. `readData()` similarly resolves to the base default, printing `"Reading raw data"`.
3. `parseData()` is called — because it's `abstract` in `DataProcessor`, Java dispatches to `JsonProcessor.parseData()`, which returns `"parsed as JSON tree"`. This is printed as `"Processed: parsed as JSON tree"`.
4. `shouldValidate()` is called next — `JsonProcessor` overrides it to return `true` (unlike `CsvProcessor`, which inherits the base default of `false`), so the `if` branch is entered.
5. `validate(parsed)` is called with `"parsed as JSON tree"` — dispatching to `JsonProcessor.validate`, which prints `"Validating: parsed as JSON tree -- looks well-formed"`.
6. `closeSource()` resolves to the base default, printing `"Closing source"`. The overall step order — open, read, parse, [optionally validate], close — was entirely fixed by `DataProcessor.process()`; only which methods ran at the "parse" and "validate" points varied by subclass.

## 7. Gotchas & takeaways

> **Gotcha:** marking the template method `final` (as `process()` is here) is important — without it, a subclass could override `process()` itself and reorder or skip steps, silently breaking the guaranteed sequence that's the entire point of the pattern.

- Template Method fixes the overall sequence of an algorithm in a base class, deferring one or more individual steps to subclasses via `abstract` methods.
- "Hook" methods (like `shouldValidate()`) provide a harmless default and let subclasses optionally customize behavior beyond the mandatory `abstract` steps, without forcing every subclass to override them.
- Marking the template method itself `final` protects the fixed sequence from being silently reordered or bypassed by a subclass.
- It shares the base-class fixed-sequence code across all variants exactly once, unlike duplicating the whole process per variant.
- Don't reach for Template Method when every step of a process varies independently by context — that's better modeled with [Strategy](1007-strategy.md), composing swappable algorithm objects rather than committing to an inheritance hierarchy for the whole process.
- Because it relies on inheritance, keep [SOLID — Liskov Substitution](0991-solid-liskov-substitution.md) in mind: every subclass's overridden steps must genuinely fit into the fixed sequence without violating what the base class's process assumes.
