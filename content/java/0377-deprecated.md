---
card: java
gi: 377
slug: deprecated
title: '@Deprecated'
---

## 1. What it is

`@Deprecated` is a built-in annotation you place on a class, method, field, or constructor to mark it as outdated — something that still works today, but that callers should stop using, typically because a better replacement exists or the old approach turned out to be unsafe or a design mistake. Using a `@Deprecated` element triggers a compiler warning (not an error — deprecated code still compiles and runs normally) at every call site, nudging callers toward the alternative without breaking existing code immediately.

## 2. Why & when

Libraries and APIs evolve. A method might turn out to have a confusing name, an unsafe default, or simply be superseded by a better-designed replacement — but other people's code already calls it, and removing it outright would break them without warning. `@Deprecated` offers a middle path: keep the old method working exactly as before, but visibly flag it so new code doesn't adopt it, and existing callers get a clear, actionable signal (a compiler warning) that they should migrate before a future version potentially removes it altogether.

You mark something `@Deprecated` when you're introducing a replacement and want to steer usage away from the old path over time — a classic example is `Date`'s many deprecated constructors and methods, superseded by `java.time` (`LocalDate`, `LocalDateTime`) in Java 8. As a caller, seeing `@Deprecated` (usually shown as strikethrough text in an IDE) is a signal to check the replacement's documentation and migrate when convenient, not necessarily an emergency.

## 3. Core concept

```java
public class DeprecatedDemo {
    static class LegacyGreeter {
        @Deprecated(since = "2.0", forRemoval = true) // marks this old, with metadata about it
        static String greetOld(String name) {
            return "Hi " + name;
        }

        static String greetNew(String name) { // the intended replacement
            return "Hello, " + name + "!";
        }
    }

    public static void main(String[] args) {
        System.out.println(LegacyGreeter.greetOld("Sam")); // compiles, but generates a warning
        System.out.println(LegacyGreeter.greetNew("Sam"));
    }
}
```

**How to run:** `javac DeprecatedDemo.java` then `java DeprecatedDemo`

Compiling this prints a warning like `warning: [deprecation] greetOld(String) in LegacyGreeter has been deprecated and marked for removal`, but the program still compiles and runs normally — both methods are called and both print their output. `since` and `forRemoval` are optional elements on `@Deprecated` that add extra metadata: which version introduced the deprecation, and whether the element is actually planned for future removal (versus just discouraged).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a deprecated method still compiles and runs normally, but every call site generates a compiler warning steering callers toward the replacement">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="50" fill="#f85149" font-size="10" text-anchor="middle">@Deprecated greetOld(name)</text>
  <text x="160" y="65" fill="#8b949e" font-size="9" text-anchor="middle">still works, but warns callers</text>

  <rect x="350" y="30" width="260" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="50" fill="#6db33f" font-size="10" text-anchor="middle">greetNew(name)</text>
  <text x="480" y="65" fill="#8b949e" font-size="9" text-anchor="middle">the intended replacement</text>

  <text x="20" y="110" fill="#e6edf3" font-size="10">Calling greetOld() compiles fine and runs normally -- only a warning is produced, no error, no crash.</text>
  <text x="20" y="130" fill="#8b949e" font-size="10">forRemoval=true signals the deprecated method may actually be deleted in a future version.</text>
</svg>

## 5. Runnable example

Scenario: a payment-processing helper migrating to a safer API, evolved from an old insecure method silently used everywhere, through marking it `@Deprecated` to surface every call site, to a version where `forRemoval = true` and a suppressed call site shows the full lifecycle of a deprecation.

### Level 1 — Basic

```java
public class PaymentLegacy {
    static boolean chargeCardUnsafe(String cardNumber, double amount) {
        System.out.println("Charging " + amount + " to card ending " +
                cardNumber.substring(cardNumber.length() - 4));
        return true;
    }

    public static void main(String[] args) {
        chargeCardUnsafe("4111111111111111", 49.99); // no warning -- looks perfectly normal
    }
}
```

**How to run:** `java PaymentLegacy.java`

Nothing here signals that `chargeCardUnsafe` might be a method callers should stop using — it looks identical to any other method, so there's no compiler-level nudge to migrate away from it even after a safer replacement exists.

### Level 2 — Intermediate

```java
public class PaymentDeprecating {
    @Deprecated(since = "2.0") // marks it, but doesn't yet claim it will be removed
    static boolean chargeCardUnsafe(String cardNumber, double amount) {
        System.out.println("Charging " + amount + " to card ending " +
                cardNumber.substring(cardNumber.length() - 4));
        return true;
    }

    static boolean chargeCardTokenized(String paymentToken, double amount) { // the new, safer path
        System.out.println("Charging " + amount + " via token " + paymentToken);
        return true;
    }

    public static void main(String[] args) {
        chargeCardUnsafe("4111111111111111", 49.99); // now generates a compiler warning
        chargeCardTokenized("tok_abc123", 49.99);    // no warning -- the intended path
    }
}
```

**How to run:** `javac PaymentDeprecating.java` (note the deprecation warning), then `java PaymentDeprecating`

Adding `@Deprecated(since = "2.0")` doesn't change runtime behaviour at all — both calls still execute and print exactly as before — but compiling now emits `warning: [deprecation] chargeCardUnsafe(...) in PaymentDeprecating has been deprecated`, giving every caller of the old method a visible, actionable signal for the first time.

### Level 3 — Advanced

```java
public class PaymentForRemoval {
    @Deprecated(since = "2.0", forRemoval = true) // stronger signal: this WILL be deleted
    static boolean chargeCardUnsafe(String cardNumber, double amount) {
        System.out.println("Charging " + amount + " to card ending " +
                cardNumber.substring(cardNumber.length() - 4));
        return true;
    }

    static boolean chargeCardTokenized(String paymentToken, double amount) {
        System.out.println("Charging " + amount + " via token " + paymentToken);
        return true;
    }

    @SuppressWarnings("deprecation") // an explicit, deliberate exception -- e.g. one remaining legacy caller
    static boolean legacyBridgeStillNeeded(String cardNumber, double amount) {
        return chargeCardUnsafe(cardNumber, amount); // suppressed -- team has acknowledged this one call site
    }

    public static void main(String[] args) {
        chargeCardTokenized("tok_abc123", 49.99);         // no warning
        legacyBridgeStillNeeded("4111111111111111", 9.99); // no warning here either, deliberately suppressed
    }
}
```

**How to run:** `javac PaymentForRemoval.java` then `java PaymentForRemoval`

`forRemoval = true` raises the severity of the deprecation, signalling a genuine future removal rather than just discouragement. `legacyBridgeStillNeeded` shows the realistic endgame of a migration: one deliberately-acknowledged call site is wrapped and marked `@SuppressWarnings("deprecation")` (see [[suppresswarnings]]), documenting "yes, we know this calls a deprecated method, and we've decided that's acceptable here for now" instead of the warning being silently ignored or, worse, accidentally left unaddressed.

## 6. Walkthrough

Execution starts in `main`. `chargeCardTokenized("tok_abc123", 49.99)` runs first: it prints `Charging 49.99 via token tok_abc123` and returns `true` — an ordinary method call with nothing deprecated involved.

`legacyBridgeStillNeeded("4111111111111111", 9.99)` runs next. Inside this method, `chargeCardUnsafe(cardNumber, amount)` is called — a call to the deprecated method. Normally, this call site would produce a compiler warning during compilation, but because `legacyBridgeStillNeeded` itself is annotated `@SuppressWarnings("deprecation")`, that specific warning is suppressed for every deprecated-method call inside this one method's body. Inside `chargeCardUnsafe`, `cardNumber.substring(cardNumber.length() - 4)` extracts the last four characters of the card number (`"1111"`), and the method prints `Charging 9.99 to card ending 1111`, then returns `true`. This return value propagates back up as `legacyBridgeStillNeeded`'s own return value.

The key point for understanding `@Deprecated`'s lifecycle: compiling this file produces **zero** deprecation warnings for the call inside `legacyBridgeStillNeeded` (because of the explicit suppression) but **would** produce a warning for any *other*, unsuppressed call to `chargeCardUnsafe` elsewhere in the codebase — the annotation's warning is per call site, not a one-time, whole-program flag.

Expected output:
```
Charging 49.99 via token tok_abc123
Charging 9.99 to card ending 1111
```

## 7. Gotchas & takeaways

> `@Deprecated` alone never stops code from compiling or running — it is purely advisory, a compiler warning at each call site. If you genuinely need to prevent a method from being used at all, remove it (a breaking change) or throw an exception from its body; deprecation is a migration signal, not an enforcement mechanism.

- `@Deprecated` marks a class, method, field, or constructor as discouraged, generating a compiler warning at every call site while leaving runtime behaviour completely unchanged.
- The `since` element documents which version introduced the deprecation; `forRemoval = true` signals a genuine planned future removal, as opposed to a softer "please stop using this" without a removal date.
- Pair `@Deprecated` code with the `@deprecated` Javadoc tag in the accompanying comment, explaining *why* it's deprecated and pointing to the specific replacement to use instead.
- `@SuppressWarnings("deprecation")` (see [[suppresswarnings]]) lets you deliberately and explicitly acknowledge a specific, intentional call to a deprecated method, rather than letting the warning go unaddressed or, worse, disabling deprecation warnings project-wide.
- A well-known example in the JDK itself: many of the original `java.util.Date` constructors and methods are deprecated in favour of the `java.time` API (`LocalDate`, `LocalDateTime`) introduced in Java 8.
