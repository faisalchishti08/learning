---
card: java
gi: 76
slug: default-values-of-each-primitive
title: Default values of each primitive
---

## 1. What it is

Every instance field and static field of a primitive type in Java is automatically initialised to a well-defined default value when the object (or class) is loaded. The defaults are all "zero-like": numeric types default to `0` (or `0.0`), `boolean` defaults to `false`, and `char` defaults to `'\0'` (the NUL character, Unicode code point 0).

| Type      | Default value  |
|-----------|---------------|
| `byte`    | `0`           |
| `short`   | `0`           |
| `int`     | `0`           |
| `long`    | `0L`          |
| `float`   | `0.0f`        |
| `double`  | `0.0`         |
| `char`    | `'\0'`        |
| `boolean` | `false`       |

This guarantee applies to **fields** (instance and static) but **not to local variables**, which must be explicitly initialised before use — the compiler enforces this.

## 2. Why & when

Default values matter in three common scenarios:
- **Counting / accumulating** — an `int` field used as a counter starts at `0` without explicit initialisation.
- **Flag state** — a `boolean` field representing "has this event occurred?" correctly starts as `false`.
- **Unset detection** — understanding that an unset `char` field is `'\0'`, not `'0'` (digit zero, value 48), prevents subtle bugs when printing character arrays that have not been fully filled.

Understanding defaults also helps you recognise when an explicit initialisation is redundant but harmless (e.g., `int count = 0;`) versus when it is necessary for clarity.

## 3. Core concept

```java
public class PrimitiveDefaults {

    // ---- Instance fields — all initialised to defaults ----
    byte    b;
    short   s;
    int     i;
    long    l;
    float   f;
    double  d;
    char    c;
    boolean flag;

    static int staticInt;   // static field — also initialised to 0

    void printDefaults() {
        System.out.println("byte    : " + b);        // 0
        System.out.println("short   : " + s);        // 0
        System.out.println("int     : " + i);        // 0
        System.out.println("long    : " + l);        // 0
        System.out.println("float   : " + f);        // 0.0
        System.out.println("double  : " + d);        // 0.0
        System.out.println("char    : '" + c + "'"); // '' (NUL — invisible)
        System.out.println("char int: " + (int) c);  // 0  (NUL code point)
        System.out.println("boolean : " + flag);     // false
        System.out.println("static  : " + staticInt);// 0
    }

    public static void main(String[] args) {
        new PrimitiveDefaults().printDefaults();

        // ---- Local variables — no default, must initialise before use ----
        int localInt;
        // System.out.println(localInt);  // compile error: variable might not have been initialised

        int explicitly = 0;   // explicit initialisation (same as field default)
        System.out.println("explicitly initialised: " + explicitly);

        // ---- char default is NUL '\0', NOT '0' ----
        char[] letters = new char[5];   // all elements default to '\0'
        letters[0] = 'H';
        letters[1] = 'i';
        System.out.println(new String(letters));          // "Hi\0\0\0" — trailing NULs
        System.out.println(new String(letters).trim());   // "Hi" after trimming
        System.out.println("letters[2] == '\\0': " + (letters[2] == '\0'));    // true
        System.out.println("letters[2] == '0':  " + (letters[2] == '0'));     // false
    }
}
```

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Primitive default values: all 8 types with their zero-like defaults, fields vs local variable contrast">
  <rect x="8" y="8" width="684" height="184" rx="8" fill="#0d1117"/>

  <!-- Fields section -->
  <rect x="16" y="18" width="400" height="164" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="216" y="36" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Fields (instance + static) — auto-initialised</text>
  <line x1="26" y1="43" x2="406" y2="43" stroke="#8b949e" stroke-width="0.5"/>

  <!-- Type columns -->
  <text x="50"  y="58" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">Type</text>
  <text x="150" y="58" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">Default</text>
  <text x="280" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">Note</text>

  <text x="50"  y="73"  fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">byte</text>
  <text x="150" y="73"  fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">0</text>
  <text x="280" y="73"  fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">numeric zero</text>

  <text x="50"  y="87"  fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">short</text>
  <text x="150" y="87"  fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">0</text>
  <text x="280" y="87"  fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">numeric zero</text>

  <text x="50"  y="101" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">int</text>
  <text x="150" y="101" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">0</text>
  <text x="280" y="101" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">numeric zero</text>

  <text x="50"  y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">long</text>
  <text x="150" y="115" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">0L</text>
  <text x="280" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">64-bit zero</text>

  <text x="50"  y="129" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">float</text>
  <text x="150" y="129" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">0.0f</text>
  <text x="280" y="129" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">positive zero</text>

  <text x="50"  y="143" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">double</text>
  <text x="150" y="143" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">0.0</text>
  <text x="280" y="143" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">positive zero</text>

  <text x="50"  y="157" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">char</text>
  <text x="150" y="157" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">'\0' (NUL)</text>
  <text x="280" y="157" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">NOT '0' (48)</text>

  <text x="50"  y="171" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">boolean</text>
  <text x="150" y="171" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">false</text>
  <text x="280" y="171" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">NOT true</text>

  <!-- Local var section -->
  <rect x="428" y="18" width="256" height="164" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="556" y="36" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Local Variables</text>
  <line x1="438" y1="43" x2="674" y2="43" stroke="#8b949e" stroke-width="0.5"/>
  <text x="556" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No automatic initialisation</text>
  <text x="556" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Compiler enforces explicit init</text>
  <text x="556" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">before first read.</text>
  <rect x="438" y="100" width="228" height="42" rx="4" fill="#0d1117"/>
  <text x="448" y="117" fill="#8b949e" font-size="7.5" font-family="monospace">int x;</text>
  <text x="448" y="131" fill="#8b949e" font-size="7.5" font-family="monospace">println(x); // compile error</text>
  <text x="556" y="158" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">int x = 0; // explicit required</text>
  <text x="556" y="174" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">applies to parameters too</text>
</svg>

Fields get zero-like defaults automatically; local variables have no default and must be initialised before use — the compiler enforces this.

## 5. Runnable example

Scenario: a scoreboard that tracks player scores and active status across rounds — the default values play a direct role in the first round of scoring, growing from simple use of defaults to detecting an uninitialised char, and finally to a diagnostic that confirms defaults via reflection.

### Level 1 — Basic

```java
public class DefaultsBasic {

    static class Player {
        String name;
        int    score;      // default: 0
        int    lives;      // default: 0 — will be set explicitly
        boolean active;    // default: false
        char    grade;     // default: '\0'
    }

    public static void main(String[] args) {
        Player p = new Player();
        p.name  = "Alice";
        p.lives = 3;       // lives needs explicit value; 0 is not a valid starting life count

        System.out.println("=== Player state after construction ===");
        System.out.println("name   : " + p.name);
        System.out.println("score  : " + p.score);   // 0 — from default
        System.out.println("lives  : " + p.lives);   // 3 — set explicitly
        System.out.println("active : " + p.active);  // false — from default
        System.out.println("grade  : [" + p.grade + "] (char value " + (int) p.grade + ")");

        // Simulate first round
        p.score  += 100;
        p.active  = true;
        p.grade   = 'C';

        System.out.println();
        System.out.println("=== After first round ===");
        System.out.println("score  : " + p.score);
        System.out.println("active : " + p.active);
        System.out.println("grade  : " + p.grade);
    }
}
```

**How to run:** `java DefaultsBasic.java`

`p.score` starts at `0` because `int` fields default to zero. `p.active` starts as `false` because `boolean` fields default to false. `p.grade` starts as `'\0'` (NUL, code point 0) — casting it to `int` shows `0`, confirming it is not the digit `'0'` (which has code point 48). `p.lives` is set explicitly to `3` because `0` lives would mean the player starts the game already eliminated — relying on the default here would be a logic bug.

### Level 2 — Intermediate

Same scoreboard: extend to detect unset `char` grades (the NUL default) as a sentinel, initialise an array of players and observe defaults in elements, and compare with object (reference) default of `null`.

```java
public class DefaultsIntermediate {

    static class Player {
        String name;
        int    score;
        boolean active;
        char    grade;

        boolean hasGrade() { return grade != '\0'; }
    }

    public static void main(String[] args) {
        // Array of Player — each element starts as null (reference default)
        Player[] roster = new Player[3];
        System.out.println("roster[0] before assignment: " + roster[0]);  // null

        roster[0] = new Player(); roster[0].name = "Alice"; roster[0].score = 250;
        roster[1] = new Player(); roster[1].name = "Bob";   roster[1].score = 180; roster[1].grade = 'B';
        roster[2] = new Player(); roster[2].name = "Carol"; roster[2].score = 310; roster[2].grade = 'A';

        System.out.println();
        System.out.printf("%-8s  %5s  %6s  %-8s%n", "Name", "Score", "Grade", "HasGrade");
        System.out.println("-".repeat(38));

        for (Player p : roster) {
            if (p == null) continue;
            System.out.printf("%-8s  %5d  %6s  %s%n",
                p.name, p.score,
                p.hasGrade() ? String.valueOf(p.grade) : "(none)",
                p.hasGrade());
        }

        // Primitive array defaults
        System.out.println();
        int[] scores = new int[5];     // all 0
        boolean[] flags = new boolean[4]; // all false
        System.out.print("int[] defaults: ");
        for (int v : scores)  System.out.print(v + " ");
        System.out.println();
        System.out.print("boolean[] defaults: ");
        for (boolean v : flags) System.out.print(v + " ");
        System.out.println();
    }
}
```

**How to run:** `java DefaultsIntermediate.java`

`Player[]` is an object array — its elements default to `null` (the reference default), not a zero-value `Player`. The `Player` object itself is only created when you write `new Player()`. `grade != '\0'` uses the NUL default as a sentinel meaning "not yet assigned", which is a common idiom for `char` fields. `int[]` elements default to `0` and `boolean[]` elements default to `false` — these primitive array defaults are guaranteed by the JLS.

### Level 3 — Advanced

Same system: use reflection to enumerate all declared fields of a class and print each field's value on a freshly created instance, confirming the defaults systematically without hard-coding them.

```java
import java.lang.reflect.Field;

public class DefaultsAdvanced {

    static class AllPrimitives {
        byte    b;
        short   s;
        int     i;
        long    l;
        float   f;
        double  d;
        char    c;
        boolean flag;
        String  ref;   // reference type — default null (for comparison)
    }

    static class Player {
        String name;
        int    score;
        boolean active;
        char    grade;
    }

    static void printDefaults(Class<?> cls) throws Exception {
        Object instance = cls.getDeclaredConstructor().newInstance();
        System.out.printf("%-12s  %-30s  %s%n", "Field", "Value", "Type");
        System.out.println("-".repeat(62));
        for (Field field : cls.getDeclaredFields()) {
            field.setAccessible(true);
            Object value = field.get(instance);
            String display = (field.getType() == char.class)
                ? "'" + value + "' (int=" + (int)(char)(Character) value + ")"
                : String.valueOf(value);
            System.out.printf("%-12s  %-30s  %s%n",
                field.getName(), display, field.getType().getSimpleName());
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== AllPrimitives defaults ===");
        printDefaults(AllPrimitives.class);
        System.out.println();
        System.out.println("=== Player defaults ===");
        printDefaults(Player.class);
    }
}
```

**How to run:** `java DefaultsAdvanced.java`

`cls.getDeclaredConstructor().newInstance()` creates a fresh instance without calling any explicit constructor body (the no-arg default constructor does nothing, so all fields remain at their JVM-assigned defaults). `Field.get(instance)` returns the field's current value boxed into its wrapper type (`int` → `Integer`, `char` → `Character`, etc.). For `char`, casting to `Character` then to `char` and then to `int` reveals the underlying NUL code point `0`. The `String` field `ref` shows `null`, demonstrating that the reference-type default differs from the primitive defaults — it is `null`, not zero.

## 6. Walkthrough

Execution trace through `DefaultsAdvanced.main` for `AllPrimitives`:

**Instance creation.** `cls.getDeclaredConstructor().newInstance()` invokes the implicit no-arg constructor for `AllPrimitives`. The JVM zeroes the object's memory before the constructor runs — every field is set to its zero-like default as part of object allocation.

**Field enumeration.** `getDeclaredFields()` returns an array of `Field` objects in declaration order. For each field, `field.setAccessible(true)` bypasses access control so private or package-private fields are readable.

**Value retrieval.** `field.get(instance)` returns a boxed representation: `int` → `Integer(0)`, `boolean` → `Boolean(false)`, `char` → `Character('\0')`. For `char`, the display code unpacks `Character` → `char` → `int` to show both the invisible NUL character and its numeric value `0`.

**Output pattern.** Across all eight primitive fields the value is always zero-like. The `String ref` field shows `null` — a reminder that reference fields default to `null`, which is the reference equivalent of zero. The complete output confirms every entry in the defaults table:

```
Field         Value                           Type
--------------------------------------------------------------
b             0                               byte
s             0                               short
i             0                               int
l             0                               long
f             0.0                             float
d             0.0                             double
c             '' (int=0)                      char
flag          false                           boolean
ref           null                            String
```

## 7. Gotchas & takeaways

> **`char` defaults to `'\0'` (NUL), not `'0'` (the digit zero).** They look similar in code but have completely different code-point values: `'\0'` is 0 and `'0'` is 48. Printing a NUL character produces an invisible character, not `'0'`, which causes confusing output from partially filled `char[]` arrays.

> **Local variables have no defaults — the compiler enforces explicit initialisation.** If you access a local variable before assigning it, the code will not compile. This is intentional: fields get defaults because the JVM controls their allocation, but local variables are on the stack and may hold arbitrary memory values if not explicitly set.

- Primitive fields (instance and static) are zero-initialised by the JVM: `0`, `0L`, `0.0f`, `0.0`, `'\0'`, and `false`.
- Local variables of primitive type have no default; you must assign them before reading.
- Reference fields (including `String` and arrays) default to `null`, not a zero-value object.
- Array elements are zero-initialised when the array is created, regardless of whether the element type is primitive or reference.
- `boolean` defaults to `false`, making it a safe sentinel for "not yet set" flags.
- Writing `int count = 0;` as an explicit field initialiser is redundant but harmless — it makes intent explicit for readers.
