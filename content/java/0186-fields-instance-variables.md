---
card: java
gi: 186
slug: fields-instance-variables
title: Fields (instance variables)
---

## 1. What it is

A **field**, also called an **instance variable**, is a variable declared directly inside a class (outside any method) that holds data belonging to each individual object created from that class. Every object (instance) created with `new` gets its **own independent copy** of each field — changing one object's field never affects another object's field of the same name.

```java
class Point {
    int x; // field / instance variable
    int y; // field / instance variable
}

Point p1 = new Point();
p1.x = 3;
p1.y = 4;

Point p2 = new Point();
p2.x = 10;
p2.y = 20;

System.out.println(p1.x); // 3 — unaffected by p2
System.out.println(p2.x); // 10
```

`x` and `y` are declared once inside the `Point` class, but each `Point` object created with `new` gets its own separate storage for both — `p1.x` and `p2.x` are two entirely different memory locations, even though they share the same field name.

## 2. Why & when

Fields exist to model the data that naturally belongs to, and varies between, individual instances of a concept:

- **Per-object state** — a `Point`'s coordinates, a `BankAccount`'s balance, a `Car`'s current speed — each instance genuinely needs its own value, since it's meaningless to have only one shared coordinate for every point in a program.
- **Distinguishing fields from local variables** — a local variable declared inside a method exists only for that method call and disappears when the method returns; a field exists for as long as the object itself exists, and is accessible from any method within that same object.
- **Default initialization** — fields (unlike local variables) are automatically given a default value (`0`, `false`, `null`) if not explicitly assigned, so every field is always in some defined state the moment an object is created, even before a constructor runs any explicit assignment.

You declare a field whenever a piece of data is a genuine, lasting property of the object itself — as opposed to a temporary value only needed during one specific method's execution, which belongs as a local variable instead.

## 3. Core concept

```java
class Rectangle {
    double width;
    double height;

    double area() {
        return width * height; // reads THIS object's own width and height fields
    }
}

public class FieldsDemo {
    public static void main(String[] args) {
        Rectangle r1 = new Rectangle();
        r1.width = 4;
        r1.height = 5;

        Rectangle r2 = new Rectangle();
        r2.width = 10;
        r2.height = 2;

        System.out.println(r1.area()); // 20.0 — uses r1's own fields
        System.out.println(r2.area()); // 20.0 — uses r2's own fields, coincidentally equal
    }
}
```

`area()` never receives `width` or `height` as parameters — it reads them directly as fields of whichever object it's called on (`r1.area()` uses `r1`'s fields; `r2.area()` uses `r2`'s), which is exactly the point of storing data as fields rather than passing it around explicitly every time.

## 4. Diagram

<svg viewBox="0 0 560 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two separate Rectangle objects each with their own independent width and height fields in separate memory locations, despite both being created from the same class blueprint">
  <rect x="8" y="8" width="544" height="144" rx="8" fill="#0d1117"/>
  <text x="280" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">class Rectangle { double width; double height; }</text>

  <rect x="60" y="45" width="160" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="65" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">r1 (object)</text>
  <text x="80" y="90" fill="#e6edf3" font-size="10" font-family="monospace">width: 4</text>
  <text x="80" y="108" fill="#e6edf3" font-size="10" font-family="monospace">height: 5</text>

  <rect x="340" y="45" width="160" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="420" y="65" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">r2 (object)</text>
  <text x="360" y="90" fill="#e6edf3" font-size="10" font-family="monospace">width: 10</text>
  <text x="360" y="108" fill="#e6edf3" font-size="10" font-family="monospace">height: 2</text>
</svg>

Same class, same field names — but each object has its own completely independent storage for them.

## 5. Runnable example

Scenario: tracking several players' scores in a simple game — starting with basic independent fields per player, then extending with a method that reads and updates a player's own fields, then hardening into a method that compares two different players' field values against each other correctly.

### Level 1 — Basic

```java
public class PlayerBasic {
    static class Player {
        String name;
        int score;
    }

    public static void main(String[] args) {
        Player p1 = new Player();
        p1.name = "Ann";
        p1.score = 10;

        Player p2 = new Player();
        p2.name = "Bo";
        p2.score = 25;

        System.out.println(p1.name + ": " + p1.score);
        System.out.println(p2.name + ": " + p2.score);
    }
}
```

**How to run:** `java PlayerBasic.java`

`p1` and `p2` each have their own independent `name` and `score` fields — assigning `p1.score = 10` has absolutely no effect on `p2.score`.

### Level 2 — Intermediate

Same players, now with a method that adds points to whichever player it's called on, reading and updating that specific object's own `score` field.

```java
public class PlayerIntermediate {
    static class Player {
        String name;
        int score;

        void addPoints(int points) {
            score = score + points; // reads and writes THIS object's own score field
        }
    }

    public static void main(String[] args) {
        Player p1 = new Player();
        p1.name = "Ann";
        p1.score = 10;

        Player p2 = new Player();
        p2.name = "Bo";
        p2.score = 25;

        p1.addPoints(5);  // only affects p1's score
        p2.addPoints(100); // only affects p2's score

        System.out.println(p1.name + ": " + p1.score); // 15
        System.out.println(p2.name + ": " + p2.score); // 125
    }
}
```

**How to run:** `java PlayerIntermediate.java`

`p1.addPoints(5)` runs `addPoints`'s body using `p1`'s own `score` field (reading `10`, writing back `15`); `p2.addPoints(100)` runs the *same method code* but against `p2`'s independent `score` field (reading `25`, writing back `125`) — one method definition, applied separately to each object's own data.

### Level 3 — Advanced

Same players, now with a method that compares two *different* player objects' score fields to determine a winner, carefully reading each object's own field via its own parameter reference.

```java
public class PlayerAdvanced {
    static class Player {
        String name;
        int score;

        void addPoints(int points) {
            score += points;
        }
    }

    static String announceWinner(Player a, Player b) {
        if (a.score > b.score) {
            return a.name + " wins with " + a.score + " points";
        } else if (b.score > a.score) {
            return b.name + " wins with " + b.score + " points";
        } else {
            return "Tie at " + a.score + " points";
        }
    }

    public static void main(String[] args) {
        Player p1 = new Player();
        p1.name = "Ann"; p1.score = 10;

        Player p2 = new Player();
        p2.name = "Bo"; p2.score = 25;

        p1.addPoints(20); // Ann catches up: 10 -> 30

        System.out.println(announceWinner(p1, p2));
    }
}
```

**How to run:** `java PlayerAdvanced.java`

`announceWinner(a, b)` compares `a.score` against `b.score` — since `a` and `b` are two distinct objects (whatever was passed in as `p1` and `p2`), each `.score` access reads that specific object's own independent field, never confusing one player's score with another's, regardless of which objects happen to be passed as arguments.

## 6. Walkthrough

Trace `PlayerAdvanced.main`:

**Setup.** `p1` (Ann) starts with `score = 10`; `p2` (Bo) starts with `score = 25` — two entirely separate `Player` objects, each with independent `score` storage.

**`p1.addPoints(20)`.** Inside `addPoints`, `score += points` operates on whichever object the method was called on — here, `p1`'s own `score` field. `score` goes from `10` to `10 + 20 = 30`. `p2.score` is completely untouched by this call.

**`announceWinner(p1, p2)`.** Inside this method, parameter `a` refers to the same object as `p1` (score `30`), and `b` refers to the same object as `p2` (score `25`, still unchanged). `a.score (30) > b.score (25)` is `true`, so the method returns `"Ann wins with 30 points"`.

```
p1 (Ann): score 10 -> addPoints(20) -> score 30
p2 (Bo):  score 25 (untouched)

announceWinner(p1, p2):
  a.score=30, b.score=25
  30 > 25 -> "Ann wins with 30 points"
```

**Final output.** `"Ann wins with 30 points"` is printed — correctly reflecting that Ann's own `score` field was updated by her own call to `addPoints`, without ever touching or being confused with Bo's separate `score` field.

## 7. Gotchas & takeaways

> **Fields are automatically given default values (`0`, `false`, `null`) the moment an object is created, even before any explicit assignment.** Reading a numeric field before assigning it doesn't cause an error the way an uninitialized *local variable* would (which is actually a compile error in Java) — it silently reads the default, which can mask a bug if you expected an explicit initial value.

> **Two objects of the same class never share field storage, even though they share the same field *declarations*.** A common point of confusion for beginners is expecting a field to behave like a single shared value across all instances — that behaviour is what `static` fields do instead (a different topic entirely), not ordinary instance fields.

- A field (instance variable) is declared inside a class and holds data that belongs to each individual object.
- Every object created with `new` gets its own independent copy of every field — changing one object's field never affects another's.
- Methods defined in the class can read and write the fields of "this" object (whichever instance the method was called on) directly, without needing them passed as parameters.
- Fields default to `0`/`false`/`null` if not explicitly assigned, unlike local variables, which must be assigned before use.
