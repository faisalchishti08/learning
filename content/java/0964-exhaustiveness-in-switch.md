---
card: java
gi: 964
slug: exhaustiveness-in-switch
title: Exhaustiveness in switch
---

## 1. What it is

Exhaustiveness is the compiler's ability to verify, at compile time, that a `switch` expression's cases cover every possible value the switched-on expression could ever have — and, for a `switch` expression (as opposed to a `switch` statement), exhaustiveness is *mandatory*: the compiler refuses to compile a `switch` expression that isn't provably exhaustive, since a `switch` expression must always produce a value, and there'd be no value to produce for an unhandled case. This check is possible for two kinds of switched-on types: `enum` types (where the compiler already knows every possible constant) and, since Java 21, [sealed types](0961-sealed-permits-clauses.md) (where the compiler knows every possible permitted subtype, transitively, down to every branch's own final resolution) — for any other type (an ordinary class, an unsealed interface, or `String`/`Integer` and similar), the compiler cannot know the complete set of possible values, so a `default` case (or an unconditional final pattern) is always required instead.

## 2. Why & when

Exhaustiveness checking exists to catch a specific, historically common class of bug at the earliest, cheapest possible point: a `switch` that was written when a type had, say, three variants, silently continuing to compile — but doing the wrong thing (either falling through unhandled, or hitting a `default` that wasn't written with the new variant in mind) — after a fourth variant is added later. Traditional `switch` *statements* over `enum` types have long offered a *warning* (not an error) for a missing case, but a `switch` *expression* elevates this to a hard compile error, and pairing it with sealed types extends the exact same guarantee to arbitrary class/interface hierarchies, not just enums. This matters most precisely in the [sealed + records + pattern-matching synergy](0963-sealed-records-pattern-matching-synergy.md) style of modeling closed variant sets: every operation written as an exhaustive `switch` over that hierarchy is guaranteed, by the compiler, to still handle every variant correctly the moment the hierarchy changes — turning what would otherwise be a silent, easy-to-miss runtime gap into an unmissable compile error at exactly the operations that need updating.

## 3. Core concept

```
enum Direction { NORTH, SOUTH, EAST, WEST }

// switch EXPRESSION over an enum -- exhaustiveness REQUIRED, no default needed
// as long as literally every enum constant has a case:
String opposite = switch (direction) {
    case NORTH -> "SOUTH";
    case SOUTH -> "NORTH";
    case EAST -> "WEST";
    case WEST -> "EAST";
    // if WEST's case were missing here: COMPILE ERROR -- "the switch expression does not
    // cover all possible input values" -- caught immediately, not at runtime
};

sealed interface Shape permits Circle, Square {}
record Circle(double r) implements Shape {}
record Square(double s) implements Shape {}

double area = switch (shape) {
    case Circle(double r) -> Math.PI * r * r;
    case Square(double s) -> s * s;
    // exhaustive: Circle + Square together cover EVERY possible Shape -- verified by
    // walking Shape's permits clause, not just a runtime guess
};
```

Exhaustiveness checking works by the compiler statically enumerating every possible case (an enum's constants, or a sealed type's complete permitted-subtype tree) and verifying the `switch`'s cases cover that exact, complete set — with no gap, and (for `switch` expressions) with a hard compile error if any gap exists.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The compiler comparing a switch expression's covered cases against a sealed type's complete permitted set, flagging a compile error if any variant is missing" >
  <rect x="20" y="30" width="260" height="90" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="48" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Sealed type's COMPLETE set</text>
  <text x="150" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Circle, Square, Triangle</text>
  <text x="150" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">(known via permits clause)</text>

  <rect x="360" y="30" width="260" height="90" fill="#1c2430" stroke="#f0883e"/>
  <text x="490" y="48" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">switch expression's cases</text>
  <text x="490" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Circle, Square</text>
  <text x="490" y="88" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Triangle MISSING -&gt; COMPILE ERROR</text>

  <line x1="280" y1="75" x2="360" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Compiler compares both sets directly -- any gap is caught before the program ever runs</text>
</svg>

*The compiler statically compares a switch expression's covered cases against the sealed type's fully known, complete set of variants.*

## 5. Runnable example

Scenario: build a small notification-dispatch system and directly observe exhaustiveness checking in action — starting with a basic exhaustive enum-based switch, then a sealed-type-based switch showing the same guarantee for a class hierarchy, then a harder case showing exactly what happens (and what's still required) when a `non-sealed` branch is present in an otherwise-sealed hierarchy.

### Level 1 — Basic

```java
public class ExhaustivenessEnumBasic {
    enum Severity { INFO, WARNING, ERROR }

    static String label(Severity severity) {
        return switch (severity) {
            case INFO -> "[i]";
            case WARNING -> "[!]";
            case ERROR -> "[X]";
            // if ERROR's case were removed: COMPILE ERROR --
            // "the switch expression does not cover all possible input values"
        };
    }

    public static void main(String[] args) {
        for (Severity s : Severity.values()) {
            System.out.println(label(s) + " " + s);
        }
    }
}
```

**How to run:** `java ExhaustivenessEnumBasic.java` (JDK 17+; switch expressions with arrow syntax are available since Java 14).

Expected output:
```
[i] INFO
[!] WARNING
[X] ERROR
```

Every one of `Severity`'s three constants has a corresponding case, so this compiles cleanly with no `default` needed — the compiler has verified, by comparing against the enum's complete, known constant list, that every possible `Severity` value is handled.

### Level 2 — Intermediate

```java
public class ExhaustivenessSealedBasic {
    sealed interface ApiResult permits Success, ClientError, ServerError {}
    record Success(String data) implements ApiResult {}
    record ClientError(int code, String message) implements ApiResult {}
    record ServerError(int code) implements ApiResult {}

    static String handle(ApiResult result) {
        return switch (result) {
            case Success(String data) -> "OK: " + data;
            case ClientError(int code, String msg) -> "Client error " + code + ": " + msg;
            case ServerError(int code) -> "Server error " + code + " -- retry later";
        };
    }

    public static void main(String[] args) {
        System.out.println(handle(new Success("user data")));
        System.out.println(handle(new ClientError(404, "not found")));
        System.out.println(handle(new ServerError(503)));
    }
}
```

**How to run:** `java ExhaustivenessSealedBasic.java` (JDK 21+; record patterns in switch require Java 21+).

Expected output:
```
OK: user data
Client error 404: not found
Server error 503 -- retry later
```

The real-world concern added: `ApiResult`'s sealed hierarchy has three variants, and `handle`'s `switch` covers all three with record-pattern deconstruction — extending exhaustiveness checking (previously only available for enums) to an arbitrary, richer class hierarchy where each variant also carries its own distinct data, verified by the compiler walking `ApiResult`'s complete `permits` tree.

### Level 3 — Advanced

```java
public class ExhaustivenessWithNonSealed {
    sealed interface ApiResult permits Success, ClientError, ExtendedResult {}
    record Success(String data) implements ApiResult {}
    record ClientError(int code) implements ApiResult {}
    non-sealed interface ExtendedResult extends ApiResult {
        String describe();
    }
    record RateLimited(int retryAfterSeconds) implements ExtendedResult {
        public String describe() { return "rate limited, retry after " + retryAfterSeconds + "s"; }
    }

    static String handle(ApiResult result) {
        return switch (result) {
            case Success(String data) -> "OK: " + data;
            case ClientError(int code) -> "Client error " + code;
            case ExtendedResult ext -> ext.describe();
            // exhaustive at the ApiResult level: Success + ClientError + ExtendedResult
            // covers everything -- but ExtendedResult's OWN subtypes cannot be
            // individually enumerated, so it must be handled generically, via describe()
        };
    }

    public static void main(String[] args) {
        System.out.println(handle(new Success("ok")));
        System.out.println(handle(new ClientError(400)));
        System.out.println(handle(new RateLimited(30)));
    }
}
```

**How to run:** `java ExhaustivenessWithNonSealed.java` (JDK 21+).

Expected output:
```
OK: ok
Client error 400
rate limited, retry after 30s
```

The production-flavored hard case: the `switch` is still fully exhaustive and compiles with no `default`, because `Success`, `ClientError`, and `ExtendedResult` together do cover every possible `ApiResult` — but `ExtendedResult`'s own further subtypes (like `RateLimited`, and any future ones) cannot be individually named in this `switch`, since `ExtendedResult` is deliberately `non-sealed`; exhaustiveness is verified only down to the level the hierarchy is actually closed, with the `non-sealed` branch necessarily handled through its own interface contract instead.

## 6. Walkthrough

Tracing the compiler's exhaustiveness verification for `handle`'s `switch` in `ExhaustivenessWithNonSealed`, step by step:

1. The compiler first determines `ApiResult`'s complete set of permitted direct subtypes from its `permits` clause: `Success`, `ClientError`, and `ExtendedResult` — this is the full, closed set it must verify coverage against.
2. It then checks the `switch`'s case labels against this set: `case Success(...)` covers `Success`; `case ClientError(...)` covers `ClientError`; `case ExtendedResult ext` covers `ExtendedResult` — every member of `ApiResult`'s permitted set has a corresponding case, so at *this* level, the `switch` is confirmed exhaustive, and no `default` is required.
3. Critically, the compiler does not attempt to further verify exhaustiveness *within* `ExtendedResult`'s own subtypes (like `RateLimited`), because `ExtendedResult` is declared `non-sealed` — its own set of possible implementers is, by design, open-ended and unknowable to the compiler; the `case ExtendedResult ext` label is accepted as sufficient coverage for the entire branch, precisely because it doesn't attempt to enumerate what's inside it.
4. At runtime, `handle(new RateLimited(30))` is called — the `switch` evaluates its cases against the actual object; `RateLimited` is not a `Success` or `ClientError`, but it does implement `ExtendedResult`, so the third case matches, binding `ext` to the `RateLimited` instance with the *static* type `ExtendedResult`.
5. `ext.describe()` is called — since `ext`'s actual runtime type is `RateLimited`, this resolves via ordinary virtual dispatch to `RateLimited.describe()`, which returns `"rate limited, retry after 30s"`.
6. This value is returned from the `switch` expression and printed — demonstrating that exhaustiveness, in the presence of a `non-sealed` branch, operates at exactly the granularity the hierarchy is actually closed to: fully verified and guaranteed at the `ApiResult` level (no possible `ApiResult` value could ever reach this `switch` unhandled), while gracefully deferring to ordinary interface-based polymorphism for whatever lies within the deliberately open `ExtendedResult` branch.

## 7. Gotchas & takeaways

> **Gotcha:** a `switch` *statement* (not expression) over an enum only ever produces a *warning*, not a compile error, for a missing case — this is different, weaker behavior than a `switch` *expression*'s hard-error requirement; if exhaustiveness genuinely needs to be enforced at compile time, prefer writing the logic as a `switch` expression (assigning its result, or using it as a `return` directly) rather than an older-style `switch` statement with separate `case`-body statements, even if you don't strictly need the resulting value for anything beyond triggering the stricter check.

- Exhaustiveness checking verifies, at compile time, that a `switch`'s cases cover every possible value — mandatory (a compile error if violated) for `switch` expressions, and possible specifically for `enum` types and, since Java 21, [sealed types](0961-sealed-permits-clauses.md).
- For any type the compiler cannot fully enumerate (an ordinary class, `String`, an unsealed interface), a `default` case (or a final unconditional pattern) is always required instead.
- A `switch` expression over a sealed hierarchy is checked against the hierarchy's complete `permits` tree — every direct permitted subtype must have a covering case, transitively down through any further-sealed branches.
- A `non-sealed` branch is treated as fully covered by a single case matching that branch's own type — the compiler does not (and cannot) further verify exhaustiveness over that branch's own, deliberately open-ended, set of implementers.
- A `switch` *statement* over an enum only warns, rather than errors, on a missing case — prefer a `switch` expression whenever you want the stricter, compile-error-level guarantee.
- See [sealed / permits clauses](0961-sealed-permits-clauses.md) for how the closed hierarchies this checking relies on are declared, and [sealed + records + pattern-matching synergy](0963-sealed-records-pattern-matching-synergy.md) for the broader design style this exhaustiveness guarantee is central to.
