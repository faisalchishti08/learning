---
card: java
gi: 970
slug: unnamed-patterns
title: Unnamed patterns (_)
---

## 1. What it is

An unnamed pattern, standardized as a final feature in Java 21 (via JEP 456), lets you use a single underscore, `_`, in place of a variable name anywhere a pattern would otherwise bind one — in a record pattern's component position (`Point(int x, _)` when you only care about `x`), as a lambda parameter you never reference, or as a catch block's exception variable when you only care that *something* was thrown, not what. The underscore is not a real identifier — you cannot refer to `_` anywhere in the surrounding code — it exists purely to signal, both to the compiler and to a human reader, "this value exists structurally and must be matched or received here, but nothing further in this code needs to reference it by name."

## 2. Why & when

Unnamed patterns solve a small but frequent readability and correctness problem: prior to this feature, a component or parameter you didn't care about still needed *some* name, and that name either became noise (a variable called `unused` or `ignored`, cluttering the pattern) or, worse, could accidentally shadow an outer variable of the same name, or simply invite an unused-variable warning from tooling that doesn't understand the value is deliberately being discarded. Reach for `_` specifically whenever a record pattern's component, a lambda's parameter, or a catch block's exception genuinely isn't needed by the code that follows — it communicates clear, deliberate intent ("I know this value exists, I'm choosing not to use it") rather than leaving a reader to wonder whether a named-but-unused variable was simply forgotten or is dead code left over from an earlier edit.

## 3. Core concept

```
record Point(int x, int y) {}

// Only care about x -- the y component is matched (its presence/shape is still
// checked structurally) but not bound to any usable name:
if (obj instanceof Point(int x, _)) {
    System.out.println("x is: " + x);
}

// Lambda parameter never used in the body:
list.forEach(_ -> counter.incrementAndGet());

// Catch block where only the FACT that something was thrown matters, not its details:
try {
    riskyOperation();
} catch (Exception _) {
    System.out.println("something went wrong -- falling back to default");
}
```

`_` is a reserved marker, not an identifier — every one of these positions still requires *some* value to be present and matched structurally (the component's type is still checked, the lambda parameter's slot is still filled, the exception is still caught), but the underscore explicitly signals that nothing downstream needs to reference that particular value by name.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A record pattern binding one component to a named variable while the other component uses the unnamed pattern underscore, signaling it is matched but deliberately not referenced" >
  <rect x="20" y="30" width="280" height="60" fill="#1c2430" stroke="#e6edf3"/>
  <text x="160" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Point(int x, _)</text>
  <text x="160" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">shape still checked -- y NOT bound to a name</text>

  <rect x="340" y="30" width="120" height="60" fill="#1c2430" stroke="#6db33f"/>
  <text x="400" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">x usable</text>
  <text x="400" y="70" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">named, bound</text>

  <rect x="480" y="30" width="140" height="60" fill="#1c2430" stroke="#f0883e"/>
  <text x="550" y="55" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">y unreachable</text>
  <text x="550" y="70" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">"_" cannot be referenced</text>

  <text x="320" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">The underscore signals deliberate intent to discard, distinct from an unused-but-named variable</text>
</svg>

*The underscore marks a value as structurally required but deliberately unreferenced, distinct from simply giving it an unused name.*

## 5. Runnable example

Scenario: process a stream of sensor events, evolving from a basic record pattern ignoring an unneeded component, to a realistic event-counting scenario using an unnamed lambda parameter, to a more advanced case combining unnamed patterns across nested record deconstruction and a catch block together.

### Level 1 — Basic

```java
public class UnnamedPatternBasic {
    record Point(int x, int y) {}

    static String xAxisLabel(Object obj) {
        if (obj instanceof Point(int x, _)) { // y is matched structurally, never named
            return "x = " + x;
        }
        return "not a point";
    }

    public static void main(String[] args) {
        System.out.println(xAxisLabel(new Point(7, 99)));
        System.out.println(xAxisLabel("hello"));
    }
}
```

**How to run:** `java UnnamedPatternBasic.java` (JDK 21+; unnamed patterns are standardized in Java 21).

Expected output:
```
x = 7
not a point
```

The `Point` pattern's second component uses `_` since this method only ever needs `x` — the `y` component's *presence* is still checked as part of confirming `obj` is genuinely a `Point`, but no variable is created for it, making clear to any reader that `y` is deliberately irrelevant here, not simply forgotten.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.atomic.*;

public class UnnamedPatternLambda {
    public static void main(String[] args) {
        List<String> events = List.of("click", "click", "scroll", "click", "scroll");
        AtomicInteger totalEvents = new AtomicInteger(0);

        events.forEach(_ -> totalEvents.incrementAndGet()); // the event value itself is irrelevant here

        System.out.println("total events processed: " + totalEvents.get());
    }
}
```

**How to run:** `java UnnamedPatternLambda.java` (JDK 21+).

Expected output:
```
total events processed: 5
```

The real-world concern added: `forEach`'s lambda only needs to increment a counter once per element — the actual event string is never used inside the lambda body, so `_` communicates directly that this is a deliberate, counting-only operation, rather than leaving a named-but-ignored parameter (like `event ->`) that a reader might reasonably (but incorrectly) assume is used somewhere in the body.

### Level 3 — Advanced

```java
import java.util.*;

public class UnnamedPatternCombined {
    record Reading(String sensorId, double value, long timestamp) {}

    static double parseAndValidate(String raw) {
        try {
            String[] parts = raw.split(",");
            return Double.parseDouble(parts[1]);
        } catch (NumberFormatException _) {
            // We only care THAT parsing failed, not the specific exception details --
            // falling back to a safe default value.
            return 0.0;
        }
    }

    static String describe(Object obj) {
        if (obj instanceof Reading(_, double value, _)) {
            // sensorId and timestamp are both irrelevant to this specific description --
            // only the reading's value matters here.
            return value > 100.0 ? "high reading: " + value : "normal reading: " + value;
        }
        return "not a reading";
    }

    public static void main(String[] args) {
        System.out.println("parsed: " + parseAndValidate("sensor-1,42.5,1000"));
        System.out.println("parsed (invalid): " + parseAndValidate("sensor-1,not-a-number,1000"));
        System.out.println(describe(new Reading("sensor-2", 150.0, 2000L)));
    }
}
```

**How to run:** `java UnnamedPatternCombined.java` (JDK 21+).

Expected output:
```
parsed: 42.5
parsed (invalid): 0.0
high reading: 150.0
```

The production-flavored hard case: `Reading(_, double value, _)` uses unnamed patterns for *two* of the record's three components (`sensorId` and `timestamp`), since `describe`'s logic genuinely depends only on `value` — combined with `catch (NumberFormatException _)`, which discards a caught exception's details entirely since only the fact that parsing failed matters for the fallback logic, this demonstrates that unnamed patterns compose naturally across genuinely different contexts (record deconstruction, catch blocks) within the same program, each communicating the identical underlying intent: "this value is structurally required here, but deliberately unused."

## 6. Walkthrough

Tracing `describe(new Reading("sensor-2", 150.0, 2000L))` end to end from `UnnamedPatternCombined.main`:

1. `describe` is called with a `Reading` instance whose three components are `sensorId = "sensor-2"`, `value = 150.0`, and `timestamp = 2000L`.
2. The pattern `Reading(_, double value, _)` is checked against this object: first, is it genuinely a `Reading`? Yes — the pattern then proceeds to check each component position; the first component (`sensorId`) matches the underscore `_`, meaning its presence and type are structurally confirmed as part of matching `Reading`'s overall shape, but no local variable is created for it.
3. The second component position, `double value`, binds the actual `value` field (`150.0`) to a genuine, usable local variable named `value` — this is the one component this method actually needs.
4. The third component position, again `_`, matches `timestamp` (`2000L`) structurally but, exactly like the first, creates no accessible variable for it.
5. With the pattern successfully matched and `value` bound to `150.0`, the `if` block's body executes: the ternary `value > 100.0 ? "high reading: " + value : "normal reading: " + value` evaluates `150.0 > 100.0`, which is `true`, so the string `"high reading: 150.0"` is constructed and returned.
6. Back in `main`, this returned string is printed directly — the entire process demonstrates that `sensorId` and `timestamp`, while genuinely present in the matched object and necessarily accounted for structurally by the pattern (since `Reading` has exactly three components, and the pattern must account for all three positions), were never given usable names, precisely because `describe`'s logic has no need to reference either of them — making that omission a deliberate, visible design choice rather than an accidental unused variable a reader might otherwise question.

## 7. Gotchas & takeaways

> **Gotcha:** `_` is a reserved token specifically for use as an unnamed pattern or unnamed variable/parameter — it is not simply a legal, ordinary identifier you can also use as a normal, referenceable variable name anymore in modern Java; code from before Java 21 that used a bare `_` as an actual variable name (legal in older Java versions, though discouraged even then) will fail to compile under newer language levels, since `_` is now a reserved, non-identifier token in this specific context.

- Unnamed patterns use `_` in place of a variable name in a record pattern's component position, a lambda parameter, or a catch block's exception variable, whenever that value is structurally required but genuinely not needed by name in the following code.
- The underscore is not an identifier — you cannot reference `_` anywhere afterward — it exists purely to communicate deliberate intent to discard a value, distinct from giving it an unused, potentially-confusing name.
- Using `_` avoids both unused-variable clutter and the risk of an unused-but-named variable accidentally shadowing an outer variable of the same name.
- Unnamed patterns compose naturally across contexts — a record pattern can use `_` for several of its components simultaneously, and the same underscore convention applies identically in catch blocks and lambda parameters.
- Because `_` is now a reserved token for this purpose, any older code that happened to use a literal `_` as an ordinary variable name will no longer compile under a modern Java language level.
- See [record deconstruction patterns](0968-record-deconstruction-patterns.md) and [nested patterns](0969-nested-patterns.md) for the broader record-pattern mechanics unnamed patterns are frequently used alongside.
