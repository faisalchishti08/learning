---
card: java
gi: 745
slug: exhaustiveness-checking-in-switch
title: Exhaustiveness checking in switch
---

## 1. What it is

**Exhaustiveness checking** is the compile-time guarantee that a `switch` expression over a [sealed type](0708-sealed-classes-interfaces-standardized.md) (or `enum`) covers **every** possible case — if it doesn't, the code simply fails to compile, with an error naming the specific subtype(s) left unhandled. It's the flip side of [pattern matching for switch](0742-pattern-matching-for-switch-standardized.md): the language lets you dispatch on type and structure, and in exchange the compiler can prove your dispatch logic has no gaps, because a `sealed` type's complete set of permitted subtypes is known and closed at compile time.

## 2. Why & when

An `if/else` chain checking types has no equivalent safety net — the compiler has no way to know what "all the possibilities" even are, so a forgotten branch just silently falls through to whatever the final `else` does (often nothing useful, or a runtime exception discovered much later). Exhaustiveness checking flips that: because `sealed` declares the complete, closed list of permitted subtypes up front, the compiler can enumerate them and cross-check every switch that dispatches over that type. This turns "did I handle every case?" from a code-review question into a build-time guarantee — and it turns **adding a new subtype** into a safety net for the future maintainer, too: the moment someone adds, say, `Triangle` to a sealed `Shape` hierarchy, every existing pattern-matching switch over `Shape` that lacks a `default` immediately fails to compile at every call site that needs updating, rather than silently miscategorizing triangles as some other shape at runtime.

## 3. Core concept

```java
sealed interface Shape permits Circle, Square {}
record Circle(double radius) implements Shape {}
record Square(double side) implements Shape {}

static double area(Shape shape) {
    return switch (shape) {
        case Circle c -> Math.PI * c.radius() * c.radius();
        case Square s -> s.side() * s.side();
        // compiles: Circle and Square are the only permitted subtypes, both handled
    };
}
```

If a third record, say `Triangle`, were added to `permits`, this exact `switch` would stop compiling with an error like `the switch expression does not cover all possible input values` until a `case Triangle t -> ...` arm (or a `default`) is added.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed interface permits a fixed set of subtypes; the compiler cross-checks every pattern-matching switch over that type against the full permitted set">
  <rect x="230" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">sealed interface Shape</text>

  <line x1="280" y1="60" x2="150" y2="95" stroke="#8b949e"/>
  <line x1="360" y1="60" x2="490" y2="95" stroke="#8b949e"/>

  <rect x="80" y="95" width="140" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="150" y="118" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Circle</text>
  <rect x="420" y="95" width="140" height="36" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="490" y="118" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Square</text>

  <rect x="140" y="150" width="360" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">switch checks: {Circle, Square} handled == {Circle, Square} permitted ✓</text>
</svg>

*The compiler compares "cases handled" against "subtypes permitted" and refuses to build if they don't match.*

## 5. Runnable example

Scenario: a notification-dispatch system over a sealed hierarchy, showing how exhaustiveness checking helps as the hierarchy grows.

### Level 1 — Basic

```java
public class NotifyTwoTypes {
    sealed interface Notification permits EmailNotification, SmsNotification {}
    record EmailNotification(String address, String body) implements Notification {}
    record SmsNotification(String phoneNumber, String body) implements Notification {}

    static String send(Notification n) {
        return switch (n) {
            case EmailNotification(var address, var body) -> "emailing " + address + ": " + body;
            case SmsNotification(var phone, var body) -> "texting " + phone + ": " + body;
        };
    }

    public static void main(String[] args) {
        System.out.println(send(new EmailNotification("a@example.com", "hello")));
        System.out.println(send(new SmsNotification("555-0100", "hi")));
    }
}
```

**How to run:** `java NotifyTwoTypes.java` (JDK 21+).

This compiles because `Notification` permits exactly two subtypes and the switch handles both — no `default` needed, and the compiler has verified there's no gap.

### Level 2 — Intermediate

```java
public class NotifyThreeTypes {
    sealed interface Notification permits EmailNotification, SmsNotification, PushNotification {}
    record EmailNotification(String address, String body) implements Notification {}
    record SmsNotification(String phoneNumber, String body) implements Notification {}
    record PushNotification(String deviceToken, String body) implements Notification {}

    static String send(Notification n) {
        return switch (n) {
            case EmailNotification(var address, var body) -> "emailing " + address + ": " + body;
            case SmsNotification(var phone, var body) -> "texting " + phone + ": " + body;
            case PushNotification(var token, var body) -> "pushing to " + token + ": " + body;
        };
    }

    public static void main(String[] args) {
        System.out.println(send(new EmailNotification("a@example.com", "hello")));
        System.out.println(send(new SmsNotification("555-0100", "hi")));
        System.out.println(send(new PushNotification("device-42", "ping")));
    }
}
```

**How to run:** `java NotifyThreeTypes.java`.

The real-world concern added: the hierarchy grows to a third subtype, `PushNotification`. Because `permits` was updated too, the compiler requires (and here, gets) a matching third `case` — this is the exhaustiveness guarantee actively doing its job as the domain model grows, not just a one-time check.

### Level 3 — Advanced

```java
public class NotifyAdvanced {
    sealed interface Notification permits EmailNotification, SmsNotification, PushNotification {}
    record EmailNotification(String address, String body) implements Notification {}
    record SmsNotification(String phoneNumber, String body) implements Notification {}
    record PushNotification(String deviceToken, String body) implements Notification {}

    // Uncomment the line below and this class stops compiling until every
    // switch over Notification adds a PriorityAlert case (or a default):
    // record PriorityAlert(String body) implements Notification {}

    static String send(Notification n) {
        return switch (n) {
            case EmailNotification(var address, var body) when body.isBlank() ->
                "skipping blank email to " + address;
            case EmailNotification(var address, var body) -> "emailing " + address + ": " + body;
            case SmsNotification(var phone, var body) -> "texting " + phone + ": " + body;
            case PushNotification(var token, var body) -> "pushing to " + token + ": " + body;
        };
    }

    public static void main(String[] args) {
        System.out.println(send(new EmailNotification("a@example.com", "")));
        System.out.println(send(new EmailNotification("a@example.com", "hello")));
        System.out.println(send(new SmsNotification("555-0100", "hi")));
        System.out.println(send(new PushNotification("device-42", "ping")));
    }
}
```

**How to run:** `java NotifyAdvanced.java`.

This adds the production-flavored hard case: a **guarded case** (`when body.isBlank()`) alongside an unguarded fallback for the same `EmailNotification` type. The compiler still verifies exhaustiveness at the level of the record *types* (`EmailNotification`, `SmsNotification`, `PushNotification` must all be covered by some combination of cases) — it does not attempt to prove the guards themselves are exhaustive, which is why the unguarded `EmailNotification` case is required as a catch-all beneath the guarded one. The commented-out `PriorityAlert` record demonstrates the guarantee in action: uncommenting it and adding it to `permits` would immediately break this exact switch at compile time, precisely because the new subtype is unhandled.

## 6. Walkthrough

Tracing what happens if a new subtype is added to a sealed hierarchy that a switch relies on:

1. A developer adds `record PriorityAlert(String body) implements Notification {}` and updates `permits EmailNotification, SmsNotification, PushNotification` to also include `PriorityAlert`.
2. At the next build, the compiler processes `NotifyAdvanced.send`'s `switch (n)`. It enumerates `Notification`'s permitted subtypes — now four — and checks each against the switch's case labels.
3. `EmailNotification`, `SmsNotification`, and `PushNotification` are each matched by some case. `PriorityAlert` is not matched by any case, and there is no `default` arm to catch it.
4. The compiler emits an error at the `switch` statement itself (not somewhere vague) — something like `the switch expression does not cover all possible input values`, naming the switch, before the code can even be built, let alone run.
5. The developer adds `case PriorityAlert(var body) -> "ALERT: " + body;` (or an equivalent), the compiler re-checks, finds all four subtypes now covered, and the build succeeds.

Concretely, running the file **as currently written** (with `PriorityAlert` still commented out) produces:
```
skipping blank email to a@example.com
emailing a@example.com: hello
texting 555-0100: hi
pushing to device-42: ping
```

The first line comes from the guarded case matching (`body.isBlank()` is `true` for `""`); the second line falls through the guard to the unguarded `EmailNotification` case since `"hello"` is not blank.

## 7. Gotchas & takeaways

> **Gotcha:** exhaustiveness checking only reasons about **type** coverage, not guard coverage. If every `case` for a given permitted type carried a `when` guard and none of them was unconditional, the compiler cannot prove those guards jointly cover every possible value — Java requires at least one unconditional (unguarded) pattern per type it needs for exhaustiveness, so you must supply a catch-all case even if you believe your guards are logically complete.

- Only works with `sealed` (or `final`) types and `enum` — an open (non-sealed) type can always gain an unknown subtype at runtime, so the compiler can never prove exhaustiveness over it and a `default` is required.
- Adding a new permitted subtype is a **useful** compile break: it surfaces every switch that needs updating, instead of a silent runtime gap.
- A guarded case never counts as "covering" its type on its own — pair it with an unguarded case for the same type as a fallback.
- Prefer exhaustive switches without `default` when the domain is genuinely closed — it's strictly more information for the compiler (and for future readers) than a `default` that silently swallows new cases.
- This is the mechanism that makes sealed hierarchies plus pattern-matching switch behave like algebraic data types with exhaustive pattern matching, familiar from languages like Kotlin, Scala, or Rust.
