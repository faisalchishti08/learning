---
card: java
gi: 194
slug: method-overloading-resolution
title: Method overloading & resolution
---

## 1. What it is

**Overload resolution** is the compile-time process Java uses to decide *which* overloaded method (or constructor) an ambiguous-looking call actually invokes, based on the number, types, and order of the arguments supplied. It happens in phases: Java first looks for an exact type match without any conversion; if none exists, it tries again allowing automatic widening (like `int` to `long`); if still none, it tries with autoboxing (`int` to `Integer`); and finally with varargs, if applicable. The compiler picks the *most specific* applicable method it finds at the earliest phase that produces a match.

```java
class Printer {
    void show(int x)    { System.out.println("int: " + x); }
    void show(long x)   { System.out.println("long: " + x); }
    void show(double x) { System.out.println("double: " + x); }
}

Printer p = new Printer();
p.show(5);     // matches show(int) — exact match, phase 1
p.show(5L);    // matches show(long) — exact match, phase 1
p.show(5.0);   // matches show(double) — exact match, phase 1
p.show((byte) 5); // matches show(int) — byte widens to int before long or double are tried
```

`show((byte) 5)` doesn't have an exact `byte` overload, so the compiler widens it — `byte` widens to `int` before it would consider `long` or `double`, since Java always prefers the *smallest* widening conversion that produces a match, picking `show(int)`.

## 2. Why & when

Understanding overload resolution matters because it determines exactly which method body actually runs for a given call — and Java's rules, while consistent, are not always obvious at a glance:

- **Predicting behaviour correctly** — a call like `show(5)` looks unambiguous, but with several overloads present, knowing the resolution order (exact match, then widening, then autoboxing, then varargs) is what lets you predict with certainty which one runs.
- **Avoiding ambiguous-call compile errors** — sometimes multiple overloads are *equally* good matches for a given call (for example, passing `null` when both `show(String)` and `show(StringBuilder)` exist), and the compiler refuses to guess, producing an "ambiguous method call" error instead.
- **Autoboxing and varargs interact with overload resolution in subtle ways** — a method with an `int` parameter is always preferred over one taking `Integer` (autoboxing) for a literal `int` argument, and a fixed-arity overload is always preferred over a varargs one, if both would otherwise match.

You need this understanding any time your class has multiple overloads of the same method name, to be certain which one actually executes for a given call, especially across primitive types that can widen into each other.

## 3. Core concept

```java
public class ResolutionDemo {
    static void handle(Object o)   { System.out.println("Object"); }
    static void handle(String s)   { System.out.println("String"); }

    public static void main(String[] args) {
        handle("hello");  // String — most specific applicable match
        handle(42);       // Object — 42 autoboxes to Integer, which is not a String, so Object is the only match
        handle((Object) "hello"); // Object — the compile-time TYPE of the expression is Object, despite the runtime value being a String
    }
}
```

Overload resolution happens based on the **compile-time declared type** of each argument, not its runtime value — `(Object) "hello"` is still a `String` object at runtime, but because the expression's *static type* is `Object`, the compiler resolves the call to `handle(Object)`, not `handle(String)`, regardless of what the object actually is underneath.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Overload resolution phases shown as a sequence: first look for an exact type match, then try widening primitive conversions, then autoboxing, then varargs, stopping at the earliest phase that finds an applicable method">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Overload resolution phases, tried in order, stopping at first match</text>

  <rect x="30" y="40" width="120" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="62" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">1. exact match</text>

  <rect x="170" y="40" width="120" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="230" y="62" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2. widening</text>

  <rect x="310" y="40" width="120" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="62" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">3. autoboxing</text>

  <rect x="450" y="40" width="120" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="510" y="62" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">4. varargs</text>

  <line x1="90" y1="75" x2="90" y2="90" stroke="#8b949e"/>
  <line x1="230" y1="75" x2="230" y2="90" stroke="#8b949e"/>
  <line x1="370" y1="75" x2="370" y2="90" stroke="#8b949e"/>
  <line x1="510" y1="75" x2="510" y2="90" stroke="#8b949e"/>

  <text x="300" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Java stops at the first phase where an applicable method is found — earlier phases are always preferred.</text>
  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Resolution is decided entirely at compile time, using each argument's declared (static) type.</text>
  <text x="300" y="163" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">A method already matched by an earlier phase is never reconsidered against a later phase.</text>
</svg>

Java tries each resolution phase in order and commits to the first phase that produces an applicable, unambiguous match.

## 5. Runnable example

Scenario: a small logging utility with several overloads — starting with basic type-based resolution, then extending to demonstrate widening in action, then hardening into a case that shows autoboxing versus a fixed-arity overload being resolved correctly ahead of a varargs fallback.

### Level 1 — Basic

```java
public class LoggerBasic {
    static void log(String message) { System.out.println("STRING: " + message); }
    static void log(int code)       { System.out.println("CODE: " + code); }

    public static void main(String[] args) {
        log("Server started");
        log(200);
    }
}
```

**How to run:** `java LoggerBasic.java`

`log("Server started")` matches `log(String)` exactly; `log(200)` matches `log(int)` exactly — both are straightforward exact-type matches, phase 1 of resolution, requiring no conversion at all.

### Level 2 — Intermediate

Same logger, now with an overload only for `long`, demonstrating that a plain `int` argument widens automatically to match it when no exact `int` overload exists.

```java
public class LoggerIntermediate {
    static void log(String message) { System.out.println("STRING: " + message); }
    static void log(long code)      { System.out.println("LONG CODE: " + code); } // no int overload exists

    public static void main(String[] args) {
        log("Server started");
        log(200); // an int literal — no log(int) exists, so it widens to long
    }
}
```

**How to run:** `java LoggerIntermediate.java`

`log(200)` has no exact `log(int)` overload to match, so the compiler proceeds to phase 2 (widening): `int` widens to `long` without any data loss, so `log(long)` is selected — this is why the output reads `"LONG CODE: 200"` even though `200` was written as a plain `int` literal in the source.

### Level 3 — Advanced

Same logger, now with three overloads together — `log(int)`, `log(int, int)`, and `log(int...)` (varargs) — demonstrating that a fixed-arity match is always preferred over a varargs one when both would otherwise apply.

```java
public class LoggerAdvanced {
    static void log(int code) {
        System.out.println("single: " + code);
    }

    static void log(int code, int severity) {
        System.out.println("pair: code=" + code + " severity=" + severity);
    }

    static void log(int... codes) { // varargs — matches ANY number of int arguments, including zero
        System.out.println("varargs: " + java.util.Arrays.toString(codes));
    }

    public static void main(String[] args) {
        log(200);          // matches log(int) — fixed-arity, preferred over varargs
        log(200, 3);        // matches log(int, int) — fixed-arity, preferred over varargs
        log(200, 3, 7);      // no fixed-arity overload takes 3 ints — falls through to varargs
        log();              // no fixed-arity overload takes zero args — falls through to varargs
    }
}
```

**How to run:** `java LoggerAdvanced.java`

`log(200)` and `log(200, 3)` both have exact fixed-arity matches (`log(int)` and `log(int, int)` respectively) and Java always prefers these over the varargs overload, even though `log(int...)` could technically also accept one or two `int` arguments — the varargs overload is only chosen for `log(200, 3, 7)` and `log()`, where no fixed-arity overload's parameter count matches at all.

## 6. Walkthrough

Trace all four calls in `LoggerAdvanced.main`, in order:

**`log(200)`.** The compiler checks fixed-arity overloads first: `log(int)` takes exactly one `int` — an exact match. Resolution stops here; `log(int, int)` and `log(int...)` are never even considered, since a match was already found. Prints `"single: 200"`.

**`log(200, 3)`.** `log(int)` doesn't match (wrong argument count). `log(int, int)` takes exactly two `int`s — an exact match. Resolution stops here. Prints `"pair: code=200 severity=3"`.

**`log(200, 3, 7)`.** Neither `log(int)` nor `log(int, int)` matches (three arguments). Only `log(int...)` can accept three separate `int` arguments, packing them into an array `{200, 3, 7}` automatically. Prints `"varargs: [200, 3, 7]"`.

**`log()`.** No fixed-arity overload accepts zero arguments. `log(int...)` accepts zero arguments too, packing them into an empty array `{}`. Prints `"varargs: []"`.

```
log(200)        -> fixed-arity log(int) matches exactly           -> "single: 200"
log(200, 3)     -> fixed-arity log(int,int) matches exactly       -> "pair: code=200 severity=3"
log(200, 3, 7)  -> no fixed-arity match (3 args) -> varargs used  -> "varargs: [200, 3, 7]"
log()           -> no fixed-arity match (0 args) -> varargs used  -> "varargs: []"
```

## 7. Gotchas & takeaways

> **A fixed-arity overload is always preferred over a varargs overload whenever both could apply.** This means adding a varargs overload alongside existing fixed-arity ones is generally safe — existing calls keep resolving to their original fixed-arity methods; the varargs version only kicks in for argument counts that no fixed-arity overload covers.

> **Overload resolution is decided at compile time, using each argument expression's declared (static) type — not its runtime value.** Casting an argument to a supertype (like `(Object) someString`) can change which overload is selected, even though the object itself is unchanged at runtime; this is a common source of confusion when debugging "why did the wrong overload run" issues.

- Java resolves overloaded calls in phases: exact match, then widening, then autoboxing, then varargs — stopping at the first phase that finds an applicable method.
- Resolution uses each argument's compile-time declared type, not its runtime type — a cast to a supertype can change which overload is picked.
- A fixed-arity overload always wins over a varargs one, whenever the argument count matches a fixed-arity signature exactly.
- If two overloads are equally good matches for a call (a genuine tie), the compiler reports an ambiguous-call error rather than guessing.
