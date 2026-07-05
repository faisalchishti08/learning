---
card: java
gi: 143
slug: string-immutability
title: String immutability
---

## 1. What it is

A Java `String` object, once created, can **never be changed** — no method on `String` modifies its characters in place. Every method that looks like it "changes" a string (`toUpperCase()`, `replace()`, `concat()`, `substring()`, ...) actually creates and returns a **brand-new** `String` object, leaving the original untouched. If you don't capture that return value, the "change" is silently lost.

```java
String name = "alice";
name.toUpperCase(); // creates a NEW string "ALICE" — but throws it away, doesn't store it anywhere!
System.out.println(name); // still prints "alice" — the original was never touched

String upper = name.toUpperCase(); // THIS captures the new string
System.out.println(upper); // "ALICE"
```

`name` itself never changes. `toUpperCase()` builds a new `String` object containing the uppercase characters and returns a reference to it; what you do with that returned reference is entirely up to you.

## 2. Why & when

Immutability is a deliberate design choice for `String`, not an accident, and it pays off in several concrete ways:

- **Safety when sharing** — since a string can never be modified after creation, it's always safe to hand the same `String` object to multiple parts of a program (or multiple threads) without any of them being able to corrupt it for the others.
- **Enables the string pool** — because strings can't change, the JVM can safely let multiple variables share the very same underlying `String` object for identical literal text (covered in the next topic), saving memory.
- **Safe as keys and constants** — `String`s are commonly used as `HashMap` keys and `switch` labels; if a string's content could change after being used as a key, the map's internal structure would silently break.
- **Predictability** — passing a `String` into a method, you can be certain the method cannot alter your copy — this is a strong guarantee that mutable objects (like arrays) don't offer.

The trade-off is that repeatedly "modifying" a string in a loop creates many discarded intermediate objects — for genuinely heavy, repeated string building, `StringBuilder` (a separate, mutable class) is the appropriate tool instead.

## 3. Core concept

```java
public class ImmutabilityDemo {
    public static void main(String[] args) {
        String original = "hello";

        String replaced = original.replace('h', 'j');
        String concatenated = original.concat(" world");
        String sub = original.substring(1);

        System.out.println("original:     " + original);     // unchanged: "hello"
        System.out.println("replaced:     " + replaced);      // "jello"
        System.out.println("concatenated: " + concatenated);  // "hello world"
        System.out.println("sub:          " + sub);           // "ello"
    }
}
```

Every one of `replace`, `concat`, and `substring` reads `original` but produces its own separate new `String`; `original` prints as `"hello"` at the end, exactly as it started, no matter how many "modifying-looking" methods were called on it.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String immutability diagram: calling toUpperCase on a string does not modify it in place; instead it creates a separate new string object, and the original variable's reference is unaffected unless the new object's reference is explicitly assigned back to it.">
  <rect x="8" y="8" width="684" height="159" rx="8" fill="#0d1117"/>
  <text x="350" y="24" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">String name = "alice"; String upper = name.toUpperCase();</text>

  <rect x="60" y="45" width="110" height="26" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="62" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">name</text>

  <path d="M 170 58 L 260 58" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <rect x="260" y="45" width="140" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="62" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"alice" (object)</text>

  <rect x="60" y="100" width="110" height="26" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">upper</text>

  <path d="M 170 113 L 260 113" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>
  <rect x="260" y="100" width="140" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="117" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"ALICE" (NEW object)</text>

  <text x="500" y="60" fill="#8b949e" font-size="8.5" font-family="sans-serif">the ORIGINAL object,</text>
  <text x="500" y="72" fill="#8b949e" font-size="8.5" font-family="sans-serif">untouched by toUpperCase()</text>

  <text x="530" y="115" fill="#8b949e" font-size="8.5" font-family="sans-serif">a completely SEPARATE object</text>

  <text x="350" y="150" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">toUpperCase() never touches "alice" — it builds "ALICE" fresh and returns a reference to it.</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`name` and `upper` point to two entirely distinct `String` objects — one is never derived by mutating the other.

## 5. Runnable example

Scenario: normalizing a batch of user-entered usernames (trimming whitespace and lowercasing) — starting with a version that has the classic "forgot to capture the result" bug, then fixing it, then hardening it to chain several immutable transformations safely while proving the original input is never altered anywhere in the process.

### Level 1 — Basic (the bug, shown deliberately)

```java
public class NormalizeBuggy {
    public static void main(String[] args) {
        String username = "  Alice_Smith  ";

        username.trim();          // result discarded!
        username.toLowerCase();   // result discarded!

        System.out.println("Normalized: [" + username + "]"); // still the original, untouched string
    }
}
```

**How to run:** `java NormalizeBuggy.java`

Neither `trim()` nor `toLowerCase()` modifies `username` — both build new strings and immediately discard them, since their return values are never assigned to anything. The printed output still shows the original, un-trimmed, un-lowercased string: `[  Alice_Smith  ]`.

### Level 2 — Intermediate (the fix)

Same normalization, now correctly capturing each method's return value by reassigning it back to `username` — a very common and perfectly valid pattern precisely because it doesn't mutate the original string; it just points `username` at each successive new string.

```java
public class NormalizeFixed {
    public static void main(String[] args) {
        String username = "  Alice_Smith  ";

        username = username.trim();
        username = username.toLowerCase();

        System.out.println("Normalized: [" + username + "]"); // "alice_smith"
    }
}
```

**How to run:** `java NormalizeFixed.java`

`username = username.trim();` does not modify the string `"  Alice_Smith  "` in place — it creates a new trimmed string and makes the variable `username` refer to that new object instead, abandoning the reference to the old one. The same happens again with `toLowerCase()`. This reassignment pattern is the standard, correct way to work with immutable strings.

### Level 3 — Advanced

Same normalization pipeline, now processing a batch of usernames and additionally proving immutability by keeping a reference to the *original* string alongside the normalized one — demonstrating that even after multiple chained transformations, the very first string object is completely unaffected and still exists, unchanged, in memory as long as something references it.

```java
public class NormalizeAdvanced {

    static String normalize(String raw) {
        return raw.trim().toLowerCase().replace(' ', '_');
    }

    public static void main(String[] args) {
        String[] rawUsernames = { "  Alice Smith  ", "BOB JONES", " Carol " };

        for (String raw : rawUsernames) {
            String normalized = normalize(raw);
            System.out.println("original: [" + raw + "]  ->  normalized: [" + normalized + "]");
        }
    }
}
```

**How to run:** `java NormalizeAdvanced.java`

`raw.trim().toLowerCase().replace(' ', '_')` chains three immutable transformations in a row: `trim()` returns a new trimmed string, `toLowerCase()` is called on *that* new string and returns yet another new string, and `replace(' ', '_')` is called on *that* one and returns a final new string — each step in the chain operates on the previous step's fresh output, never on `raw` itself. Printing `raw` inside the loop afterward proves it: the original, untrimmed, mixed-case, space-containing string is still exactly what it was, for every element of the array.

## 6. Walkthrough

Trace `normalize("  Alice Smith  ")`:

**`raw.trim()`.** Reads `raw` (`"  Alice Smith  "`) and creates a brand-new `String`, `"Alice Smith"` (leading/trailing spaces removed), leaving `raw` completely unchanged. This new object has no name yet — it exists only as an intermediate value.

**`.toLowerCase()`** is called on that intermediate `"Alice Smith"` object, producing yet another new `String`, `"alice smith"`. The `"Alice Smith"` object from the previous step is now unreferenced (nothing points to it anymore) and becomes eligible for garbage collection.

**`.replace(' ', '_')`** is called on `"alice smith"`, producing the final new `String`, `"alice_smith"`. This is the value `normalize` returns.

```
raw = "  Alice Smith  "                  (never modified, referenced by "raw" for the whole method)
  .trim()          -> new: "Alice Smith"        (raw untouched)
  .toLowerCase()    -> new: "alice smith"        (previous intermediate untouched)
  .replace(' ','_') -> new: "alice_smith"        (this one IS the return value)
```

**Back in `main`.** `normalized` is assigned the final result, `"alice_smith"`, while `raw` still holds the original `"  Alice Smith  "` — the print statement shows both side by side, confirming neither the original nor any intermediate string was ever altered; only new objects were created at each step.

**Final output.** For the three inputs, the loop prints `original: [  Alice Smith  ]  ->  normalized: [alice_smith]`, `original: [BOB JONES]  ->  normalized: [bob_jones]`, and `original: [ Carol  ]  ->  normalized: [carol]` (each trimmed correctly by `trim()` regardless of how many leading/trailing spaces it originally had).

## 7. Gotchas & takeaways

> **Calling a "modifying-looking" `String` method and ignoring its return value is a silent no-op, not an error.** `str.trim();` on its own line compiles and runs without complaint, but does absolutely nothing to `str` — the trimmed string it created is immediately discarded because nothing captured the reference to it. Always assign the result: `str = str.trim();`.

> **Immutability means a string is safe to share, but it does NOT mean the variable holding it is fixed** — `String s = "a"; s = "b";` is perfectly legal; it doesn't change the `"a"` object (which still exists if anything else references it), it just makes `s` point somewhere else entirely.

- No method on `String` ever changes the characters of an existing `String` object — every "transformation" method returns a new object.
- Always capture the return value of string methods (`str = str.someMethod();`); otherwise the transformation is silently lost.
- Chaining calls (`str.trim().toLowerCase()`) works because each call's return value becomes the next call's receiver — each link in the chain is a distinct, freshly created object.
- Immutability is what makes `String`s safe to share across variables, methods, and threads without any risk of one holder's usage corrupting another's.
