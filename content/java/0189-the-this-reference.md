---
card: java
gi: 189
slug: the-this-reference
title: The 'this' reference
---

## 1. What it is

`this` is a special reference available inside any instance method or constructor that refers to **the specific object the method was called on** — "this particular instance." It's most commonly needed when a parameter or local variable has the same name as a field, to explicitly distinguish "the field belonging to this object" from "the local parameter."

```java
class Point {
    int x;
    int y;

    void setX(int x) { // parameter also named x — shadows the field
        this.x = x; // this.x is the FIELD; plain x is the PARAMETER
    }
}
```

`this.x` unambiguously refers to the object's field; plain `x` (without `this.`) refers to the parameter — without writing `this.x = x;`, the statement `x = x;` would just assign the parameter to itself, leaving the actual field untouched.

## 2. Why & when

`this` exists to resolve ambiguity and to let an object refer to itself explicitly:

- **Disambiguating shadowed names** — when a constructor or method parameter is named the same as a field (a very common and readable convention, especially in constructors), `this.fieldName` is the only way to refer to the field rather than the parameter.
- **Passing the current object to another method** — occasionally a method needs to hand a reference to "this exact object" to some other method or constructor (for example, registering itself as a listener).
- **Constructor chaining** — `this(...)` (a related but distinct usage, calling another constructor in the same class) is covered in the constructors topic; the plain `this` reference and the `this(...)` call share the same keyword but serve different roles.

You need `this.field` specifically whenever a parameter or local variable's name shadows a field name — which is an extremely common situation in constructors and simple "setter" methods, where naming the parameter the same as the field it sets is the clearest, most conventional style.

## 3. Core concept

```java
class Rectangle {
    double width;
    double height;

    void resize(double width, double height) {
        this.width = width;   // this.width = the FIELD; width (right side) = the PARAMETER
        this.height = height; // same pattern for height
    }

    double area() {
        return this.width * this.height; // "this." here is optional but sometimes used for clarity
    }
}
```

Inside `resize`, `this.width` and `width` (without `this.`) refer to two different things simultaneously — the field and the parameter — even though they share the same identifier text; inside `area`, where there's no shadowing parameter, writing `this.width` is entirely optional and behaves identically to just `width`.

## 4. Diagram

<svg viewBox="0 0 560 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inside a method, the plain identifier width refers to the local parameter, while this dot width refers to the object's own field, shown as two separate labeled boxes despite sharing the same name">
  <rect x="8" y="8" width="544" height="134" rx="8" fill="#0d1117"/>
  <text x="280" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">void resize(double width, double height) { this.width = width; }</text>

  <rect x="60" y="45" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="65" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">parameter "width"</text>
  <text x="150" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">local, temporary, this call only</text>

  <rect x="320" y="45" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="410" y="65" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">this.width (field)</text>
  <text x="410" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">belongs to the object, persists</text>

  <line x1="240" y1="67" x2="320" y2="67" stroke="#f85149" stroke-width="2" marker-end="url(#w)"/>
  <text x="280" y="60" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">assignment</text>
  <defs><marker id="w" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker></defs>

  <text x="280" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">this.width = width  copies the parameter's value INTO the field</text>
</svg>

`this.field` and a same-named parameter are two distinct storage locations; `this.` is what tells them apart.

## 5. Runnable example

Scenario: a simple mutable `Temperature` holder — starting with a basic setter demonstrating shadowing resolved by `this`, then extending to a method that both reads and updates fields using `this` for clarity, then hardening into a method that passes `this` (the current object) to another method that needs a reference to it.

### Level 1 — Basic

```java
public class ThisBasic {
    static class Temperature {
        double celsius;

        void setCelsius(double celsius) {
            this.celsius = celsius; // this.celsius is the field; celsius alone is the parameter
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature();
        t.setCelsius(23.5);
        System.out.println(t.celsius);
    }
}
```

**How to run:** `java ThisBasic.java`

`this.celsius = celsius` assigns the parameter's value into the field — without `this.`, writing plain `celsius = celsius;` would just reassign the parameter to itself and leave the actual field at its default (`0.0`), which is a classic beginner mistake this pattern avoids.

### Level 2 — Intermediate

Same `Temperature`, now with a method that both reads the current field value and updates it, using `this` for the field access to keep the distinction from any local variable explicit and clear.

```java
public class ThisIntermediate {
    static class Temperature {
        double celsius;

        void adjustBy(double celsius) { // parameter shadows the field again
            double previous = this.celsius; // explicitly reading the FIELD's current value
            this.celsius = previous + celsius; // updating the field using both old field value and new parameter
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature();
        t.celsius = 20.0;

        t.adjustBy(3.5);
        System.out.println(t.celsius); // 23.5

        t.adjustBy(-10.0);
        System.out.println(t.celsius); // 13.5
    }
}
```

**How to run:** `java ThisIntermediate.java`

`this.celsius` on the right side of `previous = this.celsius` explicitly reads the field's *current* value into a local variable *before* it's overwritten — necessary because the parameter `celsius` shadows the field name, so without `this.`, there would be no way to reference the field's prior value at all within this method.

### Level 3 — Advanced

Same `Temperature`, now with a method that registers the current object with an external logger by passing `this` — demonstrating `this` used not just to disambiguate a field, but to hand a reference to "this exact object" to other code.

```java
public class ThisAdvanced {

    interface TemperatureListener {
        void onChange(Temperature t);
    }

    static class Temperature {
        double celsius;
        TemperatureListener listener;

        void setListener(TemperatureListener listener) {
            this.listener = listener;
        }

        void setCelsius(double celsius) {
            this.celsius = celsius;
            if (listener != null) {
                listener.onChange(this); // pass a reference to THIS object to the listener
            }
        }
    }

    public static void main(String[] args) {
        Temperature t = new Temperature();

        t.setListener(changed -> {
            System.out.println("Temperature changed to " + changed.celsius + "°C");
        });

        t.setCelsius(30.0);
        t.setCelsius(18.5);
    }
}
```

**How to run:** `java ThisAdvanced.java`

`listener.onChange(this)` passes a reference to the exact `Temperature` object whose `setCelsius` is currently executing — the lambda registered as `listener` receives that same object (as its parameter `changed`) and can read its up-to-date `celsius` field, demonstrating `this` used to let an object hand a reference to itself out to other collaborating code.

## 6. Walkthrough

Trace `ThisAdvanced.main`:

**Setup.** `t.setListener(...)` stores the lambda into `t.listener`. The lambda's parameter is named `changed` — it will receive whatever object is passed to `onChange`.

**First call: `t.setCelsius(30.0)`.** Inside `setCelsius`, `this.celsius = 30.0` (parameter `celsius` is `30.0`, assigned to the field via `this.`). Then `listener != null` is true, so `listener.onChange(this)` runs, passing the `Temperature` object currently executing this method (i.e., `t` itself) as the argument. Inside the lambda, `changed` now refers to that same object; `changed.celsius` reads `30.0` (already updated by the assignment just before). Prints `"Temperature changed to 30.0°C"`.

**Second call: `t.setCelsius(18.5)`.** Same sequence: `this.celsius = 18.5`, then `listener.onChange(this)` passes the same object again (still `t`), and the lambda prints `"Temperature changed to 18.5°C"`.

```
t.setCelsius(30.0):
  this.celsius = 30.0
  listener.onChange(this) -> changed = t (same object) -> changed.celsius = 30.0 -> print
t.setCelsius(18.5):
  this.celsius = 18.5
  listener.onChange(this) -> changed = t (same object, now updated) -> changed.celsius = 18.5 -> print
```

**Final output.** Two lines: `"Temperature changed to 30.0°C"` followed by `"Temperature changed to 18.5°C"` — each reflecting the field's value at the exact moment `this` was passed to the listener.

## 7. Gotchas & takeaways

> **Without `this.`, a parameter that shares a field's name completely shadows it inside that method** — plain `celsius = celsius;` (no `this.`) assigns the parameter to itself and silently leaves the actual field unchanged. This is one of the most common beginner mistakes when writing constructors and setters, and it produces no compiler error or warning by default.

> **`this` cannot be used inside a `static` method or `static` context**, since `static` code doesn't belong to any particular instance — there's no "this object" for it to refer to. `this` is only meaningful inside instance methods and constructors.

- `this` refers to the specific object a given instance method or constructor is currently executing on.
- `this.field` is required to unambiguously access a field when a parameter or local variable shadows its name.
- When there's no naming conflict, `this.` is optional — `field` and `this.field` behave identically in that case.
- `this` can be passed as an argument to hand other code a reference to the current object itself, not just its data.
