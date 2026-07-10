---
card: java
gi: 1014
slug: dependency-injection
title: Dependency Injection
---

## 1. What it is

**Dependency Injection (DI)** is the mechanical technique of *supplying* an object's dependencies from the outside — through a constructor, a setter, or a field — instead of having the object construct its own dependencies internally with `new`. It's the practical implementation of [SOLID — Dependency Inversion](0993-solid-dependency-inversion.md): DIP is the *principle* ("depend on abstractions, let something else decide the concrete detail"), and DI is the *technique* that makes it happen in code — someone or something else must actually do the injecting.

## 2. Why & when

A class that constructs its own dependencies internally (`new MySqlOrderRepository()` inside `OrderService`'s constructor) can't be tested without a real database, and can't be reconfigured to use a different implementation without editing its source. Constructor injection — passing dependencies in as constructor parameters — solves both problems at once: a test can pass in a fake implementation, and production code can pass in whichever real implementation is configured for that environment, all without `OrderService` itself changing.

Reach for DI whenever a class depends on something that varies by context or needs to be faked in tests — a repository, an HTTP client, a clock, a random number generator. Manual DI (passing dependencies through constructors yourself, as shown below) works fine for small applications; larger applications typically use a DI framework (Spring, Guice, CDI) to automate the wiring so you don't hand-assemble the whole object graph yourself at startup.

## 3. Core concept

```
interface Clock { long currentTimeMillis(); }
class SystemClock implements Clock {
    public long currentTimeMillis() { return System.currentTimeMillis(); }
}
class FixedClock implements Clock { // a test double, injected instead of SystemClock in tests
    private final long fixedTime;
    FixedClock(long fixedTime) { this.fixedTime = fixedTime; }
    public long currentTimeMillis() { return fixedTime; }
}

class OrderTimestamper {
    private final Clock clock; // injected, not constructed internally
    OrderTimestamper(Clock clock) { this.clock = clock; } // CONSTRUCTOR injection
    long timestampOrder() { return clock.currentTimeMillis(); }
}

// Production wiring supplies the real clock:
OrderTimestamper production = new OrderTimestamper(new SystemClock());
// A test supplies a fake clock instead -- OrderTimestamper itself never changes:
OrderTimestamper test = new OrderTimestamper(new FixedClock(1_700_000_000_000L));
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Production wiring injecting a SystemClock into OrderTimestamper while a test injects a FixedClock instead, both through the same constructor">
  <rect x="230" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderTimestamper</text>

  <rect x="30" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">production: new SystemClock()</text>

  <rect x="30" y="130" width="140" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="100" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">test: new FixedClock(...)</text>

  <line x1="170" y1="37" x2="230" y2="80" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="170" y1="147" x2="230" y2="110" stroke="#f0883e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same `OrderTimestamper` constructor accepts either a real `SystemClock` in production or a `FixedClock` in tests — nothing inside `OrderTimestamper` changes either way.

## 5. Runnable example

Scenario: a service that timestamps orders and needs deterministic tests, evolving from an internally-constructed, untestable dependency into constructor-injected, swappable dependencies.

### Level 1 — Basic

```java
// File: DiBasic.java
class OrderTimestamper {
    long timestampOrder() {
        return System.currentTimeMillis(); // hardcoded -- impossible to test deterministically
    }
}

public class DiBasic {
    public static void main(String[] args) {
        OrderTimestamper timestamper = new OrderTimestamper();
        long timestamp = timestamper.timestampOrder();
        System.out.println("got a timestamp: " + (timestamp > 0));
    }
}
```

**How to run:** save as `DiBasic.java`, then `javac DiBasic.java && java DiBasic` (JDK 17+).

Expected output:
```
got a timestamp: true
```

There's no way to write a test asserting an exact, predictable timestamp — `OrderTimestamper` always calls the real system clock, making deterministic testing of anything that depends on the returned value impossible.

### Level 2 — Intermediate

```java
// File: DiIntermediate.java
interface Clock {
    long currentTimeMillis();
}

class SystemClock implements Clock {
    public long currentTimeMillis() { return System.currentTimeMillis(); }
}

class OrderTimestamper {
    private final Clock clock;
    OrderTimestamper(Clock clock) { this.clock = clock; } // dependency injected via constructor
    long timestampOrder() { return clock.currentTimeMillis(); }
}

public class DiIntermediate {
    public static void main(String[] args) {
        OrderTimestamper timestamper = new OrderTimestamper(new SystemClock());
        long timestamp = timestamper.timestampOrder();
        System.out.println("got a timestamp: " + (timestamp > 0));
    }
}
```

**How to run:** save as `DiIntermediate.java`, then `javac DiIntermediate.java && java DiIntermediate` (JDK 17+).

Expected output:
```
got a timestamp: true
```

The real-world concern added: `OrderTimestamper` now depends on the `Clock` interface, injected through its constructor. Production code still gets a real timestamp via `SystemClock`, but `OrderTimestamper` itself no longer hardcodes which clock implementation it uses.

### Level 3 — Advanced

```java
// File: DiAdvanced.java
interface Clock {
    long currentTimeMillis();
}

class SystemClock implements Clock {
    public long currentTimeMillis() { return System.currentTimeMillis(); }
}

// A fake clock for deterministic testing -- OrderTimestamper has no idea
// it isn't talking to a real clock.
class FixedClock implements Clock {
    private final long fixedTime;
    FixedClock(long fixedTime) { this.fixedTime = fixedTime; }
    public long currentTimeMillis() { return fixedTime; }
}

class OrderTimestamper {
    private final Clock clock;
    OrderTimestamper(Clock clock) { this.clock = clock; }

    String timestampOrder(String orderId) {
        long time = clock.currentTimeMillis();
        return orderId + "@" + time;
    }
}

// A tiny hand-rolled "test" demonstrating deterministic assertions -- exactly
// what constructor injection unlocks, without needing a real test framework here.
public class DiAdvanced {
    static void assertEquals(String expected, String actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError("expected <" + expected + "> but got <" + actual + ">");
        }
        System.out.println("PASS: " + actual);
    }

    public static void main(String[] args) {
        // Production wiring:
        OrderTimestamper production = new OrderTimestamper(new SystemClock());
        System.out.println("production timestamp looks real: " + production.timestampOrder("order-1").contains("@"));

        // Deterministic "test" using an injected fake clock:
        OrderTimestamper testInstance = new OrderTimestamper(new FixedClock(1_700_000_000_000L));
        assertEquals("order-42@1700000000000", testInstance.timestampOrder("order-42"));
    }
}
```

**How to run:** save as `DiAdvanced.java`, then `javac DiAdvanced.java && java DiAdvanced` (JDK 17+).

Expected output:
```
production timestamp looks real: true
PASS: order-42@1700000000000
```

The production-flavored hard case: the exact same `OrderTimestamper` class is used with two completely different `Clock` implementations in the same program — a real one for production-style behavior, and a fixed one that makes the result perfectly predictable and assertable, which is precisely what makes automated testing of time-dependent logic practical at all.

## 6. Walkthrough

Tracing `testInstance.timestampOrder("order-42")` in `DiAdvanced.main`:

1. `new OrderTimestamper(new FixedClock(1_700_000_000_000L))` constructs a `FixedClock` holding the constant `1_700_000_000_000L`, and injects it into `OrderTimestamper`'s `clock` field.
2. `testInstance.timestampOrder("order-42")` calls `clock.currentTimeMillis()` — since `clock` is a `FixedClock` (not a `SystemClock`), this dispatches to `FixedClock.currentTimeMillis()`, which simply returns the stored `fixedTime`, `1_700_000_000_000L`, regardless of what the real system clock currently reads.
3. `time` is now `1_700_000_000_000L`. The method returns `orderId + "@" + time`, which is `"order-42" + "@" + "1700000000000"` = `"order-42@1700000000000"`.
4. `assertEquals("order-42@1700000000000", "order-42@1700000000000")` compares the two strings — they match exactly, so it prints `"PASS: order-42@1700000000000"` instead of throwing an `AssertionError`.
5. This exact assertion would be flaky and essentially impossible to write reliably if `OrderTimestamper` called `System.currentTimeMillis()` directly (as in Level 1) — the real clock's value changes every millisecond, so no fixed expected string could ever match it consistently.
6. Compare with `production.timestampOrder("order-1")`: it dispatches to `SystemClock.currentTimeMillis()` instead, since `production` was constructed with a `SystemClock`, returning the real current time — `main` only checks that the result *contains* `"@"` rather than asserting an exact value, since the real time is unpredictable by design.

## 7. Gotchas & takeaways

> **Gotcha:** dependency injection doesn't require a framework — "manual DI" (passing dependencies through plain constructors, as shown here) is a completely valid and often clearer approach for small applications. Reach for a DI framework (Spring, Guice) when the object graph grows large enough that hand-wiring every constructor call becomes tedious and error-prone, not because DI itself demands one.

- Dependency Injection is the technique — passing dependencies in via constructor, setter, or field — that makes [SOLID — Dependency Inversion](0993-solid-dependency-inversion.md)'s principle practical in real code.
- Constructor injection (dependencies passed as constructor parameters, usually stored in `final` fields) is generally preferred: it makes required dependencies explicit and guarantees the object is never in a partially-constructed, dependency-less state.
- The single biggest practical payoff is testability: injecting a fake or fixed implementation (like `FixedClock`) makes previously non-deterministic behavior (like the current time) fully controllable and assertable in tests.
- "Manual DI" (wiring dependencies by hand in `main` or a small factory) works fine for small programs; DI frameworks automate this wiring for larger applications with many interdependent objects.
- Don't inject dependencies that never vary and are never faked in tests — that's DI applied where DIP's benefit doesn't actually materialize, adding indirection without payoff.
- See [Singleton](0997-singleton.md) for a related concept: a DI framework's "singleton scope" often replaces a hand-rolled static singleton, keeping the class itself unaware that it's being shared.
