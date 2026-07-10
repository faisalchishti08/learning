---
card: java
gi: 966
slug: switch-type-patterns
title: switch type patterns
---

## 1. What it is

Type patterns in `switch`, standardized in Java 21 (after a multi-release preview), extend `switch` to match on an expression's runtime *type*, not just constant values like enum constants, strings, or integers — `case String s ->`, `case Integer i ->`, `case null ->` are all valid case labels, each simultaneously checking the switched-on value's type and binding it to a correctly-typed variable, exactly like [`instanceof` pattern binding](0965-instanceof-pattern-binding.md), but as one branch among several in a single `switch`. This turns `switch` into a general-purpose, exhaustively-checkable dispatch mechanism over an object's runtime type — something previously requiring a chain of `if`/`else if` with `instanceof` checks — and, when combined with [sealed types](0961-sealed-permits-clauses.md), gains full compiler-verified exhaustiveness exactly as described in [exhaustiveness in switch](0964-exhaustiveness-in-switch.md).

## 2. Why & when

Type patterns in `switch` matter whenever you need to branch on an object's runtime type across three or more cases — at that point, a chain of `if`/`else if instanceof` checks becomes noticeably more verbose and repetitive than the equivalent `switch`, which also gains the crucial extra benefit of compiler-verified exhaustiveness when switching over a sealed hierarchy (something an `if`/`else if` chain simply cannot offer, since the compiler has no special mechanism to verify an `if`-chain covers every case). It's also the natural evolution of `switch` itself, which historically could only match on a narrow set of constant-like types (`byte`, `short`, `char`, `int` and their wrapper types, enums, and `String`) — type patterns generalize `switch` to match on *any* reference type, including a specific case for matching `null` directly in the `switch` itself (rather than requiring a separate `null` check beforehand, which older `switch` statements required to avoid an automatic `NullPointerException` on a null selector).

## 3. Core concept

```
Object obj = ...;

String result = switch (obj) {
    case null -> "it's null";                    // explicit null case -- no separate check needed
    case Integer i when i < 0 -> "negative int";  // guarded pattern (covered separately)
    case Integer i -> "int: " + i;
    case String s -> "string of length " + s.length();
    case int[] arr -> "int array of length " + arr.length;
    default -> "something else: " + obj;
};

// Compare to the PRE-type-pattern equivalent (verbose, no exhaustiveness guarantee):
String result2;
if (obj == null) result2 = "it's null";
else if (obj instanceof Integer i && i < 0) result2 = "negative int";
else if (obj instanceof Integer i) result2 = "int: " + i;
else if (obj instanceof String s) result2 = "string of length " + s.length();
else if (obj instanceof int[] arr) result2 = "int array of length " + arr.length;
else result2 = "something else: " + obj;
```

The `switch`-based version reads linearly, top to bottom, exactly like the `if`/`else if` chain it replaces — but gains exhaustiveness checking when the switched type is sealed, and a dedicated `case null` that older `switch` forms never supported directly.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A switch statement over an Object value with type-pattern case labels for null, Integer, String, and a default, each binding a correctly-typed variable" >
  <rect x="20" y="30" width="140" height="90" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="50" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">case null -&gt;</text>
  <text x="90" y="70" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">case Integer i -&gt;</text>
  <text x="90" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">case String s -&gt;</text>
  <text x="90" y="110" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">default -&gt;</text>

  <rect x="220" y="30" width="380" height="90" fill="#1c2430" stroke="#e6edf3"/>
  <text x="410" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Each case: type check + variable binding,</text>
  <text x="410" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">in ONE label -- evaluated top to bottom,</text>
  <text x="410" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">first match wins, exactly like ordinary switch</text>
  <text x="410" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">but generalized to ANY reference type</text>
</svg>

*Each case label combines a type check and variable binding, evaluated top to bottom exactly like ordinary switch, generalized to arbitrary reference types.*

## 5. Runnable example

Scenario: build a small generic value formatter using switch type patterns, evolving from a basic multi-type dispatch, to a realistic JSON-like value renderer over several distinct types including explicit null handling, to a more advanced case combining type patterns with sealed-type exhaustiveness for full compile-time safety.

### Level 1 — Basic

```java
public class SwitchTypePatternBasic {
    static String describe(Object obj) {
        return switch (obj) {
            case Integer i -> "an Integer: " + i;
            case String s -> "a String of length " + s.length();
            case Double d -> "a Double: " + d;
            default -> "something else";
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(42));
        System.out.println(describe("hello"));
        System.out.println(describe(3.14));
        System.out.println(describe(true));
    }
}
```

**How to run:** `java SwitchTypePatternBasic.java` (JDK 21+; type patterns in switch require Java 21+).

Expected output:
```
an Integer: 42
a String of length 5
a Double: 3.14
something else
```

Each case combines a type check and a variable binding — `Integer i`, `String s`, `Double d` — directly usable in that branch's body, evaluated top to bottom like an ordinary `switch`, with `default` catching anything not matched by an earlier case (here, `Boolean`).

### Level 2 — Intermediate

```java
public class SwitchTypePatternWithNull {
    static String renderJsonValue(Object value) {
        return switch (value) {
            case null -> "null";
            case String s -> "\"" + s.replace("\"", "\\\"") + "\"";
            case Integer i -> String.valueOf(i);
            case Double d -> String.valueOf(d);
            case Boolean b -> String.valueOf(b);
            default -> throw new IllegalArgumentException("unsupported type: " + value.getClass());
        };
    }

    public static void main(String[] args) {
        System.out.println(renderJsonValue("hello \"world\""));
        System.out.println(renderJsonValue(42));
        System.out.println(renderJsonValue(null));
        System.out.println(renderJsonValue(true));
    }
}
```

**How to run:** `java SwitchTypePatternWithNull.java` (JDK 21+).

Expected output:
```
"hello \"world\""
42
null
true
```

The real-world concern added: `case null ->` handles a null input directly within the `switch` itself — before Java 21, a `switch` on a reference-typed selector would throw `NullPointerException` immediately if the selector were `null`, requiring a separate check *before* the switch even started; combining `null` handling with the other type-based cases in one place makes this JSON-value-rendering logic read as a single, complete, linear specification of every case it needs to handle.

### Level 3 — Advanced

```java
public class SwitchTypePatternExhaustive {
    sealed interface JsonValue permits JsonString, JsonNumber, JsonBool, JsonNull {}
    record JsonString(String value) implements JsonValue {}
    record JsonNumber(double value) implements JsonValue {}
    record JsonBool(boolean value) implements JsonValue {}
    record JsonNull() implements JsonValue {}

    static String render(JsonValue value) {
        return switch (value) {
            case JsonString(String s) -> "\"" + s + "\"";
            case JsonNumber(double n) -> String.valueOf(n);
            case JsonBool(boolean b) -> String.valueOf(b);
            case JsonNull() -> "null";
            // EXHAUSTIVE over JsonValue's sealed hierarchy -- no default needed at all
        };
    }

    public static void main(String[] args) {
        System.out.println(render(new JsonString("hello")));
        System.out.println(render(new JsonNumber(3.14)));
        System.out.println(render(new JsonBool(true)));
        System.out.println(render(new JsonNull()));
    }
}
```

**How to run:** `java SwitchTypePatternExhaustive.java` (JDK 21+).

Expected output:
```
"hello"
3.14
true
null
```

The production-flavored hard case: modeling the possible JSON value kinds as a sealed hierarchy of records (rather than switching over `Object` with a fallback `default`) lets the compiler verify `render`'s `switch` is *fully exhaustive* — every possible `JsonValue` variant is provably handled, with no `default` branch at all, and no risk of a forgotten case silently falling through, exactly the guarantee explored in depth in [exhaustiveness in switch](0964-exhaustiveness-in-switch.md); this is a meaningfully stronger correctness guarantee than the `Object`-based version from Level 2, which could only fail at runtime (via its thrown exception) for an unsupported type, not at compile time.

## 6. Walkthrough

Tracing `render(new JsonNumber(3.14))` end to end from `SwitchTypePatternExhaustive.main`:

1. `render` is called with a `JsonNumber` instance wrapping `3.14`, statically typed as the sealed interface `JsonValue` at the parameter.
2. The `switch`'s case labels are checked in order: `case JsonString(String s)` attempts to match the value against `JsonString`'s shape — since the actual object is a `JsonNumber`, not a `JsonString`, this case fails to match, and the `switch` proceeds to the next label.
3. `case JsonNumber(double n)` is checked next — since the actual object genuinely is a `JsonNumber`, this pattern matches, and simultaneously deconstructs it, binding `n` to `3.14` (the record's single component).
4. The matched case's body, `String.valueOf(n)`, executes with `n` already bound — this converts the `double` value `3.14` to its string representation, `"3.14"`.
5. This value is returned from the `switch` expression, and back in `main`, `System.out.println` prints it directly: `3.14`.
6. Note that the compiler was able to verify, entirely at compile time, that this `switch` handles every one of `JsonValue`'s four sealed variants (`JsonString`, `JsonNumber`, `JsonBool`, `JsonNull`) — meaning it was mathematically certain, before the program ever ran, that no `JsonValue` value could ever reach this `switch` and fall through unhandled; this is the direct payoff of using a sealed hierarchy of records rather than switching over the unconstrained `Object` type from the earlier, less strictly-checked example.

## 7. Gotchas & takeaways

> **Gotcha:** case labels in a type-pattern `switch` are still checked top to bottom, and — unlike matching on constant values, where case order doesn't matter for correctness — pattern-based cases *can* have order-dependent behavior if one pattern's type is a supertype of another's (for instance, `case Number n` appearing before `case Integer i` would always match first for any `Integer` value, silently making the `Integer` case unreachable); the compiler does flag an unreachable case like this as a compile error, but it's worth understanding *why* order matters here, unlike with ordinary constant-based switch cases.

- Type patterns in `switch` (Java 21+) let each case label check an object's runtime type and bind a correctly-typed variable simultaneously, generalizing `switch` from matching only constant-like values to matching arbitrary reference types.
- `case null ->` handles a null selector directly within the `switch`, avoiding the automatic `NullPointerException` a `switch` on a reference type would otherwise throw immediately for a null input.
- Combined with a sealed type as the switched-on type, a type-pattern `switch` can be verified fully exhaustive by the compiler, with no `default` branch needed at all — a meaningfully stronger guarantee than an equivalent `switch` over an unconstrained type like `Object`, which can only fail at runtime for an unhandled case.
- Case order matters for pattern-based cases in a way it doesn't for constant-based ones — a broader supertype pattern appearing before a narrower subtype pattern can make the narrower case unreachable, which the compiler will flag as an error.
- This feature builds directly on [`instanceof` pattern binding](0965-instanceof-pattern-binding.md)'s mechanics, generalized to a multi-branch context, and pairs naturally with [record patterns / deconstruction](0960-record-patterns-deconstruction.md) for cases that also need to extract a matched record's component values.
- See [exhaustiveness in switch](0964-exhaustiveness-in-switch.md) for the precise rules governing when the compiler can verify a type-pattern switch's completeness, and [guarded patterns (when)](0967-guarded-patterns-when.md) for adding conditional refinement to an individual case beyond just its type.
