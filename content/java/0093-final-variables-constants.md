---
card: java
gi: 93
slug: final-variables-constants
title: final variables (constants)
---

## 1. What it is

The `final` keyword on a variable means the variable can be assigned exactly once — it cannot be reassigned after its first assignment. For primitive types `final` makes the value immutable; for reference types `final` makes the reference immutable (it always points to the same object), but the object itself may still be mutated.

```java
final int    MAX_SIZE   = 100;       // constant — cannot change value
final String APP_NAME   = "MyApp";   // constant reference — always "MyApp"
final List<String> ITEMS = new ArrayList<>(); // reference is final, list is not!
ITEMS.add("x");                      // OK — mutates the list (reference unchanged)
// ITEMS = new ArrayList<>();        // compile error — cannot reassign
```

`static final` fields are Java's conventional constants, named in UPPER_SNAKE_CASE.

## 2. Why & when

Use `final` to:
- **Document intent** — `final` tells readers "this value will not change after initialisation."
- **Enable lambda/inner-class capture** — only effectively-final locals can be captured.
- **Prevent bugs** — the compiler catches accidental reassignment at compile time.
- **Support safe publication** — a `final` field is guaranteed to be fully initialised before it is visible to other threads (Java Memory Model guarantee), removing the need for synchronisation on read.

`static final` constants replace magic numbers throughout the codebase with a single named definition that is easy to change in one place.

## 3. Core concept

```java
import java.util.*;

public class FinalVariables {

    // ---- static final constants ----
    static final double  PI          = 3.141592653589793;
    static final int     MAX_RETRIES = 3;
    static final String  VERSION     = "1.0.0";

    // ---- final instance field ---- must be assigned in every constructor
    final String id;
    final int    priority;

    FinalVariables(String id, int priority) {
        this.id       = id;
        this.priority = priority;
        // id and priority cannot be changed after this constructor returns
    }

    void demonstrate() {
        // ---- final local variable ----
        final int limit = 5;
        // limit = 10;   // compile error

        // ---- effectively final (no explicit final keyword) ----
        int count = 0;   // not reassigned after this — effectively final
        Runnable r = () -> System.out.println("count: " + count);  // capture OK
        r.run();

        // ---- final reference — mutable object ----
        final List<String> items = new ArrayList<>();
        items.add("apple");   // OK — mutating the object
        items.add("bread");   // OK
        // items = new ArrayList<>();  // compile error — cannot reassign reference

        // ---- Compile-time constant folding ----
        final int A = 10;
        final int B = 20;
        int sum = A + B;   // folded to 30 by the compiler
        System.out.println(sum);  // 30

        // ---- final in switch ----
        final String colour = "red";
        switch (colour) {
            case "red"  -> System.out.println("stop");
            case "green"-> System.out.println("go");
            default     -> System.out.println("caution");
        }
    }

    public static void main(String[] args) {
        var obj = new FinalVariables("ID-001", 5);
        obj.demonstrate();
        System.out.println("id=" + obj.id + "  priority=" + obj.priority);
        // obj.id = "x";   // compile error
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="final keyword: three cases — final primitive (value locked), final reference (pointer locked, object mutable), static final constant (class-level, compile-time constant)">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>

  <!-- final primitive -->
  <rect x="16" y="18" width="200" height="133" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="116" y="36" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">final int MAX = 10</text>
  <text x="116" y="50" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">primitive — value locked</text>
  <line x1="26" y1="56" x2="206" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <rect x="60" y="66" width="110" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="84" fill="#6db33f" font-size="14" font-weight="bold" text-anchor="middle" font-family="monospace">10</text>
  <text x="115" y="104" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">MAX = 20; // error</text>
  <text x="115" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">value cannot change</text>
  <text x="115" y="135" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">compile-time constant</text>
  <text x="115" y="146" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">if static final + literal</text>

  <!-- final reference -->
  <rect x="228" y="18" width="218" height="133" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="337" y="36" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">final List&lt;T&gt; ITEMS</text>
  <text x="337" y="50" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reference locked, object mutable</text>
  <line x1="238" y1="56" x2="436" y2="56" stroke="#8b949e" stroke-width="0.5"/>
  <!-- pointer box -->
  <rect x="248" y="66" width="72" height="28" rx="3" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="284" y="84" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">ref →</text>
  <!-- heap list -->
  <rect x="330" y="66" width="96" height="28" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="378" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">["a","b","c"]</text>
  <line x1="320" y1="80" x2="330" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="337" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">ITEMS.add("x") OK</text>
  <text x="337" y="125" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">ITEMS = new ..  error</text>
  <text x="337" y="139" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pointer is locked, not content</text>

  <!-- static final -->
  <rect x="458" y="18" width="226" height="133" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="571" y="36" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">static final — constants</text>
  <line x1="468" y1="42" x2="674" y2="42" stroke="#8b949e" stroke-width="0.5"/>
  <text x="468" y="57" fill="#e6edf3" font-size="7.5" font-family="monospace">static final double PI</text>
  <text x="468" y="70" fill="#e6edf3" font-size="7.5" font-family="monospace">static final int MAX</text>
  <text x="468" y="85" fill="#8b949e" font-size="7.5" font-family="monospace">naming: UPPER_SNAKE_CASE</text>
  <text x="468" y="100" fill="#8b949e" font-size="7.5" font-family="monospace">access: ClassName.CONST</text>
  <text x="468" y="115" fill="#6db33f" font-size="7.5" font-family="monospace">JMM: safe publication</text>
  <text x="468" y="130" fill="#8b949e" font-size="7.5" font-family="monospace">effectively final: no explicit</text>
  <text x="468" y="143" fill="#8b949e" font-size="7.5" font-family="monospace">final but never reassigned</text>
</svg>

`final` on a primitive locks the value; `final` on a reference locks the pointer but not the object it points to; `static final` is the Java constant convention.

## 5. Runnable example

Scenario: a configuration manager for a deployment pipeline — pipeline-wide constants are `static final`, per-stage settings are `final` instance fields, and effectively-final locals drive lambda transformations. The scenario grows from basic constants, to final fields in a config record, to a policy checker that uses final locals captured by lambdas.

### Level 1 — Basic

```java
public class FinalBasic {

    static final String  PIPELINE_NAME = "CI/CD";
    static final int     MAX_STAGES    = 10;
    static final double  TIMEOUT_SEC   = 30.0;

    public static void main(String[] args) {
        System.out.printf("Pipeline : %s%n", PIPELINE_NAME);
        System.out.printf("Max stages: %d%n", MAX_STAGES);
        System.out.printf("Timeout  : %.0f s%n", TIMEOUT_SEC);

        // final local
        final int stageCount = 4;
        System.out.println("Running " + stageCount + " stages");

        // Compile-time constant folding (static final ints + final locals)
        final int BASE  = 1_000;
        final int LIMIT = BASE * MAX_STAGES;
        System.out.println("Max tasks: " + LIMIT);   // 10000, folded at compile time

        // final reference — list is still mutable
        final var stages = new java.util.ArrayList<String>();
        stages.add("build");
        stages.add("test");
        stages.add("deploy");
        System.out.println("Stages: " + stages);
        // stages = new java.util.ArrayList<>();  // would be compile error
    }
}
```

**How to run:** `java FinalBasic.java`

`PIPELINE_NAME`, `MAX_STAGES`, and `TIMEOUT_SEC` are `static final` — they are compile-time constants (when the type is primitive or `String` with a literal initializer) and are inlined by the compiler at each use site. `BASE * MAX_STAGES` is folded at compile time because both are compile-time constants. `final var stages` prevents reassigning `stages` to a new list, but `stages.add(...)` is perfectly legal because it mutates the existing object.

### Level 2 — Intermediate

Same pipeline: add a stage configuration `record` with `final` semantics, demonstrate that `final` fields must be assigned in the constructor, and use `final` locals to capture immutable policy decisions.

```java
import java.util.*;

public class FinalIntermediate {

    record StageConfig(String name, boolean required, int timeoutSec) {
        // Records have implicit final fields — all component fields are final
        static final int DEFAULT_TIMEOUT = 30;

        StageConfig(String name, boolean required) {
            this(name, required, DEFAULT_TIMEOUT);   // delegate to canonical constructor
        }
    }

    static final List<StageConfig> DEFAULT_STAGES = List.of(
        new StageConfig("compile",   true,  60),
        new StageConfig("test",      true,  120),
        new StageConfig("package",   true,  30),
        new StageConfig("integrate", false, 90)
    );

    public static void main(String[] args) {
        System.out.printf("%-12s  %-8s  %s%n", "Stage", "Required", "Timeout");
        System.out.println("-".repeat(34));

        for (StageConfig cfg : DEFAULT_STAGES) {
            // cfg.name() is final — cannot change
            System.out.printf("%-12s  %-8b  %d s%n",
                cfg.name(), cfg.required(), cfg.timeoutSec());
        }

        // final local: policy computed once, used in stream
        final boolean strictMode = true;

        long requiredCount = DEFAULT_STAGES.stream()
            .filter(s -> strictMode || s.required())   // captures strictMode
            .count();

        System.out.println("\nWith strictMode=" + strictMode
            + ": " + requiredCount + " stages will run");
    }
}
```

**How to run:** `java FinalIntermediate.java`

`record StageConfig(...)` makes all component fields implicitly `final` — you cannot change `cfg.name()` or `cfg.required()` after construction. `List.of(...)` returns an unmodifiable list, and `DEFAULT_STAGES` is `static final` — neither the reference nor the list contents can change. `final boolean strictMode` is captured by the lambda because it is effectively final; even without the `final` keyword, not reassigning `strictMode` anywhere would have the same effect.

### Level 3 — Advanced

Same pipeline: a policy engine that composes rules from `static final` constants and `final` locals, uses effectively-final captured state in a stream pipeline, and verifies the Java Memory Model guarantee for `final` fields.

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class FinalAdvanced {

    // Compile-time constants — inlined at every use site
    static final int    MAX_RETRIES       = 3;
    static final double SLA_SECONDS       = 120.0;
    static final String REQUIRED_STAGE    = "test";

    record Policy(String name, Predicate<String> check) {}

    static List<Policy> buildPolicies(double customSla, boolean allowSkip) {
        // Final locals — captured by lambdas
        final double sla       = customSla > 0 ? customSla : SLA_SECONDS;
        final boolean skipOk   = allowSkip;

        return List.of(
            new Policy("sla-check",
                stage -> {
                    // 'sla' captured — effectively final
                    System.out.printf("  [sla-check] stage=%s  sla=%.0fs%n", stage, sla);
                    return true;  // in reality: check elapsed time
                }),
            new Policy("required-stage",
                stage -> {
                    boolean pass = skipOk || stage.equals(REQUIRED_STAGE);
                    System.out.printf("  [required]  stage=%-10s  skipOk=%-5b  pass=%b%n",
                        stage, skipOk, pass);
                    return pass;
                })
        );
    }

    public static void main(String[] args) {
        var stages = List.of("compile", "test", "package", "lint");
        var policies = buildPolicies(60.0, false);

        System.out.println("=== Policy evaluation ===");
        Map<String, Boolean> results = stages.stream()
            .collect(Collectors.toMap(
                stage -> stage,
                stage -> policies.stream().allMatch(p -> p.check().test(stage))
            ));

        System.out.println("\n=== Results ===");
        results.forEach((stage, pass) ->
            System.out.printf("  %-10s  %s%n", stage, pass ? "PASS" : "FAIL"));

        // final field Java Memory Model guarantee
        // A final field is guaranteed to be visible to all threads
        // after the constructor completes — no synchronisation needed for reads
        System.out.println("\nMAX_RETRIES (inlined constant): " + MAX_RETRIES);
    }
}
```

**How to run:** `java FinalAdvanced.java`

`sla` and `skipOk` are `final` locals inside `buildPolicies`. The lambdas in `List.of(new Policy(...))` capture both. Because `buildPolicies` returns the list, these lambdas outlive the method call — the captured values travel with the lambdas. `REQUIRED_STAGE` is a `static final String` constant — the compiler may inline `"test"` at every reference to `REQUIRED_STAGE`. The Java Memory Model guarantees that `final` instance fields are fully visible to any thread that reads the object after the constructor completes — meaning `final String id` in a record or class is safely published without locks.

## 6. Walkthrough

Execution trace through `FinalAdvanced.main` for stage `"lint"`:

**Policy evaluation.** For `stage = "lint"`, `policies.stream().allMatch(p -> p.check().test("lint"))` evaluates each policy in order.

**`sla-check` lambda.** `sla = 60.0` (captured final local from `buildPolicies`). Prints `[sla-check] stage=lint  sla=60s`. Returns `true`.

**`required-stage` lambda.** `skipOk = false` (captured final local). `stage.equals(REQUIRED_STAGE)` = `"lint".equals("test")` = `false`. `pass = false || false = false`. Returns `false`.

**`allMatch` result.** Because `required-stage` returned `false`, `allMatch` short-circuits and returns `false`. Entry `("lint", false)` is put in `results`.

**Output.** `lint → FAIL` because it is not the required stage and `skipOk` is `false`.

```
final local capture lifecycle:
  buildPolicies(60.0, false) called:
    final double sla     = 60.0
    final boolean skipOk = false
    two lambdas created, capturing sla and skipOk
    method returns List<Policy>  ← sla and skipOk live on inside the lambdas

  sla-check lambda invoked later:
    sla   = 60.0  (still captured)
    skipOk not captured by this lambda
```

## 7. Gotchas & takeaways

> **`final` on a reference type does not make the object immutable.** `final List<String> list = new ArrayList<>()` prevents `list = someOtherList`, but `list.add("x")` is perfectly legal. For deep immutability, use `List.of(...)`, `Collections.unmodifiableList`, records, or immutable value types.

> **A `final` instance field must be assigned in every constructor — exactly once.** If a class has two constructors and one of them does not assign a `final` field, the code will not compile. Use constructor chaining (`this(...)`) to delegate to a single canonical constructor that assigns all final fields.

- `final` on a variable prevents reassignment after the first assignment — for primitives this locks the value, for references it locks the pointer.
- `static final` fields are Java's constants; name them `UPPER_SNAKE_CASE` and initialise them with literals or constant expressions to get compile-time constant inlining.
- A `final` local variable can be captured by a lambda or anonymous inner class; a non-final variable that is never reassigned is "effectively final" and has the same capture rules.
- `final` instance fields are safely published to all threads after the constructor completes — no `volatile` or synchronisation needed for reads.
- `final` prevents reassignment, not mutation — use immutable data structures (records, `List.of`, etc.) for true immutability.
