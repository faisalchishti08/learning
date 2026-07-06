---
card: java
gi: 338
slug: modifier-inspection
title: Modifier inspection
---

## 1. What it is

Every reflective member — a `Class`, `Field`, `Method`, or `Constructor` — exposes `getModifiers()`, which returns an `int` whose individual bits encode which keyword modifiers (`public`, `private`, `static`, `final`, `abstract`, and others) were used in its declaration. The `java.lang.reflect.Modifier` class provides static helper methods (`Modifier.isStatic(mods)`, `Modifier.isPublic(mods)`, etc.) to decode that bitmask into simple boolean checks, so reflective code can ask "is this static?" or "is this final?" without doing raw bit manipulation itself.

```java
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

public class ModifierDemo {
    static class Config { public static final int MAX = 100; private String name; }

    public static void main(String[] args) throws Exception {
        Field maxField = Config.class.getDeclaredField("MAX");
        int mods = maxField.getModifiers();
        System.out.println("public? " + Modifier.isPublic(mods));
        System.out.println("static? " + Modifier.isStatic(mods));
        System.out.println("final? " + Modifier.isFinal(mods));
    }
}
```

`getModifiers()` returns the raw encoded bits, and each `Modifier.isX(mods)` call checks one specific bit — this is the standard, readable way to interpret modifiers rather than working with the integer directly.

## 2. Why & when

Generic reflective code frequently needs to treat members differently based on their modifiers — skipping `static` fields when copying instance state (as seen with field reflection), refusing to reflectively modify `final` fields, or filtering out non-`public` members when only public API surface should be considered. `Modifier` inspection is how that logic is expressed cleanly.

- **Filtering fields or methods by role** — separating instance state from class-level constants (`static`), or separating a public contract from internal implementation details (`public` vs. everything else).
- **Respecting immutability** — checking `Modifier.isFinal(field.getModifiers())` before attempting to reflectively set a field's value, since final fields have special (and sometimes unsupported) rules around reflective modification.
- **Building developer tools** — IDEs, documentation generators, and debuggers use modifier inspection to display a member's declared modifiers accurately, exactly as they appear in source.

Modifiers are stored as a single `int` bitmask (each modifier is one bit), which is compact and fast to check, but not self-describing — `Modifier.toString(mods)` conveniently renders the whole set of modifiers as source-like text (e.g., `"public static final"`), which is often more useful for display than checking each bit individually.

## 3. Core concept

```java
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

public class ModifierCore {
    static class Example {
        public static final int CONST = 1;
        private int instanceField;
        protected transient long cache;
    }

    public static void main(String[] args) throws Exception {
        for (Field field : Example.class.getDeclaredFields()) {
            int mods = field.getModifiers();
            System.out.println(field.getName() + ": " + Modifier.toString(mods));
        }
    }
}
```

**How to run:** `java ModifierCore.java`

`Modifier.toString(mods)` renders the full modifier set as a readable string in the same order Java source uses (e.g., `"public static final"`), which is far more convenient than calling every individual `isX` check just to build a display string.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="getModifiers returns a bitmask; each modifier keyword corresponds to one bit, decoded via Modifier.isX helper methods">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="200" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">field.getModifiers()</text>

  <text x="250" y="52" fill="#8b949e" font-size="12">→ int bitmask</text>

  <rect x="20" y="85" width="530" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="285" y="102" fill="#6db33f" font-size="10" text-anchor="middle">Modifier.isPublic / isStatic / isFinal / isPrivate / isAbstract ...</text>
  <text x="285" y="117" fill="#8b949e" font-size="9" text-anchor="middle">each checks one specific bit of the mask</text>
</svg>

## 5. Runnable example

Scenario: a small reflective "public API summary" tool, evolved from listing all fields unconditionally, into one filtering to public-only fields, into a production-style summarizer that separates constants, static state, and instance state into distinct groups using modifier checks.

### Level 1 — Basic

```java
import java.lang.reflect.Field;

public class ApiSummaryBasic {
    static class Config {
        public static final int MAX = 100;
        public String name;
        private int internalCounter;
    }

    public static void main(String[] args) {
        for (Field field : Config.class.getDeclaredFields()) {
            System.out.println(field.getName()); // no filtering by modifier at all
        }
    }
}
```

**How to run:** `java ApiSummaryBasic.java`

This lists every field regardless of visibility, mixing internal implementation details (`internalCounter`) in with genuinely public API — not useful yet as an "API summary" since it doesn't distinguish public from private at all.

### Level 2 — Intermediate

```java
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

public class ApiSummaryIntermediate {
    static class Config {
        public static final int MAX = 100;
        public String name;
        private int internalCounter;
    }

    public static void main(String[] args) {
        for (Field field : Config.class.getDeclaredFields()) {
            if (Modifier.isPublic(field.getModifiers())) {
                System.out.println(field.getName() + " : " + field.getType().getSimpleName());
            }
        }
    }
}
```

**How to run:** `java ApiSummaryIntermediate.java`

Filtering with `Modifier.isPublic(field.getModifiers())` correctly excludes `internalCounter` from the summary, leaving only `MAX` and `name` — a real improvement, but constants (`static final`) and mutable public fields are still lumped together undifferentiated.

### Level 3 — Advanced

```java
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;

public class ApiSummaryAdvanced {
    static class Config {
        public static final int MAX = 100;
        public static int sharedCounter;
        public String name;
        private int internalCounter;
    }

    public static void main(String[] args) throws Exception {
        List<String> constants = new ArrayList<>();
        List<String> staticState = new ArrayList<>();
        List<String> instanceState = new ArrayList<>();

        for (Field field : Config.class.getDeclaredFields()) {
            int mods = field.getModifiers();
            if (!Modifier.isPublic(mods)) continue; // skip non-public entirely

            String entry = field.getName() + " : " + field.getType().getSimpleName();
            if (Modifier.isStatic(mods) && Modifier.isFinal(mods)) {
                constants.add(entry);
            } else if (Modifier.isStatic(mods)) {
                staticState.add(entry);
            } else {
                instanceState.add(entry);
            }
        }

        System.out.println("Constants: " + constants);
        System.out.println("Static state: " + staticState);
        System.out.println("Instance state: " + instanceState);
    }
}
```

**How to run:** `java ApiSummaryAdvanced.java`

By checking `Modifier.isStatic` and `Modifier.isFinal` together, public members are now sorted into three meaningfully distinct categories — immutable constants, mutable shared (`static`) state, and per-instance state — which is far more useful for genuinely summarizing a class's public API surface than a flat list.

## 6. Walkthrough

Execution starts in `main`, which initializes three empty lists (`constants`, `staticState`, `instanceState`) and then iterates `Config.class.getDeclaredFields()`, which returns all four declared fields: `MAX`, `sharedCounter`, `name`, `internalCounter`.

For `MAX`: `field.getModifiers()` encodes `public static final`. `Modifier.isPublic(mods)` is `true`, so it isn't skipped. `Modifier.isStatic(mods) && Modifier.isFinal(mods)` is `true`, so `"MAX : int"` is added to `constants`.

For `sharedCounter`: modifiers encode `public static` (no `final`). `isPublic` is `true`. The constants check (`isStatic && isFinal`) is `false` because `isFinal` is `false`; the `else if (Modifier.isStatic(mods))` branch is `true`, so `"sharedCounter : int"` is added to `staticState`.

For `name`: modifiers encode just `public`. `isPublic` is `true`; neither the constants nor static-state condition matches (not `static` at all), so it falls to the final `else`, adding `"name : String"` to `instanceState`.

For `internalCounter`: modifiers encode `private`. `Modifier.isPublic(mods)` is `false`, so the `continue` statement skips this field entirely — it never reaches any of the three lists.

After the loop, `main` prints all three lists: `Constants: [MAX : int]`, `Static state: [sharedCounter : int]`, `Instance state: [name : String]` — `internalCounter` appears nowhere in the output, exactly as intended for a public-API-only summary.

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each field's modifiers are checked for public first, then sorted into constants, static state, or instance state based on static and final bits">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">MAX (public static final)      -&gt; public? yes -&gt; static+final -&gt; Constants</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">sharedCounter (public static)   -&gt; public? yes -&gt; static only  -&gt; Static state</text>
  <text x="20" y="80" fill="#79c0ff" font-size="10">name (public)                   -&gt; public? yes -&gt; neither      -&gt; Instance state</text>
  <text x="20" y="105" fill="#f85149" font-size="10">internalCounter (private)       -&gt; public? no  -&gt; skipped entirely (continue)</text>
</svg>

## 7. Gotchas & takeaways

> Interface fields are implicitly `public static final`, even without those keywords written in source — reflective code that assumes a bare-looking field declaration means "just a regular field" will be surprised when scanning an interface's constants.

- `getModifiers()` returns a raw `int` bitmask; always decode it via `Modifier.isX(mods)` methods rather than inspecting bits manually.
- `Modifier.toString(mods)` renders the full modifier set as readable, source-like text — convenient for display or logging without checking each modifier individually.
- Combine multiple `Modifier.isX` checks (like `isStatic` and `isFinal` together) to distinguish meaningfully different categories, such as constants vs. mutable static state.
- Modifiers apply uniformly across `Class`, `Field`, `Method`, and `Constructor` reflection objects — the same `Modifier` helper methods work on all of them.
- Remember that access-level filtering (`isPublic`) and mutability filtering (`isFinal`) are independent checks — a field can be `public` and mutable, `public` and constant, or not `public` at all, and generic reflective tooling should usually check both dimensions explicitly.
