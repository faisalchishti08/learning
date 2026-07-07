---
card: java
gi: 368
slug: enums-with-fields-constructors
title: Enums with fields & constructors
---

## 1. What it is

Beyond a bare list of names, an enum can carry its own **fields** and a **constructor**, letting each constant hold extra data alongside its identity. You declare fields and a constructor exactly like in a regular class, then pass constructor arguments to each constant using parentheses right after its name — `MERCURY(3.3e23, 2.4e6)`. The constructor runs once per constant, when the enum class is first loaded, permanently attaching that data to the singleton object.

## 2. Why & when

Plain enum constants (`MONDAY`, `TUESDAY`) are great when the only thing you need is a name and an identity. But real-world fixed sets often have associated data attached to each value — a planet has a mass and radius, an HTTP status has a numeric code and reason phrase, a currency has a symbol and number of decimal places. Without enum fields, you'd end up writing a separate `switch` or lookup map somewhere else in the code to associate each constant with its data — a second source of truth that can drift out of sync with the enum itself.

Attaching fields directly to the constants keeps the data and the identity bound together in one place: the enum declaration itself becomes the single source of truth. This matters whenever you're modelling something the real world already treats as "a fixed set of named things, each with intrinsic properties" — currencies, planets, chess pieces, HTTP methods, unit conversions, and so on.

## 3. Core concept

```java
public class PlanetDemo {
    enum Planet {
        MERCURY(3.303e+23, 2.4397e6),
        VENUS(4.869e+24, 6.0518e6),
        EARTH(5.976e+24, 6.37814e6);

        private final double mass;   // kg
        private final double radius; // meters

        Planet(double mass, double radius) { // constructor: runs once per constant
            this.mass = mass;
            this.radius = radius;
        }

        double surfaceGravity() {
            final double G = 6.67300E-11;
            return G * mass / (radius * radius);
        }
    }

    public static void main(String[] args) {
        for (Planet p : Planet.values()) {
            System.out.printf("%s surface gravity: %.2f m/s^2%n", p, p.surfaceGravity());
        }
    }
}
```

**How to run:** `java PlanetDemo.java`

Each constant (`MERCURY`, `VENUS`, `EARTH`) supplies its own `(mass, radius)` pair to the enum's constructor, which is invoked automatically once per constant at class-load time. `surfaceGravity()` is an ordinary instance method that reads `this.mass` and `this.radius` — every constant computes its own gravity from its own attached data.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each enum constant calls the shared constructor with its own arguments, producing distinct field values stored on that constant's singleton object">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">enum Planet { MERCURY(3.3e23, 2.4e6), VENUS(4.9e24, 6.1e6), EARTH(6.0e24, 6.4e6); ... }</text>

  <rect x="30" y="50" width="170" height="55" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="115" y="70" fill="#6db33f" font-size="10" text-anchor="middle">MERCURY</text>
  <text x="115" y="88" fill="#8b949e" font-size="9" text-anchor="middle">mass=3.3e23, radius=2.4e6</text>

  <rect x="235" y="50" width="170" height="55" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="70" fill="#6db33f" font-size="10" text-anchor="middle">VENUS</text>
  <text x="320" y="88" fill="#8b949e" font-size="9" text-anchor="middle">mass=4.9e24, radius=6.1e6</text>

  <rect x="440" y="50" width="170" height="55" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="525" y="70" fill="#6db33f" font-size="10" text-anchor="middle">EARTH</text>
  <text x="525" y="88" fill="#8b949e" font-size="9" text-anchor="middle">mass=6.0e24, radius=6.4e6</text>

  <text x="20" y="135" fill="#8b949e" font-size="10">Same constructor code runs 3 times, once per constant, each call with different arguments --</text>
  <text x="20" y="150" fill="#8b949e" font-size="10">producing 3 singleton objects with 3 distinct sets of field values, permanently fixed at class-load time.</text>
</svg>

## 5. Runnable example

Scenario: modelling an HTTP status code, evolved from a bare enum needing an external lookup map, through fields attached directly to each constant, to a version whose fields and a helper method make the enum fully self-describing.

### Level 1 — Basic

```java
import java.util.Map;

public class HttpStatusBasic {
    enum Status { OK, NOT_FOUND, SERVER_ERROR } // no data attached at all

    static final Map<Status, Integer> CODES = Map.of(
            Status.OK, 200,
            Status.NOT_FOUND, 404,
            Status.SERVER_ERROR, 500
    ); // a second, separate source of truth -- easy to forget to update

    public static void main(String[] args) {
        Status s = Status.NOT_FOUND;
        System.out.println(s + " -> " + CODES.get(s));
    }
}
```

**How to run:** `java HttpStatusBasic.java`

This works, but the numeric code lives in a completely separate `Map`, disconnected from the enum declaration — adding a new `Status` constant means remembering to also update `CODES` elsewhere, a maintenance trap.

### Level 2 — Intermediate

```java
public class HttpStatusIntermediate {
    enum Status {
        OK(200),
        NOT_FOUND(404),
        SERVER_ERROR(500);

        private final int code; // data lives directly on the constant now

        Status(int code) {
            this.code = code;
        }

        int code() {
            return code;
        }
    }

    public static void main(String[] args) {
        Status s = Status.NOT_FOUND;
        System.out.println(s + " -> " + s.code());
    }
}
```

**How to run:** `java HttpStatusIntermediate.java`

The numeric code now travels with the constant itself — no separate map to keep in sync. Adding a new status means adding one line inside the enum, with its code right there, impossible to forget.

### Level 3 — Advanced

```java
public class HttpStatusAdvanced {
    enum Status {
        OK(200, "OK"),
        NOT_FOUND(404, "Not Found"),
        SERVER_ERROR(500, "Internal Server Error");

        private final int code;
        private final String reasonPhrase;

        Status(int code, String reasonPhrase) {
            this.code = code;
            this.reasonPhrase = reasonPhrase;
        }

        int code() { return code; }
        String reasonPhrase() { return reasonPhrase; }

        static Status fromCode(int code) { // reverse lookup built from the enum's own data
            for (Status s : values()) {
                if (s.code == code) return s;
            }
            throw new IllegalArgumentException("Unknown HTTP status code: " + code);
        }

        String statusLine() {
            return code + " " + reasonPhrase;
        }
    }

    public static void main(String[] args) {
        Status s = Status.fromCode(404);
        System.out.println("Status line: " + s.statusLine());

        try {
            Status.fromCode(999);
        } catch (IllegalArgumentException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java HttpStatusAdvanced.java`

This adds a second field (`reasonPhrase`), a computed method (`statusLine()`) combining both fields, and a reverse lookup (`fromCode`) that searches `values()` — every piece of behaviour is derived entirely from data the enum itself owns, with no external map or switch statement needed anywhere in the program.

## 6. Walkthrough

Execution starts in `main`. `Status.fromCode(404)` is called first. Inside `fromCode`, `for (Status s : values())` iterates `[OK, NOT_FOUND, SERVER_ERROR]` in declaration order. For `OK`, `s.code == 404` is `200 == 404`, false. For `NOT_FOUND`, `s.code == 404` is `404 == 404`, true — the loop returns `NOT_FOUND` immediately, without checking `SERVER_ERROR`.

Back in `main`, `s` is now `Status.NOT_FOUND`. `s.statusLine()` runs: it returns `code + " " + reasonPhrase`, which for `NOT_FOUND` is `404 + " " + "Not Found"`, producing the string `"404 Not Found"`. This is printed as `Status line: 404 Not Found`.

`Status.fromCode(999)` is called next, inside a `try` block. The loop in `fromCode` checks all three constants (`200`, `404`, `500`) against `999` — none match, so the loop completes without returning. Control falls through to `throw new IllegalArgumentException("Unknown HTTP status code: 999")`. This propagates up out of `fromCode` and is caught by the `catch (IllegalArgumentException e)` block in `main`, which prints `Caught: Unknown HTTP status code: 999`.

Expected output:
```
Status line: 404 Not Found
Caught: Unknown HTTP status code: 999
```

## 7. Gotchas & takeaways

> Enum constructors are always implicitly `private` (or package-private) — you can never call `new Status(...)` from outside the enum, and you cannot even write `public` on an enum constructor; the compiler enforces that only the constants declared in the enum body can ever exist.

- Enum fields and constructors work exactly like a regular class's — declare fields, write a constructor that assigns them, and add instance methods that use them.
- Each constant supplies its own constructor arguments in parentheses right after its name; the constructor runs once, at class-load time, for every constant.
- Attaching data directly to enum constants keeps the enum as the single source of truth, avoiding a second, easily-forgotten lookup map or switch statement maintained elsewhere.
- Enum fields should almost always be `final` — a constant's attached data is meant to be fixed for its lifetime, matching the constant's own fixed, singleton nature.
- A reverse lookup method (like `fromCode`) built by looping over `values()` and checking a field is a common, idiomatic pattern for converting external data (a database column, an API response) back into the correct constant.
