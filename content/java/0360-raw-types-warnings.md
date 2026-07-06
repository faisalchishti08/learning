---
card: java
gi: 360
slug: raw-types-warnings
title: Raw types & warnings
---

## 1. What it is

A raw type is a generic class or interface used *without* any type argument at all — `List` instead of `List<String>`, `Map` instead of `Map<String, Integer>`. Raw types are a legacy compatibility feature: they let pre-generics code (written before Java 5) keep compiling unchanged, but using one in new code discards all of generics' compile-time type checking for that variable, replacing it with unchecked `Object`-based operations and compiler warnings at every point of potential trouble.

```java
import java.util.List;
import java.util.ArrayList;

public class RawTypeDemo {
    public static void main(String[] args) {
        List rawList = new ArrayList(); // raw type -- no type argument at all
        rawList.add("hello");
        rawList.add(42); // compiles! the raw type has NO element type to enforce

        for (Object item : rawList) {
            System.out.println(item + " (" + item.getClass().getSimpleName() + ")");
        }
    }
}
```

`List rawList` (no `<String>` or any other type argument) accepts both a `String` and an `Integer` without complaint — a raw type behaves as if every method involving its type parameter was declared with `Object` instead, exactly reverting to pre-generics behavior.

## 2. Why & when

Raw types exist purely to let old, pre-Java-5 code (and libraries compiled against that era) continue compiling and running without modification alongside newer generic code — a deliberate backward-compatibility decision, not a feature meant to be used in code you're writing today.

- **Interoperating with genuinely old, unmodified legacy code** — a rare, narrow case where an old API predates generics and truly cannot be changed, and raw types are the only way to call into it directly.
- **Recognizing raw types in code you're reading or maintaining** — spotting `List list = ...` (no type argument) as a compiler-warning-generating red flag, distinct from an intentional wildcard (`List<?>`) which looks similar but carries very different safety guarantees.
- **Understanding "unchecked" compiler warnings** — nearly every "unchecked call" or "unchecked conversion" warning traces back to a raw type being used somewhere, mixed with generic code that expects real type information.

New code should almost never intentionally use a raw type — if you want "a list of unknown type," `List<?>` is almost always the correct choice, preserving full compile-time type safety for reads (as with wildcards) while raw types abandon type safety entirely, for both reads and writes, silently allowing exactly the kind of type mismatch bug generics were introduced to prevent.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class RawTypeCore {
    @SuppressWarnings({"unchecked", "rawtypes"})
    public static void main(String[] args) {
        List<String> strings = new ArrayList<>();
        strings.add("a");
        strings.add("b");

        List raw = strings; // assigning a generic list to a raw type reference -- legal, but a warning
        raw.add(42); // compiles due to the raw type, but corrupts the "real" List<String> underneath!

        try {
            for (String s : strings) { // strings is STILL declared as List<String>
                System.out.println(s);
            }
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
    }
}
```

**How to run:** `java RawTypeCore.java`

Assigning `strings` (a real `List<String>`) to a raw `List raw` reference and adding an `Integer` through it compiles without error at that point — but `strings` and `raw` are the *same underlying list object*, so the corruption is real: when the code later iterates `strings` expecting only `String`s, it hits the `Integer` and throws `ClassCastException` at the point where the compiler's inserted cast (implicit in the for-each loop) fails.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a raw type reference to a generic list bypasses all compile-time type checking, letting mismatched values be added that later cause a ClassCastException when read through the original generic reference">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="52" fill="#6db33f" font-size="10" text-anchor="middle">List&lt;String&gt; strings (checked)</text>

  <text x="260" y="52" fill="#8b949e" font-size="10">same object, raw ref →</text>

  <rect x="400" y="30" width="180" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="490" y="52" fill="#f85149" font-size="10" text-anchor="middle">List raw (unchecked!)</text>

  <text x="20" y="100" fill="#8b949e" font-size="9">raw.add(42) corrupts the SAME list -- strings later throws ClassCastException reading it back as String.</text>
</svg>

## 5. Runnable example

Scenario: a small legacy-interop scenario, evolved from an actual raw-type usage (as pre-generics code would look), into a version isolating and minimizing the raw-type surface, into a production-style adapter that fully confines raw-type risk to one small, carefully-checked boundary function.

### Level 1 — Basic

```java
import java.util.List;
import java.util.ArrayList;

public class LegacyBasic {
    @SuppressWarnings({"rawtypes", "unchecked"})
    static List getLegacyData() { // imagine this simulates an old, pre-generics API
        List data = new ArrayList();
        data.add("first");
        data.add("second");
        return data;
    }

    public static void main(String[] args) {
        List raw = getLegacyData(); // raw type used directly and pervasively
        for (Object item : raw) {
            System.out.println(item);
        }
    }
}
```

**How to run:** `java LegacyBasic.java`

This simulates calling into pre-generics-style code — the raw type is used both at the "legacy" method's boundary and by the caller, meaning the caller gets zero compile-time type safety at all, exactly reproducing what code written before Java 5 looked like everywhere.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.ArrayList;

public class LegacyIntermediate {
    @SuppressWarnings({"rawtypes", "unchecked"})
    static List getLegacyDataRaw() { // the "legacy" boundary -- still raw, unavoidably
        List data = new ArrayList();
        data.add("first");
        data.add("second");
        return data;
    }

    @SuppressWarnings("unchecked")
    static List<String> getLegacyData() { // adapter: confines the raw type to ONE place
        return getLegacyDataRaw(); // unchecked conversion happens exactly here, once
    }

    public static void main(String[] args) {
        List<String> data = getLegacyData(); // fully type-safe from here on
        for (String item : data) { // no cast needed, compiler trusts the adapter
            System.out.println(item);
        }
    }
}
```

**How to run:** `java LegacyIntermediate.java`

`getLegacyData` acts as a thin adapter, confining the raw-type interaction to a single unchecked conversion at one clearly-marked boundary — everything downstream of it (`main`'s use of `data`) gets full, genuine compile-time type safety, since the risk has been isolated rather than spread throughout the calling code.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;
import java.util.Objects;

public class LegacyAdvanced {
    @SuppressWarnings({"rawtypes", "unchecked"})
    static List getLegacyDataRaw() {
        List data = new ArrayList();
        data.add("first");
        data.add("second");
        data.add(42); // simulates a legacy source that occasionally has bad, mismatched data
        return data;
    }

    static List<String> getLegacyDataSafely() {
        List<?> raw = getLegacyDataRaw(); // wildcard, not raw -- one step safer already
        List<String> validated = new ArrayList<>();
        for (Object item : raw) {
            if (item instanceof String s) {
                validated.add(s);
            } else {
                System.out.println("Skipping non-String legacy entry: " + item
                        + " (" + Objects.requireNonNull(item).getClass().getSimpleName() + ")");
            }
        }
        return validated;
    }

    public static void main(String[] args) {
        List<String> data = getLegacyDataSafely();
        for (String item : data) {
            System.out.println("Valid entry: " + item);
        }
    }
}
```

**How to run:** `java LegacyAdvanced.java`

`getLegacyDataSafely` goes further than just confining the raw type — it treats the legacy source's data as genuinely untrustworthy, using `instanceof String s` pattern matching to validate *each individual element* before accepting it into the real, type-safe `validated` list, correctly skipping (and reporting) the deliberately-injected bad `Integer` entry instead of letting it silently corrupt the result or crash later.

## 6. Walkthrough

Execution starts in `main`, which calls `getLegacyDataSafely()`.

Inside `getLegacyDataSafely`, `getLegacyDataRaw()` is called first: it builds a raw `List`, adds `"first"`, `"second"`, and `42` (simulating a legacy data source that isn't reliably typed), and returns it. The caller receives this into `List<?> raw` — using a wildcard here (rather than another raw type) is a deliberate improvement, since it at least signals "we don't know the specific type" honestly, even though the underlying object came from an unchecked source.

`validated` starts as an empty `List<String>`. The loop `for (Object item : raw)` reads each element generically as `Object` (safe, since `List<?>` always allows reading as `Object`). For `"first"`: `item instanceof String s` is `true`, binding `s` to `"first"` and adding it to `validated`. For `"second"`: the same check succeeds, adding `"second"`.

For `42` (an `Integer`): `item instanceof String s` is `false` — the pattern match fails, so the `else` branch runs instead, printing `Skipping non-String legacy entry: 42 (Integer)`. Critically, this bad entry is never added to `validated`, so it can never later cause a `ClassCastException` or any other type-related corruption downstream.

`getLegacyDataSafely` returns `validated`, now containing exactly `["first", "second"]`. Back in `main`, the `for (String item : data)` loop iterates this clean, fully-validated list, printing `Valid entry: first` and `Valid entry: second` — the `Integer` never appears in this final output at all.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="legacy raw data flows through a wildcard reference, each element validated individually with instanceof before being accepted into a genuinely type-safe result list, with the mismatched entry rejected and reported">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">getLegacyDataRaw() -&gt; raw List: ["first", "second", 42] -&gt; captured as List&lt;?&gt; raw</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">"first": instanceof String -&gt; true -&gt; added to validated</text>
  <text x="20" y="77" fill="#6db33f" font-size="10">"second": instanceof String -&gt; true -&gt; added to validated</text>
  <text x="20" y="102" fill="#f85149" font-size="10">42 (Integer): instanceof String -&gt; false -&gt; skipped, reported, NOT added</text>
  <text x="20" y="132" fill="#8b949e" font-size="10">Result: validated = ["first", "second"] -- the bad entry never reaches the type-safe list at all.</text>
</svg>

## 7. Gotchas & takeaways

> `List` (raw) and `List<?>` (wildcard) look superficially similar but behave very differently — a raw type discards type checking entirely, for both reading and writing, while a wildcard preserves full compile-time safety for reading and only restricts writing (to `null`); always prefer the wildcard unless you have a specific, unavoidable reason to use a genuine raw type.

- A raw type is a generic type used with no type argument at all — it exists solely for backward compatibility with pre-Java-5 code, and using one in new code should be a deliberate, rare exception, not a habit.
- Compiler warnings like "unchecked call" or "unchecked conversion" almost always trace back to a raw type interacting with generic code somewhere — treat these warnings as real signals worth investigating, not routine noise to suppress reflexively.
- When you must interact with a raw-typed legacy API, confine the raw type's use to the smallest possible boundary (a single adapter method), converting to and validating against real generic types as early as possible.
- Prefer `List<?>` over a raw `List` whenever you genuinely mean "a list of an unknown type" — the wildcard version keeps compile-time read safety that a raw type simply discards.
- Validate individual elements (with `instanceof` pattern matching, as in the advanced example) when converting genuinely untrusted raw data into a type-safe collection, rather than trusting an unchecked cast to be correct for every element.
